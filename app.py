import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime

# --- הגדרות דף ---
st.set_page_config(page_title="CallBiz CRM", page_icon="💼", layout="wide")

# --- עיצוב צבעים רכים (Pastel Theme) ---
st.markdown("""
<style>
.stApp { direction: rtl; background-color: #fcfcfc; }
/* כרטיסיות רכות */
.card { background-color: #ffffff; padding: 15px; border-radius: 15px; border: 1px solid #e0e0e0; box-shadow: 0 2px 5px rgba(0,0,0,0.02); }
/* כפתור דחוף */
.urgent-task { background-color: #fff0f0 !important; border: 1px solid #ffcccc !important; }
</style>
""", unsafe_allow_html=True)

# ... (חלק ניהול מסד הנתונים נשאר זהה, רק הוספתי עמודת urgency לטבלת tasks) ...
# בהוספת משימה חדשה:
# urgency = st.checkbox("🚩 סמן כמשימה דחופה")
# שמירת ה-urgency במסד הנתונים
