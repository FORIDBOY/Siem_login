from flask import Flask, request, redirect, send_from_directory
import logging
from datetime import datetime
from twilio.rest import Client
import sqlite3
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = Flask(__name__)

# ------------------- Logging Configuration -------------------
logging.basicConfig(
    filename='security.log',
    level=logging.INFO,
    format='%(asctime)s - %(message)s'
)

# ------------------- Twilio Configuration -------------------
TWILIO_SID = os.getenv("TWILIO_ACCOUNT_SID")
TWILIO_AUTH = os.getenv("TWILIO_AUTH_TOKEN")
TWILIO_FROM = os.getenv("TWILIO_FROM")
TWILIO_TO = os.getenv("TWILIO_TO")

client = Client(TWILIO_SID, TWILIO_AUTH)

# ------------------- SQLite DB Initialization -------------------
def init_db():
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
    ''')
    conn.commit()
    conn.close()

init_db()

# ------------------- Utility -------------------
def send_sms_alert(message):
    try:
        client.messages.create(
            body=message,
            from_=TWILIO_FROM,
            to=TWILIO_TO
        )
        print("[+] SMS Alert Sent")
    except Exception as e:
        print(f"[!] Failed to send SMS: {e}")

# ------------------- Routes -------------------

@app.route('/')
def home():
    return open('templates/login.html').read()

@app.route('/login', methods=['POST'])
def login():
    username = request.form.get('username')
    password = request.form.get('password')
    ip = request.remote_addr
    user_agent = request.headers.get('User-Agent')

    # Check user from DB
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE username=? AND password=?", (username, password))
    user = cursor.fetchone()
    conn.close()

    if user:
        logging.info(f"SUCCESS_LOGIN | User: {username} | IP: {ip} | Agent: {user_agent}")
        return redirect('/static/info.html')
    else:
        logging.warning(f"FAILED_LOGIN | User: {username} | IP: {ip} | Agent: {user_agent}")
        send_sms_alert(f"🚨 FAILED_LOGIN from IP {ip} | User: {username}")
        return open('templates/login.html').read()

@app.route('/create')
def create_account():
    return open('templates/create_account.html').read()

@app.route('/register', methods=['POST'])
def register():
    username = request.form.get('username')
    password = request.form.get('password')

    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, password))
        conn.commit()
        conn.close()
        return "✅ Account created! <a href='/'>Login now</a>"
    except sqlite3.IntegrityError:
        conn.close()
        return "❌ Username already exists! <a href='/create'>Try again</a>"

@app.route('/<path:filename>')
def serve_static(filename):
    return send_from_directory('static', filename)

# ------------------- Run App -------------------
if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
