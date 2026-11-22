---
phase: 27
slug: controles-por-ambiente
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-11-22
---

# Phase 27 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | Vitest 2.1.9 |
| **Config file** | `frontend/vitest.config.ts` |
| **Quick run command** | `cd frontend && npx vitest run lib/publicEnv.test.ts` |
| **Full suite command** | `cd frontend && npm test` |
| **Estimated runtime** | ~15 seconds |

---

## Sampling Rate

- **After every task commit:** Run `cd frontend && npx vitest run lib/publicEnv.test.ts`
- **After every plan wave:** Run `cd frontend && npm test && npm run build`
- **Before `/gsd-verify-work`:** Full suite must be green; manual smoke for ads on/off and donation external/fallback
- **Max feedback latency:** 30 seconds

---

## Per-task Verification Map

| task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| 27-TBD-01 | TBD | 1 | ADS-01 | N/A | N/A (display flag) | unit | `cd frontend && npx vitest run lib/publicEnv.test.ts` | ❌ W0 | ⬜ pending |
| 27-TBD-02 | TBD | 1 | ADS-01 | N/A | N/A (display flag) | unit | `cd frontend && npx vitest run lib/publicEnv.test.ts` | ❌ W0 | ⬜ pending |
| 27-TBD-03 | TBD | 1 | DONA-01 | T-27-01 | Invalid/unsafe donation URLs (`javascript:`, `data:`, malformed, relative) fall back to internal `/doacoes`; no unsafe href rendered | unit | `cd frontend && npx vitest run lib/publicEnv.test.ts` | ❌ W0 | ⬜ pending |
| 27-TBD-04 | TBD | 1 | DONA-01 | T-27-02 | External donation link uses `rel="noopener noreferrer"` with `target="_blank"` | unit/manual | `cd frontend && npx vitest run lib/publicEnv.test.ts` | ❌ W0 | ⬜ pending |
| 27-TBD-05 | TBD | 1 | ADS-01 | N/A | N/A (display flag) | smoke/script | `powershell -File frontend/scripts/verify-ssr.ps1` (env-aware after update) | ❌ W0 | ⬜ pending |
| 27-TBD-06 | TBD | 1 | DONA-01 | T-27-01 | Header button falls back to `/doacoes` when URL absent/invalid; no invalid destination | manual smoke | Browser check on running app with env states | N/A | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `frontend/lib/publicEnv.ts` — env parsing and donation URL validation helpers (`parseAdsEnabled`, `isAdsEnabled`, `parseDonationUrl`, `getDonationUrl`)
- [ ] `frontend/lib/publicEnv.test.ts` — covers ADS-01/DONA-01 parsing/validation semantics
- [ ] Update `frontend/scripts/verify-ssr.ps1` — env-aware ad assertions (enabled default vs disabled)

*Existing infrastructure covers framework/install; no new packages required.*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Header Doações button opens configured external URL in new tab when valid; falls back to `/doacoes` when absent/invalid | DONA-01 | Requires running app/browser to confirm navigation target, new-tab behavior, and safe fallback | Set `NEXT_PUBLIC_DONATION_URL` to valid https URL, rebuild/restart, click Doações and confirm new tab external destination; clear/invalid value and confirm internal `/doacoes` |
| Public board hides all 3 ad placements when ads disabled and shows when enabled/default | ADS-01 | Visual/layout confirmation across header/sidebar/inline placements and responsive behavior | Set `NEXT_PUBLIC_ADS_ENABLED=false`, rebuild/restart, confirm no "Espaço publicitário" placeholders in header/sidebar/inline grid; set true/unset and confirm 3 placeholders return |

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
