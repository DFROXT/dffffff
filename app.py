import os
import time
import threading
import requests
import re
import json
from flask import Flask, render_template, jsonify
from datetime import datetime

app = Flask(__name__)

# ========== CONFIG ==========
# Render ke environment variables me ye daalna:
# EMAIL, PASSWORD (optional, default hardcoded hai)
EMAIL = os.getenv("EMAIL", "fucyt30@gmail.com")
PASSWORD = os.getenv("PASSWORD", "Vedxotp739π÷÷÷")
BASE_URL = "https://www.ivasms.com"

# Session
session = requests.Session()

# Data storage
nodes = set()          # unique numbers
logs = []              # OTPs with timestamp
seen_ids = set()       # to avoid duplicates

# ========== IVASMS LOGIN ==========
def login():
    try:
        r = session.get(f"{BASE_URL}/login", timeout=10)
        match = re.search(r'name="_token".*?value="([^"]+)"', r.text)
        if not match:
            return False
        token = match.group(1)
        data = {'_token': token, 'email': EMAIL, 'password': PASSWORD, 'remember': '1'}
        headers = {'Content-Type': 'application/x-www-form-urlencoded'}
        resp = session.post(f"{BASE_URL}/login", data=data, headers=headers, timeout=15)
        return 'portal' in resp.url or resp.status_code == 200
    except Exception as e:
        print("Login error:", e)
        return False

# ========== FETCH NUMBERS & OTPs ==========
def fetch_data():
    global nodes, logs, seen_ids
    if not login():
        return
    try:
        params = {
            "app": "WhatsApp",
            "draw": 1,
            "start": 0,
            "length": 150,
            "_": int(time.time() * 1000)
        }
        headers = {'X-Requested-With': 'XMLHttpRequest'}
        resp = session.get(f"{BASE_URL}/portal/sms/test/sms", params=params, headers=headers, timeout=15)
        data = resp.json().get('data', [])
        for msg in data:
            num = msg.get('termination', {}).get('test_number') or msg.get('test_number', '')
            txt = msg.get('messagedata', '')
            mid = msg.get('id', '')
            if num:
                nodes.add(num)
            if mid and mid not in seen_ids:
                otp_match = re.search(r'\b(\d{4,8})\b', txt)
                if otp_match:
                    logs.append({
                        'number': num,
                        'otp': otp_match.group(1),
                        'time': datetime.now().strftime('%H:%M')
                    })
                seen_ids.add(mid)
        # keep only last 100 logs
        if len(logs) > 100:
            logs[:] = logs[-100:]
    except Exception as e:
        print("Fetch error:", e)

# ========== BACKGROUND THREAD ==========
def background_loop():
    while True:
        fetch_data()
        time.sleep(45)   # har 45 sec

threading.Thread(target=background_loop, daemon=True).start()

# ========== ROUTES ==========
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/stats')
def stats():
    return jsonify({
        "nodes": len(nodes),
        "logs": len(logs),
        "status": "online"
    })

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
