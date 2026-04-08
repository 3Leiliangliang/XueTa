from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "XueTa Backend"
    app_env: str = "development"
    app_version: str = "0.1.0"
    api_v1_prefix: str = "/api/v1"
    project_description: str = (
        "Backend services for the XueTa AI learning assistant, including auth, "
        "planning, note taking, chat, retrieval, practice and progress tracking."
    )

    secret_key: str = "replace-me"
    access_token_expire_minutes: int = 60
    refresh_token_expire_days: int = 14

    database_url: str = Field(
        default="postgresql+psycopg://postgres:postgres@localhost:5432/xueta"
    )
    redis_url: str = "redis://localhost:6379/0"
    cors_origins: list[str] = ["http://localhost:5173"]

    run_migrations_on_startup: bool = False
    auto_create_tables: bool = True

    openai_api_key: str | None = None
    openai_model: str = "gpt-4o"
    openai_embedding_model: str = "text-embedding-3-small"

    langfuse_public_key: str | None = None
    langfuse_secret_key: str | None = None
    langfuse_host: str = "https://cloud.langfuse.com"

    local_storage_path: str = "storage"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
