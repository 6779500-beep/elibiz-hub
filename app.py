import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime

# --- עיצוב וצבעים רכים ---
st.markdown("""
<style>
.stApp { direction: rtl; background-color: #fcfcfc; }
.urgent-box { background-color: #fffaf0; border-right: 5px solid #ffb347; padding: 15px; border-radius: 10px; margin-bottom: 10px; }
.task-item { background-color: #ffffff; padding: 10px; border-radius: 8px; border: 1px solid #e0e0e0; margin-bottom: 5px; }
</style>
""", unsafe_allow_html=True)

# --- פונקציית ריכוז משימות דחופות ---
def show_global_urgent_tasks():
    today = datetime.now().strftime("%Y-%m-%d")
    conn = sqlite3.connect('crm.db')
    # שליפת משימות פתוחות מהיום או עבר
    df = pd.read_sql_query(f"""
        SELECT t.id, t.task_desc, t.due_date, c.name, t.client_id 
        FROM tasks t JOIN clients c ON t.client_id = c.id 
        WHERE t.status = 'פתוחה' AND t.due_date <= '{today}'
        ORDER BY t.due_date ASC
    """, conn)
    conn.close()
    
    if not df.empty:
        st.subheader("🚩 מרכז משימות דחופות לטיפול")
        for _, row in df.iterrows():
            st.markdown(f"""
            <div class='urgent-box'>
                <strong>{row['task_desc']}</strong><br>
                לקוח: {row['name']} | תאריך יעד: {row['due_date']}
            </div>
            """, unsafe_allow_html=True)
    else:
        st.success("אין משימות דחופות כרגע - הכל בשליטה!")

# --- שילוב בדשבורד הראשי ---
# תחת ה-Dashboard הקיים, נוסיף קריאה לפונקציה:
# show_global_urgent_tasks()
