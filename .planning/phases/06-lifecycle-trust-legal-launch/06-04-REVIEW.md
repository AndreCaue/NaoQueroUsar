# 06-04 — Revisão do plano de deploy

**Data:** 2026-11-10
**Escopo:** `06-04-PLAN.md`, `06-04-SUMMARY.md`, `render.yaml`, `.github/workflows/expire-cron.yml`, `frontend/vercel.json`, `docs/DEPLOY.md`, `scripts/verify-deploy.ps1` — confrontados com o código atual (`backend/app/**`, `frontend/**`).
**Método:** leitura integral dos artefatos + verificação estática contra o código (rotas do build, `Settings` do Pydantic, engine async, endpoint de expiração, CORS, páginas legais finais, `lib/jobs.ts`).
**Veredito:** o desenho do deploy está correto (Render + Vercel + cron de catch-up + gate reproduzível), mas **3 achados bloqueantes** impediriam um go-live correto — todos corrigidos nos artefatos neste review. Nada foi deployado; a Fase 6 continua aberta (decisão "opção B", 2026-11-10).

---

## Resumo dos achados

| ID | Severidade | Achado | Status |
|----|------------|--------|--------|
| REV-01 | **BLOCKER** | Check 5 do gate procurava `intermedi` em `/privacidade`; o texto legal final não usa essa palavra (o aviso de intermediário está em `/termos-de-uso`) → gate falharia num deploy correto | **Corrigido** |
| REV-02 | **BLOCKER** | Runbook e plano mandavam gerar `ADMIN_PASSWORD_HASH` com `passlib`, removido em IN-07 (incompatível com bcrypt 5.x) → comando do operador falha | **Corrigido** |
| REV-03 | **BLOCKER** | `DATABASE_URL` documentada como a string "pooled" do Neon sem trocar o esquema para `postgresql+asyncpg://` → SQLAlchemy procuraria psycopg2 (não instalado) e o boot morreria no `alembic upgrade head` | **Corrigido** |
| REV-04 | HIGH | Runbook/plano mandavam abrir `/admin/login`, rota que não existe (login é inline em `/admin/paste`) → 404 no checkpoint humano | **Corrigido** |
| REV-05 | HIGH | Task 1 do plano dizia `autoDeploy: true`; o `render.yaml` real e o runbook dizem `false` (deploy manual por causa de migrações forward-only) | **Corrigido** |
| REV-06 | HIGH | Check 10 media "cold-start" numa chamada posterior aos checks 1–8 → media o caminho já aquecido e nunca observaria o caso > 15 s | **Corrigido** |
| REV-07 | MEDIUM | Runbook não mandava cadastrar o domínio da Vercel em **Turnstile → Hostnames**; o widget recusa domínios não listados mesmo com as chaves certas | **Corrigido** |
| REV-08 | MEDIUM | `/privacidade` e `/termos-de-uso` estão no route group `(public)` (que já tem `<main>`/header/footer) mas renderizam `<main>`/header próprios, com cores fora dos tokens; o footer só linka `/privacidade` ("Privacidade e termos") → Termos órfão | **Aberto** (UI autoral; recomendação abaixo) |
| REV-09 | LOW | `uv run` no `startCommand` re-sincroniza o ambiente a cada boot e inclui o grupo `dev` por padrão — custo extra no cold-start | **Aberto** (otimização opcional) |
| REV-10 | LOW | `SCHEDULER_ENABLED` é citado no runbook mas não está no `render.yaml`; no plano free o scheduler in-process é best-effort | **Aberto** (consciência operacional) |
| REV-11 | LOW | Runbook dizia "Next.js 15/16"; o projeto está fixado em Next 15 | **Corrigido** |
| REV-12 | LOW | Runbook/plano passavam `-CronSecret` pela linha de comando (fica no histórico/processo); o script já lê `$env:CRON_SECRET` | **Corrigido** |
| REV-13 | LOW | `verify-deploy.ps1` não fixava TLS 1.2; PowerShell 5.1/.NET antigo pode falhar o handshake com Render/Vercel | **Corrigido** |
| REV-14 | LOW | Script não segue redirect (`AllowAutoRedirect = $false`): um alias da Vercel que responde 308 quebra o check 4 com status inesperado | **Corrigido** (documentado) |

---

## Detalhe dos bloqueadores

### REV-01 — O gate procurava o aviso de intermediário no lugar errado

**Evidência:** `scripts/verify-deploy.ps1` (versão anterior) fazia:
```powershell
Assert ($legal.Body -imatch 'intermedi') "/privacidade não contém 'intermedi' (Aviso de Intermediário)"
```
Mas o texto final do usuário (`frontend/app/(public)/privacidade/page.tsx`, 13 seções) não usa "intermedi" — ele fala em "facilitar o contato". O aviso de intermediário vive em `frontend/app/(public)/termos-de-uso/page.tsx:46` ("não realiza processos seletivos, não intermediaria contratações e não atua como agência"). A página combinada antiga ("Privacidade, Termos e Aviso Legal") foi substituída, então a asserção ficou stale.

**Impacto:** um deploy 100% correto falharia o gate no check 5, bloqueando o go-live por um falso negativo.

**Correção aplicada:**
- `/privacidade`: 200 + `LGPD` + **canal de contato por e-mail** (regex, sem acoplar ao endereço) + ausência de `Lorem ipsum`/`provisóri`/`[Seu Nome`/`[seu e-mail`.
- `/termos-de-uso`: 200 + `intermedi` + ausência de `[sua cidade`/placeholders.
- Check 9 (não vazamento) também passa a olhar o corpo de `/termos-de-uso`.
- `06-04-PLAN.md` (Task 2, check 5 e asserts) e `docs/DEPLOY.md` atualizados na mesma direção.

### REV-02 — Hash de senha com biblioteca removida

**Evidência:** `backend/pyproject.toml:15` declara `bcrypt>=4.0,<6.0`; `backend/app/core/security.py` importa `bcrypt` diretamente. `passlib` foi removido em IN-07 (`00bcab5`) porque o 1.7.4 é incompatível com o `bcrypt` 5.0.0 travado (`01-03-SUMMARY` deviation 1). Ainda assim, `docs/DEPLOY.md` e o `user_setup` do plano mandavam `from passlib.context import CryptContext`.

**Impacto:** o operador não conseguiria gerar o hash — o passo 2 do checkpoint humano travaria.

**Correção aplicada:** comando único em `docs/DEPLOY.md` e no plano:
```powershell
.\.venv\Scripts\python.exe -c "import bcrypt; print(bcrypt.hashpw(b'SEU_SEGREDO', bcrypt.gensalt()).decode())"
```
Com nota do limite de 72 bytes do bcrypt.

### REV-03 — `DATABASE_URL` sem o driver asyncpg

**Evidência:** `backend/app/db/session.py:14-19` cria o engine com `create_async_engine(settings.DATABASE_URL, ..., connect_args={"statement_cache_size": 0})`; `backend/alembic/env.py:27` injeta a mesma URL e `:62` usa `async_engine_from_config`. O `pyproject.toml` instala **apenas** `asyncpg` (não há psycopg/psycopg2). A connection string que o Neon copia começa com `postgresql://...`.

**Impacto:** com `postgresql://`, o SQLAlchemy tenta o driver síncrono padrão (psycopg2) antes de qualquer conexão → `ModuleNotFoundError` no `alembic upgrade head` → boot em loop no Render. É o bloqueador mais provável de acontecer na prática, porque o operador copia e cola do Neon.

**Correção aplicada:** o runbook agora exige explicitamente `postgresql+asyncpg://` + `?ssl=require` + host `-pooler`, explica o motivo e adiciona um diagnóstico no passo de health ("se o boot falhar no `alembic upgrade head`, confira primeiro `DATABASE_URL`"). O plano e o SUMMARY receberam a mesma instrução.

---

## Detalhe dos achados HIGH/MEDIUM

### REV-04 — Rota de login inexistente

Rotas reais do build: `/admin`, `/admin/paste`, `/admin/review` (não existe `/admin/login`). O login é inline em `frontend/app/admin/paste/ExtractForm.tsx:138-166` (`Senha do admin` + widget Turnstile + botão `Entrar`), e `components/admin/AdminGuard.tsx:27-29` redireciona para `/admin/paste` quando não há token. Corrigido em `docs/DEPLOY.md` (checklist + registro), `06-04-PLAN.md` (Task 3, passo 9) e `06-04-SUMMARY.md` (User Setup, item 9).

### REV-05 — `autoDeploy` divergente entre plano e artefato

`render.yaml:40` tem `autoDeploy: false` e o runbook explica por quê (migrações forward-only, sem rollback de schema). O texto da Task 1 do plano ainda dizia `autoDeploy: true`. Corrigido para `false`, com a justificativa, para que uma futura re-execução do plano não regrida o blueprint.

### REV-06 — Cold-start medido no lugar errado

O check 10 antigo disparava **outra** requisição a `/api/v1/public/jobs` **depois** dos checks 1–8 (que já bateram no backend várias vezes). Num deploy com spin-down, o número reportado seria a latência aquecida e o aviso de "> 15 s" nunca apareceria — justamente o critério de sucesso 5 que o check deveria observar.

**Correção aplicada:** o cronômetro começa no check 1 (primeiro request ao backend, o `GET /api/v1/health`) e o check 10 apenas reporta essa latência. O runbook agora instrui: rode o gate como **primeiro** tráfego após ~20 min ociosos, antes de abrir o board.

### REV-07 — Hostname do Turnstile fora do runbook

O widget de produção só funciona nos domínios cadastrados no Cloudflare. Com as chaves corretas, mas sem o domínio da Vercel em **Hostnames**, o reveal e o login falham (o siteverify rejeita). Adicionado aos pré-requisitos, ao passo 3 da Vercel (plano), ao checklist de go-live e ao SUMMARY.

### REV-08 — Páginas legais: aninhamento de layout e Termos órfão (aberto)

`frontend/app/(public)/layout.tsx` já renderiza `<main>` (linha 53), header e footer. As duas páginas legais estão nesse route group e **também** renderizam `<main>` + header próprio (`privacidade/page.tsx:5-36`, `termos-de-uso/page.tsx:5-36`), o que produz dois landmarks `<main>` no mesmo documento, header duplicado e estilos fora dos tokens do design (`bg-gray-900`, `text-white`, `hover:text-accent-strong`).

Além disso, o footer (`layout.tsx:61-66`) mostra o rótulo **"Privacidade e termos"** e linka **só** `/privacidade`; `/termos-de-uso` só é alcançável pelo link interno da página de privacidade. O critério de sucesso 4 do ROADMAP exige que privacidade, termos e o aviso de intermediário sejam **acessíveis**.

**Recomendação (não aplicada neste review, por ser UI autoral do usuário):**
1. Nas duas páginas, remover o `<main>`/`<div max-w-3xl>`/header próprio e devolver só o `<article>` (o layout já dá header, main e footer). Trocar `bg-gray-900`/`text-white`/`text-accent-strong` pelos tokens (`text-fg`, `text-fg-muted`, `text-accent-soft`).
2. No footer, trocar o link único por dois links (`/privacidade` "Privacidade" e `/termos-de-uso` "Termos de uso").
3. Opcional: um `metadata` por página (`title`/`description`) para SEO — as duas rotas hoje herdam o título do layout.

### REV-09 — `uv run` no boot (aberto, otimização)

`startCommand` usa `uv run alembic upgrade head && uv run uvicorn ...`. `uv run` garante o ambiente sincronizado antes de executar e, sem flags, inclui o grupo `dev` (pytest), além de revalidar o lock a cada boot — inclusive no wake-up do spin-down. Sugestão: `uv run --frozen --no-dev` nos dois comandos (ou `UV_NO_SYNC=1` no serviço), mantendo `uv sync --frozen --no-dev` no build. Não aplicado para não alterar o artefato já validado sem uma execução real de deploy.

### REV-10 — `SCHEDULER_ENABLED` (aberto, consciência operacional)

O `Settings` tem `SCHEDULER_ENABLED: bool = True` (`backend/app/core/config.py:59`) e o runbook cita a variável, mas ela não é declarada no `render.yaml`. No plano free o processo dorme, então o APScheduler interno é best-effort; o cron do GitHub é o catch-up confiável. Não é bloqueio (o default correto já vale), mas convém decidir explicitamente antes do go-live e registrar no checklist.

---

## O que já está correto (verificado)

- **Segredos:** `render.yaml` usa `sync: false` em todos os valores sensíveis; nenhum valor real versionado; workflow usa `secrets.CRON_SECRET`/`vars.API_BASE_URL` e `permissions: {}`.
- **Cron:** `.github/workflows/expire-cron.yml` agenda `0 3 * * *` (UTC) + `workflow_dispatch`, `concurrency` sem cancelamento, `--retry-connrefused`, falha com mensagem clara se as variáveis estiverem vazias e não ecoa o secret.
- **Expiração:** `POST /api/v1/admin/expire` depende de `require_cron_secret`, responde 503 quando não configurado (fail-closed) e 401 com segredo errado; é idempotente (`deleted: 0` na segunda chamada) — coerente com o gate.
- **Health:** `backend/app/api/v1/health.py` devolve `status`, `env` e `turnstile.mode` sem expor o segredo — exatamente o que o check 1 assere.
- **CORS:** `backend/app/main.py:38-45` usa `settings.cors_origins_list`, `allow_credentials=False` e `expose_headers=["Retry-After"]`; os checks 2/3 (origem exata + `evil.example`) batem com esse desenho.
- **Frontend:** `lib/jobs.ts:16-21` prioriza `BACKEND_API_URL` e usa `TIMEOUT_MS = 15_000` com `cache: "no-store"`; `lib/api.ts` falha o build sem `NEXT_PUBLIC_API_URL` (WR-04); `error.tsx` tem a copy de cold-start.
- **Vercel:** `frontend/vercel.json` é JSON válido e mínimo; Root Directory `frontend` está documentado (não codificado, correto).
- **Gate:** `-CronSecret` obrigatório para o check autenticado, 401/403/503 tratados como recusa válida, nenhuma chamada destrutiva sem segredo.

---

## Pré-requisitos ainda ausentes para o go-live (dependem do usuário)

1. Projeto **Neon de produção** (separado de dev/test) e a connection string pooled convertida para `postgresql+asyncpg://`.
2. Conta/serviço no **Render** + blueprint aplicado e deploy **manual** disparado.
3. Conta/projeto na **Vercel** com Root Directory `frontend` e as 3 variáveis (`BACKEND_API_URL`, `NEXT_PUBLIC_API_URL`, `NEXT_PUBLIC_TURNSTILE_SITE_KEY`).
4. **Turnstile de produção** (site key + secret) com o domínio da Vercel em **Hostnames**.
5. `GROQ_API_KEY`, `ADMIN_PASSWORD_HASH` (bcrypt), `JWT_SECRET`, `CRON_SECRET`.
6. `vars.API_BASE_URL` + `secrets.CRON_SECRET` no GitHub.
7. Smoke gate real + registro de URLs/cold-start em `docs/DEPLOY.md`.

Nada disso foi executado: não houve deploy, não houve smoke de produção e a Fase 6 permanece aberta por decisão do usuário (opção B).

---

## Ordem recomendada quando o lançamento for retomado

1. Neon de produção (pooled + `postgresql+asyncpg://` + `?ssl=require`), região anotada.
2. Render: blueprint, segredos, deploy manual, `alembic upgrade head` OK, health `env=prod`/`mode=live`.
3. Vercel: Root Directory `frontend`, env vars, Turnstile hostname, deploy.
4. Voltar `CORS_ORIGINS` para a origem exata da Vercel e redeployar o backend.
5. GitHub: `vars.API_BASE_URL` + `secrets.CRON_SECRET`, rodar `expire-jobs` manualmente.
6. Deixar o backend ocioso ~20 min e rodar `verify-deploy.ps1` **como primeiro tráfego**.
7. Fluxo real (busca → modal → reveal com Turnstile real → report → `/privacidade` → `/termos-de-uso`), admin em `/admin` → `/admin/paste` → `/admin/review`.
8. Preencher o **Registro de verificação** de `docs/DEPLOY.md` antes de declarar go-live.

---

## Alterações feitas neste review

| Arquivo | Mudança |
|---------|---------|
| `scripts/verify-deploy.ps1` | Check 5 reescrito (LGPD + canal em `/privacidade`; `intermedi` em `/termos-de-uso`; guarda de placeholders); check 9 cobre os Termos; check 10 mede o primeiro request; TLS 1.2 fixado; docstring atualizado. BOM/parse validados. |
| `docs/DEPLOY.md` | bcrypt no lugar de passlib; `postgresql+asyncpg://`; Turnstile Hostnames; Next 15; admin sem `/admin/login`; gate via `$env:CRON_SECRET` + domínio canônico + ordem do cold-start; checklist e registro atualizados. |
| `.planning/phases/06-lifecycle-trust-legal-launch/06-04-PLAN.md` | `autoDeploy: false`; bcrypt; esquema asyncpg; checks 5/7/9/10 do gate; rota de admin; Turnstile hostname; deploy manual; `$env:CRON_SECRET`; assert `/termos-de-uso`. |
| `.planning/phases/06-lifecycle-trust-legal-launch/06-04-SUMMARY.md` | Passos do User Setup alinhados (bcrypt, `postgresql+asyncpg://`, Turnstile hostname, admin, gate, cold-start, Termos). |
| `.planning/phases/06-lifecycle-trust-legal-launch/06-04-REVIEW.md` | Este documento. |
