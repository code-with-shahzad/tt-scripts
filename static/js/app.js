/* ── State ── */
const state = {
  action: 'comments',
  taskIds: [],
  pollingId: null,
  consoleCollapsed: false,
};

/* ── API ── */
async function api(method, path, body) {
  const start = Date.now();
  const opts = {
    method,
    headers: { 'Content-Type': 'application/json' },
  };
  if (body !== undefined) opts.body = JSON.stringify(body);

  con('req', `${method} ${path}`, body ? JSON.stringify(body).slice(0,150) : '');

  const res = await fetch(path, opts);
  const elapsed = Date.now() - start;
  const ct = res.headers.get('content-type') || '';
  const data = ct.includes('application/json') ? await res.json() : await res.text();

  if (!res.ok) {
    const msg = data?.detail || data?.message || res.statusText;
    con('err', `${method} ${path} → ${res.status}`, msg);
    throw new Error(msg);
  }

  con('res', `${method} ${path} → ${res.status} (${elapsed}ms)`, JSON.stringify(data).slice(0,200));
  return data;
}

const POST = (p, b) => api('POST', p, b);
const GET = (p) => api('GET', p);

/* ── Console ── */
function con(type, msg, data) {
  const el = document.getElementById('console-body');
  if (!el) return;
  const t = new Date().toLocaleTimeString('en-US', { hour12: false });
  const line = document.createElement('div');
  line.className = 'con-log';
  line.innerHTML = `<span class="t">${t}</span><span class="b ${type}">${type}</span><span class="m">${msg}${data ? '  ' + data : ''}</span>`;
  el.appendChild(line);
  el.scrollTop = el.scrollHeight;
  while (el.children.length > 300) el.removeChild(el.firstChild);
}

/* ── Toast ── */
function toast(msg, type = 'info') {
  const c = document.getElementById('toast-container');
  const el = document.createElement('div');
  el.style.cssText = `pointer-events:auto;padding:10px 16px;border-radius:6px;font-size:13px;font-weight:500;box-shadow:0 4px 24px rgba(0,0,0,0.4);animation:fade-in 0.2s ease;max-width:360px;backdrop-filter:blur(12px);`;
  const colors = { success: 'rgba(0,230,118,0.15)', error: 'rgba(255,61,113,0.15)', info: 'rgba(0,212,255,0.15)', warning: 'rgba(255,171,0,0.15)' };
  const text = { success: 'var(--success)', error: 'var(--danger)', info: 'var(--accent)', warning: 'var(--warning)' };
  el.style.background = colors[type] || colors.info;
  el.style.color = text[type] || text.info;
  el.textContent = msg;
  c.appendChild(el);
  setTimeout(() => { el.style.opacity = '0'; el.style.transition = 'opacity 0.3s'; setTimeout(() => el.remove(), 300); }, 3500);
}

/* ── UI helpers ── */
const $ = (id) => document.getElementById(id);
const val = (id) => { const el = $(id); return el ? el.value.trim() : ''; };
const num = (id) => { const el = $(id); return el ? parseInt(el.value) || 0 : 0; };

function escape(s) {
  const d = document.createElement('div');
  d.textContent = s;
  return d.innerHTML;
}

function fmt(n) {
  if (n >= 1000000) return (n/1000000).toFixed(1)+'M';
  if (n >= 1000) return (n/1000).toFixed(1)+'K';
  return String(n);
}

/* ── Action toggle ── */
document.querySelectorAll('.action-toggles button').forEach(btn => {
  btn.addEventListener('click', () => {
    document.querySelectorAll('.action-toggles button').forEach(b => b.classList.remove('active'));
    btn.classList.add('active');
    state.action = btn.dataset.action;

    // Enable/disable count boxes
    const a = state.action;
    $('count-comments').classList.toggle('active', a === 'comments' || a === 'both');
    $('count-likes').classList.toggle('active', a === 'likes' || a === 'both');
  });
});

/* ── Start ── */
$('start-btn').addEventListener('click', startTask);
$('username-input').addEventListener('keydown', e => { if (e.key === 'Enter') startTask(); });

async function startTask() {
  const username = val('username-input');
  if (!username) return toast('Enter a username', 'warning');

  const btn = $('start-btn');
  btn.disabled = true;
  btn.innerHTML = '<span class="spinner"></span> Looking up...';

  // Reset UI
  $('error-box').style.display = 'none';
  $('user-banner').style.display = 'none';
  $('status-area').style.display = 'none';
  $('status-area').innerHTML = '';
  state.taskIds = [];

  try {
    // Step 1: Look up user
    const info = await POST('/user-info', { username });
    con('ok', `Found @${info.username}`, `user_id=${info.user_id}`);

    // Show user banner
    const ub = $('user-banner');
    ub.style.display = 'flex';
    $('ub-username').textContent = '@' + info.username;
    $('ub-user-id').textContent = info.user_id;
    $('ub-room-id').textContent = info.room_id || '—';
    $('live-indicator').innerHTML = info.is_live
      ? '<span class="live-dot"></span><span style="color:var(--success);font-weight:600;font-size:12px;">LIVE</span>'
      : '<span class="offline-dot"></span><span style="color:var(--text-muted);font-size:12px;">Offline</span>';

    if (!info.is_live) {
      showError(`@${info.username} is not live right now`);
      btn.disabled = false;
      btn.innerHTML = '▶ Start';
      return;
    }

    // Step 2: Start tasks based on action
    const hasComments = state.action === 'comments' || state.action === 'both';
    const hasLikes = state.action === 'likes' || state.action === 'both';
    const commentCount = num('comments-count');
    const likeCount = num('likes-count');

    let tasks = [];

    if (hasComments && commentCount > 0) {
      const defaultWords = [
        "Great stream!", "Nice content", "Love the vibe", "Keep it up",
        "Well done", "Amazing broadcast", "Good energy", "Solid stream",
        "Interesting points", "Way to go", "Keep going", "Enjoying the live",
        "Nice to see you", "Loving this", "Good quality", "Awesome job",
        "Super cool", "Nice work", "Good stuff", "Love this",
        "So good", "Fantastic content", "Top notch", "Excellent work",
        "hello everyone", "sending love", "this is fire", "lets go",
        "yesss", "wow", "no way", "insane", "crazy good",
        "best stream ever", "straight fire", "lets get it", "come on",
        "whats good", "this is sick", "absolute banger", "W stream",
        "first time here", "love the energy", "this is lit",
        "came from fyp", "staying for vibes", "goated stream",
      ];
      btn.innerHTML = '<span class="spinner"></span> Starting comments...';
      const res = await POST('/send-comments', {
        user_id: info.user_id,
        room_id: info.room_id,
        words: defaultWords,
        count: commentCount,
      });
      tasks.push({ id: res.task_id, type: 'comments', total: commentCount });
      state.taskIds.push(res.task_id);
    }

    if (hasLikes && likeCount > 0) {
      btn.innerHTML = '<span class="spinner"></span> Starting likes...';
      const res = await POST('/send-likes', {
        user_id: info.user_id,
        room_id: info.room_id,
        count: likeCount,
      });
      tasks.push({ id: res.task_id, type: 'likes', total: likeCount });
      state.taskIds.push(res.task_id);
    }

    if (tasks.length === 0) {
      toast('Set at least one count > 0', 'warning');
      btn.disabled = false;
      btn.innerHTML = '▶ Start';
      return;
    }

    // Show status cards
    const sa = $('status-area');
    sa.style.display = 'flex';
    tasks.forEach(t => {
      const card = document.createElement('div');
      card.className = 'status-card';
      card.id = `sc-${t.id}`;
      card.innerHTML = `
        <div class="top-row">
          <span class="type-badge ${t.type}">${t.type === 'comments' ? '💬 Comments' : '👍 Likes'}</span>
          <span class="task-id">${t.id}</span>
          <span class="status-badge-sm running" id="st-${t.id}"><span class="dot"></span> running</span>
          <button class="stop-btn" onclick="stopTask('${t.id}')">Stop</button>
        </div>
        <div class="progress-row">
          <span class="pct" id="pct-${t.id}">0%</span>
          <div class="bar-wrap">
            <div class="bar-fill ${t.type}-fill" id="bar-${t.id}" style="width:0%"></div>
          </div>
          <span class="counts" id="cnt-${t.id}"><span class="ok">0</span> / <span class="fail">0</span> / ${t.total}</span>
        </div>
      `;
      sa.appendChild(card);
    });

    toast(`Started ${tasks.length} task(s)`, 'success');
    con('ok', `Started ${tasks.length} tasks`, tasks.map(t => `${t.type}:${t.id}`).join(', '));

    // Step 3: Poll
    btn.innerHTML = '▶ Start';
    btn.disabled = false;
    if (state.pollingId) clearInterval(state.pollingId);
    state.pollingId = setInterval(pollTasks, 1500);

  } catch (err) {
    showError(err.message);
    btn.disabled = false;
    btn.innerHTML = '▶ Start';
  }
}

function showError(msg) {
  const el = $('error-box');
  el.style.display = 'block';
  el.textContent = '✕ ' + msg;
  toast(msg, 'error');
}

/* ── Polling ── */
async function pollTasks() {
  if (state.taskIds.length === 0) return;

  try {
    const all = await GET('/send-comments');
    const relevant = all.filter(t => state.taskIds.includes(t.task_id));

    let allDone = true;

    relevant.forEach(t => {
      const pct = t.total > 0 ? Math.min(100, Math.round(t.done / t.total * 100)) : 0;
      const card = $(`sc-${t.task_id}`);
      if (!card) return;

      const pctEl = $(`pct-${t.task_id}`);
      const barEl = $(`bar-${t.task_id}`);
      const cntEl = $(`cnt-${t.task_id}`);
      const stEl = $(`st-${t.task_id}`);

      if (pctEl) pctEl.textContent = pct + '%';
      if (barEl) {
        barEl.style.width = pct + '%';
        barEl.className = 'bar-fill';
        const cls = t.task_type === 'comment' ? 'comments-fill' : 'likes-fill';
        barEl.classList.add(
          t.status === 'completed' ? 'completed-fill' :
          t.status === 'cancelled' ? 'cancelled-fill' : cls
        );
      }
      if (cntEl) cntEl.innerHTML = `<span class="ok">${t.success_count}</span> / <span class="fail">${t.failed_count}</span> / ${t.total}<br><span style="font-size:11px;color:var(--text-muted);display:block;margin-top:4px">Sessions Used: ${t.sessions_used || 0} / ${t.sessions_total || 0}</span>`;
      if (stEl) {
        stEl.className = 'status-badge-sm ' + t.status;
        stEl.innerHTML = `<span class="dot"></span> ${t.status}`;
      }

      if (t.status === 'completed' || t.status === 'cancelled') {
        // allDone remains true only if all are done
      } else {
        allDone = false;
      }
    });

    if (allDone && relevant.length > 0) {
      clearInterval(state.pollingId);
      state.pollingId = null;
      toast('All tasks completed', 'success');
      con('ok', 'All tasks finished');
    }
  } catch (err) {
    // ignore
  }
}

/* ── Stop task ── */
async function stopTask(taskId) {
  try {
    await POST(`/send-comments/${taskId}/stop`);
    toast(`Task ${taskId} cancelled`, 'warning');
  } catch (err) {
    toast(err.message, 'error');
  }
}

/* ── Console toggle ── */
$('console-header').addEventListener('click', (e) => {
  if (e.target.closest('.console-actions')) return;
  state.consoleCollapsed = !state.consoleCollapsed;
  $('console').classList.toggle('collapsed', state.consoleCollapsed);
});

$('console-clear-btn').addEventListener('click', (e) => {
  e.stopPropagation();
  $('console-body').innerHTML = '';
});

/* ── Init ── */
con('info', 'TikTok Automation UI ready');
