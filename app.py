from flask import Flask, request, redirect, send_from_directory, render_template
import logging
import os
import sqlite3
from datetime import datetime
from twilio.rest import Client
from dotenv import load_dotenv

# ------------------- Setup -------------------
load_dotenv()
app = Flask(__name__)

# ------------------- Logging -------------------
logging.basicConfig(
    filename='security.log',
    level=logging.INFO,
    format='%(asctime)s - %(message)s'
)

# ------------------- Twilio -------------------
TWILIO_SID = os.getenv("TWILIO_ACCOUNT_SID")
TWILIO_AUTH = os.getenv("TWILIO_AUTH_TOKEN")
TWILIO_FROM = os.getenv("TWILIO_FROM")
TWILIO_TO = os.getenv("TWILIO_TO")

client = Client(TWILIO_SID, TWILIO_AUTH)

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

# ------------------- Database -------------------
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

# ------------------- Routes -------------------

@app.route('/')
def home():
    return render_template('login.html', error=None)

@app.route('/login', methods=['POST'])
def login():
    username = request.form.get('username')
    password = request.form.get('password')
    ip = request.remote_addr
    user_agent = request.headers.get('User-Agent')

    # Check credentials from DB
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

