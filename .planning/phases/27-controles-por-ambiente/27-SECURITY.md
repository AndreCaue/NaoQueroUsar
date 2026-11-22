---
phase: 27
slug: controles-por-ambiente
status: verified
threats_open: 0
asvs_level: 1
created: 2026-11-22
---

# Phase 27 — Security

> Per-phase security contract: threat register, accepted risks, and audit trail.

---

## Trust Boundaries

| Boundary | Description | Data Crossing |
|----------|-------------|---------------|
| Deploy/env config → browser bundle | `NEXT_PUBLIC_*` values are operator-configured and embedded in the client bundle; treated as untrusted config input for navigation/render decisions. | `NEXT_PUBLIC_ADS_ENABLED`, `NEXT_PUBLIC_DONATION_URL` (public config strings) |
| Public UI → external destination | The Doações button may navigate to an operator-configured external URL in a new browser tab. | External donation URL (validated http/https only) |

---

## Threat Register

| Threat ID | Category | Component | Disposition | Mitigation | Status |
|-----------|----------|-----------|-------------|------------|--------|
| T-27-01 | Tampering / Information Disclosure (unsafe navigation) | `frontend/lib/publicEnv.ts`, `frontend/app/(public)/layout.tsx` | mitigate | `parseDonationUrl` accepts only absolute `http:`/`https:` via `new URL()`; unsafe/relative/malformed values return `null`; layout falls back to internal `/doacoes`. Unit tests cover unsafe schemes. Evidence: `frontend/lib/publicEnv.ts:15-25`, `frontend/app/(public)/layout.tsx:5,35,60-73`, `frontend/lib/publicEnv.test.ts:35-61`. | closed |
| T-27-02 | Spoofing / Tampering (reverse-tabnabbing) | `frontend/app/(public)/layout.tsx` | mitigate | External donation anchor always includes `target="_blank"` and `rel="noopener noreferrer"`. Evidence: `frontend/app/(public)/layout.tsx:61-66`. | closed |
| T-27-03 | Denial of Service (misconfiguration / broken UX) | `frontend/lib/publicEnv.ts`, `frontend/components/board/AdSlot.tsx`, `frontend/scripts/verify-ssr.ps1` | mitigate | Safe defaults: ads visible when flag absent/unknown (D-01); donation falls back to `/doacoes` when invalid (D-05); no throws on bad env. Ad gate is central in `AdSlot`; `verify-ssr.ps1` is env-aware. Evidence: `frontend/lib/publicEnv.ts:3-13,15-30`, `frontend/components/board/AdSlot.tsx:1,15`, `frontend/app/(public)/page.tsx:4,56,71,169-173`, `frontend/scripts/verify-ssr.ps1:4,28-33,54-62`. | closed |

*Status: open · closed*
*Disposition: mitigate (implementation required) · accept (documented risk) · transfer (third-party)*

---

## Accepted Risks Log

No accepted risks.

---

## Security Audit Trail

| Audit Date | Threats Total | Closed | Open | Run By |
|------------|---------------|--------|------|--------|
| 2026-11-22 | 3 | 3 | 0 | gsd-secure-phase (OpenCode) |

---

## Unregistered Threat Flags

No unregistered threat flags found in `27-01-SUMMARY.md` (`## Threat Flags` section absent).

---

## Sign-Off

- [x] All threats have a disposition (mitigate / accept / transfer)
- [x] Accepted risks documented in Accepted Risks Log
- [x] `threats_open: 0` confirmed
- [x] `status: verified` set in frontmatter

**Approval:** verified 2026-11-22
