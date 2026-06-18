import streamlit as st
import sqlite3
import pandas as pd
import imaplib
import email
import re
from bs4 import BeautifulSoup
import io
from datetime import datetime

# --- הגדרות עיצוב ---
st.set_page_config(page_title="CallBiz CRM", layout="wide")
st.markdown("""
<style>
    .stApp { direction: rtl; text-align: right; background-color: #fcfcfc; font-family: 'Heebo', sans-serif; }
    .stDataFrame { direction: rtl; }
    h1, h2, h3 { text-align: right; }
    .urgent-alert { background-color: #fff9e6; border-right: 5px solid #ffcc00; padding: 15px; border-radius: 8px; margin-bottom: 20px; color: #5c4a00; }
</style>
""", unsafe_allow_html=True)

# --- בסיס נתונים ---
def init_db():
    conn = sqlite3.connect('crm.db')
    c = conn.cursor()
    c.execute('CREATE TABLE IF NOT EXISTS clients (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, phone TEXT UNIQUE, tags TEXT)')
    c.execute('CREATE TABLE IF NOT EXISTS tasks (id INTEGER PRIMARY KEY AUTOINCREMENT, client_id INTEGER, task_desc TEXT, due_date TEXT, status TEXT DEFAULT "פתוחה")')
    conn.commit(); conn.close()

# --- פונקציית סנכרון חכמה ---
def fetch_and_process_emails():
    try:
        conn = sqlite3.connect('crm.db')
        existing_names = pd.read_sql_query("SELECT name FROM clients", conn)['name'].tolist()
        conn.close()
        
        mail = imaplib.IMAP4_SSL("imap.gmail.com")
        mail.login(st.secrets["EMAIL_ACCOUNT"], st.secrets["APP_PASSWORD"])
        mail.select("inbox")
        _, msgs = mail.search(None, '(UNSEEN FROM "CallBiz@callbiz.co.il")')
        
        count = 0
        if msgs[0]:
            for num in msgs[0].split():
                _, data = mail.fetch(num, "(RFC822)")
                msg = email.message_from_bytes(data[0][1])
                body = msg.get_payload(decode=True).decode("utf-8", errors="ignore")
                text = BeautifulSoup(body, "html.parser").get_text()
                
                phone = re.search(r"(\d{9,10})", text)
                found_name = next((n for n in existing_names if n in text), None)
                
                if phone or found_name:
                    conn = sqlite3.connect('crm.db')
                    c = conn.cursor()
                    c.execute("INSERT OR IGNORE INTO clients (name, phone) VALUES (?, ?)", 
                              (found_name or "לקוח חדש", phone.group(1) if phone else "לא נמצא"))
                    conn.commit(); conn.close()
                    count += 1
                mail.store(num, "+FLAGS", "\\Seen")
            mail.logout()
            return f"נקלטו {count} פניות חדשות!"
        return "אין פניות חדשות."
    except Exception as e:
        return f"שגיאה: {e}"

# --- ממשק משתמש ---
init_db()
st.title("💼 מערכת CallBiz CRM")

col1, col2 = st.columns([1, 4])
with col1:
    if st.button("🔄 סנכרן פניות מהמייל"):
        with st.spinner("סורק..."):
            st.success(fetch_and_process_emails())
            st.rerun()

# משימות דחופות
today = datetime.now().strftime("%Y-%m-%d")
conn = sqlite3.connect('crm.db')
urgent = pd.read_sql_query(f"SELECT * FROM tasks WHERE status='פתוחה' AND due_date <= '{today}'", conn)
conn.close()
if not urgent.empty:
    st.markdown(f"<div class='urgent-alert'>⚠️ {len(urgent)} משימות דחופות ממתינות!</div>", unsafe_allow_html=True)

st.subheader("📋 רשימת לקוחות")
conn = sqlite3.connect('crm.db')
st.dataframe(pd.read_sql_query("SELECT * FROM clients", conn), use_container_width=True)
conn.close()
