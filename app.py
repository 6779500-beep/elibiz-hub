import streamlit as st
import sqlite3
import pandas as pd
import imaplib
import email
import re
from bs4 import BeautifulSoup

# --- עיצוב יוקרתי ---
st.set_page_config(page_title="CallBiz CRM", layout="wide")
st.markdown("""
<style>
    .stApp { direction: rtl; font-family: 'Heebo', sans-serif; background-color: #f8f9fa; }
    .main-header { color: #2c3e50; text-align: center; font-size: 2.5rem; margin-bottom: 20px; }
    .stats-card { background: white; padding: 20px; border-radius: 12px; border: 1px solid #dee2e6; box-shadow: 0 4px 6px rgba(0,0,0,0.05); margin-bottom: 20px; }
    .stButton>button { background-color: #2c3e50; color: white; border-radius: 8px; width: 100%; }
</style>
""", unsafe_allow_html=True)

# --- לוגיקה וניקוי ---
def init_db():
    conn = sqlite3.connect('crm.db')
    c = conn.cursor()
    c.execute('CREATE TABLE IF NOT EXISTS clients (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, phone TEXT UNIQUE, status TEXT DEFAULT "חדש", notes TEXT)')
    c.execute('CREATE TABLE IF NOT EXISTS tasks (id INTEGER PRIMARY KEY AUTOINCREMENT, client_id INTEGER, desc TEXT, status TEXT DEFAULT "פתוחה")')
    conn.commit(); conn.close()

def sync_crm():
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
        conn.execute("DELETE FROM clients WHERE phone='-' OR phone='' OR phone IS NULL")
        conn.commit(); return True
    except: return False
    finally: conn.close()

# --- ממשק מושלם ---
init_db()
st.markdown("<h1 class='main-header'>💼 CallBiz CRM</h1>", unsafe_allow_html=True)

col1, col2 = st.columns([1, 4])
with col1:
    if st.button("🔄 רענן וסנכרן נתונים"):
        if sync_crm(): st.success("המערכת מעודכנת!")
        else: st.error("שגיאה בסנכרון.")
        st.rerun()

tab1, tab2 = st.tabs(["📋 לקוחות וניהול", "🚩 משימות פתוחות"])

with tab1:
    conn = sqlite3.connect('crm.db')
    df = pd.read_sql_query("SELECT * FROM clients", conn)
    st.dataframe(df, use_container_width=True, hide_index=True)
    conn.close()

with tab2:
    st.write("כאן יופיעו המשימות הדחופות שלך...")
