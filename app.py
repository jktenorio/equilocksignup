from flask import Flask, render_template, request, redirect, url_for, send_file, abort
import sqlite3
import os
import re
import csv

app = Flask(__name__)

# ---------- DATABASE SETUP ----------
def get_db_connection():
    db_path = os.path.join(os.path.dirname(__file__), 'users.db')
    conn = sqlite3.connect(db_path, timeout=10, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''CREATE TABLE IF NOT EXISTS users (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            fullname TEXT NOT NULL,
                            email TEXT NOT NULL,
                            idnumber TEXT UNIQUE NOT NULL,
                            role TEXT NOT NULL
                        )''')
        conn.commit()

# ---------- CSV BACKUP FUNCTION ----------
def backup_csv():
    db_path = os.path.join(os.path.dirname(__file__), 'users.db')
    csv_path = os.path.join(os.path.dirname(__file__), 'users_backup.csv')
    
    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id, fullname, email, idnumber, role FROM users")
        rows = cursor.fetchall()
    
    with open(csv_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(["id","fullname","email","idnumber","role"])
        for r in rows:
            writer.writerow(r)

# ---------- ROUTES ----------
@app.route('/')
def index():
    return render_template('signup.html')

@app.route('/submit', methods=['POST'])
def submit():
    fullname = request.form.get('fullname', '').strip()
    email = request.form.get('email', '').strip()
    idnumber = request.form.get('idnumber', '').strip().replace(' ', '').replace('–', '-')
    role = request.form.get('role', '').strip()
    agree = request.form.get('agree')

    # ✅ Validate required fields
    if not all([fullname, email, idnumber, role, agree]):
        return "<h2>⚠️ Please fill out all fields and agree to the terms.</h2>"

    # ✅ Validate ID number format ####-####
    if not re.match(r'^\d{4}-\d{4}$', idnumber):
        return "<h2>⚠️ Invalid ID number format. Use ####-#### (e.g., 0222-0282).</h2>"

    # ✅ Validate role
    if role not in ["Student", "Faculty"]:
        return "<h2>⚠️ Invalid role. Please select Student or Faculty.</h2>"

    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO users (fullname, email, idnumber, role) VALUES (?, ?, ?, ?)",
                (fullname, email, idnumber, role)
            )
            conn.commit()

        # ✅ Generate CSV backup on every successful signup
        backup_csv()

        # ✅ Redirect to thank you page after successful registration
        return redirect(url_for('thank_you'))

    except sqlite3.IntegrityError:
        return "<h2>⚠️ This ID number is already registered. Please use another one.</h2>"

    except sqlite3.OperationalError as e:
        return f"<h2>⚠️ Database error: {e}</h2>"

# ---------- THANK YOU PAGE ----------
@app.route('/thankyou')
def thank_you():
    return render_template('thankyou.html')

# ---------- SECURE CSV DOWNLOAD ROUTE ----------
@app.route('/download_csv')
def download_csv():
    token = request.args.get("token")
    if token != os.environ.get("ADMIN_TOKEN"):  # Set this in Render environment variables
        abort(403)
    
    csv_path = os.path.join(os.path.dirname(__file__), 'users_backup.csv')
    if not os.path.exists(csv_path):
        abort(404)
    return send_file(csv_path, as_attachment=True)

# ---------- RUN APP ----------
if __name__ == '__main__':
    init_db()
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
