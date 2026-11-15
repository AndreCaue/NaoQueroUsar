# Deploy — EmpregaNoix

Runbook de produção e **alvo contratual (state-alvo)**: frontend na **Vercel**, backend **FastAPI** no **Render**, banco **Neon (Postgres)** e **GitHub Actions** como cron de catch-up da expiração.

> **Nenhum segredo real entra neste arquivo ou em qualquer arquivo versionado.** Todos os valores sensíveis são configurados apenas em variáveis de ambiente (Render/Vercel/GitHub). Hosts legados/históricos aparecem apenas como evidência registrada no **Registro de verificação** e no mapeamento canônico↔legado — não substituem o alvo canônico.

---

## Alvo canônico (state-alvo)

Contrato de produção (D-01, D-03, D-07). Estes são os **alvos contratuais**; a execução operacional pode estar pendente e a evidência histórica pode ter sido coletada em hosts legados (ver mapeamento e matriz).

- **Frontend (origem canônica):** `https://empreganoix.vercel.app`
- **Backend (API canônica):** `https://empreganoix.onrender.com`
- `CORS_ORIGINS=https://empreganoix.vercel.app` (exato, sem barra final, sem wildcard, sem legados)
- `NEXT_PUBLIC_API_URL=https://empreganoix.onrender.com`
- `BACKEND_API_URL=https://empreganoix.onrender.com`
- Turnstile Hostnames (widget de produção): `empreganoix.vercel.app`
- GitHub Actions `vars.API_BASE_URL=https://empreganoix.onrender.com`
- Cron endpoint canônico: `https://empreganoix.onrender.com/api/v1/admin/expire` (somente `X-Cron-Secret`, fail-closed; **T-06-01 preservado** — Bearer JWT de admin **não** autoriza este endpoint)

> **`NEXT_PUBLIC_*` é embutida no build** e exige **rebuild/redeploy** ao alterar (Vercel). `BACKEND_API_URL` é lido em runtime no servidor; ainda assim valide o deploy após mudanças.

**Exemplo de gate (alvo canônico):**
```powershell
$env:CRON_SECRET = "<CRON_SECRET>"   # não fica no histórico do PowerShell
powershell -ExecutionPolicy Bypass -File scripts\verify-deploy.ps1 `
  -FrontendUrl https://empreganoix.vercel.app `
  -BackendUrl  https://empreganoix.onrender.com
```
O script permanece parametrizado e pode ser executado contra hosts legados/históricos **apenas** para reproduzir/interpretar evidência registrada (ex.: `https://empreganoix-six.vercel.app` / `https://nqu-backend-x60n.onrender.com`).

---

## Mapeamento canônico ↔ legado/histórico

Hosts legados/históricos são **não canônicos**. Desvios/bloqueios de provisionamento devem ser registrados sem trocar o canônico silenciosamente (D-02, D-14). Evidências nesses hosts permanecem válidas como histórico mapeado ao state-alvo.

| Papel | Host canônico (state-alvo) | Host legado/histórico | Notas |
| --- | --- | --- | --- |
| Frontend (origem) | `https://empreganoix.vercel.app` | `https://empreganoix-six.vercel.app`, `https://nao-quero-usar.vercel.app` | Evidências de smoke/deploy registradas nesses hosts (2026-11-12/14/15) são históricas; CORS/Turnstile Hostnames em produção devem refletir a origem **real/canônica** provisionada. |
| Backend (API) | `https://empreganoix.onrender.com` | `https://nqu-backend-x60n.onrender.com`, `https://naoquerousar.onrender.com` | `nqu-backend-x60n` e `naoquerousar` aparecem em verificações anteriores; o contrato operacional canônico aponta para `empreganoix.onrender.com`. |

---

## Matriz de alinhamento (D-10)

Status permitidos: `verificado em host legado` | `alinhado contratualmente ao canônico` | `pendente de execução operacional`.

| Check | Alvo canônico | Host/evidência verificada | Status | Referência / nota |
| --- | --- | --- | --- | --- |
| `GET /api/v1/health` (status, `env`, Turnstile configurado/live conforme contrato) | `https://empreganoix.onrender.com/api/v1/health` | 2026-11-12 `https://empreganoix.onrender.com` (env/dev, mode/test — falha registrada); 2026-11-15 smoke gate em `https://nqu-backend-x60n.onrender.com` aprovado (`env=prod`, `turnstile.mode=live`) | `verificado em host legado` | Registro 2026-11-12 e 2026-11-15; gate `scripts/verify-deploy.ps1` check 1. Execução no host canônico pode permanecer pendente de execução operacional até provisionamento. |
| Preflight CORS da origem canônica (allow/deny conforme gate, `Access-Control-Allow-Origin`) | Origin `https://empreganoix.vercel.app` → `https://empreganoix.onrender.com` | 2026-11-12 falha (400, sem ACAO); 2026-11-15 allow/deny PASS em `https://nqu-backend-x60n.onrender.com` com origin canônica ecoada e `https://evil.example` recusado | `verificado em host legado` | Registro 2026-11-12 e 2026-11-15; `scripts/verify-deploy.ps1` checks 2-3. Contrato: `CORS_ORIGINS=https://empreganoix.vercel.app`. |
| `POST /api/v1/admin/expire` (rejeição sem/errada credencial fail-closed + idempotência com `X-Cron-Secret`, 200 + `deleted` inteiro 2x) | `https://empreganoix.onrender.com/api/v1/admin/expire` | 2026-11-12 e 2026-11-15: recusado sem/errado; com segredo 200 `{"deleted":0,"status":"ok"}` 2x (idempotente) | `verificado em host legado` | Registro 2026-11-12 e 2026-11-15; `scripts/verify-deploy.ps1` checks 7-8. **T-06-01 preservado** (somente `X-Cron-Secret`; sem reabrir contrato). |
| Superfície pública board (`/`, SSR sem vazamento de contato) | `https://empreganoix.vercel.app/` | 2026-11-14/15 evidências em hosts legados; board/legal/API/cron/no-leak PASS no smoke de 2026-11-15 | `verificado em host legado` | Registro 2026-11-14 e 2026-11-15; `scripts/verify-deploy.ps1` checks 4,6,9. |
| Páginas legais `/privacidade` e `/termos-de-uso` | `https://empreganoix.vercel.app/privacidade`, `/termos-de-uso` | 2026-11-12/15 em hosts legados: 200, LGPD/canal, aviso de intermediário, sem placeholder | `verificado em host legado` | Registro 2026-11-12 e 2026-11-15; `scripts/verify-deploy.ps1` check 5. |
| Superfície login/admin (`/admin` → `/admin/paste`, fluxos autenticados) | `https://empreganoix.vercel.app/admin` | Cobertura parcial por gate; validação manual completa registrada como pendente em linhas `_pendente_` | `pendente de execução operacional` | Registro e `scripts/verify-deploy.ps1` (parcial). Requer provisionamento canônico + verificação humana. |

> **Nota:** BRND-04 e o resíduo ops de SECR-12/LIFE-13 podem ser fechados contratualmente com evidência mapeada/handoff explícito sem reabrir T-06-01 (D-12).

---

## Handoff operacional, riscos e rollback

**Sequência operacional segura (D-13):**
1. Alinhar/provisionar hosts canônicos (`empreganoix.vercel.app`, `empreganoix.onrender.com`).
2. Configurar envs, `CORS_ORIGINS=https://empreganoix.vercel.app`, Turnstile Hostnames (`empreganoix.vercel.app`) e segredos de cron.
3. **Rebuild/redeploy do frontend** por qualquer alteração em `NEXT_PUBLIC_*`.
4. Validar com `scripts/verify-deploy.ps1 -FrontendUrl https://empreganoix.vercel.app -BackendUrl https://empreganoix.onrender.com`.
5. Registrar evidência em **Registro de verificação** sem reescrever linhas históricas.

**Rollback:** rollback por reversão de env/config/domínio (reversão de env/config/domínio) e redeploy (ver seção **Rollback**). Migrações são forward-only.

**Riscos (D-15):** execução pode permanecer pendente/dev-local; Turnstile Hostnames/CORS devem coincidir com a origem real; cron/scheduler dependem de envs/segredos; cold-start e split scheduler (APScheduler + GitHub Actions). Código/contrato SECR-12/LIFE-13 já verificados; este alinhamento trata evidência/ops.

---

## Arquitetura

```text
Navegador ──HTTPS──► Vercel (Next.js 16 App Router, SSR + server fetch)
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
2. **Catch-up** — GitHub Actions chamando `POST /api/v1/admin/expire` com `X-Cron-Secret`. Idempotente.

---

## Pré-requisitos

- [ ] Contas: **Vercel**, **Render**, **Neon**, **Cloudflare** (Turnstile), **Groq**, **GitHub**
- [ ] Repositório no GitHub com este código (branch de produção)
- [ ] Projeto **Neon de produção** separado do dev/test
- [ ] Cloudflare Turnstile: widget de **produção** criado. Turnstile → Hostnames: `empreganoix.vercel.app` (state-alvo). Widget de teste **não** aceito em `ENV=prod` (exceto desvio temporário).
- [ ] Chave da Groq (`https://console.groq.com/keys`)
- [ ] Senha de admin e hash **bcrypt** gerado localmente:
  ```powershell
  cd backend
  .\.venv\Scripts\python.exe -c "import bcrypt; print(bcrypt.hashpw(b'SEU_SEGREDO', bcrypt.gensalt()).decode())"
  ```
- [ ] `JWT_SECRET`: 64 caracteres aleatórios
  ```powershell
  python -c "import secrets; print(secrets.token_urlsafe(64))"
  ```
- [ ] `CRON_SECRET`: 32+ caracteres aleatórios; mesmo valor no Render e no GitHub (`secrets.CRON_SECRET`)

---

## Backend no Render

1. **New → Blueprint** (lê `render.yaml`): `rootDir: backend`, `buildCommand: pip install uv && uv sync --frozen --no-dev`, `startCommand: uv run --no-sync alembic upgrade head && uv run --no-sync uvicorn app.main:app --host 0.0.0.0 --port $PORT`, `healthCheckPath: /api/v1/health`, `region: ohio` (alinhar ao Neon).
2. Env vars (dashboard; `sync: false` não versionado):

   | Variável | Valor / origem (state-alvo) | Notas |
   | --- | --- | --- |
   | `ENV` | `prod` |  |
   | `PYTHON_VERSION` | `3.11.9` |  |
   | `JWT_EXPIRES_IN` | `43200` | 12 h |
   | `DATABASE_URL` | Neon **pooled** `postgresql+asyncpg://...?...ssl=require` | asyncpg obrigatório |
   | `ADMIN_PASSWORD_HASH` | bcrypt hash |  |
   | `JWT_SECRET` | `token_urlsafe(64)` |  |
   | `CORS_ORIGINS` | `https://empreganoix.vercel.app` | Exato, sem barra final, sem `*`, sem legados |
   | `TURNSTILE_SITE_KEY` | Site key produção |  |
   | `TURNSTILE_SECRET_KEY` | Secret produção |  |
   | `ALLOW_TEST_TURNSTILE` | ausente/`false` | Desvio temporário apenas |
   | `GROQ_API_KEY` | Groq |  |
   | `CRON_SECRET` | 32+ chars | Mesmo no GitHub |
   | `SCHEDULER_ENABLED` | `true` |  |

3. Conferir health canônico:
   ```text
   https://empreganoix.onrender.com/api/v1/health
   → {"status":"ok","env":"prod","turnstile":{"configured":true,"mode":"live","site_key_configured":true}}
   ```
4. **Deploys manuais** (`autoDeploy: false`); migrations forward-only a cada boot. Plano free dorme (~15 min).

---

## Desvio temporário: Turnstile de teste em produção

> Histórico/operacional (2026-11-12). Remover com widget live no host canônico.

Se necessário: `ALLOW_TEST_TURNSTILE=true` (Render) + site key de teste no frontend com **rebuild/redeploy**. Gate aceita `mode=test` apenas com `-AllowTestTurnstile` e `test_override=true`. Saída: Hostnames `empreganoix.vercel.app`, chaves live, remover flag, redeploy/rebuild e revalidar.

---

## Frontend na Vercel

1. **Root Directory: `frontend`**.
2. Env vars (Production):

   | Variável | Valor (state-alvo canônico) | Notas |
   | --- | --- | --- |
   | `BACKEND_API_URL` | `https://empreganoix.onrender.com` | SSR runtime |
   | `NEXT_PUBLIC_API_URL` | `https://empreganoix.onrender.com` | Obrigatória em build; embutida (rebuild ao alterar) |
   | `NEXT_PUBLIC_TURNSTILE_SITE_KEY` | Site key produção | Rebuild ao alterar |

3. Domínio canônico: `https://empreganoix.vercel.app`. Ajustar `CORS_ORIGINS` no Render para essa origem exata e redeploy.

---

## CORS

- State-alvo: `CORS_ORIGINS=https://empreganoix.vercel.app` (exato, sem barra final, sem `*`, sem legados).
- `allow_credentials=False`, expõe `Retry-After`. Redeploy do backend após mudança.

---

## Cron de catch-up

- GitHub Actions `vars.API_BASE_URL=https://empreganoix.onrender.com`, `secrets.CRON_SECRET` = valor do Render.
- Workflow `.github/workflows/expire-cron.yml` (03:00 UTC + manual) chama `POST https://empreganoix.onrender.com/api/v1/admin/expire` com `X-Cron-Secret`.
- Resposta: `{"deleted": N, "status": "ok"}` (idempotente). **T-06-01:** somente `X-Cron-Secret` (Bearer JWT não autoriza). 503 sem segredo / 401 inválido = fail-closed.

---

## Cold-start

Primeiro request após ~15 min paga boot. Frontend timeout 15 s (`frontend/lib/jobs.ts`). Check 10 do gate mede primeiro request (health).

---

## Gate de fumaça

```powershell
$env:CRON_SECRET = "<CRON_SECRET>"
powershell -ExecutionPolicy Bypass -File scripts\verify-deploy.ps1 `
  -FrontendUrl https://empreganoix.vercel.app `
  -BackendUrl  https://empreganoix.onrender.com
```
Para reproduzir evidência legada, use hosts legados como parâmetros. Critério 6 é human-gated: só fechado após execução real e evidência registrada.

---

## Rollback

| Onde | Como | Observações |
| --- | --- | --- |
| **Render (backend)** | Rollback para deploy anterior | Sem rollback de migrations |
| **Vercel (frontend)** | Instant Rollback |  |
| **Migrações (Neon)** | Nova migration forward-only |  |
| **CORS/env/domínio** | **Rollback por reversão de env/config/domínio** e redeploy/rebuild (`NEXT_PUBLIC_*`) |  |
| **Cron** | Ajustar workflow/vars/secrets |  |

---

## Checklist de go-live

**Neon:** prod separado, pooled asyncpg, região alinhada.
**Render:** deploy manual, envs corretos (`CORS_ORIGINS=https://empreganoix.vercel.app`), health canônico `env=prod`/`turnstile.mode=live`.
**Vercel:** Root `frontend`, `BACKEND_API_URL`/`NEXT_PUBLIC_API_URL`=`https://empreganoix.onrender.com`, Hostnames `empreganoix.vercel.app`, rebuild após `NEXT_PUBLIC_*`.
**GitHub:** `vars.API_BASE_URL=https://empreganoix.onrender.com` + `secrets.CRON_SECRET`.
**Verificação:** gate PASS (canônico ou evidência mapeada), cold-start medido, fluxos reais, sem vazamentos.

---


## Registro de verificação

> Preencher **no checkpoint humano** (Task 3 do plano 06-04), após o deploy real. Não inventar valores: se um passo falhou, registrar o que foi observado.

| Data (UTC) | Etapa                                               | URL / comando                                                                                  | Resultado observado                                                                                                                                                                                                        | Cold-start | Notas                                                                                                                                                                                                                                                         |
| ---------- | --------------------------------------------------- | ---------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------- | ----------------------------------------- | ----------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | ---- | --------------------------------------------------------------------------------------------------------------- |
| 2026-11-12 | Neon — projeto de produção                          | —                                                                                              | não verificado por HTTP                                                                                                                                                                                                    | —          | confirmar no painel (fora do alcance do gate)                                                                                                                                                                                                                 |
| 2026-11-12 | Render — blueprint + segredos                       | —                                                                                              | não verificado por HTTP                                                                                                                                                                                                    | —          | confirmar `alembic upgrade head` no log do deploy                                                                                                                                                                                                             |
| 2026-11-12 | Render — `/api/v1/health`                           | `https://empreganoix.onrender.com/api/v1/health`                                               | 200 `status=ok`, **`env=dev`**, **`turnstile.mode=test`**                                                                                                                                                                  | —          | **FALHA**: falta `ENV=prod` e as chaves Turnstile de produção                                                                                                                                                                                                 |
| 2026-11-12 | Vercel — deploy produção                            | `https://empreganoix.vercel.app`                                                               | 200; board SSR renderiza vagas; bundle cliente aponta para `https://empreganoix.onrender.com`                                                                                                                              | —          | OK (`BACKEND_API_URL` e `NEXT_PUBLIC_API_URL` corretos no build atual)                                                                                                                                                                                        |
| 2026-11-12 | CORS — preflight da origem Vercel                   | `OPTIONS /api/v1/public/jobs?limit=1` ← `https://empreganoix.vercel.app`                       | **400, sem `Access-Control-Allow-Origin`**                                                                                                                                                                                 | —          | **FALHA**: origem ausente em `CORS_ORIGINS` (ou com barra final). Board funciona porque o SSR não passa por CORS; filtros/reveal/report/admin quebram no navegador                                                                                            |
| 2026-11-12 | Legal — `/privacidade` + `/termos-de-uso`           | idem frontend                                                                                  | 200/200; LGPD + canal de e-mail; "intermedi" nos Termos; sem placeholder                                                                                                                                                   | —          | OK                                                                                                                                                                                                                                                            |
| 2026-11-12 | API pública                                         | `GET https://empreganoix.onrender.com/api/v1/public/jobs?limit=1`                              | 200 com `items`/`total`                                                                                                                                                                                                    | —          | OK                                                                                                                                                                                                                                                            |
| 2026-11-12 | Cron — sem segredo                                  | `POST /api/v1/admin/expire`                                                                    | 401                                                                                                                                                                                                                        | —          | OK (fail-closed)                                                                                                                                                                                                                                              |
| 2026-11-12 | Cron — com segredo (2x)                             | `POST /api/v1/admin/expire` + `X-Cron-Secret`                                                  | 200 `{"deleted":0,"status":"ok"}` nas duas                                                                                                                                                                                 | —          | OK, idempotente; `CRON_SECRET` do Render casa com o local                                                                                                                                                                                                     |
| 2026-11-12 | Não vazamento                                       | board/health/privacidade/termos                                                                | secret não aparece                                                                                                                                                                                                         | —          | OK                                                                                                                                                                                                                                                            |
| 2026-11-12 | `verify-deploy.ps1`                                 | `-FrontendUrl https://empreganoix.vercel.app -BackendUrl https://empreganoix.onrender.com`     | **FALHOU no check 1** (`env=dev`)                                                                                                                                                                                          | não medido | Re-rodar como primeiro tráfego após corrigir `ENV`/`CORS`/Turnstile                                                                                                                                                                                           |
| 2026-11-12 | GitHub Actions — `expire-jobs` manual               | —                                                                                              | não executado                                                                                                                                                                                                              | —          | pendente                                                                                                                                                                                                                                                      |
| 2026-11-13 | Preparação de deploy (Fase 9)                       | —                                                                                              | Artefatos preparados/alinhados (ROADMAP critério 2 T-06-01, gate com aviso exato de intermediário, runbook com `uv run --no-sync` e aviso Critério 6 human-gated); deploy/smoke gate permanece human-gated (não executado) | —          | Critério 6 continua pendente de execução real e evidência registrada                                                                                                                                                                                          |
| 2026-11-14 | Deploy produção (10-04 Task 2, checkpoint aprovado) | Frontend `https://empreganoix-six.vercel.app`, Backend `https://nqu-backend-x60n.onrender.com` | **Aprovado pelo usuário** (produção verificada; evidências fornecidas: URLs e cold-start) | 0.2s | Hosts reais diferem dos exemplos do plano (`empreganoix.vercel.app` / `empreganoix.onrender.com`); serviço Render permanece `nqu-backend` (conforme decisão documentada). Detalhes de smoke gate/fluxos não informados além da aprovação — ver 10-04-SUMMARY. |
| 2026-11-15 | Smoke gate produção (09-04 Task 3, critério 6) | Frontend `https://empreganoix-six.vercel.app` · Backend `https://nqu-backend-x60n.onrender.com` | **PASS — `verify-deploy: all checks passed`**: health 200 `env=prod`, `turnstile.mode=live`; CORS preflight allow (origem canônica Vercel ecoada) e deny (`https://evil.example` recusado/400); board/legal/API OK; cron sem/errado recusado e autorizado idempotente; sem vazamento de secret | 0.2s | Evidência humana aprovada (2026-11-15). Critério 6 atendido conforme gate registrado. |
| _pendente_ | Cold-start após ~20 min ocioso                      |                                                                                                |                                                                                                                                                                                                                            |            | tempo real + comportamento da UI                                                                                                                                                                                                                              |
| _pendente_ | Fluxo público real (buscar/revelar/reportar)        |                                                                                                |                                                                                                                                                                                                                            |            | Turnstile real                                                                                                                                                                                                                                                |
| _pendente_ | Admin (`/admin` → `/admin/paste`, review)           |                                                                                                |                                                                                                                                                                                                                            |            |                                                                                                                                                                                                                                                               |

Qualquer falha acima: parar, registrar URL + observação na tabela, corrigir, re-deploy e re-rodar o gate antes de declarar o go-live.
