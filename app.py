import streamlit as st
import sqlite3
import pandas as pd
import imaplib
import email
import re
from bs4 import BeautifulSoup

# --- עיצוב מלא (RTL וצבעים) ---
st.set_page_config(page_title="CallBiz CRM", layout="wide")
st.markdown("""
<style>
    .stApp { direction: rtl; text-align: right; background-color: #f0f2f6; font-family: 'Heebo', sans-serif; }
    .header { background: #2c3e50; color: white; padding: 20px; border-radius: 10px; text-align: center; margin-bottom: 20px; }
    .card { background: white; padding: 20px; border-radius: 10px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); margin-bottom: 20px; }
    .stButton>button { width: 100%; border-radius: 8px; background-color: #3498db; color: white; font-weight: bold; }
    [data-testid="stDataFrame"] { direction: rtl; }
</style>
""", unsafe_allow_html=True)

# --- לוגיקה ---
def init_db():
    conn = sqlite3.connect('crm.db')
    c = conn.cursor()
    c.execute('CREATE TABLE IF NOT EXISTS clients (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, phone TEXT UNIQUE, status TEXT DEFAULT "חדש", notes TEXT)')
    conn.commit(); conn.close()

# --- ממשק ---
init_db()
st.markdown('<div class="header"><h1>💼 מערכת ניהול לקוחות CallBiz</h1></div>', unsafe_allow_html=True)

tab1, tab2 = st.tabs(["📋 רשימת לקוחות", "📂 תיק לקוח אישי"])

with tab1:
    conn = sqlite3.connect('crm.db')
    df = pd.read_sql_query("SELECT * FROM clients", conn)
    st.dataframe(df, use_container_width=True, hide_index=True)
    conn.close()

with tab2:
    st.subheader("ניהול תיק לקוח")
    client_id = st.number_input("הכנס ID לקוח כדי לצפות בתיק:", min_value=1)
    if st.button("טען תיק לקוח"):
        conn = sqlite3.connect('crm.db')
        client_data = pd.read_sql_query(f"SELECT * FROM clients WHERE id={client_id}", conn)
        if not client_data.empty:
            st.write(f"### פרטי לקוח: {client_data['name'][0]}")
            st.text_area("הערות:", value=client_data['notes'][0] if client_data['notes'][0] else "")
        else:
            st.error("לא נמצא לקוח עם ID זה.")
        conn.close()
