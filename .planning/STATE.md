---
gsd_state_version: 1.0
milestone: v1.0
milestone_name: milestone
status: executing
stopped_at: Completed 04-02-PLAN.md (busca/cidade/ordenacao + migration 0003 + seed dev)
last_updated: "2026-10-26T22:19:30.524Z"
last_activity: 2026-10-26
progress:
  total_phases: 6
  completed_phases: 3
  total_plans: 19
  completed_plans: 15
  percent: 50
---

# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-10-13)

**Core value:** Qualquer pessoa encontra uma vaga e o contato para se candidatar em segundos — sem cadastro, sem login, sem fricção.
**Current focus:** Phase 04 — public-board-frontend

## Current Position

Phase: 04 (public-board-frontend) — EXECUTING
Plan: 3 of 6
Status: Ready to execute
Last activity: 2026-10-26

Progress: [████████░░] 79%

## Performance Metrics

**Velocity:**

- Total plans completed: 9
- Average duration: — min
- Total execution time: 0.0 hours

**By Phase:**

| Phase | Plans | Total | Avg/Plan |
|-------|-------|-------|----------|
| 01 | 4 | - | - |
| 03 | 5 | - | - |

**Recent Trend:**

- Last 5 plans: —
- Trend: Stable

*Updated after each plan completion*
| Phase 01 P01 | 15 | 2 tasks | 27 files |
| Phase 01 P02 | 35 min | 2 tasks | 6 files |
| Phase 01 P03 | 4 min | 2 tasks | 7 files |
| Phase 01 P04 | ~6min | 2 tasks | 11 files |
| Phase 03 P01 | 8min | 2 tasks | 6 files |
| Phase 03 P02 | 93min | 3 tasks | 10 files |
| Phase 03 P03 | 17min | 2 tasks | 5 files |
| Phase 03 P04 | 26min | 2 tasks | 9 files |
| Phase 04 P01 | 7min | 3 tasks | 11 files |
| Phase 04 P02 | 197min | 3 tasks | 5 files |

## Accumulated Context

### Decisions

Decisions are logged in PROJECT.md Key Decisions table.
Recent decisions affecting current work:

- (Roadmap) 6 fases coarse; extração (Phase 2), reveal/anti-spam (Phase 3) e lifecycle/infra (Phase 6) isoladas como HIGH RISK.
- (Research) Groq `llama-3.1-8b-instant`/`llama-3.3-70b` aposentados em 2026-08-16 — usar `openai/gpt-oss-20b`/`120b` via `GROQ_MODEL` + fallback (nunca hardcoded).
- (Research) Contatos nunca no payload público; servidos só por endpoint dedicado com Turnstile server-side (anti-scraping).
- [Phase 01]: D-06..D-13 realized: Job model + initial migration (UUID PK gen_random_uuid, 4-value job_status enum, at_least_one_contact CHECK, timestamptz with expires_at=now()+14d, pg_trgm+unaccent search_text GIN trigram, city/salary free text, no soft delete)
- [Phase 01]: D-01..D-04 realized: login returns a Bearer JWT (no cookie), single long-lived 12h token (JWT_EXPIRES_IN, no refresh), master password verified against ADMIN_PASSWORD_HASH, and login Turnstile/rate-limit deliberately deferred to Phase 3 — plan 01-03 (ADMN-01/ADMN-02/ADMN-03)
- [Phase 01]: Password hashing uses the bcrypt library directly; passlib 1.7.4 is incompatible with the locked bcrypt 5.0.0 (its backend probe raises ValueError) — 01-03 deviation (Rule 3); tracked in deferred-items.md for a future re-lock
- [Phase 01]: D-14..D-18 realized (plan 01-04): public read surface is GET /api/v1/public/jobs (offset pagination page/limit 1-50 default 20 + total count) and GET /api/v1/public/jobs/{id} (404 otherwise), always filtering status='published' AND expires_at > now(), with a contact-free JobPublic schema (no contact_email/contact_phone); search/filter/sort and contact reveal deferred to Phases 4 and 3 respectively
- [Phase 01]: D-22 realized (plan 01-04): focused pytest + pytest-asyncio suite (18 tests) + scripts/seed.py proving all five Phase 1 criteria (login ok/bad, admin 401, public contact-free list/detail, published-only non-expired, schema CHECK/enum/14-day expiry)
- [Phase 03 planning]: 5 planos em 5 ondas — 03-01 (config fail-closed + IP + pin slowapi) → 03-02 (Siteverify + limiter + DI + fixtures) → 03-03 (endpoint de reveal) → 03-04 (login protegido, back+front no mesmo plano) → 03-05 (smoke live + checkpoint de browser)
- [Phase 03 planning]: os segredos de teste do Cloudflare têm **35 chars** (`1x`/`2x`/`3x` + 31 + `AA`) — o regex de bloqueio em prod é `^[123]x[0-9A-Za-z]{31}AA$`; com `{30}` a chave always-pass passaria no validator (D-12 quebrado)
- [Phase 03 planning]: `slowapi==0.1.10` verificado no wheel — `key_func` é re-resolvido por request, bucket por URL, o param `request` é obrigatório no decorator e `init_app` registraria o handler 429 default em inglês (usamos `app.state.limiter` + handler pt-BR próprio)
- [Phase 03 planning]: `next-turnstile@1.0.7` exporta `{ Turnstile }` (nomeado) e **não** tem `resetKey` — o reset do widget é por remount via `key` do React
- [Phase 03 planning]: o conftest **não** pode definir `TURNSTILE_SECRET_KEY`/`TURNSTILE_SITE_KEY`/`REVEAL_RATE_LIMIT`/`LOGIN_RATE_LIMIT` no ambiente global — em teste `ENV="dev"` (default) e env vars têm precedência sobre os defaults, o que quebraria os testes de fail-closed do plano 03-01
- [Phase 03]: D-10/D-11/D-12/D-06 realized (plan 03-01): Settings fail-closed do Turnstile (secret obrigatorio fora de dev; chaves de teste 1x/2x/3x rejeitadas), knobs REVEAL_RATE_LIMIT=10/minute e LOGIN_RATE_LIMIT=5/minute, resolver de IP proxy-aware (X-Real-IP -> XFF mais a direita publico -> client.host -> unknown) e slowapi==0.1.10 pinado — primitivas de enforcement sem endpoint novo; suíte 120 passed
- [Phase 03]: X-Real-IP e aceito quando apenas PARSEIA como IP (nao quando e 'publico') — as faixas de documentacao do IANA (203.0.113.0/24, 198.51.100.0/24) tem is_private==True no ipaddress do Python; filtro de 'publico' no X-Real-IP derrubaria o header real do Railway. O filtro de 'publico' fica restrito ao XFF (D-10)
- [Phase 03]: SECR-02 mantido desmarcado em REQUIREMENTS.md ate o plano 03-03 ligar o limiter ao endpoint de reveal — o plano 03-01 entrega so as primitivas (config, resolver de IP, pin do limiter); marcar o requisito agora daria sinal falso numa fase HIGH RISK
- [Phase 03]: D-13 fail-closed materializado no servico: TurnstileVerifier.verify() nunca levanta excecao operacional (rede/5xx/JSON invalido) e devolve TurnstileResult(success=False, error_codes=['internal-error']); token vazio devolve 'missing-input-response' sem nenhuma requisicao HTTP — o portao fecha por construcao e o router decide o 403 + copy (T-03-03/T-03-04)
- [Phase 03]: action binding modelado como error-code 'action-mismatch' dentro do cliente, e nao como caso especial de cada router — o reuso de token entre reveal e login some no servico (D-13/T-03-03)
- [Phase 03]: SafeLimiter (subclasse de Limiter) neutraliza o _inject_headers do slowapi quando a rota nao declara 'response: Response' — o slowapi 0.1.10 com headers_enabled=True levanta Exception 500 em vez de 429 nesse caso; o Retry-After passou a ser emitido pelo handler pt-BR (T-03-07)
- [Phase 03]: o mode do Turnstile no /health deriva do segredo EFETIVO (live/test/disabled) e a site key vira o booleano site_key_configured — o texto do plano dizia 'sem site key o modo e disabled', mas o modo e sobre o segredo e o proprio caso de teste do plano exige mode=='test' em dev (T-03-06)
- [Phase 03]: SECR-01 e SECR-02 seguem como contribuidos, nao concluidos — este plano entrega a mecanica (verifier fail-closed + limiter por IP), mas o requisito so vale quando o endpoint de reveal do 03-03 consumir verifier e limiter - marcar agora daria sinal falso numa fase HIGH RISK (mesmo tratamento do 03-01)
- [Phase 03]: D-03/D-13 materializados no endpoint de reveal (plan 03-03): a rota POST /api/v1/public/jobs/{id}/reveal-contact aplica rate limit -> 404 (vaga) -> Siteverify (403) -> 200; a busca da vaga vem ANTES da chamada a Cloudflare e toda falha do Siteverify e 403 (nunca 200 degradado), com as duas copies pt-BR vindas de turnstile_error_detail()
- [Phase 03]: O bucket do rate limit do slowapi escopava pela URL (key_style default), e a rota de reveal carrega o id da vaga no path: cada vaga tinha a propria janela e um scraper girava ids sem nunca bater no limite nem na cota da Cloudflare (T-03-12). Fix no plano 03-03: key_style='endpoint' -> bucket (IP, rota), com guarda de regressao em test_ratelimit.py
- [Phase 03]: O contato do reveal volta cru (E.164) e a resposta carrega o job_id: e o que permite ao Phase 4 montar wa.me/mailto e manter o contato em memoria do cliente por vaga (D-04), sem pedir token novo ao reabrir a mesma vaga. O hostname do Siteverify NAO e checado (deliberado): o binding por action ja impede reuso de token entre fluxos
- [Phase 03]: SECR-01, SECR-02 e PUBL-05 marcados como CONCLUIDOS no plano 03-03 (diferente dos planos 03-01/03-02, que mantiveram desmarcado): com a rota de reveal no lugar, a validacao server-side do Turnstile, o rate limit por IP de verdade e a ausencia de contato no payload publico passam a valer - o caso 9 da suite exige que OUTRA vaga do mesmo IP tambem receba 429, o que prova a granularidade por IP
- [Phase 03]: A suite do backend precisa rodar a partir de backend/ (cd backend; .venv\Scripts\python.exe -m pytest -q): da raiz do repo o pytest nao le backend/pyproject.toml, perde asyncio_mode=auto e a suite inteira falha com 157 errors. Nenhum arquivo do repo foi alterado para isso
- [Phase 03]: SECR-03 materializado no login do admin (plan 03-04): a rota POST /api/v1/auth/login aplica rate limit -> Siteverify(expected_action='login') -> bcrypt -> JWT - a senha NUNCA e comparada sem um token Turnstile valido na mao (D-17). Token recusado ou verificacao indisponivel = 403 com copy propria (nunca 'Senha invalida'), e o front monta o widget interaction-only com action='login' e reseta por remount (D-16/D-19) — a prova da ordem e o status code: token recusado + senha errada da 403 (nao 401), coberto por test_login_turnstile_failure_does_not_reach_password_check
- [Phase 03]: O reset do widget do Turnstile e por REMOUNT (key nova do React), nao por API: o next-turnstile@1.0.7 nao tem resetKey nem ref exposto - o useEffect de cleanup do pacote chama window.turnstile.remove(widgetId) e o remount renderiza um widget novo (D-19/T-03-18) — o token consumido pelo backend nunca pode ser reenviado: um login falho remonta o widget e a proxima tentativa usa um token novo
- [Phase 03]: A site key do Turnstile e inlinada no bundle no BUILD (comportamento padrao do Next): trocar a chave no painel da Cloudflare depois do build nao atualiza o widget do front - o build tem que ser refeito. Registrado como threat flag para a Phase 6 — risco operacional de deploy, nao de codigo: a rotacao de chave sem rebuild quebraria o login em producao
- [Phase 03]: O smoke test do Siteverify e opt-in por env (TURNSTILE_LIVE=1) e importa apenas app.services.turnstile - sem app, sem banco, sem estado global — T-03-23: prova de integracao real de terceiro sem consumir cota da Cloudflare na suite do dia a dia; com a env var os 3 casos ficam verdes contra a API real, sem ela o arquivo inteiro e skipped
- [Phase 03]: A suite nunca herda o .env local do dev: o conftest fixa TURNSTILE_SECRET_KEY='' e TURNSTILE_SITE_KEY='' — o teste do /health do 03-02 afirmava site_key_configured is False, ou seja, um valor dependente da maquina; o harness ja fixava DATABASE_URL/ADMIN_PASSWORD_HASH/JWT_SECRET pelo mesmo motivo
- [Phase 03]: O binding de action do Turnstile NAO foi corrigido automaticamente: os segredos publicos de teste da Cloudflare nao devolvem o campo action, entao login e reveal devolvem 403 em dev — T-03-03/T-03-16 sao disposicoes mitigate do portao de anti-spam e o proprio plano 03-05 manda reportar o sintoma exato sem consertar nada sem o veredito do usuario
- [Phase ?]: Phase 04 Plan 01: Tailwind v4 tokens live verbatim in app/(public)/public.css @theme; public.css is imported only by (public)/layout.tsx so Preflight never reaches /admin/* (proven from build CSS chunks: / links the canvas chunk, /admin/paste does not).
- [Phase ?]: Phase 04 Plan 01: internal navigation uses next/link (renders a plain a href) because @next/next/no-html-link-for-pages rejects raw anchors to app routes; the Doacoes entry points at the real /doacoes page.
- [Phase ?]: Phase 04 Plan 01: globals.css stays Tailwind-free and is imported by the root layout (theme-color #0f0a1a, color-scheme dark); Next 15 added target ES2017 to tsconfig during lint and it was kept.
- [Phase 04]: Phase 04 Plan 02: os valores canonicos de cidade no banco sao ACENTUADOS (Sao Paulo com til, Rio de Janeiro, Belo Horizonte, Remoto), ao contrario do que o plano/CONTEXT afirmavam; o mapa de aliases resolve sao-paulo/sao paulo/Sao Paulo para o valor acentuado de ALLOWED_CITIES e os testes inserem a forma acentuada (Rule 1) — Mapear para a forma sem acento filtraria zero linhas contra as vagas reais extraidas
- [Phase 04]: Phase 04 Plan 02: a migration 0003 mantem jobs_search_text_trg ATIVO durante o backfill e desabilita apenas jobs_updated_at, reabilitando-o na mesma transacao; aplicada nos dois branches Neon (test e dev) e verificada ao vivo (prosrc contem requirements, pg_trigger.tgenabled='O')
- [Phase 04]: Phase 04 Plan 02: o filtro q usa exatamente uma lista de predicados compartilhada entre items e count (status='published' literal mantem o indice trigram parcial utilizavel), escapa barra/percent/underscore e faz bind via func.concat + LIKE ESCAPE; ordenacao sempre termina com tie-break por id
- [Phase 04]: Phase 04 Plan 02: scripts/seed_public_demo.py e o unico caminho para popular o board antes do fluxo de aprovacao da Phase 5; exige ENV=dev + host local/.neon.tech + --yes, apaga por marcador SEED_PUBLIC_DEMO e nunca escreve search_text. 30 vagas published ficaram no branch dev para a verificacao de browser dos planos seguintes

### Pending Todos

None yet.

### Blockers/Concerns

- Phase 2/3/6 flagged for possible `/gsd-research-phase` (modelo Groq vivo, strict outputs, TPM; Siteverify; scheduler externo/Neon CU-hour/Render-Railway free-tier).
- LGPD exige revisão por advogado brasileiro antes do lançamento (tarefa humana, não de código).
- Turnstile: os segredos publicos de teste da Cloudflare (1x/2x/3x) nao devolvem o campo 'action' na resposta do Siteverify - com eles o login (expected_action='login') e o reveal (expected_action='reveal') devolvem 403 'Verificacao anti-bot falhou - tente novamente', travando o checkpoint de browser da task 3 do plano 03-05. Sintoma medido contra o backend no ar (403, e nao 401 'Senha invalida', o que prova que a chamada real a Cloudflare acontece). Correcao proposta (exigir action so quando a resposta tiver action, ou um flag enforce_action desligado quando turnstile_mode == 'test') aguardando o veredito do usuario - nenhum codigo de producao foi alterado.

## Deferred Items

Items acknowledged and carried forward from previous milestone close:

| Category | Item | Status | Deferred At |
|----------|------|--------|-------------|
| Dependency hygiene | Replace `passlib[bcrypt]` with a direct `bcrypt` dependency and re-lock with `uv` (passlib 1.7.4 is incompatible with the locked bcrypt 5.0.0) | Deferred | Phase 01 (plan 01-03) |

## Session Continuity

Last session: 2026-10-26T22:19:30.497Z
Stopped at: Completed 04-02-PLAN.md (busca/cidade/ordenacao + migration 0003 + seed dev)
Resume file: None
