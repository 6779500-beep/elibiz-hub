import streamlit as st
import sqlite3
import pandas as pd
from streamlit_extras.dataframe_explorer import dataframe_explorer

st.set_page_config(layout="wide")

# פונקציה להצגת טבלה שלחיצה עליה מפעילה פונקציה
def init_db():
    conn = sqlite3.connect('crm.db')
    c = conn.cursor()
    # מוודא שהעמודות קיימות
    c.execute('CREATE TABLE IF NOT EXISTS clients (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, phone TEXT UNIQUE, status TEXT, notes TEXT)')
    conn.commit(); conn.close()

init_db()

st.title("💼 מערכת ניהול לקוחות")

# הצגת טבלה
conn = sqlite3.connect('crm.db')
df = pd.read_sql_query("SELECT * FROM clients", conn)
conn.close()

# רכיב לבחירת לקוח מהטבלה
st.subheader("רשימת לקוחות")
selected_client = st.dataframe(df, use_container_width=True, hide_index=True, on_select="rerun")

# בדיקה אם נבחר לקוח (הלוגיקה של streamlit משתנה בהתאם לגרסה)
if selected_client and len(selected_client['selection']['rows']) > 0:
    idx = selected_client['selection']['rows'][0]
    client_id = df.iloc[idx]['id']
    st.session_state['active_client_id'] = client_id

# הצגת תיק לקוח
if 'active_client_id' in st.session_state:
    st.divider()
    st.subheader(f"תיק לקוח: {st.session_state['active_client_id']}")
    
    conn = sqlite3.connect('crm.db')
    c = conn.cursor()
    c.execute("SELECT * FROM clients WHERE id=?", (st.session_state['active_client_id'],))
    data = c.fetchone()
    
    if data:
        # data[4] זו עמודת ה-notes
        current_notes = data[4] if len(data) > 4 else ""
        new_note = st.text_area("הערות:", value=current_notes)
        if st.button("שמור הערות"):
            c.execute("UPDATE clients SET notes=? WHERE id=?", (new_note, st.session_state['active_client_id']))
            conn.commit()
            st.success("נשמר!")
    conn.close()
