import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime

# --- הגדרות דף ---
st.set_page_config(page_title="CallBiz CRM", page_icon="💼", layout="wide")

# --- עיצוב פסטלי רך (Soft Pastel Theme) ---
st.markdown("""
<style>
.stApp { direction: rtl; background-color: #fcfcfc; }
/* כרטיסייה רכה */
.card { background-color: #ffffff; padding: 20px; border-radius: 15px; border: 1px solid #eef2f3; box-shadow: 0 4px 10px rgba(0,0,0,0.03); }
/* סרגל התראות בולט אך נעים */
.sticky-alert { background-color: #fff9e6; border-right: 5px solid #ffcc00; padding: 15px; border-radius: 8px; margin-bottom: 20px; color: #5c4a00; }
/* גופן נקי */
@import url('https://fonts.googleapis.com/css2?family=Heebo:wght@300;400;600&display=swap');
body, .stApp { font-family: 'Heebo', sans-serif; }
</style>
""", unsafe_allow_html=True)

# --- לוגיקה של סרגל התראות ---
def show_notification_bar():
    today = datetime.now().strftime("%Y-%m-%d")
    conn = sqlite3.connect('crm.db')
    urgent_tasks = pd.read_sql_query(f"SELECT task_desc, due_date FROM tasks WHERE status='פתוחה' AND due_date <= '{today}'", conn)
    conn.close()
    
    if not urgent_tasks.empty:
        st.markdown(f"<div class='sticky-alert'>⚠️ <b>יש לך {len(urgent_tasks)} משימות שמחכות לטיפולך עכשיו!</b></div>", unsafe_allow_html=True)

# --- פונקציות מסד נתונים (אותן פונקציות קודמות, אין שינוי) ---
# [הפונקציות init_db, save_incoming_lead, וכו' נשארות כפי שהן...]
# (הדבק כאן את הלוגיקה שלך מהקוד הקודם כדי לשמור על רצף)

# --- הצגת האתר ---
show_notification_bar() # כאן הקסם קורה, זה יופיע בראש העמוד
st.title("💼 CallBiz CRM - מרכז ניהול אישי")
# ... (שאר הקוד של הטאבים והניהול נשאר כפי שסיכמנו) ...
