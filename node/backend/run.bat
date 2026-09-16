@echo off
echo Starting AutoGate UNS - Pos Satpam...
echo.
echo Backend: http://localhost:3000
echo.

REM Cek virtual environment
if not exist ".venv" (
    echo Creating virtual environment...
    python -m venv .venv
)

REM Pasang dependency pada interpreter yang benar
.venv\Scripts\python.exe -m pip install -r requirements.txt

REM Jalankan aplikasi (Backend + WebView)
.venv\Scripts\python.exe main.py
