import streamlit as st
import pandas as pd

# עיצוב אגרסיבי כדי לוודא שזה תופס
st.set_page_config(page_title="CallBiz CRM", layout="wide")
st.markdown("""
<style>
    .stApp { direction: rtl !important; text-align: right !important; font-family: 'Heebo', sans-serif !important; background-color: #f8f9fa !important; }
    h1 { color: #2c3e50 !important; text-align: center !important; }
    [data-testid="stDataFrame"] { direction: rtl !important; }
</style>
""", unsafe_allow_html=True)

st.title("💼 מערכת CallBiz CRM")
st.subheader("אם אתה רואה את הטקסט הזה בעברית ובצד ימין – העיצוב עובד.")

# דאטה לדוגמה כדי לראות אם זה מיושר
data = {'שם': ['ישראל ישראלי'], 'טלפון': ['050-1234567']}
st.dataframe(pd.DataFrame(data), use_container_width=True)
