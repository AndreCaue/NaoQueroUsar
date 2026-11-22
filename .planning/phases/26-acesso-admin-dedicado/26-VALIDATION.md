---
phase: 26
slug: acesso-admin-dedicado
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-11-22
---

# Phase 26 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | Vitest 2.1.9 + TypeScript 5.9.2 |
| **Config file** | `frontend/vitest.config.ts` |
| **Quick run command** | `cd frontend && npm test -- --run lib/adminReturnTo.test.ts` |
| **Full suite command** | `cd frontend && npm test` |
| **Estimated runtime** | ~30 seconds |

---

## Sampling Rate

- **After every task commit:** Run `cd frontend && npm test -- --run lib/adminReturnTo.test.ts` (when return-to helper exists); otherwise run targeted frontend checks relevant to touched files
- **After every plan wave:** Run `cd frontend && npm test && npm run build`
- **Before `/gsd-verify-work`:** Full suite must be green
- **Max feedback latency:** 30 seconds

---

## Per-task Verification Map

| task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| 26-01-01 | 01 | 1 | ADMN-01 | T-26-01 | `next`/return-to accepts only internal `/admin/...` paths; rejects `//`, `\\`, absolute/external URLs; fallback `/admin`; prevents `/admin/login` loop | unit | `cd frontend && npm test -- --run lib/adminReturnTo.test.ts` | ❌ W0 | ⬜ pending |
| 26-01-02 | 01 | 1 | ADMN-01 | T-26-02 | Unauthenticated admin access redirects to `/admin/login` preserving sanitized return-to; no JWT in URL; session stays in sessionStorage `nqu_admin_token` | smoke/manual | `cd frontend && npm run build` | ❌ manual | ⬜ pending |
| 26-01-03 | 01 | 1 | ADMN-01 | T-26-03 | Authenticated `/admin/login` redirects to sanitized return-to or `/admin`; logout clears session and hard-navigates to `/admin/login` | smoke/manual | `cd frontend && npm run build` | ❌ manual | ⬜ pending |
| 26-02-01 | 02 | 1 | ADMN-01 | T-26-02 | `/admin/paste` requires authenticated session for extraction flow; no embedded login form as main access path | smoke/manual | `cd frontend && npm run build` | ❌ manual | ⬜ pending |
| 26-02-02 | 02 | 1 | ADMN-02 | — | Privacy page shows discreet "Acesso administrativo" link below final disclaimer pointing to `/admin/login` | smoke/manual | `cd frontend && npm run build` | ❌ manual | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `frontend/lib/adminReturnTo.test.ts` — stubs/coverage for ADMN-01 return-to sanitization, fallback, and loop prevention
- [ ] `frontend/lib/adminReturnTo.ts` (or equivalent) — pure helper extracted for testable safe redirect handling

*Existing infrastructure partially covers phase requirements: Vitest is configured for `lib/**/*.test.ts` (node env), but there is no component/E2E harness for admin route UI flows.*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Dedicated `/admin/login` renders focused login UI (no admin nav while logged out), authenticates, and redirects to return-to/fallback | ADMN-01 | No React component/E2E harness configured; Vitest is node-only for `lib/**/*.test.ts` | Start frontend/backend, visit `/admin/login`, log in with valid admin creds; confirm redirect to `/admin` or intended `/admin/*` target |
| Unauthenticated protected admin route redirects to `/admin/login?next=...` (sanitized) | ADMN-01 | Route/guard behavior depends on browser navigation/sessionStorage | Clear sessionStorage, open `/admin/review`; confirm redirect to `/admin/login` and post-login return |
| Authenticated user visiting `/admin/login` is redirected away; logout lands on `/admin/login` | ADMN-01 | Browser session/navigation flow | Log in, open `/admin/login`; confirm redirect. Click Sair; confirm `/admin/login` |
| `/admin/paste` no longer presents login form as main flow | ADMN-01 | UI flow/manual smoke | While logged out, open `/admin/paste`; confirm redirect/login gate behavior. While logged in, confirm extraction UI is primary |
| Privacy page link "Acesso administrativo" is discreet below disclaimer and goes to `/admin/login` | ADMN-02 | Visual/placement assertion without component/E2E harness | Open `/privacidade`, scroll to below final disclaimer box; confirm small muted link text and destination |

*If none: "All phase behaviors have automated verification."*

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 30s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
