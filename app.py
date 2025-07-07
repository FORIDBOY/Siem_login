from flask import Flask, request, redirect, send_from_directory, render_template
import logging
from datetime import datetime
from twilio.rest import Client
import os
import sqlite3
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

# ------------------- Database Setup -------------------
def init_db():
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
    ''')
    conn.commit()
    conn.close()

init_db()

# ------------------- Helper Functions -------------------
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

def check_credentials(username, password):
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE username = ? AND password = ?", (username, password))
    result = c.fetchone()
    conn.close()
    return result

def user_exists(username):
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE username = ?", (username,))
    result = c.fetchone()
    conn.close()
    return result

def add_user(username, password):
    try:
        conn = sqlite3.connect('users.db')
        c = conn.cursor()
        c.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, password))
        conn.commit()
        conn.close()
        return True
    except:
        return False

# ------------------- Routes -------------------

@app.route('/')
def home():
    return render_template('login.html')

@app.route('/login', methods=['POST'])
def login():
    username = request.form.get('username')
    password = request.form.get('password')
    ip = request.remote_addr
    user_agent = request.headers.get('User-Agent')

    if check_credentials(username, password):
        logging.info(f"SUCCESS_LOGIN | User: {username} | IP: {ip} | Agent: {user_agent}")
        return redirect('/static/info.html')
    else:
        logging.warning(f"FAILED_LOGIN | User: {username} | IP: {ip} | Agent: {user_agent}")
        send_sms_alert(f"🚨 FAILED_LOGIN from IP {ip} | User: {username}")
        return render_template('login.html', error="Wrong username or password!")

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        if user_exists(username):
            return render_template('register.html', error="Username already exists!")
        elif add_user(username, password):
            return redirect('/')
        else:
            return render_template('register.html', error="Registration failed.")
    return render_template('register.html')

@app.route('/<path:filename>')
def serve_static(filename):
    return send_from_directory('static', filename)

# ------------------- Run the App -------------------
if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))  # Render sets PORT automatically
    app.run(host='0.0.0.0', port=port)


