"""
app/core/config.py
──────────────────
Central configuration using pydantic-settings.
All values are read from environment variables / .env file.
"""

import os
from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ── App ──────────────────────────────────────────────────────────────────
    APP_ENV: str = os.getenv("APP_ENV")
    APP_SECRET_KEY: str = os.getenv("APP_SECRET_KEY")
    APP_CORS_ORIGINS: str = os.getenv("APP_CORS_ORIGINS")

    @property
    def cors_origins(self) -> list[str]:
        return [o.strip() for o in self.APP_CORS_ORIGINS.split(",")]

    # ── Database ─────────────────────────────────────────────────────────────
    DATABASE_URL: str = os.getenv("DATABASE_URL")
    DATABASE_URL_SYNC: str = os.getenv("DATABASE_URL_SYNC")

    # ── JWT ──────────────────────────────────────────────────────────────────
    JWT_SECRET_KEY: str = os.getenv("JWT_SECRET_KEY")
    JWT_ALGORITHM: str = os.getenv("JWT_ALGORITHM")
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # ── OpenAI ───────────────────────────────────────────────────────────────
    GROQ_API_KEY: str = os.getenv("GROQ_API_KEY")
    GROQ_MODEL: str = "openai/gpt-oss-120b"
    GROQ_TEMPERATURE: float = 0.5

    # ── LangSmith ────────────────────────────────────────────────────────────
    LANGCHAIN_TRACING_V2: bool = True
    LANGCHAIN_API_KEY: str = os.getenv("LANGCHAIN_API_KEY")
    LANGCHAIN_PROJECT: str = "AI Blog Generator"
    LANGCHAIN_ENDPOINT: str = "https://api.smith.langchain.com"

    # ── Tavily ───────────────────────────────────────────────────────────────
    TAVILY_API_KEY: str = os.getenv("TAVILY_API_KEY")

    # ── SerpAPI ──────────────────────────────────────────────────────────────
    SERPAPI_API_KEY: str = os.getenv("SERPAPI_API_KEY")


@lru_cache
def get_settings() -> Settings:
    """Cached singleton — importable anywhere."""
    return Settings()


settings = get_settings()