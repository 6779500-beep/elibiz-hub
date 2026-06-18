import streamlit as st
import sqlite3
import pandas as pd
import imaplib
import email
import re
from bs4 import BeautifulSoup

# --- הגדרות עיצוב RTL (כמו שהיה כשהכל עבד) ---
st.set_page_config(page_title="CallBiz CRM", layout="wide")
st.markdown("""
<style>
    .stApp { direction: rtl; text-align: right; font-family: 'Heebo', sans-serif; background-color: #f8f9fa; }
    h1 { color: #2c3e50; text-align: center; }
    .stButton>button { width: 100%; border-radius: 8px; background-color: #2c3e50; color: white; font-weight: bold; }
</style>
""", unsafe_allow_html=True)

# --- לוגיקה ---
def init_db():
    conn = sqlite3.connect('crm.db')
    c = conn.cursor()
    c.execute('CREATE TABLE IF NOT EXISTS clients (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, phone TEXT UNIQUE, status TEXT DEFAULT "חדש")')
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
                except: pass
            mail.store(num, "+FLAGS", "\\Seen")
        conn.commit(); return True
    except: return False
    finally: conn.close()

# --- ממשק ---
init_db()
st.title("💼 מערכת CallBiz CRM")

if st.button("🔄 סנכרן נתונים מהמייל"):
    if sync_data():
        st.success("הסנכרון עבר בהצלחה!")
        st.rerun()
    else:
        st.error("שגיאה בסנכרון.")

st.subheader("📋 לקוחות")
conn = sqlite3.connect('crm.db')
df = pd.read_sql_query("SELECT * FROM clients", conn)
st.dataframe(df, use_container_width=True)
conn.close()
