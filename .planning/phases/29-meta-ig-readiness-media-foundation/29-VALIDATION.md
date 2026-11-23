---
phase: 29
slug: meta-ig-readiness-media-foundation
status: validated
nyquist_compliant: true
wave_0_complete: true
created: 2026-11-23
updated: 2026-11-23
---

# Phase 29 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 9.1.1 + pytest-asyncio >=1.0.0,<2.0.0 (backend); Vitest ^2.1.9 (frontend) |
| **Config file** | `backend/pyproject.toml` (`[tool.pytest.ini_options]`, `asyncio_mode=auto`); `frontend/package.json` scripts |
| **Quick run command** | `cd backend && uv run pytest tests/test_meta_oauth_instagram.py tests/test_integrations_instagram.py tests/test_ig_media_card.py tests/test_ig_media_validation.py tests/test_public_ig_media.py tests/test_docs_meta_instagram.py -q` |
| **Full suite command** | `cd backend && uv run pytest -q` |
| **Estimated runtime** | ~60 seconds |

---

## Sampling Rate

- **After every task commit:** Run `cd backend && uv run pytest tests/test_meta_oauth_instagram.py tests/test_integrations_instagram.py tests/test_ig_media_card.py tests/test_ig_media_validation.py tests/test_public_ig_media.py tests/test_docs_meta_instagram.py -q` (or closest phase-specific subset)
- **After every plan wave:** Run `cd backend && uv run pytest -q`
- **Before `/gsd-verify-work`:** Full suite must be green
- **Max feedback latency:** 60 seconds

---

## Per-task Verification Map

| task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| 29-01-01 | 01 | 1 | META-01 | T-29-01 | Status endpoint returns additive IG readiness without tokens/secrets; FB status unaffected | integration/unit | `cd backend && uv run pytest tests/test_meta_oauth_instagram.py tests/test_integrations_instagram.py -q` | ✅ | ✅ green |
| 29-01-02 | 01 | 1 | META-02 | T-29-02 | `ig-user-id` resolved/persisted from linked Page; missing/invalid linkage maps to safe actionable pt-BR state; FB not broken | unit/integration | `cd backend && uv run pytest tests/test_meta_oauth_instagram.py tests/test_integrations_instagram.py -q` | ✅ | ✅ green |
| 29-01-03 | 01 | 1 | META-03 | — | Ops docs contain required env/scopes/manual verification checklist; no fabricated live evidence | doc smoke | `cd backend && uv run pytest tests/test_docs_meta_instagram.py -q` | ✅ | ✅ green |
| 29-02-01 | 02 | 1 | IMAG-02 | T-29-03 | Deterministic 1080x1350 JPEG sRGB <8MB card; no contacts; bundled fonts; stable hash/version | unit | `cd backend && uv run pytest tests/test_ig_media_card.py -q` | ✅ | ✅ green |
| 29-02-02 | 02 | 1 | IMAG-01 | T-29-04 | Missing/invalid IG image returns clear pt-BR validation and blocks only IG path | unit/integration | `cd backend && uv run pytest tests/test_ig_media_validation.py tests/test_public_ig_media.py -q` | ✅ | ✅ green |
| 29-02-03 | 02 | 1 | IMAG-03 | T-29-05 | Public HTTPS non-auth URL serves exact versioned image; localhost/private/auth URLs rejected; provenance available | integration | `cd backend && uv run pytest tests/test_public_ig_media.py -q` | ✅ | ✅ green |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [x] `backend/tests/test_meta_oauth_instagram.py` — META-01, META-02 coverage present (7 tests)
- [x] `backend/tests/test_integrations_instagram.py` — META-01, META-02 API/no-secret coverage present (2 tests)
- [x] `backend/tests/test_ig_media_card.py` — IMAG-02 deterministic card/hash coverage present (2 tests)
- [x] `backend/tests/test_ig_media_validation.py` — IMAG-01 validation contract coverage present (4 tests)
- [x] `backend/tests/test_public_ig_media.py` — IMAG-03 public endpoint/no-auth coverage present (3 tests)
- [x] `backend/tests/test_docs_meta_instagram.py` — META-03 doc smoke coverage present (1 test)
- [x] `backend/assets/fonts/DejaVuSans.ttf`, `backend/assets/fonts/DejaVuSans-Bold.ttf`, and `backend/assets/fonts/README.md` — deterministic vendored fonts with license/provenance
- [x] `Pillow==13.0.0` declared in backend dependencies

*All Wave 0 artifacts exist and phase-specific automated tests pass.*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Live Meta app/page/IG linkage and permission grant behavior | META-01, META-02, META-03 | Requires real Meta app credentials, Page roles/tasks, and linked IG Business/Creator account in target app mode | Follow `docs/META-INTEGRATION-TESTING.md` IG checklist: connect page, confirm IG readiness state, verify missing-linkage/missing-permissions handling, confirm reconnect flow. Record evidence separately; do not fabricate pass. |
| Meta can fetch public image URL from deployed backend | IMAG-03 | Requires publicly reachable HTTPS deployment; localhost/dev tunnels not authoritative | Deploy/stage backend with valid `MEDIA_PUBLIC_BASE_URL`, open generated image URL unauthenticated, confirm 200 JPEG and Meta-accessible public host. |

*All phase behaviors have automated verification; remaining items require live Meta/deployment environments.*

---

## Validation Sign-Off

- [x] All tasks have `<automated>` verify or Wave 0 dependencies
- [x] Sampling continuity: no 3 consecutive tasks without automated verify
- [x] Wave 0 covers all MISSING references
- [x] No watch-mode flags
- [x] Feedback latency < 60s
- [x] `nyquist_compliant: true` set in frontmatter

**Approval:** approved (automated scope) — 2026-11-23

## Validation Audit 2026-11-23

| Metric | Count |
|--------|-------|
| Gaps found | 0 |
| Resolved | 0 |
| Escalated | 0 |

**Audit notes:**
- State A audit: existing `29-VALIDATION.md` was stale (draft/pending) while phase artifacts/tests were already present.
- Verified all 6 mapped test files exist and executed: `cd backend && uv run pytest tests/test_meta_oauth_instagram.py tests/test_integrations_instagram.py tests/test_ig_media_card.py tests/test_ig_media_validation.py tests/test_public_ig_media.py tests/test_docs_meta_instagram.py -q` → **16 passed in 48.02s**.
- Requirement coverage classified as COVERED for automated scope: META-01, META-02, META-03, IMAG-01, IMAG-02, IMAG-03.
- Remaining manual-only items retained: live Meta linkage/permissions/reconnect flow and live public HTTPS Meta fetch from deployed backend.
