
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Sentinel"
    app_version: str = "0.1.0"
    environment: str = "development"
    database_url: str = "sqlite:///./sentinel.db"

    gemini_api_key: str | None = None
    gemini_model: str = "gemini-3.5-flash-lite"

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore",
    )


settings = Settings()
