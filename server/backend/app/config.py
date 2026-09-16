"""
Konfigurasi aplikasi Server.
"""
import os
from pathlib import Path
from dotenv import load_dotenv
from urllib.parse import quote_plus

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")


class Settings:
    # Database PostgreSQL
    POSTGRES_HOST: str = os.getenv("POSTGRES_HOST", "localhost")
    POSTGRES_PORT: int = int(os.getenv("POSTGRES_PORT", "5432"))
    POSTGRES_USER: str = os.environ["POSTGRES_USER"]
    POSTGRES_PASSWORD: str = os.environ["POSTGRES_PASSWORD"]
    POSTGRES_DB: str = os.environ["POSTGRES_DB"]
    DATABASE_URL: str = (
        "postgresql+psycopg2://"
        f"{quote_plus(POSTGRES_USER)}:{quote_plus(POSTGRES_PASSWORD)}@"
        f"{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"
    )

    # Auth — JWT
    SECRET_KEY: str = os.getenv("SECRET_KEY", "change-me-in-production")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "480"))

    # Auth — API key untuk node → server (legacy, sekarang per-node)
    API_KEY: str = os.getenv("API_KEY", "")

    # Default super admin (seed saat startup pertama)
    DEFAULT_ADMIN_USERNAME: str = os.getenv("DEFAULT_ADMIN_USERNAME", "superadmin")
    DEFAULT_ADMIN_PASSWORD: str = os.getenv("DEFAULT_ADMIN_PASSWORD", "admin123")

    # Storage (untuk gambar yang dikirim dari node)
    STORAGE_DIR: str = os.getenv("STORAGE_DIR", "./storage/captures")
    STORAGE_PUBLIC_PATH: str = os.getenv("STORAGE_PUBLIC_PATH", "/storage/captures")

    # App
    APP_HOST: str = os.getenv("APP_HOST", "0.0.0.0")
    APP_PORT: int = int(os.getenv("APP_PORT", "8000"))

    # Node Monitoring
    NODE_OFFLINE_THRESHOLD_SECONDS: int = int(os.getenv("NODE_OFFLINE_THRESHOLD_SECONDS", "60"))


settings = Settings()

Path(settings.STORAGE_DIR).mkdir(parents=True, exist_ok=True)
