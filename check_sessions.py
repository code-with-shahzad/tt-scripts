import re
import time
try:
    from curl_cffi import requests
except ImportError:
    import requests

def check_session(sess):
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
            return True
        return False
    except Exception as e:
        return False

def main():
    with open("new.py", "r") as f:
        content = f.read()

    # Extract sessions
    sessions_match = re.search(r'SESSION_IDS = \[(.*?)\]', content, re.S)
    sessions = []
    if sessions_match:
        sessions = re.findall(r'"([a-f0-9]{32})"', sessions_match.group(1))

    print(f"[*] Found {len(sessions)} session IDs in new.py")
    print("[*] Checking sessions locally (No proxies, slow mode to avoid false bans)... Please wait.")

    valid_sessions = []
    invalid_sessions = []

    for i, sess in enumerate(sessions):
        print(f"Checking {i+1}/{len(sessions)}... ", end="\r")
        is_valid = check_session(sess)
        if is_valid:
            valid_sessions.append(sess)
        else:
            invalid_sessions.append(sess)
        time.sleep(1.5) # Sleep 1.5s to absolutely guarantee no local rate limit false negatives

    print("\n" + "="*50)
    print(f"[✓] Valid Sessions (Alive): {len(valid_sessions)}")
    print(f"[x] Invalid Sessions (Dead/Expired): {len(invalid_sessions)}")
    print("="*50)

if __name__ == "__main__":
    main()
