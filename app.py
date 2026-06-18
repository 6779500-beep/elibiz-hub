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

# --- עיצוב משודרג ומודרני (CSS) ---
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Heebo:wght@400;600;800&display=swap');

* {
    font-family: 'Heebo', sans-serif;
}
.stApp { direction: rtl; background-color: #f8f9fa; }
h1, h2, h3, p, div, span, label { text-align: right; }

/* עיצוב כפתורים */
.stButton>button { 
    float: right; 
    width: 100%; 
    margin-top: 10px; 
    border-radius: 8px;
    font-weight: 600;
    transition: all 0.3s ease;
}
.stButton>button:hover {
    transform: translateY(-2px);
    box-shadow: 0 4px 6px rgba(0,0,0,0.1);
}

/* כרטיסיות (Cards) לאלמנטים */
.dashboard-card {
    background-color: white;
    padding: 20px;
    border-radius: 12px;
    box-shadow: 0 4px 15px rgba(0,0,0,0.05);
    text-align: center;
    margin-bottom: 20px;
}
.dashboard-value {
    font-size: 2.5em;
    font-weight: 800;
    color: #007aff;
}
.dashboard-title {
    color: #6c757d;
    font-weight: 600;
}

.note-box {
    background-color: white;
    padding: 15px;
    border-radius: 10px;
    border-right: 5px solid #007aff;
    box-shadow: 0 2px 8px rgba(0,0,0,0.04);
    margin-bottom: 12px;
}
.task-box-open {
    background-color: white;
    padding: 15px;
    border-radius: 10px;
    border-right: 5px solid #ff9500;
    box-shadow: 0 2px 8px rgba(0,0,0,0.04);
    margin-bottom: 12px;
}
.task-box-done {
    background-color: #f1f8f1;
    padding: 15px;
    border-radius: 10px;
    border-right: 5px solid #34c759;
    margin-bottom: 12px;
    opacity: 0.7;
}

.date-span { color: #888; font-size: 0.85em; font-weight: bold; }
.status-badge {
    color: white; padding: 4px 12px; border-radius: 15px; 
    font-size: 0.6em; font-weight: bold; vertical-align: middle; 
    display: inline-block; margin-right: 10px;
}
</style>
""", unsafe_allow_html=True)

STATUS_COLORS = {
    "חדש": "#007aff", "בטיפול": "#ff9500", 
    "לטיפול עתידי": "#5856d6", "טופל": "#34c759", "לא רלוונטי": "#8e8e93"
}

# --- מסד נתונים ---
def init_db():
    conn = sqlite3.connect('crm.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS clients (id INTEGER PRIMARY KEY AUTOINCREMENT, phone TEXT UNIQUE, name TEXT, status TEXT DEFAULT 'חדש', followup_date TEXT DEFAULT '')''')
    try: c.execute("ALTER TABLE clients ADD COLUMN followup_date TEXT DEFAULT ''")
    except: pass
    c.execute('''CREATE TABLE IF NOT EXISTS messages (id INTEGER PRIMARY KEY AUTOINCREMENT, client_id INTEGER, date TEXT, text TEXT, FOREIGN KEY(client_id) REFERENCES clients(id))''')
    c.execute('''CREATE TABLE IF NOT EXISTS client_files (id INTEGER PRIMARY KEY AUTOINCREMENT, client_id INTEGER, file_name TEXT, file_data BLOB, upload_date TEXT, FOREIGN KEY(client_id) REFERENCES clients(id))''')
    c.execute('''CREATE TABLE IF NOT EXISTS client_notes (id INTEGER PRIMARY KEY AUTOINCREMENT, client_id INTEGER, note_date TEXT, note_text TEXT, FOREIGN KEY(client_id) REFERENCES clients(id))''')
    
    # טבלת המשימות
    c.execute('''CREATE TABLE IF NOT EXISTS tasks
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  client_id INTEGER,
                  task_desc TEXT,
                  due_date TEXT,
                  status TEXT DEFAULT 'פתוחה',
                  created_at TEXT,
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

def save_new_task(client_id, task_desc, due_date):
    conn = sqlite3.connect('crm.db')
    c = conn.cursor()
    created_at = datetime.now().strftime("%Y-%m-%d %H:%M")
    c.execute("INSERT INTO tasks (client_id, task_desc, due_date, status, created_at) VALUES (?, ?, ?, 'פתוחה', ?)", 
              (client_id, task_desc, due_date, created_at))
    conn.commit()
    conn.close()

def mark_task_done(task_id):
    conn = sqlite3.connect('crm.db')
    c = conn.cursor()
    c.execute("UPDATE tasks SET status = 'בוצעה' WHERE id = ?", (task_id,))
    conn.commit()
    conn.close()

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
        return 0

init_db()

# --- לוח מחוונים (Dashboard) ---
st.markdown("<h1>💼 מערכת CallBiz CRM</h1>", unsafe_allow_html=True)

conn = sqlite3.connect('crm.db')
total_clients = pd.read_sql_query("SELECT COUNT(*) FROM clients", conn).iloc[0,0]
open_tasks = pd.read_sql_query("SELECT COUNT(*) FROM tasks WHERE status='פתוחה'", conn).iloc[0,0]
new_leads = pd.read_sql_query("SELECT COUNT(*) FROM clients WHERE status='חדש'", conn).iloc[0,0]
conn.close()

col1, col2, col3, col4 = st.columns(4)
with col1:
    st.markdown(f"<div class='dashboard-card'><div class='dashboard-value'>{total_clients}</div><div class='dashboard-title'>סך הכל לקוחות</div></div>", unsafe_allow_html=True)
with col2:
    st.markdown(f"<div class='dashboard-card'><div class='dashboard-value' style='color:#ff9500;'>{open_tasks}</div><div class='dashboard-title'>משימות פתוחות</div></div>", unsafe_allow_html=True)
with col3:
    st.markdown(f"<div class='dashboard-card'><div class='dashboard-value' style='color:#34c759;'>{new_leads}</div><div class='dashboard-title'>לידים חדשים</div></div>", unsafe_allow_html=True)
with col4:
    if st.button("🔄 סנכרן פניות", use_container_width=True):
        with st.spinner("סורק..."):
            count = fetch_emails()
            if count > 0: st.success(f"נקלטו {count} חדשות!"); st.rerun()
            else: st.info("אין חדש.")

st.markdown("---")

# --- התרעות ומשימות דחופות להיום ---
today_str = datetime.now().strftime("%Y-%m-%d")
conn = sqlite3.connect('crm.db')
urgent_tasks_df = pd.read_sql_query(f"""
    SELECT t.id, t.task_desc, t.due_date, c.name, c.phone 
    FROM tasks t JOIN clients c ON t.client_id = c.id 
    WHERE t.status = 'פתוחה' AND t.due_date <= '{today_str}'
""", conn)
conn.close()

if not urgent_tasks_df.empty:
    st.warning("⚠️ **יש לך משימות פתוחות שדורשות טיפול היום או שפג תוקפן!**")
    for _, t in urgent_tasks_df.iterrows():
        f_date = datetime.strptime(t['due_date'], "%Y-%m-%d").strftime("%d/%m/%Y")
        col_txt, col_btn = st.columns([5,1])
        with col_txt:
            st.markdown(f"**{t['task_desc']}** | עבור: {t['name']} ({t['phone']}) | ⏱️ יעד: {f_date}")
        with col_btn:
            if st.button("סמן כבוצע", key=f"urg_done_{t['id']}"):
                mark_task_done(t['id'])
                st.rerun()
    st.markdown("---")

# --- אזור ניהול הלקוחות ---
col_actions, col_main = st.columns([1, 3])

conn = sqlite3.connect('crm.db')
clients_df = pd.read_sql_query("SELECT * FROM clients ORDER BY id DESC", conn)
conn.close()

with col_actions:
    st.subheader("🎯 בחירת תיק לקוח")
    if not clients_df.empty:
        client_options = {f"{row['name']} ({row['phone']})": row['id'] for _, row in clients_df.iterrows()}
        selected_client_label = st.selectbox("בחר רשומה מהרשימה:", list(client_options.keys()))
        selected_client_id = client_options[selected_client_label]
    else:
        st.info("המערכת ריקה.")
        selected_client_id = None

if selected_client_id:
    with col_main:
        conn = sqlite3.connect('crm.db')
        c = conn.cursor()
        
        # תיקון מס' 1: הפרדת הפקודה מהשליפה
        c.execute("SELECT * FROM clients WHERE id = ?", (selected_client_id,))
        client_data = c.fetchone()
        
        messages_df = pd.read_sql_query(f"SELECT date, text FROM messages WHERE client_id = {selected_client_id} ORDER BY id DESC", conn)
        notes_df = pd.read_sql_query(f"SELECT note_date, note_text FROM client_notes WHERE client_id = {selected_client_id} ORDER BY id DESC", conn)
        tasks_df = pd.read_sql_query(f"SELECT id, task_desc, due_date, status, created_at FROM tasks WHERE client_id = {selected_client_id} ORDER BY due_date ASC", conn)
        files_df = pd.read_sql_query(f"SELECT id, file_name, upload_date FROM client_files WHERE client_id = {selected_client_id}", conn)
        conn.close()
        
        current_status = client_data[3]
        status_color = STATUS_COLORS.get(current_status, "#8e8e93")
        
        st.markdown(f"""
        <div style="background: white; padding: 20px; border-radius: 12px; margin-bottom: 20px; box-shadow: 0 4px 6px rgba(0,0,0,0.05);">
            <h2 style="margin: 0; color: #333;">{client_data[2]} <span class="status-badge" style="background-color: {status_color};">{current_status}</span></h2>
            <p style="margin: 5px 0 0 0; color: #666; font-size: 1.1em;">📞 {client_data[1]}</p>
        </div>
        """, unsafe_allow_html=True)
        
        tab_tasks, tab_notes, tab_history, tab_edit, tab_files = st.tabs(["✅
