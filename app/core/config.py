from __future__ import annotations

from functools import lru_cache
from typing import Literal

from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class TokenConfig(BaseModel):
    secret_key: str = Field(default="change-me", min_length=16)
    algorithm: Literal["HS256"] = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_minutes: int = 60 * 24


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "Mini CRM"
    api_v1_prefix: str = "/api/v1"
    database_url: str = Field(
        default="postgresql+asyncpg://postgres:postgres@localhost:5432/mini_crm",
        description="SQLAlchemy compatible database URL",
    )
    token: TokenConfig = TokenConfig()
    default_page_size: int = 20
    max_page_size: int = 100
    analytics_cache_ttl_seconds: int = 60


@lru_cache
def get_settings() -> Settings:
    return Settings()
