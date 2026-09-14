"""
Application configuration.
Loads settings from environment variables (.env) with sane local defaults.
"""
import os
from datetime import timedelta
from dotenv import load_dotenv

BASE_DIR = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
load_dotenv(os.path.join(BASE_DIR, ".env"))


def _database_uri():
    """
    Prefer MySQL (DATABASE_URL). If USE_SQLITE=true is explicitly set,
    or MySQL isn't configured, fall back to local SQLite so the project
    can be evaluated instantly without a MySQL server.
    """
    use_sqlite = os.getenv("USE_SQLITE", "false").lower() == "true"
    if use_sqlite:
        return os.getenv("SQLITE_FALLBACK", "sqlite:///vpool_dev.db")
    return os.getenv(
        "DATABASE_URL",
        "mysql+pymysql://vpool_user:vpool_pass@localhost:3306/vpool_db",
    )


class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key-change-me")
    SQLALCHEMY_DATABASE_URI = _database_uri()
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {"pool_pre_ping": True, "pool_recycle": 280}

    # Sessions / auth
    PERMANENT_SESSION_LIFETIME = timedelta(days=7)
    REMEMBER_COOKIE_DURATION = timedelta(days=14)

    # Geocoding
    GEOCODING_PROVIDER = os.getenv("GEOCODING_PROVIDER", "nominatim")
    LOCATIONIQ_API_KEY = os.getenv("LOCATIONIQ_API_KEY", "")

    # Mail (optional - console fallback if unset)
    MAIL_SERVER = os.getenv("MAIL_SERVER")
    MAIL_PORT = int(os.getenv("MAIL_PORT", 587))
    MAIL_USE_TLS = os.getenv("MAIL_USE_TLS", "true").lower() == "true"
    MAIL_USERNAME = os.getenv("MAIL_USERNAME")
    MAIL_PASSWORD = os.getenv("MAIL_PASSWORD")

    JSON_SORT_KEYS = False


class DevelopmentConfig(Config):
    DEBUG = True


class ProductionConfig(Config):
    DEBUG = False


class TestingConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    WTF_CSRF_ENABLED = False


config_by_name = {
    "development": DevelopmentConfig,
    "production": ProductionConfig,
    "testing": TestingConfig,
}
