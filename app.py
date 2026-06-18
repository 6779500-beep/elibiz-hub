import streamlit as st
import sqlite3
import pandas as pd
import imaplib
import email
import re
from bs4 import BeautifulSoup
from datetime import datetime

st.set_page_config(page_title="CallBiz CRM", layout="wide")
st.markdown("""
<style>
    .stApp { direction: rtl; text-align: right; background-color: #fcfcfc; font-family: 'Heebo', sans-serif; }
    .card { background-color: #ffffff; padding: 20px; border-radius: 15px; border: 1px solid #e0e0e0; box-shadow: 0 4px 6px rgba(0,0,0,0.05); }
    .urgent { background-color: #fff1f1; border-right: 5px solid #ff4b4b; padding: 15px; border-radius: 10px; color: #820000; font-weight: bold; }
    h1 { color: #2c3e50; }
</style>
""", unsafe_allow_html=True)
def init_db():
    conn = sqlite3.connect('crm.db')
    c = conn.cursor()
    c.execute('CREATE TABLE IF NOT EXISTS clients (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, phone TEXT UNIQUE, status TEXT DEFAULT "חדש")')
    c.execute('CREATE TABLE IF NOT EXISTS tasks (client_id INTEGER, task_desc TEXT, due_date TEXT, status TEXT DEFAULT "פתוחה")')
    c.execute("DELETE FROM clients WHERE phone='לא נמצא' OR phone IS NULL")
    conn.commit(); conn.close()

def sync_all():
    try:
        conn = sqlite3.connect('crm.db')
        mail = imaplib.IMAP4_SSL("imap.gmail.com")
        mail.login(st.secrets["EMAIL_ACCOUNT"], st.secrets["APP_PASSWORD"])
        mail.select("inbox")
        _, msgs = mail.search(None, '(UNSEEN FROM "CallBiz@callbiz.co.il")')
        for num in msgs[0].split():
            _, data = mail.fetch(num, "(RFC822)")
            msg = email.message_from_bytes(data[0][1])
            body = msg.get_payload(decode=True).decode("utf-8", errors="ignore")
            text = BeautifulSoup(body, "html.parser").get_text()
            phone = re.search(r"(\d{9,10})", text)
            if phone:
                conn.execute("INSERT OR IGNORE INTO clients (name, phone) VALUES (?, ?)", ("לקוח חדש", phone.group(1)))
            mail.store(num, "+FLAGS", "\\Seen")
        conn.commit(); conn.close(); mail.logout()
        return "הסנכרון הושלם בהצלחה!"
    except: return "שגיאת סנכרון."
init_db()
st.title("💼 CallBiz CRM")
if st.button("🔄 סנכרן עכשיו"):
    st.success(sync_all()); st.rerun()

tab1, tab2 = st.tabs(["📋 רשימת לקוחות", "🚩 משימות דחופות"])

with tab1:
    conn = sqlite3.connect('crm.db')
    st.dataframe(pd.read_sql_query("SELECT * FROM clients", conn), use_container_width=True)
    conn.close()

with tab2:
    conn = sqlite3.connect('crm.db')
    urgent = pd.read_sql_query("SELECT * FROM tasks WHERE status='פתוחה'", conn)
    if not urgent.empty:
        for i, row in urgent.iterrows():
            st.markdown(f"<div class='urgent'>⚠️ {row['task_desc']}</div>", unsafe_allow_html=True)
    else: st.write("אין משימות דחופות.")
    conn.close()
