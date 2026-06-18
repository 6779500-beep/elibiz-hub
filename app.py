import streamlit as st
import sqlite3

# הגדרות דף
st.set_page_config(page_title="CallBiz CRM", layout="wide")

# אתחול בסיסי
def init_db():
    conn = sqlite3.connect('crm.db')
    c = conn.cursor()
    c.execute('CREATE TABLE IF NOT EXISTS clients (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT)')
    conn.commit()
    conn.close()

init_db()

st.title("💼 מערכת CallBiz CRM")
st.write("המערכת עובדת!")

# בדיקת כפתור פשוטה
if st.button("בדיקת סנכרון"):
    st.success("הקוד רץ בצורה תקינה!")
import imaplib
import email

def fetch_emails():
    try:
        mail = imaplib.IMAP4_SSL("imap.gmail.com")
        mail.login(st.secrets["EMAIL_ACCOUNT"], st.secrets["APP_PASSWORD"])
        mail.select("inbox")
        status, messages = mail.search(None, '(UNSEEN FROM "CallBiz@callbiz.co.il")')
        if status == "OK" and messages[0]:
            mail.logout()
            return f"נמצאו הודעות חדשות!"
        mail.logout()
        return "אין הודעות חדשות."
    except Exception as e:
        return f"שגיאה בחיבור: {e}"

# הוספת כפתור לסנכרון בממשק הקיים
if st.button("סנכרן מיילים"):
    res = fetch_emails()
    st.write(res)
