---
phase: 29
slug: meta-ig-readiness-media-foundation
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-11-23
---

# Phase 29 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 9.1.1 + pytest-asyncio >=1.0.0,<2.0.0 (backend); Vitest ^2.1.9 (frontend) |
| **Config file** | `backend/pyproject.toml` (`[tool.pytest.ini_options]`, `asyncio_mode=auto`); `frontend/package.json` scripts |
| **Quick run command** | `cd backend && uv run pytest tests/test_meta_oauth_security.py -q` |
| **Full suite command** | `cd backend && uv run pytest -q` |
| **Estimated runtime** | ~60 seconds |

---

## Sampling Rate

- **After every task commit:** Run `cd backend && uv run pytest tests/test_meta_oauth_instagram.py tests/test_ig_media_card.py -q` (or closest phase-specific subset)
- **After every plan wave:** Run `cd backend && uv run pytest -q`
- **Before `/gsd-verify-work`:** Full suite must be green
- **Max feedback latency:** 60 seconds

---

## Per-task Verification Map

| task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| 29-01-01 | 01 | 1 | META-01 | T-29-01 | Status endpoint returns additive IG readiness without tokens/secrets; FB status unaffected | integration/unit | `cd backend && uv run pytest tests/test_meta_oauth_instagram.py -q` | ❌ W0 (created as stub in 29-01 Task 1) | ⬜ pending |
| 29-01-02 | 01 | 1 | META-02 | T-29-02 | `ig-user-id` resolved/persisted from linked Page; missing/invalid linkage maps to safe actionable pt-BR state; FB not broken | unit/integration | `cd backend && uv run pytest tests/test_meta_oauth_instagram.py tests/test_integrations_instagram.py -q` | ❌ W0 (stubs created in 29-01 Task 1; fleshed out in Task 3) | ⬜ pending |
| 29-01-03 | 01 | 1 | META-03 | — | Ops docs contain required env/scopes/manual verification checklist; no fabricated live evidence | doc smoke | `cd backend && uv run pytest tests/test_docs_meta_instagram.py -q` | ❌ W0 | ⬜ pending |
| 29-02-01 | 02 | 1 | IMAG-02 | T-29-03 | Deterministic 1080x1350 JPEG sRGB <8MB card; no contacts; bundled fonts; stable hash/version | unit | `cd backend && uv run pytest tests/test_ig_media_card.py -q` | ❌ W0 (created as stub in 29-02 Task 1) | ⬜ pending |
| 29-02-02 | 02 | 1 | IMAG-01 | T-29-04 | Missing/invalid IG image returns clear pt-BR validation and blocks only IG path | unit/integration | `cd backend && uv run pytest tests/test_ig_media_validation.py tests/test_public_ig_media.py -q` | ❌ W0 (stubs created in 29-02 Task 1; fleshed out in Task 3) | ⬜ pending |
| 29-02-03 | 02 | 1 | IMAG-03 | T-29-05 | Public HTTPS non-auth URL serves exact versioned image; localhost/private/auth URLs rejected; provenance available | integration | `cd backend && uv run pytest tests/test_public_ig_media.py -q` | ❌ W0 (stub created in 29-02 Task 1; fleshed out in Task 3) | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `backend/tests/test_meta_oauth_instagram.py` — META-01, META-02 stub created in 29-01 Task 1; full coverage in 29-01 Task 3
- [ ] `backend/tests/test_integrations_instagram.py` — META-01, META-02 stub created in 29-01 Task 1; full coverage in 29-01 Task 3
- [ ] `backend/tests/test_ig_media_card.py` — IMAG-02 stub created in 29-02 Task 1; full coverage in 29-02 Task 3
- [ ] `backend/tests/test_ig_media_validation.py` — IMAG-01 stub created in 29-02 Task 1; full coverage in 29-02 Task 3
- [ ] `backend/tests/test_public_ig_media.py` — IMAG-03 stub created in 29-02 Task 1; full coverage in 29-02 Task 3
- [ ] `backend/tests/test_docs_meta_instagram.py` — covers META-03 checklist presence (lightweight doc assertion, created in 29-03 Task 2)
- [ ] `backend/assets/fonts/DejaVuSans.ttf`, `backend/assets/fonts/DejaVuSans-Bold.ttf`, and `backend/assets/fonts/README.md` — deterministic vendored fonts with license/provenance (29-02 Task 1)
- [ ] Framework/install: `cd backend && uv add "Pillow==13.0.0"` (if not already declared; declared in 29-01 Task 1)

*Wave 0 stubs are created early in plan order so every per-task `<automated>` verify command is executable at its point in the plan.*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Live Meta app/page/IG linkage and permission grant behavior | META-01, META-02, META-03 | Requires real Meta app credentials, Page roles/tasks, and linked IG Business/Creator account in target app mode | Follow `docs/META-INTEGRATION-TESTING.md` IG checklist: connect page, confirm IG readiness state, verify missing-linkage/missing-permissions handling, confirm reconnect flow. Record evidence separately; do not fabricate pass. |
| Meta can fetch public image URL from deployed backend | IMAG-03 | Requires publicly reachable HTTPS deployment; localhost/dev tunnels not authoritative | Deploy/stage backend with valid `MEDIA_PUBLIC_BASE_URL`, open generated image URL unauthenticated, confirm 200 JPEG and Meta-accessible public host. |

*If none: "All phase behaviors have automated verification."*

---

## Validation Sign-Off

- [x] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [x] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 60s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending