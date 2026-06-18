import streamlit as st
import sqlite3
import pandas as pd
import imaplib
import email
from bs4 import BeautifulSoup
from datetime import datetime

st.set_page_config(page_title="CallBiz CRM", layout="wide")

# --- מסד נתונים ---
def init_db():
    conn = sqlite3.connect('crm.db')
    c = conn.cursor()
    c.execute('CREATE TABLE IF NOT EXISTS clients (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, phone TEXT UNIQUE)')
    c.execute('CREATE TABLE IF NOT EXISTS tasks (id INTEGER PRIMARY KEY AUTOINCREMENT, client_id INTEGER, task_desc TEXT, due_date TEXT, status TEXT DEFAULT "פתוחה")')
    conn.commit(); conn.close()

init_db()

# --- פונקציית סנכרון מיילים חכמה ---
def fetch_and_process_emails():
    try:
        mail = imaplib.IMAP4_SSL("imap.gmail.com")
        mail.login(st.secrets["EMAIL_ACCOUNT"], st.secrets["APP_PASSWORD"])
        mail.select("inbox")
        status, messages = mail.search(None, '(UNSEEN FROM "CallBiz@callbiz.co.il")')
        
        count = 0
        if status == "OK" and messages[0]:
            for num in messages[0].split():
                status, data = mail.fetch(num, "(RFC822)")
                msg = email.message_from_bytes(data[0][1])
                
                body = ""
                if msg.is_multipart():
                    for part in msg.walk():
                        if part.get_content_type() == "text/html":
                            body = part.get_payload(decode=True).decode("utf-8", errors="ignore")
                else:
                    body = msg.get_payload(decode=True).decode("utf-8", errors="ignore")
                
                soup = BeautifulSoup(body, "html.parser")
                text = soup.get_text(separator="\n")
                
                # חילוץ נתונים (פשוט)
                phone = re.search(r"(\d{9,10})", text)
                phone = phone.group(1) if phone else "לא נמצא"
                
                conn = sqlite3.connect('crm.db')
                c = conn.cursor()
                try:
                    c.execute("INSERT INTO clients (name, phone) VALUES (?, ?)", ("לקוח חדש", phone))
                    conn.commit()
                    count += 1
                except: pass
                conn.close()
                mail.store(num, "+FLAGS", "\\Seen")
            mail.logout()
            return f"נקלטו {count} פניות חדשות!"
        mail.logout()
        return "אין פניות חדשות."
    except Exception as e:
        return f"שגיאה: {e}"

# --- ממשק ---
st.title("💼 CallBiz CRM")

if st.button("🔄 סנכרן מיילים"):
    with st.spinner("סורק פניות..."):
        msg = fetch_and_process_emails()
        st.success(msg)
        st.rerun()

st.subheader("📋 רשימת לקוחות")
conn = sqlite3.connect('crm.db')
df = pd.read_sql_query("SELECT * FROM clients", conn)
conn.close()
st.dataframe(df, use_container_width=True)
