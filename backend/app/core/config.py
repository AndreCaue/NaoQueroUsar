import re
from functools import lru_cache
from typing import List

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# Cloudflare's public always-pass test secret (dev/CI only — never a real secret).
DEV_TURNSTILE_SECRET = "1x0000000000000000000000000000000AA"

# Cloudflare test secrets are 35 chars: "1x"/"2x"/"3x" + 31 chars + "AA".
# The length matters: a shorter pattern would let the always-pass key slip
# through the prod validator (D-12).
_TURNSTILE_TEST_KEY_RE = re.compile(r"^[123]x[0-9A-Za-z]{31}AA$")


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

    # Cloudflare Turnstile + rate limiting (Phase 3 — SECR-01/02/03)
    TURNSTILE_SECRET_KEY: str = ""
    TURNSTILE_SITE_KEY: str = ""
    TURNSTILE_TIMEOUT_SECONDS: float = 10.0
    REVEAL_RATE_LIMIT: str = "10/minute"     # D-06 — env-tunable, no deploy needed
    LOGIN_RATE_LIMIT: str = "5/minute"       # D-06 — env-tunable, no deploy needed

    @model_validator(mode="after")
    def _validate_turnstile(self) -> "Settings":
        """Fail closed: no secret (or a known test key) outside dev (D-11/D-12)."""
        if self.ENV != "dev":
            secret = self.TURNSTILE_SECRET_KEY.strip()
            if not secret:
                raise ValueError(
                    "TURNSTILE_SECRET_KEY é obrigatória fora de dev (D-11)"
                )
            if _TURNSTILE_TEST_KEY_RE.match(secret):
                raise ValueError(
                    "chave de teste do Cloudflare (1x/2x/3x) não é permitida fora de dev (D-12)"
                )
        return self

    @property
    def effective_turnstile_secret(self) -> str:
        """The secret to use at runtime.

        In dev an empty secret falls back to Cloudflare's public always-pass
        key so local dev and CI run without a Cloudflare account (D-12).
        """
        secret = self.TURNSTILE_SECRET_KEY.strip()
        if secret:
            return secret
        if self.ENV == "dev":
            return DEV_TURNSTILE_SECRET
        return ""

    @property
    def cors_origins_list(self) -> List[str]:
        origins = self.CORS_ORIGINS.split(",")
        return [origin.strip() for origin in origins]

    @property
    def turnstile_mode(self) -> str:
        """``live`` | ``test`` | ``disabled`` — never reveals the secret.

        ``test`` means the effective secret is one of Cloudflare's public test
        keys (the always-pass one used in dev and CI); ``live`` means a real
        secret is in use; ``disabled`` means there is no secret at all.

        The classification lives next to the fail-closed validator so the
        test-key pattern has exactly one home in the codebase.
        """
        secret = self.effective_turnstile_secret
        if not secret:
            return "disabled"
        if _TURNSTILE_TEST_KEY_RE.match(secret):
            return "test"
        return "live"


@lru_cache
def get_settings() -> Settings:
    return Settings()
