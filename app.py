import streamlit as st
import sqlite3
import pandas as pd
import imaplib
import email
from bs4 import BeautifulSoup
import io

# --- עיצוב ---
st.set_page_config(page_title="CallBiz CRM", layout="wide")
st.title("💼 CallBiz CRM")

# --- בסיס נתונים ---
def init_db():
    conn = sqlite3.connect('crm.db')
    c = conn.cursor()
    c.execute('CREATE TABLE IF NOT EXISTS clients (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, phone TEXT UNIQUE)')
    conn.commit(); conn.close()

init_db()

# --- משיכת מיילים ---
def fetch_emails():
    # כאן יבוא הקוד של ה-imaplib שראינו קודם
    st.write("פונקציית המיילים תופעל כאן")

# --- ממשק ---
if st.button("סנכרן מיילים"):
    fetch_emails()

st.write("המערכת מוכנה לשלב הבא")
