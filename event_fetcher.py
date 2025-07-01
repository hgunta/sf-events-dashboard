import requests
import gspread
from datetime import datetime
from oauth2client.service_account import ServiceAccountCredentials
import re
from dateutil import parser

# 1) Google Sheets connection
def connect_sheet():
    scope = ["https://spreadsheets.google.com/feeds",
             "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_name("creds.json", scope)
    client = gspread.authorize(creds)
    return client.open("SF Events Database").sheet1

# 2) Fetch from Eventbrite
def fetch_eventbrite():
    url = "https://www.eventbriteapi.com/v3/events/search/"
    headers = {"Authorization": "Bearer YOUR_EVENTBRITE_TOKEN"}
    params = {
        "location.address": "San Francisco",
        "sort_by": "date",
        "expand": "venue",
        "start_date.range_start": datetime.now().isoformat()
    }
    data = requests.get(url, headers=headers, params=params).json()
    events = []
    for e in data.get("events", []):
        events.append({
            "title": e["name"]["text"] or "",
            "date": e["start"]["local"].split("T")[0],
            "time": e["start"]["local"].split("T")[1][:5],
            "location": (e.get("venue") or {}).get("address", {}).get("localized_address_display", ""),
            "tags": "eventbrite",
            "source": "eventbrite",
            "link": e["url"],
            "description": (e.get("description") or {}).get("text", "")
        })
    return events

# 3) Parse manually pasted text block
def parse_manual_block(block_text):
    events = []
    for line in block_text.strip().split("\n"):
        # e.g. "Chinatown Night Market — Friday, July 5 @ Grant Ave"
        m = re.match(r"(.*?)\s*[—-]\s*(.*?)\s*@\s*(.*)", line)
        if not m:
            continue
        title, date_raw, location = m.groups()
        date_parsed = ""
        try:
            date_parsed = str(parser.parse(date_raw, fuzzy=True).date())
        except:
            pass
        tags = []
        low = title.lower()
        if any(x in low for x in ["music", "concert", "dj", "live"]): tags.append("music")
        if any(x in low for x in ["giants", "warriors", "nba", "mlb"]): tags.append("sports")
        if any(x in low for x in ["night market", "holi", "festival"]): tags.append("culture")
        events.append({
            "title": title.strip(),
            "date": date_parsed,
            "time": "",
            "location": location.strip(),
            "tags": ", ".join(tags),
            "source": "manual",
            "link": "",
            "description": ""
        })
    return events

# 4) Append rows to sheet
def update_sheet(events):
    sheet = connect_sheet()
    for e in events:
        row = [
            e["title"],
            e["date"],
            e["time"],
            e["location"],
            e["tags"],
            e["source"],
            e["link"],
            e["description"]
        ]
        sheet.append_row(row)

if __name__ == "__main__":
    all_events = fetch_eventbrite()
    # you can edit this block or later load from a file
    manual_block = """
    Chinatown Night Market — Friday, July 5 @ Grant Ave
    Naruto Symphonic Experience — July 15 @ SAP Center
    SF Coffee Festival — August 10 @ Fort Mason
    """
    all_events += parse_manual_block(manual_block)
    update_sheet(all_events)
    print(f"Uploaded {len(all_events)} events to sheet.")
