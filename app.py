import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime
import io

st.set_page_config(page_title="CallBiz CRM", page_icon="💼", layout="wide")

# --- CSS עיצוב פסטלי ---
st.markdown("""
<style>
.stApp { direction: rtl; background-color: #fcfcfc; font-family: 'Heebo', sans-serif; }
.card { background-color: #ffffff; padding: 20px; border-radius: 15px; border: 1px solid #eef2f3; box-shadow: 0 4px 10px rgba(0,0,0,0.03); }
.urgent-alert { background-color: #fff9e6; border-right: 5px solid #ffcc00; padding: 15px; border-radius: 8px; margin-bottom: 20px; color: #5c4a00; }
.tag-badge { background-color: #e0f7fa; color: #006064; padding: 2px 8px; border-radius: 5px; font-size: 0.8em; }
</style>
""", unsafe_allow_html=True)

# --- ניהול מסד נתונים משודרג ---
def init_db():
    conn = sqlite3.connect('crm.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS clients 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, phone TEXT UNIQUE, name TEXT, status TEXT DEFAULT 'חדש', 
                  followup_date TEXT, id_number TEXT, tags TEXT DEFAULT '')''')
    try: 
        c.execute("ALTER TABLE clients ADD COLUMN id_number TEXT")
        c.execute("ALTER TABLE clients ADD COLUMN tags TEXT DEFAULT ''")
        conn.commit()
    except: pass
    conn.commit()
    conn.close()

# --- פונקציות עזר ---
def get_db_connection():
    return sqlite3.connect('crm.db')

# --- תצוגת משימות גלובלית ---
def show_urgent_tasks():
    today = datetime.now().strftime("%Y-%m-%d")
    conn = get_db_connection()
    df = pd.read_sql_query(f"SELECT t.task_desc, c.name FROM tasks t JOIN clients c ON t.client_id = c.id WHERE t.status='פתוחה' AND t.due_date <= '{today}'", conn)
    conn.close()
    if not df.empty:
        st.markdown(f"<div class='urgent-alert'>⚠️ יש לך {len(df)} משימות דחופות לטיפול היום!</div>", unsafe_allow_html=True)

# --- ייצוא לאקסל ---
def export_to_excel():
    conn = get_db_connection()
    df = pd.read_sql_query("SELECT * FROM clients", conn)
    conn.close()
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False)
    return output.getvalue()

# --- ריצה ---
init_db()
show_urgent_tasks()

st.title("💼 מערכת ניהול לקוחות CallBiz")

# כפתור גיבוי
if st.sidebar.button("💾 ייצוא כל הלקוחות לאקסל"):
    data = export_to_excel()
    st.sidebar.download_button("הורד קובץ גיבוי", data=data, file_name="crm_backup.xlsx")

# (שאר הלוגיקה שלך לניהול הלקוחות נשארת כאן...)
