import os
import json
import base64
import time
import requests
import gspread
from fastapi import FastAPI, Query
from fastapi.responses import JSONResponse
from google.oauth2.service_account import Credentials

# === CONFIG ===
SPREADSHEET_ID = '1MdBcEWXWtJ9Ud41hU2gtWeCBE2WyMTbTWbq6t8seCmU'
SCOPES = ['https://www.googleapis.com/auth/spreadsheets.readonly']

# === LOAD GOOGLE CREDENTIALS FROM ENVIRONMENT ===
GOOGLE_CREDS_JSON_BASE64 = os.environ.get("GOOGLE_CREDS_JSON_BASE64")
if not GOOGLE_CREDS_JSON_BASE64:
    raise EnvironmentError("Missing GOOGLE_CREDS_JSON_BASE64 environment variable")

try:
    creds_dict = json.loads(base64.b64decode(GOOGLE_CREDS_JSON_BASE64).decode())
    credentials = Credentials.from_service_account_info(creds_dict, scopes=SCOPES)
    gc = gspread.authorize(credentials)
    sheet = gc.open_by_key(SPREADSHEET_ID).sheet1
except Exception as e:
    raise RuntimeError(f"Failed to initialize Google Sheets client: {e}")

# === FASTAPI APP ===
app = FastAPI()

def get_youtuber_configs():
    try:
        records = sheet.get_all_records()
        configs = []
        for row in records:
            try:
                clip_len_raw = row.get('Clip Length (sec)', 360)
                clip_len = int(clip_len_raw) if clip_len_raw else 360
            except Exception:
                clip_len = 360  # default fallback
            config = {
                'timestamp': row.get('Timestamp'),
                'nickname': row.get('Nickname'),
                'youtube_channel_id': row.get('YouTube Channel ID'),
                'discord_webhook_url': row.get('Discord Webhook URL'),
                'clip_length': clip_len
            }
            configs.append(config)
        return configs
    except Exception as e:
        print(f"[ERROR] Failed to get configs from Google Sheets: {e}")
        return []

@app.get("/clip")
def clip(
    username: str = Query("Unknown User"),
    message: str = Query("No message provided"),
    channel_id: str = Query("")
):
    try:
        current_time = int(time.time())
        configs = get_youtuber_configs()

        if not configs:
            return JSONResponse(status_code=500, content={"error": "No youtuber configs available"})

        youtuber_config = next((c for c in configs if c['youtube_channel_id'] == channel_id), None)
        if not youtuber_config:
            return JSONResponse(status_code=404, content={"error": "YouTuber config not found for channel_id"})

        webhook_url = youtuber_config.get('discord_webhook_url')
        if not webhook_url:
            return JSONResponse(status_code=500, content={"error": "Discord webhook URL missing in youtuber config"})

        clip_length = youtuber_config.get('clip_length', 360)

        embed = {
            "title": f"Clip from {username}",
            "description": message,
            "color": 0x00ff00,
            "fields": [
                {"name": "Clip Length (seconds)", "value": str(clip_length), "inline": True},
                {"name": "Channel ID", "value": channel_id, "inline": True}
            ],
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(current_time))
        }

        response = requests.post(webhook_url, json={"embeds": [embed]})

        if response.status_code not in [200, 204]:
            return JSONResponse(status_code=500, content={"error": f"Discord webhook error: {response.status_code}"})

        return {"status": "clip posted successfully"}
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": "Internal server error"})
