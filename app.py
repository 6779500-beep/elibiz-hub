import streamlit as st
import sqlite3
import pandas as pd

# עיצוב מנצח (ימין-לשמאל, כרטיסים, עברית)
st.set_page_config(page_title="CallBiz CRM", layout="wide")
st.markdown("""
<style>
    .stApp { direction: rtl; text-align: right; background-color: #f0f2f6; font-family: 'Heebo', sans-serif; }
    .card { background: white; padding: 20px; border-radius: 12px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); margin-bottom: 20px; }
    h1 { color: #2c3e50; text-align: center; }
    .stButton>button { width: 100%; border-radius: 8px; background-color: #3498db; color: white; font-weight: bold; }
</style>
""", unsafe_allow_html=True)

# תשתית מסד נתונים
def init_db():
    conn = sqlite3.connect('crm.db')
    c = conn.cursor()
    c.execute('CREATE TABLE IF NOT EXISTS clients (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, phone TEXT UNIQUE, notes TEXT)')
    conn.commit(); conn.close()

init_db()

# ממשק משתמש
st.markdown('<div class="card"><h1>💼 מערכת CallBiz CRM</h1></div>', unsafe_allow_html=True)

# אזור הצגת הטבלה
conn = sqlite3.connect('crm.db')
df = pd.read_sql_query("SELECT * FROM clients", conn)
conn.close()

st.markdown('<div class="card">', unsafe_allow_html=True)
st.subheader("📋 רשימת לקוחות")
# הצגת טבלה פשוטה ללא ספריות חיצוניות שגורמות לשגיאות
st.dataframe(df, use_container_width=True, hide_index=True)
st.markdown('</div>', unsafe_allow_html=True)

# אזור עריכת הערות ללקוח
st.markdown('<div class="card">', unsafe_allow_html=True)
st.subheader("עדכון תיק לקוח")
client_id = st.number_input("הקלד ID של לקוח לעדכון:", min_value=1)
if st.button("טען פרטי לקוח"):
    conn = sqlite3.connect('crm.db')
    data = pd.read_sql_query(f"SELECT * FROM clients WHERE id={client_id}", conn)
    conn.close()
    if not data.empty:
        st.write(f"עורך את: {data['name'].iloc[0]}")
        new_notes = st.text_area("הערות:", value=data['notes'].iloc[0] if data['notes'].iloc[0] else "")
        if st.button("שמור שינויים"):
            conn = sqlite3.connect('crm.db')
            conn.execute("UPDATE clients SET notes=? WHERE id=?", (new_notes, client_id))
            conn.commit(); conn.close()
            st.success("נשמר!")
    else:
        st.error("לא נמצא לקוח עם ID זה.")
st.markdown('</div>', unsafe_allow_html=True)
