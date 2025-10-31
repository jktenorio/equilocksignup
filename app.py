from flask import Flask, render_template, request, redirect, url_for, send_file, abort
import sqlite3
import os
import re
import csv

app = Flask(__name__)

# ---------- DATABASE SETUP ----------
DB_PATH = os.path.join(os.path.dirname(__file__), 'users.db')

def get_db_connection():
    conn = sqlite3.connect(DB_PATH, timeout=10, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                fullname TEXT NOT NULL,
                email TEXT NOT NULL,
                idnumber TEXT UNIQUE NOT NULL,
                role TEXT NOT NULL
            )
        ''')
        conn.commit()

# ---------- CSV BACKUP ----------
CSV_PATH = os.path.join(os.path.dirname(__file__), 'users_backup.csv')

def append_to_csv(fullname, email, idnumber, role):
    """Append new user to CSV, create file with header if it doesn't exist"""
    file_exists = os.path.exists(CSV_PATH)
    with open(CSV_PATH, 'a', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(["fullname", "email", "idnumber", "role"])
        writer.writerow([fullname, email, idnumber, role])

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

    # Validate required fields
    if not all([fullname, email, idnumber, role, agree]):
        return "<h2>⚠️ Please fill out all fields and agree to the terms.</h2>"

    # Basic email format validation
    if not re.match(r'^[^@]+@[^@]+\.[^@]+$', email):
        return "<h2>⚠️ Invalid email format. Please enter a valid email.</h2>"

    # Validate ID number format ####-####
    if not re.match(r'^\d{4}-\d{4}$', idnumber):
        return "<h2>⚠️ Invalid ID number format. Use ####-#### (e.g., 0222-0282).</h2>"

    # Validate role
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

        # Append new user to CSV permanently
        append_to_csv(fullname, email, idnumber, role)

        return redirect(url_for('thank_you'))

    except sqlite3.IntegrityError:
        return "<h2>⚠️ This ID number is already registered. Please use another one.</h2>"

    except sqlite3.OperationalError as e:
        return f"<h2>⚠️ Database error: {e}</h2>"

# Thank you page
@app.route('/thankyou')
def thank_you():
    return render_template('thankyou.html')

# Secure CSV download
@app.route('/download_csv')
def download_csv():
    token = request.args.get("token")
    if token != os.environ.get("ADMIN_TOKEN"):  # Set in environment variables
        abort(403)

    if not os.path.exists(CSV_PATH):
        abort(404)

    return send_file(CSV_PATH, as_attachment=True)

# ---------- RUN APP ----------
if __name__ == '__main__':
    init_db()
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
