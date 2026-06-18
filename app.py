import streamlit as st
import sqlite3
import pandas as pd
import imaplib
import email
import re
from bs4 import BeautifulSoup
from datetime import datetime

# --- עיצוב פרימיום ---
st.set_page_config(page_title="CallBiz CRM", layout="wide")
st.markdown("""
<style>
    .stApp { direction: rtl; font-family: 'Heebo', sans-serif; background-color: #f8f9fa; }
    h1 { color: #1f77b4; text-align: center; margin-bottom: 30px; }
    .card { background: white; padding: 20px; border-radius: 12px; border: 1px solid #e0e0e0; box-shadow: 0 4px 6px rgba(0,0,0,0.05); }
    .stButton>button { width: 100%; border-radius: 8px; background-color: #1f77b4; color: white; font-weight: bold; }
    [data-testid="stDataFrame"] { direction: rtl; text-align: right; }
</style>
""", unsafe_allow_html=True)

# --- תשתית נתונים ---
def init_db():
    conn = sqlite3.connect('crm.db')
    c = conn.cursor()
    c.execute('CREATE TABLE IF NOT EXISTS clients (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, phone TEXT UNIQUE, status TEXT DEFAULT "חדש")')
    c.execute('CREATE TABLE IF NOT EXISTS tasks (id INTEGER PRIMARY KEY AUTOINCREMENT, client_id INTEGER, task_desc TEXT, due_date TEXT, status TEXT DEFAULT "פתוחה")')
    c.execute("DELETE FROM clients WHERE phone='-' OR phone='לא נמצא' OR phone='' OR phone IS NULL")
    conn.commit(); conn.close()

# --- מנוע הסנכרון ---
def sync_data():
    conn = sqlite3.connect('crm.db')
    try:
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
        conn.execute("DELETE FROM clients WHERE phone='-' OR phone='לא נמצא' OR phone='' OR phone IS NULL")
        conn.commit(); return True
    except: return False
    finally: conn.close()

# --- ממשק ---
init_db()
st.title("💼 CallBiz CRM")

col1, col2 = st.columns([1, 4])
with col1:
    if st.button("🔄 סנכרן ורענן נתונים"):
        if sync_data(): st.success("המערכת מעודכנת!")
        else: st.error("שגיאה בסנכרון.")
        st.rerun()

tab1, tab2 = st.tabs(["📋 רשימת לקוחות", "🚩 משימות פתוחות"])

with tab1:
    conn = sqlite3.connect('crm.db')
    df = pd.read_sql_query("SELECT * FROM clients", conn)
    st.dataframe(df, use_container_width=True, hide_index=True)
    conn.close()

with tab2:
    st.write("מערכת משימות ללקוחות - בבנייה (ניתן להוסיף כאן טבלאות נוספות)")
