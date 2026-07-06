"""Application configuration."""

from functools import lru_cache
from typing import List

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "Photo Printing Management System"
    app_env: str = "development"
    secret_key: str = "change-me"
    debug: bool = True

    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/photo_printing"

    jwt_secret_key: str = "change-me-jwt"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7

    storage_type: str = "local"
    local_storage_path: str = "./uploads"
    s3_endpoint_url: str = ""
    s3_access_key: str = ""
    s3_secret_key: str = ""
    s3_bucket_name: str = "photo-printing"
    s3_region: str = "us-east-1"

    frontend_url: str = "http://localhost:3000"
    cors_origins: str = "http://localhost:3000"

    rate_limit_per_minute: int = 60

    smtp_host: str = ""
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_password: str = ""
    smtp_from: str = "noreply@system.com"

    max_upload_size_mb: int = 20
    allowed_mime_types: List[str] = ["image/jpeg", "image/png", "image/webp"]

    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors(cls, value: str) -> str:
        return value

    @property
    def cors_origins_list(self) -> List[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]

    @property
    def max_upload_size_bytes(self) -> int:
        return self.max_upload_size_mb * 1024 * 1024

    @property
    def is_production(self) -> bool:
        return self.app_env == "production"


@lru_cache
def get_settings() -> Settings:
    return Settings()
