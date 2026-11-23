# Project Research Summary

**Project:** EmpregaNoix
**Domain:** Subsequent milestone (v1.5) — Instagram job-post publishing integration in admin review, reusing existing Meta/Facebook foundation
**Researched:** 2026-11-23
**Confidence:** HIGH

## Executive Summary

EmpregaNoix v1.5 adds Instagram publishing to the existing admin review flow, alongside the already-shipped Facebook/Meta integration. Experts build this kind of integration by extending the existing social publishing foundation — not by adding a second social stack. The recommended approach is to reuse the current FastAPI + SQLAlchemy async + Postgres + httpx + worker/cron/idempotency patterns, add Pillow for deterministic fallback job-card generation, and expose generated images through a public backend URL that Meta can fetch. Instagram Content Publishing is a two-step Graph API workflow (create media container, poll status, publish), so the architecture must model container lifecycle and ambiguity explicitly rather than copying the Facebook single-call publish path.

The recommended strategy is provider-aware but operationally isolated: one `social_posts` record per `(job_id, provider)`, independent draft/status/retry UX per platform, independent pipeline execution, and shared safety primitives (claim/lock, sanitized logs, idempotency, error taxonomy). Facebook must remain behaviorally unchanged. Instagram-specific constraints drive most product decisions: image is mandatory, image URL must be publicly reachable by Meta at publish time, captions have 2200-char/30-hashtag limits, caption links are not clickable, and ambiguous publish outcomes must never auto-retry into duplicates.

Key risks are integration-shaped, not infrastructure-shaped. The main mitigations are: persist container/media IDs and treat ambiguous publish as manual-check; validate/serve public JPEG media with stable URLs; verify Meta permissions, Page-to-IG linkage, and App Review/access assumptions before live rollout; classify 429/auth/media/rate-limit failures distinctly; and keep Facebook and Instagram state/actions fully decoupled in API, worker, and UI. Several decisions are intentionally left for discuss-phase (image origin, card format/storage/serving details, image generation strategy, token renewal/alert strategy) — research provides recommendations, not final product choices.

## Key Findings

### Recommended Stack

The milestone needs minimal stack additions. Keep the existing EmpregaNoix stack and social foundation; add only what Instagram uniquely requires. See [STACK.md](./STACK.md) for full details.

**Core technologies (reuse, no change):**
- **FastAPI 0.143.0 + SQLAlchemy 2.1.4 async + asyncpg 0.32.0 + Neon Postgres**: extend existing social models/endpoints — no new service boundary.
- **httpx 0.28.1**: reuse for Graph API container/publish/status/rate-limit calls following the existing publisher pattern.
- **Existing worker/cron + claim/lock/retry/idempotency**: extend for provider-aware processing; do not add Celery/Redis/queue infra.
- **Next.js 16 + React 19 + Tailwind 4**: extend review dialog/integrations UI; no new frontend package required for core flow.

**New/targeted additions:**
- **Pillow 13.0.0**: deterministic backend fallback job-card generation (1080x1080 or 1080x1350 JPEG, sRGB, <8MB). Bundle fonts in repo; do not depend on OS fonts.
- **python-multipart (conditional, only if upload chosen)**: add only if review-stage admin image upload becomes part of v1.5 scope.
- **Public backend media endpoint**: serve DB-backed image bytes at a stable, unguessable HTTPS URL for Meta fetch. No object-storage SDK by default at 100-500 jobs/month.
- **Meta Graph API config-driven**: keep `META_GRAPH_VERSION` configurable; project currently on `v21.0`, latest verified `v27.0`. Do not hardcode a bump without deliberate test.

**Critical version/constraint notes:**
- Instagram image containers require a **publicly accessible JPEG URL**; data URLs, localhost, auth-gated, or ephemeral disk URLs are unsafe.
- Graph API latest verified `v27.0`; `v21.0` remains valid until 2027-01-21. Keep version config-driven.
- Meta publish-limit docs are inconsistent; treat `GET /{ig-user-id}/content_publishing_limit` as runtime authority.

### Expected Features

v1.5 succeeds when an admin can safely publish an approved job to Instagram from the same review workflow, with clear platform-specific controls and no Facebook regression. See [FEATURES.md](./FEATURES.md) for full matrix.

**Must have (table stakes):**
- **Instagram section in review alongside Facebook** — same job context, no parallel review system.
- **Per-vaga Instagram toggle** — explicit opt-in/out; no hidden auto-posting.
- **Editable caption prefilled from job data** — Instagram-specific draft, not a blind Facebook copy.
- **2200-char counter + >30 hashtag warning** — prevent avoidable Meta validation failures.
- **No-clickable-link handling + "link na bio" CTA** — Instagram captions do not render clickable URLs.
- **Image required guardrail + preview** — image is mandatory for IG Content Publishing.
- **Per-platform publish status and independent publish execution** — Facebook failure must not block Instagram and vice versa.
- **Visible outcome, error visibility/retry, audit trail** — permalink/external ID when available, safe actionable errors, token-free logs.

**Should have (competitive):**
- **Generated fallback job card (1080x1080 or 1080x1350 JPEG)** — removes "no image" blocker for one-admin workflow.
- **IG-tuned caption prefill** — concise pt-BR copy, "link na bio", hashtag-aware, no fake clickable CTA.
- **Pre-publish validation summary / image provenance / safe ambiguity guard** — saves quota and prevents duplicate posts.

**Defer (v2+ / out of scope):**
- **Stories/Reels/carousel/video, scheduling UI, analytics/insights, comments/DM inbox, multiple IG accounts** — explicitly out of v1.5 scope or high complexity/low milestone value.

### Architecture Approach

Extend the existing social domain with provider-aware records and isolated adapters; do not create a parallel Instagram subsystem. See [ARCHITECTURE.md](./ARCHITECTURE.md) for component map and build order.

**Major components:**
1. **Meta connection/readiness extension (`social_accounts`, `meta_oauth`, integrations UI)** — reuse existing Page token/OAuth flow; resolve/store `ig_user_id` from linked Page; expose IG readiness/reconnect state.
2. **Provider-aware social records + image assets (`social_posts`, `social_post_logs`, `social_media_assets`)** — keep unique `(job_id, provider)`; add IG caption/media/container/permalink fields; persist durable public image asset metadata/bytes.
3. **Instagram publisher + provider-aware pipeline (`instagram.py`, `publish_pipeline.py`)** — implement two-step container/poll/publish behind shared result contract; preserve Facebook path; classify transient/permanent/ambiguous safely.
4. **Review/admin/public API + UI (`admin.py`, `public.py`, review dialog, integrations, api.ts)** — independent IG draft/status/retry actions, public image serving endpoint, and no-regression Facebook UX.

**Key patterns:**
- **Provider dispatch, shared core:** explicit FB/IG dispatch with shared claim/log/retry/idempotency helpers.
- **Durable public media:** canonical opaque public URL backed by durable storage (DB bytea acceptable at current scale; avoid ephemeral disk).
- **Idempotent IG lifecycle:** persist `external_container_id`; if ambiguous after publish, reconcile/check before any retry.

### Critical Pitfalls

Top risks from [PITFALLS.md](./PITFALLS.md) — these should drive roadmap sequencing and acceptance criteria.

1. **Treating Instagram as "Facebook with an image"** — model container create/poll/publish as a stateful workflow; only publish `FINISHED` containers; persist container status/IDs.
2. **Image URL not publicly fetchable by Meta** — require public HTTPS JPEG URL with no auth; validate format/size/aspect; ensure URL lifetime covers review/schedule/retry/Meta fetch; never use localhost/private/ephemeral URLs.
3. **Missing permissions or Page→IG linkage assumptions** — extend OAuth scopes, resolve/store `ig_user_id`, verify permissions/roles/tasks, and document App Review/Advanced Access assumptions before rollout.
4. **Duplicate posts from ambiguous retries/double-submit** — never auto-retry ambiguous outcomes; check existing external/container IDs before republish; keep manual retry idempotent.
5. **FB/IG UI-status coupling causes regressions** — separate per-platform draft/status/actions/errors; IG validation must not block Facebook; site approve remains site-first and best-effort per social provider.

## Implications for Roadmap

Based on research, suggested phase structure:

### Phase 1: Meta/IG Readiness & Media Contract
**Rationale:** Permissions, Page→IG linkage, and public image fetchability are hard blockers. Nothing else is safe to build on top until the system can identify the IG account and serve a Meta-fetchable image URL.
**Delivers:** IG-capable OAuth scope/config plumbing, `ig_user_id` resolution/persistence, integrations readiness UI, image asset model/storage strategy, public image serving endpoint, and manual Meta/App Review checklist.
**Addresses:** IG account linkage, image required guardrail foundation, token/permission visibility.
**Avoids:** Pitfall 2 (unfetchable image URL), Pitfall 3 (permissions/linkage assumptions), Pitfall 6 (token/reconnect blind spots).
**Needs discuss-phase decisions:** image origin, card format/storage/serving, image generation strategy, token renewal/alert strategy.

### Phase 2: Instagram Draft & Review Experience
**Rationale:** Once readiness/media primitives exist, the admin needs a safe review surface before publish automation. This isolates UX/validation from publish-side Meta behavior and protects the Facebook flow.
**Delivers:** Instagram section in review dialog, per-vaga toggle, editable caption prefill, 2200 counter, >30 hashtag warning, "link na bio" CTA, image preview/source selection, provider-aware draft/status API, and per-platform UI state.
**Uses:** Next.js/React/Tailwind existing admin patterns; FastAPI/Pydantic validation; Pillow-generated fallback card when selected.
**Implements:** Provider-aware review UI and draft persistence.
**Avoids:** Pitfall 7 (FB/IG coupling), anti-feature of reusing Facebook caption unchanged, clickable-link UX mistake.

### Phase 3: Independent Publish Pipeline & Idempotency
**Rationale:** Publishing is the highest-risk behavior: two-step IG workflow, ambiguity, retries, rate limits, and duplicate-post risk. It should build on stable draft/media/readiness contracts.
**Delivers:** `InstagramPublisher`, provider-aware pipeline dispatch, container create/poll/publish, idempotent resume/reconcile rules, retry/backoff/error taxonomy, rate-limit handling, permalink/ID persistence, and independent FB/IG worker processing.
**Uses:** httpx, existing worker/cron, `PublishResult` contract, DB claim/lock/idempotency.
**Implements:** Instagram publish adapter and shared pipeline core.
**Avoids:** Pitfall 1 (single-call assumption), Pitfall 4 (duplicates/ambiguous retry), Pitfall 5 (rate-limit storms), Pitfall 6 (auth failures misclassified).

### Phase 4: Hardening, Observability & Regression Verification
**Rationale:** The integration is operationally sensitive; "works once" is insufficient. Final work should prove no Facebook regression, confirm safe failure modes, and document operator/manual verification.
**Delivers:** Unit/integration/mock coverage for IG states, FB regression tests, structured sanitized logs, admin diagnostics/status polish, manual Meta checklist/runbook, and reconciliation paths for ambiguous/rate-limited/token failures.
**Addresses:** Audit trail, error recovery, operational confidence.
**Avoids:** Security/log leakage, silent token expiry, duplicate-post recovery gaps, unverified App Review assumptions.

### Phase Ordering Rationale

- **Dependencies first:** IG readiness (`ig_user_id`, permissions) and public image URL are prerequisites for real publish; draft UX depends on image/media contracts; publish depends on draft/readiness/media.
- **Risk isolation:** Keep risky Meta publish behavior after schema/UI contracts are stable; isolate FB regression risk by refactoring pipeline behind provider dispatch with characterization tests.
- **Architecture fit:** The existing `social_posts` per-provider model and worker pipeline naturally support incremental extension: readiness/model → UI/draft → publisher/pipeline → hardening.
- **Pitfall alignment:** The highest-severity pitfalls (image fetchability, permissions/linkage, container lifecycle, ambiguity duplicates, FB coupling) map directly to earlier phases so they are prevented by design, not patched late.

### Research Flags

Phases likely needing deeper research during planning:
- **Phase 1:** Meta App Review/Advanced Access, permission/task/role requirements, and Page→IG linkage edge cases must be verified against current Meta dashboard/app mode; image hosting/storage choice depends on deploy durability.
- **Phase 3:** Instagram container polling, error code/subcode mapping, `content_publishing_limit` behavior, and ambiguous-outcome reconciliation need careful implementation research/tests against current Graph behavior.

Phases with standard patterns (skip research-phase):
- **Phase 2:** Review UI extension, form validation, counters/warnings, and provider-aware CRUD follow established in-repo patterns.
- **Phase 4:** Test hardening, logging sanitization, and regression verification follow existing project/testing conventions.

## Confidence Assessment

| Area | Confidence | Notes |
|------|------------|-------|
| Stack | HIGH | Existing stack fit is clear from codebase; Pillow/Meta Graph core facts verified. Minor uncertainty on python-multipart need and deploy-specific image hosting. |
| Features | HIGH | Table stakes are strongly constrained by Meta platform behavior and existing EmpregaNoix review workflow. Some UX details (default toggle, image source) remain product decisions. |
| Architecture | HIGH | Direct code inspection gives high confidence for integration points; IG Graph two-step behavior is verified but some endpoint semantics still warrant implementation-time doc check. |
| Pitfalls | HIGH | Critical pitfalls are grounded in official Meta docs and current codebase risks (single-call FB pattern, ambiguity, coupling). App Review/PPA edge cases remain MEDIUM. |

**Overall confidence:** HIGH

### Gaps to Address

- **Image origin (discuss-phase decision):** logo, generated card, upload, or combination. **Recommendation:** ship deterministic generated fallback card first; design asset model to allow future upload/logo sources.
- **Card format/storage/serving (discuss-phase decision):** 1080x1080 vs 1080x1350, DB bytea vs object storage, public URL shape/TTL. **Recommendation:** 1080x1350 default for job text, JPEG sRGB <8MB, DB-backed asset + opaque public backend URL for MVP; revisit object storage if ops/scale demand.
- **Image generation strategy (discuss-phase decision):** Pillow templates vs browser rendering/service. **Recommendation:** Pillow with bundled fonts in backend; avoid Playwright/HTML-to-image in v1.5.
- **Token renewal/alert strategy (discuss-phase decision):** current system has reconnect/verify patterns but no proactive expiry alerting policy. **Recommendation:** map auth failures to `needs_reconnect`, surface admin warnings, and define lightweight expiry/health check during implementation.
- **Meta permission/App Review verification (must confirm before live rollout):** confirm current app mode, required permissions (`instagram_basic`, `instagram_content_publish`, `pages_read_engagement`; role-dependent ads permissions), Page tasks/roles, PPA behavior, and whether Advanced Access/Review applies.
- **Graph version bump:** `v21.0` works now; `v27.0` latest verified. **Recommendation:** keep config-driven, test bump deliberately, do not couple v1.5 delivery to a version jump.
- **Rate-limit authority:** Meta docs conflict on daily publish cap. **Recommendation:** never hardcode; query `content_publishing_limit` and classify 2207042 as blocked/non-storming with clear operator guidance.

## Sources

### Primary (HIGH confidence)
- `.planning/research/STACK.md` — stack additions, Meta endpoints/constraints, image serving/generation recommendations
- `.planning/research/FEATURES.md` — table stakes, differentiators, anti-features, UX expectations
- `.planning/research/ARCHITECTURE.md` — component boundaries, data flow, build order, schema impacts
- `.planning/research/PITFALLS.md` — critical pitfalls, prevention, recovery, phase mapping
- `.planning/PROJECT.md` — v1.5 scope, guardrails, open decisions, constraints
- [Meta Content Publishing](https://developers.facebook.com/docs/instagram-platform/content-publishing) — two-step flow, permissions, public image URL, rate/status behavior
- [Meta IG User Media](https://developers.facebook.com/docs/instagram-platform/instagram-graph-api/reference/ig-user/media) — image specs, caption limits, container behavior
- [Meta IG User Media Publish](https://developers.facebook.com/docs/instagram-platform/instagram-graph-api/reference/ig-user/media_publish) — publish endpoint/constraints
- [Meta Graph API Changelog](https://developers.facebook.com/docs/graph-api/changelog/) — version currency (`v27.0` latest, `v21.0` availability)
- [Pillow 13.0.0 release](https://pillow.readthedocs.io/en/latest/releasenotes/13.0.0.html) / [PyPI Pillow](https://pypi.org/project/pillow/) — version/Python support
- [FastAPI Custom Response](https://fastapi.tiangolo.com/advanced/custom-response/) — public image bytes serving pattern

### Secondary (MEDIUM confidence)
- [Meta error codes](https://developers.facebook.com/docs/instagram-platform/instagram-graph-api/reference/error-codes) — error/subcode handling guidance; verify specific mappings during implementation
- [Meta App Review / permissions overview](https://developers.facebook.com/docs/instagram-platform/app-review) — access/review expectations depend on app mode and roles

### Tertiary (LOW confidence)
- None — no single-source/weak claims retained without mitigation; unresolved items are listed as gaps.

---
*Research completed: 2026-11-23*
*Ready for roadmap: yes*
