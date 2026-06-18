import streamlit as st
import imaplib
import email
import re
from bs4 import BeautifulSoup
import sqlite3
import pandas as pd
from datetime import datetime

# --- הגדרות דף ---
st.set_page_config(page_title="CallBiz Hub", page_icon="📞", layout="centered")
st.title("📞 CallBiz Message Hub")

# --- מסד נתונים ---
def init_db():
    conn = sqlite3.connect('leads.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS leads
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  date TEXT,
                  name TEXT,
                  phone TEXT,
                  message TEXT)''')
    conn.commit()
    conn.close()

def save_lead(name, phone, message):
    conn = sqlite3.connect('leads.db')
    c = conn.cursor()
    current_date = datetime.now().strftime("%Y-%m-%d %H:%M")
    c.execute("INSERT INTO leads (date, name, phone, message) VALUES (?, ?, ?, ?)", 
              (current_date, name, phone, message))
    conn.commit()
    conn.close()

def get_all_leads():
    conn = sqlite3.connect('leads.db')
    df = pd.read_sql_query("SELECT * FROM leads ORDER BY id DESC", conn)
    conn.close()
    return df

# --- משיכת מיילים ---
def fetch_emails():
    try:
        # שימוש בסודות שנגדיר בענן
        EMAIL_ACCOUNT = st.secrets["EMAIL_ACCOUNT"]
        APP_PASSWORD = st.secrets["APP_PASSWORD"]
        TARGET_SENDER = "CallBiz@callbiz.co.il"
        
        mail = imaplib.IMAP4_SSL("imap.gmail.com")
        mail.login(EMAIL_ACCOUNT, APP_PASSWORD)
        mail.select("inbox")
        
        status, messages = mail.search(None, f'(UNSEEN FROM "{TARGET_SENDER}")')
        if status == "OK" and messages[0]:
            email_ids = messages[0].split()
            new_leads_count = 0
            for num in email_ids:
                status, data = mail.fetch(num, "(RFC822)")
                if status != "OK": continue
                
                msg = email.message_from_bytes(data[0][1])
                body = ""
                if msg.is_multipart():
                    for part in msg.walk():
                        if part.get_content_type() == "text/html":
                            body = part.get_payload(decode=True).decode("utf-8", errors="ignore")
                            break
                else:
                    body = msg.get_payload(decode=True).decode("utf-8", errors="ignore")
                
                if body:
                    soup = BeautifulSoup(body, "html.parser")
                    clean_text = soup.get_text(separator="\n")
                    
                    phone_match = re.search(r"מה מספר הטלפון לחזרה\?\s*([^\n]+)", clean_text)
                    message_match = re.search(r"מה למסור לאליהו\?\s*([^\n]+)", clean_text)
                    name_match = re.search(r"מה שמך בבקשה\?\s*([^\n]+)", clean_text)
                    
                    phone = phone_match.group(1).strip() if phone_match else "לא נמצא"
                    subject = message_match.group(1).strip() if message_match else "לא נמצא"
                    name = name_match.group(1).strip() if name_match else "לא נמצא"
                    
                    save_lead(name, phone, subject)
                    new_leads_count += 1
                    mail.store(num, "+FLAGS", "\\Seen")
            
            mail.logout()
            return new_leads_count
        else:
            mail.logout()
            return 0
    except Exception as e:
        st.error(f"שגיאה בהתחברות למייל. ודא שהסודות מוגדרים נכון.")
        return 0

# --- הפעלת המערכת ---
init_db()

# כפתור רענון
if st.button("🔄 רענן ובדוק פניות חדשות"):
    with st.spinner("מתחבר לתיבת המייל..."):
        new_count = fetch_emails()
        if new_count > 0:
            st.success(f"נמשכו {new_count} פניות חדשות!")
        else:
            st.info("אין פניות חדשות כרגע.")

# תצוגת נתונים
st.subheader("📋 רשימת הפניות")
df = get_all_leads()

if not df.empty:
    st.dataframe(df, use_container_width=True, hide_index=True)
else:
    st.write("עדיין אין פניות במערכת.")
