---
phase: 10-rebranding-launch-preparation-empreganoix
verified: 2026-11-14T22:10:00Z
status: passed
score: 11/11 must-haves verified
overrides_applied: 0
---

# Phase 10: Rebranding & Launch Preparation (EmpregaNoix) Verification Report

**Phase Goal:** Renomear a aplicacao de NaoQueroUsar para EmpregaNoix em todo o frontend e infraestrutura, garantindo consistencia de marca e configuracoes de deploy.
**Verified:** 2026-11-14T22:10:00Z
**Status:** passed
**Re-verification:** No — initial verification

## Goal Achievement

### Observable Truths

| # | Truth | Status | Evidence |
| --- | --- | --- | --- |
| 1 | Frontend público/admin exibe wordmark "EmpregaNoix", copyright "© 2026 EmpregaNoix" e slogan preservado | ✓ VERIFIED | `frontend/app/(public)/layout.tsx` contém `title: "EmpregaNoix — Vagas sem cadastro"`, `EmpregaNoix` (header), slogan `Procurar um emprego, não deve dar trabalho` (header/footer), `© 2026 EmpregaNoix`; `frontend/app/admin/layout.tsx` contém `title: "EmpregaNoix - Painel admin"` e slogan |
| 2 | Template WhatsApp, doações e `.env.example` rebranded para EmpregaNoix | ✓ VERIFIED | `frontend/lib/contacts.ts` contém `no EmpregaNoix e quero me candidatar`; `frontend/app/(public)/doacoes/page.tsx` contém `Doações — EmpregaNoix` e `apoiar o EmpregaNoix por PIX`; `frontend/.env.example` contém `variáveis de ambiente (EmpregaNoix)` |
| 3 | Páginas legais usam EmpregaNoix e `empreganoix@outlook.com`; sem `NQU`/`NaoQueroUsar`/`suportenqs` | ✓ VERIFIED | `frontend/app/(public)/privacidade/page.tsx` e `frontend/app/(public)/termos-de-uso/page.tsx` referenciam `empreganoix@outlook.com` (2 e 1 ocorrências) e marca EmpregaNoix; busca por `NaoQueroUsar`/`NQU`/`suportenqs` nessas páginas retorna vazio |
| 4 | Metadata/asset wiring aponta para `https://empreganoix.vercel.app` com favicon integrado; tokens @theme preservados | ✓ VERIFIED | `layout.tsx` define `metadataBase: new URL("https://empreganoix.vercel.app")`, `icons.icon: "/icon.svg"`, `openGraph.url/title/description`; `frontend/app/icon.svg` existe (371 bytes); `frontend/app/(public)/public.css` mantém `#8b5cf6`, `#a78bfa`, `#facc15`, `#0f0a1a`, `#1a1025` |
| 5 | Backend rebranded (API title, comentários/docs, seed) sem leftovers de marca visível em escopo | ✓ VERIFIED | `backend/app/main.py`: `FastAPI(title="EmpregaNoix API")`; `backend/scripts/seed.py`: `company="EmpregaNoix Seed"`; `backend/pyproject.toml` descrição `EmpregaNoix backend` (nome interno `nqu-backend` mantido por decisão documentada); `backend/alembic.ini`, `backend/alembic/versions/0001_initial_jobs.py`, `backend/README.md` atualizados |
| 6 | Docs/infra/scripts de deploy rebranded e com hosts EmpregaNoix | ✓ VERIFIED | `README.md` = `# EmpregaNoix`; `AGENTS.md` header `**EmpregaNoix**`; `docs/DEPLOY.md`, `render.yaml`, `scripts/verify-deploy.ps1` referenciam EmpregaNoix e exemplos `empreganoix.vercel.app` / `empreganoix.onrender.com`; buscas por `NaoQueroUsar`/`suportenqs` nesses arquivos retornam vazio |
| 7 | Testes/alinhamento de hosts e guard anti-regressão de marca presentes | ✓ VERIFIED | `backend/tests/test_cors.py` usa `https://empreganoix.vercel.app`; `backend/tests/test_brand_rename.py` existe com scan de `frontend`+`backend`, needles `NaoQueroUsar/NQU/suportenqs`, exclusões (`node_modules`, `.next`, `__pycache__`, `.venv`, `.planning`, `uv.lock`, `test_brand_rename.py`) e sufixos conforme 10-03 |
| 8 | Nenhum leftover de marca legado em código frontend/backend (exceto exclusões definidas) | ✓ VERIFIED | Busca em `frontend/` e `backend/` (excluindo `node_modules`, `.next`, `__pycache__`, `.venv`, `uv.lock`, `test_brand_rename.py`, `.planning`) sem ocorrências de `NaoQueroUsar`/`suportenqs`; ocorrências de token `NQU` limitam-se a identificadores internos documentados (`nqu-frontend` em package files, `nqu-backend` em `pyproject.toml`/nome de serviço mantido) e strings de teste de hostname não-visuais (`nqu.app` em `test_turnstile.py`) — não conflitam com BRND-01 (marca visível) nem com needles case-sensitive do guard |
| 9 | Commits atômicos dos planos 10-01/10-02/10-03 presentes no histórico | ✓ VERIFIED | `334d900`, `8cbb2cb`, `6676bf5`, `12c8456`, `96af491`, `b47654d`, `4a7a074`, `26da78f`, `1dbba2f` encontrados em `git log` |
| 10 | Deploy real em produção aprovado pelo usuário com evidência registrada (BRND-04 operacional) | ✓ VERIFIED | `10-04-SUMMARY.md` registra Task 2 (checkpoint `human-verify`) aprovada pelo usuário; evidência fornecida: Frontend `https://empreganoix-six.vercel.app`, Backend `https://nqu-backend-x60n.onrender.com`, cold-start `0.2s`. `docs/DEPLOY.md` contém registro `2026-11-14 (Phase 10, 10-04 Task 2 — checkpoint aprovado)` com os mesmos dados |
| 11 | Desvios de hosts/nomes documentados sem bloquear objetivo | ✓ VERIFIED | Desvios registrados: frontend real `empreganoix-six.vercel.app` (vs exemplo), backend real `nqu-backend-x60n.onrender.com` (vs exemplo), serviço Render mantido como `nqu-backend` — coerente com decisões 10-03/10-04 e `render.yaml` |

**Score:** 11/11 truths verified

### Required Artifacts

| Artifact | Expected | Status | Details |
| --- | --- | --- | --- |
| `frontend/app/(public)/layout.tsx` | Metadata/title/wordmark/copyright/metadataBase/og rebranded | ✓ VERIFIED | EmpregaNoix, slogan, `/icon.svg`, `https://empreganoix.vercel.app` presentes; og sem `images` (fallback opcional aceito) |
| `frontend/app/admin/layout.tsx` | Title/wordmark admin rebranded | ✓ VERIFIED | `EmpregaNoix - Painel admin` e slogan presentes |
| `frontend/app/(public)/doacoes/page.tsx` | Copy de doações rebranded | ✓ VERIFIED | Título e corpo referenciam EmpregaNoix |
| `frontend/lib/contacts.ts` | Template WhatsApp com EmpregaNoix | ✓ VERIFIED | Mensagem contém `no EmpregaNoix e quero me candidatar` |
| `frontend/.env.example` | Cabeçalho de marca atualizado | ✓ VERIFIED | `Front-end - variáveis de ambiente (EmpregaNoix)` |
| `frontend/app/(public)/privacidade/page.tsx` | Legal rebranded + canal | ✓ VERIFIED | EmpregaNoix e `empreganoix@outlook.com` (2x), sem tokens legados |
| `frontend/app/(public)/termos-de-uso/page.tsx` | Legal rebranded + canal | ✓ VERIFIED | EmpregaNoix e `empreganoix@outlook.com` (1x), sem tokens legados |
| `frontend/app/icon.svg` | Favicon file-based metadata | ✓ VERIFIED | Arquivo existe (371 bytes) e referenciado no layout |
| `frontend/app/(public)/public.css` | Tokens @theme preservados (BRND-03) | ✓ VERIFIED | `#8b5cf6`, `#a78bfa`, `#facc15`, `#0f0a1a`, `#1a1025` presentes |
| `backend/app/main.py` | FastAPI title rebranded | ✓ VERIFIED | `EmpregaNoix API` |
| `backend/scripts/seed.py` | Seed company rebranded | ✓ VERIFIED | `EmpregaNoix Seed` |
| `backend/pyproject.toml` | Descrição rebranded (nome interno mantido) | ✓ VERIFIED | `description = "EmpregaNoix backend"`, `name = "nqu-backend"` |
| `backend/README.md`, `backend/alembic.ini`, `backend/alembic/versions/0001_initial_jobs.py` | Comentários/docs rebranded | ✓ VERIFIED | EmpregaNoix presente; sem leftovers legados de marca visível |
| `README.md`, `AGENTS.md`, `docs/DEPLOY.md`, `render.yaml`, `scripts/verify-deploy.ps1` | Docs/infra rebranded | ✓ VERIFIED | Títulos/comentários e hosts EmpregaNoix atualizados |
| `backend/tests/test_cors.py` | Host de origem atualizado | ✓ VERIFIED | Referências a `https://empreganoix.vercel.app` |
| `backend/tests/test_brand_rename.py` | Guard de leftovers | ✓ VERIFIED | Implementa scan + exclusões + needles conforme plano |
| `.planning/phases/10-rebranding-launch-preparation-empreganoix/10-04-SUMMARY.md` | Evidência de deploy aprovado | ✓ VERIFIED | URLs reais, cold-start 0.2s, desvios documentados |

### Key Link Verification

| From | To | Via | Status | Details |
| --- | --- | --- | --- | --- |
| `frontend/app/(public)/layout.tsx` | `https://empreganoix.vercel.app` | `metadataBase` + `openGraph.url` | ✓ WIRED | Strings presentes em metadata export |
| `frontend/app/(public)/layout.tsx` | `frontend/app/icon.svg` | `metadata.icons.icon = "/icon.svg"` | ✓ WIRED | Arquivo existe e é referenciado |
| `docs/DEPLOY.md` / `scripts/verify-deploy.ps1` | Produção EmpregaNoix | hosts/exemplos + registro de verificação 10-04 | ✓ WIRED | Exemplos e registro aprovado com endpoints reais documentados |
| `render.yaml` / deploy runbook | Backend Render | blueprint/comentários/health/runbook | ✓ WIRED | Nome interno `nqu-backend` mantido (decisão documentada), marca/hosts alinhados no repo |

### Data-Flow Trace (Level 4)

| Artifact | Data Variable | Source | Produces Real Data | Status |
| --- | --- | --- | --- | --- |
| N/A | N/A | N/A | N/A | `?- SKIPPED` (fase de rebranding/conteúdo/config/docs/deploy; sem novos fluxos dinâmicos de dados a rastrear além do já existente) |

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
| --- | --- | --- | --- |
| Brand leftovers guardável por scan estático | Busca por `NaoQueroUsar`/`suportenqs` em `frontend/`,`backend/` (excl. build/cache/uv.lock/guard/.planning) | Nenhuma ocorrência | ✓ PASS |
| Artefatos/strings-chave presentes | Inspeção de layouts, legais, contatos, backend, docs, guard, icon | Todos os marcadores esperados encontrados | ✓ PASS |
| Build/lint/testes executados nesta verificação | Não executado (sandbox sem reexecução de suites/deploy) | Evidência delegada a SUMMARIES (lint/build/pytest verdes) e aprovação humana 10-04 | ? SKIP |

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
| --- | --- | --- | --- | --- |
| BRND-01 | 10-01, 10-02, 10-03 | App renomeado para "EmpregaNoix" em todo o frontend (textos, labels, headings, meta tags) e superfícies correlatas de marca | ✓ SATISFIED | Layouts/admin/doações/legais/contatos/.env.example/backend/docs/infra rebranded; sem leftovers `NaoQueroUsar`/`suportenqs` em código frontend/backend; guard `test_brand_rename.py` adicionado |
| BRND-02 | 10-01 | Slogan mantido "Procurar um emprego, não deve dar trabalho" refletido na nova marca | ✓ SATISFIED | Slogan presente em `frontend/app/(public)/layout.tsx` e `frontend/app/admin/layout.tsx`; cópia atualizada para EmpregaNoix onde aplicável |
| BRND-03 | 10-01 | Cores da marca mantidas (roxo/amarelo) consistentes | ✓ SATISFIED | Tokens `#8b5cf6`, `#a78bfa`, `#facc15` (e fundos escuros) preservados em `frontend/app/(public)/public.css`; assets/metadata integrados sem alterar tema |
| BRND-04 | 10-03, 10-04 | Hosts/domínio e configurações de deploy atualizados para origens EmpregaNoix; deploy executado | ✓ SATISFIED | Docs/infra/testes atualizados para hosts EmpregaNoix; produção aprovada pelo usuário (Task 2 checkpoint) com Frontend `https://empreganoix-six.vercel.app`, Backend `https://nqu-backend-x60n.onrender.com`, cold-start `0.2s` registrado em `docs/DEPLOY.md` e `10-04-SUMMARY.md` (desvios de hostname documentados) |

**Orphaned requirements:** None. REQUIREMENTS traceability maps BRND-01..04 to Phase 10, and every ID appears in at least one PLAN frontmatter (10-01: BRND-01/02/03; 10-02: BRND-01; 10-03: BRND-01/04; 10-04: BRND-04).

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
| --- | --- | --- | --- | --- |
| `frontend/app/(public)/layout.tsx` | 14-19 | `openGraph.images` omitido; PNG OG/apple opcionais não presentes | ℹ️ Info | Fallback visual aceito pelo plano/D-05 e por `10-01-SUMMARY.md`; compartilhamento depende de título/descrição até asset ser adicionado |
| `frontend/package.json`, `frontend/package-lock.json`, `backend/pyproject.toml` | 2 / 2,8 / 2 | Identificadores internos `nqu-frontend` / `nqu-backend` | ℹ️ Info | Intencional e documentado (não é marca visível ao usuário; pacote/serviço interno mantidos para evitar churn) |
| `docs/DEPLOY.md` | 102,120,286-294 | Exemplos/linhas históricas ainda citam host exemplo `empreganoix.onrender.com` junto ao registro real | ℹ️ Info | Registro 2026-11-14 documenta endpoints reais aprovados; discrepância é documental e não contradiz a aprovação registrada |

### Human Verification Required

None. O checkpoint humano de deploy/produção (10-04 Task 2) foi explicitamente aprovado pelo usuário e registrado com evidência (URLs e cold-start); não há itens automatizáveis pendentes adicionais para esta fase.

### Gaps Summary

No gaps found. Os must-haves de renomeação de marca (frontend/backend/docs/infra), preservação de slogan/tokens, guard de regressão e evidência de deploy aprovado (BRND-01..04) estão presentes e consistentes com os artefatos do repositório e registros fornecidos. Desvios observados (hostnames reais vs exemplos, identificadores internos `nqu-*`, assets OG/Apple opcionais ausentes) estão documentados e não bloqueiam o objetivo da fase.

---

_Verified: 2026-11-14T22:10:00Z_
_Verifier: OpenCode (gsd-verifier)_
