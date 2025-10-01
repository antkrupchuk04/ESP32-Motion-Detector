from flask import Flask, request
import os
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime
import requests

app = Flask(__name__)

# --- PostgreSQL через Render Environment Variables ---
DB_HOST = os.environ.get("DB_HOST")
DB_PORT = int(os.environ.get("DB_PORT", 5432))
DB_NAME = os.environ.get("DB_NAME")
DB_USER = os.environ.get("DB_USER")
DB_PASSWORD = os.environ.get("DB_PASSWORD")

# --- Telegram Bot ---
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")

def save_to_db(motion_state):
    try:
        conn = psycopg2.connect(
            host=DB_HOST,
            port=DB_PORT,
            dbname=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD
        )
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO motion_events (motion, timestamp) VALUES (%s, %s)",
            (motion_state, datetime.now())
        )
        conn.commit()
        cur.close()
        conn.close()
    except Exception as e:
        print("DB error:", e)

def send_to_telegram(motion_state):
    try:
        text = f"⚠️ Motion detected ⚠️" if motion_state else "No motion"
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        payload = {"chat_id": TELEGRAM_CHAT_ID, "text": text}
        requests.post(url, json=payload, timeout=5)
    except Exception as e:
        print("Telegram error:", e)

@app.route("/motion", methods=["POST"])
def motion():
    data = request.get_json()
    motion_state = data.get("motion", False)

    print("Motion event:", motion_state)

    save_to_db(motion_state)
    send_to_telegram(motion_state)

    return {"status": "ok"}, 200

@app.route("/motion/latest", methods=["GET"])
def latest_motion_events():
    try:
        conn = psycopg2.connect(
            host=DB_HOST,
            port=DB_PORT,
            dbname=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD
        )
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute(
            "SELECT * FROM motion_events ORDER BY timestamp DESC LIMIT 5"
        )
        rows = cur.fetchall()
        cur.close()
        conn.close()
        return {"latest_events": rows}, 200
    except Exception as e:
        print("DB error:", e)
        return {"error": "Database error"}, 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 12345))
    app.run(host="0.0.0.0", port=port)