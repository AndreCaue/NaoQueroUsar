---
phase: 03-contact-reveal-anti-spam
plan: 03
subsystem: api
tags: [turnstile, reveal-contact, rate-limit, slowapi, fastapi, pydantic, contact-privacy, publish-05, pytest, security]

# Dependency graph
requires:
  - phase: 01-backend-foundation-data-admin-auth
    provides: Job model com contact_email/contact_phone, get_published (published AND expires_at > now()), app factory + harness pytest
  - phase: 03-contact-reveal-anti-spam
    provides: (plano 03-01) resolve_client_ip + knobs REVEAL_RATE_LIMIT + pin do slowapi; (plano 03-02) TurnstileVerifier fail-closed, turnstile_error_detail(), seam get_turnstile_verifier, limiter por IP com 429 pt-BR
provides:
  - RevealRequest (cf_token) e ContactRevealResponse (job_id + contact_email + contact_phone) — os ÚNICOS schemas do projeto com campos de contato (PUBL-05)
  - POST /api/v1/public/jobs/{id}/reveal-contact: rate limit → 404 → Siteverify (action="reveal") → 200, com idempotency_key novo por submissão
  - Ordem D-03 materializada: a busca da vaga vem ANTES da chamada à Cloudflare (UUID falso não gasta cota)
  - Contrato de erro fixado para o front: 404 "Vaga não encontrada ou expirada." · 403 "Verificação anti-bot falhou — tente novamente" / "Verificação indisponível — tente novamente em instantes" · 429 + Retry-After · 422
  - Bucket do rate limit corrigido para (IP, rota) — antes era (IP, URL com o id da vaga), o que permitia bypass por rotação de ids
  - Suíte de 10 casos do reveal (200/404×3/403×3/422/429 + guarda de payload público sem contato), 100% offline
affects: [03-admin-login-turnstile, 04-frontend-reveal-ui, 06-deploy, frontend-reveal]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "contato só existe em schema de reveal: JobPublic/JobListResponse seguem sem campos de contato, garantido por teste (PUBL-05/T-03-09)"
    - "a checagem da vaga vem antes da chamada externa: UUID falso não consome cota da Cloudflare (D-03)"
    - "falha do Siteverify é sempre 403 — nunca 200 degradado — e a copy distingue 'desafio recusado' de 'verificação indisponível' (D-13)"
    - "o bucket do rate limit é (IP, rota), nunca (IP, URL): rota com id no path multiplicaria as janelas (D-05/D-08)"
    - "idempotency_key = uuid4() novo por submissão (retry com a mesma chave é do cliente)"
    - "TDD RED/GREEN por task, com o commit test(...) sempre precedendo o feat/fix(...)"

key-files:
  created:
    - backend/tests/test_reveal_api.py
  modified:
    - backend/app/schemas/job.py
    - backend/app/api/v1/public.py
    - backend/app/core/ratelimit.py
    - backend/tests/test_ratelimit.py

key-decisions:
  - "O contato volta cru (E.164) e o job_id acompanha a resposta: o Phase 4 monta wa.me/mailto e mantém o contato em memória do cliente por job_id (D-04), sem novo Turnstile ao reabrir a mesma vaga"
  - "O hostname do Siteverify NÃO é checado: ele muda entre localhost e produção e o binding por action já impede o reuso de token entre fluxos — está comentado na rota para o Phase 4 não inventar a checagem"
  - "get_published foi reutilizado como está (sem get_revealable paralelo): a proteção published AND expires_at > now() já é a do D-17"
  - "key_style do slowapi mudou de 'url' (default) para 'endpoint': com o id da vaga no path, cada vaga tinha a própria janela e um scraper podia rotacionar ids sem bater no limite nem na cota da Cloudflare (T-03-12/D-05/D-08)"
  - "O caso 9 da suíte foi reforçado com uma segunda vaga do MESMO IP: sem essa asserção, o bucket por URL passaria despercebido"

patterns-established:
  - "o arquivo de teste do reveal é lido na ordem das regras: 404 → 403 → 422 → 429 → 200, e o guard de payload público por último"
  - "nenhum teste do reveal fala com a rede: a seam get_turnstile_verifier (dependency_overrides) troca o cliente real pelo FakeTurnstileVerifier"
  - "knob de env nos testes: monkeypatch.setenv + get_settings.cache_clear() dentro de try/finally, para o default (10/minute) não vazar para o próximo teste"

requirements-completed: [SECR-01, SECR-02, PUBL-05]
requirements-contributed: []

# Metrics
duration: 17min
completed: 2026-10-22
---

# Phase 03 Plan 03: Endpoint de reveal do contato — Summary

**Endpoint único de saída do contato com Turnstile verificado no servidor, 404 antes do 403 e rate limit por IP de verdade — o portão anti-spam que materializa PUBL-05, SECR-01 e SECR-02.**

## Performance

- **Duration:** 17 min
- **Started:** 2026-10-22T00:33:36Z
- **Completed:** 2026-10-22T00:50:32Z
- **Tasks:** 2/2
- **Files modified:** 5 (1 criado, 4 modificados)

## Accomplishments
- `POST /api/v1/public/jobs/{id}/reveal-contact` — o **único** caminho pelo qual o contato sai do banco. A ordem das checagens é o contrato: rate limit → vaga (404) → Siteverify (403) → 200
- `RevealRequest` (`cf_token`, 1..2048 chars) e `ContactRevealResponse` (`job_id` + `contact_email` + `contact_phone`) em `schemas/job.py` — os únicos schemas do projeto com campos de contato; `JobPublic`/`JobListResponse` seguem intocados (OpenAPI confere: `JobPublic` não tem nenhum campo de contato)
- **404 antes de qualquer chamada externa** (D-03): UUID inexistente, vaga `pending` e vaga expirada respondem 404 sem gastar uma verificação da Cloudflare — provado pelos 3 casos de 404, que verificam `fake_turnstile.calls == []`
- **403 sempre, nunca 200 degradado** (D-13): "Verificação anti-bot falhou — tente novamente" (token recusado, replay, expirado) e "Verificação indisponível — tente novamente em instantes" (falha da própria verificação) — as duas copies vêm de `turnstile_error_detail()`, sem duplicação no router
- **Action binding**: `expected_action="reveal"` — um token mintado para `login` é recusado com `action-mismatch` (T-03-03); `idempotency_key` é um `uuid4()` novo a cada submissão (T-03-13)
- **Rate limit por IP de verdade**: o bucket do slowapi escopava pela URL (que carrega o id da vaga) — cada vaga tinha a própria janela e um scraper podia rotacionar ids sem nunca bater no limite. Corrigido para `(IP, rota)` via `key_style="endpoint"`, com guarda de regressão
- Suíte de **10 casos** em `backend/tests/test_reveal_api.py`, lida na ordem das regras, mais 1 guarda no `test_ratelimit.py`; suíte completa em **168 passed** (157 pré-existentes + 11 novos), 100% offline

## task Commits

Cada task foi commitada atomicamente, com o par RED/GREEN do TDD:

1. **task 1: schemas de reveal + rota POST /public/jobs/{id}/reveal-contact** — `e311fc8` (test — RED), `82c5138` (feat — GREEN)
2. **task 2: suíte do reveal (10 casos) — 200/404×3/403×3/422/429 + payload público sem contato** — `8dab85d` (test — RED), `870a31b` (fix — GREEN)

**TDD Gate Compliance:** task 1 RED (`e311fc8`) → GREEN (`82c5138`); task 2 RED (`8dab85d`) → GREEN (`870a31b`). Ambos os gates presentes e na ordem correta (um `test(...)` seguido de um `feat(...)`/`fix(...)`). Nenhum commit de REFACTOR foi necessário.

## Files Created/Modified
- `backend/app/schemas/job.py` — `RevealRequest` e `ContactRevealResponse` no fim do arquivo; docstring do módulo agora registra que estes são os únicos schemas com contato (T-03-09 mitigate)
- `backend/app/api/v1/public.py` — a rota `reveal_contact` (decoradores na ordem `@router.post` → `@limiter.limit(reveal_limit)`), com a checagem da vaga antes do verifier, o `remoteip` omitido quando o IP é `"unknown"` e o comentário explícito de que o `hostname` do Siteverify **não** é checado
- `backend/app/core/ratelimit.py` — `key_style="endpoint"` no `SafeLimiter` + docstring explicando por que o bucket é por rota e não por URL (T-03-12 mitigate)
- `backend/tests/test_ratelimit.py` — guarda de regressão `test_limiter_buckets_by_route_and_not_by_url`
- `backend/tests/test_reveal_api.py` — novo: os 10 casos do reveal, na ordem 404 → 403 → 422 → 429 → 200, com a guarda de payload público no fim

## Decisions Made
- **O `job_id` volta na resposta** — é o que permite ao Phase 4 manter o contato **em memória do cliente por `job_id`** (D-04): reabrir a mesma vaga mostra o contato direto, sem novo token (o token do reveal anterior é single-use e já foi consumido)
- **O telefone volta cru (E.164), sem `wa.me`/`mailto`** — decisão herdada da Fase 2 (o link é montado pelo front); o backend não inventa formatação de canal
- **`get_published` reutilizado como está** — o filtro `published AND expires_at > now()` já é exatamente o 404 do reveal (D-17); um `get_revealable` paralelo seria duplicação
- **`hostname` do Siteverify deliberadamente não checado** — varia entre localhost e produção, e o binding por `action` já impede o reuso de token entre fluxos; o comentário na rota avisa o Phase 4
- **O caso 9 da suíte foi além do roteiro do plano** — além do 3º POST dar 429, ele exige que **outra vaga do mesmo IP** também dê 429. Sem essa asserção o bucket por URL passaria despercebido e o SECR-02 ficaria verde-menta
- **SECR-01, SECR-02 e PUBL-05 foram marcados como concluídos** (ao contrário dos planos 03-01/03-02, que mantiveram desmarcado): com a rota no lugar, os três requisitos passam a valer de fato — a validação server-side, o limite por IP e o contato fora do payload público

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 2 - Missing Critical] O bucket do rate limit era por URL, não por IP — um scraper escapava do limite rotating ids**
- **Found during:** task 2 (RED da suíte — o caso 9 falhou com `404 != 429`)
- **Issue:** o slowapi 0.1.10 usa `key_style="url"` por padrão, e o escopo do bucket é o **caminho da requisição**. A rota de reveal carrega o id da vaga no path (`/api/v1/public/jobs/{uuid}/reveal-contact`), então cada vaga tinha a própria janela: o limite de 10/minute valia **por vaga**, não por visitante. Um scraper com a lista de vagas published giraria os ids e nunca bateria no limite — e cada tentativa pagaria uma verificação da Cloudflare (o DoS que T-03-12 promete fechar). O log do slowapi durante o teste confirma: `ratelimit 2 per 1 minute (127.0.0.1) exceeded at endpoint: /api/v1/public/jobs/3054bb62-.../reveal-contact`
- **Fix:** `key_style="endpoint"` no `SafeLimiter` → o escopo passa a ser o nome da função da rota e o bucket vira `(IP, rota)`: uma janela por visitante por rota, que é a leitura de D-05 ("chaveado pelo IP resolvido") e D-08 ("buckets separados por rota"). Docstring do módulo atualizada com o motivo
- **Files modified:** backend/app/core/ratelimit.py, backend/tests/test_ratelimit.py
- **Verification:** o caso 9 da suíte do reveal (3 POSTs → 429 + `Retry-After` + outra vaga do mesmo IP → 429) e a guarda `test_limiter_buckets_by_route_and_not_by_url`; os 12 testes pré-existentes de `test_ratelimit.py` seguem verdes
- **Committed in:** 870a31b (task 2 GREEN)

**2. [Rule 3 - Blocking] O comando de verificação do plano roda a partir da raiz e não encontra a config do pytest**
- **Found during:** task 1 (primeira execução de `backend\.venv\Scripts\python.exe -m pytest -q`)
- **Issue:** executado na raiz do repo, o pytest não encontra `backend/pyproject.toml` e, portanto, não lê `[tool.pytest.ini_options] asyncio_mode = "auto"` — o resultado é **157 errors** ("requested an async fixture 'reset_rate_limiter' with autouse=True, with no plugin or hook that handled it"), e não uma suíte verde. Executado dentro de `backend/`, a mesma suíte passa (157 passed)
- **Fix:** nenhum arquivo do repo foi alterado — a suíte é executada a partir de `backend/` (`cd backend; .venv\Scripts\python.exe -m pytest -q`), que é onde a config do projeto mora. Registrado no STATE.md para o plano 03-04 não perder tempo com o mesmo erro
- **Files modified:** nenhum
- **Verification:** suíte completa verde a partir de `backend/` (168 passed)
- **Committed in:** n/a (correção de ferramenta, sem mudança de código)

---

**Total deviations:** 2 auto-fixed (1 missing critical, 1 blocking)
**Impact on plan:** Nenhuma mudança de escopo de código. O desvio 1 endureceu uma mitigação que o próprio plano declarava (T-03-12/D-05) — o comportamento entregue é o que o plano pedia, agora de fato por IP. O desvio 2 foi só de comando de verificação.

## Issues Encountered
- **Gate de grep divergente (`turnstile_error_detail`):** o plano pede `grep -c "turnstile_error_detail" backend/app/api/v1/public.py == 1`, mas a implementação natural usa a string em **3** pontos — o `import`, a menção na docstring da rota (que explica de onde vem a copy) e a chamada. Gate mantido em 3: reduzir a 1 exigiria um alias de import que deixaria o código menos legível
- **Gate de grep divergente (`contact_email`):** o plano pede `grep -v "^#" ... | grep -c "contact_email" == 2` (1 no docstring do módulo + 1 no schema de reveal). O contador real é **3** porque o comentário pré-existente dentro de `JobPublic` (`# NO contact_email / contact_phone (D-18).`, da Fase 1) é indentado e não começa com `#` na coluna 0 — o filtro `^#` não o remove. A **intenção** do gate (nenhum campo de contato em `JobPublic`/`JobListResponse`) está satisfeita: o OpenAPI gerado confirma que `JobPublic` tem apenas `id, title, company, activities, requirements, salary, benefits, city, status, created_at, expires_at`
- **Ordem de leitura do arquivo de teste:** o roteiro do plano lista os casos na ordem 1..10 e ao mesmo tempo pede o caso 2 antes do caso 1 ("a ordem de leitura do arquivo = ordem das regras"). O arquivo final segue a **ordem das regras** (404 → 403 → 422 → 429 → 200, com o guard de payload público por último), o que satisfaz as duas instruções
- **Split RED/GREEN vs. tasks do plano:** o plano separa implementação (task 1) e testes (task 2), mas marca as duas como `tdd="true"`. A task 1 fez RED com os 2 casos que fixam o contrato da rota (404 sem chamar a Cloudflare e 200 com o contato) e GREEN com a implementação completa; a task 2 fez RED com os 8 casos restantes — **um deles genuinamente vermelho** (o caso 9, que expôs o bucket por URL) — e GREEN com a correção do limiter
- **Suíte lenta:** a suíte completa leva ~2-3 min (round-trips ao Postgres de teste); foi rodada 4 vezes (baseline, GREEN da task 1, RED+GREEN da task 2, verificação final)

## User Setup Required
None — este plano não exige serviço externo novo. A chave real do Cloudflare e o widget de produção continuam sendo tarefa da Phase 6 (já listada como deferred em `03-CONTEXT.md`); em dev e CI, a chave always-pass do Cloudflare é usada pelo default.

## Known Stubs
None. `RevealRequest`/`ContactRevealResponse` são contratos reais (não placeholders): `contact_email`/`contact_phone` são anuláveis porque o modelo permite contato só por e-mail ou só por telefone (CHECK `at_least_one_contact` da Fase 1). `FakeTurnstileVerifier` é um **test double** intencional (substitui o cliente real via `dependency_overrides`) — é o mecanismo do harness do plano 03-02, não um stub de produção.

## Threat Flags

| Flag | File | Description |
|------|------|-------------|
| threat_flag: rate-limit-bucket-granularity | backend/app/core/ratelimit.py | O bucket do slowapi escopava pela URL (com o id da vaga) e não pelo IP — mitigação T-03-12 mais fraca do que o plano descrevia. Corrigido com `key_style="endpoint"` + guarda de regressão |

Nenhuma superfície nova fora do threat register do plano: a rota de reveal é exatamente o componente coberto por T-03-09 (contato só no schema de reveal), T-03-10 (action binding), T-03-11 (404 antes do 403), T-03-12 (rate limit + busca antes do Siteverify), T-03-13 (idempotency_key novo) e T-03-14 (error-codes no log + 429 com Retry-After). Todos com disposição `mitigate` implementada e coberta por teste.

## Next Phase Readiness
- **Plano 03-04** pode consumir: `RevealRequest`/`ContactRevealResponse` (o contrato do reveal), `turnstile_error_detail()` (copy pt-BR — não duplicar), `limiter` + `login_limit()` e a mesma seam `get_turnstile_verifier`
- **Phase 4** (UI do reveal) implementa contra este contrato: `POST /api/v1/public/jobs/{id}/reveal-contact` com body `{"cf_token": "<token>"}`; 200 → `{job_id, contact_email, contact_phone}` (telefone cru em E.164; `wa.me`/`mailto` montados no front); 403 → duas copies distintas; 404 → "Vaga não encontrada ou expirada."; 429 → `body.detail` + header `Retry-After`. O widget vai com `appearance="interaction-only"` e `action="reveal"` (D-01) — o backend já exige esse `action`
- O `job_id` da resposta é o que permite o cache **em memória do cliente por vaga** (D-04): o Phase 4 não deve pedir token de novo ao reabrir a mesma vaga
- Contrato de nomes respeitado integralmente (`RevealRequest`, `ContactRevealResponse`, `reveal_limit`, `turnstile_error_detail`, `get_turnstile_verifier`, `UNKNOWN_IP`, `resolve_client_ip`)
- Sem bloqueios. A suíte roda a partir de `backend/` (ver "Issues Encountered")

## Requirements
- **SECR-01** (Turnstile validado no servidor antes de revelar o contato): **concluído** — `await verifier.verify(...)` com `expected_action="reveal"` roda antes de qualquer linha de contato ser montada; falha do Siteverify é sempre 403 (D-13)
- **SECR-02** (rate limiting por IP no endpoint de revelação): **concluído** — `@limiter.limit(reveal_limit)` com bucket `(IP, rota)` e 429 pt-BR + `Retry-After` (D-05/D-06/D-08/D-10)
- **PUBL-05** (contato servido por endpoint dedicado e ausente do payload público): **concluído** — rota dedicada + `JobPublic`/`JobListResponse` sem campos de contato, garantido pelo caso 10 e pelo OpenAPI
- **SECR-03** (Turnstile no login do admin): permanece **Pending** — é o plano 03-04

---
*Phase: 03-contact-reveal-anti-spam*
*Completed: 2026-10-22*

## Self-Check: PASSED

- Todos os 5 arquivos-chave existem em disco (`app/schemas/job.py`, `app/api/v1/public.py`, `app/core/ratelimit.py`, `tests/test_reveal_api.py`, `tests/test_ratelimit.py`)
- Todos os 4 commits de task encontrados no histórico: `e311fc8`, `82c5138`, `8dab85d`, `870a31b`
- Verificação reexecutada: suíte completa **168 passed** (157 pré-existentes + 11 novos), `tests/test_reveal_api.py` 10 passed, `tests/test_ratelimit.py` 12 passed
- Grep gates: `class ContactRevealResponse` = 1 ✅ · `reveal-contact` = 1 ✅ · `@limiter.limit(reveal_limit)` = 1 ✅ · `turnstile_error_detail` = 3 (gate do plano diz 1 — ver "Issues Encountered") · `contact_email` = 3 (gate do plano diz 2 — ver "Issues Encountered")
- OpenAPI confere: `POST /api/v1/public/jobs/{job_id}/reveal-contact` registrado, `JobPublic` sem nenhum campo de contato
- Nenhum arquivo pré-existente alheio ao plano foi staged ou commitado (`frontend/tsconfig.json` e os scratch files `backend/_*.txt`, `backend/body.json`, `frontend/next-env.d.ts`, `frontend/package-lock.json` seguem intactos na working tree)
