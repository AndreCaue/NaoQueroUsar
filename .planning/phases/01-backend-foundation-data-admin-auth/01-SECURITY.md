---
phase: 01
slug: backend-foundation-data-admin-auth
status: verified
threats_open: 0
asvs_level: 1
created: 2026-11-15
---

# Phase 01 — Security

> Per-phase security contract: threat register, accepted risks, and audit trail.

---

## Trust Boundaries

| Boundary | Description | Data Crossing |
|----------|-------------|---------------|
| client→API | Untrusted HTTP (method, path, headers, body) enters FastAPI | Requests, credentials, query params, JSON bodies |
| client→API (login) | Untrusted password + Turnstile token/credentials cross into auth logic | Login payload, bearer tokens |
| client→admin routes | Untrusted Bearer token/claims validated on every protected request | Authorization header, JWT claims |
| anonymous client→public API | Unauthenticated reads of published job data | Public list/detail requests and responses (contact-free) |
| API→Neon | SQLAlchemy issues SQL over TLS to Postgres (pooled endpoint) | Job records, auth/session-related reads/writes as applicable |
| migration→Neon | Alembic DDL executed against the database | Schema, enum, indexes, triggers, constraints |
| environment→process | Secrets/config loaded from environment at startup/runtime | DATABASE_URL, JWT/admin secrets, Turnstile/config values |
| test→Neon branch/local DB | Automated tests run against isolated test database, not production | Synthetic seed/test data and assertions |

---

## Threat Register

| Threat ID | Category | Component | Disposition | Mitigation | Status |
|-----------|----------|-----------|-------------|------------|--------|
| T-01-01 | Information disclosure | secrets in logs/repo | mitigate | `.env` ignored; `.env.example` placeholders only; logging/config avoid emitting secrets; settings extra fields ignored | closed |
| T-01-02 | Denial of service | CORS wildcard / oversized origins | mitigate | `CORSMiddleware` uses `settings.cors_origins_list`; `allow_credentials=False`; production CORS validation fails closed on unsafe origins | closed |
| T-01-03 | Tampering | startup with misconfigured env | mitigate | `pydantic-settings` required fields fail fast (no silent defaults for critical secrets/config) | closed |
| T-01-04 | Denial of service | Neon CU-hour burn from keep-alive | mitigate | Async engine uses `pool_pre_ping=True` and `statement_cache_size=0`; `/health` is liveness-only (no DB ping); engine disposed on shutdown | closed |
| T-01-05 | Spoofing | TLS/identity to DB | transfer | Neon/Postgres transport security is platform-managed (pooled endpoint with TLS/`ssl=require` expectation); risk transferred to managed DB platform | closed |
| T-02-01 | Tampering | invalid/partial job rows | mitigate | DB-level `title_not_blank` and `at_least_one_contact` CHECK constraints in model/migration enforce invariants | closed |
| T-02-02 | Tampering | status outside allowed set | mitigate | Native `job_status` enum (`pending/published/needs_review/invalid`) enforced in model/migration | closed |
| T-02-03 | Information disclosure | contact data modelling | mitigate | Contact columns remain server-side only; public API contract is contact-free via `JobPublic` schema and public routes return no contact fields (validated in phase artifacts/tests) | closed |
| T-02-04 | Repudiation | lost audit of changes | mitigate | `created_at` set server-side; `updated_at` maintained by DB trigger | closed |
| T-02-05 | Elevation/DoS | migration run against wrong DB | mitigate | Alembic/runtime DB URL sourced from validated settings; no hardcoded credentials; SSL required for Neon usage | closed |
| T-03-01 | Spoofing | login brute force / credential stuffing | mitigate | Plan deferred to Phase 3, but current implementation enforces Turnstile Siteverify + per-IP rate limiting on `POST /api/v1/auth/login` before password verification | closed |
| T-03-02 | Spoofing | forged JWT (algorithm confusion / weak handling) | mitigate | JWT issued/decoded with HS256 and decode pins `algorithms=["HS256"]`; claims validated by admin guard | closed |
| T-03-03 | Elevation of privilege | access admin route without valid token | mitigate | `require_admin` dependency enforces Bearer auth, rejects missing/invalid/expired/tampered tokens, and validates `sub=admin`/`role=admin`; admin routes depend on it | closed |
| T-03-04 | Information disclosure | password/token/secret leakage | mitigate | Master password stored as hash in env; verification uses bcrypt; auth errors return no token; secrets not logged in inspected auth paths | closed |
| T-03-05 | Repudiation | no record of auth failures | accept | Accepted MVP risk: no dedicated auth-failure audit trail/event logging in current implementation; documented in Accepted Risks Log (see audit rationale) | closed |
| T-03-06 | Repudiation | long-lived stolen token | mitigate | Single admin JWT with bounded lifetime (`JWT_EXPIRES_IN`, default 12h) limits replay window; no refresh token | closed |
| T-04-01 | Information disclosure | contact leaked in public list/detail | mitigate | `JobPublic` schema excludes contact fields; public list/detail endpoints return contact-free payloads; tests assert absence | closed |
| T-04-02 | Information disclosure | expired/pending jobs exposed | mitigate | Public read queries filter `status='published' AND expires_at > now()`; detail returns 404 for non-public/non-eligible jobs | closed |
| T-04-03 | Denial of service | unbounded page size / scraping throughput | mitigate | Public pagination bounds enforced (`limit` 1-50, default 20); additional anti-scrape/rate-limit controls for sensitive surfaces handled in later phases | closed |
| T-04-04 | Information disclosure | tests leaking real PII | mitigate | Seed/test data are synthetic; tests target isolated test DB/fixtures (per phase artifacts) | closed |
| T-04-05 | Tampering | SQL injection via params | mitigate | SQLAlchemy parameterized queries and typed/bounded request params used for public reads | closed |

*Status: open · closed*
*Disposition: mitigate (implementation required) · accept (documented risk) · transfer (third-party)*

---

## Accepted Risks Log

| Risk ID | Threat Ref | Rationale | Accepted By | Date |
|---------|------------|-----------|-------------|------|
| AR-01-01 | T-03-05 | MVP accepts lack of a dedicated auth-failure audit trail. Current implementation does not emit explicit structured events for failed admin login or invalid/missing/expired admin token checks, and request logging is not configured as a security audit log. Residual risk: reduced forensic visibility/repudiation evidence for authentication failures. Accepted for Phase 01 baseline; revisit by adding explicit auth-failure logging (without secrets/tokens/passwords) and/or centralized audit logging in a future hardening pass. | User (gsd-secure-phase decision) | 2026-11-15 |

---

## Security Audit Trail

| Audit Date | Threats Total | Closed | Open | Run By |
|------------|---------------|--------|------|--------|
| 2026-11-15 | 21 | 21 | 0 | gsd-security-auditor + orchestrator (gsd-secure-phase, user accepted T-03-05) |

---

## Sign-Off

- [x] All threats have a disposition (mitigate / accept / transfer)
- [x] Accepted risks documented in Accepted Risks Log
- [x] `threats_open: 0` confirmed
- [x] `status: verified` set in frontmatter

**Approval:** verified 2026-11-15
