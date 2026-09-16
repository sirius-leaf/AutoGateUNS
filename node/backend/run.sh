#!/bin/bash
echo "Starting AutoGate UNS - Pos Satpam..."
echo ""
echo "Backend: http://localhost:3000"
echo ""

# Cek virtual environment
if [ ! -d ".venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv .venv
    source .venv/bin/activate
    pip install -r requirements.txt
else
    source .venv/bin/activate
fi

# Jalankan aplikasi (Backend + WebView)
python main.py
