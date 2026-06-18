import streamlit as st
import imaplib
import email
import re
from bs4 import BeautifulSoup
import sqlite3
import pandas as pd
from datetime import datetime
import io

# --- הגדרות דף ---
st.set_page_config(page_title="CallBiz CRM", page_icon="💼", layout="wide")

# --- הזרקת קוד עיצוב (CSS) ליישור לימין (RTL) ---
st.markdown("""
<style>
.stApp { direction: rtl; }
h1, h2, h3, p, div, span, label { text-align: right; }
.stButton>button { float: right; width: 100%; margin-top: 10px; }
.stAlert { direction: rtl; text-align: right; }
div[data-testid="stExpander"] { text-align: right; direction: rtl; }
</style>
""", unsafe_allow_html=True)

st.title("💼 מערכת CallBiz CRM האישית שלך")

# --- ניהול מסד נתונים משודרג ---
def init_db():
    conn = sqlite3.connect('crm.db')
    c = conn.cursor()
    # 1. טבלת לקוחות ייחודיים
    c.execute('''CREATE TABLE IF NOT EXISTS clients
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  phone TEXT UNIQUE,
                  name TEXT,
                  status TEXT DEFAULT 'חדש',
                  notes TEXT DEFAULT '')''')
    # 2. טבלת הודעות מקושרות
    c.execute('''CREATE TABLE IF NOT EXISTS messages
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  client_id INTEGER,
                  date TEXT,
                  text TEXT,
                  FOREIGN KEY(client_id) REFERENCES clients(id))''')
    # 3. טבלת קבצים משויכים
    c.execute('''CREATE TABLE IF NOT EXISTS client_files
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  client_id INTEGER,
                  file_name TEXT,
                  file_data BLOB,
                  upload_date TEXT,
                  FOREIGN KEY(client_id) REFERENCES clients(id))''')
    conn.commit()
    conn.close()

def save_incoming_lead(name, phone, message_text):
    conn = sqlite3.connect('crm.db')
    c = conn.cursor()
    
    # בדיקה אם הלקוח כבר קיים לפי מספר טלפון
    c.execute("SELECT id, name FROM clients WHERE phone = ?", (phone,))
    client = c.fetchone()
    
    if client:
        client_id = client[0]
        # אם הלקוח קיים אך הסטטוס שלו היה 'טופל', נחזיר אותו ל'חדש' כי הגיעה הודעה חדשה
        c.execute("UPDATE clients SET status = 'חדש' WHERE id = ? AND status = 'טופל'", (client_id,))
    else:
        # לקוח חדש לחלוטין - יצירת תיק לקוח
        c.execute("INSERT INTO clients (phone, name, status) VALUES (?, ?, 'חדש')", (phone, name))
        client_id = c.lastrowid
        
    # שמירת ההודעה הנוכחית בהיסטוריה של הלקוח
    current_date = datetime.now().strftime("%Y-%m-%d %H:%M")
    c.execute("INSERT INTO messages (client_id, date, text) VALUES (?, ?, ?)", (client_id, current_date, message_text))
    
    conn.commit()
    conn.close()

# --- משיכת מיילים אוטומטית ---
def fetch_emails():
    try:
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
                    
                    save_incoming_lead(name, phone, subject)
                    new_leads_count += 1
                    mail.store(num, "+FLAGS", "\\Seen")
            
            mail.logout()
            return new_leads_count
        else:
            mail.logout()
            return 0
    except Exception as e:
        st.error("שגיאה בסנכרון הנתונים מול Gmail.")
        return 0

# --- אתחול מערכת ---
init_db()

# --- חלוקת המסך לשני עמודות (ניהול מול צפייה) ---
col_actions, col_main = st.columns([1, 3])

with col_actions:
    st.subheader("⚙️ פעולות מערכת")
    if st.button("🔄 סנכרן מיילים מ-CallBiz"):
        with st.spinner("בודק הודעות חדשות..."):
            count = fetch_emails()
            if count > 0:
                st.success(f"נקלטו {count} הודעות חדשות!")
                st.rerun()
            else:
                st.info("אין הודעות חדשות בתיבה.")

# טעינת נתונים עדכנית
conn = sqlite3.connect('crm.db')
clients_df = pd.read_sql_query("SELECT * FROM clients ORDER BY id DESC", conn)
conn.close()

with col_main:
    st.subheader("📂 תיקי לקוחות")
    
    if clients_df.empty:
        st.info("המערכת ריקה כעת. לחץ על כפתור הסנכרון כדי למשוך פניות ראשונות.")
    else:
        # יצירת רשימת בחירה של לקוחות עבור "תיק לקוח"
        client_options = {f"{row['name']} ({row['phone']}) - [{row['status']}]": row['id'] for _, row in clients_df.iterrows()}
        selected_client_label = st.selectbox("🎯 בחר תיק לקוח לפתיחה ועריכה:", list(client_options.keys()))
        selected_client_id = client_options[selected_client_label]
        
        # שליפת נתוני הלקוח הנבחר
        conn = sqlite3.connect('crm.db')
        c = conn.cursor()
        c.execute("SELECT * FROM clients WHERE id = ?", (selected_client_id,))
        client_data = c.fetchone()
        
        # שליפת הודעות הלקוח
        messages_df = pd.read_sql_query(f"SELECT date as 'תאריך', text as 'תוכן ההודעה' FROM messages WHERE client_id = {selected_client_id} ORDER BY id DESC", conn)
        
        # שליפת קבצי הלקוח
        files_df = pd.read_sql_query(f"SELECT id, file_name, upload_date FROM client_files WHERE client_id = {selected_client_id}", conn)
        conn.close()
        
        # הצגת כרטיס הלקוח הנבחר
        st.markdown(f"### 🗂️ תיק לקוח: {client_data[2]}")
        
        # כפתורי פעולה מהירים לנייד
        clean_phone = ''.join(filter(str.isdigit, client_data[1]))
        whatsapp_url = f"https://wa.me/{clean_phone}?text=%D7%A9%D7%9C%D7%95%D7%9D%20{client_data[2]}%2C%20%D7%A7%D7%99%D7%91%D7%9C%D7%AA%D7%99%20%D7%90%D7%AA%20%D7%A4%D7%A0%D7%99%D7%99%D7%AA%D7%9A"
        
        col_phone, col_wa, _ = st.columns([1, 1, 2])
        with col_phone:
            st.markdown(f'<a href="tel:{clean_phone}"><button style="width:100%; background-color:#007aff; color:white; border:none; padding:10px; border-radius:5px; font-weight:bold; cursor:pointer;">📞 חיוג טלפוני</button></a>', unsafe_allow_html=True)
        with col_wa:
            st.markdown(f'<a href="{whatsapp_url}" target="_blank"><button style="width:100%; background-color:#34c759; color:white; border:none; padding:10px; border-radius:5px; font-weight:bold; cursor:pointer;">💬 שלח וואטסאפ</button></a>', unsafe_allow_html=True)
            
        st.write("")
        
        # חלוקה לטאבים בתוך תיק הלקוח
        tab_history, tab_edit, tab_files = st.tabs(["📥 היסטוריית פניות", "📝 עריכת פרטים והערות", "📁 מסמכים וקבצים"])
        
        with tab_history:
            st.markdown("**כל ההודעות שהתקבלו מלקוח זה:**")
            if not messages_df.empty:
                st.dataframe(messages_df, use_container_width=True, hide_index=True)
            else:
                st.write("אין הודעות מתועדות.")
                
        with tab_edit:
            st.markdown("**עדכון פרטי הלקוח במערכת:**")
            
            # טופס עריכה
            new_name = st.text_input("שם הלקוח (לתיקון אם נכתב שגוי):", value=client_data[2])
            new_status = st.selectbox("סטטוס טיפול:", ["חדש", "בטיפול", "טופל", "לא רלוונטי"], index=["חדש", "בטיפול", "טופל", "לא רלוונטי"].index(client_data[3]))
            new_notes = st.text_area("הערות קבועות, סיכום שיחות ומידע נוסף:", value=client_data[4], height=150)
            
            if st.button("💾 שמור עדכונים בתיק הלקוח"):
                conn = sqlite3.connect('crm.db')
                c = conn.cursor()
                c.execute("UPDATE clients SET name = ?, status = ?, notes = ? WHERE id = ?", (new_name, new_status, new_notes, selected_client_id))
                conn.commit()
                conn.close()
                st.success("הפרטים עודכנו בהצלחה!")
                st.rerun()
                
        with tab_files:
            st.markdown("**ניהול מסמכים וקבצים משויכים ללקוח:**")
            
            # העלאת קובץ חדש ללקוח
            uploaded_file = st.file_uploader("העלה מסמך חדש לתיק הלקוח (PDF, תמונה, אקסל וכו'):", type=None)
            if uploaded_file is not None:
                file_bytes = uploaded_file.read()
                file_name = uploaded_file.name
                current_time = datetime.now().strftime("%Y-%m-%d %H:%M")
                
                if st.button(f"📎 שייך את הקובץ '{file_name}' ללקוח"):
                    conn = sqlite3.connect('crm.db')
                    c = conn.cursor()
                    c.execute("INSERT INTO client_files (client_id, file_name, file_data, upload_date) VALUES (?, ?, ?, ?)",
                              (selected_client_id, file_name, sqlite3.Binary(file_bytes), current_time))
                    conn.commit()
                    conn.close()
                    st.success("הקובץ שויך ונשמר בהצלחה!")
                    st.rerun()
            
            st.write("")
            st.markdown("**קבצים קיימים בתיק:**")
            if not files_df.empty:
                for _, file_row in files_df.iterrows():
                    file_id = file_row['id']
                    f_name = file_row['file_name']
                    u_date = file_row['upload_date']
                    
                    col_f_name, col_f_btn = st.columns([3, 1])
                    with col_f_name:
                        st.write(f"📄 {f_name} *(הועלה ב-{u_date})*")
                    with col_f_btn:
                        # שליפת מידע של קובץ ספציפי לצורך הורדה
                        conn = sqlite3.connect('crm.db')
                        c = conn.cursor()
                        c.execute("SELECT file_data FROM client_files WHERE id = ?", (file_id,))
                        b_data = c.fetchone()[0]
                        conn.close()
                        
                        st.download_button(label="⬇️ הורד קובץ", data=b_data, file_name=f_name, key=f"dl_{file_id}")
            else:
                st.write("עדיין לא הועלו קבצים ללקוח זה.")
