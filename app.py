import streamlit as st
import sqlite3
import pandas as pd
import imaplib
import email
import re
from bs4 import BeautifulSoup
from datetime import datetime

st.set_page_config(page_title="CallBiz CRM", layout="wide")

# --- תשתית ---
def init_db():
    conn = sqlite3.connect('crm.db')
    c = conn.cursor()
    c.execute('CREATE TABLE IF NOT EXISTS clients (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, phone TEXT UNIQUE, status TEXT DEFAULT "חדש")')
    c.execute('CREATE TABLE IF NOT EXISTS notes (client_id INTEGER, note TEXT)')
    c.execute('CREATE TABLE IF NOT EXISTS tasks (client_id INTEGER, task_desc TEXT, due_date TEXT, status TEXT DEFAULT "פתוחה")')
    c.execute("DELETE FROM clients WHERE phone='לא נמצא'")
    conn.commit(); conn.close()

init_db()

# --- מנוע מיילים ---
def sync_emails():
    try:
        conn = sqlite3.connect('crm.db')
        mail = imaplib.IMAP4_SSL("imap.gmail.com")
        mail.login(st.secrets["EMAIL_ACCOUNT"], st.secrets["APP_PASSWORD"])
        mail.select("inbox")
        _, msgs = mail.search(None, '(UNSEEN FROM "CallBiz@callbiz.co.il")')
        count = 0
        for num in msgs[0].split():
            _, data = mail.fetch(num, "(RFC822)")
            msg = email.message_from_bytes(data[0][1])
            body = msg.get_payload(decode=True).decode("utf-8", errors="ignore")
            text = BeautifulSoup(body, "html.parser").get_text()
            phone = re.search(r"(\d{9,10})", text)
            if phone:
                conn.execute("INSERT OR IGNORE INTO clients (name, phone) VALUES (?, ?)", ("לקוח חדש", phone.group(1)))
                count += 1
            mail.store(num, "+FLAGS", "\\Seen")
        conn.commit(); conn.close(); mail.logout()
        return f"סונכרנו {count} פניות."
    except: return "שגיאת סנכרון."

# --- ממשק ---
st.title("💼 CallBiz CRM")
if st.button("🔄 סנכרן עכשיו"):
    st.success(sync_emails()); st.rerun()

tab1, tab2 = st.tabs(["📋 לקוחות", "📝 ניהול"])
with tab1:
    conn = sqlite3.connect('crm.db')
    st.dataframe(pd.read_sql_query("SELECT * FROM clients", conn), use_container_width=True)
    conn.close()
with tab2:
    st.write("מערכת ניהול משימות והערות - בבנייה.")
