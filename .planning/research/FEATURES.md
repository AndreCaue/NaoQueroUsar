# Feature Research

**Domain:** Public job board / classifieds (Brazil, mobile-first, no-signup)
**Researched:** 2026-10-13
**Confidence:** MEDIUM (domain patterns well-evidenced from competitor products + industry guides; NQU-specific tradeoffs are reasoned, not field-tested)

## Research Note: The Differentiator Is Already Proven in Market

A critical finding: **"no signup" is not a novel claim in Brazil — it is an emerging, contested category.** Direct competitors already market it explicitly:

- **EmpregoDaqui** — "Vagas de emprego perto de você... fale direto pelo WhatsApp. **Sem cadastro, sem enrolação.**" Cards + map + swipe ("Gostei ❤ / Passar ✕"), WhatsApp + email buttons, LGPD pages, and a prominent disclaimer that the platform is only a *meio de divulgação* (not a party to hiring).
- **BrVagas** — "Sem precisar criar conta ou lembrar de senha", WhatsApp groups per city, "vagas verificadas", "origem rastreada", "sem golpe".
- **Meu Emprego** — AI job search entirely on WhatsApp, "Sem necessidade de baixar novos aplicativos ou criar contas".
- **BuscarVagas** — "100% gratuito e sem complicações", direct contact "sem intermediários", WhatsApp groups.
- **Chance na Vaga** — lists jobs publicly "sem precisar de cadastro para ver" but requires an account to apply (i.e., the *partial* version of the model).

**Implication for NQU:** the moat is NOT "no signup" alone (competitors claim it too). The defensible wedge is the **combination**: no-signup + *immediate contact reveal on the listing itself* + **curation quality** (LLM-extracted + human-reviewed, not raw group spam) + **guaranteed freshness** (hard 14-day expiry = zero ghost jobs). Features should reinforce that triad. Confidence: MEDIUM (competitor pages are live and authoritative for their own positioning; market size/moat durability unverified).

---

## Feature Landscape

### Table Stakes (Users Expect These)

Features users assume exist. Missing these = product feels incomplete or unusable.

| Feature | Why Expected | Complexity | Notes |
|---------|--------------|------------|-------|
| Public job list (published only), no gate | The entire premise; a gate = instant bounce | LOW | Home query filters `status = published` |
| Job summary card | Scanning many listings fast is the core loop | LOW | title, company, city, salary-if-present, activities preview |
| Full job detail view | Candidate must read requirements/benefits before acting | LOW–MED | Modal is fine for UX; see SEO conflict below |
| Apply / contact action that works | A job you can't reach is worthless | LOW | `mailto:` + `https://wa.me/55...` deep links (pt-BR norm) |
| Keyword search | Primary way to narrow down | MEDIUM | Server-side; pt-BR **accent- and case-insensitive** ("sao paulo" = "São Paulo"); search title + company + activities |
| City / location filter | In Brazil, location is the #1 determinant | LOW | Enum + "Remoto" bucket; multi-select eventually |
| Date sort (newest / oldest) | Freshness is the promise; users scan new-first | LOW | Default = newest desc |
| Freshness / auto-expiry | Stale listings are the #1 job-board complaint ("ghost jobs") | MEDIUM | Scheduled job flips/hard-deletes at `expires_at`; must be reliable |
| Salary display when present | Top decision factor; its absence is penalized | LOW | If missing → "A combinar", never blank/broken |
| Mobile-responsive layout | Majority of BR jobseekers are mobile | LOW–MED | Tailwind mobile-first; test 360px width |
| No-results / empty state | Dead-ends feel broken; guide the user | LOW | Suggest clearing filters / broader city |
| Privacy policy + terms + disclaimer | LGPD + trust norm; competitors all have them | LOW | Include "somos apenas meio de divulgação" disclaimer (EmpregoDaqui model) |
| Report a suspicious job | Jobs from informal groups = real scam risk; users need an escape valve | LOW–MED | MVP can be a `mailto:`/WhatsApp report link; Turnstile-protected form later |
| Anti-spam on public interaction | Bots/scrapers will hammer any public endpoint | MEDIUM | **Placement TBD** — see open question on Turnstile below |
| Share listing (WhatsApp) | Sharing jobs in groups is the dominant BR distribution behavior | LOW | `navigator.share` + WhatsApp link |

### Differentiators (Competitive Advantage)

Features that set the product apart. Align with Core Value: *"encontrar uma vaga e o contato em segundos — sem cadastro, sem login, sem fricção."*

| Feature | Value Proposition | Complexity | Notes |
|---------|-------------------|------------|-------|
| Zero-gateway browse→contact (no account ever) | Removes the exact "burocracia de cadastro" frustration that motivates the product | — (positioning) | Must be true end-to-end: no hidden wall at the apply step (where Chance na Vaga fails) |
| One-tap contact reveal (hidden by default, client-side) | Frictionless for humans, painful for scrapers | LOW | Contact in DOM but masked; reveal on click, no network call = no Turnstile needed here |
| WhatsApp-native apply (`wa.me` deep link) | Matches exactly how Brazilians already apply | LOW | Highest-conversion contact channel; format phone to E.164 (`55` + DDD + number) |
| Curated, hand-reviewed listings | "Real vagas, not raw group spam" — the quality moat | LOW (process) | The admin approve-gate IS the feature; market it |
| "Vaga revisada" / verified trust badge | Signals legitimacy vs. scammy group posts | LOW | Per card + detail; honest framing (reviewed ≠ guaranteed) |
| Guaranteed freshness (no ghost jobs) | 14-day hard delete = never apply to a dead listing | MEDIUM | Ties directly to expiry job; use as marketing claim |
| Mobile-first swipe/browse card UX | Fast, low-effort exploration (matches EmpregoDaqui) | MEDIUM | Optional v1.x; grid is enough for MVP |
| Discreet donation button | Non-intrusive alternative revenue | LOW | Yellow #facc15, hover-only, per project brief |
| SEO / Google Jobs distribution | Free organic acquisition; jobs reach people off-site | HIGH | **Conflicts with modal-only detail** — needs dedicated per-job URLs + `JobPosting` JSON-LD (see Dependencies) |
| pt-BR native + informal tone | Speaks the audience's language; trust | LOW | Copy in pt-BR; dates `dd/mm`; currency `R$ 1.837`; not corporate-stiff |

### Anti-Features (Commonly Requested, Often Problematic)

Features that seem good but break the core value or bloat scope. **Document explicitly to prevent re-adding.**

| Feature | Why Requested | Why Problematic | Alternative |
|---------|---------------|-----------------|-------------|
| User accounts / login | "Engagement", personalization | Directly contradicts the entire premise; adds auth surface, DB, support | Stay permanently anonymous |
| Saved jobs / favorites | Users like bookmarks | Requires identity/cookies + persistence; friction | Share link / browser bookmark |
| Job alerts / email subscriptions | Re-engagement standard on big boards | Needs email collection = the very "cadastro" being avoided; deliverability work | WhatsApp groups later if ever (matches BR norm) |
| Public job submission | "Crowd-source growth" | Opens a spam/scam floodgate; kills curation moat | Admin-only ingestion (pasted group text + LLM) |
| Applicant tracking / ATS / resume upload | "Be competitive with LinkedIn" | Massive scope; shifts product to recruiter-side | Candidate contacts employer directly |
| Resume database / talent bank | Monetization potential | Out of scope; needs accounts + PII (LGPD liability) | — |
| Renewals of expired jobs | "Some jobs should stay" | Complicates the clean 14-day cycle; invites stale listings | Repost manually if still valid |
| Duplicate detection | Housekeeping | Manual curation already covers at 100–500/mo | Admin eye + edit-by-ID |
| Multi-admin / roles / moderation queue consumer | "Team scale" | Single master is a feature (fast, simple, consistent) | Keep one admin |
| Real-time chat / in-platform messaging | "Keep users on site" | Moderation + PII risk; no accounts anyway | Off-platform WhatsApp/email |
| Heavy faceted filters at MVP (seniority, contract type, salary bands) | "Like the big boards" | Low inventory + mobile screen cost > benefit; dilutes focus | Search + city + date only; add facets when volume justifies |
| Infinite scroll on the main list | Modern-feeling feed | Poor SEO/shareability; hinders "where am I" on mobile | Simple pagination / "carregar mais" |
| Map view at MVP | Visual appeal (EmpregoDaqui has it) | Real geo cost (geocoding, normalization from raw text) | Defer to v1.x/v2 once vouchers exist |
| Ratings / reviews / comments | Social proof | Moderation burden; invites abuse on informal listings | Report link only |
| Aggregating/scraping other boards | Free inventory | Legal exposure; contradicts "curadoria"; noise | Curated ingestion only |
| Social login (Google/LinkedIn) | "Easy auth" | Any auth contradicts no-signup | None |
| "Feature vaga" paid promotion | Revenue | Empty at MVP scale; springs from monetization (out of scope) | Donations + AD placeholders only |

---

## Feature Dependencies

```
[Job card grid]
    ├──requires──> [Published jobs query] ──requires──> [Admin approve workflow]
    │                                                        └──requires──> [LLM extraction + review UI]
    └──requires──> [City/Search/Sort]  (all filter the same query)

[Job detail view / modal]
    └──requires──> [Job card grid]  (opens from a card)

[Contact reveal]
    └──requires──> [Job detail view]
                       └──requires──> [Contact fields stored + at least one present]

[Auto-expiry / hard delete]
    └──requires──> [status + expires_at fields] ──requires──> [Scheduled job / cron]

[Trust badge "Vaga revisada"] ──enhances──> [Admin approve workflow]
[Report suspicious job] ──enhances──> [Trust/anti-scam posture]
[Anti-spam / Turnstile] ──requires──> [A public form/POST endpoint]  ⚠ see open question

[SEO / JobPosting schema]
    └──requires──> [Dedicated single-job URL]
                       └──conflicts──> [Modal-only detail architecture]

[Job alerts / saved searches] ──conflicts──> [No-signup core value]
```

### Dependency Notes

- **[Grid] requires [Admin approve workflow]:** nothing is visible publicly until the master approvals; the curation gate is upstream of the entire public site.
- **[Detail] requires [Grid]:** detail is reached from a card (modal). This coupling is why the SEO decision matters — see conflict.
- **[Contact reveal] requires [Detail]:** reveal is a detail-level action; contact fields must be validated (at least one) at ingestion/review time, not at display time.
- **[Auto-expiry] requires [status + expires_at]:** the data model must carry both; the scheduled job is the single most fragile reliability dependency (missed runs = ghost jobs, the exact failure the product attacks).
- **[Trust badge] enhances [Approve workflow]:** zero extra machinery — the act of approving *is* the signal; just surface it.
- **[Anti-spam/Turnstile] requires a form endpoint:** in the current MVP there is **no public write/submit form** (no submission, no signup, no comments). Turnstile is worthless without a target. Two viable placements: (a) protect the **admin login** endpoint against credential stuffing, or (b) protect a **report-a-job** form. **Decision needed before implementation** (flagged as open question).
- **[SEO] conflicts with [Modal-only detail]:** Google requires `JobPosting` structured data **only on a single-job page, never on a list page**, with a stable URL and `validThrough`. A modal overlaying the home grid has no indexable per-job URL. Resolve via Next.js **intercepting routes / parallel routes**: render a real `/vaga/[id]` page for crawlers and deep links, open it as a modal in-app. This is a HIGH-value, HIGH-complexity item — decide in roadmap whether SEO is MVP or v1.x.
- **[Alerts] conflicts with [No-signup]:** any notification channel needs an identity/contact to notify = the friction NQU exists to remove. Keep out unless a truly anonymous (WhatsApp group) form emerges.

---

## pt-BR + Mobile-First UX Specifics

Concrete patterns validated by competitors and UX research:

- **Search must be accent/case-insensitive.** Users type "sao paulo", "vaga de auxiliar". Normalize accented Portuguese (`São`, `Serviços`, `Analista`) at query time (e.g., unaccent + lowercase). *Detection:* "no results" for a query that clearly has matches.
- **Filters as chips above results on mobile**, not a hidden sidebar. Make them a fullscreen overlay with an **"Aplicar"** button if they grow; for MVP, city chips + sort toggle are enough. Always show **result count** ("27 vagas") — mobile users need feedback that a filter applied.
- **Search box visible at top**, ≥45 chars wide on mobile, with a clear pt-BR label ("Buscar vaga, empresa ou palavra-chave"). Avoid auto-collapse.
- **"Remoto" is a first-class location**, rendered alongside SP/RJ/BH — remote is a *place* in the BR mental model, not a work-mode toggle (this differs from US boards' "remote toggle" pattern).
- **Salary formatting** in `R$` with thousand separators (`R$ 1.837`); support ranges ("R$ 2.000 a R$ 2.500") and "A combinar" / "Não informado".
- **Dates** short and relative-friendly (`Publicada há 2 dias`, `Expira em 5 dias`). Showing time-to-expiry is both useful and reinforces the freshness differentiator.
- **Contact action buttons** as large, thumb-reachable CTAs: primary "Falar no WhatsApp" (green affordance), secondary "Enviar e-mail". Copy the `wa.me/55…` format. On desktop, also reveal a copyable phone/email.
- **Card = scannable in one thumb glance:** title (bold, 1 line), company, city chip, salary chip, 2-line activities preview. Tap anywhere (or "Ver a vaga") → detail. Never require horizontal scroll.
- **Detail modal** should trap focus, close on backdrop/ESC, and keep "Mostrar contato" sticky/visible so the reveal is never buried.
- **pt-BR copy tone:** direct and informal ("Procurar um emprego, não deve dar trabalho"), avoid juridiquês except in the required disclaimer/LGPD pages.
- **Share** via `navigator.share()` with WhatsApp fallback link — sharing to groups is how listings spread in Brazil.

---

## MVP Definition

### Launch With (v1)

Minimum to validate: *can a stranger find and contact a real job in seconds without an account?*

- [ ] Public published-jobs grid — the product exists only if jobs are visible, ungated
- [ ] Job card + detail modal — scan then read
- [ ] Contact reveal + WhatsApp/email apply — the payoff; the reason to exist
- [ ] Keyword search (accent-insensitive) — primary narrowing tool
- [ ] City filter (SP/RJ/BH/Remoto) — top determinant in BR
- [ ] Date sort (newest default) — freshness
- [ ] Auto-expiry + hard delete (14 days) — the trust differentiator; must be reliable
- [ ] Mobile-first responsive layout — most traffic is mobile
- [ ] "Vaga revisada" badge — cheap, high-signal trust marker
- [ ] Report-a-job link (mailto/WhatsApp) — trust escape valve for informal listings
- [ ] Privacy/terms/disclaimer pages (LGPD + "meio de divulgação")
- [ ] Donations button + AD placeholders — per brief, low priority but in scope
- [ ] Anti-spam/Turnstile **placed on admin login** (pending the placement decision above)

### Add After Validation (v1.x)

Trigger-gated additions once the core loop works and volume grows.

- [ ] **Per-job URLs + `JobPosting` JSON-LD + Google Jobs** — add when organic discovery becomes the bottleneck (highest-ROI growth lever, but HIGH complexity)
- [ ] Turnstile-protected report form — when report volume/abuse justifies it
- [ ] Multi-city selection + more cities — when inventory spans beyond 4 cities
- [ ] Swipe/browse card mode — when engagement data suggests it helps
- [ ] "Carregar mais" pagination refinement — when listings exceed one screen

### Future Consideration (v2+)

- [ ] Map / "perto de mim" (geo) — needs normalized geo from raw text; big lift
- [ ] Anonymous WhatsApp-group distribution — only if it can avoid identity capture
- [ ] Featured/promoted listings — only with real monetization (out of scope now)
- [ ] Light facets (contract type, salary floor) — when inventory makes filters meaningful

---

## Feature Prioritization Matrix

| Feature | User Value | Implementation Cost | Priority |
|---------|------------|---------------------|----------|
| Public ungated job grid | HIGH | LOW | P1 |
| Job card + detail modal | HIGH | LOW–MED | P1 |
| Contact reveal (hidden by default) | HIGH | LOW | P1 |
| WhatsApp/email apply links | HIGH | LOW | P1 |
| Keyword search (accent-insensitive) | HIGH | MEDIUM | P1 |
| City filter (SP/RJ/BH/Remoto) | HIGH | LOW | P1 |
| Date sort | MEDIUM | LOW | P1 |
| Auto-expiry + hard delete | HIGH | MEDIUM | P1 |
| Mobile-first responsive | HIGH | LOW–MED | P1 |
| "Vaga revisada" badge | MEDIUM | LOW | P1 |
| Report-a-job link | MEDIUM | LOW | P1 |
| Privacy/terms/disclaimer | MEDIUM | LOW | P1 |
| Anti-spam/Turnstile | MEDIUM | MEDIUM | P1 (placement TBD) |
| Donations button | LOW | LOW | P2 |
| AD placeholders | LOW | LOW | P2 |
| Per-job URL + JobPosting schema | HIGH (growth) | HIGH | P2 |
| Swipe/browse mode | MEDIUM | MEDIUM | P3 |
| Map / geo | MEDIUM | HIGH | P3 |
| Light facets | LOW–MED | MEDIUM | P3 |

**Priority key:** P1 = must ship for launch · P2 = add when possible · P3 = future.

---

## Competitor Feature Analysis

| Feature | EmpregoDaqui | BrVagas / BuscarVagas | Chance na Vaga | Large boards (InfoJobs/Trabalha Brasil) | NQU Approach |
|---------|--------------|-----------------------|----------------|------------------------------------------|--------------|
| Signup to view jobs | No | No | Yes (view free) | Yes (often) | **Never** |
| Signup to apply/contact | No | No (WhatsApp groups) | **Yes** | Yes | **Never** — direct contact |
| Contact channel | WhatsApp + email | WhatsApp groups | In-platform | Portal/ATS | WhatsApp + email deep links |
| Curation / verification | Ads disclaimer; quiz-based premium | "Vagas verificadas / origem rastreada" | Not emphasized | Automated | **LLM-extracted + human-reviewed** |
| Freshness/expiry | Varies | Daily updates | Not emphasized | Varies | **Hard 14-day delete** |
| Filters | City, cards/map, swipe | City/area | Distance, state, modality, contract, salary | Full facets | Search + city + date (lean) |
| Trust UX | Liability disclaimer, LGPD pages | "Sem golpe", verified badges | Best Workplaces badge | Company ratings | "Vaga revisada" badge + report link + freshness |
| SEO/Google Jobs | Not evident | SEO-optimized (BuscarVagas) | — | Strong | Deferred to v1.x (modal conflict) |
| Ingestion | Employer posts + premium | Aggregated from official sources | Employer portal | Employer-paid posts | **Paste + LLM + approve** |

**Read:** NQU's realistic edge is **curation quality × guaranteed freshness × zero-friction contact**. It cannot win on inventory (aggregators) or facets (big boards). Lean into the quality/freshness story and the direct WhatsApp funnel.

---

## Sources

- EmpregoDaqui (empregodaqui.com.br) — live competitor, "sem cadastro", WhatsApp contact, disclaimer model (HIGH — primary source)
- BrVagas (brvagas.com.br) — "sem criar conta", "vagas verificadas" (HIGH — primary source)
- Meu Emprego (meuemprego.com.br) — WhatsApp AI job search, no accounts (HIGH — primary source)
- BuscarVagas (buscarvagas.com.br) — "100% gratuito", SEO-optimized, WhatsApp groups (HIGH — primary source)
- Chance na Vaga (chancenavaga.com.br) — partial no-signup model (HIGH — primary source)
- InfoJobs / Trabalha Brasil / BetaVagas — filter patterns, BR job field norms (HIGH — primary source)
- Cavuno "Job Board Features: The Complete Guide for Operators" & Job Boardly "Features Employers Expect" — table-stakes feature taxonomy (MEDIUM — vendor content, consistent across sources)
- Google Search Central, "Job posting structured data" + Schema.org `JobPosting` — required properties, single-page rule, `validThrough` (HIGH — official docs)
- LogRocket / Algolia / Pencil & Paper — mobile filter UX patterns (MEDIUM — industry UX sources, convergent)
- FBI/Europol/IC3 job-scam advisories — scam red flags, what to signal against (HIGH — official)
- UX research case study (Dibimbing) + curated-board concepts (JobCurators, FlexJobs, remoty.work) — verified-badge + reporting recommendations (MEDIUM)

---

*Feature research for: NQU — Brazilian no-signup job board*
*Researched: 2026-10-13*
