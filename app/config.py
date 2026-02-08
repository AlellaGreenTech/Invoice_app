"""Application configuration."""
import os
from datetime import timedelta


class Config:
    """Base configuration."""
    # Strip all env vars — Render's dashboard often adds trailing whitespace/newlines
    SECRET_KEY = (os.getenv('SECRET_KEY') or 'dev-secret-key-change-in-production').strip()
    SQLALCHEMY_DATABASE_URI = (os.getenv('DATABASE_URL') or 'postgresql://invoice_user:invoice_pass@localhost:5432/invoice_app').strip()
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Redis and Celery
    REDIS_URL = (os.getenv('REDIS_URL') or 'redis://redis:6379/0').strip()
    CELERY_BROKER_URL = REDIS_URL
    CELERY_RESULT_BACKEND = REDIS_URL
    # Celery 5.x uses lowercase config keys
    broker_url = REDIS_URL
    result_backend = REDIS_URL

    # Google OAuth
    GOOGLE_CLIENT_ID = (os.getenv('GOOGLE_CLIENT_ID') or '').strip()
    GOOGLE_CLIENT_SECRET = (os.getenv('GOOGLE_CLIENT_SECRET') or '').strip()
    GOOGLE_REDIRECT_URI = (os.getenv('GOOGLE_REDIRECT_URI') or 'http://localhost:5000/auth/callback').strip()
    GOOGLE_DISCOVERY_URL = "https://accounts.google.com/.well-known/openid-configuration"

    # Google Drive API
    GOOGLE_DRIVE_SCOPES = ['https://www.googleapis.com/auth/drive.readonly']

    # Anthropic Claude
    ANTHROPIC_API_KEY = (os.getenv('ANTHROPIC_API_KEY') or '').strip()

    # File Upload
    MAX_CONTENT_LENGTH = int(os.getenv('MAX_CONTENT_LENGTH', 104857600))  # 100MB
    UPLOAD_FOLDER = os.getenv('UPLOAD_FOLDER', '/tmp/invoices')
    ALLOWED_EXTENSIONS = {'pdf'}

    # Session
    PERMANENT_SESSION_LIFETIME = timedelta(days=7)

    # WTF Forms
    WTF_CSRF_ENABLED = True
    WTF_CSRF_TIME_LIMIT = None


class DevelopmentConfig(Config):
    """Development configuration."""
    DEBUG = True
    TESTING = False


class ProductionConfig(Config):
    """Production configuration."""
    DEBUG = False
    TESTING = False


class TestingConfig(Config):
    """Testing configuration."""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    WTF_CSRF_ENABLED = False


config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}
