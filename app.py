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
