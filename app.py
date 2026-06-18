import streamlit as st
import sqlite3
import pandas as pd
import imaplib
import email
import re
from bs4 import BeautifulSoup
from datetime import datetime
import io

st.set_page_config(page_title="CallBiz CRM", layout="wide")
st.markdown("""
<style>
    .stApp { direction: rtl; text-align: right; background-color: #fcfcfc; }
    .urgent { background-color: #fff9e6; border-right: 5px solid #ffcc00; padding: 10px; }
</style>
""", unsafe_allow_html=True)

def init_db():
    conn = sqlite3.connect('crm.db')
    c = conn.cursor()
    c.execute('CREATE TABLE IF NOT EXISTS clients (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, phone TEXT UNIQUE, status TEXT DEFAULT "חדש")')
    c.execute('CREATE TABLE IF NOT EXISTS notes (client_id INTEGER, note TEXT)')
    c.execute('CREATE TABLE IF NOT EXISTS tasks (client_id INTEGER, task_desc TEXT, due_date TEXT, status TEXT DEFAULT "פתוחה")')
    c.execute('CREATE TABLE IF NOT EXISTS files (client_id INTEGER, file_name TEXT)')
    conn.commit(); conn.close()
init_db()
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
                c = conn.cursor()
                c.execute("INSERT OR IGNORE INTO clients (name, phone) VALUES (?, ?)", ("לקוח חדש", phone.group(1)))
                count += 1
            mail.store(num, "+FLAGS", "\\Seen")
        conn.commit(); conn.close(); mail.logout()
        return f"סונכרנו {count} פניות."
    except: return "שגיאת סנכרון."
        def add_note(c_id, note):
    conn = sqlite3.connect('crm.db')
    conn.execute("INSERT INTO notes (client_id, note) VALUES (?, ?)", (c_id, note))
    conn.commit(); conn.close()

def add_task(c_id, task, date):
    conn = sqlite3.connect('crm.db')
    conn.execute("INSERT INTO tasks (client_id, task_desc, due_date) VALUES (?, ?, ?)", (c_id, task, date))
    conn.commit(); conn.close()
st.title("💼 CallBiz CRM המלא")
if st.button("🔄 סנכרן עכשיו"):
    st.success(sync_emails()); st.rerun()

tab1, tab2, tab3 = st.tabs(["📋 לקוחות", "📝 ניהול משימות", "📂 קבצים"])

with tab1:
    conn = sqlite3.connect('crm.db')
    df = pd.read_sql_query("SELECT * FROM clients", conn)
    st.dataframe(df, use_container_width=True)
    conn.close()

with tab2:
    st.subheader("הוספת משימה חדשה")
    c_id = st.number_input("ID לקוח", min_value=1)
    task = st.text_input("תיאור משימה")
    if st.button("שמור משימה"):
        add_task(c_id, task, datetime.now().strftime("%Y-%m-%d"))
        st.success("נשמר!")

with tab3:
    st.write("ניהול קבצים ללקוחות יתווסף כאן...")
