---
phase: 5
slug: admin-review-area
status: verified
threats_open: 0
asvs_level: 1
created: 2026-10-27
---

# Phase 5 — Security

> Per-phase security contract: threat register, accepted risks, and audit trail.

---

## Trust Boundaries

| Boundary | Description | Data Crossing |
|----------|-------------|---------------|
| client → admin API | Untrusted input (query params, body) crosses here; JWT required |
| admin API → DB | SQL via SQLAlchemy; CHECK constraints backstop |
| browser → paste page | Login via Turnstile + JWT; backend authoritative |
| admin review UI → admin API | Optimistic mutation state crosses here (client-only) |

---

## Threat Register

Phase 05 register (extracted from the `<threat_model>` blocks of the four
`05-0x-PLAN.md` files; authoritative source for verification).

| Threat ID | Category | Component | Disposition | Mitigation | Status |
|-----------|----------|-----------|-------------|------------|--------|
| T-05-01 | Elevation of privilege | admin routes | mitigate | `require_admin` Depends on every route; `test_requires_auth` 401 | closed |
| T-05-02 | Information disclosure | JobAdmin schema | mitigate | JobAdmin only used in admin routes; public routes keep JobPublic (no contact) | closed |
| T-05-03 | Tampering | city input | mitigate | `_resolve_city` whitelist; unknown → 422 (fail closed on list, validator on update) | closed |
| T-05-04 | Tampering | at_least_one_contact | mitigate | model_validator + DB CHECK + IntegrityError → 422 | closed |
| T-05-05 | Tampering | SQL injection | mitigate | parameterized queries via SQLAlchemy; no string interpolation | closed |
| T-05-06 | Spoofing | client guard | mitigate | Backend `require_admin` 401 on every route; guard only redirects | closed |
| T-05-07 | Information disclosure | JobAdmin in client | accept | Contact/snippet only after auth; token in sessionStorage | closed (accepted risk AR-05-01) |
| T-05-08 | Tampering | toast/optimistic | mitigate | Rollback + refetch + toast error | closed |
| T-05-09 | Spoofing | login | mitigate | Turnstile server-side + rate limit + bcrypt (Phase 3) | closed |
| T-05-10 | Information disclosure | token | accept | sessionStorage; cleared on logout | closed (accepted risk AR-05-02) |
| T-05-11 | Tampering | optimistic update | mitigate | Snapshot + rollback + refetch + toast error | closed |
| T-05-12 | Information disclosure | snippet/contact | mitigate | Only rendered in admin authenticated area | closed |
| T-05-13 | DoS | pagination | mitigate | limit cap 100 server-side | closed |

*Status: open · closed*
*Disposition: mitigate (implementation required) · accept (documented risk) · transfer (third-party)*

---

## Inherited Threats (verified closed — foundations Phase 05 builds on)

| Threat ID | Category | Component | Disposition | Mitigation | Status |
|-----------|----------|-----------|-------------|------------|--------|
| T-01-01 | Information disclosure | secrets in logs/repo | mitigate | `.env` gitignored; `.env.example` placeholders only; `configure_logging` never logs settings; `extra="ignore"` prevents leakage into models | closed |
| T-01-02 | Denial of service | CORS wildcard / oversized origins | mitigate | CORS restricted to `settings.cors_origins_list`; `allow_credentials=False` | closed |
| T-01-03 | Tampering | startup with misconfigured env | mitigate | pydantic-settings required fields fail fast (no silent defaults for secrets) | closed |
| T-01-04 | Denial of service | Neon CU-hour burn from keep-alive | mitigate | `pool_pre_ping=True` + small default pool; `/health` liveness-only (no DB ping); dispose engine on shutdown | closed |
| T-01-05 | Spoofing | TLS/identity to DB | transfer | Neon enforces `ssl=require` on pooled endpoint (platform-managed) | closed (transfer) |
| T-02-08 | Spoofing | extract.py auth | mitigate | `Depends(require_admin)` (Phase 1 proven JWT gate); tests assert 401 | closed |
| T-02-09 | Tampering | extract.py → DB | mitigate | Single transaction; failure → rollback + "nada foi gravado"; DB CHECK constraints `at_least_one_contact` / `title_not_blank` | closed |
| T-02-10 | DoS | extract.py | mitigate | `EXTRACT_MAX_TEXT_BYTES` → 413; `EXTRACT_TIMEOUT_SECONDS` → 504; `EXTRACT_MAX_JOBS=50`; token-budgeted chunks + pacing | closed |

---

## Accepted Risks Log

| Risk ID | Threat Ref | Rationale | Accepted By | Date |
|---------|------------|-----------|-------------|------|
| AR-05-01 | T-05-07 | Contact / source_snippet reach the single trusted admin device only after Bearer JWT validation; residual token-in-storage (sessionStorage) exposure accepted for the minimal admin surface (httpOnly cookies out of scope per Phase 1 D-01). Revisit with Phase 6 hardening. | admin (master) | 2026-10-27 |
| AR-05-02 | T-05-10 | Admin JWT (12h, no refresh) kept in sessionStorage on the single-admin device; cleared on logout and on 401. Accepted for the minimal admin session model; cookie-based session migration deferred. | admin (master) | 2026-10-27 |

*Accepted risks do not resurface in future audit runs.*

---

## Security Audit Trail

| Audit Date | Threats Total | Closed | Open | Run By |
|------------|---------------|--------|------|--------|
| 2026-10-27 | 13 | 13 | 0 | gsd-security-auditor |

### Security Audit 2026-10-27

| Metric | Count |
|--------|-------|
| Threats found | 13 (Phase 05 register) |
| Closed | 13 |
| Open | 0 |

- 11 mitigate threats verified closed against implemented code (evidence: `backend/app/api/v1/admin.py`, `backend/app/crud/jobs.py`, `backend/app/schemas/job.py`, `backend/app/api/v1/public.py`, `backend/app/api/v1/auth.py`, `backend/app/services/turnstile.py`, `backend/app/deps.py`, `backend/tests/test_admin_jobs.py`, frontend admin components + `frontend/lib/api.ts`).
- 2 accept threats closed via documented accepted risks (AR-05-01 / AR-05-02 entries above).
- Inherited Phase 1 ADMN threats (T-01-01…T-01-05) verified closed / transfer-documented; Phase 2 extraction threats underpinning the admin-extract surface (T-02-08…T-02-10) verified closed.

### Post-review fix verification (05-REVIEW.md → current code)

All findings from the Phase 05 cross-AI review were verified as resolved in the
current tree:

- CR-01: Edit dialog resets on open; focuses title input. ✓
- CR-02: LogoutButton clears token + hard-navigates. ✓
- CR-03: debug dumps removed; tree clean (`git status` empty). ✓
- WR-01/WR-03: JobUpdate validators wired (title/city/email/phone, blank-city,
  both-contacts-cleared). ✓
- WR-02: IntegrityError narrowed to contact CHECK. ✓
- WR-04: Unknown admin city filter → 422 fail closed. ✓
- WR-05: Approve requires pending/needs_review (409) + refreshes `expires_at`. ✓
- WR-06: `readError` flattens FastAPI validation arrays; ApiError keeps status. ✓
- WR-07: Single `TOKEN_KEY` in `lib/auth.ts`; EditJobDialog takes token by prop. ✓
- WR-09: Toast has dismiss control, `role="alert"` for errors, hover/focus pause,
  timer cleanup. ✓
- WR-10: Edit dialog focuses first field. ✓
- WR-11: Optimistic rollback restores snapshot without refetch; mutations
  serialized via `mutatingRef`. ✓
- WR-12: Admin test suite extended to 20 tests (incl. invalid status/city, sort,
  approve 409/TTL, blank title, detail + `/admin/me` auth, `expires_in > 0`). ✓
- IN-09: `sort: Literal["recentes","antigas"]`, `page <= 10_000`. ✓
- IN-08: all four `JobStatus` labels mapped. ✓

---

## Sign-Off

- [x] All threats have a disposition (mitigate / accept / transfer)
- [x] Accepted risks documented in Accepted Risks Log
- [x] `threats_open: 0` confirmed
- [x] `status: verified` set in frontmatter

**Approval:** verified 2026-10-27
