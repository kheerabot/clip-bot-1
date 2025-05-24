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
SERVICE_ACCOUNT_FILE = "service_account.json"

# === HARDCODED BASE64 GOOGLE CREDENTIALS ===
GOOGLE_CREDS_JSON_BASE64 = """ewogICJ0eXBlIjogInNlcnZpY2VfYWNjb3VudCIsCiAgInByb2plY3RfaWQiOiAiY2xpcGJvdC1zZXJ2aWNlIiwKICAicHJpdmF0ZV9rZXlfaWQiOiAiYmYwYjJmZWEyNjliNGM5MGU1N2IzZTdjNTBlNjUyNGEwZmMyZGYwMiIsCiAgInByaXZhdGVfa2V5IjogIi0tLS0tQkVHSU4gUFJJVkFURSBLRVktLS0tLVxuTUlJRXZBSUJBREFOQmdrcWhraUc5dzBCQVFFRkFBU0NCS1l3Z2dTaUFnRUFBb0lCQVFDYmxkNENoTVQ2aXdKc1xuV1l5OEdJQXJqcVVyN1o5aU1RWlpUTFFCR2g0SXE3VFQ0U2h0OWt5MDE4OU40bWJwSG9zUmxab0FGaXJldGYyc1xuY045eW55RHdDMjZxZHpuME9LcHlDSmp0QjhlQlp5aEpRZnlkazZGWUdUUENnc1M5TEFKendjcDJRQzJ4RXlpRVxuZy9KdmZSa3ZRbVpjQjlBVUNqWjVuN0llMFV1aWpWU1FXaEtjZVUzd3NJVFo2SG90NDFYV2F0QnlMMHE2dU4rdFxuYVBqUm1Ma1piWm83Nkdod3dOaGpNZlprSXdZZUFmMkJoWWJyUXFmRDF5QjQxZG1tSjN4aXBqTU9HS0pjcmFsaVxuZHNUS05UakUyKzBBcGk1OE1RZjlCRzdXKzdac0g3RnRVaGFlMWNoRWEvVFk0Qk9lVTRSQ3BtcWhPbjlET0krRVxuRlNxZEREL3ZBZ01CQUFFQ2dnRUFCd2FnQlc0WWRSWDA4STZrcjlQTmFlb2hwRmV4TkY1eFluUDN4dnIyY3o3SlxueGkyclJUZnpvOUVCRUF2U3lPRXp0NElSZDhLSWdoRW0yUFFwNndPcm1adHlqbWtlNlZ2cnVvV1AzbGhWRm85aFxuZnRsbmZuZ3R0NHcvelo5WklnL01ObzBBUnhIRDNuUzJoakZ0TDhLdThmYm1KMjdFNHpySTFmb3pzWGVUR2s2RVxuZGE2M3FaQWwyM000dXc5d1dWclhDRWF1WDYySnRQNEZNcElrb0pxWklwZjRrc3NpOEpWb0lzQ29KMDBIaHQwL1xuOUs1eGZrOXFCQ01CYi9oSUI1cFkzTzA0SUMvRERwT21ETmt5YzJJWDVJdGVvSDlNV1o1VjhTK2s5NG9SVWpXU1xuc2ZFQVAxb1VoRXZ0RnNHU0lSZSsvbmptT3pic2gveURuQ0MrZjA5bVNRS0JnUURaTW9NTGhCZUFhZmhqQmZtWlxuUkZ1ZHpmclYvaCtPakpReWtPM211ZmVBVnIyZUxsU2FFV0xaRjd4aWEvSjdKbmFZWlFvdUg5RExJN3VHN3krSlxuVGhUeWdGMUxCRXFRVlkxWlQ1MXA5TXE3ZFlvR213QitWczlBcUNRQzZXQXhpeGwwNUZsS2FXQlpMWjFueDNJOFxua3BBY3ZoS1Naem5FdFJZVG40eCt3aW5ZVndLQmdRQzNZWXRQTm9BM0FZQXhpL01VNnMreWtzY0hXcTVZUk5TRVxuTzBuMjByWk9yQVBWUEFLakdscENPNXF4OGg1a2U3RzdBMGFGMXdBcjBCSWZHUGFMTEw3N1EyQUtlVkNKU0piN1xuTjEvV2tRaDF1cVVrZVIzTzNISUpIUjZFSWZBSzdvY1dqMUFQbXh6SUhBQjQyclFMcXUra1pWRU1WV2tISGM4aFxudnd4YndCUDJLUUtCZ0ZpRGNVdzhKS2U4aC9FeStpa3Y1blpFL3pnK08vWUg3RTAvS3ZTZ1RQRU1hSElTUjRBU1xuSGNxREZjNjJWemRBMFl3QmdVaVN4ckJDZTZYZHkrMlUySXlMSzNucTRjZzRWVVpVWDc1U2VGdzA1bThTcy96SVxudStXSm9FTmZnRWd3ZTh0YlU5Z3pZWVIyUm5PSW9GRjNHU3ZkZWd3WDdUN3czWEpaenhQSlpPdzVBb0dBSTFmYVxuZUtiaGFUaVIwM3JNbTlCeHZWSUtxQUV6THZIOUg0c3B3emR6U1pCZm9MNVRKOHBSY1FoNTFTZjc4WlBoZWxDMFxuUytGWE9CcC9FNTFGRHlmTm16R3VGZmF4cmZQZW5ZWmJvMGdLb0Y0YnEvN24zdEdmN04rKzNPcUprQ0hPeVd0UFxubStKaVZyTUc2RVFHaFdVcGtMNnlNelZXNjdjMEQ2WDVwTWxOVDVrQ2dZQVZOQnY2TkpXVnphQVQ4YUpub255MVxuS2dQR0VsdDYrYy8yRjRKMlpneEsrRnc3Y1RIdmpSbElVd0dHUWJmaXhrdEwxMnZyamJjaHQ5TTFzMVhFaUhkVFxuR3hTQ3hZMzdIU1F5enJwMmdXd1JpWkU1UGpvcDJlMk9ySmN1cjZjelJWRVhSQ3Y4a1VDemlBaDBEVnZnN1FXSVxub1ZGY0xpeWJjdUhQenJPcXVYSWdTUT09XG4tLS0tLUVORCBQUklWQVRFIEtFWS0tLS0tXG4iLAogICJjbGllbnRfZW1haWwiOiAiY2xpcGJvdC1zZXJ2aWNlQGNsaXBib3Qtc2VydmljZS5pYW0uZ3NlcnZpY2VhY2NvdW50LmNvbSIsCiAgImNsaWVudF9pZCI6ICIxMDQ5MTU1NDQ3MTQwNjk0NjI4MTYiLAogICJhdXRoX3VyaSI6ICJodHRwczovL2FjY291bnRzLmdvb2dsZS5jb20vby9vYXV0aDIvYXV0aCIsCiAgInRva2VuX3VyaSI6ICJodHRwczovL29hdXRoMi5nb29nbGVhcGlzLmNvbS90b2tlbiIsCiAgImF1dGhfcHJvdmlkZXJfeDUwOV9jZXJ0X3VybCI6ICJodHRwczovL3d3dy5nb29nbGVhcGlzLmNvbS9vYXV0aDIvdjEvY2VydHMiLAogICJjbGllbnRfeDUwOV9jZXJ0X3VybCI6ICJodHRwczovL3d3dy5nb29nbGVhcGlzLmNvbS9yb2JvdC92MS9tZXRhZGF0YS94NTA5L2NsaXBib3Qtc2VydmljZSU0MGNsaXBib3Qtc2VydmljZS5pYW0uZ3NlcnZpY2VhY2NvdW50LmNvbSIsCiAgInVuaXZlcnNlX2RvbWFpbiI6ICJnb29nbGVhcGlzLmNvbSIKfQo=
"""  # keep the full string here

# === SETUP GOOGLE SHEETS CLIENT ===
creds_dict = json.loads(base64.b64decode(GOOGLE_CREDS_JSON_BASE64).decode())
credentials = Credentials.from_service_account_info(creds_dict, scopes=SCOPES)
gc = gspread.authorize(credentials)
sheet = gc.open_by_key(SPREADSHEET_ID).sheet1

app = FastAPI()

def get_youtuber_configs():
    try:
        records = sheet.get_all_records()
        configs = []
        for row in records:
            try:
                clip_len_raw = row.get('Clip Length (sec)', 360)
                clip_len = int(clip_len_raw) if clip_len_raw else 360
            except Exception as e:
                print(f"[WARN] Invalid clip length '{clip_len_raw}', defaulting to 360")
                clip_len = 360

            config = {
                'timestamp': row.get('Timestamp'),
                'nickname': row.get('Nickname'),
                'youtube_channel_id': row.get('YouTube Channel ID'),
                'discord_webhook_url': row.get('Discord Webhook URL'),
                'clip_length': clip_len
            }
            print(f"[DEBUG] Loaded config row: {config}")
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
                {
                    "name": "Clip Length (seconds)",
                    "value": str(clip_length),
                    "inline": True
                },
                {
                    "name": "Channel ID",
                    "value": channel_id,
                    "inline": True
                }
            ],
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(current_time))
        }

        print(f"[DEBUG] Sending webhook to {webhook_url}")
        print(f"[DEBUG] Embed content: {embed}")

        response = requests.post(webhook_url, json={"embeds": [embed]})

        if response.status_code not in [200, 204]:
            print(f"[ERROR] Discord webhook returned status {response.status_code}: {response.text}")
            return JSONResponse(status_code=500, content={"error": f"Discord webhook error: {response.status_code}"})

        return {"status": "clip posted successfully"}
    except Exception as e:
        print(f"[ERROR] Exception in /clip: {e}")
        return JSONResponse(status_code=500, content={"error": "Internal server error"})
