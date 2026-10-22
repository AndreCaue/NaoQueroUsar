---
phase: 03-contact-reveal-anti-spam
plan: 05
subsystem: testing
tags: [turnstile, cloudflare, siteverify, live-test, opt-in, pytest, env-local, leak-scan, checkpoint, browser]

# Dependency graph
requires:
  - phase: 03-contact-reveal-anti-spam
    provides: (plano 03-02) TurnstileVerifier fail-closed com action binding + seam get_turnstile_verifier; (plano 03-04) login do master com Siteverify(action="login") e widget next-turnstile
  - phase: 01-backend-foundation-data-admin-auth
    provides: harness pytest (asyncio_mode=auto) e Settings base (env_file + init kwargs)
provides:
  - backend/tests/test_turnstile_live.py — smoke test opt-in do Siteverify REAL (TURNSTILE_LIVE=1) com os 3 segredos públicos de teste da Cloudflare
  - backend/.env local com TURNSTILE_SECRET_KEY/TURNSTILE_SITE_KEY de teste (gitignored, nunca versionado)
  - frontend/.env.local com NEXT_PUBLIC_API_URL e NEXT_PUBLIC_TURNSTILE_SITE_KEY de teste (gitignored, nunca versionado)
  - Harness de teste isolado do .env local do dev (as duas chaves do Turnstile fixadas em "")
  - Varredura de vazamento de segredo com 0 hits no front e a chave always-pass só em app/core/config.py
  - Ambiente de verificação de pé (backend :8000, frontend :3000) para o checkpoint do browser
affects: [04-frontend-reveal-ui, 06-deploy, phase-03-closure]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "smoke test de terceiro é opt-in por env (TURNSTILE_LIVE=1): a suíte normal continua 100% offline e não consome cota da Cloudflare (T-03-23)"
    - "a chave pública de teste da Cloudflare é valor de teste, não credencial — a varredura de vazamento é sobre o segredo REAL, não sobre 1x/2x/3x"
    - "a suíte nunca herda o .env local do dev: as chaves do Turnstile são fixadas em '' no conftest, como as demais segredos de runtime"

key-files:
  created:
    - backend/tests/test_turnstile_live.py
  modified:
    - backend/tests/conftest.py
  untracked-by-design:
    - backend/.env
    - frontend/.env.local

key-decisions:
  - "O smoke test importa apenas app.services.turnstile: ele não monta o app, não toca no banco e não altera estado global — pode rodar contra a internet sem arrastar o harness"
  - "Timeout de 20s no live test (contra o default de 10s do serviço): a chamada sai para a internet e um round-trip lento não pode ser confundido com uma falha do anti-spam"
  - "A correção do /health foi no conftest (pin das chaves em ''), não no teste: o harness já fixa DATABASE_URL/ADMIN_PASSWORD_HASH/JWT_SECRET pelo mesmo motivo, e o teste do 03-02 afirmava um valor que dependia da máquina"
  - "task 2 não produziu artefato versionado — por design: os dois arquivos do plano são gitignored; o único commit da task é a correção do harness"
  - "O action binding incompatível com os segredos de teste da Cloudflare NÃO foi corrigido automaticamente: ele toca o portão de anti-spam (T-03-03/T-03-16) e o próprio plano 03-05 manda reportar o sintoma sem consertar nada sem o veredito do usuário"

patterns-established:
  - "prova de integração real de um terceiro = suíte opt-in separada, não um mock mais sofisticado"
  - "teste de health/configuração afirma invariantes, nunca o estado local da máquina do dev"

requirements-completed: [SECR-01, SECR-03]

# Metrics
duration: 27min
completed: pending — checkpoint de browser aberto (task 3)
---

# Phase 03 Plan 05: Prova real do Siteverify, regressão completa e checkpoint do browser — Summary

**Uma chamada real à API da Cloudflare provada com os três segredos públicos de teste (o portão abre, o portão fecha, e a falha fecha *fechado* com erro explicável), o ambiente local com as chaves de teste, a suíte e o build verdes — e a descoberta de que os segredos de teste da Cloudflare não devolvem o campo `action`, o que fecha o login contra eles.**

## Performance

- **Duration:** 27 min (tasks 1 e 2 + preparação do checkpoint)
- **Started:** 2026-10-22T01:28:00Z
- **Completed:** 2026-10-22T01:55:00Z
- **Tasks:** 2/3 (task 3 = checkpoint de browser, aguardando o veredito do usuário)
- **Files modified:** 3 (1 novo versionado, 1 modificado, 2 `.env` locais por design)

## Accomplishments
- `backend/tests/test_turnstile_live.py` fala **de verdade** com `https://challenges.cloudflare.com/turnstile/v0/siteverify`: com `TURNSTILE_LIVE=1` os 3 casos ficam verdes em ~1,4s, e **sem** a env var o arquivo inteiro aparece como *skipped* (3 skipped) — a suíte normal segue offline e sem cota
- Comportamento **observado** na API real (não presumido): `1x…` → `success=true, error-codes=[]`; `2x…` → `success=false, error-codes=["invalid-input-response"]`; `3x…` → `success=false, error-codes=["timeout-or-duplicate"]`. O segredo always-error prova o fail-closed (D-13) com `error_codes` **não vazio** — a falha é explicável, não um "pode passar" silencioso
- `backend/.env` e `frontend/.env.local` agora carregam as chaves de teste da Cloudflare — **ambos continuam untracked** (`git check-ignore`: `.gitignore:1` e `frontend/.gitignore:3`; `git status --porcelain` não lista nenhum dos dois — T-03-21 mitigado)
- Regressão completa do backend **verde**: 175 passed + 3 skipped (os live) + 1 warning pré-existente do SQLAlchemy; `npm run build` do frontend → `✓ Compiled successfully` (5,9s) com lint e type-check dentro do build
- Varredura de vazamento com os contadores esperados: `TURNSTILE_SECRET_KEY` no front versionado → **0 hits**; `TURNSTILE_SECRET` no front versionado → **0 hits**; a chave always-pass em `backend/app/` → **só `backend/app/core/config.py`**. O bundle do front inlina a **site** key (que é pública por definição) e **nenhum** segredo (0 hits em `.next/static`)
- Ambiente de verificação de pé para o checkpoint: backend em `http://localhost:8000` (uvicorn, boot sem erro de validação de env — o D-11/D-12 aceitou a chave de teste em dev), frontend em `http://localhost:3000` (Next 15.5.3, `.env.local` carregado). `GET /api/v1/health` → `{"configured": true, "mode": "test", "site_key_configured": true}`; `GET /admin/paste` → 200 com o formulário de login e a site key inlinada no chunk
- **Descoberta real (o achado do plano):** os segredos de teste da Cloudflare **não devolvem o campo `action`** na resposta do Siteverify. O login e o reveal amarram `expected_action` (`"login"` / `"reveal"`), então com a chave de teste o token é recusado com `action-mismatch` → **403 "Verificação anti-bot falhou — tente novamente"**. Reproduzido programaticamente contra o backend no ar: `POST /api/v1/auth/login` com um token de dummy → `403` (e **não** 401 "Senha inválida"), ou seja, a chamada real à Cloudflare acontece e o portão fecha — mas fecha também no caminho feliz de dev

## task Commits

Cada task foi commitada atomicamente:

1. **task 1: smoke test real do Siteverify (opt-in por TURNSTILE_LIVE=1)** — `dcf31f3` (test)
2. **task 2: env local com as chaves de teste + regressão completa + varredura de vazamento** — `c09d2e1` (fix — desvio 1 abaixo; a task em si não produz arquivo versionado, por design)
3. **task 3: checkpoint — login real no browser** — **sem commit**: checkpoint de human-verify aguardando o usuário (a infra do checkpoint — os dois servidores — já está de pé)

**TDD Gate Compliance:** a task 1 entrega **o próprio artefato de teste** — não existe código de produção a implementar (o `TurnstileVerifier` sob teste veio pronto no plano 03-02), então o par RED/GREEN colapsa em um único commit `test(...)`. O "RED" real do arquivo é contra a API da Cloudflare, não contra um fake: antes dele nada no repositório provava que o round-trip existia. A task 2 não tem artefato de código (dois `.env` gitignored) e a task 3 é checkpoint.

## Files Created/Modified
- `backend/tests/test_turnstile_live.py` — novo: smoke test opt-in do Siteverify real. 3 testes `async def` (always-pass / always-fail / always-error), `pytestmark = pytest.mark.skipif(os.environ.get("TURNSTILE_LIVE") != "1", ...)`, timeout de 20s, import **apenas** de `app.services.turnstile` (nada de app, nada de banco)
- `backend/tests/conftest.py` — modificado: as duas chaves do Turnstile fixadas em `""` no ambiente do pytest (`TURNSTILE_SECRET_KEY`, `TURNSTILE_SITE_KEY`), com o docstring do harness atualizado para explicar o porquê
- `backend/.env` — **não versionado**: `TURNSTILE_SECRET_KEY` e `TURNSTILE_SITE_KEY` com os valores públicos de teste da Cloudflare (o conteúdo do arquivo não é reproduzido aqui)
- `frontend/.env.local` — **não versionado**: `NEXT_PUBLIC_API_URL=http://localhost:8000` e `NEXT_PUBLIC_TURNSTILE_SITE_KEY` com a site key pública de teste

## Decisions Made
- **O smoke test live é separado e opt-in, não um mock melhorado** — o `FakeTurnstileVerifier` continua no lugar para a suíte do dia a dia (offline, determinística, sem cota); a prova de que a integração existe mora em um arquivo que só roda com `TURNSTILE_LIVE=1`. Isso é o que T-03-23 pede
- **A correção do `/health` foi no harness, não no teste** — `tests/test_health.py` afirmava `site_key_configured is False`, o que só valia na máquina de quem não tivesse site key no `.env`. O harness já fixa `DATABASE_URL`/`ADMIN_PASSWORD_HASH`/`JWT_SECRET` exatamente para não depender da máquina; as duas chaves do Turnstile entraram no mesmo grupo. O teste do 03-02 continua intacto (e a semântica dele — "sem site key → false" — é a que o harness passa a garantir)
- **Timeout de 20s só no live test** — o default de 10s do serviço é adequado para produção (D-04/T-03-04); contra a internet pública um round-trip lento não pode virar falso negativo
- **A chave always-pass aparece no `backend/app/core/config.py` e é o único lugar** — ela é o fallback de dev do `Settings` (03-01) e o padrão de teste do próprio harness. As ocorrências em `tests/` e nos `.planning/` são valores públicos de teste, não credenciais; o segredo **real** não existe em lugar nenhum do repositório
- **O action binding incompatível com os segredos de teste NÃO foi corrigido automaticamente** — a correção mexeria no portão de anti-spam (T-03-03/T-03-16, disposições `mitigate` do plano) e o próprio plano 03-05 diz: *"Não 'consertar' nada sem o veredito do usuário: se algo falhar, registrar o sintoma exato e voltar ao usuário"*. O achado está medido, reproduzido e a correção proposta está no checkpoint
- **SECR-01 e SECR-03 seguem concluídos** (fechados no 03-03 e no 03-04) — este plano não os reabre nem os altera; ele entrega a **prova** de que valem contra a API real (task 1) e o sintoma que impede o prova de browser (task 3)

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] A suíte herdava o `.env` local do dev e o teste do `/health` do 03-02 quebrou**
- **Found during:** task 2 (regressão completa — `test_health_reports_the_turnstile_status` falhou)
- **Issue:** o plano exige que `backend/.env` passe a ter `TURNSTILE_SITE_KEY`; como o `Settings` lê `env_file=".env"`, a variável **vazou para dentro da suíte** e o `/health` passou a reportar `site_key_configured: true` — quebrando a asserção `is False` escrita no plano 03-02. O teste era, na verdade, dependente do estado da máquina do dev: passava só porque o `.env` ainda não tinha site key
- **Fix:** as duas chaves do Turnstile foram fixadas em `""` no `os.environ` do `conftest.py`, ao lado das outras segredos de runtime que o harness já pinava. Com o secret vazio, `effective_turnstile_secret` cai na chave always-pass de dev (o mesmo valor de antes) e `site_key_configured` volta a ser `false` — o `test_health.py` do 03-02 foi **deixado intacto**
- **Files modified:** backend/tests/conftest.py
- **Verification:** suíte completa **175 passed + 3 skipped**; `tests/test_health.py` 3 passed; `npm run build` verde
- **Committed in:** `c09d2e1` (task 2)

**2. [Rule 3 - Blocking] O checkpoint do plano pedia que o usuário subisse os servidores — quem sobe é o executor**
- **Found during:** task 3 (preparação do ambiente de verificação)
- **Issue:** o `<action>` da task 3 manda o usuário abrir dois terminais e subir backend e frontend. A regra de checkpoints do GSD é o contrário: *"If OpenCode can run it, OpenCode runs it — never ask the user to execute CLI commands, start servers, or run builds"*, e um checkpoint nunca pode ser apresentado com o ambiente quebrado
- **Fix:** o backend (`uvicorn app.main:app --port 8000`) e o frontend (`npm run dev`) foram iniciados pelo executor e validados programaticamente: `/api/v1/health` → 200 com o bloco `turnstile`, `/admin/paste` → 200 com o formulário, e o chunk servido (`/_next/static/chunks/app/admin/paste/page.js`) com a site key inlinada. O usuário só precisa abrir o browser
- **Files modified:** nenhum (nenhum arquivo do repo)
- **Verification:** portas 8000 e 3000 em escuta; `health` e `/admin/paste` respondendo 200; chunk do front com a site key
- **Committed in:** n/a (preparação de ambiente, sem mudança de código)

---

**Total deviations:** 2 auto-fixed (2 blocking)
**Impact on plan:** Nenhuma mudança de escopo de código de produção. O desvio 1 corrigiu uma dependência latente da suíte em relação à máquina do dev (e era exigido pelo próprio `<acceptance_criteria>` da task 2, que pede `.env` com site key **e** suíte verde ao mesmo tempo); o desvio 2 é só de automação do checkpoint. O único arquivo versionado além do previsto no plano é `backend/tests/conftest.py`, commitado à parte porque a task 2 exige a suíte verde.

## Issues Encountered
- **O achado do plano — os segredos de teste da Cloudflare não devolvem `action`.** Medido contra a API real: `POST /siteverify` com `1x…` devolve `{"success": true, "error-codes": [], "hostname": "example.com", "metadata": {"result_with_testing_key": true}}` — **sem o campo `action`**, tanto com um token qualquer quanto com o token dummy canônico (`XXXX.DUMMY.TOKEN.XXXX`). Como o `TurnstileVerifier` compara `action != expected_action`, o token vira `action-mismatch` → `success=False` → **403**. O mesmo vale para o reveal (`expected_action="reveal"`). Ou seja: **com as chaves de teste o portão está fechado para o caminho feliz** — o comportamento fail-closed está correto (é o que o D-13 quer), mas o dev local não consegue atravessar os dois fluxos protegidos, e o passo 5 do checkpoint (login com a senha certa) vai mostrar 403 em vez do painel "Extrair vagas". O sintoma exato, medido: `POST /api/v1/auth/login` com `{"password": "...", "cf_token": "XXXX.DUMMY.TOKEN.XXXX"}` → **403 `{"detail": "Verificação anti-bot falhou — tente novamente"}`** — e **não** 401 "Senha inválida", o que prova que a chamada real à Cloudflare está acontecendo e que a falha está no binding, não na senha
- **Correção proposta (aguardando o veredito do usuário):** o binding de `action` só deve ser exigido quando a resposta **tiver** `action`. A análise de segurança mostra que isso **não abre brecha em produção**: com chave real, o nosso widget sempre manda `action` (`"login"` no login, `"reveal"` no reveal), então um token "sem action" só existe no modo de teste da Cloudflare — e o `Settings` já recusa chaves `1x/2x/3x` fora de `ENV=dev` (D-12). Alternativa mais conservadora: o `TurnstileVerifier` recebe um flag `enforce_action` que o `get_turnstile_verifier()` desliga quando `settings.turnstile_mode == "test"` (o modo já existe no `Settings` desde o 03-02). **Nenhuma das duas foi aplicada neste plano** — ambas mexem no portão de anti-spam
- **A suíte inteira é pulada sem `TEST_DATABASE_URL`** — o `pytest_collection_modifyitems` do `conftest.py` marca *todos* os itens com skip quando não há banco configurado, inclusive o live test, que não precisa de banco. Não foi mexido: é o comportamento global do harness (T-03-08) e o live test é opt-in por definição
- **Os gates de grep do plano precisam de `git grep`** — o `Select-String` do PowerShell 5.1 não tem `-Recurse`; usei `git grep` (que só enxerga arquivo versionado, que é exatamente o escopo do gate: "nenhum arquivo **versionado** do frontend")
- **A suíte é lenta (~3 min por rodada)** — round-trips ao Postgres de teste (Neon); foram 2 rodadas completas (uma com a falha do `/health`, outra verde) + o build do front
- **O `npm run dev` reclamou de múltiplos lockfiles** ("Next.js inferred your workspace root") — é o aviso pré-existente do Next 15.5.3 já registrado em `deferred-items.md` (D-3); não afeta o build nem o checkpoint
- **Warnings pré-existentes, não tocados:** 1 `SAWarning` do SQLAlchemy em `test_extract_commit_failure_rolls_back_no_rows` e as 8 vulnerabilidades do `npm audit` (todas em `next@15.5.3`, já em `deferred-items.md` D-1)

## User Setup Required
Nenhum passo novo de código. O `.env` local e o `.env.local` local já foram configurados pelo executor com as chaves públicas de teste da Cloudflare (nunca versionadas). A **chave real** do Cloudflare (site key + secret) continua sendo tarefa da Phase 6, como já estava registrado no `03-CONTEXT.md` — até lá, dev e CI usam a always-pass.

## Known Stubs
Nenhum. `test_turnstile_live.py` é um **test double do lado do teste** de propósito — ele é a prova de que o cliente real funciona, não um stub de produção. Os valores `1x…/2x…/3x…` são chaves públicas de teste documentadas pela Cloudflare, não credenciais. O `site_key_configured: true` que o `/health` mostra em dev é o estado real do `.env` local, não um placeholder.

## Threat Flags

| Flag | File | Description |
|------|------|-------------|
| threat_flag: dev-fallback-secret-opens-the-gate | backend/app/core/config.py | `effective_turnstile_secret` cai na chave always-pass quando `ENV=dev` e não há secret configurado. O D-12 recusa chaves de teste fora de dev, mas um deploy com `ENV=dev` **e** chave de teste teria o anti-spam aberto (a Cloudflare aprova tudo). O `/health` expõe `mode` (`live`/`test`/`disabled`) justamente para o master conferir antes de abrir o site |
| threat_flag: action-binding-inexercitavel-em-dev | backend/app/services/turnstile.py | Com os segredos de teste da Cloudflare o campo `action` não vem na resposta, então o binding `expected_action` rejeita **todo** token — o login e o reveal ficam fechados em dev. Não é uma brecha (o portão fecha), mas é um obstáculo para exercitar os fluxos e para o checkpoint de browser; a correção proposta está no checkpoint, aguardando veredito |
| threat_flag: build-time-site-key-inlining | frontend/app/admin/paste/ExtractForm.tsx | Herdado do 03-04: a site key é inlinada no bundle no build — trocar a chave no painel da Cloudflare depois do build não atualiza o widget |

Nenhuma superfície nova fora do threat register do plano: T-03-21 (segredo fora do versionamento) foi mitigado — `backend/.env` e `frontend/.env.local` permanecem untracked e a varredura no front versionado deu 0 hits; T-03-23 (o smoke live é opt-in) foi mitigado — sem `TURNSTILE_LIVE=1` o arquivo é *skipped*; T-03-24 (timeout-or-duplicate tratado como sucesso) foi mitigado — o segredo `3x…` prova que a falha fecha **fechado** e vem com `error_codes` não vazio.

## Next Phase Readiness
- **O que falta para a fase fechar:** o veredito do usuário no checkpoint de browser (task 3). O sintoma já está medido e reportado; a correção do binding está proposta
- **Plano 04 (frontend do reveal)** pode consumir: a rota `POST /api/v1/public/jobs/{id}/reveal-contact` com o contrato real (200 com o contato, 403 com a copy anti-bot, 404 para vaga inexistente, 429 + `Retry-After`), o widget `next-turnstile` (que precisa de `id` distinto do widget do login quando os dois coexistirem) e a certeza de que o `cf_token` do reveal precisa de um widget com `action="reveal"`
- **Phase 6** continua com: chave real do Cloudflare (site key + secret), o warning de startup previsto no D-14 e o bump do Next (D-1)
- Contrato de nomes respeitado integralmente (`TurnstileVerifier`, `TurnstileResult`, `error_codes`, `SITEVERIFY_URL`, `TURNSTILE_LIVE`)
- Sem bloqueios de infraestrutura: os dois servidores estão de pé para o checkpoint

## Requirements
- **SECR-01** (Turnstile validado no servidor antes de revelar o contato): **concluído** (fechado no 03-03) — este plano adiciona a **prova real**: o segredo `1x…` faz uma chamada HTTP de verdade ao Siteverify e volta com `success=true`; os segredos `2x…` e `3x…` provam que a recusa e a indisponibilidade fecham o portão
- **SECR-03** (Turnstile protege o login do admin): **concluído** (fechado no 03-04) — o mesmo smoke test cobre o cliente usado pelo login; o que ficou pendente é a **prova de browser**, e ela esbarrou no achado do `action` (não no mecanismo)
- **SECR-02** e **PUBL-05** permanecem como estão (fechados no 03-03) — este plano não os altera

---
*Phase: 03-contact-reveal-anti-spam*
*Completed: 2026-10-22 (tasks 1 e 2; task 3 = checkpoint de browser aberto)*

## Self-Check: PASSED

- Arquivos-chave existem no disco: `backend/tests/test_turnstile_live.py` ✓ · `backend/tests/conftest.py` ✓ · `backend/.env` (untracked) ✓ · `frontend/.env.local` (untracked) ✓ · este SUMMARY ✓
- Commits de task no histórico: `dcf31f3` (task 1), `c09d2e1` (task 2 / desvio 1) ✓ — nenhum arquivo pré-existente alheio ao plano foi staged (`frontend/tsconfig.json` e os scratch files `backend/_*.txt`, `backend/body.json`, `frontend/next-env.d.ts`, `frontend/package-lock.json` seguem intactos na working tree)
- Verificação re-executada: `TURNSTILE_LIVE=1 pytest tests/test_turnstile_live.py -q` → **3 passed**; sem a env var → **3 skipped**; suíte completa → **175 passed, 3 skipped**; `npm run build` → **✓ Compiled successfully**
- Grep gates: `TURNSTILE_SECRET_KEY` no front versionado = **0** ✅ · `TURNSTILE_SECRET` no front versionado = **0** ✅ · chave always-pass em `backend/app/` = **só `app/core/config.py`** ✅ · segredo no bundle do front (`.next/static`) = **0** ✅
- `git status --porcelain` **não** lista `backend/.env` nem `frontend/.env.local` (ambos com regra de ignore ativa) ✅
- Task 3 **não** está marcada como concluída neste SUMMARY — o plano segue **2/3**, com o checkpoint de browser aberto
