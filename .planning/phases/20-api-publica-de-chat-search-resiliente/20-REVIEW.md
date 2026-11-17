---
phase: 20-api-publica-de-chat-search-resiliente
reviewed: 2026-11-17T00:00:00Z
depth: standard
files_reviewed: 8
files_reviewed_list:
  - backend/.env.example
  - backend/app/api/v1/public.py
  - backend/app/core/config.py
  - backend/app/core/ratelimit.py
  - backend/app/schemas/chat.py
  - backend/app/services/intent/client.py
  - backend/app/services/intent/parser.py
  - backend/tests/test_chat_search_api.py
findings:
  critical: 0
  warning: 2
  info: 1
  total: 3
status: issues_found
---

# Phase 20: Code Review Report

**Reviewed:** 2026-11-17T00:00:00Z
**Depth:** standard
**Files Reviewed:** 8
**Status:** issues_found

## Summary

Revisão padrão dos arquivos do chat-search público (config/env, schema, rate limit, endpoint, parser/client de intenção e testes). O fluxo geral está alinhado com os objetivos de resiliência e segurança aparente (rate limit dedicado, validação de entrada, respostas sem contato, contrato de interpretação, sanitização/delimitadores para prompt). Porém, há um desalinhamento importante entre `parser` e endpoint que mascara falhas/timeout do LLM como “sem parâmetros extraíveis” no caminho real de execução, produzindo orientação/metadados incorretos ao usuário. Também há inconsistência entre o limite configurável por env e a validação efetiva do schema.

## Warnings

### WR-01: Parser engole exceções de extração e impede classificação correta de degradação (LLM indisponível/timeout)

**File:** `backend/app/services/intent/parser.py:63-72`, `backend/app/api/v1/public.py:274-306`
**Issue:** `extract_and_map_intent` captura `IntentExtractionError`, `ValidationError` e qualquer `Exception` e retorna `build_empty_intent(..., reason_code="no_extractable_params")`. Com isso, falhas reais de provedor/timeout não propagam para `chat_search`, e o endpoint não consegue aplicar o tratamento específico de `llm_unavailable`/`timeout` (linhas 277-292 de `public.py`). No fluxo real, o endpoint tratará o retorno como contrato “efetivamente sem parâmetros” e responderá com `degradation_reason=no_extractable_params` e guidance de parâmetros ausentes, em vez de guidance de indisponibilidade/timeout — divergindo do contrato resiliente pretendido e dos cenários simulados nos testes (que monkeypatcham `extract_and_map_intent` para lançar exceção).
**Fix:**
```python
# backend/app/services/intent/parser.py
async def extract_and_map_intent(..., timeout_seconds: float | int | None = None) -> IntentContract:
    raw_text = "" if text is None else str(text)
    if _is_empty_input(text):
        return build_empty_intent(text, reason_code="empty_input")

    candidate = await parse_intent(
        text, settings, client=client, sleep=sleep, timeout_seconds=timeout_seconds
    )
    # deixa IntentExtractionError/timeout/erros inesperados propagarem para o caller
    # (o endpoint decide degradação/guidance segura), ou retorne um contrato marcado
    # explicitamente com meta.degradation_reason quando optar por degradar aqui.

    contract = map_intent(candidate, raw_text=raw_text)
    if _is_effectively_empty(contract):
        return build_empty_intent(text, reason_code="no_extractable_params")
    return contract
```
```python
# backend/app/api/v1/public.py (se o parser passar a propagar falhas de LLM)
try:
    contract = await extract_and_map_intent(
        payload.message, settings, timeout_seconds=chat_timeout
    )
except IntentExtractionError as exc:
    is_timeout = "timeout" in str(exc).lower()
    reason_code = "timeout" if is_timeout else "llm_unavailable"
    ...
except (asyncio.TimeoutError, TimeoutError) as exc:
    ...
```
Ajuste também os testes de integração/unidade para cobrir o caminho real (parser + endpoint) conforme o contrato desejado.

### WR-02: Limite máximo da mensagem é hardcoded no schema e ignora `CHAT_SEARCH_MAX_MESSAGE_CHARS`

**File:** `backend/app/schemas/chat.py:14`, `backend/app/core/config.py:58`, `backend/.env.example:56`
**Issue:** O schema valida `message` com `Field(min_length=1, max_length=400)` fixo, enquanto a configuração expõe `CHAT_SEARCH_MAX_MESSAGE_CHARS` (e o `.env.example` documenta ajuste). Alterar o env não altera a validação efetiva da API, podendo causar comportamento inesperado em operação (ex.: operador acredita ter reduzido/aumentado o limite para custo/abuso, mas o endpoint continua aceitando/rejeitando com 400). Isso reduz a previsibilidade/configurabilidade do controle de abuso.
**Fix:**
```python
# backend/app/schemas/chat.py
from pydantic import BaseModel, Field, field_validator
from app.core.config import get_settings

def _max_message_chars() -> int:
    # fallback seguro se settings indisponível em contextos isolados
    try:
        return int(get_settings().CHAT_SEARCH_MAX_MESSAGE_CHARS)
    except Exception:
        return 400

class ChatSearchRequest(BaseModel):
    message: str = Field(min_length=1)
    page: int = Field(default=1, ge=1)
    limit: int = Field(default=20, ge=1, le=50)

    @field_validator("message")
    @classmethod
    def _validate_message(cls, value: str) -> str:
        stripped = value.strip()
        if not stripped:
            raise ValueError("Mensagem é obrigatória")
        if len(stripped) > _max_message_chars():
            raise ValueError("Mensagem excede o tamanho máximo permitido")
        return stripped
```
Alternativamente, valide explicitamente no endpoint usando `settings.CHAT_SEARCH_MAX_MESSAGE_CHARS` e mantenha o schema/documentação alinhados.

## Info

### IN-01: Sinalização de aproximação mistura texto de orientação com `limitations`

**File:** `backend/app/api/v1/public.py:116-138`
**Issue:** `_apply_approx_guidance` adiciona `_CHAT_GUIDANCE_APPROX` (frase longa de orientação ao usuário) diretamente em `interpretation.limitations` quando há aproximação/limitações. `limitations` tende a ser consumido como lista de códigos/sinais estruturados em outros pontos (ex.: verificações por códigos como `not_in_whitelist`), e misturar texto livre com códigos pode dificultar consumo programático consistente no frontend/observabilidade. Hoje é mitigado por checagens defensivas, mas é um acoplamento frágil.
**Fix:**
```python
# Preferir manter limitações como códigos/sinais e guidance em meta
meta = deepcopy(contract.meta or {})
if not meta.get("guidance"):
    meta["guidance"] = _CHAT_GUIDANCE_APPROX
contract.meta = meta

# garantir códigos relevantes presentes, sem inserir frase longa como "limitation"
codes = set(contract.limitations or [])
codes.update({"non_native_fields_limited"})
contract.limitations = list(codes)
```
Se o frontend já depende do texto em `limitations`, documente explicitamente o contrato e normalize o tipo (ex.: separar `limitation_codes` e `guidance`).

---
_Reviewed: 2026-11-17T00:00:00Z_
_Reviewer: OpenCode (gsd-code-reviewer)_
_Depth: standard_