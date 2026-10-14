from functools import lru_cache
from typing import List

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    ENV: str = "dev"
    DATABASE_URL: str
    ADMIN_PASSWORD_HASH: str
    JWT_SECRET: str
    JWT_EXPIRES_IN: int = 43200
    CORS_ORIGINS: str = "http://localhost:3000"
    TEST_DATABASE_URL: str | None = None

    @property
    def cors_origins_list(self) -> List[str]:
        origins = self.CORS_ORIGINS.split(",")
        return [origin.strip() for origin in origins]


@lru_cache
def get_settings() -> Settings:
    return Settings()
