---
phase: 03-contact-reveal-anti-spam
plan: 01
subsystem: security
tags: [turnstile, fail-closed, rate-limit, slowapi, client-ip, proxy, pydantic-settings, pytest]

# Dependency graph
requires:
  - phase: 01-backend-foundation-data-admin-auth
    provides: Settings base (BaseSettings + env_file), layout app/core/*, harness pytest (asyncio_mode=auto), padrão "falha rápido se falta env"
  - phase: 02-llm-extraction-pipeline
    provides: convenção de pin exato em pyproject + uv.lock sincronizado, layout de seção `# --- Nome (Fase N) ---` no .env.example
provides:
  - Settings fail-closed do Turnstile: `TURNSTILE_SECRET_KEY`/`TURNSTILE_SITE_KEY`/`TURNSTILE_TIMEOUT_SECONDS` + `@model_validator(mode="after")` que derruba o startup fora de dev (D-11) e rejeita as chaves de teste `1x`/`2x`/`3x` (D-12)
  - `DEV_TURNSTILE_SECRET` (chave pública always-pass do Cloudflare) + propriedade `effective_turnstile_secret` (fallback de dev)
  - Knobs de rate limit por env: `REVEAL_RATE_LIMIT=10/minute` e `LOGIN_RATE_LIMIT=5/minute` (D-06)
  - `app/core/client_ip.py::resolve_client_ip` — cadeia proxy-aware `X-Real-IP` → XFF mais à direita público → `request.client.host` → `"unknown"` (D-10)
  - `slowapi==0.1.10` pinado em pyproject/uv.lock e instalado no venv (`limits==5.8.0` transitivo)
  - 16 testes unitários novos (9 de config + 7 de IP), sem rede e sem banco
affects: [03-turnstile-verifier-and-limiter, 03-reveal-contact-endpoint, 03-admin-login-turnstile, 04-frontend-reveal-ui, 06-deploy]

# Tech tracking
tech-stack:
  added: [slowapi==0.1.10, limits==5.8.0]
  patterns:
    - "config fail-closed: segredo ausente ou de teste fora de dev derruba o startup — nunca fail-open silencioso (D-11/D-12)"
    - "chave de rate limit nunca é o leftmost do XFF nem o get_remote_address default do slowapi (D-10)"
    - "campo novo de Settings entra sempre com default seguro + validador `model_validator(mode='after')`"
    - "regex de bloqueio de chave de teste calibrado no comprimento real (35 chars: prefixo `Nx` + 31 + `AA`)"

key-files:
  created:
    - backend/app/core/client_ip.py
    - backend/tests/test_client_ip.py
    - backend/tests/test_security_config.py
  modified:
    - backend/app/core/config.py
    - backend/.env.example
    - backend/pyproject.toml
    - backend/uv.lock

key-decisions:
  - "O X-Real-IP é aceito quando apenas PARSEIA como IP (não quando é 'público'): as faixas de documentação do IANA (203.0.113.0/24, 198.51.100.0/24) têm `is_private == True` no `ipaddress` do Python, então um filtro de 'público' derrubaria o X-Real-IP do Railway e o caso cairia no XFF — o filtro de 'público' fica restrito às entradas do X-Forwarded-For, como pede o D-10"
  - "O check de chave de teste usa `^[123]x[0-9A-Za-z]{31}AA$` (35 chars, comprimento real dos segredos do Cloudflare): com `{30}` a chave always-pass passaria no validator de prod e o D-12 ficaria quebrado"

patterns-established:
  - "primitivas de segurança são testadas isoladas: `Settings(_env_file=None, **kwargs)` para não tocar o `.env` local, e `starlette.requests.Request` montado com scope HTTP à mão para testar o resolver de IP sem app/DB"
  - "TDD RED/GREEN por task, com o commit `test(...)` sempre precedendo o `feat(...)`"

requirements-completed: []
requirements-contributed: [SECR-02]

# Metrics
duration: 8min
completed: 2026-10-21
---

# Phase 03 Plan 01: Security Core — Config Fail-Closed, Rate-Limit Knobs e Resolver de IP Summary

**Configuração do Turnstile que falha fechada fora de dev, limites de rate limit ajustáveis por env e um resolvedor de IP consciente de proxy — as primitivas testáveis que sustentam SECR-01/02/03, sem expor nenhum endpoint novo.**

## Performance

- **Duration:** 8 min
- **Started:** 2026-10-21T22:21:27Z
- **Completed:** 2026-10-21T22:29:36Z
- **Tasks:** 2/2
- **Files modified:** 6 (3 criados, 3 modificados + uv.lock)

## Accomplishments
- `Settings` agora valida o Turnstile **fail-closed**: secret vazio fora de `ENV=dev` derruba o startup (`TURNSTILE_SECRET_KEY é obrigatória fora de dev (D-11)`) e as chaves de teste conhecidas do Cloudflare (`1x…`/`2x…`/`3x…`) também (`D-12`) — um `.env.example` copiado para produção não auto-aprove mais nada
- `effective_turnstile_secret` devolve o secret configurado e, em dev sem secret, cai na chave pública always-pass (`1x0000000000000000000000000000000AA`) — dev local e CI rodam sem conta Cloudflare
- Knobs `REVEAL_RATE_LIMIT=10/minute` e `LOGIN_RATE_LIMIT=5/minute` expostos por env e documentados no `.env.example`, com o aviso de que em dev o secret pode ficar vazio e fora de dev o startup falha sem ele
- `resolve_client_ip` implementa a cadeia fixa do D-10 (`X-Real-IP` → entrada mais à direita do XFF que não seja privada → `client.host` → `"unknown"`), com o leftmost do XFF nunca usado
- `slowapi==0.1.10` instalado no venv e pinado em `pyproject.toml`/`uv.lock` (`limits==5.8.0` transitivo)
- 16 testes novos, suíte completa em **120 passed** (104 pré-existentes intactos) e nenhum endpoint novo — superfície de ataque inalterada

## task Commits

Cada task foi commitada atomicamente, com o par RED/GREEN do TDD:

1. **task 1: Settings fail-closed do Turnstile + knobs de rate limit + pin do slowapi** — `2c7e728` (test — RED), `1897234` (feat — GREEN)
2. **task 2: resolver de IP proxy-aware (D-10) + testes unitários** — `0fe5f76` (test — RED), `d39734d` (feat — GREEN)

**TDD Gate Compliance:** task 1 RED (`2c7e728`) → GREEN (`1897234`); task 2 RED (`0fe5f76`) → GREEN (`d39734d`). Ambos os gates presentes e na ordem correta. Nenhum commit de REFACTOR foi necessário — a implementação do GREEN já saiu no formato final.

## Files Created/Modified
- `backend/app/core/config.py` — `DEV_TURNSTILE_SECRET`, `_TURNSTILE_TEST_KEY_RE`, 5 campos novos (TURNSTILE_*/REVEAL_RATE_LIMIT/LOGIN_RATE_LIMIT), `@model_validator(mode="after") _validate_turnstile` e a propriedade `effective_turnstile_secret` (T-03-01 mitigate)
- `backend/app/core/client_ip.py` — `UNKNOWN_IP`, `_is_public_ip`, `_rightmost_public_xff` e `resolve_client_ip` (T-03-02 mitigate)
- `backend/tests/test_security_config.py` — 9 testes: secret obrigatório fora de dev, chaves de teste rejeitadas (parametrizado 1x/2x/3x), secret real aceito, fallback de dev, defaults de rate limit e guarda de comprimento da chave always-pass
- `backend/tests/test_client_ip.py` — 7 testes da cadeia de resolução de IP, com helper `make_request` montando scope HTTP do Starlette
- `backend/.env.example` — seção `# --- Cloudflare Turnstile / Rate Limit (Phase 3) ---` com as 5 variáveis e o aviso do comportamento fail-closed (só placeholders, nenhum segredo real — T-03-02b mitigate)
- `backend/pyproject.toml` — `"slowapi==0.1.10"` em `[project].dependencies`
- `backend/uv.lock` — lock sincronizado com o novo pin (slowapi, limits, deprecated, wrapt)

## Decisions Made
- **X-Real-IP é validado por "parseia como IP", não por "é público"** — o `ipaddress` do Python marca `203.0.113.0/24` (TEST-NET-3), `198.51.100.0/24` e `192.0.2.0/24` como `is_private == True`; um filtro de "público" no X-Real-IP derrubaria o cabeçalho real do Railway e o caso cairia no XFF, contradizendo o D-10. O filtro de "público" fica restrito às entradas do XFF, exatamente como o D-10 especifica
- **A guarda de comprimento da chave always-pass virou teste** — além dos 6 casos pedidos, `test_dev_turnstile_secret_is_35_chars` fixa os 35 chars reais do segredo do Cloudflare; é a rede de proteção contra o erro de `{30}` no regex que o próprio plano apontou
- **16 testes em vez dos 13 estimados pelo plano** — a contagem do plano não expande o caso parametrizado (`1x`/`2x`/`3x` = 3 casos) nem conta a guarda de comprimento; nenhuma mudança de escopo
- **SECR-02 não foi marcado como concluído** — este plano entrega as primitivas (config, resolver de IP, pin do limiter), mas o requisito ("endpoint de revelação tem rate limiting por IP") só é satisfeito quando o plano 03-03 ligar o limiter ao endpoint; marcar agora criaria um sinal falso numa fase marcada HIGH RISK

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] `pip` não existe no venv — instalação via `uv pip`**
- **Found during:** task 1 (install de `slowapi==0.1.10`)
- **Issue:** o plano mandava `backend\.venv\Scripts\python.exe -m pip install "slowapi==0.1.10"`, mas o venv foi criado pelo `uv` e não tem o módulo `pip` (`No module named pip`) — o comando do plano falha
- **Fix:** instalado com `python -m uv pip install --python .\.venv\Scripts\python.exe "slowapi==0.1.10"` (mesmo resolvedor do projeto, mesma versão exata): `slowapi==0.1.10`, `limits==5.8.0`, `deprecated==1.3.1`, `wrapt==2.5.1`
- **Files modified:** nenhum arquivo do repo (apenas o venv)
- **Verification:** `import slowapi`/`from slowapi import Limiter` no interpretador do venv; suíte completa verde
- **Committed in:** 1897234 (task 1)

**2. [Rule 3 - Blocking] `uv.lock` regenerado apesar da instrução "não regenerar"**
- **Found during:** task 1 (pin de `slowapi`)
- **Issue:** o plano dizia para não regenerar o `uv.lock` porque o `uv` estaria ausente — mas o `uv` 0.13.1 **está** disponível via `python -m uv`, exatamente a via usada no plano 02-01. Deixar o lock dessincronizado com o `pyproject.toml` quebraria `uv sync` no próximo ambiente e apagaria o pin no lock
- **Fix:** `python -m uv lock` — diff puramente aditivo (149 linhas: slowapi, limits, deprecated, wrapt), **nenhuma** versão já travada foi alterada
- **Files modified:** backend/uv.lock
- **Verification:** `git diff --stat backend/uv.lock` → 149 insertions, 0 deletions; `uv lock` resolve 49 pacotes sem erro
- **Committed in:** 1897234 (task 1)

---

**Total deviations:** 2 auto-fixed (2 blocking)
**Impact on plan:** Nenhuma mudança de escopo de código. As duas correções foram de ferramenta: o comando de install do plano não existia no venv, e a lockfile precisava acompanhar o pin novo. O comportamento entregue segue exatamente o especificado.

## Issues Encountered
- A discrepância de 35 vs 32 chars no comprimento da chave de teste só apareceu ao rodar o código: `ipaddress`/regex não validam comprimento por conta própria, e o segredo always-pass do Cloudflare (`1x0000000000000000000000000000000AA`) tem 35 chars. O regex do plano (`{31}` + `AA` + prefixo de 2) está correto e foi mantido — com um teste de guarda para que a regressão não volte
- A instalação de `slowapi` exigiu descobrir que o `pip` não está no venv (criado pelo `uv`); a primeira tentativa do comando do plano falhou com `No module named pip` e foi substituída pela interface `uv pip`, sem efeito colateral no repositório

## User Setup Required
None - este plano não expõe nenhum endpoint e não exige serviço externo. A chave real do Cloudflare e o widget de produção continuam sendo tarefa da Phase 6 (já listada como deferred em `03-CONTEXT.md`); até lá, dev e CI usam a chave always-pass.

## Known Stubs
None. `effective_turnstile_secret` retorna string vazia quando o secret está ausente fora de dev, mas esse caminho é inalcançável: o `@model_validator` roda antes e impede a construção do `Settings` — é a guarantee do fail-closed (D-11), não um stub.

## Threat Flags
None — nenhuma superfície nova fora do threat register do plano. T-03-01 (secret ausente/de de teste) e T-03-02 (cadeia de IP) foram mitigados como especificado; T-03-02b (só placeholders no `.env.example`/`pyproject.toml`, nenhum segredo versionado) e T-03-02c (defaults folgados e ajustáveis por env, risco de CGNAT aceito por D-09) seguem inalterados. Nenhum endpoint, nenhuma chamada de rede, nenhuma mudança de schema neste plano.

## Next Phase Readiness
- O plano 03-02 pode consumir: `Settings.TURNSTILE_SECRET_KEY` (via `effective_turnstile_secret`), `TURNSTILE_SITE_KEY`, `TURNSTILE_TIMEOUT_SECONDS`, `REVEAL_RATE_LIMIT`, `LOGIN_RATE_LIMIT` e `resolve_client_ip(request)` como `key_func` do limiter slowapi (que já está instalado e pinado)
- O `slowapi` expõe `Limiter`, `RateLimitExceeded` (subclasse de `HTTPException`, com `.limit` e `.detail`) e `Limiter.reset()` — o que o plano 03-02 precisa para a fixture de reset entre testes
- Sem bloqueios. O conftest não define nenhuma das variáveis novas (decisão registrada no STATE.md) — os testes de fail-closed do plano 03-01 permanecem verdes sob `ENV=dev`

## Requirements
- **SECR-02** (rate limiting por IP no endpoint de revelação): **contribuído, não concluído** — este plano entrega o resolver de IP (D-10) e os knobs de limite (D-06); o requisito só passa a valer com o endpoint do plano 03-03 ligado ao limiter. Mantido desmarcado em `REQUIREMENTS.md` de propósito, para não gerar sinal falso numa fase HIGH RISK

---
*Phase: 03-contact-reveal-anti-spam*
*Completed: 2026-10-21*

## Self-Check: PASSED

- Todos os 7 arquivos-chave existem em disco (`app/core/config.py`, `app/core/client_ip.py`, `tests/test_security_config.py`, `tests/test_client_ip.py`, `.env.example`, `pyproject.toml`, `uv.lock`)
- Todos os 4 commits de task encontrados no histórico: `2c7e728`, `1897234`, `0fe5f76`, `d39734d`
- Verificação reexecutada: 120/120 testes passam (104 pré-existentes + 16 novos); grep gates do plano OK (`TURNSTILE_SECRET_KEY` em 4 linhas não-comentário ≥ 3; `def resolve_client_ip` == 1; `slowapi==0.1.10` == 1)
