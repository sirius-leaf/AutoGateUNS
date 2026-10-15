#!/bin/sh
# Entrypoint production untuk container backend.
# 1. Tunggu PostgreSQL siap
# 2. Jalankan migrasi Alembic (best-effort; init_db di app juga create_all)
# 3. Start uvicorn
set -eu

echo "[entrypoint] Menunggu PostgreSQL ${POSTGRES_HOST:-postgres}:${POSTGRES_PORT:-5432}..."
python - <<'PY'
import os
import time

import psycopg2

host = os.getenv("POSTGRES_HOST", "postgres")
port = int(os.getenv("POSTGRES_PORT", "5432"))
user = os.environ["POSTGRES_USER"]
password = os.environ["POSTGRES_PASSWORD"]
dbname = os.environ["POSTGRES_DB"]

for attempt in range(60):
    try:
        conn = psycopg2.connect(
            host=host, port=port, user=user, password=password, dbname=dbname,
            connect_timeout=3,
        )
        conn.close()
        print("[entrypoint] PostgreSQL siap.")
        break
    except Exception as exc:  # noqa: BLE001
        if attempt == 59:
            raise SystemExit(f"[entrypoint] PostgreSQL tidak reachable: {exc}")
        time.sleep(2)
PY

if alembic upgrade head; then
    echo "[entrypoint] Migrasi Alembic selesai."
else
    echo "[entrypoint] WARNING: 'alembic upgrade head' gagal — lanjut, init_db akan create_all."
fi

echo "[entrypoint] Start uvicorn di 0.0.0.0:${APP_PORT:-8000} (workers=${UVICORN_WORKERS:-2})."
exec uvicorn app.main:app \
    --host 0.0.0.0 \
    --port "${APP_PORT:-8000}" \
    --workers "${UVICORN_WORKERS:-2}"
