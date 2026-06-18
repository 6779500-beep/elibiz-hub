import streamlit as st
import sqlite3
import pandas as pd
import imaplib
import email
import re
from bs4 import BeautifulSoup

# עיצוב יפה (אותו CSS שעבד)
st.set_page_config(page_title="CallBiz CRM", layout="wide")
st.markdown("""
<style>
    .stApp { direction: rtl; text-align: right; background-color: #f4f7f6; font-family: 'Heebo', sans-serif; }
    .card { background: white; padding: 25px; border-radius: 15px; box-shadow: 0 6px 12px rgba(0,0,0,0.08); margin-bottom: 20px; }
    .stButton>button { width: 100%; border-radius: 10px; background-color: #3498db; color: white; font-weight: bold; }
    [data-testid="stDataFrame"] { direction: rtl; }
</style>
""", unsafe_allow_html=True)

# תשתית עם הגנה מכפילויות
def init_db():
    conn = sqlite3.connect('crm.db')
    c = conn.cursor()
    # UNIQUE(phone) הוא המפתח למניעת כפילויות
    c.execute('''CREATE TABLE IF NOT EXISTS clients 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                  name TEXT, 
                  phone TEXT UNIQUE, 
                  status TEXT DEFAULT "חדש")''')
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
                # INSERT OR IGNORE מונע יצירת שורה חדשה אם הטלפון כבר קיים
                conn.execute("INSERT OR IGNORE INTO clients (name, phone) VALUES (?, ?)", ("לקוח חדש", phone.group(1)))
            
            # מסמן כנקרא כדי שלא יקרא שוב
            mail.store(num, "+FLAGS", "\\Seen")
        
        conn.execute("DELETE FROM clients WHERE phone='-' OR phone='' OR phone IS NULL")
        conn.commit()
        return True
    except: return False
    finally: conn.close()

# ממשק
init_db()
st.markdown('<div class="card"><h1>💼 מערכת CallBiz CRM</h1></div>', unsafe_allow_html=True)

if st.button("🔄 סנכרן ונקו כפילויות"):
    if sync_data(): st.success("הנתונים סונכרנו ונוקו מכפילויות!")
    else: st.error("שגיאה בסנכרון.")
    st.rerun()

st.markdown('<div class="card">', unsafe_allow_html=True)
conn = sqlite3.connect('crm.db')
df = pd.read_sql_query("SELECT * FROM clients", conn)
st.dataframe(df, use_container_width=True, hide_index=True)
conn.close()
st.markdown('</div>', unsafe_allow_html=True)
