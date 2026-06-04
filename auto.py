import warnings

warnings.filterwarnings(
    "ignore",
    message="urllib3 v2 only supports OpenSSL",
    category=Warning,
)

import requests
import time
import random
import re
import json
import uuid
import binascii
import os
import secrets
import threading
from html import unescape
from typing import Tuple, Set
from concurrent.futures import ThreadPoolExecutor, as_completed
import string
try:
    import SignerPy
except ImportError:
    import subprocess
    import sys
    subprocess.check_call([sys.executable, "-m", "pip", "install", "SignerPy"])
    import SignerPy

class Config:
    REGIONS = ["AE", "IQ", "US", "FR", "DE"]
    DEVICE_TYPES = ["SM-S928B", "P40", "Mi 11", "iPhone12,1", "OnePlus9"]
    DEVICE_BRANDS = ["samsung", "huawei", "xiaomi", "apple", "oneplus"]
    SESSION_IDS = [
    "97070268205d331109684cc6ca65b05f",
]
comment_success = 0
comment_failed = 0
like_success = 0
like_failed = 0
count_lock = threading.Lock()

class TikTokLookupError(Exception):
    pass

def clean_username(username: str) -> str:
    username = username.strip()
    if username.startswith("@"):
        username = username[1:]
    return username.strip()

def walk_json(value):
    if isinstance(value, dict):
        yield value
        for item in value.values():
            yield from walk_json(item)
    elif isinstance(value, list):
        for item in value:
            yield from walk_json(item)

def json_script_data(html: str):
    for match in re.finditer(r'<script[^>]*type="application/json"[^>]*>(.*?)</script>', html, re.S):
        raw = unescape(match.group(1)).strip()
        if not raw:
            continue
        try:
            yield json.loads(raw)
        except json.JSONDecodeError:
            continue

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

    escaped = re.escape(username)
    patterns = [
        rf'"id":"(\d+)"[^{{}}]{{0,500}}"uniqueId":"{escaped}"',
        rf'"uniqueId":"{escaped}"[^{{}}]{{0,500}}"id":"(\d+)"',
        r'"authorId":"(\d+)"',
    ]
    for pattern in patterns:
        match = re.search(pattern, html, re.I | re.S)
        if match:
            return match.group(1)

    return ""

def extract_room_id(html: str) -> str:
    for data in json_script_data(html):
        for node in walk_json(data):
            for key in ("roomId", "room_id"):
                value = node.get(key)
                if value and str(value).isdigit():
                    return str(value)

    patterns = [
        r'"roomId"\s*:\s*"?(\d+)"?',
        r'"room_id"\s*:\s*"?(\d+)"?',
    ]
    for pattern in patterns:
        match = re.search(pattern, html)
        if match:
            return match.group(1)

    return ""

def get_user_info(username: str) -> Tuple[str, str]:
    username = clean_username(username)
    if not username:
        raise TikTokLookupError("Username is empty.")

    response = requests.get(
        f"https://www.tiktok.com/@{username}/live",
        headers={
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/125.0.0.0 Safari/537.36"
            )
        },
        timeout=20
    )
    if response.status_code == 404:
        raise TikTokLookupError(f"Account not found: @{username}")
    response.raise_for_status()

    text = response.text
    if "SlardarWAF" in text or "slardar_us_waf" in text:
        raise TikTokLookupError(
            "TikTok blocked this automated request before returning profile data. "
            "Open the profile in a normal browser to confirm whether the account exists "
            "and whether it is live."
        )

    user_id = extract_user_id(text, username)
    if not user_id:
        raise TikTokLookupError(
            f"Could not read profile data for @{username}. "
            "The account may not exist, TikTok may be blocking this request, "
            "or the page format may have changed."
        )

    room_id = extract_room_id(text)
    if not room_id:
        raise TikTokLookupError(f"@{username} exists, but is not live right now.")

    return user_id, room_id

def generate_mobile_ua() -> str:
    android_versions = ["10", "11", "12", "13", "14"]
    android_apis = ["29", "30", "31", "32", "33", "34"]
    models = [
        "SM-S908B", "SM-G991B", "M2011K2G", "ELS-NX9", "LE2123",
        "Pixel 6", "Pixel 7", "CPH2237", "V2045", "XQ-BC72",
        "LM-F100N", "SM-A536B", "2107113SG", "M2101K6G", "NE2213"
    ]
    app_versions = [
        "2022806050", "2022907000", "2023008001", "2023109002",
        "2023111003", "2023122004", "2024011005", "2024022006"
    ]
    ttnet_versions = ["6a8e8a4c", "7b9f9b5d", "8c0a0c6e", "9d1b1d7f"]
    quic_versions = ["5f23035d", "6g34146e", "7h45257f", "8i56368g"]
    
    model = random.choice(models)
    android_ver = random.choice(android_versions)
    api_level = random.choice(android_apis)
    build_id = ''.join(random.choices(string.ascii_uppercase + string.digits, k=random.randint(6, 10)))
    app_ver = random.choice(app_versions)
    ttnet_ver = random.choice(ttnet_versions)
    quic_ver = random.choice(quic_versions)
    
    return f"com.zhiliaoapp.musically/{app_ver} (Linux; U; Android {android_ver}; {api_level}; ar_EG; {model}; Build/{build_id}; Cronet/TTNetVersion:{ttnet_ver} QuicVersion:{quic_ver})"

def build_params():
    return {
        'iid': str(random.randint(10**18, 10**19 - 1)),
        'device_id': str(random.randint(10**18, 10**19 - 1)),
        'ac': random.choice(["wifi", "4g", "5g"]),
        'channel': "googleplay",
        'aid': "1233",
        'app_name': "musical_ly",
        'version_code': str(random.randint(270000, 290000)),
        'version_name': f"{random.randint(27,29)}.{random.randint(0,9)}.{random.randint(0,9)}",
        'device_platform': "android",
        'ab_version': "28.6.5",
        'ssmix': "a",
        'device_type': random.choice(Config.DEVICE_TYPES),
        'device_brand': random.choice(Config.DEVICE_BRANDS),
        'language': "ar",
        'os_api': str(random.randint(28, 34)),
        'os_version': str(random.randint(10, 14)),
        'openudid': binascii.hexlify(os.urandom(8)).decode(),
        'manifest_version_code': str(random.randint(2022000000, 2024999999)),
        'resolution': random.choice(["1080*2400", "720*1600", "1440*3200"]),
        'dpi': str(random.choice([240, 320, 480])),
        'update_version_code': str(random.randint(2022000000, 2024999999)),
        '_rticket': str(int(time.time() * 1000)),
        'app_type': "normal",
        'sys_region': random.choice(Config.REGIONS),
        'mcc_mnc': str(random.randint(10000, 99999)),
        'timezone_name': random.choice(["Africa/Cairo", "Asia/Baghdad", "Europe/Paris"]),
        'carrier_region_v2': str(random.randint(100, 999)),
        'app_language': "ar",
        'carrier_region': random.choice(Config.REGIONS),
        'ac2': random.choice(["wifi", "4g", "5g"]),
        'uoo': "0",
        'op_region': random.choice(Config.REGIONS),
        'timezone_offset': str(random.choice([7200, 10800, 3600])),
        'build_number': "28.6.5",
        'host_abi': "arm64-v8a",
        'locale': "ar",
        'region': random.choice(Config.REGIONS),
        'ts': int(time.time()),
        'cdid': str(uuid.uuid4()),
        'webcast_language': "ar",
        'webcast_locale': "ar_EG",
        'effect_sdk_version': "1.3.0"
    }

def send_comment_thread(user_id: str, room_id: str, words: Set[str], thread_name: str) -> None:
    global comment_success, comment_failed
    try:
        session = requests.Session()
        ss = random.choice(Config.SESSION_IDS)
        secret = secrets.token_hex(16)
        session.cookies.update({
            "passport_csrf_token": secret,
            "passport_csrf_token_default": secret,
            "sessionid": ss
        })
        
        host = random.choice(["22", "21", "16", "15", "19"])
        url = f"https://webcast{host}-normal-c-alisg.tiktokv.com/webcast/room/chat/"
        params = build_params()                          
        cmm = random.choice(list(words))        
        payload = {
            'room_id': room_id,
            'emotes_with_index': "",
            'anchor_id': user_id,
            'is_ad': "0",
            'input_type': "0",
            'enter_source': "",
            'post_anyway': "0",
            'client_start_timestamp_millisecond': str(int(time.time() * 1000)),
            'content': cmm,
            'enter_method': "live_cover",
            'enter_from_merge': "live_merge",
            'tag': "live_ad",
            'request_id': f"req_{uuid.uuid4().hex}"
        }
        
        headers = {'User-Agent': generate_mobile_ua()}
        mm = SignerPy.sign(params=params, payload=payload, url=url)
        headers.update(mm)        
        response = session.post(url, params=params, data=payload, headers=headers, timeout=10)
        
        with count_lock:
            if response.status_code == 200 and ("id" in response.text or "msg_id" in response.text):
                comment_success += 1
            else:
                comment_failed += 1
        print(f"\r[+] Comment - Success: {comment_success} | Failed: {comment_failed}", end="", flush=True)
        
    except Exception:
        with count_lock:
            comment_failed += 1
        print(f"\r[+] Comment - Success: {comment_success} | Failed: {comment_failed}", end="", flush=True)

def send_like_thread(user_id: str, room_id: str, thread_name: str) -> None:
    global like_success, like_failed
    try:
        session = requests.Session()
        ss = random.choice(Config.SESSION_IDS)
        secret = secrets.token_hex(16)
        session.cookies.update({
            "passport_csrf_token": secret,
            "passport_csrf_token_default": secret,
            "sessionid": ss
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
            'request_id': f"req_{uuid.uuid4().hex}"
        }
        
        headers = {'User-Agent': generate_mobile_ua()}
        mm = SignerPy.sign(params=params, payload=payload, url=url)
        headers.update(mm)
        response = session.post(url, params=params, data=payload, headers=headers, timeout=10)
        
        with count_lock:
            if response.status_code == 200:
                like_success += 1
            else:
                like_failed += 1
        print(f"\r[+] Like - Success: {like_success} | Failed: {like_failed}", end="", flush=True)
        
    except Exception:
        with count_lock:
            like_failed += 1
        print(f"\r[+] Like - Success: {like_success} | Failed: {like_failed}", end="", flush=True)


def main() -> None:
    username = clean_username(input("username : "))
    
    mode = input("Mode (c=comments, l=likes, b=both): ").strip().lower()
    comment_count = int(input("How many comments/likes to send: ") or "1000")
    
    words = {
        "سلام عليكم", "شخباركم", "كيفكم", "نحبك", "هلا", "مرحبا", "اهلين", "شلونك",
        "شنو الاخبار", "شكو ماكو", "تمام", "الحمدلله", "يا هلا", "حبيبي", "قلبي",
        "احبك", "احبك هواي", "فديتك", "صباح الخير", "مساء الخير", "الله يحفظك",
        "مشتاقلك", "😂", "🤣", "❤️", "😍", "😎"
    }
    
    try:
        user_id, room_id = get_user_info(username)
        print(f"[✓] User ID: {user_id}")
        print(f"[✓] Room ID: {room_id}")
        print("=" * 50)
        
        with ThreadPoolExecutor(max_workers=50) as executor:
            futures = []
            for i in range(comment_count):
                if mode in ("c", "b"):
                    futures.append(executor.submit(send_comment_thread, user_id, room_id, words, f"C{i+1}"))
                if mode in ("l", "b"):
                    futures.append(executor.submit(send_like_thread, user_id, room_id, f"L{i+1}"))
            for future in as_completed(futures):
                future.result()
        
        print("\n" + "=" * 50)
        print("[✓] All threads completed")
        print(f"[✓] Comments - Success: {comment_success} | Failed: {comment_failed}")
        print(f"[✓] Likes    - Success: {like_success} | Failed: {like_failed}")
        print("=" * 50)
        
    except TikTokLookupError as e:
        print(e)
    except requests.RequestException as e:
        print(f"Network error while checking TikTok: {e}")

if __name__ == "__main__":
    main()