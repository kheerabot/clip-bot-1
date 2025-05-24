import os
import json
import base64
import time
import requests
import gspread
from flask import Flask, request, jsonify
from google.oauth2.service_account import Credentials

# === CONFIG ===
SPREADSHEET_ID = '1MdBcEWXWtJ9Ud41hU2gtWeCBE2WyMTbTWbq6t8seCmU'
SCOPES = ['https://www.googleapis.com/auth/spreadsheets.readonly']
SERVICE_ACCOUNT_FILE = "service_account.json"

# === HARDCODED BASE64 GOOGLE CREDENTIALS ===
GOOGLE_CREDS_JSON_BASE64 = """<PASTE YOUR BASE64 CREDENTIAL STRING HERE>"""

# === Write Google credentials file
with open(SERVICE_ACCOUNT_FILE, "w") as f:
    f.write(base64.b64decode(GOOGLE_CREDS_JSON_BASE64).decode("utf-8"))

# === Authorize Sheets
creds = Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES)
gc = gspread.authorize(creds)
sheet = gc.open_by_key(SPREADSHEET_ID).sheet1

# === Load configs
def get_youtuber_configs():
    records = sheet.get_all_records()
    configs = []
    for row in records:
        configs.append({
            'timestamp': row.get('Timestamp'),
            'nickname': row.get('Nickname'),
            'youtube_channel_id': row.get('YouTube Channel ID'),
            'discord_webhook_url': row.get('Discord Webhook URL'),
            'clip_length': int(row.get('Clip Length (sec)', 360))
        })
    return configs

# === Flask App
app = Flask(__name__)

@app.route('/')
def home():
    return "✅ Clip Server is running. Use /clip to send clips."

@app.route('/clip', methods=['GET', 'POST'])
def receive_clip():
    try:
        # Read parameters
        if request.method == 'GET':
            user_message = request.args.get("message") or "No message provided"
            username = request.args.get("username", "Unknown User")
            pfp_url = request.args.get("pfp_url", "")
            channel_id = request.args.get("channel_id")
        else:
            data = request.get_json() or {}
            user_message = data.get("message") or "No message provided"
            username = data.get("username", "Unknown User")
            pfp_url = data.get("pfp_url", "")
            channel_id = data.get("channel_id")

        if not channel_id:
            return jsonify({"status": "error", "message": "Missing YouTube Channel ID"}), 400

        # Match channel
        configs = get_youtuber_configs()
        config = next((c for c in configs if c["youtube_channel_id"] == channel_id), None)

        if not config:
            return jsonify({"status": "error", "message": "No config found for this channel"}), 404

        webhook_url = config["discord_webhook_url"]
        nickname = config["nickname"]
        clip_length = config.get("clip_length", 360)

        print(f"[DEBUG] Posting to Discord webhook for {nickname}...")

        # Simulate clip link
        clip_url = f"https://example.com/fake_clip_{int(time.time())}.mp4"

        # Discord embed
        embed = {
            "title": f"🎬 New Clip from {nickname}'s Stream!",
            "description": f"**{username}** clipped:\n`{user_message}`\n⏱️ **Duration:** {clip_length}s",
            "color": 0x00ffcc,
            "fields": [{"name": "Clip URL", "value": clip_url, "inline": False}],
            "footer": {"text": f"YouTube Channel ID: {channel_id}"}
        }

        if pfp_url:
            embed["thumbnail"] = {"url": pfp_url}

        # Send to Discord
        response = requests.post(webhook_url, json={"embeds": [embed]})
        response.raise_for_status()

        return jsonify({"status": "success", "message": "Clip posted to Discord!"})

    except requests.RequestException as e:
        print(f"[ERROR] Failed to post to Discord webhook: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500
    except Exception as e:
        print(f"[ERROR] Server error: {e}")
        return jsonify({"status": "error", "message": "Internal Server Error"}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
