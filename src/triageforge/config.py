from functools import lru_cache
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    jwt_secret: str = Field(min_length=32)
    jwt_algorithm: str = "HS256"
    token_ttl_minutes: int = 30

    provider: Literal["ollama", "groq", "mock"] = "ollama"
    ollama_url: str = "http://localhost:11434"
    ollama_model: str = "qwen2.5:1.5b"
    groq_api_key: str = ""
    groq_model: str = "llama-3.1-8b-instant"
    request_timeout_s: float = 120.0

    rate_limit_per_min: int = 10
    daily_token_quota: int = 50_000


@lru_cache
def get_settings() -> Settings:
    return Settings()
