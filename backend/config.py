import os

BASE_DIR = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))


class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-change-me-0123456789abcdef")
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "jwt-secret-change-me-0123456789abcdef")
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

    # Predefined admin (created programmatically on first run)
    ADMIN_EMAIL = os.getenv("ADMIN_EMAIL", "admin@portal.com")
    ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "Admin@123")

    # Notifications (optional - jobs degrade gracefully if unset)
    GCHAT_WEBHOOK_URL = os.getenv("GCHAT_WEBHOOK_URL", "")
    CACHE_DEFAULT_TIMEOUT = 60