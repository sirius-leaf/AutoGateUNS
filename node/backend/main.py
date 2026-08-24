import threading
import uvicorn
import webview
import time
import os

from app.main import app
from app.config import settings

def start_server():
    # Menjalankan FastAPI dengan Uvicorn
    uvicorn.run(app, host="0.0.0.0", port=3000)

def main():
    # 1. Jalankan backend (FastAPI) di thread terpisah agar tidak memblokir GUI
    server_thread = threading.Thread(target=start_server, daemon=True)
    server_thread.start()

    # 2. Tunggu sebentar agar server backend punya waktu untuk mulai
    time.sleep(2)
    
    # Tentukan URL frontend
    # Karena frontend sudah di-build dan di-serve oleh FastAPI, kita gunakan URL backend
    frontend_url = os.getenv("FRONTEND_URL", "http://localhost:3000")

    # 4. Buat dan jalankan window pywebview
    webview.create_window(
        "AutoGate UNS - Pos Satpam", 
        frontend_url,
        width=1024,
        height=768
    )
    webview.start()

if __name__ == "__main__":
    main()