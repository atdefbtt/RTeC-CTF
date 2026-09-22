import os
import json
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

import requests
from dotenv import load_dotenv


# =========================
# CONFIG
# =========================

load_dotenv()

WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL")

CTFTIME_URL = "https://ctftime.org/api/v1/events/"

SENT_FILE = "sent_events.json"

VIETNAM_TZ = ZoneInfo("Asia/Ho_Chi_Minh")


# =========================
# CHECK CONFIG
# =========================

if not WEBHOOK_URL:
    raise ValueError(
        "Chưa tìm thấy DISCORD_WEBHOOK_URL trong file .env"
    )


# =========================
# LOAD SENT EVENTS
# =========================

if os.path.exists(SENT_FILE):
    with open(SENT_FILE, "r", encoding="utf-8") as file:
        sent_events = set(json.load(file))
else:
    sent_events = set()


# =========================
# GET EVENTS FROM CTFTIME
# =========================

response = requests.get(
    CTFTIME_URL,
    headers={
        "User-Agent": "RTeC-CTF/1.0"
    },
    timeout=20
)

response.raise_for_status()

events = response.json()

print(f"CTFtime trả về: {len(events)} cuộc thi")


# =========================
# CURRENT TIME
# =========================

now = datetime.now(timezone.utc)


# =========================
# PROCESS EVENTS
# =========================

new_events = []

for event in events:

    event_id = str(event.get("id"))

    title = event.get("title", "Không có tên")

    start_text = event.get("start")

    finish_text = event.get("finish")

    url = event.get("url", "")

    format_type = event.get("format", "Unknown")

    onsite = event.get("onsite")


    # Không có thời gian thì bỏ qua
    if not start_text or not finish_text:
        continue


    # Parse thời gian
    try:
        start = datetime.fromisoformat(
            start_text.replace("Z", "+00:00")
        )

        finish = datetime.fromisoformat(
            finish_text.replace("Z", "+00:00")
        )

    except ValueError:
        continue


    # Đã kết thúc
    if finish < now:
        continue


    # Chỉ lấy CTF online
    if onsite is True:
        continue


    # Đã gửi trước đó
    if event_id in sent_events:
        continue


    new_events.append({
        "id": event_id,
        "title": title,
        "start": start,
        "finish": finish,
        "url": url,
        "format": format_type
    })


# =========================
# SORT BY START TIME
# =========================

new_events.sort(key=lambda x: x["start"])


# =========================
# SEND TO DISCORD
# =========================

for event in new_events:

    start_vn = event["start"].astimezone(VIETNAM_TZ)

    finish_vn = event["finish"].astimezone(VIETNAM_TZ)

    message = (
        "🏆 **RTeC — CTF UPCOMING**\n\n"
        f"🎯 **{event['title']}**\n"
        f"🌐 Format: `{event['format']}`\n"
        f"🕐 Bắt đầu: `{start_vn:%H:%M %d/%m/%Y}`\n"
        f"🏁 Kết thúc: `{finish_vn:%H:%M %d/%m/%Y}`\n"
        f"🔗 {event['url']}"
    )

    discord_response = requests.post(
        WEBHOOK_URL,
        json={
            "content": message
        },
        timeout=20
    )

    discord_response.raise_for_status()

    print(
        f"✅ Đã gửi: {event['title']}"
    )

    sent_events.add(event["id"])


# =========================
# SAVE SENT EVENTS
# =========================

with open(
    SENT_FILE,
    "w",
    encoding="utf-8"
) as file:

    json.dump(
        sorted(sent_events),
        file,
        ensure_ascii=False,
        indent=2
    )


print()
print(f"CTF mới đã gửi: {len(new_events)}")
print("✅ Hoàn thành!")