import requests
import os

# ---------------- CONFIGURATION ----------------
# URL of your deployed Flask app's CSV endpoint
RENDER_URL = "https://equilock-sign-up-form.onrender.com/download_csv"  # replace with your Render URL

# Admin token set in Render environment variables
TOKEN = "equishanedavekevin"  # must match ADMIN_TOKEN on Render

# Path to save CSV locally
LOCAL_CSV ="/home/equilock/Documents/FrontEnd/users_backup.csv"

# ---------------- DOWNLOAD FUNCTION ----------------
def download_csv():
    try:
        # Request the CSV with token
        response = requests.get(f"{RENDER_URL}?token={TOKEN}", timeout=10)
        response.raise_for_status()  # Raise error for HTTP issues

        # Save CSV to local path
        with open(LOCAL_CSV, "wb") as f:
            f.write(response.content)

        print(f"[✓] Backup downloaded successfully: {LOCAL_CSV}")

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
