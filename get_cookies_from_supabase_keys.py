#!/usr/bin/env python3
# get_cookies_from_supabase_keys.py - Usa due progetti Supabase distinti

import requests
import time
from datetime import datetime
from supabase import create_client

# ==================== CONFIGURAZIONE DUE PROGETTI ====================
# Progetto 1: dove risiedono le chiavi Browserless (tabella browserless_keys)
SUPABASE_KEYS_URL = "https://lmtmjfrhzbjtayjwcpsq.supabase.co"
SUPABASE_KEYS_SERVICE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImxtdG1qZnJoemJqdGF5andjcHNxIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc3NTEyNDc4MCwiZXhwIjoyMDkwNzAwNzgwfQ.2mPQPwTlCK0JHbX27cOM8b_Sbu9KRtBXMVbOh46_o1o"   # <-- SOSTITUISCI

# Progetto 2: dove salvare i cookie (tabella account_cookies)
SUPABASE_COOKIES_URL = "https://ofijopixtpwahgbwyutc.supabase.co"
SUPABASE_COOKIES_SERVICE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im9maWpvcGl4dHB3YWhnYnd5dXRjIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc3NTkyODIxMiwiZXhwIjoyMDkxNTA0MjEyfQ.BkWb8EuUUJSUUgg3sepDmOdUzsXY7pjGjykQnPMK9q4"   # <-- SOSTITUISCI

ACCOUNT_NAME = "main"
EASYHITS_EMAIL = "sandrominori50+uiszuzoqatr@gmail.com"
EASYHITS_PASSWORD = "DDnmVV45!!"
REFERER_URL = "https://www.easyhits4u.com/?ref=nicolacaporale"
BROWSERLESS_URL = "https://production-sfo.browserless.io/chrome/bql"

def log(msg):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}", flush=True)

def get_cf_token(api_key):
    query = """
    mutation {
      goto(url: "https://www.easyhits4u.com/logon/", waitUntil: networkIdle, timeout: 60000) {
        status
      }
      solve(type: cloudflare, timeout: 60000) {
        solved
        token
        time
      }
    }
    """
    url = f"{BROWSERLESS_URL}?token={api_key}"
    try:
        start = time.time()
        response = requests.post(url, json={"query": query}, headers={"Content-Type": "application/json"}, timeout=120)
        if response.status_code != 200:
            return None
        data = response.json()
        if "errors" in data:
            return None
        solve_info = data.get("data", {}).get("solve", {})
        if solve_info.get("solved"):
            token = solve_info.get("token")
            log(f"   ✅ Token ({time.time()-start:.1f}s)")
            return token
        return None
    except Exception as e:
        log(f"   ❌ Errore token: {e}")
        return None

def login_and_get_cookies(api_key):
    session = requests.Session()
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Firefox/148.0',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'it-IT,it;q=0.8,en-US;q=0.5,en;q=0.3',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
    }
    # GET homepage
    session.get("https://www.easyhits4u.com/", headers=headers, verify=False, timeout=15)
    time.sleep(1)
    token = get_cf_token(api_key)
    if not token:
        return None
    login_headers = headers.copy()
    login_headers['Content-Type'] = 'application/x-www-form-urlencoded'
    login_headers['Referer'] = REFERER_URL
    data = {
        'manual': '1',
        'fb_id': '',
        'fb_token': '',
        'google_code': '',
        'username': EASYHITS_EMAIL,
        'password': EASYHITS_PASSWORD,
        'cf-turnstile-response': token,
    }
    login_resp = session.post("https://www.easyhits4u.com/logon/", data=data, headers=login_headers, allow_redirects=True, timeout=30)
    if login_resp.status_code != 200:
        return None
    time.sleep(2)
    session.get("https://www.easyhits4u.com/member/", headers=headers, verify=False, timeout=15)
    time.sleep(1)
    session.get("https://www.easyhits4u.com/surf/", headers=headers, verify=False, timeout=15)
    time.sleep(1)
    session.get(REFERER_URL, headers=headers, verify=False, timeout=15)
    cookies = session.cookies.get_dict()
    if 'user_id' in cookies and 'sesids' in cookies:
        cookies['surftype'] = '2'
        cookie_string = '; '.join([f"{k}={v}" for k, v in cookies.items()])
        return cookie_string, cookies['user_id'], cookies['sesids']
    return None

def main():
    log("=" * 50)
    log("🚀 GENERATORE COOKIE (CHIAVI DA SUPABASE PROGETTO KEYS)")
    log("=" * 50)

    # Client per leggere le chiavi Browserless
    supabase_keys = create_client(SUPABASE_KEYS_URL, SUPABASE_KEYS_SERVICE_KEY)
    keys_resp = supabase_keys.table('browserless_keys')\
        .select('id', 'api_key')\
        .eq('status', 'working')\
        .execute()
    if not keys_resp.data:
        log("❌ Nessuna chiave 'working' trovata nella tabella browserless_keys (progetto keys)")
        return
    keys = keys_resp.data
    log(f"🔑 Trovate {len(keys)} chiavi 'working'")

    # Client per scrivere i cookie
    supabase_cookies = create_client(SUPABASE_COOKIES_URL, SUPABASE_COOKIES_SERVICE_KEY)

    for key_record in keys:
        key_id = key_record['id']
        api_key = key_record['api_key']
        log(f"🔑 Tentativo con chiave: {api_key[:10]}...")
        result = login_and_get_cookies(api_key)
        if result:
            cookie_string, uid, sid = result
            log(f"🎉 Cookie ottenuti! user_id={uid}, sesids={sid}")
            supabase_cookies.table('account_cookies').upsert({
                'account_name': ACCOUNT_NAME,
                'cookie_string': cookie_string,
                'user_id': uid,
                'sesids': sid,
                'status': 'active',
                'updated_at': datetime.now().isoformat()
            }, on_conflict='account_name').execute()
            log("✅ Cookie salvati su Supabase (progetto cookies)")
            # Opzionale: segna la chiave come 'used' nel progetto keys
            supabase_keys.table('browserless_keys')\
                .update({'status': 'used'})\
                .eq('id', key_id)\
                .execute()
            return
        else:
            log(f"   ❌ Fallito, marco chiave come 'broken'")
            supabase_keys.table('browserless_keys')\
                .update({'status': 'broken'})\
                .eq('id', key_id)\
                .execute()
    log("❌ Nessuna chiave funzionante, impossibile generare cookie")

if __name__ == "__main__":
    main()
