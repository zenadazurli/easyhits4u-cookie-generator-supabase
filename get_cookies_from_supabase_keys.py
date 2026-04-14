#!/usr/bin/env python3
# get_cookies_from_supabase_keys.py - Con log dettagliati delle chiavi

import re
import requests
import time
from datetime import datetime
from supabase import create_client

# ==================== CONFIGURAZIONE ====================
SUPABASE_KEYS_URL = "https://lmtmjfrhzbjtayjwcpsq.supabase.co"
SUPABASE_KEYS_SERVICE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImxtdG1qZnJoemJqdGF5andjcHNxIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc3NTEyNDc4MCwiZXhwIjoyMDkwNzAwNzgwfQ.2mPQPwTlCK0JHbX27cOM8b_Sbu9KRtBXMVbOh46_o1o"

SUPABASE_COOKIES_URL = "https://ofijopixtpwahgbwyutc.supabase.co"
SUPABASE_COOKIES_SERVICE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im9maWpvcGl4dHB3YWhnYnd5dXRjIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc3NTkyODIxMiwiZXhwIjoyMDkxNTA0MjEyfQ.BkWb8EuUUJSUUgg3sepDmOdUzsXY7pjGjykQnPMK9q4"


ACCOUNT_NAME = "main"
EASYHITS_EMAIL = "sandrominori50+uiszuzoqatr@gmail.com"
EASYHITS_PASSWORD = "DDnmVV45!!"
REFERER_URL = "https://www.easyhits4u.com/?ref=nicolacaporale"
BROWSERLESS_URL = "https://production-sfo.browserless.io/chrome/bql"

def clean_key(api_key):
    """Pulisce la chiave: rimuove spazi, newline, caratteri invisibili"""
    if not api_key:
        return None
    cleaned = re.sub(r'[\s\r\n\t]', '', str(api_key))
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
    log("=" * 60)
    log("🚀 GENERATORE COOKIE - LOG DETTAGLIATO")
    log("=" * 60)

    # Connessione a Supabase (progetto chiavi)
    log("📡 Connessione a Supabase (progetto keys)...")
    try:
        supabase_keys = create_client(SUPABASE_KEYS_URL, SUPABASE_KEYS_SERVICE_KEY)
        log("✅ Connessione riuscita")
    except Exception as e:
        log(f"❌ Errore connessione a Supabase keys: {e}")
        return

    # Verifica la tabella browserless_keys
    log("📊 Verifico tabella 'browserless_keys'...")
    try:
        # Prova a leggere una riga qualsiasi
        test_resp = supabase_keys.table('browserless_keys').select('count').limit(1).execute()
        log(f"✅ Tabella accessibile. Count: {test_resp.count if hasattr(test_resp, 'count') else 'N/A'}")
    except Exception as e:
        log(f"❌ Errore accesso tabella: {e}")
        return

    # Prendi TUTTE le chiavi (senza filtro status per debug)
    log("🔍 Cerco TUTTE le chiavi (senza filtro status)...")
    resp = supabase_keys.table('browserless_keys')\
        .select('id', 'api_key', 'status')\
        .execute()
    
    all_keys = resp.data
    log(f"📋 Trovate {len(all_keys)} chiavi TOTALI nel database")
    
    if not all_keys:
        log("❌ Nessuna chiave trovata nel database!")
        log("   Verifica che la tabella 'browserless_keys' contenga dati.")
        return
    
    # Mostra le prime 10 chiavi (con status)
    log("\n📋 PRIME 10 CHIAVI (ID, status, key[:20]):")
    for i, k in enumerate(all_keys[:10]):
        log(f"   {i+1}. ID={k['id']}, status='{k['status']}', key={k['api_key'][:20]}...")
    
    # Conta per status
    status_count = {}
    for k in all_keys:
        s = k.get('status', 'unknown')
        status_count[s] = status_count.get(s, 0) + 1
    log(f"\n📊 STATISTICHE PER STATUS:")
    for s, count in status_count.items():
        log(f"   {s}: {count}")
    
    # Filtra chiavi con status 'working' o 'untested'
    working_untested = [k for k in all_keys if k.get('status') in ['working', 'untested']]
    log(f"\n🔑 Chiavi con status 'working' o 'untested': {len(working_untested)}")
    
    if not working_untested:
        log("❌ Nessuna chiave 'working' o 'untested' trovata!")
        log("   Esegui prima il tester avanzato per aggiornare gli status.")
        return
    
    # Pulisci e testa le chiavi
    log("\n🔧 Pulizia e test delle chiavi...")
    for key_record in working_untested[:10]:  # Test solo prime 10 per velocità
        key_id = key_record['id']
        raw_key = key_record['api_key']
        old_status = key_record['status']
        
        log(f"\n🔑 ID={key_id}, status={old_status}")
        log(f"   Raw key: '{raw_key}' (len={len(raw_key)})")
        
        cleaned = clean_key(raw_key)
        if cleaned:
            log(f"   Cleaned: '{cleaned[:20]}...' (len={len(cleaned)})")
            if cleaned != raw_key:
                log(f"   ⚠️ CHIAVE MODIFICATA! Aggiorno database...")
                supabase_keys.table('browserless_keys')\
                    .update({'api_key': cleaned})\
                    .eq('id', key_id)\
                    .execute()
        else:
            log(f"   ❌ Chiave non valida dopo pulizia!")
            continue
        
        # Testa la chiave
        log(f"   🔍 Test login con questa chiave...")
        result = login_and_get_cookies(cleaned)
        if result:
            cookie_string, uid, sid = result
            log(f"   🎉 SUCCESSO! Cookie ottenuti per chiave {cleaned[:10]}...")
            # Salva su Supabase (progetto cookies)
            supabase_cookies = create_client(SUPABASE_COOKIES_URL, SUPABASE_COOKIES_SERVICE_KEY)
            supabase_cookies.table('account_cookies').upsert({
                'account_name': ACCOUNT_NAME,
                'cookie_string': cookie_string,
                'user_id': uid,
                'sesids': sid,
                'status': 'active',
                'updated_at': datetime.now().isoformat()
            }, on_conflict='account_name').execute()
            log("   ✅ Cookie salvati su Supabase")
            return
        else:
            log(f"   ❌ Login fallito per questa chiave")
    
    log("\n❌ Nessuna chiave funzionante tra le prime 10 testate")
    log("   Se vuoi testare TUTTE le chiavi, modifica il limite nel codice.")

if __name__ == "__main__":
    main()
