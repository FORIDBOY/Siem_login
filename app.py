from flask import Flask, request, redirect, send_from_directory
import logging
from datetime import datetime
from twilio.rest import Client
import os
from dotenv import load_dotenv

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

    if username == "admin" and password == "1234":
        logging.info(f"SUCCESS_LOGIN | User: {username} | IP: {ip} | Agent: {user_agent}")
        return redirect('/static/info.html')
    else:
        logging.warning(f"FAILED_LOGIN | User: {username} | IP: {ip} | Agent: {user_agent}")
        send_sms_alert(f"🚨 FAILED_LOGIN from IP {ip} | User: {username}")
        return open('templates/login.html').read()

@app.route('/<path:filename>')
def serve_static(filename):
    return send_from_directory('static', filename)

# ------------------- Run the App -------------------
if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))  # fallback for local
    app.run(host='0.0.0.0', port=port)
