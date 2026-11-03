# Deploy — NaoQueroUsar (NQU)

Runbook de produção: frontend na **Vercel**, backend **FastAPI** no **Render**, banco **Neon (Postgres)** e **GitHub Actions** como cron de catch-up da expiração.

> **Nenhum segredo real entra neste arquivo ou em qualquer arquivo versionado.** Todos os valores sensíveis são configurados apenas em variáveis de ambiente (Render/Vercel/GitHub). Onde este documento mostra `https://<backend>.onrender.com`, substitua pelos endereços reais do seu deploy.

---

## Arquitetura

```text
Navegador ──HTTPS──► Vercel (Next.js 15/16 App Router, SSR + server fetch)
                         │ cache: "no-store" com timeout de 15 s (frontend/lib/jobs.ts)
                         ▼
                 Render (FastAPI, plano free)
                   • GET  /api/v1/health            (público — status, nunca segredos)
                   • GET  /api/v1/public/jobs       (público)
                   • POST /api/v1/admin/expire      (X-Cron-Secret)
                   • /admin/*                        (JWT de admin)
                         │ SQLAlchemy async + asyncpg (pooled)
                         ▼
                    Neon (Postgres serverless)
                         ▲
                         │
              GitHub Actions (cron 03:00 UTC + workflow_dispatch)
              → POST /api/v1/admin/expire  (catch-up idempotente)
```

Fluxo de dados do board: o SSR da Vercel busca as vagas no backend (`BACKEND_API_URL`), o HTML servido **nunca** contém `contact_email`, `contact_phone` ou `mailto:` — o contato só aparece após o clique em "Mostrar contato" (Turnstile + rate limit).

**Schedulers de expiração (2 caminhos, 1 regra):**
1. **Primário** — APScheduler in-process (`backend/app/core/scheduler.py`), diário às 03:00 UTC com `misfire_grace_time=3600`, `coalesce=True`, `max_instances=1`.
2. **Catch-up** — GitHub Actions chamando `POST /api/v1/admin/expire` com `X-Cron-Secret`. Idempotente (re-chamar sem expirados responde `{"deleted": 0, "status": "ok"}`).

---

## Pré-requisitos

- [ ] Contas: **Vercel**, **Render**, **Neon**, **Cloudflare** (Turnstile), **Groq**, **GitHub**
- [ ] Repositório no GitHub com este código (branch de produção)
- [ ] Projeto **Neon de produção** separado do dev/test (nunca reutilize o banco de desenvolvimento)
- [ ] Cloudflare Turnstile: widget de **produção** criado (site key pública + secret privada). O widget de teste **não** é aceito em `ENV=prod` (o backend recusa a chave de teste — D-11/D-12)
- [ ] Chave da Groq (`https://console.groq.com/keys`)
- [ ] Senha de admin definida e hash **bcrypt** gerado localmente:
  ```powershell
  cd backend
  uv run python -c "from passlib.context import CryptContext; print(CryptContext(schemes=['bcrypt']).hash('SEU_SEGREDO'))"
  ```
- [ ] `JWT_SECRET`: 64 caracteres aleatórios
  ```powershell
  python -c "import secrets; print(secrets.token_urlsafe(64))"
  ```
- [ ] `CRON_SECRET`: 32+ caracteres aleatórios; o **mesmo valor** será usado no Render e no GitHub (`secrets.CRON_SECRET`)

---

## Backend no Render

1. **New → Blueprint** e selecione este repositório. O Render lê `render.yaml` da raiz:
   - `rootDir: backend` (o backend não vive na raiz do repo)
   - `buildCommand: pip install uv && uv sync --frozen --no-dev` (usa `pyproject.toml` + `uv.lock`; **não** há `requirements.txt`)
   - `startCommand: uv run alembic upgrade head && uv run uvicorn app.main:app --host 0.0.0.0 --port $PORT`
   - `healthCheckPath: /api/v1/health`
   - `region: ohio` — **alinhe à região do seu projeto Neon** (Neon → Project → Settings → General → Region)
2. Preencha os env vars abaixo no dashboard (Environment). Os marcados `sync: false` no `render.yaml` **não** têm valor no git:

   | Variável | Valor / origem | Notas |
   |---|---|---|
   | `ENV` | `prod` (já no blueprint) | Ativa o validador que recusa Turnstile de teste |
   | `PYTHON_VERSION` | `3.11.9` (já no blueprint) | |
   | `JWT_EXPIRES_IN` | `43200` (já no blueprint) | 12 h |
   | `DATABASE_URL` | Neon → Dashboard → Connection string **pooled** (host com `-pooler`) + `?ssl=require` | Nunca a string "direct" para tráfego web |
   | `ADMIN_PASSWORD_HASH` | bcrypt hash gerado no pré-requisito | |
   | `JWT_SECRET` | `token_urlsafe(64)` | |
   | `CORS_ORIGINS` | Origem exata da Vercel (ex.: `https://<seu-projeto>.vercel.app`) | Sem barra final, sem `*`, sem espaços |
   | `TURNSTILE_SITE_KEY` | Site key do widget de produção | Pública, mas fica no backend |
   | `TURNSTILE_SECRET_KEY` | Secret privada do widget de produção | `ENV=prod` recusa chave de teste |
   | `GROQ_API_KEY` | `https://console.groq.com/keys` | |
   | `CRON_SECRET` | 32+ caracteres aleatórios | Mesmo valor no GitHub `secrets.CRON_SECRET` |
   | `SCHEDULER_ENABLED` | `true` (padrão) | Veja "Cron de catch-up" abaixo |

3. Após o primeiro deploy, confira:
   ```text
   https://<backend>.onrender.com/api/v1/health
   → {"status":"ok","env":"prod","turnstile":{"configured":true,"mode":"live","site_key_configured":true}}
   ```
   `turnstile.mode` **precisa** ser `live`. Se vier `test` ou `disabled`, o deploy está errado (ou o validador derrubou o boot).
4. **Deploys são manuais** (`autoDeploy: false` no `render.yaml`): um push na branch de produção **não** sobe automaticamente — cada deploy é disparado no dashboard do Render após revisão. Isso é de propósito: o `startCommand` roda `alembic upgrade head` a cada boot e migrações são forward-only — um deploy automático aplicaria schema novo em produção sem aprovação e sem rollback. Dispare em **Deploy latest commit** depois de revisar (e, para mudanças de schema, após snapshot/backup do Neon).
5. **Migrações rodam a cada boot** (`alembic upgrade head` no `startCommand`). São idempotentes e forward-only. Risco conhecido e aceito: uma migration quebrada derruba o boot em loop (inclusive a cada wake-up do plano free) e derruba o board público junto — não existe rollback de schema. Mitigações atuais: deploy manual/gated (a migration é revisada antes do deploy), regra de migrações forward-only, e snapshot do Neon antes de merges que tocam schema. Separar a migração num step de release próprio (pre-deploy do Render) é trabalho futuro — **não remova o `alembic upgrade head` do boot sem que esse step revisado exista e esteja documentado**.
6. **Plano free dorme após ~15 min sem tráfego.** O primeiro request depois do spin-down paga o cold-start (ver seção **Cold-start**) — e também refaz o upgrade do Alembic no boot.

---

## Frontend na Vercel

1. **Add New → Project** e importe este repositório.
2. **Root Directory: `frontend`** (configuração de projeto no dashboard — não está no `vercel.json` de propósito). Framework: Next.js (detectado automaticamente; `frontend/vercel.json` só fixa `framework: "nextjs"` e o `$schema`).
3. Configure as env vars (Production — e Preview se quiser testar previews):

   | Variável | Valor | Escopo |
   |---|---|---|
   | `BACKEND_API_URL` | URL pública do Render, ex.: `https://<backend>.onrender.com` | Server-side fetch (SSR) |
   | `NEXT_PUBLIC_API_URL` | Mesma URL do Render | Obrigatória — build de produção **falha** se ausente (WR-04) |
   | `NEXT_PUBLIC_TURNSTILE_SITE_KEY` | Site key pública do widget de produção | Inlined no build |

   Não existe `NEXT_PUBLIC_*` para segredos: `CRON_SECRET`, `JWT_SECRET`, `TURNSTILE_SECRET_KEY` etc. **nunca** vão para a Vercel.
   Todas as variáveis de frontend estão documentadas em `frontend/.env.example` (no desenvolvimento, copie para `.env.local`).

   **Desde WR-04, `next build` falha se `NEXT_PUBLIC_API_URL` estiver ausente em build de produção** — não existe mais fallback silencioso para `http://localhost:8000` (o fallback só vale em desenvolvimento). Se o build falhar com essa mensagem, configure a variável no escopo **Production** e refaça o deploy.
4. Deploy. Anote o domínio de produção (ex.: `https://<seu-projeto>.vercel.app`).
5. Volte ao Render e ajuste `CORS_ORIGINS` para **exatamente** esse domínio (sem barra final) e faça **redeploy** do backend — CORS é lido no boot.
6. Abra o board no navegador e no celular (390 px) e confirme que carrega sem erro de CORS no console.

---

## CORS

- `CORS_ORIGINS` no Render é uma lista separada por vírgulas (`https://a.com,https://b.com`). Em produção use **exatamente uma**: o domínio de produção da Vercel.
- **Sem** barra final, **sem** `*`, **sem** esquema diferente (`http://` não vale para produção).
- Previews da Vercel (`https://<projeto>-<hash>-<time>.vercel.app`) **não** são cobertos por padrão:
  - ou adicione a origem do preview explicitamente em `CORS_ORIGINS` e redeploy,
  - ou teste previews contra o backend local,
  - ou aceite que previews apontam para produção e valide neles apenas o que não depende de escrita.
- O middleware usa `allow_credentials=False` e expõe apenas `Retry-After` (necessário para o countdown de 429 do reveal de contato).
- Depois de **qualquer** mudança em `CORS_ORIGINS`: **redeploy do backend**. O valor é lido no boot do processo.

---

## Cron de catch-up

**Por que existe:** o plano free do Render não oferece cron job, e o Vercel Hobby agenda no máximo 1×/dia sem retry. O scheduler in-process é o mecanismo primário; o GitHub Actions é a rede de segurança.

Configuração (uma vez, no GitHub):
1. **Settings → Secrets and variables → Actions → Variables** → crie `API_BASE_URL` = URL pública do Render **sem barra final** (ex.: `https://<backend>.onrender.com`).
2. **… → Secrets** → crie `CRON_SECRET` = o mesmo valor definido no Render.
3. O workflow `.github/workflows/expire-cron.yml` roda diariamente às **03:00 UTC** (mesma janela do scheduler interno) e também aceita execução manual: **Actions → expire-jobs → Run workflow**.
4. O step falha com mensagem clara se `API_BASE_URL`/`CRON_SECRET` estiverem vazios, e usa `curl --fail-with-body --retry 3 --retry-delay 15 --retry-connrefused --max-time 120` (retry só para falhas de transporte/conexão — 4xx **não** é retentado). O secret nunca é ecoado no log.
5. Resposta esperada: `{"deleted": N, "status": "ok"}` — `N` pode ser `0` (idempotente).

**Atrasos:** o GitHub pode atrasar o cron (filas, em especial em repos públicos/de baixa atividade). Não é um problema de correção — é a janela do catch-up; o APScheduler in-process cobre o caso em que o processo está acordado. Se o Render ficar dormindo por longos períodos, considere `SCHEDULER_ENABLED=false` (o endpoint vira o único gatilho) ou um plano pago.

**Sem segredo configurado:** `POST /api/v1/admin/expire` responde **503** ("Expiração manual não configurada") — **fail-closed**: significa que o gatilho manual está **desativado** (a expiração depende só do scheduler in-process), nunca que o endpoint está aberto. Com segredo errado/ausente: **401**. Em ambos os casos o endpoint destrutivo permanece fechado; um 2xx sem o segredo indicaria configuração incorreta grave. O gate `verify-deploy.ps1` aceita 401/403/503 como recusa válida e só falha (ou aponta erro) para respostas inesperadas — ele nunca trata 503 como "endpoint aberto".

---

## Cold-start

O plano free do Render **dorme após ~15 min sem tráfego**. No primeiro request depois do sono, a plataforma paga o boot do processo (+ migrações Alembic no `startCommand`).

**Como o frontend lida com isso:**
- `frontend/lib/jobs.ts` faz fetch com `cache: "no-store"` e **timeout de 15 s** (`AbortSignal.timeout`).
- Se estourar o timeout, o board não trava: `frontend/app/(public)/error.tsx` renderiza **"O servidor está acordando."** e um botão **"Tentar novamente"** (que re-renderiza a rota).
- Erros não-timeout mostram "Não foi possível carregar as vagas." com o mesmo botão.

**O que fazer na operação:**
1. Meça e registre o tempo real do primeiro request após spin-down (ver **Registro de verificação** abaixo).
2. Se o cold-start for consistentemente maior que 15 s, as opções (sem provisionar nada automaticamente) são:
   - **Plano pago do Render** (instância sempre ligada),
   - **Ping externo opcional** (ex.: cron-job.org / UptimeRobot chamando `/api/v1/health` a cada 10 min) — mantém o processo acordado; é opcional e não é provisionado por este runbook,
   - Aumentar o timeout do frontend (**não recomendado** sem medir; 15 s é o contrato documentado).
3. O timeout do frontend é um contrato: `docs/` e o código (`TIMEOUT_MS = 15_000`) devem ser alterados juntos, com a decisão registrada aqui.

---

## Gate de fumaça

`scripts/verify-deploy.ps1` valida o deploy de produção de ponta a ponta (health + Turnstile `live`, CORS permitido/negado, board sem dados de contato, página legal, contrato da API, cron 401/403/503 (fail-closed) e idempotência, ausência de vazamento do secret, latência de cold-start).

```powershell
powershell -ExecutionPolicy Bypass -File scripts\verify-deploy.ps1 `
  -FrontendUrl https://<seu-projeto>.vercel.app `
  -BackendUrl  https://<backend>.onrender.com `
  -CronSecret  <CRON_SECRET>
```

`-CronSecret` é obrigatório para o check de cron autenticado (ou exporte `CRON_SECRET` na sessão antes de rodar). Cada check imprime `PASS - ...`; ao final: `verify-deploy: all checks passed`. Se qualquer check falhar, o script lança exceção com a mensagem do que falhou — **não** considere o deploy pronto enquanto houver falha.

Compatível com PowerShell 5.1, salvo em UTF-8 com BOM.

---

## Rollback

| Onde | Como | Observações |
|---|---|---|
| **Render (backend)** | Dashboard → serviço `nqu-backend` → **Events/Deploys** → deploy anterior → **Rollback** | O rollback restaura o código; migrações já aplicadas **não** são desfeitas (ver abaixo). |
| **Vercel (frontend)** | Dashboard → projeto → **Deployments** → deployment anterior → **⋯ → Instant Rollback** | Instantâneo; o domínio de produção passa a servir o build anterior. |
| **Migrações (Neon)** | **Não existe rollback de schema.** Migrações são forward-only: corrija com uma **nova** migration (`alembic revision --autogenerate -m "..."`) e aplique com `alembic upgrade head`. | Nunca edite uma migration já aplicada nem rode `alembic downgrade` em produção sem plano explícito. |
| **CORS errado** | Corrija `CORS_ORIGINS` e redeploy do backend | Não precisa de deploy do frontend. |
| **Cron quebrado** | Desative/edite `.github/workflows/expire-cron.yml` ou remova `vars.API_BASE_URL`/`secrets.CRON_SECRET` | O scheduler in-process continua como mecanismo primário; o catch-up é desativável sem downtime. |

**Ordem segura de rollback completo:** (1) frontend na Vercel → deployment anterior; (2) backend no Render → deploy anterior; (3) se a causa for schema, escrever migration corretiva e re-deploy. Em qualquer caso, registre o incidente na tabela **Registro de verificação**.

---

## Checklist de go-live

**Neon**
- [ ] Projeto de produção criado e separado do dev/test
- [ ] Connection string **pooled** copiada com `?ssl=require`
- [ ] Região anotada (e `region` do `render.yaml` alinhada)

**Render (backend)**
- [ ] Blueprint aplicado a partir do `render.yaml` (deploys **manuais** — `autoDeploy: false`; cada deploy é disparado no dashboard após revisão)
- [ ] Todos os env vars preenchidos (`DATABASE_URL`, `ADMIN_PASSWORD_HASH`, `JWT_SECRET`, `CORS_ORIGINS`, `TURNSTILE_SITE_KEY`, `TURNSTILE_SECRET_KEY`, `GROQ_API_KEY`, `CRON_SECRET`)
- [ ] Snapshot/backup do Neon tirado antes do deploy (migrações são forward-only — sem rollback de schema)
- [ ] Boot rodou `alembic upgrade head` sem erro
- [ ] `/api/v1/health` → `status=ok`, `env=prod`, `turnstile.mode=live`
- [ ] `CORS_ORIGINS` = origem exata da Vercel, sem barra final; redeploy feito após ajuste

**Vercel (frontend)**
- [ ] Root Directory = `frontend`
- [ ] `BACKEND_API_URL`, `NEXT_PUBLIC_API_URL`, `NEXT_PUBLIC_TURNSTILE_SITE_KEY` configurados (ver `frontend/.env.example`)
- [ ] Build de produção passou (sem `NEXT_PUBLIC_API_URL` ele **falha** de propósito — WR-04)
- [ ] Deploy de produção concluído; domínio anotado
- [ ] Board carrega sem erro de CORS no console do navegador

**GitHub Actions (cron)**
- [ ] `vars.API_BASE_URL` e `secrets.CRON_SECRET` cadastrados
- [ ] `expire-jobs` rodado manualmente (Run workflow) com sucesso; log sem o secret
- [ ] Resposta `{"deleted": N, "status": "ok"}` registrada

**Verificação**
- [ ] `scripts/verify-deploy.ps1` → todas as linhas `PASS` + `verify-deploy: all checks passed`
- [ ] Cold-start medido e registrado (ver Registro de verificação)
- [ ] Fluxo real: buscar vaga → abrir modal → revelar contato (Turnstile real) → reportar vaga → `/privacidade`
- [ ] HTML do board sem `contact_email`, `contact_phone`, `mailto:`
- [ ] `/admin/login`, `/admin/paste` e fila de review funcionando
- [ ] `git status --porcelain` limpo quanto a `.env`/`.env.local`; `render.yaml` sem valores; nenhum secret em logs

---

## Registro de verificação

> Preencher **no checkpoint humano** (Task 3 do plano 06-04), após o deploy real. Não inventar valores: se um passo falhou, registrar o que foi observado.

| Data (UTC) | Etapa | URL / comando | Resultado observado | Cold-start | Notas |
|---|---|---|---|---|---|
| _pendente_ | Neon — projeto de produção | | | | |
| _pendente_ | Render — blueprint + segredos | | | | |
| _pendente_ | Render — `/api/v1/health` | | | | `env=prod`, `mode=live` |
| _pendente_ | Vercel — deploy produção | | | | Root Directory `frontend` |
| _pendente_ | CORS — board sem erro | | | | |
| _pendente_ | GitHub Actions — `expire-jobs` manual | | | | `{"deleted": N, "status": "ok"}` |
| _pendente_ | `verify-deploy.ps1` | | | | todas as linhas `PASS` |
| _pendente_ | Cold-start após ~20 min ocioso | | | | tempo real + comportamento da UI |
| _pendente_ | Fluxo público real (buscar/revelar/reportar) | | | | Turnstile real |
| _pendente_ | Admin (`/admin/login`, `/admin/paste`, review) | | | | |

Qualquer falha acima: parar, registrar URL + observação na tabela, corrigir, re-deploy e re-rodar o gate antes de declarar o go-live.
