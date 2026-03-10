import os, time, threading, requests, re, json
from flask import Flask, render_template, jsonify
from datetime import datetime
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
from telegram.constants import ParseMode

app = Flask(__name__)

# ========== ANONYMOUS CONFIG ==========
# RENDER PAR CONFIG VARS MA 'BOT_TOKEN' ADD KARJO
BOT_TOKEN = os.getenv("BOT_TOKEN")
OPENROUTER_KEY = "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"
AI_MODEL = "google/gemini-2.0-flash-001"

EMAIL = "fucyt30@gmail.com"
PASS = "Vedxotp739π÷÷÷"
URL = "https://www.ivasms.com"

# SYSTEM STORAGE
SESS = requests.Session()
NODES = set()
LOGS = []
SEEN = set()

# ========== CORE LOGIC ==========

def gateway_login():
    try:
        r = SESS.get(f"{URL}/login", timeout=10)
        tok = re.search(r'name="_token" value="([^"]+)"', r.text).group(1)
        data = {'_token': tok, 'email': EMAIL, 'password': PASS, 'remember': '1'}
        res = SESS.post(f"{URL}/login", data=data, timeout=15)
        return 'portal' in res.url or res.status_code == 200
    except: return False

def deep_sync():
    global NODES, LOGS, SEEN
    if not gateway_login(): return
    try:
        p = {"app": "WhatsApp", "draw": 1, "start": 0, "length": 150}
        h = {'X-Requested-With': 'XMLHttpRequest'}
        r = SESS.get(f"{URL}/portal/sms/test/sms", params=p, headers=h, timeout=15)
        raw = r.json().get('data', [])
        for i in raw:
            n = str(i.get('termination', {}).get('test_number') or i.get('test_number', ''))
            txt = str(i.get('messagedata', ''))
            mid = str(i.get('id', ''))
            if n: NODES.add(n)
            if mid not in SEEN:
                otp = re.search(r'\b(\d{4,8})\b', txt)
                if otp: LOGS.append({'n': n, 'o': otp.group(1), 't': datetime.now().strftime('%H:%M')})
                SEEN.add(mid)
    except: pass

# ========== WEB ROUTES ==========

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/stats')
def get_stats():
    return jsonify({
        "nodes": len(NODES),
        "logs": len(LOGS),
        "status": "online"
    })

# ========== TELEGRAM BOT RUNNER ==========

def run_bot():
    if not BOT_TOKEN:
        print("❌ BOT_TOKEN NOT FOUND IN ENV!")
        return
    application = Application.builder().token(BOT_TOKEN).build()
    application.add_handler(CommandHandler("start", lambda u,c: u.message.reply_text("🟢 ANONYMOUS ONLINE")))
    # ADD OTHER HANDLERS HERE...
    application.run_polling()

if __name__ == "__main__":
    # START BACKGROUND SYNC
    threading.Thread(target=lambda: [(deep_sync(), time.sleep(45)) for _ in iter(int, 1)], daemon=True).start()
    # START BOT IN THREAD
    threading.Thread(target=run_bot, daemon=True).start()
    # START WEB SERVER
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 5000)))
