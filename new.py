import warnings
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
warnings.filterwarnings("ignore", message="urllib3 v2 only supports OpenSSL", category=Warning)

import requests
import time
import random
import re
import json
import uuid
import binascii
import os
import threading
import subprocess
import sys
from html import unescape
from typing import Tuple, Set
from concurrent.futures import ThreadPoolExecutor, as_completed

CHROME_PATH = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"

try:
    import SignerPy
except ImportError:
    subprocess.check_call([sys.executable, "-m", "pip", "install", "SignerPy"])
    import SignerPy

try:
    from curl_cffi import requests as curl_requests
except ImportError:
    subprocess.check_call([sys.executable, "-m", "pip", "install", "curl_cffi"])
    from curl_cffi import requests as curl_requests

SESSION_ID = "df20a3975324769a20a8d993a369db79"
SID_TT = "df20a3975324769a20a8d993a369db79"
UID_TT = "9a64dbc5bbe69f7521cdaef09bf78245196192f3eefbbc7801459243da8448e7"
TT_CSRF = "pWNT60G4-XKn3GrnIEcy0fQwsKDIV3fMXZTU"

success_count = 0
failed_count = 0
count_lock = threading.Lock()


class TikTokError(Exception):
    pass


def walk_json(value):
    if isinstance(value, dict):
        yield value
        for item in value.values():
            yield from walk_json(item)
    elif isinstance(value, list):
        for item in value:
            yield from walk_json(item)


def json_script_data(html: str) -> list:
    result = []
    for m in re.finditer(r'<script[^>]*type="application/json"[^>]*>(.*?)</script>', html, re.S):
        raw = unescape(m.group(1)).strip()
        if raw:
            try:
                result.append(json.loads(raw))
            except json.JSONDecodeError:
                continue
    return result


def clean_username(username: str) -> str:
    username = username.strip()
    if username.startswith("@"):
        username = username[1:]
    return username.strip()


def extract_user_id(html: str, username: str) -> str:
    username_lower = username.lower()
    for data in json_script_data(html):
        for node in walk_json(data):
            unique_id = str(node.get("uniqueId") or node.get("unique_id") or "").lower()
            if unique_id == username_lower and node.get("id"):
                return str(node["id"])
            user = node.get("user")
            if isinstance(user, dict):
                unique_id = str(user.get("uniqueId") or user.get("unique_id") or "").lower()
                if unique_id == username_lower and user.get("id"):
                    return str(user["id"])
    return ""


def extract_room_id(html: str) -> str:
    for data in json_script_data(html):
        for node in walk_json(data):
            rid = node.get("roomId") or node.get("room_id") or ""
            if rid and str(rid).isdigit():
                return str(rid)
            user = node.get("user") or {}
            if isinstance(user, dict):
                rid = user.get("roomId") or user.get("room_id") or ""
                if rid and str(rid).isdigit():
                    return str(rid)
    for m in re.finditer(r'"roomId"\s*:\s*"(\d+)"', html):
        return m.group(1)
    return ""


def get_user_info(username: str) -> Tuple[str, str]:
    username = clean_username(username)
    if not username:
        raise TikTokError("Username is empty.")
    sess = requests.Session()
    sess.headers.update({
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
    })
    html = sess.get(f"https://www.tiktok.com/@{username}", timeout=25, verify=False).text
    user_id = extract_user_id(html, username)
    if not user_id:
        raise TikTokError(f"Could not read profile data for @{username}.")

    room_id = ""
    for attempt in range(20):
        try:
            proc = subprocess.run([
                CHROME_PATH, '--headless', '--dump-dom',
                '--ignore-certificate-errors', '--incognito',
                '--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                f'https://www.tiktok.com/@{username}/live',
                '--timeout=15000',
            ], capture_output=True, timeout=25)
            live_html = proc.stdout.decode('utf-8', errors='replace')
            room_id = extract_room_id(live_html)
            if room_id:
                print(f"[✓] Got room ID on attempt {attempt+1}")
                break
            print(f"[~] WAF blocked, retry {attempt+1}/20", end="\r")
        except Exception as e:
            print(f"[~] Error: {e}, retry {attempt+1}/20", end="\r")
        time.sleep(2)

    return user_id, room_id


def generate_mobile_ua() -> str:
    models = ["SM-S908B", "SM-G991B", "Pixel 6", "Pixel 7", "CPH2237", "NE2213"]
    model = random.choice(models)
    return (
        f"com.zhiliaoapp.musically/280000 (Linux; U; Android 11; en; {model}; "
        f"Build/ABCDEF; Cronet/TTNetVersion:7b9f9b5d QuicVersion:5f23035d)"
    )


def build_params():
    return {
        'iid': str(random.randint(10**18, 10**19 - 1)),
        'device_id': str(random.randint(10**18, 10**19 - 1)),
        'ac': 'wifi',
        'channel': 'googleplay',
        'aid': '1233',
        'app_name': 'musical_ly',
        'version_code': '280000',
        'version_name': '28.0.0',
        'device_platform': 'android',
        'device_type': 'SM-S928B',
        'device_brand': 'samsung',
        'language': 'en',
        'os_api': '30',
        'os_version': '11',
        'openudid': binascii.hexlify(os.urandom(8)).decode(),
        'resolution': '1080*2400',
        'dpi': '480',
        'ts': int(time.time()),
    }


def send_comment_thread(user_id: str, room_id: str, words: Set[str]) -> None:
    global success_count, failed_count
    try:
        sess = curl_requests.Session()
        sess.cookies.update({
            "sessionid": SESSION_ID,
            "sid_tt": SID_TT,
            "uid_tt": UID_TT,
            "tt_csrf_token": TT_CSRF,
        })
        host = random.choice(["22", "21", "16", "15", "19"])
        url = f"https://webcast{host}-normal-c-alisg.tiktokv.com/webcast/room/chat/"
        params = build_params()
        cmm = random.choice(list(words))
        payload = {
            'room_id': room_id,
            'anchor_id': user_id,
            'content': cmm,
            'is_ad': '0',
            'input_type': '0',
            'enter_source': '',
            'post_anyway': '0',
            'client_start_timestamp_millisecond': str(int(time.time() * 1000)),
            'enter_method': 'live_cover',
            'enter_from_merge': 'live_merge',
            'tag': 'live_ad',
            'request_id': f"req_{uuid.uuid4().hex}",
        }
        headers = {'User-Agent': generate_mobile_ua()}
        mm = SignerPy.sign(params=params, payload=payload, url=url)
        headers.update(mm)
        resp = sess.post(url, params=params, data=payload, headers=headers, impersonate='chrome120')
        ok = resp.status_code == 200 and '"id"' in resp.text
        with count_lock:
            if ok:
                success_count += 1
            else:
                failed_count += 1
    except Exception:
        with count_lock:
            failed_count += 1
    print(f"\r[+] Success: {success_count} | Failed: {failed_count}", end="", flush=True)


def main() -> None:
    username = clean_username(input("username : "))
    words = {
        "hacker is here", "Hacker is Here", "HACKER IS HERE",
        "you've been hacked", "You've Been Hacked",
        "hacker", "Hacker", "HACKER",
        "i'm in", "I'm in", "IM IN",
        "your account is mine", "Your Account Is Mine",
        "got you", "Got You", "GOT YOU",
    }
    try:
        user_id, room_id = get_user_info(username)
        print(f"[✓] User ID: {user_id}")
        if not room_id:
            print(f"[!] @{username} is not live right now (no room ID found)")
            return
        print(f"[✓] Room ID: {room_id}")
        print("=" * 50)
        with ThreadPoolExecutor(max_workers=50) as executor:
            futures = [executor.submit(send_comment_thread, user_id, room_id, words) for _ in range(10000)]
            for future in as_completed(futures):
                future.result()
        print("\n" + "=" * 50)
        print(f"[✓] Final - Success: {success_count} | Failed: {failed_count}")
    except TikTokError as e:
        print(e)
    except requests.RequestException as e:
        print(f"Network error: {e}")


if __name__ == "__main__":
    main()
