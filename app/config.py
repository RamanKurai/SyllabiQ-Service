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
    UPLOAD_MAX_SIZE_MB: int = 10
    OPENAI_API_KEY: Optional[str] = None
    # OpenAI model names (used when LLM_PROVIDER or EMBEDDING_PROVIDER is openai). Set in env for quick config.
    OPENAI_MODEL: str = "gpt-4o-mini"
    OPENAI_EMBEDDING_MODEL: str = "text-embedding-3-small"
    CHROMA_PERSIST_DIR: str = "./chroma_data"

    # LLM/embedding provider: "openai" or "ollama". Default openai for backward compatibility.
    LLM_PROVIDER: str = "openai"
    # If unset, follows LLM_PROVIDER. Changing embedding provider may require re-indexing ChromaDB.
    EMBEDDING_PROVIDER: Optional[str] = None
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "llama3.2"
    OLLAMA_EMBEDDING_MODEL: str = "nomic-embed-text"

    @property
    def embedding_provider(self) -> str:
        """Effective embedding provider; defaults to LLM_PROVIDER when EMBEDDING_PROVIDER is unset."""
        return self.EMBEDDING_PROVIDER or self.LLM_PROVIDER

    @property
    def embedding_model_name(self) -> str:
        """Name of the active embedding model (for API responses)."""
        return self.OLLAMA_EMBEDDING_MODEL if self.embedding_provider == "ollama" else self.OPENAI_EMBEDDING_MODEL

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()

