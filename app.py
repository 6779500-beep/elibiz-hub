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
.stApp { direction: rtl; text-align: right; background-color: #f0f4f8; }
[data-testid="stAppViewContainer"] { background-color: #f0f4f8; }

/* שורת התראות */
.alert-bar {
    background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%);
    color: white; padding: 12px 24px; border-radius: 12px;
    margin-bottom: 20px; display: flex; align-items: center;
    gap: 16px; flex-wrap: wrap; direction: rtl;
    box-shadow: 0 4px 15px rgba(15,52,96,0.3);
}
.alert-badge {
    background: #e74c3c; color: white; border-radius: 20px;
    padding: 4px 12px; font-weight: 700; font-size: 13px;
    animation: pulse 2s infinite;
}
.alert-badge-warn {
    background: #f39c12; color: white; border-radius: 20px;
    padding: 4px 12px; font-weight: 700; font-size: 13px;
}
@keyframes pulse { 0%,100%{opacity:1} 50%{opacity:0.7} }

/* כרטיסיות */
.card {
    background: white; padding: 24px; border-radius: 14px;
    box-shadow: 0 2px 12px rgba(0,0,0,0.06); margin-bottom: 20px;
    border: 1px solid #e8eef3;
}

/* כותרת ראשית */
.main-title {
    color: #1a1a2e; text-align: center; font-weight: 800;
    font-size: 28px; margin-bottom: 4px;
}
.main-subtitle {
    color: #6b7280; text-align: center; font-size: 14px;
    margin-bottom: 0;
}

/* כפתורים */
.stButton>button {
    background-color: #3498db; color: white; border-radius: 8px;
    font-weight: 600; border: none; padding: 10px 20px;
    transition: all 0.2s ease; width: 100%;
}
.stButton>button:hover { background-color: #2980b9; transform: translateY(-1px); }

/* תגיות סטטוס */
.status-new { background:#dbeafe; color:#1d4ed8; padding:3px 10px; border-radius:20px; font-size:12px; font-weight:600; }
.status-inprogress { background:#fef9c3; color:#854d0e; padding:3px 10px; border-radius:20px; font-size:12px; font-weight:600; }
.status-closed { background:#dcfce7; color:#166534; padding:3px 10px; border-radius:20px; font-size:12px; font-weight:600; }
.status-irrelevant { background:#f3f4f6; color:#6b7280; padding:3px 10px; border-radius:20px; font-size:12px; font-weight:600; }

/* תיק לקוח */
.client-header {
    background: linear-gradient(135deg, #3498db, #2980b9);
    color: white; padding: 16px 20px; border-radius: 10px;
    margin-bottom: 16px;
}
.client-header h3 { margin:0; font-size:18px; font-weight:700; }
.client-header p { margin:4px 0 0 0; opacity:0.85; font-size:13px; }

/* הערות */
.note-item {
    background: #f8fafc; border-right: 3px solid #3498db;
    padding: 10px 14px; border-radius: 0 8px 8px 0;
    margin-bottom: 8px;
}
.note-item .note-text { color: #1e293b; font-size:14px; margin-bottom:4px; }
.note-item .note-date { color: #94a3b8; font-size:11px; }

/* משימות */
.task-item {
    background: #f8fafc; border: 1px solid #e2e8f0;
    padding: 10px 14px; border-radius: 8px; margin-bottom: 8px;
    display: flex; align-items: center; gap: 10px;
}
.task-done { text-decoration: line-through; color: #94a3b8; }

/* קבצים */
.file-item {
    background: #f8fafc; border: 1px solid #e2e8f0;
    padding: 10px 14px; border-radius: 8px; margin-bottom: 8px;
    display: flex; align-items: center; gap: 10px;
}

[data-testid="stDataFrame"] { direction: rtl; }
.stTabs [data-baseweb="tab"] { font-weight: 600; font-size: 14px; }

/* לוח משימות דחופות גלובלי */
.urgent-box {
    background: #fff7ed; border-right: 4px solid #f59e0b;
    padding: 10px 14px; border-radius: 0 8px 8px 0; margin-bottom: 8px;
}
.urgent-box .urgent-desc { color: #1e293b; font-weight: 600; font-size: 14px; }
.urgent-box .urgent-meta { color: #92400e; font-size: 12px; margin-top: 2px; }
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
            if phone:
                try:
                    conn.execute("INSERT INTO clients (name, phone) VALUES (?, ?)",
                                 ("לקוח חדש", phone.group(1)))
                    count += 1
                except sqlite3.IntegrityError:
                    pass
            mail.store(num, "+FLAGS", "\\Seen")

        conn.execute(
            "DELETE FROM clients WHERE phone IS NULL OR phone='' OR phone LIKE '%-%' OR phone='לא נמצא'")
        conn.commit()
        conn.close()
        return True, count
    except Exception as e:
        return False, str(e)

# --- שאילתות עזר ---
def get_clients():
    conn = sqlite3.connect('crm.db')
    df = pd.read_sql_query(
        "SELECT id, name, phone, status, created_at FROM clients ORDER BY id DESC", conn)
    conn.close()
    return df

def get_alerts():
    conn = sqlite3.connect('crm.db')
    today = date.today().isoformat()
    new_count = conn.execute("SELECT COUNT(*) FROM clients WHERE status='חדש'").fetchone()[0]
    urgent_tasks = conn.execute(
        "SELECT COUNT(*) FROM tasks WHERE is_done=0 AND due_date<=? AND due_date!=''", (today,)
    ).fetchone()[0]
    conn.close()
    return new_count, urgent_tasks

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

# --- שורת התראות ---
new_leads, urgent_tasks = get_alerts()
alerts_html = '<div class="alert-bar">🔔 <strong>התראות:</strong>'
if new_leads > 0:
    alerts_html += f'&nbsp;<span class="alert-badge">📥 {new_leads} פניות חדשות לטיפול</span>'
else:
    alerts_html += '&nbsp;<span style="font-size:13px;opacity:0.7">אין פניות חדשות</span>'
if urgent_tasks > 0:
    alerts_html += f'&nbsp;<span class="alert-badge-warn">⚡ {urgent_tasks} משימות דחופות להיום</span>'
else:
    alerts_html += '&nbsp;<span style="font-size:13px;opacity:0.7"> | אין משימות דחופות</span>'
alerts_html += '</div>'
st.markdown(alerts_html, unsafe_allow_html=True)

# --- לוח משימות דחופות גלובלי ---
urgent_list = get_urgent_tasks()
if urgent_list:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.subheader("⏰ משימות דחופות מכל הלקוחות")
    today_str = date.today().isoformat()
    for t_id, t_desc, t_due, c_name, c_id in urgent_list:
        label = "באיחור" if t_due < today_str else "להיום"
        st.markdown(f'''
        <div class="urgent-box">
            <div class="urgent-desc">{t_desc}</div>
            <div class="urgent-meta">👤 {c_name} &nbsp;|&nbsp; 🗓 {t_due} ({label})</div>
        </div>
        ''', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

# --- כפתור סנכרון ---
col_sync, col_empty = st.columns([1, 5])
with col_sync:
    if st.button("🔄 סנכרן מייל"):
        with st.spinner("מסנכרן..."):
            ok, result = sync_data()
        if ok:
            st.success(f"סנכרון הושלם! נוספו {result} לקוחות חדשים.")
            st.rerun()
        else:
            st.error(f"שגיאה: {result}")

# --- טבלת לקוחות ---
st.markdown('<div class="card">', unsafe_allow_html=True)
st.subheader("📋 רשימת לקוחות")

df = get_clients()

if df.empty:
    st.info("אין לקוחות במערכת. לחץ על 'סנכרן מייל' להוספת לקוחות.")
else:
    display_df = df.rename(columns={
        'id': 'מזהה', 'name': 'שם לקוח',
        'phone': 'טלפון', 'status': 'סטטוס', 'created_at': 'תאריך קליטה'
    })

    selection = st.dataframe(
        display_df,
        use_container_width=True,
        hide_index=True,
        selection_mode="single-row",
        on_select="rerun",
        column_config={
            "מזהה": st.column_config.NumberColumn(width="small"),
            "סטטוס": st.column_config.TextColumn(width="medium"),
            "תאריך קליטה": st.column_config.TextColumn(width="medium"),
        }
    )

st.markdown('</div>', unsafe_allow_html=True)

# --- תיק לקוח ---
selected_rows = []
if not df.empty and isinstance(selection, dict):
    selected_rows = selection.get("selection", {}).get("rows", [])
elif not df.empty and hasattr(selection, "selection"):
    sel_obj = selection.selection
    selected_rows = sel_obj.get("rows", []) if isinstance(sel_obj, dict) else (
        sel_obj.rows if hasattr(sel_obj, "rows") else [])

if selected_rows:
    selected_idx = selected_rows[0]
    client_id = int(df.iloc[selected_idx]['id'])
    client = get_client(client_id)

    if client:
        c_id, c_name, c_phone, c_status, c_created = client

        # כותרת תיק
        st.markdown(f'''
        <div class="client-header">
          <h3>📂 תיק לקוח: {c_name}</h3>
          <p>📞 {c_phone} &nbsp;|&nbsp; 🗓 נקלט: {c_created[:10] if c_created else "-"}</p>
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

            status_options = ["חדש", "בטיפול", "נסגר", "לא רלוונטי"]
            status_idx = status_options.index(c_status) if c_status in status_options else 0
            new_status = st.selectbox("סטטוס פנייה", options=status_options,
                                       index=status_idx, key=f"status_{client_id}")

            if st.button("💾 שמור פרטים", key=f"save_details_{client_id}"):
                conn = sqlite3.connect('crm.db')
                try:
                    conn.execute(
                        "UPDATE clients SET name=?, phone=?, status=? WHERE id=?",
                        (new_name, new_phone, new_status, client_id))
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
