---
phase: 14
slug: fundacao-social-dados-e-configuracao
status: audited
nyquist_compliant: true
wave_0_complete: true
created: 2026-11-15
updated: 2026-11-15
---

# Phase 14 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 9.1.1 + pytest-asyncio (>=1.0.0,<2.0.0), `asyncio_mode=auto` |
| **Config file** | `backend/pyproject.toml` (`[tool.pytest.ini_options]`) |
| **Quick run command** | `cd backend && pytest tests/test_social_*.py -x` |
| **Full suite command** | `cd backend && pytest` |
| **Estimated runtime** | ~30 seconds (unit/structural social tests); DB migration apply on target DB remains manual/inherited gap |

---

## Sampling Rate

- **After every task commit:** Run `cd backend && pytest tests/test_social_*.py -x` (or the specific social test file changed)
- **After every plan wave:** Run `cd backend && pytest`
- **Before `/gsd-verify-work`:** Full suite must be green (subject to inherited DB-backed test environment gaps)
- **Max feedback latency:** 30 seconds for quick social subset

---

## Per-task Verification Map

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| 14-03-01 | 14-03 | 2 | SOC-04 | V6 Cryptography / Info Disclosure | Encrypt/decrypt uses Fernet; invalid key/decrypt fails with safe domain error; token handled as text without leaking secrets/ciphertext/key in safe error messages | unit | `cd backend && pytest tests/test_social_crypto.py -x` | ✅ | ✅ green |
| 14-02-01 | 14-02 | 1 | SOC-01 | V5 Input/Data integrity | `SocialAccount`/enum and migration define required fields/status enum and encrypted token text column (`page_access_token`) with expected indexes | unit/structural (+ migration contract) | `cd backend && pytest tests/test_social_models.py -x` | ✅ | ✅ green |
| 14-02-02 | 14-02 | 1 | SOC-02 | Data integrity / idempotency foundation | `SocialPost`/enum and migration enforce FK `job_id -> jobs.id` CASCADE, unique `(job_id, provider)`, attempts default 0, timestamps/operational fields and indexes | unit/structural (+ migration contract) | `cd backend && pytest tests/test_social_models.py -x` | ✅ | ✅ green |
| 14-02-03 | 14-02 | 1 | SOC-03 | Auditability | `SocialPostLog` and migration persist attempts/results/errors/response summary safely with FK `social_post_id -> social_posts.id` CASCADE and timestamps/indexes | unit/structural (+ migration contract) | `cd backend && pytest tests/test_social_models.py -x` | ✅ | ✅ green |
| 14-03-02 | 14-03 | 2 | SOC-05 | Contract safety | `SocialPublisher` is async/typed contract; `FacebookPublisher` is explicit stub with no external HTTP (`httpx`/`requests`) and returns controlled typed failure `PublishResult` | unit | `cd backend && pytest tests/test_social_publisher.py -x` | ✅ | ✅ green |
| 14-01-01/02 | 14-01 | 1 | SOC-06 | V5 Input Validation | Settings/.env.example cover exact SOC-06 vars with format validation, safe defaults/placeholders, Fernet-key validation when filled, and retry parsing (`5`, `300,900,3600,10800,21600`) | unit | `cd backend && pytest tests/test_social_config.py -x` | ✅ | ✅ green |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

*Note: SOC-01/02/03 automated coverage is structural/contract-level (ORM metadata, Alembic registration, migration 0004 content). Applying migration on a target Postgres/Neon DB remains manual-only (see below).*

---

## Wave 0 Requirements

- [x] `backend/tests/test_social_crypto.py` — tests for SOC-04 (Fernet roundtrip, key validation, safe decrypt errors)
- [x] `backend/tests/test_social_publisher.py` — tests for SOC-05 (async contract behavior, typed result/categories, stub no-HTTP)
- [x] `backend/tests/test_social_config.py` — tests for SOC-06 (Settings parsing/validation, `.env.example` coverage/defaults/placeholders)
- [x] `backend/tests/test_social_models.py` — tests for SOC-01/02/03 (models, constraints, enums, defaults, Alembic/env registration, migration 0004 contract)
- [x] `backend/tests/conftest.py` — confirmed existing harness sufficient for new unit/structural social tests (no social-specific fixture changes required)
- [x] `cryptography` dependency available in backend env (`backend/pyproject.toml` declares `cryptography==50.0.2`) for SOC-04

*Note: DB-backed integration assertions (actual migration apply/schema introspection on DB) depend on a reproducible migrated test database (known inherited gap).*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Alembic migration applies cleanly on target Neon/Postgres and creates expected enums/tables/constraints/indexes | SOC-01, SOC-02, SOC-03 | Requires configured `DATABASE_URL`/migrated DB environment; local CI/test DB reproducibility is a known gap | Run migration against a disposable/test Postgres/Neon DB, inspect schema for `social_accounts`, `social_posts`, `social_post_logs`, unique `(job_id, provider)`, FK cascades, enum types, and indexes |
| `.env.example` social block is complete, pt-BR, and free of real secrets/placeholders only | SOC-06 | Documentation/comment quality and secret hygiene are partly editorial (beyond key automated assertions) | Review `backend/.env.example` for exact SOC-06 variable coverage, pt-BR comments, placeholders, and no leaked secrets/defaults |

*Automated tests assert key parse/validation/schema-contract behaviors where practical.*

---

## Validation Sign-Off

- [x] All tasks have `<automated>` verify or Wave 0 dependencies
- [x] Sampling continuity: no 3 consecutive tasks without automated verify
- [x] Wave 0 covers all MISSING references
- [x] No watch-mode flags
- [x] Feedback latency < 30s (quick subset)
- [x] `nyquist_compliant: true` set in frontmatter

**Approval:** approved (automated gap closure for SOC-01..SOC-06; DB migration apply remains manual-only)

## Validation Audit 2026-11-15

| Requirement | Plan / Area | Gap found | Automated test(s) | Command | Result | Resolved / Escalated | Notes |
|-------------|-------------|-----------|-------------------|---------|--------|----------------------|-------|
| SOC-04 | 14-03 / crypto | MISSING | `backend/tests/test_social_crypto.py` (4 tests) | `cd backend && pytest tests/test_social_crypto.py -x` | ✅ green | Resolved | Fernet roundtrip, invalid key validation, safe decrypt/domain error behavior (no key/token/ciphertext leak in safe message). |
| SOC-05 | 14-03 / publisher contract | MISSING | `backend/tests/test_social_publisher.py` (4 tests) | `cd backend && pytest tests/test_social_publisher.py -x` | ✅ green | Resolved | Async contract behavior, typed `PublishResult`/categories/payload, Facebook stub controlled failure, no `httpx`/`requests` in social contract/stub modules. |
| SOC-06 | 14-01 / settings & env docs | MISSING | `backend/tests/test_social_config.py` (9 tests) | `cd backend && pytest tests/test_social_config.py -x` | ✅ green | Resolved | Exact SOC-06 fields/defaults/parsing, URL/max-attempts/retry-delays validation, Fernet key format validation (safe custom error), `.env.example` coverage/defaults/empty secret placeholders. |
| SOC-01 | 14-02 / models & migration | MISSING (DB-integration aspect manual-only) | `backend/tests/test_social_models.py` (subset, 5 tests total file) | `cd backend && pytest tests/test_social_models.py -x` | ✅ green | Resolved (automated structural/contract) | ORM enum/table/columns/indexes + Alembic env/init registration + migration 0004 account schema markers verified without live DB. Migration apply on target DB: manual-only. |
| SOC-02 | 14-02 / models & migration | MISSING (DB-integration aspect manual-only) | `backend/tests/test_social_models.py` (subset, 5 tests total file) | `cd backend && pytest tests/test_social_models.py -x` | ✅ green | Resolved (automated structural/contract) | FK `job_id` CASCADE, unique `(job_id, provider)`, attempts default, status enum/indexes, migration 0004 markers verified. Migration apply on target DB: manual-only. |
| SOC-03 | 14-02 / models & migration | MISSING (DB-integration aspect manual-only) | `backend/tests/test_social_models.py` (subset, 5 tests total file) | `cd backend && pytest tests/test_social_models.py -x` | ✅ green | Resolved (automated structural/contract) | `social_post_logs` FK cascade, audit fields/timestamps/indexes, registration and migration 0004 markers verified. Migration apply on target DB: manual-only. |

**Quick suite:** `cd backend && pytest tests/test_social_*.py -x` → **22 passed** (2026-11-15). No escalations. Implementation files were not modified.
