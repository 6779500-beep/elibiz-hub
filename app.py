import streamlit as st
import sqlite3
import pandas as pd
import imaplib
import email
import re
from bs4 import BeautifulSoup

# עיצוב CSS מלא - מובטח
st.set_page_config(page_title="CallBiz CRM", layout="wide")
st.markdown("""
<style>
    .stApp { direction: rtl !important; text-align: right !important; background-color: #f0f2f6 !important; font-family: 'Heebo', sans-serif !important; }
    h1 { color: #2c3e50 !important; text-align: center !important; margin-bottom: 30px !important; }
    .card { background-color: white !important; padding: 25px !important; border-radius: 15px !important; box-shadow: 0 4px 10px rgba(0,0,0,0.1) !important; margin-bottom: 20px !important; }
    .stButton>button { width: 100% !important; border-radius: 10px !important; background-color: #3498db !important; color: white !important; font-weight: bold !important; border: none !important; padding: 10px !important; }
    [data-testid="stDataFrame"] { direction: rtl !important; border-radius: 10px !important; }
</style>
""", unsafe_allow_html=True)

# לוגיקה
def init_db():
    conn = sqlite3.connect('crm.db')
    c = conn.cursor()
    c.execute('CREATE TABLE IF NOT EXISTS clients (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, phone TEXT UNIQUE, status TEXT DEFAULT "חדש")')
    conn.commit(); conn.close()

def reset_db():
    conn = sqlite3.connect('crm.db')
    conn.execute('DROP TABLE IF EXISTS clients')
    conn.execute('CREATE TABLE clients (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, phone TEXT UNIQUE, status TEXT DEFAULT "חדש")')
    conn.commit(); conn.close()

def sync():
    conn = sqlite3.connect('crm.db')
    try:
        mail = imaplib.IMAP4_SSL("imap.gmail.com")
        mail.login(st.secrets["EMAIL_ACCOUNT"], st.secrets["APP_PASSWORD"])
        mail.select("inbox")
        _, msgs = mail.search(None, '(UNSEEN)')
        for num in msgs[0].split():
            _, data = mail.fetch(num, "(RFC822)")
            msg = email.message_from_bytes(data[0][1])
            body = msg.get_payload(decode=True).decode("utf-8", errors="ignore")
            phone = re.search(r"(\d{9,10})", text := BeautifulSoup(body, "html.parser").get_text())
            if phone:
                try: conn.execute("INSERT INTO clients (name, phone) VALUES (?, ?)", ("לקוח חדש", phone.group(1)))
                except: pass
            mail.store(num, "+FLAGS", "\\Seen")
        conn.commit(); return True
    except: return False
    finally: conn.close()

# ממשק מעוצב
init_db()
st.markdown('<div class="card"><h1>💼 מערכת CallBiz CRM</h1></div>', unsafe_allow_html=True)

col1, col2 = st.columns([1, 3])
with col1:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    if st.button("🔄 סנכרן נתונים"):
        sync(); st.rerun()
    if st.button("🗑️ איפוס מלא"):
        reset_db(); st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

with col2:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.subheader("📋 לקוחות")
    df = pd.read_sql_query("SELECT * FROM clients", sqlite3.connect('crm.db'))
    st.dataframe(df, use_container_width=True, hide_index=True)
    st.markdown('</div>', unsafe_allow_html=True)
