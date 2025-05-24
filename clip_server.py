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
GOOGLE_CREDS_JSON_BASE64 = """ewogICJ0eXBlIjogInNlcnZpY2VfYWNjb3VudCIsCiAgInByb2plY3RfaWQiOiAiY2xpcGJvdC1zZXJ2aWNlIiwKICAicHJpdmF0ZV9rZXlfaWQiOiAiYmYwYjJmZWEyNjliNGM5MGU1N2IzZTdjNTBlNjUyNGEwZmMyZGYwMiIsCiAgInByaXZhdGVfa2V5IjogIi0tLS0tQkVHSU4gUFJJVkFURSBLRVktLS0tLVxuTUlJRXZBSUJBREFOQmdrcWhraUc5dzBCQVFFRkFBU0NCS1l3Z2dTaUFnRUFBb0lCQVFDYmxkNENoTVQ2aXdKc1xuV1l5OEdJQXJqcVVyN1o5aU1RWlpUTFFCR2g0SXE3VFQ0U2h0OWt5MDE4OU40bWJwSG9zUmxab0FGaXJldGYyc1xuY045eW55RHdDMjZxZHpuME9LcHlDSmp0QjhlQlp5aEpRZnlkazZGWUdUUENnc1M5TEFKendjcDJRQzJ4RXlpRVxuZy9KdmZSa3ZRbVpjQjlBVUNqWjVuN0llMFV1aWpWU1FXaEtjZVUzd3NJVFo2SG90NDFYV2F0QnlMMHE2dU4rdFxuYVBqUm1Ma1piWm83Nkdod3dOaGpNZlprSXdZZUFmMkJoWWJyUXFmRDF5QjQxZG1tSjN4aXBqTU9HS0pjcmFsaVxuZHNUS05UakUyKzBBcGk1OE1RZjlCRzdXKzdac0g3RnRVaGFlMWNoRWEvVFk0Qk9lVTRSQ3BtcWhPbjlET0krRVxuRlNxZEREL3ZBZ01CQUFFQ2dnRUFCd2FnQlc0WWRSWDA4STZrcjlQTmFlb2hwRmV4TkY1eFluUDN4dnIyY3o3SlxueGkyclJUZnpvOUVCRUF2U3lPRXp0NElSZDhLSWdoRW0yUFFwNndPcm1adHlqbWtlNlZ2cnVvV1AzbGhWRm85aFxuZnRsbmZuZ3R0NHcvelo5WklnL01ObzBBUnhIRDNuUzJoakZ0TDhLdThmYm1KMjdFNHpySTFmb3pzWGVUR2s2RVxuZGE2M3FaQWwyM000dXc5d1dWclhDRWF1WDYySnRQNEZNcElrb0pxWklwZjRrc3NpOEpWb0lzQ29KMDBIaHQwL1xuOUs1eGZrOXFCQ01CYi9oSUI1cFkzTzA0SUMvRERwT21ETmt5YzJJWDVJdGVvSDlNV1o1VjhTK2s5NG9SVWpXU1xuc2ZFQVAxb1VoRXZ0RnNHU0lSZSsvbmptT3pic2gveURuQ0MrZjA5bVNRS0JnUURaTW9NTGhCZUFhZmhqQmZtWlxuUkZ1ZHpmclYvaCtPakpReWtPM211ZmVBVnIyZUxsU2FFV0xaRjd4aWEvSjdKbmFZWlFvdUg5RExJN3VHN3krSlxuVGhUeWdGMUxCRXFRVlkxWlQ1MXA5TXE3ZFlvR213QitWczlBcUNRQzZXQXhpeGwwNUZsS2FXQlpMWjFueDNJOFxua3BBY3ZoS1Naem5FdFJZVG40eCt3aW5ZVndLQmdRQzNZWXRQTm9BM0FZQXhpL01VNnMreWtzY0hXcTVZUk5TRVxuTzBuMjByWk9yQVBWUEFLakdscENPNXF4OGg1a2U3RzdBMGFGMXdBcjBCSWZHUGFMTEw3N1EyQUtlVkNKU0piN1xuTjEvV2tRaDF1cVVrZVIzTzNISUpIUjZFSWZBSzdvY1dqMUFQbXh6SUhBQjQyclFMcXUra1pWRU1WV2tISGM4aFxudnd4YndCUDJLUUtCZ0ZpRGNVdzhKS2U4aC9FeStpa3Y1blpFL3pnK08vWUg3RTAvS3ZTZ1RQRU1hSElTUjRBU1xuSGNxREZjNjJWemRBMFl3QmdVaVN4ckJDZTZYZHkrMlUySXlMSzNucTRjZzRWVVpVWDc1U2VGdzA1bThTcy96SVxudStXSm9FTmZnRWd3ZTh0YlU5Z3pZWVIyUm5PSW9GRjNHU3ZkZWd3WDdUN3czWEpaenhQSlpPdzVBb0dBSTFmYVxuZUtiaGFUaVIwM3JNbTlCeHZWSUtxQUV6THZIOUg0c3B3emR6U1pCZm9MNVRKOHBSY1FoNTFTZjc4WlBoZWxDMFxuUytGWE9CcC9FNTFGRHlmTm16R3VGZmF4cmZQZW5ZWmJvMGdLb0Y0YnEvN24zdEdmN04rKzNPcUprQ0hPeVd0UFxubStKaVZyTUc2RVFHaFdVcGtMNnlNelZXNjdjMEQ2WDVwTWxOVDVrQ2dZQVZOQnY2TkpXVnphQVQ4YUpub255MVxuS2dQR0VsdDYrYy8yRjRKMlpneEsrRnc3Y1RIdmpSbElVd0dHUWJmaXhrdEwxMnZyamJjaHQ5TTFzMVhFaUhkVFxuR3hTQ3hZMzdIU1F5enJwMmdXd1JpWkU1UGpvcDJlMk9ySmN1cjZjelJWRVhSQ3Y4a1VDemlBaDBEVnZnN1FXSVxub1ZGY0xpeWJjdUhQenJPcXVYSWdTUT09XG4tLS0tLUVORCBQUklWQVRFIEtFWS0tLS0tXG4iLAogICJjbGllbnRfZW1haWwiOiAiY2xpcGJvdC1zZXJ2aWNlQGNsaXBib3Qtc2VydmljZS5pYW0uZ3NlcnZpY2VhY2NvdW50LmNvbSIsCiAgImNsaWVudF9pZCI6ICIxMDQ5MTU1NDQ3MTQwNjk0NjI4MTYiLAogICJhdXRoX3VyaSI6ICJodHRwczovL2FjY291bnRzLmdvb2dsZS5jb20vby9vYXV0aDIvYXV0aCIsCiAgInRva2VuX3VyaSI6ICJodHRwczovL29hdXRoMi5nb29nbGVhcGlzLmNvbS90b2tlbiIsCiAgImF1dGhfcHJvdmlkZXJfeDUwOV9jZXJ0X3VybCI6ICJodHRwczovL3d3dy5nb29nbGVhcGlzLmNvbS9vYXV0aDIvdjEvY2VydHMiLAogICJjbGllbnRfeDUwOV9jZXJ0X3VybCI6ICJodHRwczovL3d3dy5nb29nbGVhcGlzLmNvbS9yb2JvdC92MS9tZXRhZGF0YS94NTA5L2NsaXBib3Qtc2VydmljZSU0MGNsaXBib3Qtc2VydmljZS5pYW0uZ3NlcnZpY2VhY2NvdW50LmNvbSIsCiAgInVuaXZlcnNlX2RvbWFpbiI6ICJnb29nbGVhcGlzLmNvbSIKfQo=
"""

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
