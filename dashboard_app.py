import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime, timedelta
import subprocess

# 1) Connect to Google Sheet
def load_events():
    scope = ["https://spreadsheets.google.com/feeds",
             "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_name("creds.json", scope)
    client = gspread.authorize(creds)
    sheet = client.open("SF Events Database").sheet1
    data = sheet.get_all_records()
    df = pd.DataFrame(data)
    df['date'] = pd.to_datetime(df['date'], errors='coerce').dt.date
    return df

# 2) Date filtering
def filter_by_date(df, opt):
    today = datetime.today().date()
    if opt == "Today":
        return df[df['date'] == today]
    if opt == "This Weekend":
        sat = today + timedelta((5 - today.weekday()) % 7)
        sun = sat + timedelta(days=1)
        return df[df['date'].isin([sat, sun])]
    if opt == "This Month":
        return df[df['date'].apply(lambda d: d.month == today.month and d.year == today.year)]
    return df

# 3) App
def main():
    st.title("SF Events Dashboard")
    if st.button("Refresh Events"):
        subprocess.call(["python", "event_fetcher.py"])
        st.experimental_rerun()

    df = load_events()

    # Sidebar filters
    date_opt = st.sidebar.selectbox("When?", ["All", "Today", "This Weekend", "This Month"])
    df = filter_by_date(df, date_opt)

    tags = sorted({tag for row in df['tags'].fillna("") for tag in row.split(", ") if tag})
    chosen = st.sidebar.multiselect("Tags", tags)
    if chosen:
        df = df[df['tags'].apply(lambda t: any(c in t for c in chosen))]

    # Display
    for _, r in df.sort_values("date").iterrows():
        st.subheader(r['title'])
        st.write(f"**Date:** {r['date']}  **Time:** {r.get('time','')}")
        st.write(f"**Location:** {r.get('location','')}")
        st.write(f"**Tags:** {r.get('tags','')}")
        if r.get('link'):
            st.markdown(f"[More info]({r['link']})")
        st.write("---")

if __name__ == "__main__":
    main()
