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

SESSION_IDS = [
    "41b6da299c3ef4ae21f521f2d2b15bd7",
    "20ce7d3a456a3a9fee3855a8e255fdf4",
    "3b1bfc8cc8ae1a9cf11b62e72281cd00",
    "1e152a17616b1e782cf8cc61cbb91bb3",
    "58dc54cf3683887177302881483ae377",
    "24180f8593a2a1fcc3067faf959c6429",
    "176fe741c87a89077d5551534638f7a4",
    "2530f644ba19dd2af5ce47f368f745f9",
    "62c129a252218856386d6f1ed820b567",
    "df20a3975324769a20a8d993a369db79",
    "345f84c146f335afac10e3812e4c1036",
    "12f587f76da894ff4c97c377ef2d2701",
    "3cf0d0506e1b29f56bd51a8e3feb529a",
    "553e913f283421af9b8609c3f842cc1e",
    "6b89789bec69edc6cc19f8339dee3a7c",
    "352929797106fb0ba35f7c67fe568753",
    "4538799c6b6aec3e44ab14ac44e77f36",
    "3587096c3c693e4eaded28698eba7e78",
    "97070268205d331109684cc6ca65b05f",
    "4ac8b9a8a1f452d1c0242dd7f8bba0dc",
    "7952b5f43115ce2c961f1b88109b8935",
    "765ffe2c064c2a12b79925e345d5ceaa",
    "7a40e2007ada042493213484d9102b87",
    "aa0793fea02903d2a4175c9f3879a254",
    "a02c909d0d59748384b11876e3c95ff3",
    "999ab52746768e0f2350df8d12f1fe39",
    "aec26fc0a29d849a77864ef8b9bc9726",
    "a1f778c3ea389e24daa725ac77edd4ba",
    "a4bb43e930bbfdd6a17d4245dea38729",
    "7f645181d5936f3d04c4052f1dbd86c5",
    "7cc4ecf185702c25d84de8ce8e6ac03d",
    "b225a7d4399fd4296a198deccd1d2925",
    "ac92b3c19e435a2070e076b1d397af5f",
    "8396fe8ff00188c0b2f6ac65461b3f2c",
    "7cbd19de01ece28886d04b42d352a062",
    "bf5f15cca680e41daf37ac3791c2c7f9",
    "a49e1e1fa53a86eedb0b2f32c61daac7",
    "b8a9c7d3e4f5a6b7c8d9e0f1a2b3c4d5",
    "70cf01c9fbcb771879801b31724864bf",
    "68998360c4cfc08e279c55ac14465ffb",
    "c7f39c9046f21bf65cbb346dac2319a8",
    "d05154e0ce203af5551e09e75d415c60",
    "eb21f64a0864a803c4757ac9ebb45015",
    "e96ca45cbe375cc81ece8aac4b1a8511",
    "ea83031e5a059b78069b6aa4c79c7a7a",
    "e3b4c90df76b91fb953368d7dda2d46e",
    "e1b731c52feebb2df5106e27c4fbc35c",
    "c37fd504e72356827cdca6de5ae02562",
    "e9f8d7c6b5a4e3d2c1b0a9f8e7d6c5b4",
    "e7873d8aa4512938f980226b966791b7",
    "ea3823f67daa95976dfcd68b56c21f8b",
    "f8fc5a7d71caefa8fa606eb0612ba21e",
    "d83f7ca44b3422b2b7ff7bc672a194b1",
    "d8df8982e2f705f05a1672bbe5896ad0",
    "ed5f8bd4d239ced09488d3986c400c29"
]
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


def _fetch_profile_html(username: str) -> str:
    for attempt in range(3):
        # Try curl_cffi with impersonation first
        try:
            sess = curl_requests.Session()
            sess.headers.update({
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.9",
            })
            resp = sess.get(f"https://www.tiktok.com/@{username}", impersonate='chrome120', timeout=15)
            if resp.status_code == 200:
                return resp.text
        except Exception:
            pass
        # Fallback: plain requests
        try:
            sess2 = requests.Session()
            sess2.headers.update({
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            })
            resp = sess2.get(f"https://www.tiktok.com/@{username}", timeout=(15, 15), verify=False)
            if resp.status_code == 200:
                return resp.text
        except Exception:
            pass
        if attempt < 2:
            time.sleep(2)
    raise TikTokError(f"Could not reach TikTok for @{username}.")


def get_user_info(username: str) -> Tuple[str, str]:
    username = clean_username(username)
    if not username:
        raise TikTokError("Username is empty.")
    html = _fetch_profile_html(username)

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


def send_comment_thread(user_id: str, room_id: str, words: Set[str]) -> bool:
    global success_count, failed_count
    try:
        sess = curl_requests.Session()
        ss = random.choice(SESSION_IDS)
        sess.cookies.update({
            "sessionid": ss,
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
        resp = sess.post(url, params=params, data=payload, headers=headers, impersonate='chrome120', timeout=10)
        response_text = resp.text
        ok = resp.status_code == 200 and ("id" in response_text or "msg_id" in response_text)
        with count_lock:
            if ok:
                success_count += 1
            else:
                failed_count += 1
        print(f"\r[+] Success: {success_count} | Failed: {failed_count}", end="", flush=True)
        return ok
    except Exception:
        with count_lock:
            failed_count += 1
        print(f"\r[+] Success: {success_count} | Failed: {failed_count}", end="", flush=True)
        return False


def send_like_thread(user_id: str, room_id: str) -> bool:
    global success_count, failed_count
    try:
        sess = curl_requests.Session()
        ss = random.choice(SESSION_IDS)
        sess.cookies.update({
            "sessionid": ss,
            "sid_tt": SID_TT,
            "uid_tt": UID_TT,
            "tt_csrf_token": TT_CSRF,
        })
        host = random.choice(["22", "21", "16", "15", "19"])
        url = f"https://webcast{host}-normal-c-alisg.tiktokv.com/webcast/room/like/"
        params = build_params()
        count = random.randint(1, 30)
        payload = {
            'room_id': room_id,
            'anchor_id': user_id,
            'count': str(count),
            'like_count': str(count),
            'enter_from_merge': 'live_merge',
            'request_id': f"req_{uuid.uuid4().hex}",
        }
        headers = {'User-Agent': generate_mobile_ua()}
        mm = SignerPy.sign(params=params, payload=payload, url=url)
        headers.update(mm)
        resp = sess.post(url, params=params, data=payload, headers=headers, impersonate='chrome120', timeout=10)
        ok = resp.status_code == 200
        with count_lock:
            if ok:
                success_count += 1
            else:
                failed_count += 1
        print(f"\r[+] Like - Success: {success_count} | Failed: {failed_count}", end="", flush=True)
        return ok
    except Exception:
        with count_lock:
            failed_count += 1
        print(f"\r[+] Like - Success: {success_count} | Failed: {failed_count}", end="", flush=True)
        return False


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
