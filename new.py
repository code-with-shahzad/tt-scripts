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
import secrets
import threading
import subprocess
import sys
import string
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
REGIONS = ["AE", "IQ", "US", "FR", "DE"]
DEVICE_TYPES = ["SM-S928B", "P40", "Mi 11", "iPhone12,1", "OnePlus9"]
DEVICE_BRANDS = ["samsung", "huawei", "xiaomi", "apple", "oneplus"]
UA_APP_VERSIONS = [
    "2022806050", "2022907000", "2023008001", "2023109002",
    "2023111003", "2023122004", "2024011005", "2024022006"
]
UA_TTNET_VERSIONS = ["6a8e8a4c", "7b9f9b5d", "8c0a0c6e", "9d1b1d7f"]
UA_QUIC_VERSIONS = ["5f23035d", "6g34146e", "7h45257f", "8i56368g"]

PROXY_LIST = [
    "38.154.203.95:5863:nvlfwozd:amv8s0aajp2i",
    "198.105.121.200:6462:nvlfwozd:amv8s0aajp2i",
    "64.137.96.74:6641:nvlfwozd:amv8s0aajp2i",
    "209.127.138.10:5784:nvlfwozd:amv8s0aajp2i",
    "38.154.185.97:6370:nvlfwozd:amv8s0aajp2i",
    "84.247.60.125:6095:nvlfwozd:amv8s0aajp2i",
    "142.111.67.146:5611:nvlfwozd:amv8s0aajp2i",
    "191.96.254.138:6185:nvlfwozd:amv8s0aajp2i",
    "31.58.9.4:6077:nvlfwozd:amv8s0aajp2i",
    "104.239.107.47:5699:nvlfwozd:amv8s0aajp2i"
]

def get_proxy_dict(proxy_str):
    parts = proxy_str.split(':')
    if len(parts) == 4:
        ip, port, user, password = parts
        proxy_url = f"http://{user}:{password}@{ip}:{port}"
        return {"http": proxy_url, "https": proxy_url}
    return None

comment_success = 0
comment_failed = 0
like_success = 0
like_failed = 0
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
            rid = node.get("roomId") or node.get("room_id") or ""
            if rid and str(rid).isdigit():
                return str(rid)
            user = node.get("user") or {}
            if isinstance(user, dict):
                rid = user.get("roomId") or user.get("room_id") or ""
                if rid and str(rid).isdigit():
                    return str(rid)
    patterns = [
        r'"roomId"\s*:\s*"?(\d+)"?',
        r'"room_id"\s*:\s*"?(\d+)"?',
    ]
    for pattern in patterns:
        match = re.search(pattern, html)
        if match:
            return match.group(1)
    return ""


def _fetch_profile_html(username: str) -> str:
    for attempt in range(3):
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

    print(f"[*] Fetching live room information for @{username}...")
    user_id = ""
    room_id = ""

    # Method 1: Bypass WAF completely by hitting api-live/user/room/ directly with clientParams
    try:
        sess = curl_requests.Session(impersonate='chrome120')
        url = f"https://www.tiktok.com/api-live/user/room/?uniqueId={username}&sourceType=54&aid=1988&app_language=en&device_platform=web_pc"
        resp = sess.get(url, timeout=15)
        
        if resp.status_code == 200:
            js = resp.json()
            data = js.get("data", {})
            if data:
                user_info = data.get("user", {})
                
                # The API returns both room_id and user_id directly inside `data.user`
                user_id = str(user_info.get("id", ""))
                room_id = str(user_info.get("roomId", ""))
                
                if user_id and room_id and room_id != "0":
                    print(f"[✓] Got room ID via Webcast API-Live!")
                    return user_id, room_id
                elif user_id and (not room_id or room_id == "0"):
                    print(f"[!] TikTok API confirms @{username} is currently OFFLINE.")
                    return user_id, ""
    except Exception as e:
        print(f"[~] Webcast API-Live error: {e}")

    # Method 2: Fallback to HTML scraping if API fails or returns offline (in case profile contains different info)
    html = _fetch_profile_html(username)
    if "SlardarWAF" in html or "slardar_us_waf" in html:
        raise TikTokError(
            "TikTok blocked this automated request before returning profile data. "
            "Open the profile in a normal browser to confirm whether the account exists "
            "and whether it is live."
        )

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
    android_versions = ["10", "11", "12", "13", "14"]
    android_apis = ["29", "30", "31", "32", "33", "34"]
    model = random.choice(DEVICE_TYPES)
    android_ver = random.choice(android_versions)
    api_level = random.choice(android_apis)
    build_id = ''.join(random.choices(string.ascii_uppercase + string.digits, k=random.randint(6, 10)))
    app_ver = random.choice(UA_APP_VERSIONS)
    ttnet_ver = random.choice(UA_TTNET_VERSIONS)
    quic_ver = random.choice(UA_QUIC_VERSIONS)
    return f"com.zhiliaoapp.musically/{app_ver} (Linux; U; Android {android_ver}; {api_level}; en; {model}; Build/{build_id}; Cronet/TTNetVersion:{ttnet_ver} QuicVersion:{quic_ver})"


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
        'device_type': random.choice(DEVICE_TYPES),
        'device_brand': random.choice(DEVICE_BRANDS),
        'language': "en",
        'os_api': str(random.randint(28, 34)),
        'os_version': str(random.randint(10, 14)),
        'openudid': binascii.hexlify(os.urandom(8)).decode(),
        'manifest_version_code': str(random.randint(2022000000, 2024999999)),
        'resolution': random.choice(["1080*2400", "720*1600", "1440*3200"]),
        'dpi': str(random.choice([240, 320, 480])),
        'update_version_code': str(random.randint(2022000000, 2024999999)),
        '_rticket': str(int(time.time() * 1000)),
        'app_type': "normal",
        'sys_region': random.choice(REGIONS),
        'mcc_mnc': str(random.randint(10000, 99999)),
        'timezone_name': random.choice(["Africa/Cairo", "Asia/Baghdad", "Europe/Paris"]),
        'carrier_region_v2': str(random.randint(100, 999)),
        'app_language': "en",
        'carrier_region': random.choice(REGIONS),
        'ac2': random.choice(["wifi", "4g", "5g"]),
        'uoo': "0",
        'op_region': random.choice(REGIONS),
        'timezone_offset': str(random.choice([7200, 10800, 3600])),
        'build_number': "28.6.5",
        'host_abi': "arm64-v8a",
        'locale': "en",
        'region': random.choice(REGIONS),
        'ts': int(time.time()),
        'cdid': str(uuid.uuid4()),
        'webcast_language': "en",
        'webcast_locale': "en_US",
        'effect_sdk_version': "1.3.0"
    }


def send_comment_thread(user_id: str, room_id: str, words: Set[str]) -> bool:
    time.sleep(random.uniform(0.01, 0.5))
    global comment_success, comment_failed
    max_retries = 3
    retry_delay = 2
    
    for attempt in range(max_retries):
        try:
            sess = curl_requests.Session()
            ss = random.choice(SESSION_IDS)
            secret = secrets.token_hex(16)
            sess.cookies.update({
                "passport_csrf_token": secret,
                "passport_csrf_token_default": secret,
                "sessionid": ss,
            })
            host = random.choice(["22", "21", "16", "15", "19"])
            url = f"https://webcast{host}-normal-c-alisg.tiktokv.com/webcast/room/chat/"
            params = build_params()
            cmm = random.choice(list(words))
            payload = {
                'room_id': room_id,
                'emotes_with_index': "",
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
            # proxy_str = random.choice(PROXY_LIST)
            # proxies = get_proxy_dict(proxy_str)
            resp = sess.post(url, params=params, data=payload, headers=headers, proxies=None, impersonate='chrome120', timeout=15)
            response_text = resp.text
            ok = resp.status_code == 200 and ("id" in response_text or "msg_id" in response_text)
            
            with count_lock:
                if ok:
                    comment_success += 1
                    print(f"\r[+] Comment - Success: {comment_success} | Failed: {comment_failed}", end="", flush=True)
                    return True
                else:
                    comment_failed += 1
            
            if attempt < max_retries - 1:
                time.sleep(2 ** attempt)
                
        except Exception as e:
            with count_lock:
                comment_failed += 1
            if attempt < max_retries - 1:
                time.sleep(2 ** attempt)
            continue
    
    print(f"\r[+] Comment - Success: {comment_success} | Failed: {comment_failed}", end="", flush=True)
    return False


def send_like_thread(user_id: str, room_id: str) -> bool:
    time.sleep(random.uniform(0.01, 0.5))
    global like_success, like_failed
    max_retries = 3
    
    for attempt in range(max_retries):
        try:
            sess = curl_requests.Session()
            ss = random.choice(SESSION_IDS)
            secret = secrets.token_hex(16)
            sess.cookies.update({
                "passport_csrf_token": secret,
                "passport_csrf_token_default": secret,
                "sessionid": ss,
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
            # proxy_str = random.choice(PROXY_LIST)
            # proxies = get_proxy_dict(proxy_str)
            resp = sess.post(url, params=params, data=payload, headers=headers, proxies=None, impersonate='chrome120', timeout=15)
            ok = resp.status_code == 200
            
            with count_lock:
                if ok:
                    like_success += 1
                    print(f"\r[+] Like - Success: {like_success} | Failed: {like_failed}", end="", flush=True)
                    return True
                else:
                    like_failed += 1
            
            if attempt < max_retries - 1:
                time.sleep(retry_delay)
                
        except Exception as e:
            with count_lock:
                like_failed += 1
            if attempt < max_retries - 1:
                time.sleep(retry_delay)
            continue
    
    print(f"\r[+] Like - Success: {like_success} | Failed: {like_failed}", end="", flush=True)
    return False


def run_automation(username: str, mode: str, count: int = 1000) -> dict:
    global comment_success, comment_failed, like_success, like_failed
    comment_success = 0
    comment_failed = 0
    like_success = 0
    like_failed = 0
    
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
            return {"status": "error", "message": "User is not live"}
            
        print(f"[✓] Room ID: {room_id}")
        print("=" * 50)
        
        with ThreadPoolExecutor(max_workers=100) as executor:
            futures = []
            if mode == "1":
                print("[*] Starting COMMENT flood...")
                futures = [executor.submit(send_comment_thread, user_id, room_id, words) for _ in range(count)]
            elif mode == "2":
                print("[*] Starting LIKE flood...")
                futures = [executor.submit(send_like_thread, user_id, room_id) for _ in range(count)]
            elif mode == "3":
                print("[*] Starting BOTH Comments & Likes flood...")
                half = count // 2
                for _ in range(half):
                    futures.append(executor.submit(send_comment_thread, user_id, room_id, words))
                    futures.append(executor.submit(send_like_thread, user_id, room_id))
            else:
                print("Invalid mode selected.")
                return {"status": "error", "message": "Invalid mode"}
                
            for future in as_completed(futures):
                pass
                
        print("\n" + "=" * 50)
        if mode in ["1", "3"]:
            print(f"[✓] Comments Final - Success: {comment_success} | Failed: {comment_failed}")
        if mode in ["2", "3"]:
            print(f"[✓] Likes Final - Success: {like_success} | Failed: {like_failed}")
            
        return {
            "status": "success",
            "comments_success": comment_success,
            "comments_failed": comment_failed,
            "likes_success": like_success,
            "likes_failed": like_failed
        }
            
    except TikTokError as e:
        print(e)
        return {"status": "error", "message": str(e)}
    except requests.RequestException as e:
        print(f"Network error: {e}")
        return {"status": "error", "message": str(e)}

def main() -> None:
    username = clean_username(input("username : "))
    mode = input("Select Mode [1: Comments] [2: Likes] [3: Both]: ").strip()
    run_automation(username, mode, count=1000)

if __name__ == "__main__":
    main()
