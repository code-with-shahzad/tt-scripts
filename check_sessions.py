import re
import random
from concurrent.futures import ThreadPoolExecutor
try:
    from curl_cffi import requests
except ImportError:
    import requests

def get_proxy_dict(proxy_str):
    parts = proxy_str.split(':')
    if len(parts) == 4:
        ip, port, user, password = parts
        proxy_url = f"http://{user}:{password}@{ip}:{port}"
        return {"http": proxy_url, "https": proxy_url}
    return None

def check_session(sess, proxies_raw):
    proxy_str = random.choice(proxies_raw) if proxies_raw else None
    proxy_dict = get_proxy_dict(proxy_str) if proxy_str else None
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "application/json, text/plain, */*"
    }
    try:
        sess_obj = requests.Session()
        resp = sess_obj.get(
            "https://www.tiktok.com/passport/web/account/info/?aid=1459&app_language=en&app_name=tiktok_web",
            cookies={"sessionid": sess},
            headers=headers,
            proxies=None,
            impersonate="chrome120",
            timeout=10
        )
        data = resp.json()
        if data.get("data", {}).get("user_id"):
            return sess, True
        return sess, False
    except Exception as e:
        return sess, False

def main():
    with open("new.py", "r") as f:
        content = f.read()

    # Extract sessions
    sessions_match = re.search(r'SESSION_IDS = \[(.*?)\]', content, re.S)
    sessions = []
    if sessions_match:
        sessions = re.findall(r'"([a-f0-9]{32})"', sessions_match.group(1))

    # Extract proxies
    proxies_match = re.search(r'PROXY_LIST = \[(.*?)\]', content, re.S)
    proxies_raw = []
    if proxies_match:
        proxies_raw = re.findall(r'"([^"]+)"', proxies_match.group(1))

    print(f"[*] Found {len(sessions)} session IDs and {len(proxies_raw)} proxies in new.py")
    print("[*] Checking sessions... Please wait.")

    valid_sessions = []
    invalid_sessions = []

    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(check_session, sess, proxies_raw) for sess in sessions]
        for future in futures:
            sess, is_valid = future.result()
            if is_valid:
                valid_sessions.append(sess)
            else:
                invalid_sessions.append(sess)

    print("\n" + "="*50)
    print(f"[✓] Valid Sessions (Alive): {len(valid_sessions)}")
    print(f"[x] Invalid Sessions (Dead/Expired): {len(invalid_sessions)}")
    print("="*50)

if __name__ == "__main__":
    main()
