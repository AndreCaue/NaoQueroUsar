# Phase 22: qualidade, hardening e validação operacional - Pattern Map

**Mapped:** 2026-11-18
**Files analyzed:** 18 (4 new/modified artifacts + 14 code/test files in scope)
**Analogs found:** 17 / 18

## File Classification

| New/Modified File | Role | Data Flow | Closest Analog | Match Quality |
|-------------------|------|-----------|----------------|---------------|
| `.planning/phases/22-qualidade-hardening-e-valida-o-operacional/22-MVP-EXAMPLES.md` | QA artifact (versioned matrix) | document / evidence traceability | `.planning/phases/21-interface-de-chat-e-integracao-no-board/21-VERIFICATION.md` (evidence tables + gaps/human items) and `21-HUMAN-UAT.md` (scenario/result structure) | role-match (new matrix format per D-01/D-03) |
| `.planning/phases/22-qualidade-hardening-e-valida-o-operacional/22-MANUAL-UAT.md` | QA artifact (manual/UAT runbook) | document / guided verification steps | `.planning/phases/21-interface-de-chat-e-integracao-no-board/21-HUMAN-UAT.md` | exact |
| `backend/app/core/config.py` | config/settings (Pydantic BaseSettings) | config / env loading + validation | `backend/app/core/config.py` (existing `CHAT_SEARCH_*`, validators, properties) | exact (self/extension) |
| `backend/.env.example` | config template | config documentation | `backend/.env.example` (Chat-search público block) | exact (self/extension) |
| `backend/app/api/v1/public.py` | API route/controller (`/public`) | request-response (async HTTP), orchestration, deterministic DB read, degraded/disabled boundary, structured logging | `backend/app/api/v1/public.py` (`chat_search`, `_chat_degraded_contract`, rate-limit decorators, existing logging) | exact (self/extension) |
| `backend/app/schemas/chat.py` | Pydantic request/response schemas | validation / serialization | `backend/app/schemas/chat.py` (`ChatSearchRequest/Response/Results`) | exact (self/compatibility-preserving) |
| `backend/tests/test_chat_search_api.py` | integration/API tests (pytest-asyncio, DB-backed harness) | request-response (ASGI client) + mocked intent seam | `backend/tests/test_chat_search_api.py` | exact (self/extension) |
| `backend/tests/test_intent_schema.py` | unit tests (pure schema) | transform / validation | `backend/tests/test_intent_schema.py` | exact (self/extension) |
| `backend/tests/test_intent_mapper.py` | unit tests (pure deterministic mapping) | transform / deterministic | `backend/tests/test_intent_mapper.py` | exact (self/extension) |
| `backend/tests/test_intent_parser.py` | unit tests (orchestration + fake client) | transform / seam-mocked async | `backend/tests/test_intent_parser.py` | exact (self/extension) |
| `backend/tests/test_intent_client.py` | unit tests (client seam + fake Groq client) | transform / seam-mocked async | `backend/tests/test_intent_client.py` | exact (self/extension) |
| `backend/tests/conftest.py` | test harness/config/fixtures | test infrastructure (DB gating, monkeypatch, fakes) | `backend/tests/conftest.py` (`db_independent` whitelist, env pinning, fixtures, `fake_turnstile`, settings monkeypatch patterns elsewhere) | exact (self/extension, optional) |
| `frontend/lib/api.ts` | client HTTP/service + shared types | request-response (fetch), typed contracts | `frontend/lib/api.ts` (`chatSearch`, `ApiError`, `readError`, typed request/response interfaces) | exact (self/extension) |
| `frontend/components/board/chat/ChatWidget.tsx` | client UI component/state controller | event-driven + request-response (session-local) | `frontend/components/board/chat/ChatWidget.tsx` (state, request sequencing, error/degraded handling, apply/detail/manual-search flows) | exact (self/extension) |
| `frontend/components/board/chat/ChatLauncher.tsx` | presentational UI component | render (client) | `frontend/components/board/chat/ChatLauncher.tsx` | exact (likely unchanged; rendering gated by `ChatWidget`) |
| `frontend/lib/chatApply.ts` | pure UI logic utility | transform (deterministic) | `frontend/lib/chatApply.ts` | exact (self/extension only if needed) |
| `frontend/lib/chatApply.test.ts` | unit tests (Vitest node, pure logic) | transform / deterministic | `frontend/lib/chatApply.test.ts` | exact (self/extension only if needed) |
| `frontend/lib/*.test.ts` (if new helper added) | unit tests (Vitest node) | transform / deterministic | `frontend/lib/chatApply.test.ts` | role-match |

## Pattern Assignments

### `backend/app/core/config.py` (config/settings, config)

**Analog:** `backend/app/core/config.py`

**Imports / class pattern** (`backend/app/core/config.py:1-27`):
```python
import logging
import re
from functools import lru_cache
from typing import List
from urllib.parse import urlparse

from cryptography.fernet import Fernet
from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

logger = logging.getLogger(__name__)

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )
```

**Chat/env setting declarations (knob pattern to extend for kill-switch)** (`backend/app/core/config.py:56-60`):
```python
    # Chat-search público (Phase 20 — API-01..03, D-05/D-06/D-07)
    CHAT_SEARCH_RATE_LIMIT: str = "20/minute"
    CHAT_SEARCH_MAX_MESSAGE_CHARS: int = 400
    CHAT_SEARCH_INTENT_TIMEOUT_SECONDS: int = 12
```

**Boolean/env operational toggle precedent** (`backend/app/core/config.py:78-79`):
```python
    # Turns the in-process APScheduler clock off (LIFE-02/D-01). Useful for
    # multi-worker boxes and for hosts that spin down when idle...
    SCHEDULER_ENABLED: bool = True
```

**Validation/fail-closed & warning pattern (use as reference if adding constraints)** (`backend/app/core/config.py:157-181` excerpt):
```python
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
                if not self.ALLOW_TEST_TURNSTILE:
                    raise ValueError(
                        "chave de teste do Cloudflare (1x/2x/3x) não é permitida fora de dev (D-12)"
                    )
                logger.warning(
                    "ALLOW_TEST_TURNSTILE=true: ENV=%s está usando uma chave de "
                    "TESTE do Cloudflare Turnstile...",
                    self.ENV,
                )
        return self
```

**Accessor pattern** (`backend/app/core/config.py:251-253`):
```python
@lru_cache
def get_settings() -> Settings:
    return Settings()
```

**Phase 22 guidance:** add a single env-driven toggle (e.g. `CHAT_SEARCH_ENABLED: bool = True`) near chat-search settings; document in `.env.example`; keep validation minimal/explicit and avoid coupling to board/public jobs config.

---

### `backend/.env.example` (config template, config)

**Analog:** `backend/.env.example`

**Chat-search section to extend for kill-switch** (`backend/.env.example:52-58`):
```dotenv
# --- Chat-search público (Phase 20 / API-01..03) ---
# Rate limit dedicado por IP/rota para o chat-search público.
CHAT_SEARCH_RATE_LIMIT=20/minute
# Limite curto de caracteres da mensagem para reduzir abuso/custo.
CHAT_SEARCH_MAX_MESSAGE_CHARS=400
# Timeout curto da extração de intenção no chat, com fallback controlado (desacoplado do GROQ_TIMEOUT_SECONDS admin).
CHAT_SEARCH_INTENT_TIMEOUT_SECONDS=12
```

**Cron/operational comment style (reference for operational toggle docs)** (`backend/.env.example:60-67`):
```dotenv
# --- Cron / operação agendada (expiração e worker social) ---
# CRON_SECRET protege endpoints operacionais acionados por cron...
# Use o MESMO segredo no executor do cron (Render/GitHub Actions). Não versionar valor real.
CRON_SECRET=
# Scheduler in-process (APScheduler) para expiração; pode ser desativado se depender apenas de cron externo.
SCHEDULER_ENABLED=true
```

**Phase 22 guidance:** add the kill-switch env (and any status-signal knob if introduced) with pt-BR/operational comment explaining safe disable without affecting manual board search; never include secrets.

---

### `backend/app/api/v1/public.py` (route/controller, request-response + degraded boundary + logging)

**Analog:** `backend/app/api/v1/public.py`

**Imports / router / module logger** (`backend/app/api/v1/public.py:1-34`):
```python
import asyncio
import logging
import uuid
from copy import deepcopy

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.client_ip import UNKNOWN_IP, resolve_client_ip
from app.core.config import get_settings
from app.core.ratelimit import chat_search_limit, limiter, reveal_limit
from app.crud import get_published, list_published
from app.schemas.chat import ChatSearchRequest, ChatSearchResponse, ChatSearchResults
from app.schemas.job import ContactRevealResponse, JobListResponse, JobPublic, ReportRequest, RevealRequest
from app.services.cities import resolve_city, resolve_sort
from app.services.intent.mapper import build_empty_intent
from app.services.intent.parser import extract_and_map_intent
from app.services.intent.schema import IntentContract

router = APIRouter(prefix="/public", tags=["public"])
logger = logging.getLogger(__name__)
```

**Safe pt-BR guidance/constants and approximation signaling** (`backend/app/api/v1/public.py:41-60`):
```python
_CHAT_GUIDANCE_LLM = (
    "Não foi possível interpretar sua busca agora. "
    "Tente usar palavras-chave na busca manual (ex.: cargo, empresa ou cidade)."
)
_CHAT_GUIDANCE_NO_PARAMS = (
    "Não consegui identificar filtros na sua mensagem. "
    "Use palavras-chave na busca manual ou informe cargo/cidade/ordenação."
)
_CHAT_GUIDANCE_APPROX = (
    "Filtros como salário/modalidade/contrato/senioridade não possuem filtro estruturado garantido; "
    "quando possível foi usada apenas aproximação textual. "
    "Cidades fora da lista suportada (São Paulo, Rio de Janeiro, Belo Horizonte, Remoto) "
    "não são inferidas automaticamente."
)
_APPROX_LIMITATION_CODES = {
    "unsupported_structured_filter",
    "textual_approximation_in_q",
    "non_native_fields_limited",
    "not_in_whitelist",
}
```

**Degraded contract builder (core pattern to mirror for `chat_disabled`)** (`backend/app/api/v1/public.py:70-103`):
```python
def _chat_degraded_contract(
    message: str | None, reason_code: str, guidance: str, limitation: str | None = None
) -> IntentContract:
    """Build a safe degraded interpretation contract with no automatic results."""
    contract = build_empty_intent(message, reason_code="no_extractable_params").model_copy(deep=True)
    contract.applied_params.q = None
    contract.applied_params.city = None
    contract.applied_params.sort = None

    limitations: list[str] = list(contract.limitations or [])
    if limitation:
        limitations.append(limitation)
    if reason_code == "llm_unavailable":
        limitations.append("llm_unavailable")
    elif reason_code == "timeout":
        limitations.append("llm_timeout")
    elif reason_code == "no_extractable_params":
        limitations.append("no_extractable_params")
    contract.limitations = list(dict.fromkeys(limitations))

    contract.meta = {
        **(contract.meta or {}),
        "degraded": True,
        "degradation_reason": reason_code,
        "guidance": guidance,
    }
    for fs in contract.field_statuses:
        if getattr(fs.status, "value", fs.status) in {"aplicado", "aproximado"}:
            fs.status = "ignorado"
            fs.applied = None
        if reason_code in {"llm_unavailable", "timeout"}:
            fs.reason_code = reason_code
    return contract
```

**Deterministic public list pattern (must remain independent/unaffected)** (`backend/app/api/v1/public.py:147-183` excerpt):
```python
@router.get("/jobs", response_model=JobListResponse)
async def list_public_jobs(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=50),
    q: str | None = Query(None, max_length=80),
    city: str | None = Query(None, max_length=40),
    sort: str = Query("recentes", max_length=20),
    session: AsyncSession = Depends(get_session),
) -> JobListResponse:
    term = q.strip() if q else None
    if not term:
        term = None
    items, total = await list_published(
        session, page=page, limit=limit, q=term, city=resolve_city(city), sort=resolve_sort(sort),
    )
    return JobListResponse(
        items=[JobPublic.model_validate(job) for job in items],
        page=page, limit=limit, total=total,
    )
```

**Chat endpoint orchestration / degraded fallback / deterministic equivalence (kill-switch + logging insertion point)** (`backend/app/api/v1/public.py:258-333`):
```python
@router.post("/chat-search", response_model=ChatSearchResponse)
@limiter.limit(chat_search_limit)
async def chat_search(
    request: Request,
    payload: ChatSearchRequest,
    session: AsyncSession = Depends(get_session),
) -> ChatSearchResponse:
    """Busca pública por linguagem natural com interpretação transparente (API-01..03)."""
    settings = get_settings()
    chat_timeout = getattr(settings, "CHAT_SEARCH_INTENT_TIMEOUT_SECONDS", 12)

    if not payload.message or not payload.message.strip():
        raise HTTPException(status_code=400, detail="Mensagem inválida para busca por chat.")

    try:
        try:
            contract = await extract_and_map_intent(
                payload.message, settings, timeout_seconds=chat_timeout
            )
        except Exception as exc:  # noqa: BLE001 - fallback controlado (D-08/D-09)
            logger.warning("chat_search_intent_failed", extra={"reason": type(exc).__name__})
            is_timeout = isinstance(exc, (asyncio.TimeoutError, TimeoutError)) or "timeout" in str(exc).lower()
            reason_code = "timeout" if is_timeout else "llm_unavailable"
            degraded = _chat_degraded_contract(payload.message, reason_code, _CHAT_GUIDANCE_LLM)
            return ChatSearchResponse(
                interpretation=degraded,
                results=ChatSearchResults(items=[], page=payload.page, limit=payload.limit, total=0),
            )

        if contract is None or _is_effectively_no_params(contract):
            degraded = _chat_degraded_contract(
                payload.message, "no_extractable_params", _CHAT_GUIDANCE_NO_PARAMS,
                limitation="no_extractable_params",
            )
            return ChatSearchResponse(
                interpretation=degraded,
                results=ChatSearchResults(items=[], page=payload.page, limit=payload.limit, total=0),
            )

        contract = _apply_approx_guidance(contract)
        applied = contract.applied_params
        items, total = await list_published(
            session, page=payload.page, limit=payload.limit,
            q=applied.q, city=applied.city, sort=(applied.sort or "recentes"),
        )
        return ChatSearchResponse(
            interpretation=contract,
            results=ChatSearchResults(
                items=[JobPublic.model_validate(job) for job in items],
                page=payload.page, limit=payload.limit, total=total,
            ),
        )
    except HTTPException:
        raise
    except Exception:
        logger.exception("chat_search_unexpected_error")
        raise HTTPException(
            status_code=500, detail="Erro interno ao processar a busca por chat."
        )
```

**Existing logging style (structured `extra`/warning; avoid PII)** (`backend/app/api/v1/public.py:278`, `360-365` excerpts):
```python
logger.warning("chat_search_intent_failed", extra={"reason": type(exc).__name__})
# ...
logger.info(
    "job_report job_id=%s reason=%s ip=%s",
    str(job_id), _log_safe(reason), resolve_client_ip(request),
)
```

**Phase 22 guidance (per D-06/D-07):** short-circuit disabled state before LLM/DB work with controlled 200 + safe pt-BR guidance and a stable reason (e.g. `chat_disabled`) and empty `JobPublic` results; emit one structured per-request event (e.g. `logger.info("chat_search", extra={...})`) with `outcome/reason/latency_ms/results_count/total/page/limit` only — never `payload.message`, extracted text, contacts, or exception internals. If adding a status signal endpoint, mirror existing `@router.get("/...")` public patterns (no auth, simple response model/dict) and keep board routes independent.

---

### `backend/app/schemas/chat.py` (schemas, validation/serialization)

**Analog:** `backend/app/schemas/chat.py`

**Request validation (cap from settings) and response envelope** (`backend/app/schemas/chat.py:12-52`):
```python
def _max_message_chars() -> int:
    """Return configured chat message max length with a safe fallback."""
    try:
        return int(get_settings().CHAT_SEARCH_MAX_MESSAGE_CHARS)
    except Exception:
        return 400

class ChatSearchRequest(BaseModel):
    """Entrada pública não confiável para busca por linguagem natural."""
    message: str = Field(min_length=1)
    page: int = Field(default=1, ge=1)
    limit: int = Field(default=20, ge=1, le=50)

    @field_validator("message")
    @classmethod
    def _validate_message(cls, value: str) -> str:
        stripped = value.strip()
        if not stripped:
            raise ValueError("Mensagem é obrigatória")
        max_chars = _max_message_chars()
        if len(stripped) > max_chars:
            raise ValueError("Mensagem excede o tamanho máximo permitido")
        return stripped

class ChatSearchResults(BaseModel):
    """Resultados pagináveis determinísticos, sem contato."""
    items: list[JobPublic]
    page: int
    limit: int
    total: int

class ChatSearchResponse(BaseModel):
    """Envelope server-authoritative: interpretação + resultados."""
    interpretation: IntentContract
    results: ChatSearchResults
```

**Phase 22 guidance:** preserve compatibility (`interpretation + results`, `JobPublic` items/no contacts, `meta.degraded/reason/guidance` semantics). Avoid schema churn unless strictly required for status signaling.

---

### `backend/tests/test_chat_search_api.py` (integration/API tests, request-response, DB-backed + mocked seam)

**Analog:** `backend/tests/test_chat_search_api.py`

**Imports and fixtures/helpers** (`backend/tests/test_chat_search_api.py:1-67`):
```python
"""Contract, resilience and safety tests for POST /api/v1/public/chat-search (API-01..03).
LLM/intent extraction is always mocked (no network). DB-backed assertions rely on
the shared test fixtures (real Postgres test DB when configured).
"""
from datetime import datetime, timezone
from sqlalchemy import text

from app.models.job import Job, JobStatus
from app.services.intent.mapper import build_empty_intent
from app.services.intent.schema import (
    AppliedParams, FieldAssessment, FieldStatus, IntentContract, UnderstoodIntent,
)

SAO_PAULO = "São Paulo"

def _job(**overrides) -> Job:
    defaults = {"title": "Vaga de Teste", "city": "Remoto", "contact_phone": "+55 11 90000-0200", "status": JobStatus.published}
    defaults.update(overrides)
    return Job(**defaults)

async def _insert(db_session, **overrides) -> Job:
    job = _job(**overrides)
    db_session.add(job)
    await db_session.flush()
    return job

def _contract(*, q=None, city=None, sort=None, field_statuses=None, limitations=None, meta=None) -> IntentContract:
    return IntentContract(
        understood=UnderstoodIntent(q=q, city=city, sort=sort),
        field_statuses=field_statuses or [],
        applied_params=AppliedParams(q=q, city=city, sort=sort),
        limitations=list(limitations or []),
        meta=dict(meta or {}),
    )

def _assert_no_contacts(items: list[dict]) -> None:
    for item in items:
        assert "contact_email" not in item
        assert "contact_phone" not in item
```

**Core mocked-seam + equivalence/privacy assertion pattern** (`backend/tests/test_chat_search_api.py:69-116` excerpt):
```python
async def test_chat_search_equivalent_to_public_jobs_and_hides_contacts(db_session, client, monkeypatch):
    await _insert(db_session, title="Analista de Dados", company="Empresa X", city=SAO_PAULO,
                  contact_email="segredo@example.com", contact_phone="+55 11 98888-0001")
    interpretation = _contract(q="analista", city=SAO_PAULO, sort="recentes")

    async def fake_extract(*args, **kwargs):
        return interpretation

    monkeypatch.setattr("app.api.v1.public.extract_and_map_intent", fake_extract)

    chat = await client.post("/api/v1/public/chat-search",
                             json={"message": "vaga analista em sao paulo", "page": 1, "limit": 20})
    assert chat.status_code == 200
    body = chat.json()

    jobs = await client.get("/api/v1/public/jobs",
                            params={"q": "analista", "city": "sao-paulo", "sort": "recentes", "page": 1, "limit": 20})
    assert jobs.status_code == 200
    assert [i["id"] for i in body["results"]["items"]] == [i["id"] for i in jobs.json()["items"]]
    _assert_no_contacts(body["results"]["items"])
```

**Safe pt-BR text assertion helper** (`backend/tests/test_chat_search_api.py:172-178`):
```python
def _assert_safe_ptbr_text(value: str) -> None:
    assert isinstance(value, str) and value.strip()
    lowered = value.lower()
    assert "traceback" not in lowered
    assert "exception" not in lowered
    assert "groq" not in lowered
```

**Rate-limit test with settings monkeypatch + header/body assertions** (`backend/tests/test_chat_search_api.py:199-216` excerpt):
```python
async def test_chat_search_rate_limit_returns_429_with_retry_after(client, monkeypatch):
    from app.core.config import get_settings
    settings = get_settings()
    monkeypatch.setattr(settings, "CHAT_SEARCH_RATE_LIMIT", "1/minute")

    async def fake_extract(*args, **kwargs):
        return _contract(q="vaga", city=None, sort="recentes")

    monkeypatch.setattr("app.api.v1.public.extract_and_map_intent", fake_extract)
    first = await client.post("/api/v1/public/chat-search", json={"message": "vaga remota"})
    assert first.status_code == 200
    second = await client.post("/api/v1/public/chat-search", json={"message": "outra vaga"})
    assert second.status_code == 429
    assert second.headers.get("Retry-After")
    _assert_safe_ptbr_text(second.json().get("detail"))
```

**Degraded/timeout/no-params contract assertions** (`backend/tests/test_chat_search_api.py:219-267` excerpts):
```python
# llm failure -> degraded 200, empty results, applied_params null, meta.degraded/reason/guidance
assert body["results"]["items"] == []
assert body["interpretation"]["applied_params"] == {"q": None, "city": None, "sort": None}
assert body["interpretation"]["meta"]["degraded"] is True
assert body["interpretation"]["meta"]["degradation_reason"] in {"llm_unavailable", "timeout"}
_assert_safe_ptbr_text(body["interpretation"]["meta"]["guidance"])
# timeout reason specific
assert body["interpretation"]["meta"]["degradation_reason"] == "timeout"
# no_extractable_params
assert body["interpretation"]["meta"]["degradation_reason"] == "no_extractable_params"
```

**Phase 22 guidance:** extend (don’t duplicate) with kill-switch/disabled cases (controlled 200, no LLM call, no internals, empty results, guidance pt-BR, stable reason like `chat_disabled`), structured logging assertions via `caplog` (`chat_search` event fields present; no `message`/PII/contacts), and MVP scenario gaps as deterministic mocked-contract cases. Keep DB-backed assumptions explicit (harness-gated).

---

### `backend/tests/test_intent_mapper.py` (unit, deterministic transform)

**Analog:** `backend/tests/test_intent_mapper.py`

**Pure contract assertions and helper** (`backend/tests/test_intent_mapper.py:1-18`, `20-46` excerpts):
```python
from app.services.intent import IntentLLMOutput, IntentSalary, map_intent, build_empty_intent
from app.services.intent.schema import IntentContractType, IntentMode, IntentSeniority

def _field(contract, name: str):
    for fs in contract.field_statuses:
        if fs.field == name:
            return fs
    raise AssertionError(f"missing field status: {name}")

def test_build_empty_intent_returns_valid_contract_with_clear_statuses() -> None:
    contract = build_empty_intent("")
    assert contract.applied_params.q is None
    assert "no_extractable_params" in contract.limitations
```

**Whitelist / not-in-whitelist / explicit-sort / approximation patterns (directly relevant to QA-01 MVP gaps)** (`backend/tests/test_intent_mapper.py:49-117` excerpts):
```python
c4 = map_intent(IntentLLMOutput.model_validate({"city": "Campinas"}))
assert c4.applied_params.city is None
assert _field(c4, "city").status == "ignorado"
assert _field(c4, "city").reason_code == "not_in_whitelist"

s1 = map_intent(IntentLLMOutput.model_validate({"sort": "antigas", "q": "vagas"}), raw_text="vagas mais antigas")
assert s1.applied_params.sort == "antigas"
s3 = map_intent(IntentLLMOutput.model_validate({"q": "dev"}), raw_text="quero vagas mais recentes e mais antigas")
assert s3.applied_params.sort is None
assert _field(s3, "sort").reason_code == "conflict_resolved"

# non-native fields: textual approximation in q / salary ignored as structured filter
assert fs_seniority.status == "aproximado"
assert fs_seniority.reason_code == "textual_approximation_in_q"
assert fs_salary.status == "ignorado"
assert fs_salary.reason_code == "unsupported_structured_filter"
```

**Phase 22 guidance:** add deterministic MVP cases (SP whitelist/sort explicit, Remoto+React+CLT approximation, Campinas out-of-whitelist, salary non-native, “parecidas” as textual seed in `q` only, estágio marketing digital SP) asserting `applied_params`, `field_statuses`, `limitations/meta` without inventing semantic/link/ID behavior.

---

### `backend/tests/test_intent_parser.py` (unit, fake client seam)

**Analog:** `backend/tests/test_intent_parser.py`

**Fake client/script and settings pattern** (`backend/tests/test_intent_parser.py:1-69` excerpts):
```python
import pytest
from types import SimpleNamespace
from app.services.intent.schema import IntentContract, IntentLLMOutput

class _Settings:
    GROQ_API_KEY = "test-key"
    GROQ_MODEL = "model-a"
    GROQ_MODEL_FALLBACK = "model-b"
    GROQ_TIMEOUT_SECONDS = 12

class _FakeCompletions:
    def __init__(self, script):
        self.script = list(script)
        self.calls = []
    async def create(self, **kwargs):
        self.calls.append(kwargs)
        item = self.script.pop(0)
        if isinstance(item, Exception): raise item
        if callable(item): return item(kwargs)
        return item

class FakeGroqClient:
    def __init__(self, script):
        self.chat = SimpleNamespace(completions=_FakeCompletions(script))

class RaisingClient:
    class _C:
        async def create(self, **kwargs): raise RuntimeError("boom")
    chat = SimpleNamespace(completions=_C())

def _response(content: str, finish_reason: str = "stop"):
    return SimpleNamespace(choices=[SimpleNamespace(finish_reason=finish_reason, message=SimpleNamespace(content=content))])
```

**No-LLM-on-empty, safe mapping, and error propagation** (`backend/tests/test_intent_parser.py:73-163` excerpts):
```python
@pytest.mark.asyncio
async def test_extract_and_map_intent_empty_input_returns_safe_contract_without_llm():
    from app.services.intent.parser import extract_and_map_intent
    # client.create raises AssertionError if called
    contract = await extract_and_map_intent("", _Settings(), client=NoCallClient())
    assert contract.applied_params.q is None and contract.applied_params.city is None and contract.applied_params.sort is None

@pytest.mark.asyncio
async def test_extract_and_map_intent_client_failure_propagates_for_api_degradation():
    from app.services.intent.client import IntentExtractionError
    from app.services.intent.parser import extract_and_map_intent
    with pytest.raises(IntentExtractionError):
        await extract_and_map_intent("dev backend", _Settings(), client=RaisingClient())
```

---

### `backend/tests/test_intent_client.py` (unit, fake client seam)

**Analog:** `backend/tests/test_intent_client.py`

**Fake Groq client + response helper + call assertions** (`backend/tests/test_intent_client.py:18-58`, `123-141` excerpts):
```python
class _FakeCompletions:
    def __init__(self, script): self.script = list(script); self.calls = []
    async def create(self, **kwargs):
        self.calls.append(kwargs); item = self.script.pop(0)
        if isinstance(item, Exception): raise item
        if callable(item): return item(kwargs)
        return item

class FakeGroqClient:
    def __init__(self, script): self.chat = SimpleNamespace(completions=_FakeCompletions(script))
    @property
    def calls(self): return self.chat.completions.calls

def _response(content: str, finish_reason: str = "stop"):
    return SimpleNamespace(choices=[SimpleNamespace(finish_reason=finish_reason, message=SimpleNamespace(content=content))])

# call assertions
assert call["response_format"]["json_schema"]["strict"] is True
assert call["temperature"] == 0
assert call["timeout"] == 12
```

---

### `backend/tests/test_intent_schema.py` (unit, Pydantic contract validation)

**Analog:** `backend/tests/test_intent_schema.py`

**Strict schema/extra-forbid and contract shape assertions** (`backend/tests/test_intent_schema.py:23-104`, `120-136` excerpts):
```python
def test_intent_llm_output_empty_object_has_null_defaults() -> None:
    candidate = IntentLLMOutput.model_validate({})
    assert candidate.q is None and candidate.city is None and candidate.salary is None

def test_intent_llm_output_rejects_extra_keys() -> None:
    with pytest.raises(ValidationError):
        IntentLLMOutput.model_validate({"q": "vaga", "hacker_field": "x"})

# FieldStatus exact pt-BR values
assert {"aplicado", "ignorado", "aproximado"}.issubset(status_values)
```

---

### `backend/tests/conftest.py` (test harness/fixtures, infrastructure)

**Analog:** `backend/tests/conftest.py`

**DB-independent whitelist and skip logic (optional Phase 22 extension point)** (`backend/tests/conftest.py:93-114`):
```python
def pytest_collection_modifyitems(config, items):
    """Skip DB-dependent tests when no test DB is configured.
    Pure unit tests ... must remain runnable without a database.
    """
    if not HAS_DB:
        db_independent = {
            "test_social_post_generation.py",
            "test_social_post_policy.py",
            "test_facebook_publisher.py",
            "test_social_retry_policy.py",
            "test_social_idempotency.py",
            "test_social_publish_pipeline.py",
            "test_social_publisher.py",
        }
        for item in items:
            path = str(getattr(item, "fspath", "")).replace("\\", "/")
            if path.rsplit("/", 1)[-1] in db_independent:
                continue
            item.add_marker(pytest.mark.skip(reason="TEST_DATABASE_URL/DATABASE_URL not set"))
```

**Deterministic env pinning before app imports** (`backend/tests/conftest.py:58-73` excerpts):
```python
os.environ["DATABASE_URL"] = TEST_DATABASE_URL or ("postgresql+asyncpg://postgres@127.0.0.1:5432/nqu_placeholder")
os.environ["ADMIN_PASSWORD_HASH"] = bcrypt.hashpw(TEST_ADMIN_PASSWORD.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
os.environ["JWT_SECRET"] = "test-secret-key-for-pytest-only-0123456789abcdef"
# ... later
get_settings.cache_clear()
```

**Dependency override / fake seam fixture pattern** (`backend/tests/conftest.py:221-257` excerpts):
```python
@pytest.fixture
async def app(db_session):
    application = create_app()

    async def _override_get_session():
        yield db_session

    async def _override_get_turnstile_verifier():
        return fake

    fake = FakeTurnstileVerifier()
    application.dependency_overrides[get_session] = _override_get_session
    application.dependency_overrides[get_turnstile_verifier] = _override_get_turnstile_verifier
    application.state.fake_turnstile = fake
    yield application
    application.dependency_overrides.clear()
```

**Rate limiter reset (global state isolation)** (`backend/tests/conftest.py:263-267`):
```python
@pytest.fixture(autouse=True)
async def reset_rate_limiter():
    """The limiter store is global — never let a bucket leak across tests."""
    limiter.reset()
    yield
    limiter.reset()
```

**Phase 22 guidance:** if pure intent unit tests are confirmed fixture-free, consider adding them to `db_independent` for better QA-02 executability; never claim DB-backed suite execution without environment.

---

### `frontend/lib/api.ts` (client/service + types, request-response)

**Analog:** `frontend/lib/api.ts`

**API base / ApiError / error parsing** (`frontend/lib/api.ts:111-164` excerpts):
```ts
function resolveApiBase(): string {
  const fromEnv = process.env.NEXT_PUBLIC_API_URL?.trim();
  if (fromEnv) return fromEnv;
  if (process.env.NODE_ENV === "production") {
    throw new Error("NEXT_PUBLIC_API_URL is not set...");
  }
  return "http://localhost:8000";
}

const API = resolveApiBase();

export class ApiError extends Error {
  readonly status: number;
  constructor(message: string, status: number) {
    super(message);
    this.name = "ApiError";
    this.status = status;
  }
}

async function readError(res: Response): Promise<string> { /* reads detail string/array, fallback `Erro ${res.status}` */ }
```

**Chat types and contract (extend carefully for status/disabled signaling)** (`frontend/lib/api.ts:762-809`):
```ts
export type ChatFieldStatus = "aplicado" | "ignorado" | "aproximado";

export interface ChatAppliedParams {
  q: string | null;
  city: string | null;
  sort: "recentes" | "antigas" | null;
}

export interface ChatInterpretation {
  understood: Record<string, unknown>;
  field_statuses: ChatFieldAssessment[];
  applied_params: ChatAppliedParams;
  limitations: string[];
  meta: Record<string, unknown> & {
    degraded?: boolean;
    degradation_reason?: string;
    guidance?: string;
  };
}

export interface ChatSearchResponse {
  interpretation: ChatInterpretation;
  results: ChatSearchResults;
}
```

**chatSearch fetch/error/timeout pattern** (`frontend/lib/api.ts:811-839`):
```ts
export async function chatSearch(payload: ChatSearchRequest): Promise<ChatSearchResponse> {
  let res: Response;
  try {
    res = await fetch(`${API}/api/v1/public/chat-search`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
      signal: AbortSignal.timeout(15_000),
    });
  } catch (error) {
    const timedOut = error instanceof Error && (error.name === "TimeoutError" || error.name === "AbortError");
    throw new ApiError(
      timedOut
        ? "A requisição demorou demais. Verifique sua conexão e tente novamente."
        : "Não foi possível buscar agora. Verifique sua conexão e tente novamente.",
      0,
    );
  }
  if (!res.ok) {
    throw new ApiError(await readError(res), res.status);
  }
  return (await res.json()) as ChatSearchResponse;
}
```

**Phase 22 guidance:** add a lightweight status-signal consumer if used (e.g. GET helper returning enabled flag) consistent with `fetch`/`ApiError`/timeout-safe patterns; handle disabled reason in responses without blocking board behavior. Keep types aligned with backend `meta.degradation_reason` (e.g. `chat_disabled`) and never expose internals.

---

### `frontend/components/board/chat/ChatWidget.tsx` (client component, event-driven/request-response state)

**Analog:** `frontend/components/board/chat/ChatWidget.tsx`

**Imports and session-local state/request sequencing** (`frontend/components/board/chat/ChatWidget.tsx:1-65` excerpts):
```tsx
"use client";
import { useMemo, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import { chatSearch, ApiError } from "@/lib/api";
import type { ChatSearchResponse, JobPublic } from "@/lib/api";
import { appliedParamsToBoardFilters, canApplyChatToBoard } from "@/lib/chatApply";
import { buildBoardHref } from "@/lib/filters";

export function ChatWidget() {
  const router = useRouter();
  const [isOpen, setIsOpen] = useState(false);
  const [draft, setDraft] = useState("");
  const [turns, setTurns] = useState<ChatTurn[]>([]);
  const [isSending, setIsSending] = useState(false);
  // ...
  const requestSeq = useRef(0);
  const activeRequestRef = useRef(0);
```

**Send flow, error handling, degraded/response application** (`frontend/components/board/chat/ChatWidget.tsx:75-125` excerpts):
```tsx
const runSend = async (message: string) => {
  const trimmed = message.trim();
  if (!trimmed || isSending) return;
  const seq = ++requestSeq.current;
  activeRequestRef.current = seq;
  setSendError(null);
  setIsSending(true);
  setIsOpen(true);
  // ...
  try {
    const response = await chatSearch({ message: trimmed, page: 1, limit: 20 });
    if (activeRequestRef.current !== seq) return;
    setLastResponse(response);
    setItems(response.results.items ?? []);
    setTotal(response.results.total ?? 0);
    setTurns((prev) => prev.map((t) => t.id === turnId ? { ...t, status: "done", response } : t));
    setDraft("");
  } catch (err) {
    if (activeRequestRef.current !== seq) return;
    const messageErr = err instanceof ApiError && err.message ? err.message : "Não foi possível buscar agora.";
    setSendError(messageErr || "Não foi possível buscar agora.");
    setTurns((prev) => prev.map((t) => t.id === turnId ? { ...t, status: "error", error: messageErr } : t));
  } finally {
    if (activeRequestRef.current === seq) setIsSending(false);
  }
};
```

**Apply-to-board canonical navigation and launcher/panel rendering** (`frontend/components/board/chat/ChatWidget.tsx:176-201` excerpts):
```tsx
const handleApplyToBoard = () => {
  if (!lastResponse) return;
  if (!canApplyChatToBoard(lastResponse.interpretation)) return;
  const filters = appliedParamsToBoardFilters(lastResponse.interpretation.applied_params);
  const href = buildBoardHref({ ...filters, page: 1, vaga: null });
  router.replace(href, { scroll: false });
  setIsOpen(false);
};

return (
  <>
    {!isOpen && !selectedJob ? <ChatLauncher onOpen={() => setIsOpen(true)} /> : null}
    <ChatPanel open={isOpen} ...>...</ChatPanel>
    {selectedJob ? <JobDetailDialog job={selectedJob} open onClose={handleCloseDetail} /> : null}
  </>
);
```

**Phase 22 guidance:** consult backend-provided disabled signal and, when confirmed disabled, hide launcher/entry and avoid rendering/opening chat panel (per UI-SPEC D-06/SC4). Status check must be non-blocking/fail-safe for board UX and must not affect manual board flows (`page.tsx` remains independent). Preserve request sequencing, session-local state behavior, canonical apply/detail/reveal, and no-contact guarantees.

---

### `frontend/components/board/chat/ChatLauncher.tsx` (presentational UI component)

**Analog:** `frontend/components/board/chat/ChatLauncher.tsx`

**Enabled launcher affordance (accent/44px/focus) — hidden entirely when disabled** (`frontend/components/board/chat/ChatLauncher.tsx:7-29`):
```tsx
export function ChatLauncher({ onOpen }: ChatLauncherProps) {
  return (
    <button
      type="button"
      aria-label="Abrir busca por chat"
      onClick={onOpen}
      className="fixed bottom-4 right-4 z-40 inline-flex h-11 min-h-11 items-center justify-center gap-2 rounded-full border border-accent bg-surface px-4 text-sm font-semibold text-accent-soft shadow-lg transition-colors hover:border-accent-soft hover:text-fg focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-accent-soft sm:bottom-6 sm:right-6"
    >
      {/* svg icon */}
      Chat
    </button>
  );
}
```

**Phase 22 guidance:** do not render a dead/disabled accent control; prefer gating in `ChatWidget`.

---

### `frontend/lib/chatApply.ts` and `frontend/lib/chatApply.test.ts` (pure logic + Vitest node tests)

**Analog:** `frontend/lib/chatApply.ts`, `frontend/lib/chatApply.test.ts`

**Canonical mapping and apply gating** (`frontend/lib/chatApply.ts:1-22`):
```ts
import { normalizeFilters, type Filters } from "@/lib/filters";
import type { ChatAppliedParams, ChatInterpretation } from "@/lib/api";

export function appliedParamsToBoardFilters(applied: ChatAppliedParams): Filters {
  const normalized = normalizeFilters({
    q: (applied.q ?? "").trim(),
    city: (applied.city ?? "").trim().toLowerCase(),
    sort: applied.sort ?? "recentes",
    page: "1",
    vaga: "",
  });
  return { ...normalized, page: 1, vaga: null };
}

export function canApplyChatToBoard(interpretation: ChatInterpretation): boolean {
  if (interpretation.meta?.degraded === true) return false;
  const p = interpretation.applied_params;
  const hasQ = typeof p.q === "string" && p.q.trim().length > 0;
  const hasCity = typeof p.city === "string" && p.city.trim().length > 0;
  const hasSort = p.sort === "antigas";
  return hasQ || hasCity || hasSort;
}
```

**Vitest pure-logic test style** (`frontend/lib/chatApply.test.ts:1-28`, `68-86` excerpts):
```ts
import { describe, expect, it } from "vitest";
import type { ChatInterpretation } from "@/lib/api";
import { appliedParamsToBoardFilters, canApplyChatToBoard } from "@/lib/chatApply";

function interpretation(overrides: { degraded?: boolean; q?: string | null; city?: string | null; sort?: "recentes" | "antigas" | null; }): ChatInterpretation {
  return { understood: {}, field_statuses: [], applied_params: { q: overrides.q ?? null, city: overrides.city ?? null, sort: overrides.sort ?? null }, limitations: [], meta: overrides.degraded ? { degraded: true } : {} };
}

describe("canApplyChatToBoard", () => {
  it("returns false when degraded or all empty/default", () => { /* ... */ });
  it("returns true when q, whitelisted city, or sort antigas is present", () => { /* ... */ });
});
```

**Phase 22 guidance:** extend only if new pure helpers are introduced (e.g. disabled-state gating helper); keep node/Vitest-only, no RTL/Playwright.

---

### `.planning/phases/22-qualidade-hardening-e-valida-o-operacional/22-MANUAL-UAT.md` (QA artifact, guided verification)

**Analog:** `.planning/phases/21-interface-de-chat-e-integracao-no-board/21-HUMAN-UAT.md`

**Structure/frontmatter and test-case format** (`21-HUMAN-UAT.md:1-39` excerpt):
```markdown
---
status: complete
phase: 21-interface-de-chat-e-integracao-no-board
source: [21-VERIFICATION.md]
started: 2026-11-17T21:55:00Z
updated: 2026-11-17T23:49:00Z
---

## Current Test
[testing complete]

## Tests

### 1. Mobile/desktop chat panel behavior and layering
expected: ...
result: pass

## Summary

total: 4
passed: 4
issues: 0
pending: 0
skipped: 0
blocked: 0

## Gaps
```

**Phase 22 guidance:** create a versioned runbook covering critical chat flow + disabled/degraded states and explicit non-regression of manual board (search/list/filters/pagination/detail/reveal) with chat off/degraded; include kill-switch verification steps, no-contacts checks, and manual-search guidance per D-04/D-06/UI-SPEC. Keep feasible in current environment (no Playwright/RTL).

---

### `.planning/phases/22-qualidade-hardening-e-valida-o-operacional/22-MVP-EXAMPLES.md` (QA artifact, matrix)

**Analog:** `.planning/phases/21-interface-de-chat-e-integracao-no-board/21-VERIFICATION.md` and `21-HUMAN-UAT.md` (role-match for evidence recording; matrix shape is new per D-01)

**Evidence/reference style from verification artifacts** (conceptual, role-match): per-item expected/observed status and traceable refs to tests/executions; gaps/limitations explicitly listed. See `21-VERIFICATION.md` for truth-table/requirements-evidence structure and `21-HUMAN-UAT.md` for scenario/result tracking.

**Phase 22 guidance (D-01/D-02/D-03):** for each of the 5 exemplos-alvo record input, interpretação/`applied_params`/`field_statuses` esperados, resultados/`limitations`/`meta.guidance` esperados, lacunas explícitas, and **contrato esperado + resultado observado** with references to deterministic automated tests (mocked intent/chat) and/or documented fixtures/runs. Explicitly state: “parecidas” = seed textual limitado (termos em `q`), sem similaridade semântica/vetorial e sem seed por link/ID; Campinas fora da whitelist; salário/modalidade/contrato/senioridade não filtrados nativamente (aproximados/sinalizados quando aplicável).

## Shared Patterns

### 1) Deterministic retrieval & contact safety (must not regress)
**Source:** `backend/app/api/v1/public.py:147-183`, `258-326`; `backend/app/schemas/chat.py:39-52`; `backend/tests/test_chat_search_api.py:69-116`, `163-169`
**Apply to:** chat-search success/disabled/degraded paths, all QA-02/QA-03 assertions.
```python
items, total = await list_published(session, page=payload.page, limit=payload.limit,
    q=applied.q, city=applied.city, sort=(applied.sort or "recentes"))
return ChatSearchResponse(interpretation=contract, results=ChatSearchResults(
    items=[JobPublic.model_validate(job) for job in items], page=payload.page, limit=payload.limit, total=total))
# assertions: ids/total == GET /api/v1/public/jobs for same params; no contact_email/contact_phone in results
```

### 2) Controlled degradation/disabled guidance (safe pt-BR, no internals, no auto results)
**Source:** `backend/app/api/v1/public.py:41-103`, `272-306`; `backend/tests/test_chat_search_api.py:172-267`
**Apply to:** `chat_disabled`, `llm_unavailable`, `timeout`, `no_extractable_params` handling and QA-01/03 expectations.
```python
degraded = _chat_degraded_contract(message, reason_code, guidance, limitation=...)
return ChatSearchResponse(interpretation=degraded,
    results=ChatSearchResults(items=[], page=payload.page, limit=payload.limit, total=0))
# meta: degraded=True, degradation_reason=<stable>, guidance=<pt-BR safe>; applied_params all null
```

### 3) LLM seam mocking for deterministic tests (no network)
**Source:** `backend/tests/test_chat_search_api.py:89-94`; `backend/tests/test_intent_parser.py:15-64`, `94-106`; `backend/tests/test_intent_client.py:18-58`
**Apply to:** all intent/chat automated scenarios (QA-01/QA-02).
```python
async def fake_extract(*args, **kwargs): return interpretation
monkeypatch.setattr("app.api.v1.public.extract_and_map_intent", fake_extract)
# or inject FakeGroqClient(script)/RaisingClient into parser/client seams
```

### 4) No-PII structured operational logging (target)
**Source pattern refs:** `backend/app/api/v1/public.py:278`, `360-365`; `backend/app/core/logging.py:5-21`; D-07/22-RESEARCH.
**Apply to:** `chat_search` boundary instrumentation and `caplog` assertions.
```python
# target shape (per research): time.perf_counter() + finally logger.info("chat_search", extra={...})
# allowed: outcome, reason/degradation_reason, latency_ms, results_count, total, page, limit
# forbidden: payload.message, understood raw dumps, contacts/PII, exception internals to users
```

### 5) Canonical board apply & URL source of truth (must remain intact)
**Source:** `frontend/lib/chatApply.ts:1-22`; `frontend/lib/filters.ts:31-92`; `frontend/components/board/chat/ChatWidget.tsx:176-181`; `frontend/app/(public)/page.tsx:38-47`, `165`
**Apply to:** UI non-regression, disabled/degraded flows (no apply when inapplicable), manual search continuity.
```ts
const filters = appliedParamsToBoardFilters(response.interpretation.applied_params);
const href = buildBoardHref({ ...filters, page: 1, vaga: null });
router.replace(href, { scroll: false });
// normalizeFilters/buildBoardHref own q/city/sort/page/vaga contract
```

### 6) Test infrastructure & environment constraints
**Source:** `backend/tests/conftest.py:93-114`, `263-267`; `frontend/vitest.config.ts` (node env), `frontend/package.json` (`test:chat` / `test` scripts implied)
**Apply to:** QA-02 execution notes and optional DB-independent whitelisting of pure intent tests.
```python
# DB-dependent tests skipped without TEST_DATABASE_URL/DATABASE_URL unless in db_independent
# limiter.reset() autouse keeps rate-limit buckets isolated
# Frontend automation: Vitest node, pure logic only (no Playwright/RTL)
```

## No Analog Found

Files with no close exact match in the codebase (planner should follow locked contracts/RESEARCH patterns and closest role-match analogs):

| File | Role | Data Flow | Reason |
|------|------|-----------|--------|
| `.planning/phases/22-qualidade-hardening-e-valida-o-operacional/22-MVP-EXAMPLES.md` | QA artifact (contrato esperado + observado matrix) | document | No prior `*-MVP-EXAMPLES.md` matrix artifact in the phase set; use `21-VERIFICATION.md`/`21-HUMAN-UAT.md` evidence style as role-match and satisfy D-01/D-03 structure. |
| Chat status signal endpoint/helper (if introduced, e.g. GET under `/public`) | public API/status | request-response | No existing public “chat status/enabled” endpoint; closest analogs are simple public GET handlers in `backend/app/api/v1/public.py` (e.g. `list_public_jobs`, `get_public_job`) and degraded/disabled response handling already in `chat_search`. Shape is discretionary but must be safe, non-blocking for board, and consistent with D-06/UI-SPEC. |

## Metadata

**Analog search scope:** `backend/app/**`, `backend/tests/**`, `frontend/app/**`, `frontend/components/**`, `frontend/lib/**`, `.planning/phases/21-interface-de-chat-e-integracao-no-board/**`, `.planning/phases/22-qualidade-hardening-e-valida-o-operacional/**`
**Files scanned:** ~120+ (backend Python, frontend TS/TSX, phase artifacts inspected via targeted reads/glob/dir; key analogs read in full)
**Pattern extraction date:** 2026-11-18
