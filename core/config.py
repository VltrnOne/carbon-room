"""
Carbon Room Configuration
=========================
Environment-based configuration with validation.
Supports SQLite (local/dev) and PostgreSQL (production on Render).
"""

import os
from typing import Optional, Literal
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path

# Base directory for the project
BASE_DIR = Path(__file__).resolve().parent.parent


@dataclass
class Settings:
    """
    Application settings loaded from environment variables.

    Usage:
        from core.config import settings
        db_url = settings.DATABASE_URL
    """

    # Environment
    ENV: Literal["development", "staging", "production"] = field(
        default_factory=lambda: os.getenv("ENV", "development")
    )
    DEBUG: bool = field(
        default_factory=lambda: os.getenv("DEBUG", "true").lower() == "true"
    )

    # Database Configuration
    # SQLite for local dev, PostgreSQL for production (Render provides free Postgres)
    DATABASE_URL: str = field(
        default_factory=lambda: os.getenv(
            "DATABASE_URL",
            f"sqlite:///{BASE_DIR}/carbon_room.db"
        )
    )

    # Database Pool Settings (for PostgreSQL)
    DB_POOL_SIZE: int = field(
        default_factory=lambda: int(os.getenv("DB_POOL_SIZE", "5"))
    )
    DB_MAX_OVERFLOW: int = field(
        default_factory=lambda: int(os.getenv("DB_MAX_OVERFLOW", "10"))
    )
    DB_POOL_TIMEOUT: int = field(
        default_factory=lambda: int(os.getenv("DB_POOL_TIMEOUT", "30"))
    )

    # API Settings
    API_HOST: str = field(
        default_factory=lambda: os.getenv("API_HOST", "0.0.0.0")
    )
    API_PORT: int = field(
        default_factory=lambda: int(os.getenv("API_PORT", "8003"))
    )
    API_KEY: Optional[str] = field(
        default_factory=lambda: os.getenv("API_KEY")
    )
    SECRET_KEY: str = field(
        default_factory=lambda: os.getenv(
            "SECRET_KEY",
            "carbon-room-dev-secret-change-in-production"
        )
    )

    # GitHub Integration
    GITHUB_TOKEN: Optional[str] = field(
        default_factory=lambda: os.getenv("GITHUB_TOKEN")
    )
    GITHUB_REPO: str = field(
        default_factory=lambda: os.getenv("GITHUB_REPO", "")
    )
    GITHUB_BRANCH: str = field(
        default_factory=lambda: os.getenv("GITHUB_BRANCH", "main")
    )
    GITHUB_BACKUP_PATH: str = field(
        default_factory=lambda: os.getenv("GITHUB_BACKUP_PATH", "backups")
    )

    # Render Integration
    RENDER_API_KEY: Optional[str] = field(
        default_factory=lambda: os.getenv("RENDER_API_KEY")
    )
    RENDER_SERVICE_ID: Optional[str] = field(
        default_factory=lambda: os.getenv("RENDER_SERVICE_ID")
    )
    RENDER_DEPLOY_HOOK: Optional[str] = field(
        default_factory=lambda: os.getenv("RENDER_DEPLOY_HOOK")
    )

    # SiteGround Integration (existing hosting)
    SITEGROUND_HOST: Optional[str] = field(
        default_factory=lambda: os.getenv("SITEGROUND_HOST")
    )
    SITEGROUND_USER: Optional[str] = field(
        default_factory=lambda: os.getenv("SITEGROUND_USER")
    )
    SITEGROUND_KEY_PATH: Optional[str] = field(
        default_factory=lambda: os.getenv("SITEGROUND_KEY_PATH")
    )

    # Lightning Network (for payments/fast data)
    LIGHTNING_NODE_URL: Optional[str] = field(
        default_factory=lambda: os.getenv("LIGHTNING_NODE_URL")
    )
    LIGHTNING_MACAROON: Optional[str] = field(
        default_factory=lambda: os.getenv("LIGHTNING_MACAROON")
    )
    LIGHTNING_TLS_CERT: Optional[str] = field(
        default_factory=lambda: os.getenv("LIGHTNING_TLS_CERT")
    )

    # Blockchain/Hash Settings
    HASH_ALGORITHM: str = field(
        default_factory=lambda: os.getenv("HASH_ALGORITHM", "sha256")
    )
    WATERMARK_PREFIX: str = field(
        default_factory=lambda: os.getenv("WATERMARK_PREFIX", "C6")
    )

    # File Storage
    UPLOAD_DIR: Path = field(
        default_factory=lambda: Path(
            os.getenv("UPLOAD_DIR", str(BASE_DIR / "uploads"))
        )
    )
    CERTIFICATE_DIR: Path = field(
        default_factory=lambda: Path(
            os.getenv("CERTIFICATE_DIR", str(BASE_DIR / "certificates"))
        )
    )
    MAX_UPLOAD_SIZE_MB: int = field(
        default_factory=lambda: int(os.getenv("MAX_UPLOAD_SIZE_MB", "50"))
    )

    # Logging
    LOG_LEVEL: str = field(
        default_factory=lambda: os.getenv("LOG_LEVEL", "INFO")
    )
    LOG_FORMAT: str = field(
        default_factory=lambda: os.getenv(
            "LOG_FORMAT",
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
    )

    # CORS Settings
    CORS_ORIGINS: list = field(
        default_factory=lambda: os.getenv(
            "CORS_ORIGINS",
            "http://localhost:3000,http://localhost:8003"
        ).split(",")
    )

    def __post_init__(self):
        """Validate and create necessary directories."""
        # Ensure upload and certificate directories exist
        self.UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
        self.CERTIFICATE_DIR.mkdir(parents=True, exist_ok=True)

        # Fix Render's PostgreSQL URL (uses postgres:// but SQLAlchemy needs postgresql://)
        if self.DATABASE_URL.startswith("postgres://"):
            self.DATABASE_URL = self.DATABASE_URL.replace(
                "postgres://", "postgresql://", 1
            )

    @property
    def is_production(self) -> bool:
        """Check if running in production."""
        return self.ENV == "production"

    @property
    def is_sqlite(self) -> bool:
        """Check if using SQLite database."""
        return self.DATABASE_URL.startswith("sqlite")

    @property
    def is_postgres(self) -> bool:
        """Check if using PostgreSQL database."""
        return "postgresql" in self.DATABASE_URL

    def get_db_engine_args(self) -> dict:
        """Get SQLAlchemy engine arguments based on database type."""
        if self.is_sqlite:
            return {
                "connect_args": {"check_same_thread": False},
                "echo": self.DEBUG,
            }
        else:
            # PostgreSQL connection pool settings
            return {
                "pool_size": self.DB_POOL_SIZE,
                "max_overflow": self.DB_MAX_OVERFLOW,
                "pool_timeout": self.DB_POOL_TIMEOUT,
                "pool_pre_ping": True,  # Verify connections before use
                "echo": self.DEBUG,
            }


@lru_cache()
def get_settings() -> Settings:
    """
    Get cached settings instance.

    Returns:
        Settings: Application settings singleton
    """
    return Settings()


# Global settings instance
settings = get_settings()


def reload_settings() -> Settings:
    """
    Reload settings (useful for testing).

    Returns:
        Settings: Fresh settings instance
    """
    get_settings.cache_clear()
    return get_settings()
