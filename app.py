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

st.markdown("""
<style>
.stApp { direction: rtl; background-color: #fcfcfc; font-family: 'Heebo', sans-serif; }
.card { background-color: #ffffff; padding: 20px; border-radius: 15px; border: 1px solid #eef2f3; }
.urgent-alert { background-color: #fff9e6; border-right: 5px solid #ffcc00; padding: 15px; border-radius: 8px; margin-bottom: 20px; color: #5c4a00; }
</style>
""", unsafe_allow_html=True)

def init_db():
    conn = sqlite3.connect('crm.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS clients (id INTEGER PRIMARY KEY AUTOINCREMENT, phone TEXT UNIQUE, name TEXT, status TEXT DEFAULT 'חדש', followup_date TEXT, id_number TEXT, tags TEXT DEFAULT '')''')
    c.execute('''CREATE TABLE IF NOT EXISTS messages (id INTEGER PRIMARY KEY AUTOINCREMENT, client_id INTEGER, date TEXT, text TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS client_notes (id INTEGER PRIMARY KEY AUTOINCREMENT, client_id INTEGER, note_date TEXT, note_text TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS tasks (id INTEGER PRIMARY KEY AUTOINCREMENT, client_id INTEGER, task_desc TEXT, due_date TEXT, status TEXT DEFAULT 'פתוחה')''')
    c.execute('''CREATE TABLE IF NOT EXISTS client_files (id INTEGER PRIMARY KEY AUTOINCREMENT, client_id INTEGER, file_name TEXT, file_data BLOB, upload_date TEXT)''')
    conn.commit(); conn.close()

init_db()
st.title("💼 מערכת CallBiz CRM")
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
                # לוגיקת המשיכה תעבוד כאן
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
    if st.button("🔄 סנכרן פניות"):
    if fetch_emails(): st.success("סונכרן!")

# כאן יבוא הדשבורד וחלוקת הטאבים...
st.write("המערכת מוכנה להמשך פיתוח...")
