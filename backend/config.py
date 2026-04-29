import os

# VULN: Hardcoded credentials - should use environment variables exclusively
# VULN: Debug mode enabled in production
# VULN: Secret key is weak and hardcoded

class Config:
    # VULN: Hardcoded secret key (weak, predictable)
    SECRET_KEY = "super-secret-key-12345"

    # VULN: Debug mode enabled - exposes stack traces and interactive debugger
    DEBUG = True

    # VULN: Hardcoded database credentials as fallback
    DB_HOST = os.environ.get("DB_HOST", "localhost")
    DB_PORT = os.environ.get("DB_PORT", "5432")
    DB_NAME = os.environ.get("DB_NAME", "inventory_db")
    DB_USER = os.environ.get("DB_USER", "inventory_admin")
    DB_PASSWORD = os.environ.get("DB_PASSWORD", "postgres_root_password_123")

    # VULN: Admin token hardcoded in source
    ADMIN_API_TOKEN = "admin-token-2024-xyz"

    # VULN: No session timeout configuration
    SESSION_COOKIE_SECURE = False
    SESSION_COOKIE_HTTPONLY = False

    # VULN: Permissive CORS
    CORS_ORIGINS = "*"

    # Export settings
    EXPORT_DIR = "/tmp/exports"

    # VULN: Verbose logging that may leak sensitive data
    LOG_LEVEL = "DEBUG"
