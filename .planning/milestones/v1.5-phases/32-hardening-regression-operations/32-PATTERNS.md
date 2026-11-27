# Phase 32: Hardening, Regression & Operations - Pattern Map

**Mapped:** 2026-11-26
**Files analyzed:** 14
**Analogs found:** 14 / 14

## File Classification

| New/Modified File | Role | Data Flow | Closest Analog | Match Quality |
|---|---|---|---|---|
| `backend/tests/test_facebook_publisher.py` | test | request-response | `backend/tests/test_facebook_publisher.py` | exact (extend in place, D-01) |
| `backend/tests/test_social_publish_pipeline.py` | test | async state-machine | `backend/tests/test_social_publish_pipeline.py` | exact (extend in place, D-01) |
| `backend/tests/test_instagram_publisher.py` | test | request-response | `backend/tests/test_instagram_publisher.py` | exact (extend if HARD-01 gap) |
| `backend/tests/test_social_post_generation.py` | test | transform | `backend/tests/test_social_post_generation.py` | exact (extend if HARD-01 gap) |
| `backend/tests/test_ig_media_validation.py` | test | request-response | `backend/tests/test_ig_media_validation.py` | exact (extend if HARD-01 gap) |
| `backend/tests/test_social_idempotency.py` | test | async state-machine | `backend/tests/test_social_idempotency.py` | exact (FB gate candidate) |
| `backend/tests/test_social_retry_policy.py` | test | transform | `backend/tests/test_social_retry_policy.py` | exact (FB gate candidate) |
| `backend/tests/test_admin_social_publish.py` | test | request-response | `backend/tests/test_admin_social_publish.py` | exact (FB gate candidate) |
| `backend/tests/test_admin_social_retry_api.py` | test | request-response | `backend/tests/test_admin_social_retry_api.py` | exact (FB gate candidate) |
| `backend/tests/test_admin_social_status_api.py` | test | request-response | `backend/tests/test_admin_social_status_api.py` | exact (FB gate candidate) |
| `backend/tests/test_admin_instagram_social_posts.py` | test | request-response | `backend/tests/test_admin_instagram_social_posts.py` | exact (draft/validation gap candidate) |
| `docs/META-INTEGRATION-TESTING.md` | config | doc/ops runbook | `docs/META-INTEGRATION-TESTING.md` | exact (expand, D-09) |
| `backend/.env.example` | config | env contract | `backend/.env.example` | exact (align if needed, D-11/A3) |
| `.planning/phases/32-hardening-regression-operations/32-VERIFICATION.md` | config | evidence artifact | `.planning/phases/31-independent-publish-pipeline/31-VERIFICATION.md` | role-match (new file, same format) |

## Pattern Assignments

### `backend/tests/test_facebook_publisher.py` (test, request-response)

**Analog:** `backend/tests/test_facebook_publisher.py` (extend in place; D-01/D-02/D-03)
**Role in phase:** Primary FB publisher contract/gate file. Extend for explicit FB regression/contract cases without snapshotting full payloads.

**Imports pattern** (`backend/tests/test_facebook_publisher.py:1-6`):
```python
import httpx
import pytest

from app.services.social.facebook import FacebookPublisher
from app.services.social.types import PublishFailureCategory, SocialPostPayload
```

**Fake httpx client / monkeypatch pattern** (`backend/tests/test_facebook_publisher.py:9-38,60-97`):
```python
@pytest.mark.asyncio
async def test_facebook_publisher_posts_message_link_and_returns_external_id(monkeypatch):
    calls = {}

    class FakeResponse:
        status_code = 200

        def json(self):
            return {"id": "123_456"}

    class FakeAsyncClient:
        def __init__(self, *args, **kwargs):
            calls["init_kwargs"] = kwargs

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            return False

        async def post(self, url, data=None):
            calls["url"] = url
            calls["data"] = data
            return FakeResponse()

    monkeypatch.setattr(httpx, "AsyncClient", FakeAsyncClient)
    monkeypatch.setattr(
        "app.services.social.facebook.get_settings",
        lambda: type("S", (), {"META_GRAPH_VERSION": "v21.0"})(),
    )
```

**Behavioral contract assertions (no full-payload snapshots, D-03)** (`backend/tests/test_facebook_publisher.py:51-56,94-97,118-121,136-140,162-165`):
```python
assert result.ok is True
assert result.external_post_id == "123_456"
assert calls["url"] == "https://graph.facebook.com/v21.0/page-1/feed"

result = await publisher.publish(payload)
assert result.ok is False
assert result.category == PublishFailureCategory.transient
assert "automática" in (result.error_message or "").lower() or "tempor" in (result.error_message or "").lower()

# timeout -> ambiguous (anti-duplicate)
assert result.category == PublishFailureCategory.ambiguous
assert "duplic" in (result.error_message or "").lower() or "confirmar" in (result.error_message or "").lower()

# permanent
assert result.category == PublishFailureCategory.permanent
assert "não foi possível publicar" in (result.error_message or "").lower() or "revise" in (result.error_message or "").lower()
```

**What to copy:** Same `FakeAsyncClient`/`FakeResponse`, `monkeypatch.setattr(httpx, "AsyncClient", ...)`, settings stub, `SocialPostPayload(...)`, and category/safe-message assertions. Add new FB gate cases as separate `@pytest.mark.asyncio` tests; keep assertions on behavior/state/category/safe pt-BR fragments.

---

### `backend/tests/test_social_publish_pipeline.py` (test, async state-machine)

**Analog:** `backend/tests/test_social_publish_pipeline.py` (extend in place; D-01/D-02/HARD-01 gaps)
**Role in phase:** Core provider-aware pipeline coverage: FB full-cycle gate pieces, IG ambiguity/reconciliation/rate-limit/provider isolation, idempotency/retry semantics.

**Imports / fake session pattern** (`backend/tests/test_social_publish_pipeline.py:1-26`):
```python
import uuid
from datetime import datetime, timezone
from types import SimpleNamespace

import pytest

from app.models.social_account import SocialAccountStatus
from app.models.social_post import SocialPostStatus
from app.services.social.publish_pipeline import MSG_RECONNECT, MSG_TRANSIENT, process_claimed_post
from app.services.social.types import PublishFailureCategory, PublishResult


class FakeSession:
    def __init__(self, job=None):
        self._job = job
        self.added = []

    async def get(self, model, ident):
        return self._job

    def add(self, obj):
        self.added.append(obj)

    async def flush(self):
        return None
```

**Pipeline setup/monkeypatch pattern** (`backend/tests/test_social_publish_pipeline.py:29-77,80-132`):
```python
job_id = uuid.uuid4()
post = SimpleNamespace(
    id=uuid.uuid4(),
    job_id=job_id,
    provider="facebook",
    text="Texto",
    status=SocialPostStatus.publishing,
    attempts=0,
    next_retry_at=None,
    last_error=None,
    external_post_id=None,
    published_at=None,
)
settings = SimpleNamespace(
    SITE_PUBLIC_URL="https://site.exemplo/",
    SOCIAL_MAX_ATTEMPTS=5,
    social_retry_delays_list=[300, 900, 3600, 10800, 21600],
    SOCIAL_TOKEN_ENCRYPTION_KEY="k",
)

async def noop_log(*args, **kwargs):
    return None

monkeypatch.setattr(pipeline, "_append_log", noop_log)
outcome = await process_claimed_post(
    FakeSession(job=SimpleNamespace(id=job_id)),
    post,
    settings=settings,
    publisher=TransientPublisher(),
    now=now,
)
assert outcome == "retried"
assert post.status == SocialPostStatus.failed
assert post.attempts == 1
assert post.last_error == MSG_TRANSIENT
```

**IG ambiguity/reconciliation pattern** (`backend/tests/test_social_publish_pipeline.py:331-414`):
```python
class AmbiguousIGPublisher:
    async def publish(self, payload):
        return PublishResult(
            ok=False,
            category=PublishFailureCategory.ambiguous,
            error_message="ambiguous",
            container_id="container-1",
            error_code="ig_publish_timeout_ambiguous",
        )

outcome = await process_claimed_post(..., publisher=AmbiguousIGPublisher(), ...)
assert outcome == "failed_final"
assert post.status == SocialPostStatus.failed
assert post.next_retry_at is None
assert post.ig_reconciliation_required is True
assert post.ig_reconciliation_state == "needs_reconciliation"
assert post.ig_container_id == "container-1"
```

**IG rate-limit no-retry-storm pattern** (`backend/tests/test_social_publish_pipeline.py:417-466`):
```python
class RateLimitPublisher:
    async def publish(self, payload):
        return PublishResult(
            ok=False,
            category=PublishFailureCategory.permanent,
            error_message="rate",
            error_code="ig_content_publishing_limit",
        )

outcome = await process_claimed_post(...)
assert outcome == "failed_final"
assert post.next_retry_at is None
assert post.ig_last_publish_error_code == "ig_content_publishing_limit"
assert "limite" in (post.last_error or "").lower()
```

**Provider isolation pattern** (`backend/tests/test_social_publish_pipeline.py:470-520`):
```python
# IG post fails preflight as not ready
outcome = await process_claimed_post(FakeSession(job=SimpleNamespace(id=ig_job_id)), ig_post, settings=settings)
assert outcome == "failed_final"
assert ig_post.status == SocialPostStatus.failed
assert ig_post.next_retry_at is None

# FB post remains processable independently
fb_outcome = await process_claimed_post(FakeSession(job=SimpleNamespace(id=fb_job_id)), fb_post, settings=settings, publisher=OkFB())
assert fb_outcome == "published"
assert fb_post.status == SocialPostStatus.published
```

**Claim filter / DB-query contract pattern** (`backend/tests/test_social_publish_pipeline.py:311-328`):
```python
await list_due_for_claim(FakeSession(), provider="instagram", limit=10)
stmt = captured["stmt"]
compiled = str(stmt.compile(compile_kwargs={"literal_binds": False}))
assert "publish_enabled" in compiled
```

**What to copy:** `SimpleNamespace` post/account/settings fixtures, `FakeSession`, monkeypatching `pipeline.*` dependencies, fake publisher classes with `async def publish(self, payload)`, and behavioral assertions on `outcome`, `post.status`, `next_retry_at`, reconciliation fields, safe error fragments. For FB gate extensions, prefer same `process_claimed_post` + explicit outcome/status/error/retry assertions.

---

### `backend/tests/test_instagram_publisher.py` (test, request-response)

**Analog:** `backend/tests/test_instagram_publisher.py` (extend only for real HARD-01 gaps)
**Role in phase:** IG publisher contract: 2-step create/status/publish, timeout ambiguity, 2207042/content_publishing_limit, permalink best-effort, safe failures.

**Fake response/client pattern** (`backend/tests/test_instagram_publisher.py:14-50`):
```python
class FakeResponse:
    def __init__(self, status_code=200, body=None, json_exc=False):
        self.status_code = status_code
        self._body = body
        self._json_exc = json_exc

    def json(self):
        if self._json_exc:
            raise ValueError("bad json")
        return self._body

class FakeAsyncClient:
    def __init__(self, responses):
        self._responses = list(responses)
        self.calls = []

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return False

    async def post(self, url, data=None, **kwargs):
        self.calls.append(("POST", url, data))
        item = self._responses.pop(0)
        if isinstance(item, Exception):
            raise item
        return item

    async def get(self, url, params=None, **kwargs):
        self.calls.append(("GET", url, params))
        item = self._responses.pop(0)
        if isinstance(item, Exception):
            raise item
        return item
```

**Payload/settings monkeypatch pattern** (`backend/tests/test_instagram_publisher.py:53-66,98-126`):
```python
def _ig_payload(**overrides):
    base = dict(
        job_id="job-1",
        provider="instagram",
        message="Legenda IG",
        image_url="https://media.example.com/ig.jpg",
        ig_user_id="1789",
        page_access_token="plain-token",
    )
    base.update(overrides)
    return SocialPostPayload(**base)

monkeypatch.setattr(ig_mod.httpx, "AsyncClient", lambda timeout=None: fake)
monkeypatch.setattr(ig_mod, "get_settings", lambda: type("S", (), {...})())
```

**Key IG contract assertions** (`backend/tests/test_instagram_publisher.py:128-135,174-205,208-232,236-252`):
```python
assert result.ok is True
assert result.external_post_id == "media-1"
assert result.container_id == "container-1"
assert result.published_media_id == "media-1"
assert result.permalink == "https://instagram.com/p/abc"

# timeout after create = ambiguous
assert result.ok is False
assert result.category == PublishFailureCategory.ambiguous
assert result.container_id == "container-1"
assert "access_token" not in (result.error_message or "").lower()

# 2207042/content_publishing_limit = blocked, no retry storm
assert result.category == PublishFailureCategory.permanent
assert result.error_code in {"ig_rate_limit_blocked", "ig_content_publishing_limit"}
assert "aguarde" in (result.error_message or "").lower()

# permalink best-effort
assert result.ok is True
assert result.external_post_id == "media-1"
assert result.permalink is None
```

**What to copy:** `FakeAsyncClient` with queued responses/exceptions, `_ig_payload`, `ig_mod` monkeypatching, and assertions on `ok/category/error_code/container_id/published_media_id/permalink` plus safe-text checks.

---

### `backend/tests/test_social_post_generation.py` (test, transform)

**Analog:** `backend/tests/test_social_post_generation.py` (extend if HARD-01 draft/validation gap exists)
**Role in phase:** Draft generation/normalization and policy-safe output for HARD-01 "draft/validação Instagram" backend scope.

**Fake Groq/settings/job pattern** (`backend/tests/test_social_post_generation.py:13-73,75-113`):
```python
def _settings(site_url="https://site.exemplo/"):
    return SimpleNamespace(
        SITE_PUBLIC_URL=site_url,
        GROQ_API_KEY="gsk_test",
        GROQ_MODEL="openai/gpt-oss-20b",
        GROQ_TIMEOUT_SECONDS=30,
        SOCIAL_POST_INCLUDE_CONTACT=False,
    )

class _FakeGroqClient:
    def __init__(self, *, content=None, exc=None):
        self.chat = _FakeChat(content=content, exc=exc)

result = await generate_draft_for_job(job, settings=settings, client=client)
assert result.origin == "llm"
assert result.warning is None
assert link in result.text
assert "Empresa Confidencial SA" not in result.text
assert "rh@confidencial.com" not in result.text
```

**What to copy:** `SimpleNamespace` settings/job, fake Groq client, assertions on `origin`, `warning`, link presence, policy-safe sanitization (no company/contacts leaked).

---

### `backend/tests/test_ig_media_validation.py` (test, request-response)

**Analog:** `backend/tests/test_ig_media_validation.py` (extend if HARD-01 gap exists)
**Role in phase:** IG media validation/preparation contracts, pt-BR safe messages, no contact/provenance leakage.

**DB-backed validation pattern** (`backend/tests/test_ig_media_validation.py:20-35,42-53,72-88`):
```python
@pytest.mark.asyncio
async def test_prepare_returns_invalid_public_url_with_ptbr_message(db_session, seed_published_job, monkeypatch):
    settings = SimpleNamespace(MEDIA_PUBLIC_BASE_URL="http://localhost:8000")
    monkeypatch.setattr(image_media, "_generate_asset_bytes", lambda job: _async_bytes(b"fake"))

    resp = await prepare_instagram_media(db_session, seed_published_job.id, settings)

    assert resp.validation.valid is False
    assert resp.validation.code == "invalid_public_url"
    assert resp.validation.message == MSG_INVALID_PUBLIC_URL
    assert resp.image_url is None
    assert "contact_email" not in resp.provenance

resp = await prepare_instagram_media(db_session, seed_published_job.id, settings)
assert resp.validation.valid is True
assert resp.image_url.startswith("https://media.example.com/api/v1/public/ig-media/")
```

**What to copy:** `db_session`/`seed_published_job` fixtures, `SimpleNamespace(MEDIA_PUBLIC_BASE_URL=...)`, monkeypatch `image_media._generate_asset_bytes`, assertions on `validation.valid/code/message`, safe provenance, and public URL shape.

---

### `backend/tests/test_social_idempotency.py` (test, async state-machine)

**Analog:** `backend/tests/test_social_idempotency.py` (FB gate / HARD-01 idempotency)
**Role in phase:** Idempotency/no-duplicate behavior; FB regression gate candidate.

**Pattern** (`backend/tests/test_social_idempotency.py:24-90`):
```python
post_published = SimpleNamespace(..., status=SocialPostStatus.published, external_post_id="123_456", ...)
outcome = await process_claimed_post(session, post_published, settings=settings, now=now)
assert outcome == "idempotent"

# Duplo acionamento/reexecução não deve criar novo publish nem alterar estado.
assert await process_claimed_post(session, post, settings=settings, now=now) == "idempotent"
assert await process_claimed_post(session, post, settings=settings, now=now) == "idempotent"
```

**What to copy:** Minimal `FakeSession`, `SimpleNamespace` post/settings, repeated `process_claimed_post` calls asserting `idempotent` and no state mutation.

---

### `backend/tests/test_social_retry_policy.py` (test, transform)

**Analog:** `backend/tests/test_social_retry_policy.py` (FB gate / HARD-01 retry semantics)
**Role in phase:** Retry/backoff contract characterization.

**Pattern** (`backend/tests/test_social_retry_policy.py:7-43`):
```python
def _settings(max_attempts=5, delays="300,900,3600,10800,21600"):
    return SimpleNamespace(
        SOCIAL_MAX_ATTEMPTS=max_attempts,
        social_retry_delays_list=[int(x) for x in delays.split(",")],
    )

now = datetime(2026, 1, 1, 12, 0, tzinfo=timezone.utc)
assert compute_next_retry(1, settings, now=now) == datetime(2026, 1, 1, 12, 5, tzinfo=timezone.utc)
assert compute_next_retry(5, settings, now=now) is None
```

**What to copy:** Pure deterministic datetime assertions with `timezone.utc`; keep contract explicit for max attempts/delay progression/exhaustion.

---

### `backend/tests/test_admin_social_publish.py` (test, request-response)

**Analog:** `backend/tests/test_admin_social_publish.py` (FB gate candidate; site-first/dispatch contract)
**Role in phase:** Admin approve/site-first/async dispatch behavior; FB gate full-cycle coverage.

**Admin login + BackgroundTasks spy pattern** (`backend/tests/test_admin_social_publish.py:10-20,44-79,107-139`):
```python
VALID_CF_TOKEN = "token-de-teste"

async def _login(client, admin_password="test-password"):
    resp = await client.post(
        "/api/v1/auth/login",
        json={"password": admin_password, "cf_token": VALID_CF_TOKEN},
    )
    assert resp.status_code == 200
    return resp.json()["access_token"]

calls = []
original_add_task = BackgroundTasks.add_task

def spy_add_task(self, func, *args, **kwargs):
    calls.append((getattr(func, "__name__", str(func)), args, kwargs))
    return original_add_task(self, func, *args, **kwargs)

monkeypatch.setattr(BackgroundTasks, "add_task", spy_add_task)
...
assert any(name == "process_social_post_safe" and args and str(args[0]) == str(post.id) for name, args, _ in calls)
```

**Site-first invariant on dispatch failure** (`backend/tests/test_admin_social_publish.py:107-139`):
```python
def boom(self, func, *args, **kwargs):
    raise RuntimeError("dispatch fail")

monkeypatch.setattr(BackgroundTasks, "add_task", boom)
resp = await client.patch(f"/api/v1/admin/jobs/{job.id}/approve", headers={"Authorization": f"Bearer {token}"})
assert resp.status_code == 200, resp.text
body = resp.json()
assert body["job"]["status"] == "published"
assert body["social"]["status"] == "registered"
```

**What to copy:** `_login` helper, seed pending job, `BackgroundTasks.add_task` spy/boom monkeypatch, assertions on site-first approval and dispatch enqueue/no-enqueue.

---

### `backend/tests/test_admin_social_retry_api.py` (test, request-response)

**Analog:** `backend/tests/test_admin_social_retry_api.py` (FB gate / HARD-01 retry contract)
**Role in phase:** Admin retry endpoint eligibility, pipeline invocation, safe no-op/block reasons.

**Pattern** (`backend/tests/test_admin_social_retry_api.py:12-74,77-118`):
```python
async def _login(client, admin_password="test-password"):
    resp = await client.post("/api/v1/auth/login", json={"password": admin_password, "cf_token": VALID_CF_TOKEN})
    assert resp.status_code == 200
    return resp.json()["access_token"]

async def fake_cycle(*, post_id=None, limit=20):
    called["post_id"] = str(post_id)
    called["limit"] = limit
    return {"claimed": 1, "processed": 1, "published": 1, "retried": 0, "failed_final": 0, "skipped": 0, "idempotent": 0}

monkeypatch.setattr("app.api.v1.admin.run_social_publish_cycle", fake_cycle)
resp = await client.post(.../retry, headers={"Authorization": f"Bearer {token}"})
assert body["outcome"] in {"retried", "noop"}
assert called["post_id"] == str(post.id)
assert body["outcome"] == "not_eligible"
assert "Reconexão" in (body["item"]["retry_block_reason"] or "")
```

**What to copy:** Admin auth helper, DB-seeded `SocialPost`, monkeypatch `app.api.v1.admin.run_social_publish_cycle`, assertions on outcome, `can_retry`, `retry_block_reason`, and no-op behavior.

---

### `backend/tests/test_admin_social_status_api.py` (test, request-response)

**Analog:** `backend/tests/test_admin_social_status_api.py` (FB gate / HARD-01 safe status contract)
**Role in phase:** Safe admin status/list contracts, pt-BR labels, no token/secret leakage.

**Pattern** (`backend/tests/test_admin_social_status_api.py:12-18,35-83,87-120`):
```python
async def _login(client, admin_password="test-password"): ...
resp = await client.get(f"/api/v1/admin/jobs/{seed_published_job.id}/social-status", headers={"Authorization": f"Bearer {token}"})
assert body["status"] == "none"
assert body["status_label"] == "Sem rascunho"
...
assert body["status"] == "failed"
assert body["status_label"] == "Falhou"
assert body["can_retry"] is True
assert "access_token" not in str(body).lower()
assert "page_access_token" not in str(body).lower()
assert "secret" not in str(body).lower()
```

**What to copy:** Endpoint contract assertions for status labels, retryability, safe fields, and explicit secret/token absence checks.

---

### `backend/tests/test_admin_instagram_social_posts.py` (test, request-response)

**Analog:** `backend/tests/test_admin_instagram_social_posts.py` (HARD-01 draft/validation IG backend gap candidate)
**Role in phase:** Backend draft/validation/social-post contracts for IG review flow; only extend for real HARD-01 gaps (D-05/D-06).

**Pattern** (`backend/tests/test_admin_instagram_social_posts.py:21-28,30-49,59-76,78-100`):
```python
async def _login(client, admin_password="test-password"):
    resp = await client.post("/api/v1/auth/login", json={"password": admin_password, "cf_token": VALID_CF_TOKEN})
    assert resp.status_code == 200, resp.text
    return resp.json()["access_token"]

def _valid_media_result():
    return SimpleNamespace(validation=SimpleNamespace(valid=True, code=None, message="Imagem pronta para publicação no Instagram."))

monkeypatch.setenv("SITE_PUBLIC_URL", "https://site.exemplo/")
get_settings.cache_clear()
monkeypatch.setattr("app.api.v1.admin.prepare_instagram_media", fake_prepare_ok)
```

**What to copy:** Admin login helper, DB job seeding, `get_settings.cache_clear()` after env monkeypatch, monkeypatching admin media preparation, endpoint-level assertions for IG draft CRUD/isolation.

---

### `docs/META-INTEGRATION-TESTING.md` (config, doc/ops runbook)

**Analog:** `docs/META-INTEGRATION-TESTING.md` (expand in place; D-09-D-12)
**Role in phase:** Single operational source for Meta/FB + IG readiness + IG publish pipeline troubleshooting. HARD-02 must expand, not duplicate.

**Existing section/table pattern** (`docs/META-INTEGRATION-TESTING.md:1-5,24-38,99-146`):
```markdown
# Integração Meta/Facebook — roteiro de teste manual e operação (TEST-04, DOC-01)

Este documento descreve ... Não contém segredos reais.

## 5) Prontidão Instagram e mídia IG (META-03 / Phase 29)

### 5.4 Estados de prontidão IG e troubleshooting

| Estado | Significado | Ação do admin (pt-BR segura) |
|--------|-------------|------------------------------|
| `ready` | ... | ... |

### 5.5 Checklist manual (handoff)

Execução real depende de credenciais/app Meta e Página de teste. Registrar evidência separadamente; **não marcar como aprovado sem execução real**.

- [ ] Conectar Página Facebook no `/admin/integracoes` com app/permissões corretas.
```

**What to copy / extend:**
- Keep single-doc structure and pt-BR operational tone.
- Add Phase 31 publish-state troubleshooting as **actionable table** (D-10): columns should cover Estado/Sintoma, Significado, Causa provável, Ação do admin, Retry/Reconciliar?, Pré-condições, Escalar quando.
- Add canonical env vars/security table aligned to `backend/.env.example` + `backend/app/core/config.py` (D-11), including IG publish budget vars (`IG_PUBLISH_HTTP_TIMEOUT_SECONDS`, `IG_STATUS_POLL_MAX_ATTEMPTS`, `IG_STATUS_POLL_DELAY_SECONDS`, `IG_PUBLISH_MAX_ATTEMPT_SECONDS`) if they are real config knobs.
- Keep handoff checklist explicit with "não executado / não evidenciado nesta sessão" fields (D-12/D-14).
- Never expose tokens/secrets/payloads brutos.

---

### `backend/.env.example` (config, env contract)

**Analog:** `backend/.env.example` (align only if needed; D-11, A3)
**Role in phase:** Canonical env var reference for HARD-02 docs. Edit only for behavior-preserving documentation/alignment.

**Existing env section/comment pattern** (`backend/.env.example:34-55,66-73`):
```dotenv
# --- Integração Social / Meta (Phase 14 - Fundação) ---
# Variáveis para a fundação da integração com Meta/Facebook (SOC-06) e operação social (v1.2).
# Segredos, chaves e tokens ficam apenas no backend e nunca devem ser expostos ao frontend ou logs.
# Preencha os segredos somente no ambiente real (.env/deploy), sem versionar valores reais.
META_APP_ID=
...
SOCIAL_RETRY_DELAYS=300,900,3600,10800,21600
SITE_PUBLIC_URL=

# --- Instagram / Mídia IG (Phase 29) ---
# Base pública HTTPS do backend usada para servir mídia IG acessível pela Meta. Não usar localhost/IP privado.
MEDIA_PUBLIC_BASE_URL=

# --- Cron / operação agendada (expiração e worker social) ---
# CRON_SECRET protege endpoints operacionais acionados por cron (X-Cron-Secret, fail-closed T-06-01):
CRON_SECRET=
```

**What to copy:** Section header comments with phase/intent, pt-BR security note, placeholder-only values. If adding IG publish budget vars, put them in a clearly named Instagram/publish section and document safe defaults/intent; do not add real secrets.

---

### `.planning/phases/32-hardening-regression-operations/32-VERIFICATION.md` (config, evidence artifact)

**Analog:** `.planning/phases/31-independent-publish-pipeline/31-VERIFICATION.md` (new file; D-13-D-16)
**Role in phase:** Primary HARD-01/HARD-02 evidence artifact. Must separate automated evidence from manual Meta handoff and include explicit FB Regression Gate.

**Frontmatter/report pattern** (`.planning/phases/31-independent-publish-pipeline/31-VERIFICATION.md:1-17`):
```markdown
---
phase: 31-independent-publish-pipeline
verified: 2026-11-25T00:00:00Z
status: passed
score: 5/5 must-haves verified
overrides_applied: 0
---

# Phase 31: Independent Publish Pipeline Verification Report

**Phase Goal:** Publicação Instagram ocorre de forma assíncrona, segura e independente do Facebook.
**Verified:** 2026-11-25T00:00:00Z
**Status:** passed
**Re-verification:** No — initial verification
```

**Evidence table pattern** (`.planning/phases/31-independent-publish-pipeline/31-VERIFICATION.md:20-27,73-84,93-103`):
```markdown
| # | Truth | Status | Evidence |
|---|-------|--------|----------|

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |

### Gaps Summary

No gaps found. ...
```

**What to copy/adapt for Phase 32 (per D-13-D-16):**
- Keep frontmatter and clear status, but include Phase 32 goal/IDs.
- Add **HARD-01 Scenario Matrix** with scenario → requirement/risk → automated tests/files → command → result → automated/handoff note.
- Add explicit **Facebook Regression Gate** block listing full-cycle FB flows covered, test files/test IDs, command, result, non-regression conclusion.
- Add **Manual Meta Handoff** section with `handoff/manual`, preconditions, responsible/environment needed, evidence required, and `Not executed in this session` where applicable. Never mark approved without real execution.
- Reference `docs/META-INTEGRATION-TESTING.md`; do not duplicate operational status there.

## Shared Patterns

### Async pytest + monkeypatch
**Source:** `backend/tests/test_facebook_publisher.py:8-38`, `backend/tests/test_instagram_publisher.py:98-126`, `backend/tests/test_social_publish_pipeline.py:29-77`
**Apply to:** All backend HARD-01 tests touched.
```python
@pytest.mark.asyncio
async def test_...(monkeypatch):
    monkeypatch.setattr(httpx, "AsyncClient", FakeAsyncClient)
    monkeypatch.setattr("app.services.social.facebook.get_settings", lambda: type("S", (), {"META_GRAPH_VERSION": "v21.0"})())
```

### SimpleNamespace fixtures for posts/settings/accounts
**Source:** `backend/tests/test_social_publish_pipeline.py:34-50,96-102,335-366`
**Apply to:** Pipeline/idempotency/retry/admin-adjacent unit tests where full ORM fixtures are unnecessary.
```python
post = SimpleNamespace(id=uuid.uuid4(), job_id=job_id, provider="facebook", status=SocialPostStatus.publishing, attempts=0, next_retry_at=None, ...)
settings = SimpleNamespace(SITE_PUBLIC_URL="https://site.exemplo/", SOCIAL_MAX_ATTEMPTS=5, social_retry_delays_list=[300, ...], SOCIAL_TOKEN_ENCRYPTION_KEY="k")
```

### Safe pt-BR / no-secrets assertions
**Source:** `backend/tests/test_instagram_publisher.py:84-86,204,232`, `backend/tests/test_admin_social_status_api.py:81-83`
**Apply to:** Publisher, pipeline, admin status/retry/log tests and docs/verification evidence.
```python
assert "access_token" not in (result.error_message or "").lower()
assert "secret" not in str(body).lower()
```

### Admin API test auth helper
**Source:** `backend/tests/test_admin_social_publish.py:13-20`, `backend/tests/test_admin_social_retry_api.py:12-19`, `backend/tests/test_admin_social_status_api.py:12-19`, `backend/tests/test_admin_instagram_social_posts.py:21-28`
**Apply to:** Admin endpoint tests in FB gate and IG HARD-01 gap coverage.
```python
VALID_CF_TOKEN = "token-de-teste"

async def _login(client, admin_password="test-password"):
    resp = await client.post("/api/v1/auth/login", json={"password": admin_password, "cf_token": VALID_CF_TOKEN})
    assert resp.status_code == 200
    return resp.json()["access_token"]
```

### Handoff/manual evidence, never fabricated
**Source:** `docs/META-INTEGRATION-TESTING.md:44-47,145-151`, `.planning/phases/31-independent-publish-pipeline/31-VERIFICATION.md:93-96`
**Apply to:** `docs/META-INTEGRATION-TESTING.md` and `32-VERIFICATION.md`.
```markdown
> Execução real depende de credenciais/app Meta e Página de teste. ... **não marcar como aprovado sem execução real**.
| Item | Status | Preconditions | Evidence Required | Executed |
|---|---|---|---|---|
| Live Meta smoke | handoff/manual | ... | ... | Not executed in this session |
```

## No Analog Found

| File | Role | Data Flow | Reason |
|---|---|---|---|
| — | — | — | All Phase 32 target files have close in-repo analogs; 32-VERIFICATION.md is new but follows 31-VERIFICATION.md format. |

## Metadata

**Analog search scope:** `backend/tests/*social*`, `backend/tests/*instagram*`, `backend/tests/*facebook*`, `docs/META-INTEGRATION-TESTING.md`, `backend/.env.example`, `.planning/phases/31-independent-publish-pipeline/31-VERIFICATION.md`
**Files scanned:** 14 key files read (targeted), 2 grep scans, 4 glob checks
**Pattern extraction date:** 2026-11-26
