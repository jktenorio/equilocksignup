import requests
import os
import sqlite3
import csv

# ---------------- CONFIGURATION ----------------
RENDER_URL = "https://equilock-sign-up-form.onrender.com/download_csv"
TOKEN = "equishanedavekevin"  # must match ADMIN_TOKEN on Render

LOCAL_CSV = "/home/equilock/Documents/backend/users_backup.csv"
LOCAL_DB = "/home/equilock/Documents/backend/users.db"  # <-- make sure path is correct


# ---------------- SYNC CSV INTO SQLITE ----------------
def sync_csv_to_sqlite(csv_path, db_path):
    if not os.path.exists(csv_path):
        print("[✗] CSV file not found, skipping sync.")
        return

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Ensure table exists
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                fullname TEXT NOT NULL,
                email TEXT NOT NULL,
                idnumber TEXT UNIQUE NOT NULL,
                role TEXT NOT NULL
            )
        ''')

        with open(csv_path, newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                cursor.execute("""
                    INSERT OR IGNORE INTO users (fullname, email, idnumber, role)
                    VALUES (?, ?, ?, ?)
                """, (row["fullname"], row["email"], row["idnumber"], row["role"]))

        conn.commit()
        conn.close()
        print("[✓] Synced CSV → SQLite permanently")

    except Exception as e:
        print(f"[✗] Error syncing CSV to SQLite: {e}")


# ---------------- DOWNLOAD FUNCTION ----------------
def download_csv():
    try:
        print("[…] Downloading backup from Render…")

        # Request the CSV with token
        response = requests.get(f"{RENDER_URL}?token={TOKEN}", timeout=10)
        response.raise_for_status()

        # Save CSV to local path
        with open(LOCAL_CSV, "wb") as f:
            f.write(response.content)

        print(f"[✓] CSV downloaded successfully: {LOCAL_CSV}")

        # Sync downloaded CSV to local database
        sync_csv_to_sqlite(LOCAL_CSV, LOCAL_DB)

    except requests.exceptions.HTTPError as http_err:
        print(f"[✗] HTTP error: {http_err}")

    except requests.exceptions.ConnectionError as conn_err:
        print(f"[✗] Connection error: {conn_err}")

    except requests.exceptions.Timeout:
        print("[✗] Timeout error: server took too long to respond")

    except Exception as e:
        print(f"[✗] Unexpected error: {e}")


# ---------------- RUN ----------------
if __name__ == "__main__":
    download_csv()
