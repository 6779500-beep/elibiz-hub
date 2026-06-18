import streamlit as st
import sqlite3
import pandas as pd
import imaplib
import email
import re
from bs4 import BeautifulSoup

# --- עיצוב הבית (החלק שאהבת) ---
st.set_page_config(page_title="CallBiz CRM", layout="wide")
st.markdown("""
<style>
    .stApp { direction: rtl; text-align: right; font-family: 'Heebo', sans-serif; background-color: #f8f9fa; }
    .card { background: white; padding: 25px; border-radius: 15px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); margin-bottom: 20px; }
    h1 { color: #2c3e50; text-align: center; }
    .stButton>button { width: 100%; border-radius: 8px; background-color: #2c3e50; color: white; font-weight: bold; }
    [data-testid="stDataFrame"] { direction: rtl; text-align: right; }
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
                try: conn.execute("INSERT INTO clients (name, phone) VALUES (?, ?)", ("לקוח חדש", phone.group(1)))
                except: pass
            mail.store(num, "+FLAGS", "\\Seen")
        conn.commit(); return True
    except: return False
    finally: conn.close()

# --- ממשק מעוצב ---
init_db()
st.markdown('<div class="card"><h1>💼 מערכת CallBiz CRM</h1></div>', unsafe_allow_html=True)

col1, col2 = st.columns([1, 3])
with col1:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    if st.button("🔄 סנכרן נתונים"):
        if sync_data(): st.success("הסנכרון עבר בהצלחה!"); st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

with col2:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.subheader("📋 לקוחות")
    conn = sqlite3.connect('crm.db')
    df = pd.read_sql_query("SELECT * FROM clients", conn)
    st.dataframe(df, use_container_width=True, hide_index=True)
    conn.close()
    st.markdown('</div>', unsafe_allow_html=True)
