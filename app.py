import streamlit as st
import sqlite3
import pandas as pd
import imaplib
import email
import re
import os
import base64
from datetime import datetime, date
from bs4 import BeautifulSoup

# --- עיצוב ממשק פרימיום (RTL ועברית מלאה) ---
st.set_page_config(page_title="CallBiz CRM", layout="wide")

st.html("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Heebo:wght@400;500;600;700;800&display=swap');
* { font-family: 'Heebo', sans-serif !important; }
.stApp { direction: rtl; text-align: right; background-color: #f6f4ef; }
[data-testid="stAppViewContainer"] { background-color: #f6f4ef; }

/* שורת התראות */
.alert-bar {
    background: linear-gradient(135deg, #15182e 0%, #1f2440 50%, #2b1f47 100%);
    color: white; padding: 12px 24px; border-radius: 12px;
    margin-bottom: 20px; display: flex; align-items: center;
    gap: 16px; flex-wrap: wrap; direction: rtl;
    box-shadow: 0 4px 15px rgba(20,16,40,0.35);
    border: 1px solid rgba(201,162,39,0.25);
}
.alert-badge {
    background: linear-gradient(135deg, #b3472f, #8e2f3a); color: white; border-radius: 20px;
    padding: 4px 12px; font-weight: 700; font-size: 13px;
    animation: pulse 2s infinite;
}
.alert-badge-warn {
    background: linear-gradient(135deg, #c9a227, #a9791a); color: #1f1500; border-radius: 20px;
    padding: 4px 12px; font-weight: 700; font-size: 13px;
}
@keyframes pulse { 0%,100%{opacity:1} 50%{opacity:0.7} }

/* כרטיסיות */
.card {
    background: white; padding: 24px; border-radius: 14px;
    box-shadow: 0 4px 18px rgba(31,28,53,0.07); margin-bottom: 20px;
    border: 1px solid #ece7da; border-top: 3px solid #c9a227;
}

/* כותרת ראשית */
.main-title {
    color: #1f2440; text-align: center; font-weight: 800;
    font-size: 28px; margin-bottom: 4px;
}
.main-subtitle {
    color: #8a8472; text-align: center; font-size: 14px;
    margin-bottom: 0;
}

/* כפתורים */
.stButton>button {
    background: linear-gradient(135deg, #1f2440, #2b3160); color: #f3e9c8; border-radius: 8px;
    font-weight: 600; border: 1px solid #c9a227; padding: 10px 20px;
    transition: all 0.2s ease; width: 100%;
}
.stButton>button:hover {
    background: linear-gradient(135deg, #2b3160, #3a4180); color: #ffffff;
    border-color: #e0bb3a; transform: translateY(-1px);
}

/* תגיות סטטוס */
.status-new { background:#e7edfb; color:#1d3a8f; padding:3px 10px; border-radius:20px; font-size:12px; font-weight:600; }
.status-inprogress { background:#fdf0d5; color:#92660b; padding:3px 10px; border-radius:20px; font-size:12px; font-weight:600; }
.status-closed { background:#e3f5ec; color:#0f7a4e; padding:3px 10px; border-radius:20px; font-size:12px; font-weight:600; }
.status-irrelevant { background:#eef0f2; color:#5b6472; padding:3px 10px; border-radius:20px; font-size:12px; font-weight:600; }
.status-followup { background:#f1e7fb; color:#6b2fa0; padding:3px 10px; border-radius:20px; font-size:12px; font-weight:600; }

/* תיק לקוח */
.client-header {
    background: linear-gradient(135deg, #1f2440, #2b3160);
    color: #f3e9c8; padding: 16px 20px; border-radius: 10px;
    margin-bottom: 16px; border: 1px solid #c9a227;
}
.client-header h3 { margin:0; font-size:18px; font-weight:700; color:#ffffff; }
.client-header p { margin:4px 0 0 0; opacity:0.85; font-size:13px; }

/* הערות */
.note-item {
    background: #faf9f5; border-right: 3px solid #c9a227;
    padding: 10px 14px; border-radius: 0 8px 8px 0;
    margin-bottom: 8px;
}
.note-item .note-text { color: #1e293b; font-size:14px; margin-bottom:4px; }
.note-item .note-date { color: #94a3b8; font-size:11px; }

/* משימות */
.task-item {
    background: #faf9f5; border: 1px solid #ece7da;
    padding: 10px 14px; border-radius: 8px; margin-bottom: 8px;
    display: flex; align-items: center; gap: 10px;
}
.task-done { text-decoration: line-through; color: #94a3b8; }

/* קבצים */
.file-item {
    background: #faf9f5; border: 1px solid #ece7da;
    padding: 10px 14px; border-radius: 8px; margin-bottom: 8px;
    display: flex; align-items: center; gap: 10px;
}

.stTabs [data-baseweb="tab"] { font-weight: 600; font-size: 14px; }

/* לוח משימות דחופות גלובלי */
.urgent-box {
    background: #fdf6e3; border-right: 4px solid #c9a227;
    padding: 10px 14px; border-radius: 0 8px 8px 0; margin-bottom: 8px;
}
.urgent-box .urgent-desc { color: #1e293b; font-weight: 600; font-size: 14px; }
.urgent-box .urgent-meta { color: #8a6300; font-size: 12px; margin-top: 2px; }

/* טבלת לקוחות מותאמת */
.client-table-header {
    display: flex; align-items: center; padding: 10px 16px;
    color: #8a8472; font-size: 12px; font-weight: 700;
    border-bottom: 2px solid #ece7da;
}
.client-row {
    display: flex; align-items: center; padding: 14px 16px;
    background: #ffffff; text-decoration: none !important;
    border-bottom: 1px solid #f1eee5; transition: background 0.15s ease;
}
.client-row:hover { background: #fbf6e6; }
.client-row.selected { background: #fbf3d6; border-right: 4px solid #c9a227; }
.client-row .cell { color: #1f2440; font-size: 14px; }
.client-row .cell-id { color: #8a8472; font-size: 13px; }
.client-row .cell-phone { direction: ltr; text-align: right; }

/* התראה על כפילות אפשרית */
.dup-warning {
    background: #fdf0d5; border: 1px solid #c9a227; border-right: 4px solid #c9a227;
    padding: 14px 16px; border-radius: 8px; margin-bottom: 12px; color: #5b4400;
}

/* רשימת ממתינים בלשונית התראות */
.pending-item {
    display: block; text-decoration: none !important; background: #faf9f5;
    border: 1px solid #ece7da; border-radius: 8px; padding: 10px 14px;
    margin-bottom: 8px; transition: background 0.15s ease;
}
.pending-item:hover { background: #fbf6e6; }
.pending-item .pending-title { color: #1f2440; font-weight: 600; font-size: 14px; }
.pending-item .pending-meta { color: #8a8472; font-size: 12px; margin-top: 2px; }

/* תגיות תיעדוף */
.priority-urgent { background:#fbe2e1; color:#a13b32; padding:3px 10px; border-radius:20px; font-size:12px; font-weight:600; }
.priority-soon { background:#fdebd3; color:#9a5b13; padding:3px 10px; border-radius:20px; font-size:12px; font-weight:600; }
.priority-week { background:#dcf2ee; color:#0f766e; padding:3px 10px; border-radius:20px; font-size:12px; font-weight:600; }

/* תגיות סיווג */
.category-new { background:#e3eefc; color:#2563a8; padding:3px 10px; border-radius:20px; font-size:12px; font-weight:600; }
.category-retention { background:#e6f4ea; color:#2f7d4f; padding:3px 10px; border-radius:20px; font-size:12px; font-weight:600; }
.category-recruit { background:#efe6fb; color:#6b3fa0; padding:3px 10px; border-radius:20px; font-size:12px; font-weight:600; }
.category-recruit-retention { background:#fbe7ee; color:#a13d63; padding:3px 10px; border-radius:20px; font-size:12px; font-weight:600; }
</style>
""")

# --- תשתית מסד נתונים ---
UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

def init_db():
    conn = sqlite3.connect('crm.db')
    c = conn.cursor()

    # טבלת לקוחות
    c.execute('''CREATE TABLE IF NOT EXISTS clients (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        phone TEXT UNIQUE,
        status TEXT DEFAULT "חדש",
        created_at TEXT DEFAULT (datetime('now','localtime'))
    )''')

    # מיגרציה: עמודות נוספות לכרטיס לקוח (מצורפות בבטחה לטבלה קיימת)
    existing_cols = {row[1] for row in c.execute("PRAGMA table_info(clients)").fetchall()}
    for col_name, col_def in [
        ("id_number", "TEXT DEFAULT ''"),
        ("phone2", "TEXT DEFAULT ''"),
        ("phone2_label", "TEXT DEFAULT ''"),
        ("phone3", "TEXT DEFAULT ''"),
        ("phone3_label", "TEXT DEFAULT 'נייח'"),
        ("follow_up_date", "TEXT DEFAULT ''"),
        ("priority", "TEXT DEFAULT ''"),
        ("category", "TEXT DEFAULT ''"),
    ]:
        if col_name not in existing_cols:
            c.execute(f"ALTER TABLE clients ADD COLUMN {col_name} {col_def}")

    # טבלת הערות
    c.execute('''CREATE TABLE IF NOT EXISTS notes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        client_id INTEGER,
        content TEXT,
        created_at TEXT DEFAULT (datetime('now','localtime')),
        FOREIGN KEY(client_id) REFERENCES clients(id)
    )''')

    # טבלת משימות
    c.execute('''CREATE TABLE IF NOT EXISTS tasks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        client_id INTEGER,
        description TEXT,
        due_date TEXT,
        is_done INTEGER DEFAULT 0,
        created_at TEXT DEFAULT (datetime('now','localtime')),
        updated_at TEXT DEFAULT (datetime('now','localtime')),
        FOREIGN KEY(client_id) REFERENCES clients(id)
    )''')

    # טבלת קבצים
    c.execute('''CREATE TABLE IF NOT EXISTS files (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        client_id INTEGER,
        filename TEXT,
        filepath TEXT,
        uploaded_at TEXT DEFAULT (datetime('now','localtime')),
        FOREIGN KEY(client_id) REFERENCES clients(id)
    )''')

    conn.commit()
    conn.close()

# --- מנוע סנכרון מייל ---
def sync_data():
    try:
        conn = sqlite3.connect('crm.db')
        mail = imaplib.IMAP4_SSL("imap.gmail.com")
        mail.login(st.secrets["EMAIL_ACCOUNT"], st.secrets["APP_PASSWORD"])
        mail.select("inbox")
        _, msgs = mail.search(None, '(UNSEEN FROM "CallBiz@callbiz.co.il")')
        count = 0
        for num in msgs[0].split():
            _, data = mail.fetch(num, "(RFC822)")
            msg = email.message_from_bytes(data[0][1])
            body = ""
            if msg.is_multipart():
                for part in msg.walk():
                    if part.get_content_type() == "text/html":
                        body = part.get_payload(decode=True).decode("utf-8", errors="ignore")
                        break
                    elif part.get_content_type() == "text/plain":
                        body = part.get_payload(decode=True).decode("utf-8", errors="ignore")
            else:
                body = msg.get_payload(decode=True).decode("utf-8", errors="ignore")

            text = BeautifulSoup(body, "html.parser").get_text()
            phone = re.search(r"(?<!\d)(0[5-9]\d{8})(?!\d)", text)
            name_match = re.search(r"שם(?: מלא| הלקוח| פונה)?\s*[:\-]\s*(.+)", text)
            lead_name = name_match.group(1).strip().split("\n")[0][:60] if name_match else "לקוח חדש"
            if phone:
                phone_value = phone.group(1)
                try:
                    conn.execute("INSERT INTO clients (name, phone) VALUES (?, ?)",
                                 (lead_name, phone_value))
                    count += 1
                except sqlite3.IntegrityError:
                    existing = conn.execute(
                        "SELECT id FROM clients WHERE phone=?", (phone_value,)).fetchone()
                    if existing:
                        conn.execute(
                            "INSERT INTO notes (client_id, content) VALUES (?,?)",
                            (existing[0], f"התקבלה פנייה נוספת מהמייל ({lead_name})."))
            mail.store(num, "+FLAGS", "\\Seen")

        conn.execute(
            "DELETE FROM clients WHERE phone IS NULL OR phone='' OR phone LIKE '%-%' OR phone='לא נמצא'")
        conn.commit()
        conn.close()
        return True, count
    except Exception as e:
        return False, str(e)

# --- שאילתות עזר ---
def get_clients(search=""):
    conn = sqlite3.connect('crm.db')
    query = "SELECT id, name, phone, phone2, id_number, status, priority, category, created_at FROM clients"
    params = ()
    if search.strip():
        query += " WHERE name LIKE ? OR phone LIKE ? OR phone2 LIKE ? OR phone3 LIKE ? OR id_number LIKE ?"
        like = f"%{search.strip()}%"
        params = (like, like, like, like, like)
    query += " ORDER BY id DESC"
    df = pd.read_sql_query(query, conn, params=params)
    conn.close()
    return df

def get_alerts():
    conn = sqlite3.connect('crm.db')
    today = date.today().isoformat()
    new_count = conn.execute("SELECT COUNT(*) FROM clients WHERE status='חדש'").fetchone()[0]
    urgent_tasks = conn.execute(
        "SELECT COUNT(*) FROM tasks WHERE is_done=0 AND due_date<=? AND due_date!=''", (today,)
    ).fetchone()[0]
    due_followups = conn.execute(
        "SELECT COUNT(*) FROM clients WHERE status='לטיפול עתידי' AND follow_up_date!='' AND follow_up_date<=?",
        (today,)
    ).fetchone()[0]
    conn.close()
    return new_count, urgent_tasks, due_followups

def get_urgent_tasks():
    conn = sqlite3.connect('crm.db')
    today = date.today().isoformat()
    rows = conn.execute("""
        SELECT t.id, t.description, t.due_date, c.name, c.id
        FROM tasks t JOIN clients c ON t.client_id = c.id
        WHERE t.is_done=0 AND t.due_date!='' AND t.due_date<=?
        ORDER BY t.due_date ASC
    """, (today,)).fetchall()
    conn.close()
    return rows

def get_due_followups():
    conn = sqlite3.connect('crm.db')
    today = date.today().isoformat()
    rows = conn.execute("""
        SELECT id, name, follow_up_date FROM clients
        WHERE status='לטיפול עתידי' AND follow_up_date!='' AND follow_up_date<=?
        ORDER BY follow_up_date ASC
    """, (today,)).fetchall()
    conn.close()
    return rows

def get_new_leads():
    conn = sqlite3.connect('crm.db')
    rows = conn.execute(
        "SELECT id, name, phone, created_at FROM clients WHERE status='חדש' ORDER BY created_at DESC"
    ).fetchall()
    conn.close()
    return rows

def add_note(client_id, content):
    conn = sqlite3.connect('crm.db')
    conn.execute("INSERT INTO notes (client_id, content) VALUES (?,?)", (client_id, content))
    conn.commit()
    conn.close()

def find_duplicate_clients(name="", phone="", id_number="", exclude_id=None):
    conn = sqlite3.connect('crm.db')
    matches = {}
    if phone:
        for row in conn.execute(
            "SELECT id, name, phone, status FROM clients WHERE phone=? OR phone2=? OR phone3=?",
            (phone, phone, phone)).fetchall():
            matches[row[0]] = (*row, "טלפון")
    if id_number:
        for row in conn.execute(
            "SELECT id, name, phone, status FROM clients WHERE id_number=? AND id_number!=''",
            (id_number,)).fetchall():
            matches.setdefault(row[0], (*row, "תעודת זהות"))
    if name.strip():
        for row in conn.execute(
            "SELECT id, name, phone, status FROM clients WHERE name=? AND name!='' AND name!='לקוח חדש'",
            (name.strip(),)).fetchall():
            matches.setdefault(row[0], (*row, "שם"))
    conn.close()
    if exclude_id is not None:
        matches.pop(exclude_id, None)
    return list(matches.values())

def get_client(client_id):
    conn = sqlite3.connect('crm.db')
    row = conn.execute("SELECT * FROM clients WHERE id=?", (client_id,)).fetchone()
    conn.close()
    return row

def get_notes(client_id):
    conn = sqlite3.connect('crm.db')
    rows = conn.execute(
        "SELECT id, content, created_at FROM notes WHERE client_id=? ORDER BY created_at DESC",
        (client_id,)).fetchall()
    conn.close()
    return rows

def get_tasks(client_id):
    conn = sqlite3.connect('crm.db')
    rows = conn.execute(
        "SELECT id, description, due_date, is_done, created_at, updated_at FROM tasks WHERE client_id=? ORDER BY is_done, due_date",
        (client_id,)).fetchall()
    conn.close()
    return rows

def get_files(client_id):
    conn = sqlite3.connect('crm.db')
    rows = conn.execute(
        "SELECT id, filename, filepath, uploaded_at FROM files WHERE client_id=? ORDER BY uploaded_at DESC",
        (client_id,)).fetchall()
    conn.close()
    return rows

init_db()

# ===== ממשק ראשי =====

# כותרת
st.markdown('''
<div class="card">
  <p class="main-title">💼 מערכת ניהול לקוחות CallBiz</p>
  <p class="main-subtitle">ריכוז לידים, ניהול תיקי לקוח ומשימות</p>
</div>
''', unsafe_allow_html=True)

STATUS_BADGE_CLASS = {
    "חדש": "status-new",
    "בטיפול": "status-inprogress",
    "לטיפול עתידי": "status-followup",
    "נסגר": "status-closed",
    "לא רלוונטי": "status-irrelevant",
}
STATUS_OPTIONS = ["חדש", "בטיפול", "לטיפול עתידי", "נסגר", "לא רלוונטי"]

PRIORITY_BADGE_CLASS = {
    "דחוף": "priority-urgent",
    "לטיפול בהקדם": "priority-soon",
    "בשבוע-שבועיים הקרובים": "priority-week",
}
PRIORITY_OPTIONS = ["", "דחוף", "לטיפול בהקדם", "בשבוע-שבועיים הקרובים"]

CATEGORY_BADGE_CLASS = {
    "לקוח חדש": "category-new",
    "שימור קיים": "category-retention",
    "גיוס פוטנציאלי": "category-recruit",
    "שימור גיוס": "category-recruit-retention",
}
CATEGORY_OPTIONS = ["", "לקוח חדש", "שימור קיים", "גיוס פוטנציאלי", "שימור גיוס"]

# --- ניתוב לפי פרמטרי כתובת ---
view = st.query_params.get("view")
selected_client_id = st.query_params.get("client_id")
selected_client_id = int(selected_client_id) if selected_client_id else None

# --- שורת התראות (לחיצה פותחת את רשימת הממתינים) ---
new_leads, urgent_tasks, due_followups = get_alerts()
alerts_html = '<div class="alert-bar">🔔 <strong>התראות:</strong>'
if new_leads > 0:
    alerts_html += f'&nbsp;<a href="?view=alerts" target="_self" class="alert-badge" style="color:white">📥 {new_leads} פניות חדשות לטיפול</a>'
else:
    alerts_html += '&nbsp;<span style="font-size:13px;opacity:0.7">אין פניות חדשות</span>'
if urgent_tasks > 0:
    alerts_html += f'&nbsp;<a href="?view=alerts" target="_self" class="alert-badge-warn" style="color:#1f1500">⚡ {urgent_tasks} משימות דחופות להיום</a>'
if due_followups > 0:
    alerts_html += f'&nbsp;<a href="?view=alerts" target="_self" class="alert-badge-warn" style="color:#1f1500">🔁 {due_followups} מועדי טיפול עתידי</a>'
if urgent_tasks == 0 and due_followups == 0:
    alerts_html += '&nbsp;<span style="font-size:13px;opacity:0.7"> | אין משימות דחופות</span>'
alerts_html += '</div>'
st.markdown(alerts_html, unsafe_allow_html=True)

# ===================== מצב 1: לשונית התראות/ממתינים =====================
if view == "alerts":
    st.markdown('<a href="?" target="_self">← חזרה לרשימת הלקוחות</a>', unsafe_allow_html=True)

    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.subheader("📥 פניות חדשות")
    leads = get_new_leads()
    if not leads:
        st.info("אין פניות חדשות.")
    else:
        for l_id, l_name, l_phone, l_created in leads:
            st.markdown(f'''
            <a class="pending-item" href="?client_id={l_id}" target="_self">
                <div class="pending-title">👤 {l_name}</div>
                <div class="pending-meta">📞 {l_phone} &nbsp;|&nbsp; 🗓 התקבל: {l_created[:10] if l_created else "-"}</div>
            </a>
            ''', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.subheader("⏰ משימות דחופות")
    urgent_list = get_urgent_tasks()
    if not urgent_list:
        st.info("אין משימות דחופות.")
    else:
        today_str = date.today().isoformat()
        for t_id, t_desc, t_due, c_name, c_id in urgent_list:
            label = "באיחור" if t_due < today_str else "להיום"
            st.markdown(f'''
            <a class="pending-item" href="?client_id={c_id}" target="_self">
                <div class="pending-title">{t_desc}</div>
                <div class="pending-meta">👤 {c_name} &nbsp;|&nbsp; 🗓 {t_due} ({label})</div>
            </a>
            ''', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.subheader("🔁 מועדי טיפול עתידי שהגיעו")
    followups = get_due_followups()
    if not followups:
        st.info("אין מועדי טיפול עתידי שהגיעו.")
    else:
        for f_id, f_name, f_due in followups:
            st.markdown(f'''
            <a class="pending-item" href="?client_id={f_id}" target="_self">
                <div class="pending-title">👤 {f_name}</div>
                <div class="pending-meta">🗓 מועד טיפול: {f_due}</div>
            </a>
            ''', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

# ===================== מצב 2: תיק לקוח פתוח (מסך מלא) =====================
elif selected_client_id is not None and get_client(selected_client_id):
    client_id = selected_client_id
    client = get_client(client_id)

    st.markdown('<a href="?" target="_self">← חזרה לרשימת הלקוחות</a>', unsafe_allow_html=True)

    if client:
        (c_id, c_name, c_phone, c_status, c_created,
         c_id_number, c_phone2, c_phone2_label, c_phone3, c_phone3_label, c_followup,
         c_priority, c_category) = client

        badges_html = f'<span class="{STATUS_BADGE_CLASS.get(c_status, "status-irrelevant")}">{c_status}</span>'
        if c_priority:
            badges_html += f' <span class="{PRIORITY_BADGE_CLASS.get(c_priority, "")}">{c_priority}</span>'
        if c_category:
            badges_html += f' <span class="{CATEGORY_BADGE_CLASS.get(c_category, "")}">{c_category}</span>'

        # כותרת תיק
        st.markdown(f'''
        <div class="client-header">
          <h3>📂 תיק לקוח: {c_name}</h3>
          <p>📞 {c_phone} &nbsp;|&nbsp; 🗓 נקלט: {c_created[:10] if c_created else "-"}</p>
          <p>{badges_html}</p>
        </div>
        ''', unsafe_allow_html=True)

        tab_details, tab_docs, tab_notes = st.tabs(["📄 פרטים", "📎 מסמכים", "📝 הערות ומשימות"])

        # ==================== לשונית 1: פרטים ====================
        with tab_details:
            st.markdown('<div class="card">', unsafe_allow_html=True)

            col1, col2 = st.columns(2)
            with col1:
                new_name = st.text_input("שם לקוח", value=c_name, key=f"name_{client_id}")
            with col2:
                new_phone = st.text_input("מספר טלפון", value=c_phone, key=f"phone_{client_id}")

            col_id, col_status = st.columns(2)
            with col_id:
                new_id_number = st.text_input("תעודת זהות", value=c_id_number or "", key=f"idnum_{client_id}")
            with col_status:
                status_idx = STATUS_OPTIONS.index(c_status) if c_status in STATUS_OPTIONS else 0
                new_status = st.selectbox("סטטוס פנייה", options=STATUS_OPTIONS,
                                           index=status_idx, key=f"status_{client_id}")

            new_followup_date = c_followup
            if new_status == "לטיפול עתידי":
                followup_value = datetime.strptime(c_followup, "%Y-%m-%d").date() if c_followup else None
                followup_input = st.date_input("מועד טיפול עתידי", value=followup_value, key=f"followup_{client_id}")
                new_followup_date = followup_input.isoformat() if followup_input else ""

            col_prio, col_cat = st.columns(2)
            with col_prio:
                prio_idx = PRIORITY_OPTIONS.index(c_priority) if c_priority in PRIORITY_OPTIONS else 0
                new_priority = st.selectbox("תיעדוף", options=PRIORITY_OPTIONS,
                                             index=prio_idx, key=f"priority_{client_id}")
            with col_cat:
                cat_idx = CATEGORY_OPTIONS.index(c_category) if c_category in CATEGORY_OPTIONS else 0
                new_category = st.selectbox("סיווג", options=CATEGORY_OPTIONS,
                                             index=cat_idx, key=f"category_{client_id}")

            st.markdown("##### טלפונים נוספים")
            col_p2, col_p2l = st.columns([2, 1])
            with col_p2:
                new_phone2 = st.text_input("טלפון נוסף", value=c_phone2 or "", key=f"phone2_{client_id}")
            with col_p2l:
                phone2_labels = ["", "בעל", "אישה", "אחר"]
                p2l_idx = phone2_labels.index(c_phone2_label) if c_phone2_label in phone2_labels else 0
                new_phone2_label = st.selectbox("שייך ל-", options=phone2_labels, index=p2l_idx, key=f"phone2l_{client_id}")

            col_p3, col_p3l = st.columns([2, 1])
            with col_p3:
                new_phone3 = st.text_input("טלפון בבית", value=c_phone3 or "", key=f"phone3_{client_id}")
            with col_p3l:
                phone3_labels = ["נייח", "בעל", "אישה"]
                p3l_idx = phone3_labels.index(c_phone3_label) if c_phone3_label in phone3_labels else 0
                new_phone3_label = st.selectbox("סוג", options=phone3_labels, index=p3l_idx, key=f"phone3l_{client_id}")

            if st.button("💾 שמור פרטים", key=f"save_details_{client_id}"):
                conn = sqlite3.connect('crm.db')
                try:
                    conn.execute(
                        """UPDATE clients SET name=?, phone=?, status=?, id_number=?,
                           phone2=?, phone2_label=?, phone3=?, phone3_label=?, follow_up_date=?,
                           priority=?, category=?
                           WHERE id=?""",
                        (new_name, new_phone, new_status, new_id_number,
                         new_phone2, new_phone2_label, new_phone3, new_phone3_label,
                         new_followup_date if new_status == "לטיפול עתידי" else "",
                         new_priority, new_category,
                         client_id))
                    conn.commit()
                    st.success("הפרטים נשמרו!")
                    st.rerun()
                except sqlite3.IntegrityError:
                    st.error("מספר הטלפון כבר קיים במערכת.")
                finally:
                    conn.close()

            st.markdown('</div>', unsafe_allow_html=True)

        # ==================== לשונית 2: מסמכים ====================
        with tab_docs:
            st.markdown('<div class="card">', unsafe_allow_html=True)
            st.subheader("העלאת מסמכים")

            uploaded_file = st.file_uploader(
                "בחר קובץ להעלאה", key=f"upload_{client_id}",
                type=["pdf", "png", "jpg", "jpeg", "docx", "xlsx", "txt"]
            )

            if uploaded_file and st.button("📤 העלה קובץ", key=f"do_upload_{client_id}"):
                client_dir = os.path.join(UPLOAD_DIR, str(client_id))
                os.makedirs(client_dir, exist_ok=True)
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                safe_name = f"{timestamp}_{uploaded_file.name}"
                filepath = os.path.join(client_dir, safe_name)
                with open(filepath, "wb") as f:
                    f.write(uploaded_file.getbuffer())
                conn = sqlite3.connect('crm.db')
                conn.execute(
                    "INSERT INTO files (client_id, filename, filepath) VALUES (?,?,?)",
                    (client_id, uploaded_file.name, filepath))
                conn.commit()
                conn.close()
                st.success(f"הקובץ '{uploaded_file.name}' הועלה בהצלחה!")
                st.rerun()

            st.markdown("---")
            st.subheader("קבצים שהועלו")
            files = get_files(client_id)

            if not files:
                st.info("אין קבצים עדיין.")
            else:
                for f_id, f_name, f_path, f_date in files:
                    col_f1, col_f2, col_f3 = st.columns([4, 2, 1])
                    with col_f1:
                        st.markdown(f"📄 **{f_name}**")
                    with col_f2:
                        st.markdown(f"<small style='color:#94a3b8'>{f_date[:16] if f_date else ''}</small>",
                                    unsafe_allow_html=True)
                    with col_f3:
                        if st.button("🗑", key=f"del_file_{f_id}"):
                            try:
                                os.remove(f_path)
                            except:
                                pass
                            conn = sqlite3.connect('crm.db')
                            conn.execute("DELETE FROM files WHERE id=?", (f_id,))
                            conn.commit()
                            conn.close()
                            st.rerun()

            st.markdown('</div>', unsafe_allow_html=True)

        # ==================== לשונית 3: הערות ומשימות ====================
        with tab_notes:

            # --- הערות ---
            st.markdown('<div class="card">', unsafe_allow_html=True)
            st.subheader("📝 הערות")

            with st.form(key=f"note_form_{client_id}", clear_on_submit=True):
                note_text = st.text_area("הוסף הערה חדשה:", height=100, placeholder="כתוב הערה כאן...")
                if st.form_submit_button("➕ הוסף הערה"):
                    if note_text.strip():
                        conn = sqlite3.connect('crm.db')
                        conn.execute(
                            "INSERT INTO notes (client_id, content) VALUES (?,?)",
                            (client_id, note_text.strip()))
                        conn.commit()
                        conn.close()
                        st.success("ההערה נשמרה!")
                        st.rerun()

            notes = get_notes(client_id)
            if not notes:
                st.info("אין הערות עדיין.")
            else:
                for n_id, n_content, n_date in notes:
                    col_n1, col_n2 = st.columns([9, 1])
                    with col_n1:
                        st.markdown(f'''
                        <div class="note-item">
                          <div class="note-text">{n_content}</div>
                          <div class="note-date">🕐 {n_date[:16] if n_date else ""}</div>
                        </div>
                        ''', unsafe_allow_html=True)
                    with col_n2:
                        if st.button("🗑", key=f"del_note_{n_id}"):
                            conn = sqlite3.connect('crm.db')
                            conn.execute("DELETE FROM notes WHERE id=?", (n_id,))
                            conn.commit()
                            conn.close()
                            st.rerun()

            st.markdown('</div>', unsafe_allow_html=True)

            # --- משימות ---
            st.markdown('<div class="card">', unsafe_allow_html=True)
            st.subheader("✅ משימות לביצוע")

            with st.form(key=f"task_form_{client_id}", clear_on_submit=True):
                col_t1, col_t2 = st.columns([3, 1])
                with col_t1:
                    task_desc = st.text_input("תיאור המשימה:", placeholder="למשל: לחזור בשיחה, לשלוח הצעת מחיר...")
                with col_t2:
                    task_due = st.date_input("תאריך יעד:", value=None)
                if st.form_submit_button("➕ הוסף משימה"):
                    if task_desc.strip():
                        due_str = task_due.isoformat() if task_due else ""
                        conn = sqlite3.connect('crm.db')
                        conn.execute(
                            "INSERT INTO tasks (client_id, description, due_date) VALUES (?,?,?)",
                            (client_id, task_desc.strip(), due_str))
                        conn.commit()
                        conn.close()
                        st.success("המשימה נוספה!")
                        st.rerun()

            tasks = get_tasks(client_id)
            if not tasks:
                st.info("אין משימות עדיין.")
            else:
                today_str = date.today().isoformat()
                for t_id, t_desc, t_due, t_done, t_created, t_updated in tasks:
                    col_chk, col_desc, col_due, col_del = st.columns([1, 5, 2, 1])

                    is_overdue = (not t_done) and t_due and t_due < today_str

                    with col_chk:
                        new_done = st.checkbox("", value=bool(t_done), key=f"task_done_{t_id}")
                        if new_done != bool(t_done):
                            conn = sqlite3.connect('crm.db')
                            conn.execute(
                                "UPDATE tasks SET is_done=?, updated_at=datetime('now','localtime') WHERE id=?",
                                (1 if new_done else 0, t_id))
                            conn.commit()
                            conn.close()
                            st.rerun()
                    with col_desc:
                        style = "text-decoration:line-through;color:#94a3b8" if t_done else ""
                        color = "color:#e74c3c;font-weight:600" if is_overdue else ""
                        st.markdown(
                            f"<span style='{style}{color}'>{t_desc}</span>",
                            unsafe_allow_html=True)
                    with col_due:
                        if t_due:
                            label = "⚠️ " if is_overdue else "🗓 "
                            st.markdown(
                                f"<small style='color:{'#e74c3c' if is_overdue else '#64748b'}'>{label}{t_due}</small>",
                                unsafe_allow_html=True)
                    with col_del:
                        if st.button("🗑", key=f"del_task_{t_id}"):
                            conn = sqlite3.connect('crm.db')
                            conn.execute("DELETE FROM tasks WHERE id=?", (t_id,))
                            conn.commit()
                            conn.close()
                            st.rerun()

            st.markdown('</div>', unsafe_allow_html=True)

# ===================== מצב 3: רשימת הלקוחות =====================
else:
    col_sync, col_add, col_empty = st.columns([1, 1, 4])
    with col_sync:
        if st.button("🔄 סנכרן מייל"):
            with st.spinner("מסנכרן..."):
                ok, result = sync_data()
            if ok:
                st.success(f"סנכרון הושלם! נוספו {result} לקוחות חדשים.")
                st.rerun()
            else:
                st.error(f"שגיאה: {result}")
    with col_add:
        if st.button("➕ הוסף לקוח חדש"):
            st.session_state["show_add_form"] = not st.session_state.get("show_add_form", False)

    # --- טופס הוספת לקוח ידנית ---
    if st.session_state.get("show_add_form"):
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.subheader("➕ הוספת לקוח חדש")

        with st.form(key="add_client_form", clear_on_submit=False):
            col_n, col_p = st.columns(2)
            with col_n:
                add_name = st.text_input("שם לקוח")
            with col_p:
                add_phone = st.text_input("מספר טלפון")
            add_id_number = st.text_input("תעודת זהות (לא חובה)")
            submitted = st.form_submit_button("שמור לקוח")

        if submitted:
            if not add_name.strip() or not add_phone.strip():
                st.error("יש למלא שם וטלפון.")
            else:
                matches = find_duplicate_clients(add_name, add_phone.strip(), add_id_number.strip())
                phone_matches = [m for m in matches if m[4] == "טלפון"]
                other_matches = [m for m in matches if m[4] != "טלפון"]

                if phone_matches:
                    existing = phone_matches[0]
                    add_note(existing[0], f"נוצרה פנייה ידנית נוספת בשם '{add_name.strip()}'.")
                    st.warning(f"מספר הטלפון כבר קיים ללקוח '{existing[1]}' (מזהה {existing[0]}) — נוספה הערה לתיק הקיים במקום פתיחת תיק כפול.")
                elif other_matches:
                    st.session_state["pending_client"] = {
                        "name": add_name.strip(), "phone": add_phone.strip(),
                        "id_number": add_id_number.strip(),
                    }
                    st.session_state["dup_matches"] = other_matches
                    st.rerun()
                else:
                    conn = sqlite3.connect('crm.db')
                    try:
                        conn.execute(
                            "INSERT INTO clients (name, phone, id_number) VALUES (?,?,?)",
                            (add_name.strip(), add_phone.strip(), add_id_number.strip()))
                        conn.commit()
                        st.session_state["show_add_form"] = False
                        st.success("הלקוח נוסף בהצלחה!")
                        st.rerun()
                    except sqlite3.IntegrityError:
                        st.error("מספר הטלפון כבר קיים במערכת.")
                    finally:
                        conn.close()

        st.markdown('</div>', unsafe_allow_html=True)

    # --- אזהרת כפילות אפשרית: בחירה למזג או להשאיר נפרד ---
    if st.session_state.get("pending_client"):
        pending = st.session_state["pending_client"]
        dup_matches = st.session_state["dup_matches"]
        st.markdown('<div class="card">', unsafe_allow_html=True)
        match_lines = "".join(
            f"<li>{m[1]} — {m[2]} (מזהה {m[0]}, התאמה לפי {m[4]})</li>" for m in dup_matches
        )
        st.markdown(f'''
        <div class="dup-warning">
            <strong>⚠ נמצא לקוח קיים עם פרטים תואמים</strong>
            <ul>{match_lines}</ul>
            האם למזג את הפנייה לתיק הקיים, או להשאיר כתיק לקוח נפרד?
        </div>
        ''', unsafe_allow_html=True)

        col_merge, col_separate = st.columns(2)
        with col_merge:
            if st.button("🔗 מזג לתיק הקיים"):
                existing_id = dup_matches[0][0]
                add_note(existing_id, f"מוזגה פנייה ידנית: '{pending['name']}', טלפון {pending['phone']}.")
                conn = sqlite3.connect('crm.db')
                row = conn.execute("SELECT id_number, phone2 FROM clients WHERE id=?", (existing_id,)).fetchone()
                if pending["id_number"] and not row[0]:
                    conn.execute("UPDATE clients SET id_number=? WHERE id=?", (pending["id_number"], existing_id))
                if pending["phone"] and not row[1]:
                    conn.execute("UPDATE clients SET phone2=? WHERE id=?", (pending["phone"], existing_id))
                conn.commit()
                conn.close()
                st.session_state.pop("pending_client", None)
                st.session_state.pop("dup_matches", None)
                st.session_state["show_add_form"] = False
                st.success("הפנייה מוזגה לתיק הקיים.")
                st.rerun()
        with col_separate:
            if st.button("📁 השאר כתיק נפרד"):
                conn = sqlite3.connect('crm.db')
                try:
                    conn.execute(
                        "INSERT INTO clients (name, phone, id_number) VALUES (?,?,?)",
                        (pending["name"], pending["phone"], pending["id_number"]))
                    conn.commit()
                    st.session_state.pop("pending_client", None)
                    st.session_state.pop("dup_matches", None)
                    st.session_state["show_add_form"] = False
                    st.success("נפתח תיק לקוח נפרד.")
                    st.rerun()
                except sqlite3.IntegrityError:
                    st.error("מספר הטלפון כבר קיים במערכת.")
                finally:
                    conn.close()
        st.markdown('</div>', unsafe_allow_html=True)

    # --- חיפוש ---
    search_term = st.text_input("🔍 חיפוש לפי שם, טלפון או תעודת זהות", key="client_search")

    # --- טבלת לקוחות ---
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.subheader("📋 רשימת לקוחות")

    df = get_clients(search_term)

    if df.empty:
        st.info("לא נמצאו לקוחות.")
    else:
        rows_html = '''
        <div class="client-table-header">
            <div class="cell cell-id" style="flex:0 0 60px">מזהה</div>
            <div class="cell" style="flex:1.8">שם לקוח</div>
            <div class="cell" style="flex:1.3">טלפון</div>
            <div class="cell" style="flex:1">סטטוס</div>
            <div class="cell" style="flex:1.2">תיעדוף</div>
            <div class="cell" style="flex:1.2">סיווג</div>
        </div>
        '''
        for _, row in df.iterrows():
            badge_class = STATUS_BADGE_CLASS.get(row['status'], "status-irrelevant")
            priority_html = (f'<span class="{PRIORITY_BADGE_CLASS.get(row["priority"], "")}">{row["priority"]}</span>'
                              if row['priority'] else '<span style="color:#c7c2b3">—</span>')
            category_html = (f'<span class="{CATEGORY_BADGE_CLASS.get(row["category"], "")}">{row["category"]}</span>'
                              if row['category'] else '<span style="color:#c7c2b3">—</span>')
            rows_html += f'''
            <a class="client-row" href="?client_id={int(row['id'])}" target="_self">
                <div class="cell cell-id" style="flex:0 0 60px">{int(row['id'])}</div>
                <div class="cell" style="flex:1.8">{row['name']}</div>
                <div class="cell cell-phone" style="flex:1.3">{row['phone']}</div>
                <div class="cell" style="flex:1"><span class="{badge_class}">{row['status']}</span></div>
                <div class="cell" style="flex:1.2">{priority_html}</div>
                <div class="cell" style="flex:1.2">{category_html}</div>
            </a>
            '''
        st.html(rows_html)

    st.markdown('</div>', unsafe_allow_html=True)
