---
phase: 14
slug: fundacao-social-dados-e-configuracao
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-11-15
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
| **Estimated runtime** | ~30 seconds (unit-focused social tests); DB integration depends on available test DB |

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
| 14-TBD-crypto | TBD | TBD | SOC-04 | V6 Cryptography / Info Disclosure | Encrypt/decrypt uses Fernet; invalid key/decrypt fails with safe domain error; token stored/handled as text without leaking secrets in errors/logs | unit | `cd backend && pytest tests/test_social_crypto.py -x` | ❌ W0 | ⬜ pending |
| 14-TBD-models-accounts | TBD | TBD | SOC-01 | V5 Input/Data integrity | `social_accounts` schema/models enforce required fields/status enum and store only encrypted token text | integration/unit (DB when available) | `cd backend && pytest tests/test_social_models.py -x` | ❌ W0 | ⬜ pending |
| 14-TBD-models-posts | TBD | TBD | SOC-02 | Data integrity / idempotency foundation | `social_posts` enforces FK `job_id` CASCADE, unique `(job_id, provider)`, defaults/nullability/operational fields | integration/unit (DB when available) | `cd backend && pytest tests/test_social_models.py -x` | ❌ W0 | ⬜ pending |
| 14-TBD-models-logs | TBD | TBD | SOC-03 | Auditability | `social_post_logs` persists attempts/results/errors/response summary safely with FK to `social_posts` and timestamps | integration/unit (DB when available) | `cd backend && pytest tests/test_social_models.py -x` | ❌ W0 | ⬜ pending |
| 14-TBD-publisher | TBD | TBD | SOC-05 | Contract safety | `SocialPublisher` is async/typed; `FacebookPublisher` is explicit stub with no external HTTP and returns controlled typed result | unit | `cd backend && pytest tests/test_social_publisher.py -x` | ❌ W0 | ⬜ pending |
| 14-TBD-config | TBD | TBD | SOC-06 | V5 Input Validation | Settings/.env.example cover exact SOC-06 vars with format validation, safe defaults/placeholders, and retry parsing (`5`, `300,900,3600,10800,21600`) | unit | `cd backend && pytest tests/test_social_config.py -x` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `backend/tests/test_social_crypto.py` — stubs/tests for SOC-04 (Fernet, key validation, safe decrypt errors)
- [ ] `backend/tests/test_social_publisher.py` — stubs/tests for SOC-05 (async contract, typed result, stub no-HTTP)
- [ ] `backend/tests/test_social_config.py` — stubs/tests for SOC-06 (Settings parsing/validation, `.env.example` coverage expectations)
- [ ] `backend/tests/test_social_models.py` — stubs/tests for SOC-01/02/03 (models, constraints, enums, defaults; DB integration where available)
- [ ] `backend/tests/conftest.py` — confirm/extend shared fixtures if needed for social tests/DB settings
- [ ] `cryptography` dependency available in backend env (`pip install cryptography==50.0.2` or project-managed equivalent) for SOC-04

*Note: DB-backed integration assertions depend on a reproducible migrated test database (known inherited gap).*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Alembic migration applies cleanly on target Neon/Postgres and creates expected enums/tables/constraints/indexes | SOC-01, SOC-02, SOC-03 | Requires configured `DATABASE_URL`/migrated DB environment; local CI/test DB reproducibility is a known gap | Run migration against a disposable/test Postgres/Neon DB, inspect schema for `social_accounts`, `social_posts`, `social_post_logs`, unique `(job_id, provider)`, FK cascades, and enum types |
| `.env.example` social block is complete, pt-BR, and free of real secrets/placeholders only | SOC-06 | Documentation/comment quality and secret hygiene are partly editorial | Review `backend/.env.example` for exact SOC-06 variable coverage, pt-BR comments, placeholders, and no leaked secrets/defaults |

*Automated tests should still assert key parse/validation behaviors where practical.*

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 30s (quick subset)
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
