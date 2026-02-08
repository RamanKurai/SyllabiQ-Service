try:
    # pydantic v2+ split BaseSettings into pydantic-settings package
    from pydantic_settings import BaseSettings
except Exception:
    try:
        # Fallback for older pydantic versions
        from pydantic import BaseSettings
    except Exception as e:
        raise ImportError(
            "BaseSettings not available. Install 'pydantic-settings' for pydantic v2 "
            "(`pip install pydantic-settings`) or pin pydantic<2.12."
        ) from e
from typing import List, Optional


class Settings(BaseSettings):
    """
    Centralized configuration loaded from environment or a `.env` file.
    Defaults are safe for local development but should be overridden in production.
    """
    DATABASE_URL: str = "sqlite+aiosqlite:///./dev.db"
    # Optional superuser/admin URL used to create the DB/user when AUTO_CREATE_DB is true.
    # Example: postgresql+asyncpg://postgres:postgres@localhost:5432/postgres
    DATABASE_SUPERUSER_URL: Optional[str] = None
    # When true and DATABASE_URL points to Postgres, the app will attempt to create the
    # database (and role if needed) at startup using DATABASE_SUPERUSER_URL.
    AUTO_CREATE_DB: bool = False
    JWT_SECRET: str = "devsecret"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_SECONDS: int = 60 * 60 * 24
    CORS_ALLOW_ORIGINS: List[str] = ["*"]

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()

