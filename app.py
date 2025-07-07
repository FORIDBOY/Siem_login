from flask import Flask, request, redirect, send_from_directory, render_template
import logging
from datetime import datetime
from twilio.rest import Client
import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()
app = Flask(__name__)

# Logging
logging.basicConfig(filename='security.log', level=logging.INFO,
                    format='%(asctime)s - %(message)s')

# Twilio config
TWILIO_SID = os.getenv("TWILIO_ACCOUNT_SID")
TWILIO_AUTH = os.getenv("TWILIO_AUTH_TOKEN")
TWILIO_FROM = os.getenv("TWILIO_FROM")
TWILIO_TO = os.getenv("TWILIO_TO")
client = Client(TWILIO_SID, TWILIO_AUTH)

# Database config
DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")
DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")

def get_db_connection():
    return psycopg2.connect(
        host=DB_HOST,
        port=DB_PORT,
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD
    )

# Create users table if it doesn't exist
def init_db():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        );
    """)
    conn.commit()
    cur.close()
    conn.close()

init_db()

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
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM users WHERE username = %s AND password = %s", (username, password))
    result = cur.fetchone()
    cur.close()
    conn.close()
    return result

def user_exists(username):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM users WHERE username = %s", (username,))
    result = cur.fetchone()
    cur.close()
    conn.close()
    return result

def add_user(username, password):
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("INSERT INTO users (username, password) VALUES (%s, %s)", (username, password))
        conn.commit()
        cur.close()
        conn.close()
        return True
    except:
        return False

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

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
