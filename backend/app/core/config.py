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

    # Groq (Phase 2) — never hardcode a model (PITFALL 1)
    GROQ_API_KEY: str = ""
    GROQ_MODEL: str = "openai/gpt-oss-20b"
    GROQ_MODEL_FALLBACK: str = "openai/gpt-oss-120b"
    GROQ_TIMEOUT_SECONDS: int = 60
    # Extraction caps/throttling (EXTR-04, PITFALL 10)
    EXTRACT_MAX_TEXT_BYTES: int = 262144      # 256 KB paste cap
    EXTRACT_MAX_JOBS: int = 50                # per-extract job cap
    EXTRACT_CHUNK_MAX_TOKENS: int = 3500      # ~chars/4 heuristic; free TPM is 8K
    EXTRACT_CHUNK_DELAY_SECONDS: float = 2.5  # RPM 30 => >=2s between calls
    EXTRACT_TIMEOUT_SECONDS: int = 180        # overall sync request budget (D-01)

    @property
    def cors_origins_list(self) -> List[str]:
        origins = self.CORS_ORIGINS.split(",")
        return [origin.strip() for origin in origins]


@lru_cache
def get_settings() -> Settings:
    return Settings()
