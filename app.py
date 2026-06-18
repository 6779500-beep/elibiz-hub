import streamlit as st
import imaplib
import email
import re
from bs4 import BeautifulSoup
import sqlite3
import pandas as pd
from datetime import datetime
from email.header import decode_header

st.set_page_config(page_title="CallBiz CRM", page_icon="💼", layout="wide")

# --- CSS מעוצב ---
st.markdown("""
<style>
.stApp { direction: rtl; background-color: #f8f9fa; }
.note-box { background-color: white; padding: 15px; border-radius: 10px; border-right: 5px solid #007aff; margin-bottom: 12px; }
.status-badge { color: white; padding: 4px 12px; border-radius: 15px; font-size: 0.6em; font-weight: bold; }
</style>
""", unsafe_allow_html=True)

# --- ניהול מסד נתונים ---
def init_db():
    conn = sqlite3.connect('crm.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS clients 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, phone TEXT UNIQUE, name TEXT, status TEXT DEFAULT 'חדש', followup_date TEXT, id_number TEXT)''')
    # תמיכה בטבלאות נוספות
    c.execute('''CREATE TABLE IF NOT EXISTS contact_phones 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, client_id INTEGER, phone_num TEXT, label TEXT, FOREIGN KEY(client_id) REFERENCES clients(id))''')
    # (שאר הטבלאות נשארות כפי שהיו - הודעות, הערות, משימות, קבצים...)
    conn.commit()
    conn.close()

# --- פונקציית חיפוש חכמה ---
def search_clients(query):
    conn = sqlite3.connect('crm.db')
    # חיפוש בשם, ת"ז, או כל טלפון מקושר
    query_sql = f"%{query}%"
    df = pd.read_sql_query("""
        SELECT DISTINCT c.id, c.name, c.id_number 
        FROM clients c 
        LEFT JOIN contact_phones cp ON c.id = cp.client_id
        WHERE c.name LIKE ? OR c.id_number LIKE ? OR c.phone LIKE ? OR cp.phone_num LIKE ?
    """, conn, params=(query_sql, query_sql, query_sql, query_sql))
    conn.close()
    return df

# --- ממשק משתמש ---
st.title("💼 מערכת CRM מתקדמת")

# תיבת חיפוש גלובלית
search_query = st.text_input("🔍 חיפוש לקוח (שם / ת"ז / טלפון):")
if search_query:
    results = search_clients(search_query)
    if not results.empty:
        st.write("תוצאות חיפוש:")
        st.dataframe(results)
    else:
        st.write("לא נמצאו תוצאות.")

# --- אזור ניהול תיק לקוח ---
# (כאן תוסיף את שאר הלוגיקה שלך לטאבים)
# בתוך טאב "📝 פרטים":
# st.text_input("מספר תעודת זהות:", key="id_input")
# st.text_input("הוסף טלפון נוסף:", key="extra_phone")
# st.selectbox("סוג:", ["נייד", "בית", "משרד", "אחר"])
