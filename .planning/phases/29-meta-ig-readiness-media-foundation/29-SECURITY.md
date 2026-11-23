---
phase: 29
slug: meta-ig-readiness-media-foundation
status: verified
threats_open: 0
asvs_level: 1
created: 2026-11-23
---

# Phase 29 — Security

> Per-phase security contract: threat register, accepted risks, and audit trail.

---

## Trust Boundaries

| Boundary | Description | Data Crossing |
|----------|-------------|---------------|
| Admin UI/API → backend integrations endpoints | Authenticated admin controls Meta connection/readiness state and Instagram media preparation; requests must be authorized and responses safe. | Admin claims/JWT context; safe Meta/IG readiness state, page metadata, validation/provenance |
| Backend → Meta Graph API | External API boundary for IG readiness resolution; provider payloads/tokens are sensitive and untrusted. | Encrypted/stored Page token used in Graph calls; Graph JSON responses/errors |
| Backend persistence (Postgres) | Stores encrypted Page tokens, additive IG readiness metadata, and durable IG media bytes. | Encrypted tokens, IG readiness fields, generated image bytes/provenance metadata |
| Public internet → public IG media endpoint | Unauthenticated endpoint intentionally fetchable by Meta/browser for exact IG media version. | job_id + version hash in path; image/jpeg bytes |
| Documentation/checklist → operator behavior | Ops docs guide manual Meta setup and verification; inaccurate guidance can cause misconfiguration or leakage. | Env var names, scopes, checklist instructions |

---

## Threat Register

| Threat ID | Category | Component | Disposition | Mitigation | Status |
|-----------|----------|-----------|-------------|------------|--------|
| T-29-01 | Information Disclosure | `backend/app/api/v1/integrations.py`, `backend/app/schemas/social_integrations.py` | mitigate | Additive IG readiness schemas expose only allowlisted safe fields (`ready`, `ig_user_id`, `ig_username`, `state`, `message`, `checked_at`). Integrations tests assert responses contain no `access_token`, `page_access_token`, `client_secret`, `EAAB`, `SOCIAL_TOKEN_ENCRYPTION_KEY`. | closed |
| T-29-02 | Spoofing / Elevation of Privilege | `/api/v1/admin/integrations/meta/*` | mitigate | All Meta admin integration endpoints keep `Depends(require_admin)` (`/meta/status`, `/meta/start`, `/meta/callback`, `/meta/pages/confirm`, `/meta/verify`, `/meta/disconnect`, pending selection). | closed |
| T-29-03 | Tampering | `backend/app/services/social/instagram_readiness.py` Graph handling | mitigate | IG Graph response shape is normalized/validated; missing/invalid shapes map to safe actionable/unknown states. Expected Graph/timeout/request errors are caught and returned as safe `InstagramReadinessResult` (no raw provider payload/state transition trust). | closed |
| T-29-04 | Denial of Service | IG readiness Graph calls | mitigate | D-14 preserved: `get_current_meta_status` reads persisted account/pending state only; no Graph query on status GET. IG readiness refresh occurs on connect/confirm/verify paths. Graph calls use bounded `httpx` timeout (`_GRAPH_TIMEOUT_SECONDS = 10.0`). | closed |
| T-29-05 | Information Disclosure | `backend/app/services/social/meta_oauth.py` logs | mitigate | Meta OAuth/IG readiness logging uses safe `error_type`/fixed codes only; no token, token query param, or raw Graph body logging. Code scan shows no token-in-log patterns. | closed |
| T-29-06 | Information Disclosure | `backend/app/api/v1/public.py` IG media endpoint | mitigate | Public endpoint is unauthenticated by design but serves only DB-resolved `job_id + version` asset bytes. Strict version regex (`^[a-f0-9]{16}$`), 404 on missing/invalid, fixed `image/jpeg`, immutable cache headers; no user path/file access and no auth/token data. | closed |
| T-29-07 | Denial of Service | `backend/app/services/social/image_card.py` / media prepare | mitigate | Fixed 1080x1350 canvas; deterministic JPEG quality clamp down to 70 and hard fail if still >8MB (`MAX_BYTES`). Strict version hash format validation and no user-upload image processing in v1.5. Public rebuild only for current expected hash. | closed |
| T-29-08 | Tampering / Spoofing | `MEDIA_PUBLIC_BASE_URL` / public image URL | mitigate | Explicit config validation requires HTTPS public non-localhost/non-private base URL (`backend/app/core/config.py`, `image_media.validate_media_public_base_url`); invalid/missing returns IMAG-01/03 pt-BR `invalid_public_url`. URL never inferred from request host. | closed |
| T-29-09 | Elevation of Privilege | admin media prepare endpoint | mitigate | `POST /api/v1/admin/jobs/{job_id}/instagram/media/prepare` requires `Depends(require_admin)`. Public IG media route remains read-only and separate under `/api/v1/public/ig-media/{job_id}/{version}.jpg` with no admin dependency. | closed |
| T-29-10 | Information Disclosure | image content/provenance | mitigate | Card renderer includes essential job fields only; no contact email/phone/whatsapp/telegram. IG hash payload excludes contact/status/id/timestamps/source fields. Provenance contains safe metadata only. Tests assert contact-only changes do not alter hash and response/body has no token leakage. | closed |
| T-29-11 | Information Disclosure | `frontend/app/admin/integracoes/IntegrationsClient.tsx` | mitigate | UI renders only allowlisted readiness fields/safe pt-BR messages and maps states to fixed actionable copy. No token/secret/raw provider error rendering in Integrations UI. | closed |
| T-29-12 | Spoofing / Elevation of Privilege | Integrations admin UI actions | mitigate | UI uses existing admin-token API helpers (`frontend/lib/api.ts`) for Meta status/start/verify/confirm/disconnect flows; backend endpoints remain `require_admin`. No unauthenticated admin action added. | closed |
| T-29-13 | Tampering (operator process) | `docs/META-INTEGRATION-TESTING.md` | mitigate | META-03 docs document explicit scopes/env vars/linkage and mark live Meta verification as handoff with "não marcar como aprovado sem execução real". Smoke test guards required strings/boundary. | closed |
| T-29-14 | Repudiation / Operational ambiguity | IG readiness messaging | mitigate | Actionable pt-BR state copy maps ready/missing_linkage/missing_permissions/needs_reconnect/unknown to verify/reconnect guidance in UI and docs troubleshooting table/checklist. | closed |

*Status: open · closed*
*Disposition: mitigate (implementation required) · accept (documented risk) · transfer (third-party)*

---

## Accepted Risks Log

| Risk ID | Threat Ref | Rationale | Accepted By | Date |
|---------|------------|-----------|-------------|------|

No accepted risks.

---

## Security Audit Trail

| Audit Date | Threats Total | Closed | Open | Run By |
|------------|---------------|--------|------|--------|
| 2026-11-23 | 14 | 14 | 0 | gsd-security-auditor (workflow) |

### 2026-11-23 — Phase 29 Secure-Phase Audit (State B)

**Scope:** Phase 29 plans 29-01/02/03 threat models, summaries, and implemented code/docs/tests.

**Evidence reviewed:**
- Plans: `29-01-PLAN.md`, `29-02-PLAN.md`, `29-03-PLAN.md` threat registers (T-29-01..T-29-14)
- Summaries: `29-01-SUMMARY.md`, `29-02-SUMMARY.md`, `29-03-SUMMARY.md` (no `## Threat Flags`)
- Code: `backend/app/services/social/instagram_readiness.py`, `backend/app/services/social/meta_oauth.py`, `backend/app/api/v1/integrations.py`, `backend/app/api/v1/public.py`, `backend/app/api/v1/admin.py`, `backend/app/services/social/image_card.py`, `backend/app/services/social/image_media.py`, `backend/app/core/config.py`, `frontend/app/admin/integracoes/IntegrationsClient.tsx`, `frontend/lib/api.ts`
- Docs/tests: `docs/META-INTEGRATION-TESTING.md`, `backend/tests/test_integrations_instagram.py`, `backend/tests/test_ig_media_card.py`

**Result:** All 14 planned threats have mitigations present in code/docs/tests. No open threats, no accepted risks.

---

## Sign-Off

- [x] All threats have a disposition (mitigate / accept / transfer)
- [x] Accepted risks documented in Accepted Risks Log
- [x] `threats_open: 0` confirmed
- [x] `status: verified` set in frontmatter

**Approval:** verified 2026-11-23
