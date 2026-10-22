---
phase: 03-contact-reveal-anti-spam
plan: 02
subsystem: api
tags: [turnstile, cloudflare, siteverify, fail-closed, slowapi, rate-limit, fastapi, httpx, pytest, dependency-overrides]

# Dependency graph
requires:
  - phase: 01-backend-foundation-data-admin-auth
    provides: FastAPI app skeleton (create_app), Settings base, pytest harness com fixtures engine/db_session/client
  - phase: 03-contact-reveal-anti-spam
    provides: (plan 03-01) resolve_client_ip (chave do bucket por IP), TURNSTILE_* em Settings com default fail-closed de dev
provides:
  - TurnstileVerifier assíncrono (httpx) contra o Siteverify, fail-closed em qualquer erro, com taxonomia de error-codes e action binding
  - TurnstileResult (frozen dataclass) + TURNSTILE_CHALLENGE_ERRORS / TURNSTILE_UNAVAILABLE_ERRORS / turnstile_error_detail() — copy pt-BR em um único lugar
  - Seam de DI get_turnstile_verifier em app/deps.py (sobrescrevível via dependency_overrides)
  - limiter slowapi in-memory (key_func=resolve_client_ip) + rate_limit_exceeded_handler com 429 pt-BR e header Retry-After
  - /api/v1/health reportando o status do Turnstile (live/test/disabled) sem revelar o segredo
  - Harness 100% offline: fixture app (com app.state.fake_turnstile), fixture client, fixture fake_turnstile e autouse reset_rate_limiter
affects: [03-contact-reveal-anti-spam-03-03, 03-contact-reveal-anti-spam-03-04, 03-contact-reveal-anti-spam-03-05, frontend-reveal]

# Tech tracking
tech-stack:
  added: [slowapi==0.1.10]
  patterns:
    - "fail-closed por padrão: toda falha do Siteverify (rede/5xx/JSON inválido) vira TurnstileResult(success=False) — nunca levanta exceção de operação"
    - "error-codes → copy pt-BR centralizada em turnstile_error_detail(); os routers 03-03/03-04 NÃO duplicam a copy"
    - "nomes de env resolvidos a cada request via callable de 0 args (reveal_limit/login_limit)"
    - "seam de DI por dependency_overrides: a suíte nunca fala com a Cloudflare"
    - "TDD RED/GREEN commits por task"

key-files:
  created:
    - backend/app/services/turnstile.py
    - backend/app/core/ratelimit.py
    - backend/tests/test_turnstile_service.py
    - backend/tests/test_ratelimit.py
    - backend/tests/test_health.py
  modified:
    - backend/app/deps.py
    - backend/app/main.py
    - backend/app/api/v1/health.py
    - backend/app/core/config.py
    - backend/tests/conftest.py

key-decisions:
  - "O cliente Siteverify nunca levanta exceção operacional: devolve TurnstileResult(success=False, error_codes=['internal-error']) — o portão fecha por padrão (D-13) e o router decide o 403"
  - "expected_action divergente vira error_code 'action-mismatch' (e não um success) — o reuso de token entre 'reveal' e 'login' é impossível por construction (T-03-03)"
  - "O form enviado ao Siteverify nunca leva 'sitekey' (a tabela oficial de params não tem esse campo); só secret/response/remoteip/idempotency_key"
  - "A chave do bucket é o IP resolvido por resolve_client_ip (nunca get_remote_address do slowapi) — D-10"
  - "Limite in-memory com default_limits=[]: nenhuma rota fora da Fase 3 é limitada por acidente — D-08"
  - "Handler 429 customizado devolve {'detail': ...} em pt-BR (o padrão do slowapi devolve {'error': ...} em inglês e o frontend só lê body.detail) — T-03-07"
  - "SafeLimiter (subclasse de Limiter) neutraliza o _inject_headers do slowapi quando a rota não declara response: Response — o behaviour do header Retry-After fica a cargo do handler pt-BR"
  - "O modo do Turnstile no /health é derivado do segredo EFETIVO (live/test/disabled) e a configuração da site key vira o booleano site_key_configured — assim a resposta tem 3 campos estáveis e nunca expõe segredo nem chave parcial"
  - "O /health lê get_settings() dentro da função (não no import) — pega o valor cacheado corretamente e mantém o router testável"

patterns-established:
  - "serviços de terceiro externos ao app são sempre alcançados por uma dependência sobrescrevível (get_turnstile_verifier) — nenhum import direto do cliente real nos routers"
  - "todo store global de teste (limiter) é zerado por fixture autouse — T-03-08"
  - "logs de anti-spam registram apenas error-codes/action/path — nunca token, nunca segredo, nunca corpo da resposta — T-03-05"

requirements-completed: []
requirements-contributed: [SECR-01, SECR-02]

# Metrics
duration: 93min
completed: 2026-10-21
---

# Phase 03 Plan 02: Turnstile Siteverify client, slowapi limiter e harness offline — Summary

**Cliente Cloudflare Siteverify fail-closed com taxonomia de error-codes e action binding, limiter slowapi in-memory por IP com 429 em pt-BR, status do Turnstile no `/health` e harness de teste 100% offline — nenhuma rota protegida exposta ainda.**

## Performance

- **Duration:** 93 min
- **Started:** 2026-10-21T22:46:58Z
- **Completed:** 2026-10-22T00:20:00Z
- **Tasks:** 3/3
- **Files modified:** 10 (5 novos, 5 modificados)

## Accomplishments
- `TurnstileVerifier.verify()` fala com o Siteverify via httpx e **fecha o portão em qualquer falha** (rede caída, HTTP 500, corpo não-JSON → `internal-error`; token vazio → `missing-input-response` sem nenhuma requisição HTTP), com 23 testes via `httpx.MockTransport` e zero chamada de rede
- Taxonomia de error-codes → copy pt-BR centralizada (`turnstile_error_detail`): "Verificação anti-bot falhou — tente novamente" para rejeição do desafio, "Verificação indisponível — tente novamente em instantes" para falha da própria verificação — os planos 03-03/03-04 importam essa função em vez de duplicar a copy
- `action` binding: um token verificado para `login` é rejeitado com `action-mismatch` no fluxo de `reveal` (e vice-versa); o form enviado nunca leva `sitekey`
- Limiter slowapi in-memory (`key_func=resolve_client_ip`, `default_limits=[]`, `headers_enabled=True`) com handler 429 próprio: `{"detail": "Muitas tentativas. Aguarde alguns segundos e tente novamente."}` + header `Retry-After`; buckets separados por IP; limites lidos do env **a cada request**
- Seam de DI `get_turnstile_verifier` em `app/deps.py` + `app.state.limiter` e `add_exception_handler` em `main.py` — o wiring pronto para os planos 03-03/03-04
- `/api/v1/health` passou a reportar `turnstile: {configured, mode, site_key_configured}` (`mode` = `live`/`test`/`disabled`) sem revelar o segredo nem a chave de teste
- Harness 100% offline: `FakeTurnstileVerifier` + fixtures `app`/`client`/`fake_turnstile` e autouse `reset_rate_limiter`; suíte completa **157 passed** (120 pré-existentes + 37 novos) sem rede

## task Commits

Cada task foi commitada atomicamente (TDD RED → GREEN):

1. **task 1: cliente Siteverify fail-closed — TDD (RED)** - `585fa0a` (test)
2. **task 1: cliente Siteverify fail-closed — TDD (GREEN)** - `34697b1` (feat)
3. **task 2: limiter + handler 429 + wiring + seam — TDD (RED)** - `5382746` (test)
4. **task 2: regressão slowapi sem `response: Response` — TDD (RED)** - `0e3db2a` (test)
5. **task 2: limiter + handler 429 + wiring + seam — TDD (GREEN)** - `2358703` (feat)
6. **task 3: status do Turnstile no /health + fixtures — TDD (RED)** - `6bb7715` (test)
7. **task 3: status do Turnstile no /health + fixtures — TDD (GREEN)** - `c15a5e3` (feat)

**TDD Gate Compliance:** para as 3 tasks existe um commit `test(...)` (RED) seguido de um `feat(...)` (GREEN) — gate do plano satisfeito.

## Files Created/Modified
- `backend/app/services/turnstile.py` — novo: `SITEVERIFY_URL`, `TurnstileResult` (frozen), `TurnstileVerifier.verify()`, `TURNSTILE_CHALLENGE_ERRORS`, `TURNSTILE_UNAVAILABLE_ERRORS`, `turnstile_error_detail()`
- `backend/app/core/ratelimit.py` — novo: `SafeLimiter`/`limiter` (slowapi, `key_func=resolve_client_ip`, `storage_uri="memory://"`), `RATE_LIMIT_MESSAGE`, `reveal_limit()`, `login_limit()`, `rate_limit_exceeded_handler`
- `backend/app/deps.py` — `get_turnstile_verifier()` (seam sobrescrevível) + `__all__` atualizado; `require_admin`/`bearer_scheme` intactos
- `backend/app/main.py` — `app.state.limiter = limiter` e `app.add_exception_handler(RateLimitExceeded, rate_limit_exceeded_handler)` antes do `include_router`; CORS/logging/lifespan intocados
- `backend/app/api/v1/health.py` — resposta nova com o bloco `turnstile`; `get_settings()` lido dentro da função
- `backend/app/core/config.py` — nova property `Settings.turnstile_mode` (`live`/`test`/`disabled`) ao lado do validator fail-closed
- `backend/tests/conftest.py` — `FakeTurnstileVerifier`, fixture `app` (override de sessão + verifier, `app.state.fake_turnstile`), fixture `client`, fixture `fake_turnstile`, autouse `reset_rate_limiter`; fixtures `engine`/`db_session`/`seed_*` preservados
- `backend/tests/test_turnstile_service.py` — novo: 23 testes do cliente Siteverify (sucesso, action binding, rede caída, 500, JSON inválido, token vazio sem request, conteúdo do form, copy pt-BR, ausência de `sitekey`)
- `backend/tests/test_ratelimit.py` — novo: 2×200 → 3×429 com `detail` pt-BR + `Retry-After`, IP distinto continua 200, wiring do app, limite lido a cada request
- `backend/tests/test_health.py` — novo: status do Turnstile no `/health`, segredo ausente do corpo e guarda do seam (o verifier real está substituído)

## Decisions Made
- O cliente Siteverify **não levanta exceção** em falha operacional: devolve `TurnstileResult(success=False)`. O router decide o 403 e a copy — o serviço fica testável e o portão fechado por construção (D-13)
- `action-mismatch` é modelado como *error code* e não como caso especial do router: o reuso de token entre `reveal` e `login` some no serviço, e não depende de cada endpoint lembrar de checar
- `SafeLimiter` (subclasse de `Limiter`) neutraliza o `_inject_headers` do slowapi quando a rota não declara `response: Response`. O slowapi, com `headers_enabled=True`, levanta `Exception: parameter 'response' must be an instance of starlette.responses.Response` nesse caso — o que quebraria as rotas 03-03/03-04. O `Retry-After` continua sendo emitido, agora pelo handler pt-BR
- `default_limits=[]` mantido: o limiter só age nas rotas decoradas — nenhuma rota fora da Fase 3 é limitada por acidente (D-08)
- `mode` do Turnstile deriva do segredo **efetivo** e a site key vira o booleano `site_key_configured`: a resposta tem 3 campos estáveis (`configured`, `mode`, `site_key_configured`) e o texto do plano que dizia "sem site key o modo é disabled" não faria sentido (o modo é sobre o *segredo*). O caso de teste do próprio plano (`mode == "test"` em dev) foi seguido
- As env vars `TURNSTILE_SECRET_KEY`/`TURNSTILE_SITE_KEY` **não** são definidas no `conftest.py`: em teste `ENV` é `dev` e o default de dev do plano 03-01 já é a chave always-pass; sobrescrever por env quebraria o teste de fail-closed do 03-01
- Teste extra em `test_health.py` (3º caso): garante que `get_turnstile_verifier` está de fato em `dependency_overrides` — os planos 03-03/03-04 dependem dessa seam e uma regressão nela só apareceria tarde
- **SECR-01 e SECR-02 seguem como "contribuídos", não "concluídos"** (mesmo tratamento do plano 03-01): este plano entrega a mecânica — validação server-side e limiter por IP — mas o requisito só vale quando o endpoint de reveal do plano 03-03 consumir o verifier e o limiter. Marcar agora daria sinal falso numa fase marcada HIGH RISK

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] `headers_enabled=True` do slowapi quebrava qualquer rota sem `response: Response`**
- **Found during:** task 2 (GREEN — a rota de teste do próprio plano não declarava `response: Response`)
- **Issue:** O slowapi 0.1.10 injeta headers de limite na resposta e, sem o parâmetro `request`/`response` na assinatura, levanta `Exception: parameter 'response' must be an instance of starlette.responses.Response` — erro 500 em vez de 429. Como o plano 03-03/03-04 protegem rotas com a assinatura enxuta, o problema se repetiria lá
- **Fix:** `SafeLimiter(Limiter)` sobrescreve `_inject_headers` para não tocar na resposta quando ela é `None`; o `Retry-After` passa a ser emitido pelo handler pt-BR (que já era obrigatório pelo contrato do frontend). Nenhuma rota fica limitada por acidente — o `default_limits=[]` do plano foi preservado
- **Files modified:** backend/app/core/ratelimit.py, backend/tests/test_ratelimit.py
- **Verification:** teste de regressão dedicado (rota sem `response: Response` → 429 com `detail` pt-BR, sem exceção 500); suíte completa 157 passed
- **Committed in:** `0e3db2a` (RED) + `2358703` (GREEN)

**2. [Rule 3 - Blocking] `backend/app/core/config.py` não estava na lista `files_modified` do plano**
- **Found during:** task 3 (implementação do `mode` do Turnstile)
- **Issue:** O plano exigia classificar a chave efetiva como `live`/`test`/`disabled` a partir do padrão de chave de teste do Cloudflare, mas o único regex existente vive no validator fail-closed de `Settings` — em `config.py`, arquivo fora da lista de arquivos do plano. Sem tocar nele, o regex teria de ser duplicado em `health.py`
- **Fix:** adicionada a property `Settings.turnstile_mode` em `app/core/config.py`, ao lado do regex — um único lar para o padrão de chave de teste. `health.py` só consome a property
- **Files modified:** backend/app/core/config.py
- **Verification:** `/health` devolve `mode == "test"` em dev (chave always-pass) e nunca expõe o segredo; 157 passed
- **Committed in:** `c15a5e3` (task 3 GREEN)

**3. [Rule 2 - Missing Critical] Guarda de regressão para a seam `get_turnstile_verifier`**
- **Found during:** task 3 (GREEN)
- **Issue:** O plano pedia 2 casos em `test_health.py`; nada garantia que `dependency_overrides[get_turnstile_verifier]` continuaria instalado. Uma regressão ali faria a suíte passar a chamar a Cloudflare de verdade (e a falhar offline) só nos planos 03-03/03-04
- **Fix:** terceiro caso em `test_health.py` verifica que o override está instalado e que `app.state.fake_turnstile` é o fake devolvido pelo fixture
- **Files modified:** backend/tests/test_health.py
- **Verification:** 3 passed em `tests/test_health.py`; suíte completa 157 passed
- **Committed in:** `c15a5e3` (task 3 GREEN)

---

**Total deviations:** 3 auto-fixed (1 bug, 1 blocking, 1 missing critical)
**Impact on plan:** Todos os três foram necessários para a correção e a testabilidade pedidas pelo próprio plano. O desvio 1 evita a mesma falha nos planos 03-03/03-04; o desvio 2 evita duplicar o regex de chave de teste; o desvio 3 blinda a seam de que os próximos planos dependem. Nenhum endpoint novo foi exposto.

## Issues Encountered
- **Gate de grep divergente:** o plano pede `grep -c "RateLimitExceeded" backend/app/main.py == 1`, mas a implementação natural (e a que o `key_links` do plano descreve) usa a string em dois pontos — o `import` e o `add_exception_handler`. O gate foi mantido em 2. A implementação foi mantida natural em vez de artificialmente "otimizada" para o gate, porque reduzir a uma ocorrência exigiria um alias de import que tornaria o código menos legível
- **Contagem de testes divergente:** o plano assume 104 testes pré-existentes; a suíte real tinha 120 (a contagem do plano é do momento da escrita). Os 120 pré-existentes continuam verdes sem nenhuma alteração nos arquivos de teste antigos
- **Contradição interna do plano no `mode`:** o texto diz "sem [site key] o modo é 'disabled'", mas o caso de teste do mesmo plano exige `mode == "test"` no ambiente de teste (que tem a chave always-pass). O caso de teste foi seguido e a informação da site key foi exposta como o booleano `site_key_configured`
- **BOM em arquivo escrito pelo PowerShell:** `backend/tests/test_ratelimit.py` saiu com BOM UTF-8 (efeito do `Set-Content` do PowerShell 5.1). Removido com um one-liner Python — o arquivo está BOM-free (igual aos demais)

## User Setup Required
Nenhum para este plano — o `TURNSTILE_SECRET_KEY`/`TURNSTILE_SITE_KEY` reais entram no plano 03-05 (com a chave de verdade e o warning de startup). O `/health` já expõe o modo (`test`/`live`/`disabled`) para o master conferir.

## Known Stubs
Nenhum. `FakeTurnstileVerifier` é um **test double** intencional (substitui o cliente real via `dependency_overrides`) — é o mecanismo do harness, não um stub de produção. `TurnstileResult` com campos anuláveis reflete o contrato do Siteverify (o campo `action` só vem quando a verificação passa), não um placeholder.

## Threat Flags
Nenhum novo além do threat register do plano. A superfície criada (verifier server-side, limiter por IP, `/health` público) está coberta por T-03-03 a T-03-08, todos com disposição `mitigate` implementada neste plano:
- T-03-03 (Spoofing): action binding + validação server-side + token nunca cacheado como "ok"
- T-03-04 (DoS): timeout finito de 10 s no httpx + fail-closed
- T-03-05 (Info Disclosure): logs registram só error-codes/action — nunca token, segredo ou corpo
- T-03-06 (Info Disclosure): `/health` só publica booleanos e o modo
- T-03-07 (Elevation of Privilege): handler 429 próprio com `detail` pt-BR + `Retry-After`
- T-03-08 (Tampering): fixture autouse `reset_rate_limiter` zera o store global

## Next Phase Readiness
- **Plano 03-03** pode consumir: `get_turnstile_verifier` (seam), `turnstile_error_detail()` (copy pt-BR — não duplicar), `limiter` + `reveal_limit()` (decorator `@limiter.limit(reveal_limit)`) e `TurnstileResult`
- **Plano 03-04** pode consumir: `login_limit()` e a mesma seam de DI
- Contrato de nomes respeitado integralmente (`SITEVERIFY_URL`, `TurnstileResult`, `TurnstileVerifier`, `TURNSTILE_CHALLENGE_ERRORS`, `TURNSTILE_UNAVAILABLE_ERRORS`, `turnstile_error_detail`, `limiter`, `RATE_LIMIT_MESSAGE`, `reveal_limit`, `login_limit`, `rate_limit_exceeded_handler`, `get_turnstile_verifier`)
- **SECR-01** (Turnstile validado no servidor antes de revelar o contato): **contribuído, não concluído** — o cliente fail-closed e o `action` binding existem e estão testados offline; o requisito só passa a valer com o endpoint de reveal do plano 03-03 consumindo `get_turnstile_verifier`. Mantido desmarcado em `REQUIREMENTS.md` de propósito (fase HIGH RISK)
- **SECR-02** (rate limiting por IP no endpoint de revelação): **contribuído, não concluído** — o limiter, o `key_func` por IP resolvido e o handler 429 pt-BR estão prontos; falta o endpoint do plano 03-03 usar `@limiter.limit(reveal_limit)`
- Nenhum endpoint protegido exposto — a Fase 3 continua sem rota pública nova
- Sem bloqueios

---
*Phase: 03-contact-reveal-anti-spam*
*Completed: 2026-10-21*

## Self-Check: PASSED

- Todos os 10 key files existem no disco (`app/services/turnstile.py`, `app/core/ratelimit.py`, `app/deps.py`, `app/main.py`, `app/api/v1/health.py`, `app/core/config.py`, `tests/conftest.py`, `tests/test_turnstile_service.py`, `tests/test_ratelimit.py`, `tests/test_health.py`)
- Todos os 7 commits de task encontrados no histórico: 585fa0a, 34697b1, 5382746, 0e3db2a, 2358703, 6bb7715, c15a5e3
- Verificação re-executada: suíte completa **157 passed** (1 warning pré-existente do SQLAlchemy), `tests/test_health.py` 3 passed
- Grep gates: `sitekey` em `turnstile.py` = 0 ✅ · `key_func=resolve_client_ip` em `ratelimit.py` = 1 ✅ · `get_turnstile_verifier` em `deps.py` = 2 (>= 2) ✅ · `RateLimitExceeded` em `main.py` = 2 (o gate do plano diz 1 — ver "Issues Encountered")
