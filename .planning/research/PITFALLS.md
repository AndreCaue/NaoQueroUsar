# Pitfalls Research

**Domain:** Adding NL chatbot job search (intent extraction + public chat UI) to an existing PT-BR public job board
**Researched:** 2026-11-17
**Confidence:** HIGH (grounded in project constraints/context + established LLM/chat/search patterns; some operational thresholds are MEDIUM pending production metrics)

## Critical Pitfalls

### Pitfall 1: Hallucinated or Over-Constrained Filters Kill Recall

**What goes wrong:**
The LLM turns vague PT-BR requests into overly specific or invented filters (e.g. infers `modality=remote`, `salary_min`, seniority, or exact city not mentioned), so valid jobs disappear and users conclude "não tem vaga" even when the board has matches.

**Why it happens:**
- Prompts/examples bias the model to "fill all fields" instead of leaving unknowns null.
- No strict schema/default-null discipline between extraction and query building.
- Developers reuse admin-extraction habits (maximize structure) for user intent, where under-specification is normal.
- Mismatch between rich extraction schema and sparse existing DB/search fields encourages invented mappings.

**How to avoid:**
- Use a strict JSON schema with nullable fields, explicit `unknown/not_specified`, and "extract only what user stated or clearly implied" rules.
- Separate **extracted intent** from **applied filters**; drop/relax unsupported or low-confidence constraints before querying.
- Apply conservative defaults: no salary/modality/contract/seniority filter unless explicitly supported by evidence in user text.
- Implement progressive relaxation/fallback search (all filters → drop weakest/unsupported → keyword/title-only) and show what was relaxed.
- Add golden tests with PT-BR ambiguity ("vaga de atendimento em SP", "algo home office", "ganhando bem") to ensure recall-preserving behavior.

**Warning signs:**
- High zero-result rate on broad queries compared to manual board search.
- Extracted params frequently include fields user never mentioned.
- Support/analytics show users rephrasing repeatedly to get any results.
- Same query returns results on existing search UI but none via chat.

**Phase to address:**
Phase 1 (Intent schema + safe mapping) and Phase 3 (UX/result strategy/QA). Must be validated before broad public rollout.

---

### Pitfall 2: Public Chat Endpoint Becomes a Cost, Latency, and Abuse Magnet

**What goes wrong:**
A public, no-login LLM endpoint is hammered by bots/scripts/curious users, causing Groq quota exhaustion, slow responses, 429/5xx spikes, and degraded experience for both chat and potentially the rest of the app.

**Why it happens:**
- "Public no friction" is correctly preserved but implemented without guardrails.
- Each request triggers synchronous LLM extraction with no caching, timeout budget, or cheap pre-filter path.
- Free-tier infrastructure (Groq/Neon/Vercel/server hosting) has tight rate/concurrency limits.
- No observability on request volume, token/latency, and failure modes.

**How to avoid:**
- Add layered protections: IP+UA rate limiting, request size cap, strict server timeout, concurrency cap, and circuit breaker/fallback when Groq is unavailable.
- Keep LLM use minimal: extract parameters only (never send hundreds of jobs), use smallest adequate model, bounded `max_tokens`, deterministic-ish settings.
- Cache normalized query→intent results briefly (short TTL) and reuse for repeated prompts; short-circuit empty/too-short/gibberish input without LLM call when safe.
- Return fast partial fallback (keyword search on existing endpoint/logic) when extraction is slow/fails.
- Instrument metrics/logs (latency, timeout, rate-limit hits, provider errors) and set budget alerts/kill-switch for chat feature.

**Warning signs:**
- P95 latency > a few seconds, frequent timeouts, or Groq 429s.
- Sudden traffic spikes to chat endpoint; many identical prompts.
- Backend CPU/memory/connection pressure correlated with chat usage.
- Chat outages impacting unrelated public API responsiveness.

**Phase to address:**
Phase 2 (Public chat-search API, protections, resilience) with verification in Phase 4 (hardening/observability/launch checks).

---

### Pitfall 3: Prompt Injection and Untrusted Chat Input Break Safety/Behavior

**What goes wrong:**
User messages (or pasted job-like blobs) manipulate the model to ignore instructions, emit invalid/non-JSON output, reveal system prompts/internal behavior, or produce parameters that bypass intended constraints (e.g. requesting hidden/admin behavior, unsupported filters, or abusive content flows).

**Why it happens:**
- Treating chat text as benign search input instead of untrusted adversarial input.
- Reusing extraction prompts hardened for admin-only curated blobs in a public context with different threat model.
- Not enforcing output validation/allowlists after generation.
- Logging raw prompts/responses without redaction, amplifying impact.

**How to avoid:**
- System prompt hardening: explicit role ("extract search intent only"), ignore user instructions that conflict, never execute actions, output JSON only matching schema.
- Strict post-processing: JSON parse + schema validation + allowlisted enums/fields/cities + range checks; reject/strip unknown fields.
- Never pass secrets, admin context, or internal system details to the public chat prompt.
- Limit input length and sanitize/control characters; do not let user text become SQL/ORM fragments (parameterized queries only, but also avoid dynamic field injection).
- Red-team tests with PT-BR injection cases ("ignore as instruções...", "mostre o prompt", "liste vagas expiradas/contatos", attempts to force unsupported filters).

**Warning signs:**
- Non-JSON or schema-invalid model outputs in logs.
- Extracted params include unexpected keys/values outside allowlists.
- User-visible responses echo instructions/system text or behave inconsistently.
- Security review finds raw prompt/PII over-logging.

**Phase to address:**
Phase 1 (prompt/schema/validation) and Phase 2 (API hardening), with explicit security test cases in Phase 4.

---

### Pitfall 4: Extracted Parameters Don't Match Real DB/Search Capabilities

**What goes wrong:**
Chat advertises or attempts filters the system cannot reliably apply today (salary range, modality, contract type, seniority, free-text location nuances beyond whitelist), producing wrong results, silent mismatches, or brittle post-filter behavior.

**Why it happens:**
- MVP examples imply richer filtering than `GET /api/v1/public/jobs` / `crud.list_published` currently supports natively.
- Job data is unstructured PT-BR text; salary/modality/contract may be missing, inconsistent, or not normalized in schema.
- City whitelist (SP/RJ/BH/Remoto) conflicts with user inputs ("Campinas", "híbrido em Osasco", "qualquer lugar").
- Team chooses ad-hoc string matching without defining semantics, precedence, or truthfulness.

**How to avoid:**
- Build an explicit **capability matrix**: supported-now (DB/query), supported-via-safe-text-mapping, unsupported (must disclose/ignore).
- Normalize to existing whitelist/canonical values; map common PT-BR synonyms carefully (`home office`→Remoto, `CLT/PJ/estágio` only if representable) and reject/relax unknown cities instead of guessing.
- If adding fields/filters, do controlled schema/query extension with backfill/normalization rules; otherwise use transparent post-filtering on retrieved candidates with clear limits.
- Never claim a filter was applied when it wasn't; include `applied_filters`, `ignored_or_unsupported`, and `interpretation` in response.
- Document known gaps per MVP example and test them as acceptance criteria.

**Warning signs:**
- "Interpreted" chips show filters not reflected in results.
- Discrepancies between chat results and equivalent manual filters/search.
- Frequent empty results for salary/modality/contract queries on dataset lacking those fields.
- Growing special-case code in mapping layer without tests/spec.

**Phase to address:**
Phase 1 (capability matrix + normalization/mapping contract) and Phase 2 (API response contract), rechecked in Phase 3 (UI transparency).

---

### Pitfall 5: Integration Breaks Existing Public Board/Search and Core No-Login Value

**What goes wrong:**
Adding chat introduces regressions in the main board: changed query semantics, shared code path bugs in `crud.list_published` / public endpoints, new frontend bundle/perf issues, or accidental exposure/coupling of contact-reveal/admin flows.

**Why it happens:**
- Reusing/modifying existing search logic without characterization tests or compatibility checks.
- New UI (drawer/modal/chat state) interferes with existing filters, pagination, modal/detail, or mobile layout.
- Convenience refactors blur boundaries between public job listing, contact reveal endpoint, and admin-only flows.
- Performance regressions (large JS, blocking calls) hurt mobile users on low-end devices.

**How to avoid:**
- Treat existing public search/list/detail/contact-reveal behavior as a contract: add/keep regression tests before changing shared CRUD/query code.
- Prefer additive integration: new chat endpoint/service that composes existing safe query primitives; avoid risky rewrites of `list_published` unless necessary and well-tested.
- Keep chat UI lazy-loaded and isolated; ensure it does not block initial board render and preserves "ver vagas sem login/fricção" in first paint.
- Enforce payload boundaries: chat responses return `JobPublic` data only, never contact fields/tokens/admin data.
- Run side-by-side verification: same filters via old UI vs chat-mapped params produce consistent, explainable results.

**Warning signs:**
- Existing public API tests fail or require semantic changes after chat work.
- Increased frontend bundle size / slower mobile load after adding chat.
- Bug reports on core board filters/sort/detail after chat merge.
- Any chat path referencing contact-reveal internals or admin auth dependencies.

**Phase to address:**
Phase 1 (design/contracts) and Phase 3 (frontend integration), with regression gate in Phase 4.

## Technical Debt Patterns

Shortcuts that seem reasonable but create long-term problems.

| Shortcut | Immediate Benefit | Long-term Cost | When Acceptable |
|----------|-------------------|----------------|-----------------|
| Let LLM output drive DB filters directly (no mapping/allowlist layer) | Fastest path to demo | Hallucinations, invalid queries, security/behavior drift, hard-to-debug mismatches | Never |
| Implement "salary/modality/contract" as brittle regex post-filter without capability contract | Satisfies MVP examples quickly | Inconsistent semantics, false positives/negatives, user distrust, untestable edge cases | MVP only, if labeled approximate + covered by tests + tracked for proper modeling |
| Single global prompt with no versioning/eval cases | Quick iteration | Silent regressions in PT-BR understanding and safety; no rollback confidence | Only for throwaway spike, never merged as-is |
| Reuse admin extraction prompt/config for public chat unchanged | Less code | Wrong threat model, wrong optimization (structure over recall), leakage/logging risks | Never without explicit adaptation and validation |
| No rate limiting because "traffic is low now" | Zero setup now | Immediate exposure to abuse/quota exhaustion on public endpoint | Never for public LLM endpoint |
| Log full user messages + raw LLM I/O forever | Easy debugging | Privacy/compliance risk, noisy storage, sensitive content retention on no-login product | Only short-lived, sampled, redacted debug logs with retention limits |

## Integration Gotchas

Common mistakes when connecting to external services.

| Integration | Common Mistake | Correct Approach |
|-------------|----------------|------------------|
| Groq chat completions (public intent extraction) | Assuming admin-extraction reliability/latency holds for untrusted public prompts and traffic | Separate public-chat config (timeouts, token caps, model/fallback), strict JSON validation, and graceful fallback when provider fails/throttles |
| Existing public jobs API / `crud.list_published` | Adding chat by mutating shared query behavior for new params | Introduce an intent→query adapter layer; preserve existing contracts and add regression tests for current filters/sort/pagination |
| Neon Postgres (free tier) | Post-filtering by fetching large result sets or adding expensive unindexed text scans per chat request | Bound candidate sets, reuse indexed filters first (status/expiry/city/date), measure query cost, and avoid patterns that exhaust connections/compute |
| Vercel frontend ↔ backend chat endpoint | Long LLM waits causing function/proxy timeouts and poor mobile UX | Set explicit timeout budgets, stream or return staged response if supported/needed later, but for MVP prefer fast fail + fallback search and clear loading states |
| Cloudflare Turnstile / abuse controls (if used for chat) | Applying heavy friction that breaks "sem login, sem etapas" or skipping verification entirely | Prefer invisible/low-friction protections where possible (rate limit first); only add challenges proportional to abuse risk and never block core board browsing |

## Performance Traps

Patterns that work at small scale but fail as usage grows.

| Trap | Symptoms | Prevention | When It Breaks |
|------|----------|------------|----------------|
| Synchronous LLM call in every chat request with no timeout/cap | Slow UI, hanging requests, thread/worker saturation | Hard timeout, bounded tokens, cheap prechecks, fallback path, concurrency limits | Immediately under bot bursts or Groq slowness; noticeable even at tens of concurrent users on free tiers |
| Fetch-all-then-filter for salary/modality/contract inference | Rising DB/CPU latency, memory spikes | Constrain with native filters first, limit candidate rows, paginate/short-circuit, precompute normalized fields if feature persists | As dataset grows past a few hundred active jobs or with frequent chat use |
| Chat UI ships heavy client bundle/state logic eagerly | Worse LCP/TTI on mobile, jank on open | Lazy-load chat drawer/modal/components, keep dependencies minimal, avoid blocking main thread | On low-end mobile devices/common PT-BR connections from first release |
| No caching/dedup for repeated NL queries | Repeated Groq cost/latency for same intents | Short-TTL cache keyed by normalized prompt+locale/capability version | During campaigns/sharing or simple repeated usage patterns |

## Security Mistakes

Domain-specific security issues beyond general web security.

| Mistake | Risk | Prevention |
|---------|------|------------|
| Exposing contact info or reveal tokens through chat responses "for convenience" | Re-enables scraping/bypasses existing reveal protections and trust model | Return only public-safe `JobPublic` fields; keep contact access on existing protected flow |
| Trusting extracted params/enums without allowlist validation | Query abuse, logic bypass, inconsistent behavior via injected/invalid values | Validate against strict schema + allowlists (city whitelist, sort/order enums, supported filter keys/ranges) server-side |
| Logging raw chat prompts/responses and inferred attributes without controls | Privacy leakage in a no-login public product; sensitive user intent retained unnecessarily | Redact/truncate, avoid storing PII, set retention, separate security/audit logs from debug dumps |
| Public chat endpoint without rate limit/size/timeout controls | DoS/quota drain, cost spike, degraded availability | Enforce request caps, throttling, abuse detection, and operational kill-switch |
| Leaking system prompt/internal capability details in errors/debug UI | Easier prompt injection and probing of defenses | Generic user-facing errors, sanitized server logs, no prompt echoing to client |

## UX Pitfalls

Common user experience mistakes in this domain.

| Pitfall | User Impact | Better Approach |
|---------|-------------|-----------------|
| Returning zero results with no explanation | User assumes platform has no jobs; abandons (breaks core value) | Show interpreted params, state which constraints may be too strict/unsupported, offer relax/remove-filter actions and nearby alternatives |
| Hiding what the chatbot understood/applied | Loss of trust; users can't correct misinterpretation | Display transparent chips/summary: understood intent, applied filters, ignored/unsupported fields, and editable refinements |
| Over-chatty or slow interaction before showing jobs | Adds friction opposite to "encontrar vaga em segundos" | Prioritize fast results list; keep chat concise, show loading/progressive states, allow one-tap fallback to normal search |
| Pretending unsupported filters (salary/modality/contract) work fully | Wrong expectations and perceived dishonesty when results don't match | Explicitly label partial/unsupported capabilities and document MVP gaps in-response |
| Poor mobile drawer/modal ergonomics | Hard to type/read/refine on primary device type (mobile PT-BR audience) | Mobile-first layout, keyboard-safe input, easy filter chips/editing, accessible focus/scroll behavior |

## "Looks Done But Isn't" Checklist

Things that appear complete but are missing critical pieces.

- [ ] **NL intent extraction:** Often missing null/default discipline and schema rejection paths — verify ambiguous prompts produce no invented filters and invalid model output is handled safely.
- [ ] **Chat-search API:** Often missing timeout/rate-limit/size caps/fallback behavior — verify overload, slow Groq, and malformed input scenarios.
- [ ] **Filter mapping:** Often missing capability matrix and "unsupported vs applied" signaling — verify response explicitly reports ignored/relaxed filters for salary/modality/contract/city edge cases.
- [ ] **Public UI integration:** Often missing regression checks on existing board/search and mobile performance — verify core browse/search/detail/contact flows still work without login/friction.
- [ ] **Privacy & operations:** Often missing log redaction/retention and basic metrics — verify prompts/results aren't stored indiscriminately and latency/error/rate-limit signals are observable.
- [ ] **MVP examples coverage:** Often missing documented gaps — verify each agreed example is tested and any unsupported parameter behavior is explicit, not silent.

## Recovery Strategies

When pitfalls occur despite prevention, how to recover.

| Pitfall | Recovery Cost | Recovery Steps |
|---------|---------------|----------------|
| Over-constrained/hallucinated filters causing low recall | MEDIUM | Hotfix mapping to default-null + relaxation logic, adjust prompt/schema, add failing queries to golden tests, temporarily bias to keyword fallback |
| Public endpoint abuse/quota exhaustion/latency spikes | MEDIUM | Enable kill-switch or degrade to non-LLM keyword search, tighten rate/timeout limits, reduce token/model cost, review logs/traffic and rotate protections |
| Prompt injection or unsafe output handling discovered | HIGH | Disable/feature-flag chat endpoint, patch prompt+validator+allowlists, audit logs for exposure, add red-team regression cases before re-enable |
| Param/DB capability mismatch producing misleading results | MEDIUM | Correct response contract to disclose unsupported filters, patch normalization/mapping, backfill or scope down claims in UI/docs, add targeted tests |
| Regression in existing board/search behavior | HIGH | Revert chat integration commits/feature flag off, restore `list_published` contract, run regression suite, reintroduce via isolated adapter |

## Pitfall-to-Phase Mapping

How roadmap phases should address these pitfalls.

| Pitfall | Prevention Phase | Verification |
|---------|------------------|--------------|
| Hallucinated/over-constrained filters harming recall | Phase 1: Intent schema + mapping; Phase 3: UX/relaxation | Golden PT-BR queries show no invented filters; zero-result rate acceptable vs baseline; relaxation behavior visible |
| Latency/cost/abuse on public endpoint | Phase 2: API protections/resilience; Phase 4: hardening/ops | Load/abuse tests pass; timeouts/rate limits/circuit-breaker/fallback verified; metrics and kill-switch in place |
| Prompt injection in public chat | Phase 1: prompt+schema validation; Phase 2: endpoint hardening; Phase 4: security tests | Red-team cases cannot override instructions or emit unallowlisted actions/fields; raw internals not exposed |
| Mismatch between extracted params and DB capabilities (salary/modality/contract/city whitelist) | Phase 1: capability matrix+normalization; Phase 2: response contract; Phase 3: UI transparency | Each supported/unsupported param has defined behavior; `applied` vs `ignored` accurate; whitelist enforced |
| Poor UX when zero results | Phase 3: chat UI/result presentation | Zero-result state explains interpretation, suggests relaxations/alternatives, preserves fast path to jobs |
| Privacy/logging risks on no-login chat | Phase 2: API/logging policy; Phase 4: review | Logs redacted/truncated with retention; no contacts/secrets/PII persisted unnecessarily |
| Breaking existing board/search behavior or core no-friction value | Phase 1: additive design; Phase 3: isolated UI integration; Phase 4: regression gate | Existing public search/detail/contact flows unchanged; chat is additive/lazy-loaded; `JobPublic` boundary preserved |

## Sources

- `.planning/PROJECT.md` — milestone v1.3 goals, constraints (public no-login, free tiers, Groq, existing `GET /api/v1/public/jobs`/`crud.list_published`, `JobPublic` boundary), and known gaps (HIGH confidence, primary project context)
- EmpregaNoix domain facts provided in milestone brief: PT-BR unstructured job texts, 100–500 jobs/month, small curated dataset, admin-hardened extraction vs new public chat threat model (HIGH confidence)
- Established LLM application/security patterns: strict schema validation/allowlists for tool-less intent extraction, prompt-injection resistance for untrusted input, null-over-guessing for retrieval recall, and graceful degradation/fallbacks (MEDIUM-HIGH confidence; training knowledge aligned with common OWASP LLM/application guidance)
- Public API/free-tier operations patterns: rate limiting, timeout budgets, bounded token usage, caching/dedup, and kill switches for abuse/cost control (MEDIUM-HIGH confidence)
- Note: Live web/Context7 verification was not required to derive these domain-specific pitfalls from provided project artifacts; confidence on exact numeric thresholds (rate limits, cache TTLs) is MEDIUM and should be tuned from observed traffic/latency in Phase 2/4.

---
*Pitfalls research for: EmpregaNoix v1.3 Chatbot Inteligente de Busca de Vagas (subsequent milestone)*
*Researched: 2026-11-17*