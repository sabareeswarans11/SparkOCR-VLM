"""Environment-driven settings via pydantic-settings."""

from __future__ import annotations

from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """All API keys + tunables come from the environment (.env file or process env)."""

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore", case_sensitive=False
    )

    # API keys (all optional — backends raise if their key is missing at call time)
    openrouter_api_key: SecretStr | None = None
    together_api_key: SecretStr | None = None
    gemini_api_key: SecretStr | None = None
    modal_token_id: SecretStr | None = None
    modal_token_secret: SecretStr | None = None

    # Databricks (only required for push_databricks.sh)
    databricks_host: str | None = None
    databricks_token: SecretStr | None = None

    # S3 / MinIO (only when using local Delta via MinIO)
    s3_endpoint_url: str | None = None
    aws_access_key_id: str | None = None
    aws_secret_access_key: SecretStr | None = None

    # Default backend + model (override per-call or via env)
    sparkocr_default_backend: str = "openrouter"
    sparkocr_default_model: str = "qwen/qwen2.5-vl-72b-instruct:free"

    # Behavior flags
    log_costs: bool = False  # SPARKOCR_LOG_COSTS=1 appends to runtime/COSTS.md
    private_runtime: bool = False  # SPARKOCR_PRIVATE_RUNTIME=1 keeps runtime/ out of git


# Lazy singleton — call settings() rather than importing a module-level instance,
# so tests can monkeypatch the env before settings is built.
_settings: Settings | None = None


def settings() -> Settings:
    """Return cached Settings, building on first call."""
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings


def reset_settings() -> None:
    """For tests only."""
    global _settings
    _settings = None
