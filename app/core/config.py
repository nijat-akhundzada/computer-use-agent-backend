from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    DATABASE_URL: str = "postgresql+psycopg://postgres:postgres@db:5432/agent"
    REDIS_URL: str = "redis://redis:6379/0"
    ENV: str = "dev"


settings = Settings()
