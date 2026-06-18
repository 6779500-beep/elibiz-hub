import streamlit as st
import sqlite3
import pandas as pd
import imaplib
import email
import re
from bs4 import BeautifulSoup
from datetime import datetime

# --- עיצוב מושלם (עברית ו-RTL) ---
st.set_page_config(page_title="CallBiz CRM", layout="wide")
st.markdown("""
<style>
    .stApp { direction: rtl; text-align: right; font-family: 'Heebo', sans-serif; background-color: #f4f7f6; }
    h1 { color: #2c3e50; text-align: center; margin-bottom: 30px; }
    .stButton>button { background-color: #3498db; color: white; border-radius: 10px; font-weight: bold; width: 100%; }
    .card { background-color: white; padding: 20px; border-radius: 15px; border: 1px solid #dcdde1; box-shadow: 0 4px 6px rgba(0,0,0,0.05); margin-bottom: 20px; }
    [data-testid="stDataFrame"] { direction: rtl; }
</style>
""", unsafe_allow_html=True)

# --- לוגיקה חכמה ---
def init_db():
    conn = sqlite3.connect('crm.db')
    c = conn.cursor()
    c.execute('CREATE TABLE IF NOT EXISTS clients (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, phone TEXT UNIQUE, status TEXT DEFAULT "חדש")')
    c.execute('CREATE TABLE IF NOT EXISTS tasks (id INTEGER PRIMARY KEY AUTOINCREMENT, client_id INTEGER, task_desc TEXT, due_date TEXT, status TEXT DEFAULT "פתוחה")')
    conn.commit(); conn.close()

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
                try:
                    conn.execute("INSERT INTO clients (name, phone) VALUES (?, ?)", ("לקוח חדש", phone.group(1)))
                except sqlite3.IntegrityError: pass
            mail.store(num, "+FLAGS", "\\Seen")
        conn.execute("DELETE FROM clients WHERE phone='-' OR phone='לא נמצא' OR phone='' OR phone IS NULL")
        conn.commit(); return True
    except: return False
    finally: conn.close()

# --- ממשק ---
init_db()
st.markdown("<h1>💼 מערכת CallBiz CRM</h1>", unsafe_allow_html=True)

col1, col2 = st.columns([1, 4])
with col1:
    if st.button("🔄 סנכרן נתונים"):
        if sync_data(): st.success("הסנכרון הושלם!")
        else: st.error("שגיאה בסנכרון.")
        st.rerun()

tab1, tab2 = st.tabs(["📋 רשימת לקוחות", "🚩 משימות פתוחות"])

with tab1:
    conn = sqlite3.connect('crm.db')
    df = pd.read_sql_query("SELECT * FROM clients", conn)
    st.dataframe(df, use_container_width=True, hide_index=True)
    conn.close()

with tab2:
    st.write("משימות לטיפול - בבנייה (ניתן להוסיף כאן טבלה נוספת)")
