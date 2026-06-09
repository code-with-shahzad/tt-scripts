import os
import uuid
import threading
import time
from math import ceil
from typing import Optional
from concurrent.futures import ThreadPoolExecutor
from enum import Enum

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from new import (
    get_user_info,
    send_comment_thread as _send_comment,
    send_like_thread as _send_like,
    clean_username,
    TikTokError,
)

app = FastAPI(
    title="TikTok Automation API",
    description="HTTP interface for TikTok live comment automation",
    version="1.0.0",
)

STATIC_DIR = os.path.join(os.path.dirname(__file__), "static")
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

def _calc_workers(total: int) -> int:
    try:
        from new import SESSION_IDS
        session_count = len(SESSION_IDS)
    except ImportError:
        session_count = 50
    return min(session_count, max(5, ceil(total / 10)))


class TaskStatus(str, Enum):
    pending = "pending"
    running = "running"
    completed = "completed"
    cancelled = "cancelled"


class CommentTask:
    def __init__(self, task_id: str, user_id: str, room_id: str, total: int,
                 task_type: str = "comment", words: list[str] = None, like_count: int = 1):
        self.task_id = task_id
        self.user_id = user_id
        self.room_id = room_id
        self.words = words or []
        self.total = total
        self.workers = _calc_workers(total)
        self.task_type = task_type
        self.like_count = like_count
        self.status = TaskStatus.pending
        self.success_count = 0
        self.failed_count = 0
        self._cancel_event = threading.Event()
        self._lock = threading.Lock()

    def increment_success(self):
        with self._lock:
            self.success_count += 1

    def increment_failed(self):
        with self._lock:
            self.failed_count += 1

    @property
    def done_count(self) -> int:
        with self._lock:
            return self.success_count + self.failed_count

    def should_cancel(self) -> bool:
        return self._cancel_event.is_set()

    def cancel(self):
        self._cancel_event.set()
        self.status = TaskStatus.cancelled

    def to_dict(self):
        d = {
            "task_id": self.task_id,
            "user_id": self.user_id,
            "room_id": self.room_id,
            "task_type": self.task_type,
            "status": self.status.value,
            "success_count": self.success_count,
            "failed_count": self.failed_count,
            "total": self.total,
            "done": self.done_count,
            "workers": self.workers,
            "like_count": self.like_count,
        }
        
        try:
            from new import session_usage, SESSION_IDS
            d["sessions_used"] = len(session_usage)
            d["sessions_total"] = len(SESSION_IDS)
        except ImportError:
            d["sessions_used"] = 0
            d["sessions_total"] = 0
            
        return d


tasks: dict[str, CommentTask] = {}
tasks_lock = threading.Lock()


def run_comment_task(task: CommentTask):
    word_set = set(task.words)

    def wrapped_send():
        if task.should_cancel():
            return
        try:
            ok = _send_comment(task.user_id, task.room_id, word_set)
        except Exception:
            ok = False
        if ok:
            task.increment_success()
        else:
            task.increment_failed()

    task.status = TaskStatus.running
    with ThreadPoolExecutor(max_workers=task.workers) as executor:
        futures = []
        for _ in range(task.total):
            if task.should_cancel():
                break
            futures.append(executor.submit(wrapped_send))
        for f in futures:
            if task.should_cancel():
                break
            f.result()
    if task.status != TaskStatus.cancelled:
        task.status = TaskStatus.completed


def run_like_task(task: CommentTask):
    def wrapped_send():
        if task.should_cancel():
            return
        ok = _send_like(task.user_id, task.room_id)
        if ok:
            task.increment_success()
        else:
            task.increment_failed()

    task.status = TaskStatus.running
    with ThreadPoolExecutor(max_workers=task.workers) as executor:
        futures = []
        for _ in range(task.total):
            if task.should_cancel():
                break
            futures.append(executor.submit(wrapped_send))
        for f in futures:
            if task.should_cancel():
                break
            f.result()
    if task.status != TaskStatus.cancelled:
        task.status = TaskStatus.completed


# ─── Request / Response Models ───────────────────────────────────────────────

class UserInfoRequest(BaseModel):
    username: str = Field(..., description="TikTok username (with or without @)")


class UserInfoResponse(BaseModel):
    username: str
    user_id: str
    room_id: str
    is_live: bool


class SendCommentRequest(BaseModel):
    user_id: str
    room_id: str
    content: str


class SendCommentResponse(BaseModel):
    success: bool
    message: str


class BulkCommentRequest(BaseModel):
    user_id: str
    room_id: str
    words: list[str] = Field(..., min_length=1, description="List of comment texts")
    count: int = Field(default=100, ge=1, le=50000, description="Number of comments to send")


class SendLikeRequest(BaseModel):
    user_id: str
    room_id: str


class SendLikeResponse(BaseModel):
    success: bool
    message: str


class BulkLikeRequest(BaseModel):
    user_id: str
    room_id: str
    count: int = Field(default=100, ge=1, le=50000, description="Number of likes to send")


class BulkLikeResponse(BaseModel):
    task_id: str
    status: str
    message: str


class BulkCommentResponse(BaseModel):
    task_id: str
    status: str
    message: str


class TaskStatusResponse(BaseModel):
    task_id: str
    status: str
    user_id: str
    room_id: str
    task_type: str = "comment"
    success_count: int
    failed_count: int
    total: int
    done: int
    workers: int
    like_count: int = 1
    sessions_used: int = 0
    sessions_total: int = 0


class StatsResponse(BaseModel):
    total_tasks: int
    active_tasks: int
    total_success: int
    total_failed: int
    total_sent: int


class HealthResponse(BaseModel):
    status: str
    active_tasks: int


# ─── Error handler ───────────────────────────────────────────────────────────

@app.exception_handler(TikTokError)
async def tiktok_error_handler(request, exc: TikTokError):
    return JSONResponse(status_code=400, content={"detail": str(exc)})


# ─── Endpoints ───────────────────────────────────────────────────────────────

@app.get("/")
async def index():
    return FileResponse(os.path.join(STATIC_DIR, "index.html"))


@app.get("/health", response_model=HealthResponse)
async def health():
    active = sum(1 for t in tasks.values() if t.status == TaskStatus.running)
    return HealthResponse(status="ok", active_tasks=active)


@app.post("/user-info", response_model=UserInfoResponse)
async def user_info(req: UserInfoRequest):
    username = clean_username(req.username)
    if not username:
        raise HTTPException(400, "Username cannot be empty")
    user_id, room_id = get_user_info(username)
    return UserInfoResponse(
        username=username,
        user_id=user_id,
        room_id=room_id,
        is_live=bool(room_id),
    )


@app.post("/send-comment", response_model=SendCommentResponse)
async def send_single_comment(req: SendCommentRequest):
    try:
        threading.Thread(
            target=_send_comment,
            args=(req.user_id, req.room_id, {req.content}),
            daemon=True,
        ).start()
        return SendCommentResponse(success=True, message="Comment sent")
    except Exception as e:
        return SendCommentResponse(success=False, message=str(e))


@app.post("/send-comments", response_model=BulkCommentResponse)
async def start_bulk_comments(req: BulkCommentRequest, background_tasks: BackgroundTasks):
    task_id = uuid.uuid4().hex[:12]
    task = CommentTask(
        task_id=task_id,
        user_id=req.user_id,
        room_id=req.room_id,
        words=req.words,
        total=req.count,
    )
    with tasks_lock:
        tasks[task_id] = task
    background_tasks.add_task(run_comment_task, task)
    return BulkCommentResponse(
        task_id=task_id,
        status=TaskStatus.pending.value,
        message=f"Started sending {req.count} comments",
    )


@app.post("/send-like", response_model=SendLikeResponse)
async def send_single_like(req: SendLikeRequest):
    try:
        ok = _send_like(req.user_id, req.room_id)
        return SendLikeResponse(success=ok, message="Like sent" if ok else "Like failed")
    except Exception as e:
        return SendLikeResponse(success=False, message=str(e))


@app.post("/send-likes", response_model=BulkLikeResponse)
async def start_bulk_likes(req: BulkLikeRequest, background_tasks: BackgroundTasks):
    task_id = uuid.uuid4().hex[:12]
    task = CommentTask(
        task_id=task_id,
        user_id=req.user_id,
        room_id=req.room_id,
        total=req.count,
        task_type="like",
    )
    with tasks_lock:
        tasks[task_id] = task
    background_tasks.add_task(run_like_task, task)
    return BulkLikeResponse(
        task_id=task_id,
        status=TaskStatus.pending.value,
        message=f"Started sending {req.count} likes",
    )


@app.get("/send-comments", response_model=list[TaskStatusResponse])
async def list_tasks():
    with tasks_lock:
        return [t.to_dict() for t in tasks.values()]


@app.get("/send-comments/{task_id}", response_model=TaskStatusResponse)
async def get_task_status(task_id: str):
    task = tasks.get(task_id)
    if not task:
        raise HTTPException(404, f"Task {task_id} not found")
    return task.to_dict()


@app.post("/send-comments/{task_id}/stop")
async def stop_task(task_id: str):
    task = tasks.get(task_id)
    if not task:
        raise HTTPException(404, f"Task {task_id} not found")
    if task.status in (TaskStatus.completed, TaskStatus.cancelled):
        raise HTTPException(400, f"Task {task_id} is already {task.status.value}")
    task.cancel()
    return {"task_id": task_id, "status": TaskStatus.cancelled.value, "message": "Task cancelled"}


@app.get("/stats", response_model=StatsResponse)
async def stats():
    active = 0
    total_success = 0
    total_failed = 0
    with tasks_lock:
        for t in tasks.values():
            if t.status == TaskStatus.running:
                active += 1
            total_success += t.success_count
            total_failed += t.failed_count
    return StatsResponse(
        total_tasks=len(tasks),
        active_tasks=active,
        total_success=total_success,
        total_failed=total_failed,
        total_sent=total_success + total_failed,
    )


@app.delete("/tasks/{task_id}")
async def delete_task(task_id: str):
    task = tasks.get(task_id)
    if not task:
        raise HTTPException(404, f"Task {task_id} not found")
    if task.status == TaskStatus.running:
        task.cancel()
    with tasks_lock:
        del tasks[task_id]
    return {"message": f"Task {task_id} deleted", "task_id": task_id}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)
