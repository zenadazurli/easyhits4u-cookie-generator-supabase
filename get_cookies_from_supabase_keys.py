#!/usr/bin/env python3
# get_cookies_from_supabase_keys.py - Con pulizia delle chiavi

import re
import requests
import time
from datetime import datetime
from supabase import create_client

# ==================== CONFIGURAZIONE ====================
SUPABASE_KEYS_URL = "https://lmtmjfrhzbjtayjwcpsq.supabase.co"
SUPABASE_KEYS_SERVICE_KEY = "la_tua_service_key"

SUPABASE_COOKIES_URL = "https://ofijopixtpwahgbwyutc.supabase.co"
SUPABASE_COOKIES_SERVICE_KEY = "la_tua_service_key_cookies"

ACCOUNT_NAME = "main"
EASYHITS_EMAIL = "sandrominori50+uiszuzoqatr@gmail.com"
EASYHITS_PASSWORD = "DDnmVV45!!"
REFERER_URL = "https://www.easyhits4u.com/?ref=nicolacaporale"
BROWSERLESS_URL = "https://production-sfo.browserless.io/chrome/bql"

def clean_key(api_key):
    """Pulisce la chiave: rimuove spazi, newline, caratteri invisibili"""
    if not api_key:
        return None
    # Rimuove spazi, tab, newline, carriage return
    cleaned = re.sub(r'[\s\r\n\t]', '', str(api_key))
    # Se la chiave sembra valida (inizia con 2U e ha almeno 40 caratteri)
    if cleaned.startswith('2U') and len(cleaned) >= 40:
        return cleaned
    return None

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
    log("🚀 GENERATORE COOKIE (CHIAVI DA SUPABASE CON PULIZIA)")
    log("=" * 50)

    supabase_keys = create_client(SUPABASE_KEYS_URL, SUPABASE_KEYS_SERVICE_KEY)
    supabase_cookies = create_client(SUPABASE_COOKIES_URL, SUPABASE_COOKIES_SERVICE_KEY)

    # Prendi le chiavi con status 'working' (o 'untested')
    resp = supabase_keys.table('browserless_keys')\
        .select('id', 'api_key', 'status')\
        .in_('status', ['working', 'untested'])\
        .execute()
    
    keys = resp.data
    if not keys:
        log("❌ Nessuna chiave 'working' o 'untested' trovata")
        return
    
    log(f"🔑 Trovate {len(keys)} chiavi. Pulizia in corso...")
    
    valid_keys = []
    for k in keys:
        cleaned = clean_key(k['api_key'])
        if cleaned:
            if cleaned != k['api_key']:
                log(f"   🧹 Pulita chiave {k['api_key'][:10]}... -> {cleaned[:10]}...")
                # Aggiorna la chiave pulita nel database
                supabase_keys.table('browserless_keys')\
                    .update({'api_key': cleaned})\
                    .eq('id', k['id'])\
                    .execute()
            valid_keys.append((k['id'], cleaned))
        else:
            log(f"   ⚠️ Chiave non valida (scartata): {k['api_key'][:20]}...")
            supabase_keys.table('browserless_keys')\
                .update({'status': 'invalid_format'})\
                .eq('id', k['id'])\
                .execute()
    
    log(f"🔑 Chiavi valide dopo pulizia: {len(valid_keys)}")
    
    for key_id, api_key in valid_keys:
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
            log("✅ Cookie salvati su Supabase")
            # Opzionale: segna la chiave come 'used'
            supabase_keys.table('browserless_keys')\
                .update({'status': 'used', 'last_used': datetime.now().isoformat()})\
                .eq('id', key_id)\
                .execute()
            return
        else:
            log(f"   ❌ Fallito, marco chiave come 'broken'")
            supabase_keys.table('browserless_keys')\
                .update({'status': 'broken', 'last_tested': datetime.now().isoformat()})\
                .eq('id', key_id)\
                .execute()
    
    log("❌ Nessuna chiave funzionante, impossibile generare cookie")

if __name__ == "__main__":
    main()
