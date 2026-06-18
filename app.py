import streamlit as st
import imaplib
import email
import re
from bs4 import BeautifulSoup
import sqlite3
import pandas as pd
from datetime import datetime

# --- הגדרות דף ---
st.set_page_config(page_title="CallBiz CRM", page_icon="💼", layout="wide")

# --- הזרקת קוד עיצוב (CSS) ליישור לימין וצבעי סטטוסים ---
st.markdown("""
<style>
.stApp { direction: rtl; }
h1, h2, h3, p, div, span, label { text-align: right; }
.stButton>button { float: right; width: 100%; margin-top: 10px; }
.stAlert { direction: rtl; text-align: right; }
div[data-testid="stExpander"] { text-align: right; direction: rtl; }
.note-box {
    background-color: #f0f2f6;
    padding: 12px;
    border-radius: 8px;
    border-right: 4px solid #007aff;
    margin-bottom: 10px;
}
.date-span {
    color: #666666;
    font-size: 0.85em;
    font-weight: bold;
}
.status-badge {
    color: white;
    padding: 4px 12px;
    border-radius: 15px;
    font-size: 0.6em;
    font-weight: bold;
    vertical-align: middle;
    display: inline-block;
    margin-right: 10px;
}
</style>
""", unsafe_allow_html=True)

st.title("💼 מערכת CallBiz CRM האישית שלך")

# מילון צבעים קבוע לסטטוסים
STATUS_COLORS = {
    "חדש": "#007aff",         # כחול
    "בטיפול": "#ff9500",      # כתום
    "לטיפול עתידי": "#5856d6",  # סגול
    "טופל": "#34c759",        # ירוק
    "לא רלוונטי": "#8e8e93"   # אפור
}

# --- ניהול מסד נתונים ---
def init_db():
    conn = sqlite3.connect('crm.db')
    c = conn.cursor()
    
    # 1. טבלת לקוחות עם תמיכה בתאריך יעד
    c.execute('''CREATE TABLE IF NOT EXISTS clients
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  phone TEXT UNIQUE,
                  name TEXT,
                  status TEXT DEFAULT 'חדש',
                  followup_date TEXT DEFAULT '')''')
                  
    # הגנה למסד נתונים קיים - הוספת העמודה החדשה אם היא לא קיימת
    try:
        c.execute("ALTER TABLE clients ADD COLUMN followup_date TEXT DEFAULT ''")
        conn.commit()
    except sqlite3.OperationalError:
        pass # העמודה כבר קיימת, אין צורך בשינוי
        
    # 2. טבלת הודעות מ-CallBiz
    c.execute('''CREATE TABLE IF NOT EXISTS messages
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  client_id INTEGER,
                  date TEXT,
                  text TEXT,
                  FOREIGN KEY(client_id) REFERENCES clients(id))''')
                  
    # 3. טבלת קבצים
    c.execute('''CREATE TABLE IF NOT EXISTS client_files
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  client_id INTEGER,
                  file_name TEXT,
                  file_data BLOB,
                  upload_date TEXT,
                  FOREIGN KEY(client_id) REFERENCES clients(id))''')
                  
    # 4. טבלת הערות
    c.execute('''CREATE TABLE IF NOT EXISTS client_notes
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  client_id INTEGER,
                  note_date TEXT,
                  note_text TEXT,
                  FOREIGN KEY(client_id) REFERENCES clients(id))''')
                  
    conn.commit()
    conn.close()

def save_incoming_lead(name, phone, message_text):
    conn = sqlite3.connect('crm.db')
    c = conn.cursor()
    
    c.execute("SELECT id FROM clients WHERE phone = ?", (phone,))
    client = c.fetchone()
    
    if client:
        client_id = client[0]
        c.execute("UPDATE clients SET status = 'חדש' WHERE id = ? AND status = 'טופל'", (client_id,))
    else:
        c.execute("INSERT INTO clients (phone, name, status, followup_date) VALUES (?, ?, 'חדש', '')", (phone, name))
        client_id = c.lastrowid
        
    current_date = datetime.now().strftime("%Y-%m-%d %H:%M")
    c.execute("INSERT INTO messages (client_id, date, text) VALUES (?, ?, ?)", (client_id, current_date, message_text))
    
    conn.commit()
    conn.close()

def save_new_note(client_id, note_text):
    conn = sqlite3.connect('crm.db')
    c = conn.cursor()
    current_date = datetime.now().strftime("%Y-%m-%d %H:%M")
    c.execute("INSERT INTO client_notes (client_id, note_date, note_text) VALUES (?, ?, ?)", 
              (client_id, current_date, note_text))
    conn.commit()
    conn.close()

# --- משיכת מיילים ---
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

# --- חלוקת המסך ---
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

# טעינת נתונים כללית
conn = sqlite3.connect('crm.db')
clients_df = pd.read_sql_query("SELECT * FROM clients ORDER BY id DESC", conn)
conn.close()

with col_main:
    # --- מנגנון תזכורות אקטיבי בראש עמוד הלקוחות ---
    today_str = datetime.now().strftime("%Y-%m-%d")
    conn = sqlite3.connect('crm.db')
    reminders_df = pd.read_sql_query(f"""
        SELECT name, phone, followup_date 
        FROM clients 
        WHERE status = 'לטיפול עתידי' AND followup_date <= '{today_str}' AND followup_date != ''
    """, conn)
    conn.close()
    
    if not reminders_df.empty:
        st.markdown("### 🔔 תזכורות חמות לטיפול היום!")
        for _, r_row in reminders_df.iterrows():
            # המרת פורמט תאריך לתצוגה ישראלית נוחה
            formatted_date = datetime.strptime(r_row['followup_date'], "%Y-%m-%d").strftime("%d/%m/%Y")
            st.error(f"🚨 **הגיע מועד המעקב:** חזרה אל **{r_row['name']}** ({r_row['phone']}) | תאריך יעד: {formatted_date}")
        st.markdown("---")

    st.subheader("📂 תיקי לקוחות")
    
    if clients_df.empty:
        st.info("המערכת ריקה כעת. לחץ על כפתור הסנכרון כדי למשוך פניות ראשונות.")
    else:
        client_options = {f"{row['name']} ({row['phone']}) - [{row['status']}]": row['id'] for _, row in clients_df.iterrows()}
        selected_client_label = st.selectbox("🎯 בחר תיק לקוח לפתיחה ועריכה:", list(client_options.keys()))
        selected_client_id = client_options[selected_client_label]
        
        # שליפת נתוני הלקוח הנבחר
        conn = sqlite3.connect('crm.db')
        c = conn.cursor()
        c.execute("SELECT * FROM clients WHERE id = ?", (selected_client_id,))
        client_data = c.fetchone()
        
        # שליפת הודעות, הערות וקבצים
        messages_df = pd.read_sql_query(f"SELECT date as 'תאריך', text as 'תוכן ההודעה' FROM messages WHERE client_id = {selected_client_id} ORDER BY id DESC", conn)
        notes_df = pd.read_sql_query(f"SELECT note_date, note_text FROM client_notes WHERE client_id = {selected_client_id} ORDER BY id DESC", conn)
        files_df = pd.read_sql_query(f"SELECT id, file_name, upload_date FROM client_files WHERE client_id = {selected_client_id} ORDER BY id DESC", conn)
        conn.close()
        
        # הצגת כרטיס הלקוח עם תג סטטוס צבעוני
        current_status = client_data[3]
        status_color = STATUS_COLORS.get(current_status, "#8e8e93")
        
        st.markdown(f"""
        ### 🗂️ תיק לקוח: {client_data[2]} 
        <span class="status-badge" style="background-color: {status_color};">{current_status}</span>
        """, unsafe_allow_html=True)
        
        if current_status == "לטיפול עתידי" and client_data[4]:
            f_date = datetime.strptime(client_data[4], "%Y-%m-%d").strftime("%d/%m/%Y")
            st.markdown(f"⏱️ **תאריך יעד למעקב:** {f_date}")
        
        st.write("")
        
        # כפתורי פעולה מהירים לנייד
        clean_phone = ''.join(filter(str.isdigit, client_data[1]))
        whatsapp_url = f"https://wa.me/{clean_phone}?text=%D7%A9%D7%9C%D7%95%D7%9D%20{client_data[2]}%2C%20%D7%A7%D7%99%D7%91%D7%9C%D7%AA%D7%99%20%D7%90%D7%AA%20%D7%A4%D7%A0%D7%99%D7%99%D7%AA%D7%9A"
        
        col_phone, col_wa, _ = st.columns([1, 1, 2])
        with col_phone:
            st.markdown(f'<a href="tel:{clean_phone}"><button style="width:100%; background-color:#007aff; color:white; border:none; padding:10px; border-radius:5px; font-weight:bold; cursor:pointer;">📞 חיוג טלפוני</button></a>', unsafe_allow_html=True)
        with col_wa:
            st.markdown(f'<a href="{whatsapp_url}" target="_blank"><button style="width:100%; background-color:#34c759; color:white; border:none; padding:10px; border-radius:5px; font-weight:bold; cursor:pointer;">💬 שלח וואטסאפ</button></a>', unsafe_allow_html=True)
            
        st.write("")
        
        tab_history, tab_notes, tab_edit, tab_files = st.tabs(["📥 היסטוריית פניות מערכת", "✍️ הערות ותיעוד ידני", "📝 עריכת סטטוס ושם", "📁 מסמכים וקבצים"])
        
        with tab_history:
            st.markdown("**הודעות אוטומטיות שהתקבלו מ-CallBiz עבור לקוח זה:**")
            if not messages_df.empty:
                st.dataframe(messages_df, use_container_width=True, hide_index=True)
            else:
                st.write("אין הודעות מערכת מתועדות.")
                
        with tab_notes:
            st.markdown("**✍️ הוספת הערה חדשה לתיק:**")
            new_note_input = st.text_area("הקלד הערה חדשה:", value="", height=100, key=f"note_input_{selected_client_id}")
            
            if st.button("💾 שמור הערה בתיק הלקוח"):
                if new_note_input.strip() != "":
                    save_new_note(selected_client_id, new_note_input.strip())
                    st.success("ההערה נשמרה בהצלחה בציר הזמן!")
                    st.rerun()
                else:
                    st.warning("לא ניתן לשמור הערה ריקה.")
            
            st.markdown("---")
            st.markdown("**📜 ציר זמן - הערות מתועדות:**")
            if not notes_df.empty:
                for _, note_row in notes_df.iterrows():
                    st.markdown(f"""
                    <div class="note-box">
                        <span class="date-span">📅 {note_row['note_date']}</span><br>
                        <p style="margin-top:5px; margin-bottom:0; white-space: pre-wrap;">{note_row['note_text']}</p>
                    </div>
                    """, unsafe_allow_html=True)
            else:
                st.write("עדיין אין הערות ידניות בתיק זה.")
                
        with tab_edit:
            st.markdown("**עדכון פרטי זיהוי וסטטוס:**")
            new_name = st.text_input("תיקון שם הלקוח (אם נכתב משובש במקור):", value=client_data[2])
            
            status_options = ["חדש", "בטיפול", "לטיפול עתידי", "טופל", "לא רלוונטי"]
            try:
                current_idx = status_options.index(client_data[3])
            except ValueError:
                current_idx = 0
                
            new_status = st.selectbox("סטטוס טיפול נוכחי:", status_options, index=current_idx)
            
            # הצגת בחירת תאריך רק אם נבחר סטטוס לטיפול עתידי
            new_followup_date = client_data[4] if len(client_data) > 4 else ""
            if new_status == "לטיפול עתידי":
                # טעינת התאריך הקיים או ברירת מחדל של היום
                try:
                    default_date = datetime.strptime(client_data[4], "%Y-%m-%d").date() if client_data[4] else datetime.now().date()
                except ValueError:
                    default_date = datetime.now().date()
                    
                picked_date = st.date_input("📅 בחר תאריך יעד לתזכורת המעקב:", value=default_date)
                new_followup_date = picked_date.strftime("%Y-%m-%d")
            else:
                # אם הסטטוס שונה, ננקה את תאריך היעד
                new_followup_date = ""
            
            if st.button("💾 שמור שינויי שם, סטטוס ותאריך"):
                conn = sqlite3.connect('crm.db')
                c = conn.cursor()
                c.execute("UPDATE clients SET name = ?, status = ?, followup_date = ? WHERE id = ?", 
                          (new_name, new_status, new_followup_date, selected_client_id))
                conn.commit()
                conn.close()
                st.success("הפרטים והסטטוס עודכנו בהצלחה!")
                st.rerun()
                
        with tab_files:
            st.markdown("**ניהול מסמכים וקבצים משויכים ללקוח:**")
            uploaded_file = st.file_uploader("בחר קובץ להעלאה (PDF, תמונה, אקסל וכו'):", type=None)
            if uploaded_file is not None:
                file_bytes = uploaded_file.read()
                file_name = uploaded_file.name
                current_time = datetime.now().strftime("%Y-%m-%d %H:%M")
                
                if st.button(f"📎 העלה ושייך את הקובץ '{file_name}'"):
                    conn = sqlite3.connect('crm.db')
                    c = conn.cursor()
                    c.execute("INSERT INTO client_files (client_id, file_name, file_data, upload_date) VALUES (?, ?, ?, ?)",
                              (selected_client_id, file_name, sqlite3.Binary(file_bytes), current_time))
                    conn.commit()
                    conn.close()
                    st.success("הקובץ נשמר בהצלחה בתיק הלקוח!")
                    st.rerun()
            
            st.write("")
            st.markdown("**📋 רשימת מסמכים בתיק:**")
            if not files_df.empty:
                for _, file_row in files_df.iterrows():
                    file_id = file_row['id']
                    f_name = file_row['file_name']
                    u_date = file_row['upload_date']
                    
                    col_f_name, col_f_btn = st.columns([3, 1])
                    with col_f_name:
                        st.markdown(f"📄 **{f_name}** <br> <span style='color:#666; font-size:0.85em;'>⏱️ הועלה ב: {u_date}</span>", unsafe_allow_html=True)
                    with col_f_btn:
                        conn = sqlite3.connect('crm.db')
                        c = conn.cursor()
                        c.execute("SELECT file_data FROM client_files WHERE id = ?", (file_id,))
                        b_data = c.fetchone()[0]
                        conn.close()
                        
                        st.download_button(label="⬇️ הורד קובץ", data=b_data, file_name=f_name, key=f"dl_{file_id}")
            else:
                st.write("עדיין לא הועלו קבצים ללקוח זה.")
