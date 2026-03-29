"""Centralized configuration using Pydantic Settings.

All environment variables are prefixed with DECKFORGE_ and loaded from .env.
"""

from __future__ import annotations

from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables.

    Environment variables are prefixed with DECKFORGE_ (case-insensitive).
    Example: DECKFORGE_DATABASE_URL overrides DATABASE_URL.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="DECKFORGE_",
        case_sensitive=False,
    )

    # Database
    DATABASE_URL: str = (
        "postgresql+psycopg://deckforge:deckforge@localhost:5432/deckforge"
    )

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"

    # S3-compatible storage (MinIO for local dev, Cloudflare R2 for production)
    S3_ENDPOINT_URL: str = "http://localhost:9000"
    S3_ACCESS_KEY: str = "minioadmin"
    S3_SECRET_KEY: str = "minioadmin"
    S3_BUCKET: str = "deckforge"

    # API server
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000

    # Environment
    DEBUG: bool = True
    ENVIRONMENT: Literal["development", "staging", "production"] = "development"

    # LLM provider settings
    LLM_DEFAULT_PROVIDER: str = "claude"
    LLM_FALLBACK_CHAIN: str = "claude,openai,gemini"
    ANTHROPIC_API_KEY: str | None = None
    OPENAI_API_KEY: str | None = None
    GEMINI_API_KEY: str | None = None
    OLLAMA_BASE_URL: str = "http://localhost:11434"

    @property
    def llm_fallback_list(self) -> list[str]:
        """Parse the comma-separated fallback chain into a list."""
        return [p.strip() for p in self.LLM_FALLBACK_CHAIN.split(",") if p.strip()]


settings = Settings()
