import streamlit as st
import sqlite3
import pandas as pd
import imaplib
import email
import re
from bs4 import BeautifulSoup

# --- 1. עיצוב ממשק פרימיום (RTL ועברית מלאה) ---
st.set_page_config(page_title="CallBiz CRM", layout="wide")
st.markdown("""
<style>
    .stApp { direction: rtl; text-align: right; background-color: #f4f7f6; font-family: 'Heebo', sans-serif; }
    .card { background: white; padding: 25px; border-radius: 12px; box-shadow: 0 4px 10px rgba(0,0,0,0.05); margin-bottom: 20px; border: 1px solid #e1e8ed; }
    h1 { color: #2c3e50; text-align: center; font-weight: 800; margin-bottom: 30px; }
    .stButton>button { width: 100%; background-color: #3498db; color: white; border-radius: 8px; font-weight: bold; border: none; padding: 10px; transition: all 0.3s ease; }
    .stButton>button:hover { background-color: #2980b9; }
    [data-testid="stDataFrame"] { direction: rtl; }
</style>
""", unsafe_allow_html=True)

# --- 2. תשתית מסד נתונים וחסינת כפילויות ---
def init_db():
    conn = sqlite3.connect('crm.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS clients 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                  name TEXT, 
                  phone TEXT UNIQUE, 
                  status TEXT DEFAULT "חדש", 
                  notes TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS tasks 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                  client_id INTEGER, 
                  task_desc TEXT, 
                  status TEXT DEFAULT "פתוחה")''')
    
    # בדיקה ועדכון אוטומטי של עמודת ההערות
    c.execute("PRAGMA table_info(clients)")
    columns = [col[1] for col in c.fetchall()]
    if 'notes' not in columns:
        c.execute("ALTER TABLE clients ADD COLUMN notes TEXT")
    
    conn.commit()
    conn.close()

# --- 3. מנוע סנכרון נתונים מהמייל ---
def sync_data():
    try:
        conn = sqlite3.connect('crm.db')
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
                try:
                    conn.execute("INSERT INTO clients (name, phone) VALUES (?, ?)", ("לקוח חדש", phone.group(1)))
                except sqlite3.IntegrityError:
                    pass # חסימת כפילויות
            
            mail.store(num, "+FLAGS", "\\Seen")
        
        conn.execute("DELETE FROM clients WHERE phone='-' OR phone IS NULL OR phone='' OR phone='לא נמצא'")
        conn.commit()
        conn.close()
        return True
    except:
        return False

init_db()

# --- 4. מבנה הממשק ---
st.markdown('<div class="card"><h1>💼 מערכת ניהול לקוחות CallBiz</h1></div>', unsafe_allow_html=True)

col1, col2 = st.columns([1, 4])
with col1:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    if st.button("🔄 סנכרן נתונים"):
        with st.spinner("מסנכרן נתונים..."):
            if sync_data():
                st.success("הסנכרון בוצע בהצלחה!")
            else:
                st.error("שגיאה בסנכרון.")
    st.markdown('</div>', unsafe_allow_html=True)

# שינינו את מבנה הלשוניות לזרימת עבודה חלקה יותר
tab1, tab2 = st.tabs(["📋 לקוחות ותיקי לקוח", "🚩 משימות"])

# לשונית מרכזית: טבלה ותיק לקוח משולבים
with tab1:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.subheader("רשימת לקוחות - הקלק על שורה כדי לפתוח את התיק")
    
    conn = sqlite3.connect('crm.db')
    df = pd.read_sql_query("SELECT id as [מזהה], name as [שם לקוח], phone as [טלפון], status as [סטטוס] FROM clients", conn)
    conn.close()
    
    # הצגת הטבלה
    selection = st.dataframe(
        df, 
        use_container_width=True, 
        hide_index=True, 
        selection_mode="single-row", 
        on_select="rerun"
    )
    st.markdown('</div>', unsafe_allow_html=True)
    
    # לכידת בחירת המשתמש והצגת תיק הלקוח מיד מתחת
    selected_rows = []
    if isinstance(selection, dict):
        selected_rows = selection.get("selection", {}).get("rows", [])
    elif hasattr(selection, "selection"):
        sel_obj = selection.selection
        selected_rows = sel_obj.get("rows", []) if isinstance(sel_obj, dict) else (sel_obj.rows if hasattr(sel_obj, "rows") else [])

    if selected_rows:
        selected_idx = selected_rows[0]
        client_id = int(df.iloc[selected_idx]['מזהה'])
        
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.subheader(f"📂 תיק לקוח אישי (מזהה: {client_id})")
        
        conn = sqlite3.connect('crm.db')
        client_data = pd.read_sql_query(f"SELECT * FROM clients WHERE id={client_id}", conn)
        
        if not client_data.empty:
            st.write(f"**שם הלקוח:** {client_data['name'].iloc[0]} | **מספר טלפון:** {client_data['phone'].iloc[0]}")
            
            current_notes = str(client_data['notes'].iloc[0]) if 'notes' in client_data.columns and pd.notna(client_data['notes'].iloc[0]) else ""
            
            with st.form(key=f"note_form_{client_id}"):
                new_notes = st.text_area("הערות הלקוח (ערוך ולחץ על שמירה):", value=current_notes, height=150)
                submit_button = st.form_submit_button("שמור הערות")
                
                if submit_button:
                    conn.execute("UPDATE clients SET notes=? WHERE id=?", (new_notes, client_id))
                    conn.commit()
                    st.success("ההערות נשמרו בהצלחה!")
        conn.close()
        st.markdown('</div>', unsafe_allow_html=True)

with tab2:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.subheader("מערכת משימות")
    st.write("תשתית המשימות פתוחה, מוגדרת בעברית ומוכנה לעבודה בהמשך.")
    st.markdown('</div>', unsafe_allow_html=True)
