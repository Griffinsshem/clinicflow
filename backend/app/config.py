"""
Environment-driven configuration.

Nothing here has a usable default for a secret. Development falls back
to placeholders so the app runs locally; production validates and
raises on startup if anything is missing or still a placeholder.
"""

import os
from datetime import timedelta

from dotenv import load_dotenv

load_dotenv()

_PLACEHOLDERS = {"", "change-me", "changeme", "secret", "dev"}


def _split_origins(raw: str) -> list[str]:
    """CORS_ORIGINS is a comma-separated string; empty entries dropped."""
    return [origin.strip() for origin in raw.split(",") if origin.strip()]


class BaseConfig:
    ENV_NAME = "base"
    DEBUG = False
    TESTING = False

    SECRET_KEY = os.getenv("SECRET_KEY", "dev-only-secret-key")

    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL", "")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        "pool_pre_ping": True,
        "pool_recycle": 280,
    }

    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "dev-only-jwt-secret")
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(
        minutes=int(os.getenv("JWT_ACCESS_TOKEN_EXPIRES_MINUTES", "60"))
    )
    JWT_ERROR_MESSAGE_KEY = "message"

    CORS_ORIGINS = _split_origins(os.getenv("CORS_ORIGINS", ""))

    BEHIND_PROXY = False

    @classmethod
    def validate(cls) -> None:
        """Overridden by ProductionConfig. No-op elsewhere."""
        return None


class DevelopmentConfig(BaseConfig):
    ENV_NAME = "development"
    DEBUG = True


class TestingConfig(BaseConfig):
    ENV_NAME = "testing"
    TESTING = True
    SQLALCHEMY_DATABASE_URI = os.getenv("TEST_DATABASE_URL", "")
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(minutes=15)
    CORS_ORIGINS = ["http://localhost:3000"]


class ProductionConfig(BaseConfig):
    ENV_NAME = "production"
    BEHIND_PROXY = True

    @classmethod
    def validate(cls) -> None:
        """
        Fail fast at boot rather than serving traffic with a known-bad
        configuration. A crashed deploy is visible; a deploy running on
        a placeholder JWT secret is not.
        """
        problems: list[str] = []

        if cls.SECRET_KEY in _PLACEHOLDERS or cls.SECRET_KEY.startswith("dev-only"):
            problems.append("SECRET_KEY is missing or still a placeholder")
        if cls.JWT_SECRET_KEY in _PLACEHOLDERS or cls.JWT_SECRET_KEY.startswith("dev-only"):
            problems.append("JWT_SECRET_KEY is missing or still a placeholder")
        if cls.SECRET_KEY == cls.JWT_SECRET_KEY:
            problems.append("SECRET_KEY and JWT_SECRET_KEY must differ")
        if not cls.SQLALCHEMY_DATABASE_URI:
            problems.append("DATABASE_URL is not set")
        if not cls.CORS_ORIGINS:
            problems.append("CORS_ORIGINS is not set")
        if "*" in cls.CORS_ORIGINS:
            problems.append("CORS_ORIGINS must not contain a wildcard")

        if problems:
            raise RuntimeError(
                "Refusing to start in production:\n  - " + "\n  - ".join(problems)
            )


_CONFIGS = {
    "development": DevelopmentConfig,
    "testing": TestingConfig,
    "production": ProductionConfig,
}


def get_config(name: str | None = None) -> type[BaseConfig]:
    return _CONFIGS.get(name or os.getenv("FLASK_ENV", "development"), DevelopmentConfig)
