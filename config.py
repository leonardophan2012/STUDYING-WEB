import os

class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "change-this-secret-key-before-deploy")

    DB_HOST = os.environ.get("DB_HOST", "localhost")
    DB_PORT = int(os.environ.get("DB_PORT", "3306"))
    DB_USER = os.environ.get("DB_USER", "root")
    DB_PASSWORD = os.environ.get("DB_PASSWORD", "")
    DB_NAME = os.environ.get("DB_NAME", "school_subjects")

    SMTP_HOST = os.environ.get("SMTP_HOST", "smtp.gmail.com")
    SMTP_PORT = int(os.environ.get("SMTP_PORT", "587"))
    SMTP_USER = os.environ.get("SMTP_USER", "")
    SMTP_PASSWORD = os.environ.get("SMTP_PASSWORD", "")
    MAIL_FROM = os.environ.get("MAIL_FROM", SMTP_USER or "noreply@example.com")

    TOKEN_MAX_AGE_SECONDS = 60 * 60 * 24

    OPENTDB_BASE_URL = "https://opentdb.com"
