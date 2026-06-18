import streamlit as st
import sqlite3
import pandas as pd
import imaplib
import email
import re
from bs4 import BeautifulSoup
from datetime import datetime

# עיצוב מוחלט
st.set_page_config(page_title="CallBiz CRM", layout="wide")
st.markdown("""
<style>
    .stApp { direction: rtl; text-align: right; font-family: 'Heebo', sans-serif; background-color: #f8f9fa; }
    .stDataFrame { direction: rtl; text-align: right; }
    .card { background-color: white; padding: 20px; border-radius: 15px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }
</style>
""", unsafe_allow_html=True)

# בסיס נתונים
def init_db():
    conn = sqlite3.connect('crm.db')
    c = conn.cursor()
    c.execute('CREATE TABLE IF NOT EXISTS clients (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, phone TEXT UNIQUE, status TEXT DEFAULT "חדש")')
    c.execute('CREATE TABLE IF NOT EXISTS tasks (client_id INTEGER, task_desc TEXT, due_date TEXT, status TEXT DEFAULT "פתוחה")')
    conn.commit(); conn.close()

# סנכרון וניקוי כפילויות
def sync_data():
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
                try:
                    conn.execute("INSERT INTO clients (name, phone) VALUES (?, ?)", ("לקוח חדש", phone.group(1)))
                except: pass
            mail.store(num, "+FLAGS", "\\Seen")
        # ניקוי סופי
        conn.execute("DELETE FROM clients WHERE phone='-' OR phone='' OR phone IS NULL")
        conn.commit(); conn.close(); mail.logout()
        return True
    except: return False

# ממשק
init_db()
st.title("💼 מערכת CallBiz CRM")
if st.button("🔄 סנכרן ורענן את הנתונים"):
    if sync_data(): st.success("הנתונים סונכרנו בהצלחה!")
    else: st.error("שגיאה בסנכרון.")
    st.rerun()

st.subheader("📋 רשימת לקוחות פעילים")
conn = sqlite3.connect('crm.db')
df = pd.read_sql_query("SELECT * FROM clients", conn)
st.dataframe(df, use_container_width=True)
conn.close()
