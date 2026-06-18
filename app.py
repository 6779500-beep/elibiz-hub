import streamlit as st
import imaplib
import email
import re
from bs4 import BeautifulSoup
import sqlite3
import pandas as pd
from datetime import datetime
from email.header import decode_header
import io

st.set_page_config(page_title="CallBiz CRM", page_icon="💼", layout="wide")

# --- CSS עיצוב ---
st.markdown("""
<style>
.stApp { direction: rtl; background-color: #fcfcfc; font-family: 'Heebo', sans-serif; }
.card { background-color: #ffffff; padding: 20px; border-radius: 15px; border: 1px solid #eef2f3; box-shadow: 0 4px 10px rgba(0,0,0,0.03); }
.urgent-alert { background-color: #fff9e6; border-right: 5px solid #ffcc00; padding: 15px; border-radius: 8px; margin-bottom: 20px; color: #5c4a00; }
.note-box { background-color: white; padding: 15px; border-radius: 10px; border-right: 5px solid #007aff; margin-bottom: 12px; box-shadow: 0 2px 5px rgba(0,0,0,0.05); }
.task-box-open { background-color: white; padding: 15px; border-radius: 10px; border-right: 5px solid #ff9500; margin-bottom: 10px; }
.status-badge { color: white; padding: 4px 12px; border-radius: 15px; font-size: 0.8em; font-weight: bold; }
</style>
""", unsafe_allow_html=True)

# --- לוגיקה מלאה ---
def init_db():
    conn = sqlite3.connect('crm.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS clients (id INTEGER PRIMARY KEY AUTOINCREMENT, phone TEXT UNIQUE, name TEXT, status TEXT DEFAULT 'חדש', followup_date TEXT, id_number TEXT, tags TEXT DEFAULT '')''')
    c.execute('''CREATE TABLE IF NOT EXISTS messages (id INTEGER PRIMARY KEY AUTOINCREMENT, client_id INTEGER, date TEXT, text TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS client_files (id INTEGER PRIMARY KEY AUTOINCREMENT, client_id INTEGER, file_name TEXT, file_data BLOB, upload_date TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS client_notes (id INTEGER PRIMARY KEY AUTOINCREMENT, client_id INTEGER, note_date TEXT, note_text TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS tasks (id INTEGER PRIMARY KEY AUTOINCREMENT, client_id INTEGER, task_desc TEXT, due_date TEXT, status TEXT DEFAULT 'פתוחה')''')
    conn.commit(); conn.close()

def fetch_emails():
    try:
        mail = imaplib.IMAP4_SSL("imap.gmail.com")
        mail.login(st.secrets["EMAIL_ACCOUNT"], st.secrets["APP_PASSWORD"])
        mail.select("inbox")
        status, messages = mail.search(None, '(UNSEEN FROM "CallBiz@callbiz.co.il")')
        if status == "OK" and messages[0]:
            for num in messages[0].split():
                status, data = mail.fetch(num, "(RFC822)")
                msg = email.message_from_bytes(data[0][1])
                # ... כאן נכנסת כל לוגיקת ה-BeautifulSoup וה-save_incoming_lead שלנו ...
                mail.store(num, "+FLAGS", "\\Seen")
            mail.logout()
        return True
    except: return False

def export_to_excel():
    conn = sqlite3.connect('crm.db')
    df = pd.read_sql_query("SELECT * FROM clients", conn)
    conn.close()
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False)
    return output.getvalue()

# --- ממשק ---
init_db()
st.title("💼 CallBiz CRM")

# כפתורים וסינכרון
col1, col2 = st.columns([1, 4])
with col1:
    if st.button("🔄 סנכרן פניות"):
        if fetch_emails(): st.success("סונכרן!")
        else: st.error("שגיאה")
    data = export_to_excel()
    st.download_button("💾 ייצוא לאקסל", data=data, file_name="crm_backup.xlsx")

# הצגת משימות דחופות (מרכז שליטה)
today = datetime.now().strftime("%Y-%m-%d")
conn = sqlite3.connect('crm.db')
tasks = pd.read_sql_query(f"SELECT * FROM tasks WHERE status='פתוחה' AND due_date <= '{today}'", conn)
conn.close()
if not tasks.empty:
    st.markdown(f"<div class='urgent-alert'>⚠️ יש לך {len(tasks)} משימות דחופות!</div>", unsafe_allow_html=True)

# בחירת לקוח והצגת התוכן (כאן נכנס שאר הקוד של הטאבים שלך...)
