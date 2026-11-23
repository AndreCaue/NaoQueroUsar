---
phase: 27
slug: controles-por-ambiente
status: partial
nyquist_compliant: false
wave_0_complete: true
created: 2026-11-22
updated: 2026-11-22
---

# Phase 27 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | Vitest 2.1.9 |
| **Config file** | `frontend/vitest.config.ts` |
| **Quick run command** | `cd frontend && npx vitest run lib/publicEnv.test.ts lib/publicEnv.contract.test.ts` |
| **Full suite command** | `cd frontend && npm test` |
| **Estimated runtime** | ~15 seconds |

---

## Sampling Rate

- **After every task commit:** Run `cd frontend && npx vitest run lib/publicEnv.test.ts lib/publicEnv.contract.test.ts`
- **After every plan wave:** Run `cd frontend && npm test && npm run build`
- **Before `/gsd-verify-work`:** Full suite must be green; manual smoke for ads on/off and donation external/fallback
- **Max feedback latency:** 30 seconds

---

## Per-task Verification Map

| task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| 27-TBD-01 | 01 | 1 | ADS-01 | N/A | N/A (display flag) | unit | `cd frontend && npx vitest run lib/publicEnv.test.ts` | ✅ | ✅ green |
| 27-TBD-02 | 01 | 1 | ADS-01 | N/A | N/A (display flag) | unit | `cd frontend && npx vitest run lib/publicEnv.test.ts` | ✅ | ✅ green |
| 27-TBD-03 | 01 | 1 | DONA-01 | T-27-01 | Invalid/unsafe donation URLs (`javascript:`, `data:`, malformed, relative) fall back to internal `/doacoes`; no unsafe href rendered | unit | `cd frontend && npx vitest run lib/publicEnv.test.ts` | ✅ | ✅ green |
| 27-TBD-04 | 01 | 1 | DONA-01 | T-27-02 | External donation link uses `rel="noopener noreferrer"` with `target="_blank"` | unit (source contract) | `cd frontend && npx vitest run lib/publicEnv.contract.test.ts` | ✅ | ✅ green |
| 27-TBD-05 | 01 | 1 | ADS-01 | N/A | N/A (display flag contract) | unit (source contract) | `cd frontend && npx vitest run lib/publicEnv.contract.test.ts` | ✅ | ✅ green |
| 27-TBD-06 | 01 | 1 | DONA-01 | T-27-01 | Header button falls back to `/doacoes` when URL absent/invalid; no invalid destination | manual smoke | Browser check on running app with env states | N/A | ⚠️ manual-only |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ manual-only*

---

## Wave 0 Requirements

- [x] `frontend/lib/publicEnv.ts` — env parsing and donation URL validation helpers (`parseAdsEnabled`, `isAdsEnabled`, `parseDonationUrl`, `getDonationUrl`)
- [x] `frontend/lib/publicEnv.test.ts` — covers ADS-01/DONA-01 parsing/validation semantics
- [x] Update `frontend/scripts/verify-ssr.ps1` — env-aware ad assertions (enabled default vs disabled)
- [x] `frontend/lib/publicEnv.contract.test.ts` — source-contract coverage for 27-TBD-04 (layout external link attrs) and 27-TBD-05 (verify-ssr env-aware contract)

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

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies (27-TBD-06 remains manual-only browser smoke)
- [x] Sampling continuity: no 3 consecutive tasks without automated verify
- [x] Wave 0 covers all MISSING references
- [x] No watch-mode flags
- [x] Feedback latency < 30s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** partial - 27-TBD-06 escalated as manual-only

## Validation Audit 2026-11-22

| Metric | Count |
|--------|-------|
| Gaps found | 3 |
| Resolved | 2 |
| Escalated | 1 |

### Notes
- **State A audit:** VALIDATION existed but was stale (draft/TBD/pending). Implementation and tests already present for core parsing/URL safety.
- **Resolved by automation:** 27-TBD-04 covered by `frontend/lib/publicEnv.contract.test.ts` (layout donation external-link `target="_blank"` + `rel="noopener noreferrer"` + `/doacoes` fallback contract); 27-TBD-05 covered by same file (verify-ssr.ps1 `Get-AdsEnabled`, disabled values, 0-ad disabled assertion contract).
- **Escalated manual-only:** 27-TBD-06 (DONA-01) requires browser smoke to confirm real new-tab navigation and internal fallback behavior; current Vitest node infra has no DOM/browser harness and no new deps allowed.
- **Verification:** `cd frontend; npx vitest run lib/publicEnv.test.ts lib/publicEnv.contract.test.ts` → 9/9 green.
