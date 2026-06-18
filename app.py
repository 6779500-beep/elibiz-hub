import streamlit as st
import sqlite3
import pandas as pd
import imaplib
import email
import re
from bs4 import BeautifulSoup

# 1. הגדרות תצוגה ועיצוב מתקדם
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

# 2. אתחול מסד נתונים חסין כפילויות
def init_db():
    conn = sqlite3.connect('crm.db')
    c = conn.cursor()
    # שימוש ב-UNIQUE על עמודת הטלפון למניעת כפילויות
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
    conn.commit()
    conn.close()

# 3. מנוע סנכרון חכם עם המייל
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
                    pass # הטלפון קיים, המערכת מדלגת ולא יוצרת כפילות
            
            mail.store(num, "+FLAGS", "\\Seen")
        
        # מחיקת רשומות לא תקינות מהטבלה
        conn.execute("DELETE FROM clients WHERE phone='-' OR phone IS NULL OR phone='' OR phone='לא נמצא'")
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        return False

init_db()

# 4. ממשק המשתמש
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

# מערכת הלשוניות
tab1, tab2, tab3 = st.tabs(["📋 טבלת לקוחות", "📂 ניהול תיק לקוח", "🚩 משימות"])

# לשונית 1: טבלת הלקוחות הכללית
with tab1:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    conn = sqlite3.connect('crm.db')
    df = pd.read_sql_query("SELECT id, name, phone, status FROM clients", conn)
    conn.close()
    st.dataframe(df, use_container_width=True, hide_index=True)
    st.markdown('</div>', unsafe_allow_html=True)

# לשונית 2: ניהול תיק לקוח ספציפי
with tab2:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.subheader("איתור ועדכון תיק לקוח")
    client_id = st.number_input("הכנס מספר ID של לקוח (מתוך הטבלה):", min_value=1, step=1)
    
    if st.button("טען נתונים של לקוח זה"):
        conn = sqlite3.connect('crm.db')
        data = pd.read_sql_query(f"SELECT * FROM clients WHERE id={client_id}", conn)
        
        if not data.empty:
            st.divider()
            st.write(f"**שם הלקוח:** {data['name'].iloc[0]} | **מספר טלפון:** {data['phone'].iloc[0]}")
            
            # שליפת ההערות הקיימות, אם ישנן
            current_notes = data['notes'].iloc[0] if pd.notna(data['notes'].iloc[0]) else ""
            
            # שימוש בטופס ייעודי לשמירת הערות בצורה נקייה וללא קריסות
            with st.form(key=f"note_form_{client_id}"):
                new_notes = st.text_area("הערות הלקוח (ניתן לערוך ולהוסיף מידע):", value=current_notes, height=150)
                submit_button = st.form_submit_button("שמור הערות")
                
                if submit_button:
                    conn.execute("UPDATE clients SET notes=? WHERE id=?", (new_notes, client_id))
                    conn.commit()
                    st.success("ההערות נשמרו בהצלחה במסד הנתונים!")
        else:
            st.warning("לא נמצא לקוח עם מספר ID זה. ודא שהמספר מופיע בטבלה.")
        
        conn.close()
    st.markdown('</div>', unsafe_allow_html=True)

# לשונית 3: משימות
with tab3:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.subheader("מערכת משימות")
    st.write("התשתית למשימות הוגדרה במסד הנתונים בהצלחה. ניתן להרחיב חלק זה בהמשך.")
    st.markdown('</div>', unsafe_allow_html=True)
