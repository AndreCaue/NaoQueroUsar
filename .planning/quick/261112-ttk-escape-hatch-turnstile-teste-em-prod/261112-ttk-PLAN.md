---
phase: 261112-ttk
plan: 01
type: execute
wave: 1
depends_on: []
files_modified:
  - backend/app/core/config.py
  - backend/app/api/v1/health.py
  - backend/tests/test_security_config.py
  - backend/tests/test_health.py
  - scripts/verify-deploy.ps1
  - render.yaml
  - docs/DEPLOY.md
  - .planning/STATE.md
autonomous: true
requirements: []   # quick task — desvio temporário pedido pelo usuário
user_setup:
  - service: render
    why: "Sem ALLOW_TEST_TURNSTILE=true no dashboard o boot continua recusando a chave de teste (fail-closed)."
    env_vars:
      - name: ALLOW_TEST_TURNSTILE
        source: "Dashboard → Environment → ALLOW_TEST_TURNSTILE = true"
      - name: ENV
        source: "prod (já no blueprint)"
      - name: CORS_ORIGINS
        source: "https://nao-quero-usar.vercel.app (sem barra final)"

must_haves:
  truths:
    - "ENV=prod + chave de teste do Cloudflare só sobe com ALLOW_TEST_TURNSTILE=true explícito; sem o flag o boot continua sendo recusado (D-12 preservada)"
    - "TURNSTILE_SECRET_KEY vazia continua derrubando o boot fora de dev (D-11 não relaxada)"
    - "/health reporta turnstile.mode=test e turnstile.test_override=true, sem revelar o segredo"
    - "O gate só aceita mode=test quando rodado com -AllowTestTurnstile E o health declara test_override=true"
    - "Com chaves live o comportamento antigo permanece: mode=live, gate verde sem switch"
  artifacts:
    - path: "backend/app/core/config.py"
      provides: "flag ALLOW_TEST_TURNSTILE (default false) + WARN de boot"
      contains: "ALLOW_TEST_TURNSTILE: bool = False"
    - path: "backend/app/api/v1/health.py"
      provides: "campo aditivo turnstile.test_override"
      contains: "test_override"
    - path: "scripts/verify-deploy.ps1"
      provides: "switch -AllowTestTurnstile com WARN no check 1"
      contains: "AllowTestTurnstile"
    - path: "render.yaml"
      provides: "env var do flag com sync: false"
      contains: "ALLOW_TEST_TURNSTILE"
    - path: "docs/DEPLOY.md"
      provides: "seção do desvio temporário + como sair dele"
      contains: "Desvio temporário"
  key_links:
    - from: "backend/app/core/config.py"
      to: "backend/app/api/v1/health.py"
      via: "settings.ALLOW_TEST_TURNSTILE"
      pattern: "test_override"
    - from: "scripts/verify-deploy.ps1"
      to: "GET /api/v1/health"
      via: "turnstile.test_override=true"
      pattern: "test_override"
---

<objective>
Destravar o boot do Render que hoje falha porque `ENV=prod` + chave de **teste** do Cloudflare Turnstile viola o validador fail-closed (`ValueError` em `Settings`, D-12), permitindo um **desvio temporário explícito** enquanto o operador não tem domínio próprio nem widget live.

Purpose: o usuário pediu para "desativar essa trava temporariamente". Em vez de remover a validação (o que deixaria qualquer deploy futuro aceitar chave de teste sem ninguém perceber), adiciona-se um opt-in `ALLOW_TEST_TURNSTILE=false` por padrão: fail-closed continua sendo o comportamento normal, e o desvio fica visível no boot (WARN) e no `/health` (`test_override=true`).

Output: código + testes + gate + blueprint + runbook documentando o desvio e o caminho de saída (chaves live com hostname da Vercel, sem domínio próprio).
</objective>

<tasks>

<task type="auto">
  <name>Task 1: Escape hatch explícito no Settings</name>
  <files>backend/app/core/config.py</files>
  <action>
    Adicionar `ALLOW_TEST_TURNSTILE: bool = False`. Em `_validate_turnstile`, manter a recusa de chave de teste fora de dev, exceto quando o flag for `True`; nesse caso emitir `logger.warning` destacando que é desvio temporário e que qualquer token é aceito. Não relaxar a exigência de `TURNSTILE_SECRET_KEY` (D-11).
  </action>
  <verify>`Settings(ENV="prod", TURNSTILE_SECRET_KEY="1x...AA")` levanta `ValidationError`; com `ALLOW_TEST_TURNSTILE=True` constrói e `turnstile_mode == "test"`.</verify>
  <done>Flag disponível, default fail-closed, WARN no boot.</done>
</task>

<task type="auto">
  <name>Task 2: Observabilidade no /health</name>
  <files>backend/app/api/v1/health.py</files>
  <action>
    Adicionar `turnstile.test_override` (bool) ao contrato. Campo aditivo; nenhum campo existente muda e o segredo continua fora da resposta.
  </action>
  <verify>`GET /api/v1/health` em dev retorna `test_override: false` e continua sem vazar a chave.</verify>
  <done>Contrato aditivo publicado.</done>
</task>

<task type="auto">
  <name>Task 3: Testes de config e health</name>
  <files>backend/tests/test_security_config.py, backend/tests/test_health.py</files>
  <action>
    Cobrir: prod + chave de teste sem flag → erro; com flag → boota, modo `test` e WARN emitido; prod + flag + segredo vazio → erro D-11; prod + flag + segredo real → `live`. Em `test_health`, garantir `test_override` presente e `false` por padrão.
  </action>
  <verify>`.venv\Scripts\python.exe -m pytest tests/test_security_config.py tests/test_health.py -q` verde.</verify>
  <done>Testes acrescentados e suíte verde.</done>
</task>

<task type="auto">
  <name>Task 4: Gate de produção com opt-in</name>
  <files>scripts/verify-deploy.ps1</files>
  <action>
    Adicionar `-AllowTestTurnstile`. No check 1: `mode=live` → `PASS`; `mode=test` + switch + `test_override=true` → `WARN` explícito; qualquer outro caso → `throw`. Manter os demais checks inalterados e o arquivo em UTF-8 com BOM.
  </action>
  <verify>Parser do PowerShell sem erros; bytes começam com `EF BB BF`; sem o switch o comportamento antigo é preservado.</verify>
  <done>Gate aceita o desvio apenas de forma explícita e auditável.</done>
</task>

<task type="auto">
  <name>Task 5: Blueprint + runbook</name>
  <files>render.yaml, docs/DEPLOY.md</files>
  <action>
    `render.yaml`: declarar `ALLOW_TEST_TURNSTILE` com `sync: false` e comentário de escape hatch. `docs/DEPLOY.md`: nova seção "Desvio temporário: Turnstile de teste em produção" (o que liga, riscos aceitos, como sair), linha na tabela de env do Render, nota no passo de health e bullet do `-AllowTestTurnstile` no gate.
  </action>
  <verify>`git grep -n "ALLOW_TEST_TURNSTILE"` cobre config, health/testes, gate, blueprint e runbook.</verify>
  <done>Desvio documentado com caminho de saída.</done>
</task>

</tasks>

<verification>
- `backend\.venv\Scripts\python.exe -m pytest -q` verde (inclui D-11/D-12 e o novo override).
- `scripts/verify-deploy.ps1` parseia e mantém UTF-8 com BOM.
- Sem `ALLOW_TEST_TURNSTILE`, nada muda: prod + chave de teste continua recusado e o gate continua exigindo `mode=live`.
</verification>
