from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore",
    )

    # --- Core runtime ---
    ENV: str = "dev"
    SERVICE_NAME: str = "computer-use-backend"

    # --- Database / cache ---
    DATABASE_URL: str = "postgresql+psycopg://postgres:postgres@db:5432/agent"
    REDIS_URL: str = "redis://redis:6379/0"

    # --- Networking ---
    PUBLIC_HOST: str = "localhost"  # host where browser accesses mapped ports

    # --- Computer-use agent ---
    COMPUTER_USE_IMAGE: str = (
        "ghcr.io/anthropics/anthropic-quickstarts:computer-use-demo-latest"
    )

    AGENT_MODE: Literal["mock", "anthropic"] = "mock"

    # --- Anthropic / Claude ---
    ANTHROPIC_API_KEY: str | None = None
    ANTHROPIC_MODEL: str = "claude-3-5-sonnet-latest"

    # --- API auth (frontend → backend) ---
    API_KEY: str | None = None


settings = Settings()
