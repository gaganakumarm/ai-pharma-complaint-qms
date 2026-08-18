from functools import lru_cache

from pydantic import AnyHttpUrl, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application configuration sourced from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )

    app_name: str = "AI Pharma Complaint QMS"
    environment: str = "development"
    database_url: str = (
        "postgresql+asyncpg://postgres:postgres@localhost:5432/pharma_qms"
    )
    groq_api_key: str = ""
    groq_model: str = "openai/gpt-oss-120b"
    cors_origins: list[AnyHttpUrl] = Field(
        default_factory=lambda: [
            AnyHttpUrl("http://localhost:5173"),
            AnyHttpUrl("http://127.0.0.1:5173"),
        ]
    )
    max_upload_size_mb: int = Field(default=10, gt=0)
    max_pdf_pages: int = Field(default=50, gt=0, le=500)
    max_pdf_text_length: int = Field(default=20000, ge=1000, le=100000)
    max_text_input_length: int = Field(default=20000, ge=1000, le=100000)
    max_correction_instruction_length: int = Field(default=2000, ge=100, le=10000)


@lru_cache
def get_settings() -> Settings:
    return Settings()
