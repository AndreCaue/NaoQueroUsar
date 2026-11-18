---
phase: 21
slug: interface-de-chat-e-integracao-no-board
status: verified
threats_open: 0
asvs_level: 1
created: 2026-11-17
---

# Phase 21 — Security

> Per-phase security contract: threat register, accepted risks, and audit trail.

---

## Trust Boundaries

| Boundary | Description | Data Crossing |
|----------|-------------|---------------|
| browser -> public chat-search API | User-controlled NL message and untrusted JSON response cross the client/server boundary for chat search. | `ChatSearchRequest` message/page/limit in; `ChatSearchResponse` interpretation + public job results out (no contact fields). |
| chat-search API response -> UI state/render | Untrusted interpretation, guidance, limitations, and job fields are rendered and used to drive board navigation/state. | Field statuses, reasons, limitations, guidance, applied params, and `JobPublic` fields rendered as text/state. |
| chat results -> canonical detail/reveal flow | Public `JobPublic` chat items cross into the existing board detail dialog; contact reveal remains in the canonical protected detail flow only. | Job public fields and `vaga` URL selection only; no chat-side contact fetch/reveal. |

---

## Threat Register

| Threat ID | Category | Component | Disposition | Mitigation | Status |
|-----------|----------|-----------|-------------|------------|--------|
| T-21-01 | Tampering | `frontend/lib/api.ts` chatSearch request/response handling | mitigate | `chatSearch` POSTs JSON with `Content-Type: application/json` to `/api/v1/public/chat-search`, enforces `AbortSignal.timeout(15_000)`, throws `ApiError` on non-2xx via `readError`, and wraps transport/timeout failures as `ApiError` with status 0/pt-BR-safe message; server remains authoritative for validation. Evidence: `frontend/lib/api.ts:816-838`, 21-01-SUMMARY. | closed |
| T-21-02 | Information Disclosure | chat client types/state foundations | mitigate | Chat contract/types use `JobPublic` result items only and expose no `contact_*` fields in chat request/response/interpretation/result helpers; chat components do not reference contact fields or reveal endpoints. Evidence: `frontend/lib/api.ts` chat types, `frontend/components/board/chat/*` grep clean for contact/reveal, 21-01-SUMMARY/21-02-SUMMARY. | closed |
| T-21-03 | Tampering | `frontend/lib/chatApply.ts` URL mapping | mitigate | `appliedParamsToBoardFilters` routes through `normalizeFilters` (whitelisted city/sort/q normalization), forces `page: 1` and `vaga: null`; `canApplyChatToBoard` blocks degraded/non-useful apply. Evidence: `frontend/lib/chatApply.ts:5-20`, `frontend/lib/chatApply.test.ts`, 21-01-SUMMARY. | closed |
| T-21-04 | Information Disclosure | `ChatWidget`/results rendering | mitigate | Chat results render only public `JobPublic` fields (título, empresa, local, salário quando disponível) and open canonical detail via `JobDetailDialog`/`RevealContact`; no contact fields/state/fetch in chat UI. Evidence: `frontend/components/board/chat/ChatResultItem.tsx`, `ChatWidget.tsx` detail integration, 21-02-SUMMARY. | closed |
| T-21-05 | Tampering | interpretation/results UI rendering | mitigate | Server-authoritative interpretation/guidance/limitations rendered as text/JSX nodes (no `dangerouslySetInnerHTML` in chat components), with "Entendi"/status labels and limitations block; apply gated by `canApplyChatToBoard`. Evidence: `ChatInterpretation.tsx`, `ChatResultsList.tsx`, chat grep clean for dangerous HTML, 21-02-SUMMARY. | closed |
| T-21-06 | Denial of Service | send/load-more interaction flow | mitigate | Duplicate sends blocked while `isSending`; load-more scoped to active query/turn with in-flight checks and stale-response guards; pagination appends only for matching active context; retryable pt-BR error states used on failures. Evidence: `frontend/components/board/chat/ChatWidget.tsx` send/load-more guards, 21-02-SUMMARY. | closed |
| T-21-07 | Elevation of Privilege (workflow bypass) / Tampering | apply-to-board and detail layering | mitigate | Apply uses `appliedParamsToBoardFilters` + `buildBoardHref` with canonical params (`page: 1`, `vaga` cleared) via `router.replace`; detail opens in canonical dialog flow with chat minimized/preserved and `vaga` URL sync, avoiding parallel reveal/detail paths. Evidence: `frontend/components/board/chat/ChatWidget.tsx:65,174-179,234`, 21-02-SUMMARY. | closed |

*Status: open / closed*
*Disposition: mitigate (implementation required) / accept (documented risk) / transfer (third-party)*

---

## Accepted Risks Log

No accepted risks.

---

## Security Audit Trail

| Audit Date | Threats Total | Closed | Open | Run By |
|------------|---------------|--------|------|--------|
| 2026-11-17 | 7 | 7 | 0 | gsd-secure-phase (phase 21 audit from PLAN/SUMMARY/code evidence) |

### Security Audit 2026-11-17
| Metric | Count |
|--------|-------|
| Threats found | 7 |
| Closed | 7 |
| Open | 0 |

- Input state: **B** (no prior `*-SECURITY.md`; `*-PLAN.md` and `*-SUMMARY.md` present for phase 21).
- Threat register built from `<threat_model>` blocks in `21-01-PLAN.md` (T-21-01..03) and `21-02-PLAN.md` (T-21-04..07).
- SUMMARY threat flags: none found in `21-01-SUMMARY.md` / `21-02-SUMMARY.md`.
- Verification basis: implementation evidence in `frontend/lib/api.ts`, `frontend/lib/chatApply.ts`, `frontend/lib/chatApply.test.ts`, and `frontend/components/board/chat/*`; summaries report passing `npm --prefix frontend run test:chat` (6 tests) and lint checks.
- Gate result: `threats_open: 0` (no auditor spawn required).

---

## Sign-Off

- [x] All threats have a disposition (mitigate / accept / transfer)
- [x] Accepted risks documented in Accepted Risks Log
- [x] `threats_open: 0` confirmed
- [x] `status: verified` set in frontmatter

**Approval:** verified 2026-11-17
