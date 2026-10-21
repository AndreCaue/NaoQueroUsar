# Phase 3: Contact Reveal & Anti-Spam - Context

**Gathered:** 2026-10-21
**Status:** Ready for planning

<domain>
## Phase Boundary

O contato das vagas sai do banco **somente** por um endpoint dedicado, protegido por Cloudflare Turnstile verificado no servidor (Siteverify) e rate limiting por IP — ocultar no cliente não basta (PITFALLS 7). O login do master passa pelo mesmo gate, contra credential stuffing.

**Entregue nesta fase (SECR-01, SECR-02, SECR-03, PUBL-05):**
- `POST /api/v1/public/jobs/{id}/reveal-contact` — único caminho de saída do contato; token Turnstile verificado server-side + rate limit por IP.
- `POST /api/v1/auth/login` passa a exigir `cf_token` (Turnstile) e tem rate limit próprio.
- Serviço de Siteverify (httpx) com verificação de `action`, `idempotency_key` e tratamento de `timeout-or-duplicate`.
- Resolver de IP do cliente consciente de proxy (Railway sobrescreve `X-Real-IP`; Render anexa ao XFF).
- Frontend: widget do Turnstile na tela de login do admin (`ExtractForm.tsx`) + assinatura de `loginAdmin(password, cfToken)` — **no mesmo plano** da mudança no backend.
- Observabilidade: logs de falha com error-codes + `/health` reportando o status do Turnstile.

**Fora desta fase:** UI pública do reveal (botão "Mostrar contato", modal, grade) — Phase 4 (PUBL-01..04, PUBL-06); página pública de teste — Phase 4; denunciação de vaga (TRST-02) e páginas legais — Phase 6; wiring de deploy/env vars de produção — Phase 6; Redis/limiter distribuído — Phase 6.

</domain>

<decisions>
## Implementation Decisions

### Fricção do visitante no reveal
- **D-01:** O widget do Turnstile no reveal usa modo **`interaction-only`** — o visitante não vê checkbox; o desafio só aparece se o Turnstile desconfiar. Reveal = 1 clique, coerente com o core value "sem fricção".
- **D-02:** Esta fase entrega **só o backend do reveal + o widget do login do admin** no frontend. Não cria página pública de teste nem board — a UI do reveal público é Phase 4, que implementa contra o contrato de erro (403/429/404) definido aqui.
- **D-03:** Ordem das verificações no endpoint de reveal: **rate limit → busca da vaga (404) → Siteverify (403) → 200**. A checagem da vaga vem **antes** do Turnstile: IDs são UUID (sem oráculo prático de existência, D-06 da Fase 1) e o atacante não gasta chamada da Cloudflare com IDs falsos.
- **D-04:** O contato revelado é mantido **em memória do cliente, por `job_id`**, enquanto a aba estiver aberta: reabrir a mesma vaga mostra o contato direto, sem novo Turnstile. Não vai para `sessionStorage`/`localStorage` (não sobrevive a F5) e **não "libera" a aba** — revelar outra vaga exige token novo, porque o token do reveal anterior é single-use e já foi consumido. *(Contrato para a Phase 4 implementar.)*

### Política de rate limit
- **D-05:** `slowapi` + `limits` com backend **in-memory (memória do processo)**; janela de **1 minuto**, chaveado pelo IP resolvido. Sem Redis, sem tabela nova, sem migração.
- **D-06:** Limites por env: `REVEAL_RATE_LIMIT` default `10/minute`, `LOGIN_RATE_LIMIT` default `5/minute` (defaults da pesquisa; ajustáveis sem deploy).
- **D-07:** O contador conta **todas as tentativas**, inclusive as com token inválido — senão o bot inunda o Siteverify de graça e o custo da chamada cai no nosso bolso.
- **D-08:** **Buckets separados por rota**: o reveal público nunca tranca o login do master (que é o cliente mais sensível e fica na mesma faixa de IP em horários de pico).
- **D-09:** **Sem mitigação específica para CGNAT / IP compartilhado** — só limite por IP. Risco aceito: em hora de pico um CGNAT carregado pode levar visitantes legítimos junto. Se surgirem 429 em massa na prática, os números são o ponto de ajuste (env), sem mudança de código.
- **D-10:** A chave do rate limit é o IP resolvido por cadeia de prioridade: `X-Real-IP` → entrada mais à direita do `X-Forwarded-For` que não seja privada/loopback → `request.client.host` → `"unknown"`. **Nunca** o leftmost do XFF (spoofável) e nunca o `get_remote_address` default do slowapi (colapsa todo mundo num bucket só).

### Chave Turnstile ausente: fail-closed
- **D-11:** **Falha no startup** quando `TURNSTILE_SECRET_KEY` está ausente/vazia e `ENV != "dev"` — mesmo padrão de "falha rápido se falta env" do D-05 da Fase 1. Fail-open silencioso é proibido.
- **D-12:** Em `ENV == "dev"` o default é a chave pública always-pass do Cloudflare (`1x0000000000000000000000000000000AA`), para dev local e CI rodarem sem conta Cloudflare. Em ambiente não-dev o **validator rejeita chaves de teste conhecidas** (`1x…`, `2x…`, `3x…`) → o startup falha. Isso impede que o `.env.example` copiado para produção auto-aprove tudo (PITFALLS 7).
- **D-13:** **Falha fechada em qualquer erro do Siteverify** (rede, HTTP 5xx, JSON inválido) → 403 + log. Sem modo degradado, sem fail-open, mesmo durante indisponibilidade da Cloudflare.
- **D-14:** Observabilidade em 3 camadas: (a) WARNING de startup quando a chave falta ou está errada; (b) error-codes do Siteverify registrados no log estruturado a cada falha; (c) o `/health` passa a reportar o status do Turnstile **sem vazar o segredo**. O dashboard do Cloudflare com zero validações continua sendo o sinal externo definitivo.

### Turnstile no login do admin
- **D-15:** Turnstile **incondicional** no `/auth/login` — SECR-03 é absoluto ("também protege o login"), sem modo progressivo por número de falhas.
- **D-16:** O widget no login usa o mesmo modo `interaction-only` do reveal.
- **D-17:** Ordem no login: **rate limit → Siteverify (403) → bcrypt (401) → JWT (200)**. A senha nunca é comparada sem um token Turnstile válido na mão (ASVS V2).
- **D-18:** **Sem fallback.** Se o Turnstile estiver indisponível, o login é recusado com mensagem pt-BR explícita de "verificação indisponível" (distinta de "Senha inválida") — fail closed, coerente com D-13.
- **D-19:** `LoginRequest` ganha `cf_token` e `loginAdmin(password, cfToken)` muda de assinatura. **A mudança do backend e o widget no frontend têm de sair no mesmo plano** — mudar `/auth/login` sem o frontend quebra com 422 (anti-pattern listado em 03-RESEARCH).

### Contrato do endpoint (derivado de 03-RESEARCH.md — não é escolha do usuário)
- `POST /api/v1/public/jobs/{id}/reveal-contact` — body `{ "cf_token": "<≤2048 chars>" }` → `200 { contact_email?, contact_phone? }` · `404` (vaga desconhecida/não publicada/expirada) · `403` (Turnstile falhou, inclusive `timeout-or-duplicate`) · `429` (rate limit, com `Retry-After`) · `422` (body inválido). Sem autenticação, com CORS travado à origem do front.
- Siteverify aceita **exatamente** `secret`, `response`, `remoteip` (opcional), `idempotency_key` (opcional). **Não existe** `sitekey` — não enviar (o ARCHITECTURE.md L468 sugere, mas a tabela oficial de params não tem).
- Token: válido por **300 s**, **single-use**; replay e expiração retornam `timeout-or-duplicate` → 403 tratável ("tente novamente"), nunca sucesso cacheado.
- `action`binding: `reveal` no endpoint de reveal, `login` no login — o servidor compara com o `action` esperado para impedir reuso de token entre os dois fluxos.
- `idempotency_key` = um `uuid4()` por submissão do usuário; retry só com a mesma chave.
- Erros do Siteverify a tratar: `missing-input-secret`, `invalid-input-secret`, `missing-input-response`, `invalid-input-response`, `bad-request`, `timeout-or-duplicate`, `internal-error`.

### OpenCode's Discretion
- Nomes exatos dos campos da resposta de reveal (`contact_email`/`contact_phone` com `null` para o ausente) e se o backend já devolve `wa.me`/`mailto` prontos ou o Phase 4 formata a partir do E.164 (a Fase 2 já decidiu que o telefone é armazenado em E.164 e que o front monta o link — presumir que o backend devolve cru).
- Shape estendido do `/health` (nome do campo de status do Turnstile) e nível de detalhe do warning de startup.
- Estrutura interna de arquivos: `app/core/client_ip.py`, `app/core/ratelimit.py`, `app/services/turnstile.py`, `app/schemas/job.py` (`RevealRequest`/`ContactRevealResponse`) — a única exigência é que o contato **só** exista nesses schemas de reveal, nunca em `JobPublic`.
- Mecânica do `key_func` do slowapi e do handler de 429 em pt-BR (a copy "Muitas tentativas. Aguarde alguns segundos e tente novamente." já está no 03-UI-SPEC).
- Como resetar o store in-memory do limiter entre testes (fixture) e se o `hostname` do Siteverify é checado condicionalmente ou sempre.
- Se `TURNSTILE_SITE_KEY` (backend, opcional) é lido do env ou fixado no widget.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Escopo e requisitos
- `.planning/ROADMAP.md` — Phase 3: goal, dependências (Phase 1), 4 critérios de sucesso e a marcação HIGH RISK.
- `.planning/REQUIREMENTS.md` — SECR-01, SECR-02, SECR-03, PUBL-05 (linhas 53–55, 42); tabela de rastreabilidade.
- `.planning/PROJECT.md` — visão, constraints (stack fixada, pt-BR, admin único), Key Decisions (a linha "Servir contato via endpoint dedicado" já registra o anti-padrão client-side).

### Pesquisa e contrato técnico (obrigatório)
- `.planning/phases/03-contact-reveal-anti-spam/03-RESEARCH.md` — mecânica do Siteverify (300 s, single-use, `timeout-or-duplicate`, params), padrão de IP atrás de proxy (Railway sobrescreve X-Real-IP; Render anexa ao XFF), wiring do slowapi, 7 pitfalls, mapa de requisitos → teste, architecture de validação.
- `.planning/phases/03-contact-reveal-anti-spam/03-UI-SPEC.md` — contrato visual e de copy desta fase: máquina de estados do reveal (idle/verifying/revealed/error 403|429|404), copy pt-BR das mensagens de erro, `loginAdmin(password, cfToken)`, reset do widget, botão "Entrar" desabilitado sem `cfToken`. **O reveal público é implementado na Phase 4 contra este contrato.**
- `.planning/research/ARCHITECTURE.md` — L282 (contrato REST do reveal), L464-L468 (onde o Turnstile acontece), L485-L489 (anti-patterns), L55-L95 (estrutura de pastas), L438-L462 (env vars e topologia de deploy).
- `.planning/research/PITFALLS.md` — Pitfall 7 (contato oculto ≠ contato protegido; os 3 requisitos do endpoint), seção "Security Mistakes" (linhas 380–391), checklist "Looks Done But Isn't" (linhas 423–435), "Pitfall-to-Phase Mapping" (linhas 456–477).
- `.planning/research/STACK.md` — `next-turnstile` 1.0.7, httpx 0.28.1, Pydantic v2, pytest/pytest-asyncio (versões fixadas).

### Decisões herdadas (não reabrir)
- `.planning/phases/01-backend-foundation-data-admin-auth/01-CONTEXT.md` — D-06 (UUID opaco), D-17 (filtro `published AND expires_at > now()`), D-18 (contato nunca no payload público), D-04 (Turnstile/rate limit do login adiados para cá), D-05 (env obrigatório, falha rápido).
- `.planning/phases/02-llm-extraction-pipeline/02-CONTEXT.md` — D-04 (página mínima de paste = `ExtractForm.tsx`, tocada nesta fase), telefone armazenado em E.164 (wa.me é montado no front).
- `AGENTS.md` — stack fixada, tema dark roxo, pt-BR, admin único.

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `backend/app/crud/jobs.py::get_published(session, job_id)` — já filtra `status='published' AND expires_at > now()`; **reusar como está** para o 404 do reveal (D-03). Não criar um `get_revealable` paralelo.
- `backend/app/deps.py` — padrão de `Depends` com `dependency_overrides` (mesmo mecanismo do override de `get_session` nos testes); é onde entra o `get_turnstile_verifier` sobrescrevível para stubar o Siteverify nos testes.
- `backend/app/schemas/job.py::JobPublic` — schema **sem** campos de contato; o novo `ContactRevealResponse` é o único lugar do projeto onde `contact_email`/`contact_phone` aparecem num schema de resposta.
- `backend/app/core/config.py::Settings` — `BaseSettings` com `env_file=".env"`, validação de env obrigatório no import; o default da chave de teste e o bloqueio de chaves de teste em prod entram aqui (D-11/D-12).
- `backend/app/main.py::create_app()` — app factory; é onde o `app.state.limiter` e o exception handler de `RateLimitExceeded` são registrados.
- `frontend/app/admin/paste/ExtractForm.tsx` — já é `"use client"` (o pacote `next-turnstile` não tem diretiva `"use client"` própria — PITFALL 6 do 03-RESEARCH): o widget entra aqui, sem arquivo novo.
- `frontend/lib/api.ts` — `loginAdmin(password)` vira `loginAdmin(password, cfToken)`; o padrão de extrair `body.detail` do erro para pt-BR já existe e é o que a UI-SPEC exige.
- `frontend/app/admin/paste/globals-admin.css` — tokens de cor/tipografia/spaçamento do admin; a UI-SPEC exige reaproveitar `.admin-error` e o estado disabled `opacity:.5; cursor:not-allowed`.

### Established Patterns
- **Camadas**: `api/v1` (router fino) → `services` → `crud` → `schemas`/`models`. O serviço do Turnstile é a primeira peça em `services/` que não é extração.
- **Erros pt-BR no `detail`**: o frontend renderiza `body.detail` direto — os 403/404/429 novos devem falar português.
- **Chaves obrigatórias no startup**: o padrão do `Settings` já falha rápido; a chave do Turnstile segue o mesmo caminho.
- **Testes**: pytest + pytest-asyncio (`asyncio_mode=auto`), `testpaths=["tests"]`, override de dependência em `tests/conftest.py`; a suíte atual tem 104 testes que precisam seguir verdes.
- **Frontend**: sem Tailwind, sem shadcn, sem biblioteca de ícones — CSS plano com variáveis. `next-turnstile` entra como dependência npm.

### Integration Points
- `backend/app/api/v1/public.py` — a rota `POST /jobs/{job_id}/reveal-contact` entra neste router (prefixo `/public`, sem auth).
- `backend/app/api/v1/auth.py` — o login passa a receber `cf_token` e a validar Turnstile antes do bcrypt (D-17); o comentário "Turnstile + rate limiting added in Phase 3 — do NOT add them here" (linhas 18-19) deixa de valer.
- `backend/app/api/v1/router.py` — registro das rotas; `health.py` é onde o `/health` reporta o status do Turnstile (D-14).
- `backend/app/schemas/auth.py::LoginRequest` — ganha `cf_token`.
- `backend/pyproject.toml` — adicionar `slowapi==0.1.10` (e `limits` transitivo); `frontend/package.json` — adicionar `next-turnstile@1.0.7`.

</code_context>

<specifics>
## Specific Ideas

- **Chaves de teste do Cloudflare** (funcionam em `localhost`, sem conta): `1x…AA` sempre aprova · `2x…AA` sempre falha · `3x…AA` devolve `timeout-or-duplicate`. Dev local e CI rodam com elas; a CI deve usar a `1x…` apenas.
- **Verificação manual (UAT)**: o único caminho real do Siteverify nesta fase é o **login do admin** — é por ele que se confirma que a Cloudflare está sendo chamada de verdade (o dashboard do Turnstile deve mostrar validações > 0). O reveal público só ganha UI na Phase 4.
- **`timeout-or-duplicate` é o estado normal de retry**, não um bug: o frontend deve traduzir para "Verificação anti-bot falhou — tente novamente" e resetar o widget (copy já definida na UI-SPEC).
- **A existência de uma chave real do Cloudflare é tarefa humana** (conta + widget + hostname allowlist). Até lá, tudo é verificável com as chaves de teste — exceto a prova "de produção", que fica para o Phase 6.
- **Warning silencioso é o pior resultado**: se o backend subir sem a chave de verdade, a proteção não existe e nada denuncia — por isso D-11 (falha no startup) e D-14 (warning + `/health`).
- **O widget do reveal na Phase 4 é montado no momento do clique**, nunca pré-mintido: o token vive 300 s e é single-use.

</specifics>

<deferred>
## Deferred Ideas

- **UI do reveal no frontend** (botão "Mostrar contato", modal, máquina de estados `idle → verifying → revealed | error`, cache em memória por vaga, `wa.me`/`mailto`) — **Phase 4** (PUBL-04/PUBL-06). O contrato está fixado em D-01 e D-04 + no 03-UI-SPEC.
- **Página pública mínima para verificar o reveal de ponta a ponta** — **Phase 4** (decidido explicitamente NÃO fazer nesta fase).
- **Conta Cloudflare + widget de produção** e plugar `NEXT_PUBLIC_TURNSTILE_SITE_KEY` (Vercel) + `TURNSTILE_SECRET_KEY` (Railway/Render) — **Phase 6** (deploy).
- **Limiter distribuído (Redis/tabela)** se o backend sair de 1 worker — **Phase 6** (topologia de deploy). Hoje o in-memory é suficiente e zera a cada restart/deploy.
- **Denúncia de vaga / relatório de abuso** (TRST-02) e páginas legais (TRST-03) — **Phase 6**.
- **Higiene de tooling**: `uv` não está instalado no ambiente (o `pyproject.toml`/`uv.lock` do backend ficam sem regeneração do lock) — item de dívida já registrado no STATE.md.

</deferred>

---

*Phase: 03-contact-reveal-anti-spam*
*Context gathered: 2026-10-21*
