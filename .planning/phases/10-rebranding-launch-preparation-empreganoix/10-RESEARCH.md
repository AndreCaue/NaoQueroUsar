# Phase 10: Rebranding & Launch Preparation (EmpregaNoix) - Research

**Researched:** 2026-11-14
**Domain:** Rebranding (content rename) + launch preparation (deploy Vercel + Render, smoke gate)
**Confidence:** HIGH

## Summary

Phase 10 is a **rename + launch** phase, not a feature phase. The codebase already implements all functional requirements (Phases 1–9). What remains is: (a) a mechanical but thorough content rename from "NaoQueroUsar"/"NQU"/"suportenqs@outlook.com" to "EmpregaNoix"/"empreganoix@outlook.com" across frontend, backend, docs, and planning artifacts; (b) generation of new brand assets (logo, favicon, og:image); (c) host/CORS/env alignment to `empreganoix.vercel.app` / `empreganoix.onrender.com`; and (d) the **real** production deploy + smoke gate that was deliberately deferred in Phase 6 (decision reversed by D-04).

No new libraries or dependencies are required. The existing stack (Next.js 16.4.6, Tailwind v4 `@theme`, FastAPI 0.143, pydantic-settings) already supports everything. The risk surface is operational (dashboard config, Turnstile hostnames, env inlining in the Next build) rather than code.

**Primary recommendation:** Execute as three waves — (1) content rename + assets (pure code, fully testable locally), (2) host/CORS/env + config updates with regression tests updated, (3) deploy + smoke gate with human checkpoints for dashboard secrets. Keep repo directory name untouched (D-01).

## User Constraints (from CONTEXT.md)

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

- **D-01:** Renomeação completa do **conteúdo** (textos, labels, headings, meta tags, toasts, template WhatsApp, páginas legais, título da API FastAPI, docs, README, descrição do pyproject, seed company, email) de "NaoQueroUsar"/"NQU" para "EmpregaNoix". O **diretório do repositório** e `.planning/` permanecem "NaoQueroUsar" — não renomear a pasta.
- **D-02:** Slogan mantido verbatim: "Procurar um emprego, não deve dar trabalho".
- **D-03:** Novos hosts oficiais: frontend `https://empreganoix.vercel.app`, backend `https://empreganoix.onrender.com`. Hosts antigos não mantidos como redirect. Atualizar `CORS_ORIGINS`/`ALLOWED_ORIGINS`, `NEXT_PUBLIC_API_URL`/`BACKEND_API_URL` e Turnstile Hostnames.
- **D-04:** Executar deploy real Vercel + Render agora, com `ENV=prod`, CORS travado, chaves Turnstile live e `CRON_SECRET` em ambos; rodar smoke gate até verde.
- **D-05:** Criar logo completo novo (identidade visual completa), incluindo favicon e og:image, além do wordmark textual. Se atrasar, wordmark textual "EmpregaNoix" serve como fallback sem bloquear deploy.
- **D-06:** Atualizar referências "NQU"/"NaoQueroUsar" em `/privacidade` e `/termos-de-uso` para "EmpregaNoix"; email `suportenqs@outlook.com` → `empreganoix@outlook.com`; WhatsApp template → "Vi a vaga ... no EmpregaNoix".

### OpenCode's Discretion

- Ferramenta/fluxo exato para gerar os assets de marca (favicon, og:image, logo) — image generation ou SVG manual.
- Ordem de execução das substituições (frontend primeiro, depois backend/docs/infra).
- Fallback de wordmark textual se assets não estiverem prontos no momento do deploy (não bloquear BRND-04).
- Se o logo completo atrasar, manter wordmark textual como fallback sem bloquear deploy.

### Deferred Ideas (OUT OF SCOPE)

- Domínio próprio (ex.: `empreganoix.com.br`) — fora desta fase; mantém tier gratuito.
- Redirect dos hosts antigos — não mantidos.
- Renomeação do diretório do repositório/`.planning` — não feita.
- Revisão jurídica dos textos legais — fora de escopo de código (task humana).
</user_constraints>

## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| BRND-01 | App renomeado de "NaoQueroUsar" para "EmpregaNoix" em todo o frontend (textos, labels, headings, meta tags) | Inventário completo de superfícies em `code_context` (CONTEXT.md) + grep listado na seção "Rename Inventory" |
| BRND-02 | Slogan mantido "Procurar um emprego, não deve dar trabalho" — atualizado para refletir a nova marca | Slogan já aparece em layout.tsx (header/footer) e admin layout; manter verbatim, apenas trocar wordmark |
| BRND-03 | Cores da marca mantidas (roxo #8b5cf6/#a78bfa, amarelo #facc15) — consistência visual | Tokens já em `frontend/app/(public)/public.css` `@theme`; apenas verificar, sem mudança |
| BRND-04 | Hosts atualizados — backend `https://empreganoix.onrender.com`, frontend `https://empreganoix.vercel.app`; CORS configurado | Config via env vars + dashboards; smoke gate `scripts/verify-deploy.ps1` |

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Content rename (textos/meta/tags) | Frontend (Next.js) + Backend (FastAPI) | Docs/Planning | Strings vivem no código-fonte; não há runtime config |
| Brand assets (logo/favicon/og) | CDN/Static (Vercel public/) | Frontend metadata | Arquivos estáticos servidos pela Vercel; metadata referenciados no layout |
| Host/CORS/env alignment | API/Backend (FastAPI settings) | Frontend (Next build) | CORS validado no boot do backend; `NEXT_PUBLIC_*` inlined no build |
| Turnstile hostname allow-list | External (Cloudflare dashboard) | — | Configuração vive fora do repo |
| Deploy + smoke gate | Infra (Vercel/Render/GitHub) | — | Dashboards + PowerShell gate |

## Standard Stack

Nenhuma biblioteca nova. Reusar o stack travado:

### Core (já fixado)
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| Next.js (App Router) | 16.4.6 | Frontend | Fixed; metadata API (`icons`, `openGraph.images`) usada para favicon/og |
| Tailwind CSS | 4.3.3 | Styling | `@theme` em `public.css` já carrega os tokens da marca |
| FastAPI | 0.143.0 | Backend | `FastAPI(title=...)` em `backend/app/main.py` |
| pydantic-settings | 2.x | Env validation | CORS fail-closed já implementado (T-09-13) |

### Supporting (já presentes)
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| next (metadata file convention) | 16.4.6 | `app/icon.png`, `app/apple-icon.png`, `app/opengraph-image.png`, `app/favicon.ico` | Auto-gera tags `<link rel="icon">` e `og:image` sem config manual |
| Image generation (OpenCode tool) | — | Gerar logo/favicon/og-image PNG/SVG | D-05 — OpenCode gera os assets |

**Installation:** nenhuma instalação adicional.

**Version verification:** não aplicável (sem pacote novo).

## Architecture Patterns

### System Architecture Diagram

```text
┌─────────────────────────────────────────────────────────────────────┐
│                    Phase 10 — Rebranding & Launch                   │
└─────────────────────────────────────────────────────────────────────┘

  ┌──────────────┐     ┌──────────────┐     ┌──────────────┐
  │  Code rename │────►│  Asset gen   │────►│  Host/env    │
  │  (Wave 1)    │     │  (Wave 1)    │     │  (Wave 2)    │
  └──────────────┘     └──────────────┘     └──────┬───────┘
                                                   │
                                                   ▼
  ┌──────────────┐     ┌──────────────┐     ┌──────────────┐
  │  Cloudflare  │◄────│   Deploy     │────►│  Smoke gate  │
  │  Turnstile   │     │  Vercel+     │     │ verify-deploy│
  │  Hostnames   │     │  Render      │     │   .ps1       │
  └──────────────┘     └──────────────┘     └──────────────┘
```

Data flow (rename): edit source strings → rebuild frontend (Next inlines `NEXT_PUBLIC_*`) → deploy → smoke gate verifies new hosts.

### Recommended Project Structure (unchanged)
```
frontend/
├── app/
│   ├── icon.png              # NOVO (favicon 32x32/192) — file-based metadata
│   ├── apple-icon.png         # NOVO (180x180)
│   ├── opengraph-image.png    # NOVO (1200x630)
│   └── favicon.ico           # NOVO (opcional, retrocompat)
├── public/                    # NÃO existe hoje — criar se usar public/ em vez de app/
└── ...
backend/ ... (sem mudança estrutural)
```

### Pattern 1: Mechanical Rename via grep-driven edits
**What:** Substituir todas as ocorrências de `NaoQueroUsar`, `NQU`, `suportenqs@outlook.com`, hosts antigos em arquivos de código/docs/config, **exceto** o diretório do repo e `.planning/` paths (D-01).
**When to use:** Sempre que um rename de marca for necessário.
**Example:**
```ts
// frontend/app/(public)/layout.tsx
title: "EmpregaNoix — Vagas sem cadastro",
// wordmark
EmpregaNoix
// footer
© 2026 EmpregaNoix
```
```python
# backend/app/main.py
app = FastAPI(title="EmpregaNoix API", lifespan=lifespan)
```

### Pattern 2: Next.js File-Based Metadata for Brand Assets
**What:** Colocar `icon.png`, `apple-icon.png`, `opengraph-image.png` em `frontend/app/` para que o Next gere automaticamente `<link rel="icon">`, `<link rel="apple-touch-icon">` e `<meta property="og:image">`. Alternativa: manter em `public/` e referenciar em `export const metadata`.
**When to use:** D-05 — assets novos.
**Example (metadata-based, se assets em public/):**
```ts
export const metadata: Metadata = {
  title: "EmpregaNoix — Vagas sem cadastro",
  description: "...",
  icons: { icon: "/favicon.ico", apple: "/apple-touch-icon.png" },
  openGraph: { images: ["/og-image.png"] },
};
```

### Pattern 3: Env-Driven Hosts (no code change)
**What:** Hosts vivem em env vars (`NEXT_PUBLIC_API_URL`, `BACKEND_API_URL`, `CORS_ORIGINS`). O código não tem host hardcoded (confirmado por grep). A troca de marca de host é configuração de dashboard + rebuild.
**When to use:** BRND-04.

### Anti-Patterns to Avoid
- **Renomear o diretório do repo/`.planning`:** quebra paths absolutos em scripts/docs, histórico git e a sessão OpenCode (D-01). Não fazer.
- **Manter host antigo como redirect:** fora de escopo (deferred). Lançamento apenas sob nova marca.
- **Trocar `NEXT_PUBLIC_TURNSTILE_SITE_KEY` sem rebuild:** a chave é inlined no build (T-03-18). Sempre rebuild após trocar.
- **Editar migration 0001 para renomear:** migrations são forward-only; o rename de marca não toca schema. Não editar histórico.
- **Atualizar testes para passar com host novo de forma a mascarar regressão:** os testes de CORS usam host antigo como *exemplo* de origem válida; podem ser atualizados para o novo host por consistência, mas a asserção de comportamento (echo exato, reject foreign) deve permanecer.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Favicon/og tags | `<link>`/`<meta>` manual em cada layout | Next.js file-based metadata (`app/icon.png`) ou `metadata.icons` | Next gera tamanhos e `apple-touch-icon` automaticamente |
| Logo SVG/PNG | Desenhar à mão em código | OpenCode image generation (D-05) | Identidade visual completa; fallback wordmark textual |
| Host rename em código | Buscar/substituir hosts hardcoded | Env vars já existentes | Nenhum host hardcoded no código (grep confirmou) |
| Deploy orchestration | Script que chama APIs da Vercel/Render | Dashboards manuais + smoke gate | CLIs não instalados (ver Environment Availability) |

**Key insight:** Este phase é 90% configuração/operacional. O código já está pronto; o risco é esquecer um dashboard/env/hostname.

## Runtime State Inventory

> Esta fase é rename/refactor/migration (conteúdo + hosts). Resposta explícita para as 5 categorias.

| Category | Items Found | Action Required |
|----------|-------------|------------------|
| Stored data | Neon `jobs` table: campo `company` em linhas seed ("NQU Seed"). Nenhuma string de marca em schema/coluna. Mem0/n8n/Redis não aplicáveis. | Code edit apenas (seed.py futuro). Linhas existentes não precisam de migration; se desejado, UPDATE pontual em dev. |
| Live service config | Vercel project env vars (`NEXT_PUBLIC_API_URL`, `BACKEND_API_URL`, `NEXT_PUBLIC_TURNSTILE_SITE_KEY`); Render service env vars (`CORS_ORIGINS`, `ENV`, `TURNSTILE_*`, `CRON_SECRET`); Cloudflare Turnstile Hostnames list; GitHub Actions `vars.API_BASE_URL` + `secrets.CRON_SECRET`. | Atualização manual nos dashboards (human checkpoint). Turnstile Hostnames: adicionar `empreganoix.vercel.app`. |
| OS-registered state | Nenhum. APScheduler é in-process; GitHub Actions cron usa `vars.API_BASE_URL`. Nenhum task scheduler/pm2/launchd/systemd. | Nenhuma. |
| Secrets/env vars | Nomes de secret não mudam (`CRON_SECRET`, `JWT_SECRET`, etc.). Valores de `CRON_SECRET` já existem localmente (43 chars, não commitado). `.env`/`.env.local` gitignored. | Copiar valores existentes para dashboards; não rotacionar (a menos que desejado). |
| Build artifacts | `frontend/.next` contém `NEXT_PUBLIC_API_URL` antigo inlined; `__pycache__`, `.pytest_cache`. Backend usa uv (sem egg-info). | Rebuild frontend após env change; limpar `.next` antes do deploy. `npm run build` regenera. |

**Nothing found in category:** OS-registered state — verificado (nenhum scheduler externo; APScheduler in-process).

## Common Pitfalls

### Pitfall 1: `NEXT_PUBLIC_*` inlined no build
**What goes wrong:** Trocar env var no dashboard sem rebuild deixa o bundle apontando para host antigo.
**Why it happens:** Next inlina `NEXT_PUBLIC_*` em build time (T-03-18).
**How to avoid:** Sempre redeploy (rebuild) após trocar `NEXT_PUBLIC_API_URL`/`NEXT_PUBLIC_TURNSTILE_SITE_KEY`.
**Warning signs:** Bundle cliente mostra host antigo (verificado no smoke anterior — "A first fetch of the API chunk briefly showed a `naquerousar` host").

### Pitfall 2: CORS lido no boot
**What goes wrong:** Atualizar `CORS_ORIGINS` no Render sem redeploy não tem efeito.
**Why it happens:** Settings carregado no startup (lru_cache).
**How to avoid:** Redeploy do backend após ajuste; smoke gate confirma `Access-Control-Allow-Origin`.

### Pitfall 3: Turnstile Hostnames
**What goes wrong:** Widget recusa domínio não cadastrado → reveal/login falham em prod mesmo com chaves corretas.
**Why it happens:** Cloudflare valida hostname do widget.
**How to avoid:** Adicionar `empreganoix.vercel.app` ao widget de produção antes do deploy; remover host antigo (opcional).

### Pitfall 4: Testes de CORS com host antigo
**What goes wrong:** `test_cors.py` usa `https://nao-quero-usar.vercel.app` como exemplo; após rename, pode-se atualizar para novo host por consistência, mas não é obrigatório para passar (são strings de teste, não config).
**How to avoid:** Atualizar para `https://empreganoix.vercel.app` para manter coerência (BRND-04), mantendo asserções de comportamento.

### Pitfall 5: Esquecer `.planning`/docs (D-01 permite atualizar conteúdo)
**What goes wrong:** Deixar "NQU — NaoQueroUsar" em PROJECT.md/README/ROADMAP após rename de código → inconsistência de marca.
**How to avoid:** Incluir docs/README/pyproject/alembic.ini/seed/main.py/AGENTS.md na onda de rename.

### Pitfall 6: Assets de marca atrasando deploy
**What goes wrong:** Bloquear BRND-04 esperando logo perfeito.
**How to avoid:** D-05 — wordmark textual "EmpregaNoix" como fallback; deploy não bloqueia.

### Pitfall 7: Smoke gate com host errado
**What goes wrong:** Rodar `verify-deploy.ps1` com hosts antigos.
**How to avoid:** Sempre passar `-FrontendUrl https://empreganoix.vercel.app -BackendUrl https://empreganoix.onrender.com`.

## Code Examples

### Rename wordmark + metadata (frontend)
```tsx
// frontend/app/(public)/layout.tsx
export const metadata: Metadata = {
  title: "EmpregaNoix — Vagas sem cadastro",
  description: "Encontre vagas e o contato para se candidatar em segundos. Sem conta, sem login e sem burocracia.",
  icons: { icon: "/favicon.ico", apple: "/apple-touch-icon.png" },
  openGraph: { images: ["/og-image.png"] },
};
// header wordmark
EmpregaNoix
// footer
© 2026 EmpregaNoix
```

### Rename backend title
```python
# backend/app/main.py
app = FastAPI(title="EmpregaNoix API", lifespan=lifespan)
```

### WhatsApp template
```ts
// frontend/lib/contacts.ts
return `Olá! Vi a vaga "${title}" no EmpregaNoix e quero me candidatar.`;
```

### Seed company
```python
# backend/scripts/seed.py
company="EmpregaNoix Seed",
```

### Legal pages (controller + email)
```
O site EmpregaNoix é operado por ...
empreganoix@outlook.com
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| NaoQueroUsar / NQU brand | EmpregaNoix brand | Phase 10 (2026-11-14) | Todos os textos/meta/assets |
| Hosts antigos (nao-quero-usar.vercel.app / naoquerousar.onrender.com) | empreganoix.vercel.app / empreganoix.onrender.com | Phase 10 | CORS/env/Turnstile hostnames |
| Deploy adiado (Phase 6 opção B) | Deploy real agora | D-04 (2026-11-14) | Fecha BRND-04 + Phase 6 |

**Deprecated/outdated:**
- Hosts antigos: não mantidos como redirect (deferred).
- `suportenqs@outlook.com`: substituído por `empreganoix@outlook.com`.

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | Nenhum host hardcoded no código (apenas env vars) | Architecture Patterns | Se houver host hardcoded em algum componente não grepado, o rename de host falha em runtime |
| A2 | Cloudflare Turnstile permite cadastrar `*.vercel.app` como hostname (confirmado por docs anteriores) | Common Pitfalls | Se não permitir, deploy bloqueia reveal/login |
| A3 | File-based metadata (`app/icon.png`) é suportado no Next 16.4.6 (sim, desde Next 13) | Architecture Patterns | Se houver conflito com metadata export, usar `public/` + `metadata.icons` |
| A4 | Apenas um job seed com "NQU Seed" no banco dev; nenhum dado de produção ainda | Runtime State Inventory | Se houver dados de produção com "NQU" em campos livres, precisariam de UPDATE |

**If this table is empty:** N/A — 4 assumptions listadas.

## Open Questions (RESOLVED)

1. **Logo completo atrasa?** — RESOLVED: D-05 permite fallback wordmark textual; assets gerados em Wave 1, deploy não bloqueia se faltarem.
   - What we know: D-05 permite fallback wordmark textual.
   - What's unclear: Se o image generation produzirá qualidade aceitável.
   - Recommendation: Gerar assets em Wave 1; se não aprovados, seguir com wordmark e não bloquear deploy.

2. **Turnstile live keys disponíveis?** — RESOLVED: preferir modo live (BRND-04 exige `turnstile.mode=live`); escape hatch `ALLOW_TEST_TURNSTILE=true` apenas documentado se live keys não estiverem prontas.
   - What we know: Escape hatch `ALLOW_TEST_TURNSTILE=true` existe (desvio temporário).
   - What's unclear: Se o operador já criou o widget de produção com hostname novo.
   - Recommendation: Preferir modo live (BRND-04 exige `turnstile.mode=live`); usar escape hatch apenas se live keys não estiverem prontas, documentando.

3. **GitHub Actions `vars.API_BASE_URL` já configurado?** — RESOLVED: atualizar para `https://empreganoix.onrender.com` no checkpoint humano (Task 2 do 10-04).
   - What we know: Workflow lê `vars.API_BASE_URL`.
   - What's unclear: Se já está setado para host antigo.
   - Recommendation: Atualizar para `https://empreganoix.onrender.com` (human checkpoint).

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| Node.js | Frontend build | ✓ | 22.23.4 | — |
| npm | Frontend deps | ✓ | 10.9.9 | — |
| Python | Backend | ✓ | 3.13.3 | — |
| uv | Backend deps/migrations | ✓ | 0.13.1 | pip |
| git | Version control | ✓ | 2.43.0 | — |
| PowerShell 5.1 | Smoke gate | ✓ | (Windows) | — |
| Vercel CLI | Deploy | ✗ | — | Dashboard manual (root dir `frontend`) |
| Render CLI | Deploy | ✗ | — | Dashboard manual (blueprint) |
| GitHub CLI | Actions vars | ✗ | — | Dashboard manual |

**Missing dependencies with no fallback:**
- Nenhuma bloqueante para o rename local. Deploy requer dashboards (manual por design — `autoDeploy: false`).

**Missing dependencies with fallback:**
- Vercel/Render/GitHub CLIs ausentes → usar dashboards (já é o fluxo documentado em docs/DEPLOY.md).

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest 9.1.1 (backend) + Vitest 5.0.4 (frontend, se aplicável) |
| Config file | `backend/pyproject.toml` (`[tool.pytest.ini_options]`) |
| Quick run command | `cd backend; .venv\Scripts\python.exe -m pytest -q` |
| Full suite command | `cd backend; .venv\Scripts\python.exe -m pytest -q` (backend) + `cd frontend; npm run lint && npm run build` |

### Phase Requirements → Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| BRND-01 | Nenhum "NaoQueroUsar"/"NQU"/"suportenqs" em código frontend (exceto .planning) | grep/CI | `grep -rn "NaoQueroUsar\|suportenqs" frontend/` (deve ser vazio) | ❌ Wave 0 |
| BRND-02 | Slogan presente em layout.tsx e admin layout | grep | `grep -rn "Procurar um emprego, não deve dar trabalho" frontend/` | ✅ |
| BRND-03 | Tokens @theme intactos (#8b5cf6/#a78bfa/#facc15) | grep | `grep -n "#8b5cf6\|#a78bfa\|#facc15" frontend/app/(public)/public.css` | ✅ |
| BRND-04 | Smoke gate verde com novos hosts | E2E/manual | `powershell -File scripts\verify-deploy.ps1 -FrontendUrl https://empreganoix.vercel.app -BackendUrl https://empreganoix.onrender.com` | ✅ |

### Sampling Rate
- **Per task commit:** `cd backend; .venv\Scripts\python.exe -m pytest -q` (backend) + `cd frontend; npm run build` (frontend)
- **Per wave merge:** Full suite + build
- **Phase gate:** Smoke gate verde (`verify-deploy.ps1` → `all checks passed`)

### Wave 0 Gaps
- [ ] `grep`-based assertion (ou script) para BRND-01 (nenhum leftover "NaoQueroUsar"/"NQU"/"suportenqs" em código)
- [ ] Atualizar `backend/tests/test_cors.py` exemplos para novo host (consistência)
- [ ] Criar assets de marca (favicon, og-image) — D-05

*(Se não houver gaps além dos acima: "None — existing test infra covers rename assertions via grep")*

## Security Domain

### Applicable ASVS Categories

| ASVS Category | Applies | Standard Control |
|---------------|---------|-----------------|
| V2 Authentication | no (sem mudança) | — |
| V3 Session Management | no | — |
| V4 Access Control | yes | CORS fail-closed (T-09-13) — hosts novos devem ser exatos |
| V5 Input Validation | yes | pydantic-settings valida env (CORS_ORIGINS, Turnstile) |
| V6 Cryptography | yes | JWT_SECRET/CRON_SECRET não rotacionados; mantidos |

### Known Threat Patterns for {stack}

| Pattern | STRIDE | Standard Mitigation |
|---------|--------|---------------------|
| CORS permissivo em prod | Tampering | Fail-closed validator (T-09-13) + smoke gate preflight |
| Secret leak no bundle | Information Disclosure | `NEXT_PUBLIC_*` apenas vars públicas; nunca secrets |
| Turnstile bypass via host não cadastrado | Spoofing | Cadastrar hostname no widget; modo live verificado no health |
| Stale build com host antigo | Availability | Rebuild obrigatório após env change |

## Rename Inventory (superfícies confirmadas por grep)

### Frontend
- `frontend/app/(public)/layout.tsx` — title, wordmark (header/footer), copyright
- `frontend/app/(public)/page.tsx` — (verificar headings/empty states)
- `frontend/app/(public)/privacidade/page.tsx` — title/desc, "NQU", email
- `frontend/app/(public)/termos-de-uso/page.tsx` — title/desc, "NQU", email
- `frontend/app/(public)/doacoes/page.tsx` — title/corpo
- `frontend/app/admin/layout.tsx` — title, wordmark
- `frontend/lib/contacts.ts` — template WhatsApp
- `frontend/.env.example` — comentário "NQU"
- `frontend/app/layout.tsx` — (sem nome de marca, mas verificar metadata default)

### Backend
- `backend/app/main.py` — `FastAPI(title="NQU API")`
- `backend/alembic.ini` — comentário "NQU backend"
- `backend/alembic/versions/0001_initial_jobs.py` — comentário "NQU"
- `backend/pyproject.toml` — description "NQU backend", name `nqu-backend`
- `backend/scripts/seed.py` — `company="NQU Seed"`
- `backend/README.md` — "NQU Backend"
- `backend/tests/test_cors.py` — exemplos de host (atualizar por consistência)

### Docs / Infra / Planning
- `README.md` (raiz) — "# NQU — NaoQueroUsar"
- `AGENTS.md` — "# NQU — NaoQueroUsar" (primeira linha do bloco GSD project)
- `docs/DEPLOY.md` — título e exemplos de host antigo
- `render.yaml` — comentário "NQU"
- `scripts/verify-deploy.ps1` — comentário "NaoQueroUsar"
- `.planning/PROJECT.md`, `.planning/REQUIREMENTS.md`, `.planning/ROADMAP.md`, `.planning/STATE.md` — títulos/refs (conteúdo apenas; diretório mantido)
- `.planning/research/*.md` — refs "NQU" (opcional, baixa prioridade)

## Sources

### Primary (HIGH confidence)
- CONTEXT.md (Phase 10) — decisões D-01..D-06, escopo, canonical refs
- `frontend/app/(public)/public.css` — tokens @theme verificados
- `backend/app/core/config.py` — CORS fail-closed verificado
- `backend/app/main.py` — FastAPI title verificado
- `scripts/verify-deploy.ps1` — smoke gate verificado
- `docs/DEPLOY.md` — runbook verificado

### Secondary (MEDIUM confidence)
- `backend/tests/test_cors.py` — exemplos de host antigo
- STATE.md — histórico de deploy (2026-11-12) confirmando hosts antigos e falha de CORS

### Tertiary (LOW confidence)
- Nenhuma claim LOW não-verificada incluída.

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — nenhum pacote novo; stack travado e verificado no repo
- Architecture: HIGH — rename mecânico; hosts via env vars confirmado por grep
- Pitfalls: HIGH — derivados do histórico real (STATE.md deploy 2026-11-12) e código

**Research date:** 2026-11-14
**Valid until:** 2026-12-14 (30 dias para fase de rename/deploy)
