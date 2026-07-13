import os
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))

class Config:
    SECRET_KEY = os.getenv("SECRET_KEY","2ccd4fbf01b6818ffd7ae35664d8d6a2377bdbf51074f08faf595e57cb091f5")
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY","e52947827594a53db8e809c49b8fb2b709c639c0cd15442c0046616e5860f16")
    JWT_ACCESS_TOKEN_EXPIRES = 60 * 60 * 8  # 8 hours (seconds)

    SQLALCHEMY_DATABASE_URI = os.getenv(
        "SQLALCHEMY_DATABASE_URI",
        "sqlite:///" + os.path.join(BASE_DIR, "instance", "placement.db"),
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Redis / Celery
    REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    CELERY_BROKER_URL = os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/1")
    CELERY_RESULT_BACKEND = os.getenv("CELERY_RESULT_BACKEND", "redis://localhost:6379/2")
    CACHE_REDIS_URL = os.getenv("CACHE_REDIS_URL", "redis://localhost:6379/3")

    # Uploads
    UPLOAD_FOLDER = os.path.join(BASE_DIR, "static", "uploads", "resumes")
    OFFER_FOLDER = os.path.join(BASE_DIR, "static", "uploads", "offers")
    EXPORT_FOLDER = os.path.join(BASE_DIR, "static", "uploads", "exports")
    MAX_CONTENT_LENGTH = 5 * 1024 * 1024

    # Predefined admin
    ADMIN_EMAIL = os.getenv("ADMIN_EMAIL", "admin@portal.com")
    ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "Admin@123")

    # Notifications
    GCHAT_WEBHOOK_URL = os.getenv("GCHAT_WEBHOOK_URL", "")
    CACHE_DEFAULT_TIMEOUT = 60

    #SMTP + MailHog
    SMTP_HOST = os.getenv("SMTP_HOST", "localhost")
    SMTP_PORT = int(os.getenv("SMTP_PORT", "1025"))
    SMTP_USE_TLS = os.getenv("SMTP_USE_TLS", "false").lower() == "true"
    SMTP_USERNAME = os.getenv("SMTP_USERNAME", "")
    SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")
    SMTP_FROM = os.getenv("SMTP_FROM", "placements@portal.local")