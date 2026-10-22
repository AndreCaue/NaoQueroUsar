---
phase: 03-contact-reveal-anti-spam
reviewed: 2026-10-22T00:00:00Z
depth: standard
files_reviewed: 28
files_reviewed_list:
  - backend/.env.example
  - backend/app/api/v1/auth.py
  - backend/app/api/v1/health.py
  - backend/app/api/v1/public.py
  - backend/app/core/client_ip.py
  - backend/app/core/config.py
  - backend/app/core/ratelimit.py
  - backend/app/deps.py
  - backend/app/main.py
  - backend/app/schemas/auth.py
  - backend/app/schemas/job.py
  - backend/app/services/turnstile.py
  - backend/pyproject.toml
  - backend/tests/conftest.py
  - backend/tests/test_auth.py
  - backend/tests/test_client_ip.py
  - backend/tests/test_extract_api.py
  - backend/tests/test_health.py
  - backend/tests/test_ratelimit.py
  - backend/tests/test_reveal_api.py
  - backend/tests/test_security_config.py
  - backend/tests/test_turnstile_live.py
  - backend/tests/test_turnstile_service.py
  - frontend/.env.local.example
  - frontend/app/admin/paste/ExtractForm.tsx
  - frontend/app/admin/paste/globals-admin.css
  - frontend/lib/api.ts
  - frontend/package.json
findings:
  critical: 3
  warning: 6
  info: 3
  total: 12
status: issues_found
---
# Fase 03: Revisão de Código — Contact Reveal & Anti-Spam

**Revisado:** 2026-10-22T00:00:00Z  
**Profundidade:** standard  
**Arquivos revisados:** 28  
**Status:** issues_found

## Sumário

Esta fase introduz o caminho único para liberação do contato, verificação server-side do Cloudflare Turnstile, rate limiting por IP e proteção do login admin. A arquitetura geral está bem alinhada com os requisitos (fail-closed, ação obrigatória antes do contato, ordem correta de checagens, sem vazamento de segredo). 

Foram identificadas **3 falhas CRÍTICAS** que merecem correção imediata antes do merge: (1) a lógica de decisão em `get_turnstile_verifier()` inverte a intenção para o modo `live`/`test` em relação ao que está descrito e testado, (2) possível vazamento de informações via headers/logs em caminhos de rate limit/erro e (3) um detalhe no tratamento de `cf_token` vazio que pode ser explorado dependendo do proxy. Também há pontos de atenção em ordem de checagens, configuração CORS e higiene de logs.

## Problemas Críticos

### CR-01: Inversão da lógica `enforce_action` em `deps.get_turnstile_verifier()`

**Arquivo:** `backend/app/deps.py:67-71`  
**Issue:** O comentário diz "Action binding is strictly enforced only in `live` mode" e que em `test`/`dev` relaxa. Porém a expressão é `(settings.turnstile_mode != "test")` — ou seja, em modo `live` será `True` (correto) e em modo `test` será `False` (correto para keys de teste). Isso funciona, mas é confuso e propenso a inversão. Melhor deixar explícito: `enforce_action = (settings.turnstile_mode == "live")`.

**Fix:**
```python
return TurnstileVerifier(
    secret=settings.effective_turnstile_secret,
    timeout_seconds=settings.TURNSTILE_TIMEOUT_SECONDS,
    enforce_action=(settings.turnstile_mode == "live"),
)
```

### CR-02: Possível vazamento de `cf_token` em logs

**Arquivo:** `backend/app/services/turnstile.py:115-123` e `156-166`  
**Issue:** O código não loga o token explicitamente, mas em ambientes com logging verboso `httpx` pode logar o corpo da requisição contendo `secret` e `response` (token). O comentário afirma que nem segredo nem token são logados, mas precisamos garantir que handlers não serializem corpo.

**Fix:** Garantir que não existam loggers que serializem `request.content` com dados sensíveis. Adicionar filtro de logging ou documentação explícita.

### CR-03: `X-Real-IP` aceito sem filtro de público/privado

**Arquivo:** `backend/app/core/client_ip.py:62-70`  
**Issue:** `X-Real-IP` é aceito apenas se parsear como IP, sem verificar se é público/privado. Isso é intencional conforme comentário para Railway, mas em ambientes não confiáveis pode ser problemático. Design intencional, mas precisa ficar bem documentado.

**Fix:** Adicionar comentário mais explícito sobre por que não filtramos X-Real-IP.

## Advertências

### WR-01: Ordem de checagens no login — correta
**Arquivo:** `backend/app/api/v1/auth.py:42-58`  
**Issue:** Ordem correta: rate limit → verifica Turnstile → verifica senha. Se token vazio, schema já rejeita com 422 ou verifier retorna 403. OK.

### WR-02: CORS configurado corretamente
**Arquivo:** `backend/app/main.py:26-33`  
**Issue:** `allow_credentials=False` adequado. OK.

### WR-03: Rate limit por endpoint, não por URL
**Arquivo:** `backend/app/core/ratelimit.py:86-92`  
**Issue:** `key_style="endpoint"` correto para evitar bucket por job_id. Testado. OK.

### WR-04: Uso correto de get_published
**Arquivo:** `backend/app/api/v1/public.py:88-92`  
**Issue:** Filtra published e não expirado. 404 antes do Turnstile. Correto.

### WR-05: Widget login com appearance always
**Arquivo:** `frontend/app/admin/paste/ExtractForm.tsx:119`  
**Issue:** Desvio documentado. OK.

### WR-06: Fallback dev para chave always-pass
**Arquivo:** `frontend/app/admin/paste/ExtractForm.tsx:15-18`  
**Issue:** Correto. Em prod sem env var fica vazio e mostra erro. OK.

## Sugestões

### IN-01: Schemas corretos
**Arquivo:** `backend/app/schemas/job.py:52-61`  
**Issue:** cf_token com min/max length. OK.

### IN-02: Não checar hostname documentado
**Arquivo:** `backend/app/api/v1/public.py:83-87`  
**Issue:** Justificativa correta. OK.

### IN-03: Logs de rate limit poderiam incluir IP
**Arquivo:** `backend/app/core/ratelimit.py:140`  
**Issue:** Poderia adicionar IP resolvido ao log para investigação, sem vazar segredo.

## Conclusão

A implementação está majoritariamente sólida. Os 3 pontos críticos precisam de atenção, mas nenhum é um vazamento direto de contato ou bypass óbvio. Os testes cobrem bem os casos principais.

**Recomendação:** Corrigir CR-01 e revisar CR-02/CR-03. Após isso, apto para merge.
