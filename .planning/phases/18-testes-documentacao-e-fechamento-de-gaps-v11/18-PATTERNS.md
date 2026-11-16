# Phase 18: Testes, Documentação e Fechamento de Gaps v1.1 - Pattern Map

**Mapped:** 2026-11-16
**Files analyzed:** 28
**Analogs found:** 24 / 28

## File Classification

| New/Modified File | Role | Data Flow | Closest Analog | Match Quality |
|-------------------|------|-----------|----------------|---------------|
| `.planning/phases/11-verify-phases-7-8-reveal-admin-review-evidence/11-VERIFICATION.md` | verification artifact (markdown) | evidence consolidation (read/aggregate -> write) | `.planning/phases/07-contact-reveal-anti-spam-completeness/07-VERIFICATION.md` | exact |
| `.planning/phases/18-testes-documentacao-e-fechamento-de-gaps-v11/18-VERIFICATION.md` (implied) | verification artifact (markdown) | evidence/status reconciliation | `.planning/phases/17-publicacao-assincrona-retry-idempotencia-e-status/17-VERIFICATION.md` | exact |
| `.planning/phases/18-testes-documentacao-e-fechamento-de-gaps-v11/*EVIDENCE*/*handoff*` artifacts (discretionary) | evidence/checklist doc (markdown) | evidence capture + handoff | `.planning/phases/17-publicacao-assincrona-retry-idempotencia-e-status/17-VERIFICATION.md` (`human_verification`, gaps/evidence tables) | role-match |
| `.planning/phases/07-contact-reveal-anti-spam-completeness/07-VERIFICATION.md` | verification artifact (markdown, modify) | caveat/traceability reconciliation | `.planning/phases/17-publicacao-assincrona-retry-idempotencia-e-status/17-VERIFICATION.md` (re_verification/status framing) | role-match |
| `.planning/phases/08-admin-review-area-completeness/08-VERIFICATION.md` | verification artifact (markdown, modify) | caveat/traceability reconciliation | `.planning/phases/07-contact-reveal-anti-spam-completeness/07-VERIFICATION.md` | exact |
| `docs/DEPLOY.md` | ops runbook doc (markdown) | operational config/reference + handoff matrix | `docs/DEPLOY.md` (self; existing canonical structure) | exact |
| `docs/META-INTEGRATION.md` or `docs/META-APP-REVIEW.md` (candidate, TEST-04/DOC-01) | ops/manual runbook (markdown) | setup/checklist (request-response with external Meta ops) | `docs/DEPLOY.md` | role-match |
| `docs/TESTING.md` or `backend/TESTING-DB.md` (candidate, D-02) | ops/dev doc (markdown) | reproducible test DB workflow (migrations + command execution) | `docs/DEPLOY.md` ("Gate de fumaça"/command/checklist sections) | role-match |
| `backend/.env.example` | config template (env) | config documentation (key/value placeholders) | `backend/.env.example` (self) | exact |
| `frontend/.env.example` | config template (env) | config documentation (public/build/runtime vars) | `frontend/.env.example` (self) | exact |
| `scripts/verify-deploy.ps1` (if aligned) | ops script (PowerShell) | smoke-gate request-response checks | `scripts/verify-deploy.ps1` (self) | exact |
| `backend/scripts/setup-test-db.ps1` (candidate, D-02) | ops script (PowerShell) | DB bootstrap + migration execution | `scripts/verify-deploy.ps1` (param/Invoke/check pattern) | role-match |
| `backend/tests/test_facebook_publisher.py` | test (unit/integration-style, mocked HTTP) | request-response to mocked Graph API | `backend/tests/test_facebook_publisher.py` (self) | exact |
| `backend/tests/test_social_post_generation.py` | test (unit, LLM mocked) | transform/generation with mocked provider | `backend/tests/test_facebook_publisher.py` (mock/monkeypatch style) + `backend/tests/test_social_post_policy.py` (DB-independent unit style) | role-match |
| `backend/tests/test_social_retry_policy.py` | test (unit) | deterministic backoff/classification computation | `backend/tests/test_social_idempotency.py` (pure logic/state assertions) | role-match |
| `backend/tests/test_social_publish_pipeline.py` | test (unit/integration, DB-independent in current harness) | state machine/transitions + event logging | `backend/tests/test_social_idempotency.py` | exact |
| `backend/tests/test_social_idempotency.py` | test (unit, state/idempotency) | idempotent state transitions | `backend/tests/test_social_idempotency.py` (self) | exact |
| `backend/tests/test_social_worker_claim.py` | test (API/worker, mocked cycle) | request-response (cron endpoint) + idempotent cycle trigger | `backend/tests/test_social_worker_claim.py` (self) | exact |
| `backend/tests/test_meta_oauth_flow.py` | test (integration/service contract, offline) | OAuth redirect/callback request-response + state validation | `backend/tests/test_meta_oauth_flow.py` (self) | exact |
| `backend/tests/test_meta_oauth_security.py` | test (integration/security, offline) | auth/state/security checks | `backend/tests/test_meta_oauth_flow.py` | exact |
| `backend/tests/test_meta_oauth_validation.py` | test (integration/validation, offline) | input/config validation | `backend/tests/test_meta_oauth_flow.py` | exact |
| `backend/tests/test_integrations_api.py` | test (integration, ASGI) | request-response admin integrations API | `backend/tests/test_meta_oauth_flow.py` / `backend/tests/test_social_worker_claim.py` (client/headers patterns) | role-match |
| `backend/tests/test_admin_social_publish.py` | test (integration, DB-backed where schema ready) | approve dispatch + pipeline side-effects | `backend/tests/test_social_worker_claim.py` (endpoint/auth patterns) + `backend/tests/conftest.py` fixtures | role-match |
| `backend/tests/test_admin_social_status_api.py` | test (integration, DB-backed) | request-response status/list contracts | `backend/tests/test_social_worker_claim.py` | role-match |
| `backend/tests/test_admin_social_retry_api.py` | test (integration, DB-backed) | request-response retry/idempotency contract | `backend/tests/test_social_worker_claim.py` + `backend/tests/test_social_idempotency.py` | role-match |
| `backend/tests/test_admin_social_posts.py` | test (integration, DB-backed) | request-response list/status | `backend/tests/test_social_worker_claim.py` | role-match |
| `backend/tests/conftest.py` (possible extension, D-02) | test config/fixtures (pytest) | test environment/bootstrap, DB isolation, dependency overrides | `backend/tests/conftest.py` (self) | exact |
| `.planning/REQUIREMENTS.md` / `.planning/STATE.md` / phase VERIFICATION traceability files (reconciliation, implied) | planning/status artifacts (markdown) | status/traceability updates with evidence refs | `.planning/phases/17-publicacao-assincrona-retry-idempotencia-e-status/17-VERIFICATION.md` + `REQUIREMENTS.md` table conventions | role-match |

## Pattern Assignments

### `.planning/phases/11-verify-phases-7-8-reveal-admin-review-evidence/11-VERIFICATION.md` (verification artifact, evidence consolidation)

**Analog:** `.planning/phases/07-contact-reveal-anti-spam-completeness/07-VERIFICATION.md`

**Frontmatter/status contract** (lines 1-30):
```markdown
---
phase: 07-contact-reveal-anti-spam-completeness
verified: 2026-11-15T03:10:00Z
status: gaps_found
score: 2/3 requirements fully evidenced (SECR-12 split/deferred by design)
gaps:
  - truth: "DB-backed reveal endpoint evidence (test_reveal_api.py) can be re-run and recorded as green in this environment"
    status: failed
    reason: "Targeted DB-backed suite could not execute because the configured test database/migrations were not ready (`relation \"jobs\" does not exist` during test fixture setup). Offline/unit evidence for Turnstile and rate limiting passed."
    artifacts:
      - path: "backend/tests/test_reveal_api.py"
        issue: "10 setup errors in this environment: `sqlalchemy.exc.ProgrammingError ... relation \"jobs\" does not exist` while `tests/conftest.py` executes `DELETE FROM jobs`."
    missing:
      - "Run `cd backend; .\\.venv\\Scripts\\python.exe -m pytest tests/test_reveal_api.py -q` against a migrated TEST_DATABASE_URL/DATABASE_URL (jobs table present) and record passing results."
      - "Optional: perform live/browser smoke for reveal flow with real Turnstile widget/token in a configured environment (TURNSTILE_LIVE or manual UI check)."
human_verification:
  - test: "Execute reveal flow in browser against a running backend+frontend with Turnstile configured"
    expected: "Published job reveals contact only after valid Turnstile token; repeated attempts from same IP hit pt-BR 429 with Retry-After; invalid/expired token returns 403 with fail-closed copy"
    why_human: "Interactive widget/token lifecycle and end-to-end browser behavior are not proven by static inspection; DB-backed API suite was environment-blocked here."
requirements:
  - id: SECR-10
    status: verified_with_caveat
```

**Report structure / evidence tables** (lines 31-61, 86-94):
```markdown
# Phase 7: Contact Reveal & Anti-Spam Completeness Verification Report

**Phase Goal:** Um visitante revela o contato de uma vaga publicada passando por verificação anti-bot real, sem que o contato vaze antes disso; um scraper não consegue varrer contatos em massa.
**Verified:** 2026-11-15T03:10:00Z
**Status:** gaps_found
**Re-verification:** No — initial Phase 11 backfill verification

## Goal Achievement

### Observable Truths / Requirement Outcomes

| # | Truth / Outcome | Status | Evidence |
| --- | --- | --- | --- |

## Targeted Test Evidence (recorded)

| Command | Result | Notes |
| --- | --- | --- |

## Requirements Coverage

| Requirement | Status | Evidence / Notes |
| --- | --- | --- |
```

**Handoff/caveat phrasing** (lines 47, 92-93, 123): explicitly split ownership (`Phase 12 owns /admin/expire contract reconciliation`), record env-blocked evidence without claiming pass, and separate automated vs human verification.

**Secondary analog (recent re-verification style):** `.planning/phases/17-publicacao-assincrona-retry-idempotencia-e-status/17-VERIFICATION.md` lines 1-29, 141-170 show `re_verification` block, `human_needed` status, behavioral spot-checks table with `? SKIP (env not migrated)` and explicit "Gaps Summary"/human reasons.

---

### `docs/DEPLOY.md` and new ops/manual docs (ops runbook, DOC-01/AUD-05/TEST-04)

**Analog:** `docs/DEPLOY.md`

**State-alvo + non-secret/canonical-vs-legacy framing** (lines 1-21, 33-44):
```markdown
# Deploy — EmpregaNoix

Runbook de produção e **alvo contratual (state-alvo)**: frontend na **Vercel**, backend **FastAPI** no **Render**, banco **Neon (Postgres)** e **GitHub Actions** como cron de catch-up da expiração.

> **Nenhum segredo real entra neste arquivo ou em qualquer arquivo versionado.** Todos os valores sensíveis são configurados apenas em variáveis de ambiente (Render/Vercel/GitHub). Hosts legados/históricos aparecem apenas como evidência registrada no **Registro de verificação** e no mapeamento canônico↔legado — não substituem o alvo canônico.

---

## Alvo canônico (state-alvo)

- **Frontend (origem canônica):** `https://empreganoix.vercel.app`
- **Backend (API canônica):** `https://empreganoix.onrender.com`
- `CORS_ORIGINS=https://empreganoix.vercel.app` (exato, sem barra final, sem wildcard, sem legados)

## Mapeamento canônico ↔ legado/histórico

| Papel | Host canônico (state-alvo) | Host legado/histórico | Notas |
| --- | --- | --- | --- |
```

**Alignment matrix + handoff/rollback/checklist pattern** (lines 45-76, 200-233, 235-261): status vocabulary (`verificado em host legado` | `alinhado contratualmente ao canônico` | `pendente de execução operacional`), explicit command examples, rollback table, go-live checklist, and append-only "Registro de verificação" table with pending rows and notes. Preserve T-06-01 wording (`/admin/expire` somente `X-Cron-Secret`, fail-closed/idempotente).

---

### `backend/.env.example` and `frontend/.env.example` (config template, DOC-01)

**Analogs:** `backend/.env.example`, `frontend/.env.example`

**Backend env grouping + safe placeholders/comments** (lines 1-8, 9-20, 21-33, 34-50):
```dotenv
ENV=dev
DATABASE_URL=postgresql+asyncpg://USER:PASSWORD@ep-XXXX-pooler.REGION.aws.neon.tech/DBNAME?ssl=require
ADMIN_PASSWORD_HASH=
JWT_SECRET=REPLACE_WITH_64_CHAR_RANDOM_STRING
...
# --- Groq / Extração (Phase 2) ---
GROQ_API_KEY=
...
# --- Cloudflare Turnstile / Rate Limit (Phase 3) ---
TURNSTILE_SITE_KEY=
TURNSTILE_SECRET_KEY=
...
# --- Integração Social / Meta (Phase 14 - Fundação) ---
# ... nunca devem ser expostos ao frontend ou logs.
# ... sem versionar valores reais.
META_APP_ID=
META_APP_SECRET=
META_GRAPH_VERSION=v21.0
META_OAUTH_REDIRECT_URI=
SOCIAL_TOKEN_ENCRYPTION_KEY=
SOCIAL_WORKER_SECRET=
SOCIAL_MAX_ATTEMPTS=5
SOCIAL_RETRY_DELAYS=300,900,3600,10800,21600
SITE_PUBLIC_URL=
SOCIAL_POST_INCLUDE_CONTACT=false
```

**Frontend env public/runtime split + rebuild caveat** (lines 1-29):
```dotenv
# NUNCA comite `.env.local` nem valores reais de produção. Nenhum `NEXT_PUBLIC_*` pode conter segredos...
# `NEXT_PUBLIC_*` é embutida no build e exige rebuild/redeploy ao alterar.

# URL pública do backend FastAPI.
# Local (dev): http://localhost:8000
# Produção (state-alvo canônico): https://empreganoix.onrender.com
NEXT_PUBLIC_API_URL=http://localhost:8000

# URL do backend usada apenas no SSR (fetch server-side do board).
# Lida em RUNTIME no servidor (não é inlined no build) ...
BACKEND_API_URL=http://localhost:8000

# Site key pública do widget Cloudflare Turnstile (widget de produção).
NEXT_PUBLIC_TURNSTILE_SITE_KEY=
```

---

### `scripts/verify-deploy.ps1` (and optional `backend/scripts/setup-test-db.ps1`) (ops script, request-response/check execution)

**Analog:** `scripts/verify-deploy.ps1`

**Parameter/help + safe defaults pattern** (lines 1-61):
```powershell
#Requires -Version 5.1
<#
.SYNOPSIS
  Gate de fumaça pós-deploy (produção) do EmpregaNoix.
...
.EXAMPLE
  $env:CRON_SECRET = "<CRON_SECRET>"
  powershell -ExecutionPolicy Bypass -File scripts\verify-deploy.ps1 `
    -FrontendUrl https://empreganoix.vercel.app `
    -BackendUrl  https://empreganoix.onrender.com
#>
param(
    [Parameter(Mandatory = $true)]
    [string]$FrontendUrl,

    [Parameter(Mandatory = $true)]
    [string]$BackendUrl,

    # Segredo do cron ... Padrão: lê $env:CRON_SECRET da sessão.
    [string]$CronSecret = $env:CRON_SECRET,
    [switch]$AllowTestTurnstile
)
```

**HTTP helper + assertion/check output pattern** (lines 62-127, 133-176, 220-282):
```powershell
function Write-Pass { param([string]$Message); Write-Output "PASS - $Message" }
function Assert { param([bool]$Condition, [string]$Message); if (-not $Condition) { throw $Message } }

function Invoke-Http {
    param([Parameter(Mandatory = $true)][string]$Method, [Parameter(Mandatory = $true)][string]$Url, [hashtable]$Headers = @{})
    ...
    return [pscustomobject]@{ Status = $status; Headers = $headers; Body = $bodyText }
}
...
$health = Invoke-Http -Method GET -Url "$BackendUrl/api/v1/health"
Assert ($health.Status -eq 200) "Health retornou $($health.Status) ..."
Write-Pass "CORS preflight permitido ($allowOrigin)"
...
Write-Output "verify-deploy: all checks passed"
```

---

### Backend social unit tests (mocked Graph/LLM/policy, DB-independent) (test, unit/request-response/transform)

**Analog:** `backend/tests/test_facebook_publisher.py`

**Imports + monkeypatched HTTP client pattern** (lines 1-57):
```python
import httpx
import pytest

from app.services.social.facebook import FacebookPublisher
from app.services.social.types import PublishFailureCategory, SocialPostPayload


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

**Failure classification/assertion pattern (safe pt-BR messages, no real network)** (lines 60-116): mock transient/timeout responses via fakes and assert `result.ok/category/error_message` semantics (`transient`, `ambiguous`, "duplic/confirmar" guidance).

---

### Backend idempotency/pipeline/claim tests (test, state machine + concurrency/idempotency)

**Analog:** `backend/tests/test_social_idempotency.py`

**Lightweight fake session + `SimpleNamespace` state fixtures** (lines 1-35):
```python
import uuid
from datetime import datetime, timezone
from types import SimpleNamespace

import pytest

from app.models.social_post import SocialPostStatus
from app.services.social.publish_pipeline import process_claimed_post
from app.services.social.types import PublishFailureCategory, PublishResult


class FakeSession:
    async def get(self, model, ident):
        return None
    def add(self, obj):
        return None
    async def flush(self):
        return None
```

**Idempotent/no-auto-retry assertions on state transitions** (lines 37-121): assert noop when `published` or `external_post_id` present; on ambiguous publish result assert `failed_final`, `attempts == 1`, `next_retry_at is None`, and safe pt-BR "duplic/confirmar" error.

**Worker/cron endpoint claim/idempotency analog:** `backend/tests/test_social_worker_claim.py` (lines 12-63) uses `client` + `cron_secret_header`, patches `app.api.v1.admin.run_social_publish_cycle`, asserts 503/401/200 contracts and idempotent repeated trigger (`calls["n"]` increments per call while response remains `status="ok"`).

---

### Meta OAuth / integrations API tests (test, request-response, offline ASGI with overrides)

**Analog:** `backend/tests/test_meta_oauth_flow.py`

**DB-independent app/client/turnstile overrides inside test module** (lines 16-97):
```python
import pytest
from httpx import ASGITransport, AsyncClient

from app.db.session import get_session
from app.deps import get_turnstile_verifier
from app.main import create_app


class _DummySession:
    async def execute(self, *args, **kwargs): ...
    async def commit(self): return None


class _FakeTurnstileVerifier:
    async def verify(self, token: str, remoteip: str | None = None, **kwargs):
        from types import SimpleNamespace
        return SimpleNamespace(success=True, error_codes=[], action=kwargs.get("expected_action"))


@pytest.fixture
async def app(db_session):
    application = create_app()
    ...
    application.dependency_overrides[get_session] = _override_get_session
    application.dependency_overrides[get_turnstile_verifier] = _override_get_turnstile_verifier
    yield application
    application.dependency_overrides.clear()


@pytest.fixture
async def client(app):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as ac:
        yield ac
```

**State/redirect contract assertions (no real Meta network)** (lines 104-147, 188-270): validate signed state (`purpose`, `nonce`, `exp`, tamper/expiry rejection), dialog URL params (`scope`, `client_id`, `redirect_uri`, `state`), safe redirect outcomes (`result=error/cancelled/select_page&pending=`) without leaking tokens.

---

### `backend/tests/conftest.py` (test config/fixtures, D-02 foundation)

**Analog:** `backend/tests/conftest.py`

**Env resolution + deterministic settings before app imports** (lines 1-89):
```python
_BACKEND_DIR = Path(__file__).resolve().parents[1]
_FILE_ENV = dotenv_values(_BACKEND_DIR / ".env")

TEST_DATABASE_URL = (
    os.environ.get("TEST_DATABASE_URL")
    or _FILE_ENV.get("TEST_DATABASE_URL")
    or os.environ.get("DATABASE_URL")
    or _FILE_ENV.get("DATABASE_URL")
)
HAS_DB = bool(TEST_DATABASE_URL)
...
os.environ["DATABASE_URL"] = TEST_DATABASE_URL or ("postgresql+asyncpg://postgres@127.0.0.1:5432/nqu_placeholder")
os.environ["ADMIN_PASSWORD_HASH"] = ...
os.environ["JWT_SECRET"] = "test-secret-key-for-pytest-only-0123456789abcdef"
os.environ["TURNSTILE_SECRET_KEY"] = ""
os.environ["TURNSTILE_SITE_KEY"] = ""
...
get_settings.cache_clear()
```

**DB-independent selection, fakes/overrides, isolation and helpers** (lines 92-115, 118-264, 315-419): `pytest_collection_modifyitems` skips DB-dependent tests when `HAS_DB` is false except whitelisted DB-independent files; `FakeTurnstileVerifier` is fully offline; `db_session` uses transaction rollback and `DELETE FROM jobs`; `app/client` fixtures install dependency overrides and reset limiter; helper fixtures include `cron_secret_header`, `social_test_encryption_key`, seeded social posts/accounts.

## Shared Patterns

### Evidence-first, no-fabrication closure (D-01/D-04)
**Source:** `.planning/phases/07-contact-reveal-anti-spam-completeness/07-VERIFICATION.md:8-19,58-61,122-124`, `.planning/phases/17-publicacao-assincrona-retry-idempotencia-e-status/17-VERIFICATION.md:4-29,110-112,166-170`
**Apply to:** 11/18 verification artifacts, 07/08 reconciliation updates, REQUIREMENTS/STATE/ROADMAP traceability edits, TEST-04/DOC-01 handoffs.
```markdown
- Record executed commands/results with pass/fail/skip and explicit environment blockers (e.g. `relation "jobs" does not exist`).
- Separate "validated/verified" from "human_needed"/"partial + handoff rastreável" when runtime/infra/credentials are unavailable.
- Never claim live Meta/canonical-host execution without observed evidence.
```

### Offline/mocked external integrations in CI (TEST-01..03)
**Source:** `backend/tests/test_facebook_publisher.py:1-57,80-116`, `backend/tests/test_meta_oauth_flow.py:16-97,188-270`, `backend/tests/conftest.py:118-175,229-239`
**Apply to:** All social generation/OAuth/publisher/worker tests and any new TEST-01..03 coverage.
```python
# Monkeypatch httpx.AsyncClient / service dependencies; use ASGITransport + dependency_overrides.
# Fake verifiers/publishers return deterministic outcomes; never call real Groq/Graph/Turnstile.
assert result.ok is True
assert calls["url"] == "https://graph.facebook.com/v21.0/page-1/feed"
```

### DB-backed reproducibility and isolation (D-02)
**Source:** `backend/tests/conftest.py:41-71,92-115,184-214`, `docs/DEPLOY.md:235-261` (evidence registration discipline)
**Apply to:** DB test setup docs/scripts, any "suite green" evidence claims, 07/08/11/18 verification updates.
```python
TEST_DATABASE_URL = os.environ.get("TEST_DATABASE_URL") or _FILE_ENV.get("TEST_DATABASE_URL") or os.environ.get("DATABASE_URL") or _FILE_ENV.get("DATABASE_URL")
...
await session.execute(text("DELETE FROM jobs"))
...
await trans.rollback()
```
```powershell
# Proposed reproducible flow (document/script; do not commit secrets):
$env:TEST_DATABASE_URL="postgresql+asyncpg://USER:PASS@HOST:PORT/empreganoix_test?ssl=require"
$env:DATABASE_URL=$env:TEST_DATABASE_URL
.\.venv\Scripts\python.exe -m alembic upgrade head
.\.venv\Scripts\python.exe -m pytest -q
```

### Secret-safe operations and preserved contracts
**Source:** `backend/.env.example:34-50`, `frontend/.env.example:4-29`, `docs/DEPLOY.md:6,18-20,189-193,257-265`, `scripts/verify-deploy.ps1:220-265`
**Apply to:** DOC-01 env/docs/roteiro/checklists, evidence artifacts, any test fixtures/log assertions.
```text
- No real tokens/secrets/headers/payloads in repo or evidence; placeholders/generated test keys only.
- Preserve T-06-01: /admin/expire only X-Cron-Secret (fail-closed, idempotent), Bearer JWT not accepted.
- Preserve canonical-vs-legacy host mapping and NEXT_PUBLIC_* rebuild requirement.
```

### Idempotent worker/retry state handling
**Source:** `backend/tests/test_social_worker_claim.py:34-63`, `backend/tests/test_social_idempotency.py:37-121`, `backend/tests/test_facebook_publisher.py:99-116`
**Apply to:** TEST-03 extensions, pipeline/worker contract assertions, retry eligibility evidence.
```python
# Ambiguous publish/timeout => safe failure without auto-retry duplication.
assert post.attempts == 1
assert post.next_retry_at is None
# Worker endpoint returns idempotent summary per invocation; pipeline/claim guards prevent duplicates.
```

## No Analog Found

Files with no close match in the codebase (planner should use RESEARCH.md/CONTEXT.md patterns and existing conventions instead):

| File | Role | Data Flow | Reason |
|------|------|-----------|--------|
| `docs/META-INTEGRATION.md` (or equivalent Meta setup/App Review/Live + TEST-04 roteiro doc, exact name discretionary) | ops/manual runbook (new) | external Meta ops checklist (request-response/OAuth/publish procedures) | No existing Meta-specific operator manual/roteiro in `docs/`; closest is generic `docs/DEPLOY.md` structure only. |
| `backend/scripts/setup-test-db.ps1` or `docs/TESTING.md` (discretionary, D-02) | reproducible DB test bootstrap doc/script (new) | local DB provisioning + migration + pytest execution workflow | No existing repo-level test DB bootstrap script/guide found; `conftest.py` implies env contract but not an operator-facing reproducible setup artifact. |
| `.planning/phases/18-testes-documentacao-e-fechamento-de-gaps-v11` evidence/handoff bundle (exact filenames discretionary) | evidence matrix/checklist artifacts (new) | traceability aggregation + operational handoff | Phase 18-specific closure bundle not present yet; prior VERIFICATION files provide conventions but not this combined AUD-01..05 handoff layout. |

## Metadata

**Analog search scope:** `.planning/phases/07,08,11,17`, `.planning/phases/18-*`, `docs/`, `scripts/`, `backend/.env.example`, `frontend/.env.example`, `backend/tests/` (social/meta/admin/public/reveal/expiry/conftest), `backend/app/services/social/`, `backend/app/api/v1/`, `backend/alembic/`, `frontend/app/admin/`, `frontend/app/(public)/`, `frontend/lib/api.ts`
**Files scanned:** ~80 (targeted reads of 12 key analog files; broad inventory via glob/dir listing across phase artifacts, tests, docs, env/templates, scripts)
**Pattern extraction date:** 2026-11-16
