---
phase: 03-contact-reveal-anti-spam
plan: 04
subsystem: security
tags: [turnstile, admin-login, credential-stuffing, rate-limit, slowapi, bcrypt, jwt, next-turnstile, react, fail-closed, pytest, security]

# Dependency graph
requires:
  - phase: 01-backend-foundation-data-admin-auth
    provides: rota POST /api/v1/auth/login (bcrypt + JWT), ADMIN_PASSWORD_HASH, require_admin, harness pytest
  - phase: 03-contact-reveal-anti-spam
    provides: (plano 03-01) knobs LOGIN_RATE_LIMIT=5/minute + resolve_client_ip; (plano 03-02) TurnstileVerifier fail-closed, turnstile_error_detail(), seam get_turnstile_verifier, limiter slowapi com 429 pt-BR; (plano 03-03) padrão da rota de reveal (rate limit → verificação → 200)
provides:
  - LoginRequest com cf_token obrigatório (1..2048) — o login sem token é 422
  - POST /api/v1/auth/login na ordem D-17: rate limit → Siteverify(action="login") → bcrypt → JWT; token recusado/indisponível = 403 com copy própria, nunca "Senha inválida"
  - Action binding no login: um token mintado para "reveal" é recusado com action-mismatch → 403 (T-03-16)
  - 429 no login com detail pt-BR + header Retry-After (bucket (IP, rota))
  - loginAdmin(password, cfToken) no front + widget Turnstile interaction-only com action="login" e reset por remount
  - Painel .admin-error no bloco de login (antes "Senha inválida" era invisível) e botão "Entrar" desabilitado sem cfToken
  - 7 casos de teste novos do login (12 no total em tests/test_auth.py), 100% offline
affects: [03-contact-reveal-anti-spam-03-05, 04-frontend-reveal-ui, 06-deploy, frontend-admin-login]

# Tech tracking
tech-stack:
  added: [next-turnstile==1.0.7, eslint==8.57.1, eslint-config-next==15.5.3]
  patterns:
    - "ordem de verificação do login: rate limit → Siteverify → bcrypt → JWT — a senha nunca é comparada sem um token válido na mão (D-17)"
    - "falha do Siteverify é sempre 403 e nunca 'Senha inválida': a copy vem de turnstile_error_detail(), nunca duplicada no router (D-18)"
    - "o shape do /auth/login e o widget do front saem no mesmo plano — mudar a API sem o front trancaria o admin fora do projeto com 422 (D-19)"
    - "next-turnstile não tem resetKey: o reset do widget é por remount com uma key nova do React (o useEffect de cleanup remove o widget antigo)"
    - "a site key é pública por definição; fora de produção a chave always-pass do Cloudflare assume, em produção sem env var o login fica bloqueado (fail closed)"
    - "TDD RED/GREEN por task, com o commit test(...) sempre precedendo o feat(...)"

key-files:
  created: []
  modified:
    - backend/app/schemas/auth.py
    - backend/app/api/v1/auth.py
    - backend/tests/test_auth.py
    - backend/tests/test_extract_api.py
    - frontend/lib/api.ts
    - frontend/app/admin/paste/ExtractForm.tsx
    - frontend/app/admin/paste/globals-admin.css
    - frontend/package.json
    - frontend/.env.local.example

key-decisions:
  - "O rate limit do login fica na rota e não no handler de senhas: o bucket é (IP, rota) pelo key_style='endpoint' herdado do plano 03-03 — um attacker que rotacione o corpo do request não escapa da janela"
  - "expected_action='login' no Siteverify do login: o action binding que o 03-03 criou para o reveal é reusado, então um token mintado para 'reveal' não abre o login (T-03-16)"
  - "O ip_address do Turnstile é omitido quando o IP resolvido é 'unknown' (mesma regra do reveal) — mandar 'unknown' para a Cloudflare poisons a estatística dela sem ganho nenhum"
  - "A cópia pt-BR do frontend é sempre o body.detail do backend: o painel .admin-error no bloco de login renderiza a string do backend sem mapeamento próprio no front"
  - "A site key de dev é a always-pass do Cloudflare (1x00000000000000000000AA) e só fora de produção; em produção a env var é obrigatória e a ausência bloqueia o login em vez de degradar"

patterns-established:
  - "todo endpoint que devolve segredo (JWT, contato) passa por verifier.verify() antes — a chamada de terceiro é a fronteira de confiança, não a comparação de senha"
  - "o reset de um widget de terceiro sem API de reset = remount com key nova do React"
  - "pinos exatos em package.json (nunca ^), seguindo a convenção do projeto"

requirements-completed: [SECR-03]
requirements-contributed: []

# Metrics
duration: 26min
completed: 2026-10-22
---

# Phase 03 Plan 04: Login do admin protegido por Turnstile + rate limit — Summary

**O único caminho para o JWT do master passou a exigir um Turnstile verificado no servidor antes de qualquer comparação de senha — backend e widget no mesmo plano, com a ordem D-17 e a copy de indisponibilidade provadas por teste.**

## Performance

- **Duration:** 26 min
- **Started:** 2026-10-22T00:59:49Z
- **Completed:** 2026-10-22T01:26:00Z
- **Tasks:** 2/2
- **Files modified:** 9 (0 criados, 9 modificados)

## Accomplishments
- `LoginRequest` passou a exigir `cf_token` (1..2048 chars): login sem token é **422** e nunca chega ao hash da senha
- `POST /api/v1/auth/login` reescrito na ordem D-17 — **rate limit → Siteverify(action="login") → bcrypt → JWT** — com o comentário "Turnstile + rate limiting added in Phase 3 — do NOT add them here" removido (ele deixou de valer)
- **A senha nunca é comparada sem um token válido na mão**: `authenticate_password()` só roda depois do `verifier.verify()` passar. O teste `test_login_turnstile_failure_does_not_reach_password_check` fixa isso (token recusado + senha errada = **403**, não 401) — um 401 ali provaria que a senha foi checada
- **403 tem duas copies distintas** (D-18), vindas de `turnstile_error_detail()`: "Verificação anti-bot falhou — tente novamente" (desafio recusado) e "Verificação indisponível — tente novamente em instantes" (a própria verificação caiu). Nenhuma delas é "Senha inválida"
- **Action binding no login**: um token mintado para `reveal` é recusado com `action-mismatch` → 403 (T-03-16)
- **Rate limit por IP no login**: `@limiter.limit(login_limit)` com o default `5/minute` (D-06) — o 6º POST do mesmo IP é 429 com `{"detail": "Muitas tentativas. Aguarde alguns segundos e tente novamente."}` + header `Retry-After`
- **Widget no formulário de login**: `next-turnstile@1.0.7` instalado (pin exato), renderizado em `appearance="interaction-only"` (sem checkbox visível) e `action="login"`, acima do botão "Entrar" — D-16 respeitado
- **"Entrar" nasce desabilitado** e só habilita com senha não vazia **e** `cfToken` presente; `onExpire`/`onError` limpam o token e o botão volta a travar (T-03-18)
- **Login falho remonta o widget** (`key` nova do React → remount → token novo): o token consumido pelo backend nunca é reenviado (D-19). `next-turnstile` não tem `resetKey` nem API de reset — o remount é o mecanismo
- **O `.admin-error` agora aparece no bloco de login**: antes o painel de erro só existia dentro do bloco `token &&`, então "Senha inválida" era literalmente invisível para o admin
- **Sem `NEXT_PUBLIC_TURNSTILE_SITE_KEY` o login não trava o projeto em dev**: fora de produção a chave always-pass do Cloudflare assume; **em produção** a env var é obrigatória e a ausência bloqueia o login com aviso explícito (fail closed)
- Suíte do backend em **175 passed** (168 pré-existentes + 7 novos), 100% offline; `npm run build` e `npm run lint` verdes

## task Commits

Cada task foi commitada atomicamente, com o par RED/GREEN do TDD:

1. **task 1: backend do login — cf_token, rate limit → Siteverify → bcrypt → JWT** — `3747f75` (test — RED), `ca8b034` (feat — GREEN)
2. **task 2: frontend — `loginAdmin(password, cfToken)` + widget interaction-only com reset** — `bc233ef` (test — RED), `b1bce2a` (feat — GREEN)

Commit de ajuste posterior: `1db7567` (docs — docstring do `LoginRequest` enxuto para o gate `grep -c "cf_token" == 1` do plano).

**TDD Gate Compliance:** task 1 RED (`3747f75` — 6 testes falhando com 6 passando) → GREEN (`ca8b034`); task 2 RED (`bc233ef` — build quebrado com `Module not found: Can't resolve 'next-turnstile'`) → GREEN (`b1bce2a` — build e lint verdes). Ambos os gates presentes e na ordem correta. Nenhum commit de REFACTOR foi necessário.

**Nota sobre o gate RED da task 2:** o frontend não tem runner de teste instalado (nenhum vitest/playwright no `package.json`), então o gate de falha é o próprio `npm run build`, que roda o type-check do TypeScript — foi ele que acusou o módulo ausente. É o gate que o próprio plano especifica para a task.

## Files Created/Modified
- `backend/app/schemas/auth.py` — `LoginRequest.password` + `LoginRequest.cf_token` (`Field(min_length=1, max_length=2048)`, **sem default** → obrigatório); `TokenResponse` intocado
- `backend/app/api/v1/auth.py` — a rota `login` com os decorators na ordem (`@router.post` → `@limiter.limit(login_limit)`), assinatura com `request: Request` + `verifier: TurnstileVerifier = Depends(get_turnstile_verifier)`, a sequência rate limit → Siteverify → bcrypt → JWT e o `remoteip` omitido quando o IP é `"unknown"`
- `backend/tests/test_auth.py` — os 3 testes que faziam login passaram a enviar `cf_token`; 7 casos novos (422, 403 recusado, 403 indisponível, 403-não-chega-na-senha, 401 com token válido, action mismatch, 429 com `Retry-After`)
- `backend/tests/test_extract_api.py` — o helper `_get_admin_token` passou a enviar `cf_token` (o shape do login mudou; ver desvio 1)
- `frontend/lib/api.ts` — `loginAdmin(password: string, cfToken: string)` envia `{ password, cf_token: cfToken }`; o tratamento de erro que lê `body.detail` permanece igual (é ele que renderiza a copy pt-BR do backend)
- `frontend/app/admin/paste/ExtractForm.tsx` — `import { Turnstile } from "next-turnstile"`, a constante `TURNSTILE_SITE_KEY` (env var → chave always-pass fora de produção → string vazia em produção), os states `cfToken`/`turnstileKey`, o `resetTurnstile()`, o widget `interaction-only`/`action="login"` acima do botão, o painel `.admin-error` no bloco de login e o `isLoginDisabled` com `!cfToken`
- `frontend/app/admin/paste/globals-admin.css` — `.admin-turnstile { margin-top: 1rem; max-width: 100%; overflow: hidden; }` com o comentário de nunca aplicar `transform`/`scale` no iframe da Cloudflare; tokens existentes reutilizados, nenhuma cor nova
- `frontend/package.json` — `"next-turnstile": "1.0.7"` em `dependencies` (pin exato, como as outras deps) e `"eslint": "8.57.1"` + `"eslint-config-next": "15.5.3"` em `devDependencies` (ver desvio 2). **A versão do Next (15.5.3) e do React (19.1.1) não mudou**
- `frontend/.env.local.example` — `NEXT_PUBLIC_TURNSTILE_SITE_KEY=` (vazio = chave de teste em dev; obrigatório em produção)
- `.planning/phases/03-contact-reveal-anti-spam/deferred-items.md` — novo: discoveries fora do escopo (CVEs do Next, tsconfig pré-existente, aviso de lockfile do Next)

## Decisions Made
- **A ordem das verificações é o contrato, e o teste a fixa por status code** — a prova de que a senha não é comparada antes do Turnstile é um 403 (não 401) no caso "token recusado + senha errada". Se a implementação voltasse a checar a senha primeiro, o teste cairia para 401 e falharia
- **Action binding reaproveitado no login** — o `expected_action="login"` é a mesma mecânica que o 03-03 criou para o reveal; o `FakeTurnstileVerifier` do harness já sabia simular `action-mismatch`, então o caso saiu de graça e cobre T-03-16
- **O `remoteip` é omitido quando o IP resolvido é `"unknown"`** — mesma regra do reveal: mandar a string `"unknown"` para a Cloudflare apenas polui a estatística dela
- **A site key de dev é a always-pass do Cloudflare e só fora de produção** — `process.env.NODE_ENV === "production" ? "" : "1x00000000000000000000AA"`. Em produção, sem env var, o widget não renderiza, o aviso aparece e o botão continua desabilitado: o projeto nunca fica trancado fora, e a produção nunca abre uma brecha
- **O widget é resetado por remount, não por API** — `next-turnstile@1.0.7` não tem `resetKey` nem ref exposto; o `useEffect` de cleanup do pacote chama `window.turnstile.remove(widgetId)` e o remount renderiza um widget novo. A `key` do React é o mecanismo oficial de reset aqui
- **O `.admin-error` do bloco de login renderiza a string do backend sem mapeamento** — a copy pt-BR do `detail` (403 anti-bot / 403 indisponível / 401 senha / 429 rate limit) chega intacta ao admin; o front não tem tabela de erros
- **SECR-03 foi marcado como concluído** (o frontend também está no mesmo plano): com o backend exigindo o token e o widget produzindo-o, o requisito vale de ponta a ponta — não é o caso dos planos 03-01/03-02, que entregaram só a mecânica

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] `backend/tests/test_extract_api.py` também faz login — e o plano só listava `test_auth.py`**
- **Found during:** task 1 (GREEN — suíte completa)
- **Issue:** o helper `_get_admin_token` de `tests/test_extract_api.py` fazia `POST /api/v1/auth/login` com só `{"password": ...}`. Com o `cf_token` agora obrigatório, os **8 testes de extração** passaram a devolver 422 (`assert 422 == 200`). A lista `files_modified` do plano não cita esse arquivo, e o plano acreditava que só 3 testes do `test_auth.py` precisavam de ajuste
- **Fix:** o helper passou a enviar `{"password": ..., "cf_token": "token-de-teste"}` — o token real nunca é validado porque o `FakeTurnstileVerifier` do harness substitui o cliente da Cloudflare
- **Files modified:** backend/tests/test_extract_api.py
- **Verification:** suíte completa **175 passed** (168 pré-existentes + 7 novos), sem regressão nos testes de extração
- **Committed in:** ca8b034 (task 1 GREEN)

**2. [Rule 3 - Blocking] `npm run lint` era impossível: `eslint` e `eslint-config-next` nunca foram declarados**
- **Found during:** task 2 (GREEN — o gate de lint do plano)
- **Issue:** o `frontend/package.json` tem o script `"lint": "next lint"` e existe um `.eslintrc.json` com `"extends": "next/core-web-vitals"` — mas `devDependencies` nunca declararam `eslint` nem `eslint-config-next` (foram adicionados no plano 02-04 e o gap ficou). O `next lint` morria com `Failed to load config "next/core-web-vitals" to extend from`, **antes** de qualquer regra ser avaliada. O gate de lint do plano não podia passar por motivo nenhum que não fosse meu
- **Fix:** `eslint@8.57.1` + `eslint-config-next@15.5.3` instaladas como devDependencies com **pin exato** (a versão do `eslint-config-next` casa com a do Next). O `.eslintrc.json` não foi tocado — o ESLint 8 é o par natural do formato `eslintrc` que o projeto já usa
- **Files modified:** frontend/package.json
- **Verification:** `npm run lint` → `✔ No ESLint warnings or errors`; `npm run build` continua verde
- **Committed in:** b1bce2a (task 2 GREEN)

**3. [Rule 3 - Blocking] `npm install` gravou `"^1.0.7"` — o plano exige o pin exato**
- **Found during:** task 2 (GREEN — instalação da dependência)
- **Issue:** o `npm install next-turnstile@1.0.7` grava `"^1.0.7"` por padrão, e o plano exige `"next-turnstile": "1.0.7"` (versão exata, "como as outras deps do projeto" — que usam `next: 15.5.3`, `react: 19.1.1`, `typescript: 5.9.2`). Um `^` permitiria um bump automático de minor em produção, sem revisão
- **Fix:** o `package.json` foi editado para o pin exato e o `npm install` refeito para o lockfile local ficar consistente
- **Files modified:** frontend/package.json
- **Verification:** `git diff frontend/package.json` → `"next-turnstile": "1.0.7"`
- **Committed in:** b1bce2a (task 2 GREEN)

**4. [Rule 3 - Blocking] Os comandos de verificação do plano rodam a partir da raiz — e a suíte não sobe de lá**
- **Found during:** task 1 (RED)
- **Issue:** o `<verify>` do plano manda `backend\.venv\Scripts\python.exe -m pytest backend/tests/test_auth.py -q` executado na **raiz do repo**. De lá o pytest não lê `backend/pyproject.toml` e perde `asyncio_mode = "auto"`, o que faz a suíte inteira explodir em errors. Já registrado no STATE.md pelo plano 03-03
- **Fix:** nenhum arquivo do repo foi alterado — a suíte é executada a partir de `backend/` (`cd backend; .venv\Scripts\python.exe -m pytest -q`), que é onde a config do projeto mora
- **Files modified:** nenhum
- **Verification:** suíte completa verde a partir de `backend/` (175 passed)
- **Committed in:** n/a (correção de ferramenta, sem mudança de código)

---

**Total deviations:** 4 auto-fixed (4 blocking)
**Impact on plan:** Nenhuma mudança de escopo de código — as quatro correções foram de ferramenta/arquivo-adjacente. O desvio 1 evitou 8 falsos vermelhos na suíte de extração; o desvio 2 destravou o gate de lint que o próprio plano exige; o desvio 3 preservou a convenção de pin exato do projeto; o desvio 4 foi só de comando. O comportamento entregue é exatamente o especificado.

## Issues Encountered
- **Contagem de testes divergente:** o `<done>` da task 1 fala em "11 casos verdes" (5 existentes + 6 novos do roteiro) e o bloco `artifacts` fala em "7 novos". O roteiro de `<acceptance_criteria>` lista 6 testes novos; a 7ª (**action binding**: um token mintado para `reveal` não abre o login) foi adicionada porque a própria `<acceptance_criteria>` exige esse comportamento ("um token mintado para `reveal` **não** abre o login") e o threat register tem o T-03-16 sobre reuso de token entre fluxos. Total final: **12 casos** em `tests/test_auth.py`
- **Gate de grep de `cf_token`:** o plano pede `grep -c "cf_token" backend/app/schemas/auth.py == 1`, mas a docstring do `LoginRequest` repetia o nome do campo (2 ocorrências). Em vez de mexer na semântica, a docstring foi reescrita para dizer "the Cloudflare Turnstile token" — commit isolado (`1db7567`), e o gate agora dá 1
- **Gate de grep de `turnstile_error_detail`:** o plano não define gate para o router do login, mas o padrão do `03-03` foi mantido — a copy é importada de `turnstile_error_detail()` e **não** duplicada no router
- **`npm audit` reporta 8 vulnerabilidades** (7 high, 1 critical) — **todas em `next@15.5.3`** (RCE no React flight protocol, exposição de Server Actions, DoS, cache poisoning, SSRF, XSS). `next-turnstile` não tem dependência de runtime, então **nenhuma** vulnerabilidade veio do widget. O plano proíbe mexer na versão do Next e a stack é decisão do usuário → registrado em `deferred-items.md` (D-1) para a Phase 6, junto do `tsconfig.json` pré-existente (D-2) e do aviso de lockfile do Next (D-3)
- **`next lint` está deprecado no Next 16** — o aviso aparece no stderr mas não quebra o gate; fica para a Phase 6 junto com o bump de Next (D-1)
- **Suíte lenta:** ~3 min por rodada (round-trips ao Postgres de teste); rodada 5 vezes (RED task 1, GREEN task 1 + suíte completa, RED task 2 via build, GREEN task 2 via build/lint, e a verificação final)

## User Setup Required
None para o código — mas **a chave real do Cloudflare continua pendente**: `NEXT_PUBLIC_TURNSTILE_SITE_KEY` (front) e `TURNSTILE_SECRET_KEY`/`TURNSTILE_SITE_KEY` (backend) são tarefa da Phase 6, já listada como deferred em `03-CONTEXT.md`. Até lá, dev e CI usam a chave always-pass (front) e a always-pass secret (backend, via `effective_turnstile_secret` do plano 03-01). O smoke real contra a API da Cloudflare é o plano 03-05.

## Known Stubs
None. `FakeTurnstileVerifier` é um **test double** intencional (substitui o cliente real via `dependency_overrides`) — é o mecanismo do harness do plano 03-02, não um stub de produção. O `TURNSTILE_SITE_KEY` com fallback para a chave always-pass é comportamento **real** fora de produção (documentado no `.env.local.example`), não placeholder. A string vazia em produção não é stub: é o fail closed — sem site key, o widget não renderiza, o aviso aparece e o botão "Entrar" continua desabilitado.

## Threat Flags

| Flag | File | Description |
|------|------|-------------|
| threat_flag: build-time-site-key-inlining | frontend/app/admin/paste/ExtractForm.tsx | `NEXT_PUBLIC_TURNSTILE_SITE_KEY` é **inlinada no bundle no momento do build** (comportamento padrão do Next). Trocar a site key no painel da Cloudflare depois do build **não** atualiza o widget do front — o build tem que ser refeito. Chave rotacionada sem rebuild = login quebrado em produção |
| threat_flag: dependency-cve-backlog | frontend/package.json | `npm audit` reporta 8 vulnerabilidades (7 high, 1 critical) **todas em `next@15.5.3`**, pré-existentes a esta fase. `next-turnstile` não tem dependência de runtime (nenhuma vulnerabilidade veio do widget). O bump de Next é proibido pelo plano e é decisão de stack do usuário → Phase 6 |
| threat_flag: dev-fallback-site-key | frontend/app/admin/paste/ExtractForm.tsx | Fora de produção a site key always-pass do Cloudflare é assumida. O backend tem o mesmo fallback (`effective_turnstile_secret`, plano 03-01) e o `Settings` **recusa** chaves de teste fora de `ENV=dev` (D-12) — a proteção contra chave de teste em produção está no backend, não no front. Se o front for compilado com `NODE_ENV=production` e a env var ausente, o login bloqueia (fail closed) |

Nenhuma superfície nova fora do threat register do plano: a rota de login é exatamente o componente coberto por T-03-15 (senha comparada só depois do Turnstile), T-03-16 (action binding), T-03-17 (só a site key no browser), T-03-18 (token consumido nunca reenviado), T-03-19 (rate limit por IP) e T-03-20 (erro explicável + `Retry-After`). Todos com disposição `mitigate` implementada e coberta por teste.

## Next Phase Readiness
- **Plano 03-05** pode consumir: o contrato real do login (`POST /api/v1/auth/login` com `{ password, cf_token }` → 200 `{access_token, token_type, expires_in}` · 401 "Senha inválida" · 403 "Verificação anti-bot falhou — tente novamente" / "Verificação indisponível — tente novamente em instantes" · 422 sem `cf_token` · 429 + `Retry-After`), o widget `interaction-only` com `action="login"` e a site key always-pass para o smoke local
- O smoke de browser do 03-05 já tem o caminho destravado: em dev o front usa a chave always-pass e o backend usa a always-pass secret, então o login funciona **sem** conta Cloudflare — o que falta é a prova de que a chamada real ao Siteverify acontece (aí sim a chave de verdade da Cloudflare)
- **Phase 4** (UI do reveal) não é afetada: o `loginAdmin` só é usado pelo admin. O Phase 4 vai precisar do widget na modal de reveal com `action="reveal"` — e o `next-turnstile` dá um `id="turnstile-widget"` fixo por padrão, então o widget do login e o da modal precisam de `id`s distintos quando coexistirem
- Contrato de nomes respeitado integralmente (`LoginRequest.cf_token`, `turnstile_error_detail`, `get_turnstile_verifier`, `login_limit`, `limiter.limit(login_limit)`, `resolve_client_ip`, `UNKNOWN_IP`, `loginAdmin(password, cfToken)`)
- Sem bloqueios

## Requirements
- **SECR-03** (Turnstile também protege o login do admin contra credential stuffing): **concluído** — o backend exige um `cf_token` verificado server-side (ordem rate limit → Siteverify → bcrypt → JWT) e o front produz o token no formulário de login; o rate limit por IP (`5/minute`) fecha o brute force e o action binding impede o reuso de token entre `reveal` e `login`
- **SECR-01** e **SECR-02** (marcados no 03-03) permanecem concluídos — este plano não os altera
- **PUBL-05** (marcado no 03-03) permanece concluído — este plano não toca no payload público

---
*Phase: 03-contact-reveal-anti-spam*
*Completed: 2026-10-22*

## Self-Check: PASSED

- Todos os 9 arquivos-chave existem em disco (`backend/app/schemas/auth.py`, `backend/app/api/v1/auth.py`, `backend/tests/test_auth.py`, `backend/tests/test_extract_api.py`, `frontend/lib/api.ts`, `frontend/app/admin/paste/ExtractForm.tsx`, `frontend/app/admin/paste/globals-admin.css`, `frontend/package.json`, `frontend/.env.local.example`)
- Todos os 5 commits de task encontrados no histórico: `3747f75`, `ca8b034`, `bc233ef`, `b1bce2a`, `1db7567`
- Verificação reexecutada: suíte completa **175 passed** (168 pré-existentes + 7 novos), `tests/test_auth.py` 12 passed; `npm run build` → `✓ Compiled successfully`; `npm run lint` → `✔ No ESLint warnings or errors`
- Grep gates: `cf_token` em `backend/app/schemas/auth.py` = 1 ✅ · `limiter.limit(login_limit)` em `backend/app/api/v1/auth.py` = 1 ✅ · `expected_action="login"` = 1 ✅ · `cf_token` em `frontend/lib/api.ts` = 1 ✅ · `next-turnstile` em `frontend/package.json` = 1 ✅ · `appearance="interaction-only"` em `ExtractForm.tsx` = 1 ✅ · `loginAdmin(password, cfToken)` = 1 ✅
- Nenhum arquivo pré-existente alheio ao plano foi staged ou commitado: `frontend/tsconfig.json` e os scratch files `backend/_*.txt`, `backend/body.json`, `frontend/next-env.d.ts` seguem intactos na working tree; `frontend/package-lock.json` permanece **não rastreado** (o diff versionado do front é só o `package.json`)
