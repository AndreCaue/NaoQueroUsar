---
phase: 14-fundacao-social-dados-e-configuracao
reviewed: 2026-11-15T00:00:00Z
depth: standard
files_reviewed: 14
files_reviewed_list:
  - backend/.env.example
  - backend/alembic/env.py
  - backend/alembic/versions/0004_social_foundation.py
  - backend/app/core/config.py
  - backend/app/models/__init__.py
  - backend/app/models/social_account.py
  - backend/app/models/social_post.py
  - backend/app/models/social_post_log.py
  - backend/app/services/social/__init__.py
  - backend/app/services/social/crypto.py
  - backend/app/services/social/facebook.py
  - backend/app/services/social/publisher.py
  - backend/app/services/social/types.py
  - backend/pyproject.toml
findings:
  critical: 0
  warning: 4
  info: 1
  total: 5
status: issues_found
---

# Phase 14: Code Review Report

**Reviewed:** 2026-11-15T00:00:00Z
**Depth:** standard
**Files Reviewed:** 14
**Status:** issues_found

## Summary

Reviewed the Phase 14 social foundation artifacts (env/config, Alembic migration, SQLAlchemy models, and social service stubs/crypto utilities) at standard depth. The schema and configuration scaffolding are generally coherent (native enums, FK/cascade, indexes, Fernet key validation in settings), but there are contract and data-handling gaps that can lead to insecure token storage usage, interface drift, and misleading timestamps if carried into Phase 17 implementation without correction.

## Warnings

### WR-01: `SocialAccount.page_access_token` has no enforced encryption boundary

**File:** `backend/app/models/social_account.py:29`, `backend/alembic/versions/0004_social_foundation.py:44`, `backend/app/services/social/crypto.py:19-33`
**Issue:** The account model and migration persist `page_access_token` as plain text, while the codebase also introduces Fernet encrypt/decrypt helpers. Without an explicit write/read boundary (e.g., service/repository/helper that always encrypts before persist and decrypts on use), future callers can accidentally store raw provider tokens in the database. This is a sensitive-secret handling risk for Meta page access tokens.
**Fix:**
```python
# Example direction: enforce encryption at the persistence/use boundary
# (model field can still store ciphertext as Text, but callers must not pass plaintext).

from app.services.social.crypto import encrypt_token, decrypt_token

def set_page_access_token(account: SocialAccount, plaintext_token: str, key: str) -> None:
    account.page_access_token = encrypt_token(plaintext_token, key)

def get_page_access_token(account: SocialAccount, key: str) -> str:
    return decrypt_token(account.page_access_token, key)

# Optionally rename/document storage semantics:
# page_access_token_ciphertext: Mapped[str] = mapped_column("page_access_token", Text, nullable=False)
```

### WR-02: `FacebookPublisher.publish` signature does not match the `SocialPublisher` protocol

**File:** `backend/app/services/social/facebook.py:13`, `backend/app/services/social/publisher.py:9`, `backend/app/services/social/types.py:21-25`
**Issue:** The protocol requires `publish(self, post: SocialPostPayload) -> PublishResult`, but the Facebook stub accepts `post: SocialPostPayload | object | None = None`. This weakens the contract, hides required payload usage, and can allow callers/type checkers to diverge from the intended interface before real publishing logic is added.
**Fix:**
```python
class FacebookPublisher(SocialPublisher):
    async def publish(self, post: SocialPostPayload) -> PublishResult:
        # `post` will be required when the real implementation is added.
        return PublishResult(
            ok=False,
            external_post_id=None,
            category=PublishFailureCategory.unknown,
            error_message="publicação Facebook não implementada na Fase 14 (stub)",
        )
```

### WR-03: `updated_at` columns default to `now()` but are never auto-updated

**File:** `backend/app/models/social_account.py:48-52`, `backend/app/models/social_post.py:66-70`, `backend/alembic/versions/0004_social_foundation.py:66-70,116-120`
**Issue:** Both `social_accounts.updated_at` and `social_posts.updated_at` are initialized with `server_default=now()` but have no `onupdate`/database trigger. Any future status/token/retry updates will leave `updated_at` stale, which undermines auditing, debugging, and worker observability.
**Fix:**
```python
# Model example
from sqlalchemy import func

updated_at: Mapped[datetime] = mapped_column(
    TIMESTAMP(timezone=True),
    nullable=False,
    server_default=sql_text("now()"),
    onupdate=func.now(),
)

# Migration example (if DB-side behavior is desired, use a trigger or server-side onupdate strategy
# appropriate for the stack; at minimum keep ORM onupdate consistent).
```

### WR-04: Crypto key errors are handled asymmetrically (`decrypt` wrapped, `encrypt`/`validate` leak raw exception types)

**File:** `backend/app/services/social/crypto.py:10-26`
**Issue:** `decrypt_token` converts invalid-token/key issues into a safe domain error, but `encrypt_token` (and `validate_fernet_key` callers outside settings context) can raise raw `ValueError`/library exceptions from `Fernet(...)`. This inconsistency can produce unclear failures or accidental leakage of low-level error details at call sites that only expect the module's safe failure mode.
**Fix:**
```python
class SocialTokenEncryptError(Exception):
    """Falha segura de criptografia de token social (sem expor segredo)."""

def encrypt_token(plaintext: str, key: str | bytes) -> str:
    try:
        key_bytes = key.encode() if isinstance(key, str) else key
        return Fernet(key_bytes).encrypt(plaintext.encode()).decode()
    except Exception as exc:
        raise SocialTokenEncryptError("chave de criptografia inválida para token social") from exc

def validate_fernet_key(key: str | bytes) -> None:
    try:
        key_bytes = key.encode() if isinstance(key, str) else key
        Fernet(key_bytes)
    except Exception as exc:
        raise ValueError("SOCIAL_TOKEN_ENCRYPTION_KEY inválida") from exc
```

## Info

### IN-01: `social_post_logs.response_summary`/`error_message` have no explicit redaction/truncation policy

**File:** `backend/app/models/social_post_log.py:31-33`, `backend/alembic/versions/0004_social_foundation.py:145-146`
**Issue:** Log fields are free-form text and may eventually capture provider responses or error payloads. Without an explicit sanitization/truncation policy at write time, future implementations could persist sensitive or excessively large upstream payloads.
**Fix:**
```python
# Apply a centralized sanitizer before persisting logs, e.g.:
# - strip tokens/secrets/PII patterns
# - cap length (e.g. 1-2 KB)
# - store structured error codes separately when possible
log.response_summary = sanitize_and_truncate(response_summary, max_chars=2000)
```

---

_Reviewed: 2026-11-15T00:00:00Z_
_Reviewer: OpenCode (gsd-code-reviewer)_
_Depth: standard_
