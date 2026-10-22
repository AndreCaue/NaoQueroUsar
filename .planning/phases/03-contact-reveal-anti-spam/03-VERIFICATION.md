---
phase: 03-contact-reveal-anti-spam
verified: 2026-10-22T08:30:00Z
status: passed
score: 16/16 must-haves verified
re_verification: false
---

# Verificação da Fase 03: Contact Reveal & Anti-Spam

**Meta da fase (ROADMAP.md):** *O contato das vagas é servido apenas por um endpoint dedicado, protegido por Turnstile verificado no servidor e rate limiting por IP - ocultar no cliente não basta.* Também protege o login do admin com Turnstile contra credential stuffing.

**Requisitos:** SECR-01, SECR-02, SECR-03, PUBL-05  
**Status:** passed  
**Plano:** 4/5 concluídos no ROADMAP, 5/5 executados (03-05 fez prova real + checkpoint)

## Resumo da Verificação

A fase implementa o caminho único para liberação de contatos, com todas as proteções no servidor conforme especificado. Foram verificados contra o código-fonte real (não apenas SUMMARYs): configuração fail-closed do Turnstile, resolução de IP consciente de proxy, cliente Siteverify com binding por ação, rate limiting com slowapi, endpoint dedicado de reveal com ordem correta de checagens, login admin protegido com Turnstile, e widgets no frontend. Os testes (175 passed, 3 skipped - os 3 são `test_turnstile_live.py` com `TURNSTILE_LIVE!=1`), build e lint do frontend passam.

## Cobertura de Requisitos

| Requisito | Descrição | Status | Evidência |
|-----------|-----------|--------|-----------|
| SECR-01 | Cloudflare Turnstile validado no servidor antes de revelar o contato | ✓ SATISFEITO | `backend/app/services/turnstile.py` (cliente Siteverify httpx, fail-closed), `backend/app/api/v1/public.py` chama `verifier.verify()` com `expected_action="reveal"`. Smoke test live provou chamada real à API Cloudflare (03-05). |
| SECR-02 | Endpoint de revelação de contato tem rate limiting por IP | ✓ SATISFEITO | `backend/app/core/ratelimit.py` com slowapi in-memory, `@limiter.limit(reveal_limit)` em `backend/app/api/v1/public.py`, chave via `resolve_client_ip` (D-10). `REVEAL_RATE_LIMIT=10/minute` configurável. Testes cobrem 429 com Retry-After em pt-BR. |
| SECR-03 | Turnstile também protege o login do admin contra credential stuffing | ✓ SATISFEITO | `backend/app/api/v1/auth.py` com `@limiter.limit(login_limit)`, verifica Turnstile com `expected_action="login"` antes de comparar senha, ordem correta. Frontend tem widget em `frontend/app/admin/paste/ExtractForm.tsx`. |
| PUBL-05 | Contato servido por endpoint dedicado e não aparece no payload público da lista | ✓ SATISFEITO | `backend/app/schemas/job.py` - `JobPublic` sem `contact_email`/`contact_phone`; `ContactRevealResponse` é o único schema com contato. Endpoint `POST /api/v1/public/jobs/{job_id}/reveal-contact`. Teste `test_public_job_payload_has_no_contact` garante não vazamento. |

## Verdades Observáveis (Must-Haves Consolidadas)

| # | Verdade | Status | Evidência |
|---|---------|--------|-----------|
| 1 | Chave Turnstile ausente/de teste (1x/2x/3x) derruba startup fora de ENV=dev (fail-closed) | ✓ VERIFIED | `backend/app/core/config.py:_validate_turnstile()` rejeita vazio fora de dev e regex `_TURNSTILE_TEST_KEY_RE` bloqueia chaves de teste. |
| 2 | Em ENV=dev usa chave always-pass do Cloudflare quando não configurada | ✓ VERIFIED | `Settings.effective_turnstile_secret()` retorna `DEV_TURNSTILE_SECRET` em dev sem secret. |
| 3 | IP resolvido por cadeia fixa: X-Real-IP → XFF mais à direita não-privado → request.client.host → "unknown"; leftmost XFF nunca usado | ✓ VERIFIED | `backend/app/core/client_ip.py:resolve_client_ip()` implementa exatamente essa lógica. |
| 4 | Limites REVEAL_RATE_LIMIT=10/minute e LOGIN_RATE_LIMIT=5/minute configuráveis por env | ✓ VERIFIED | `backend/app/core/config.py` com defaults, documentados em `.env.example`. |
| 5 | Cliente Siteverify assíncrono (httpx) fail-closed em qualquer erro; token nunca logado | ✓ VERIFIED | `backend/app/services/turnstile.py` - captura erros, fail-closed, sem log de token/segredo. |
| 6 | Action binding entre fluxos; enforcement condicional por modo | ✓ VERIFIED | `TurnstileVerifier.verify()` com binding; `deps.get_turnstile_verifier()` ajusta `enforce_action` por modo. |
| 7 | Rate limit com slowapi in-memory, chave por IP resolvido, bucket por endpoint, 429 pt-BR com Retry-After | ✓ VERIFIED | `backend/app/core/ratelimit.py` - implementação completa. |
| 8 | /health reporta status do Turnstile sem vazar segredo | ✓ VERIFIED | `backend/app/api/v1/health.py`. |
| 9 | Testes 100% offline via dependency_overrides | ✓ VERIFIED | `backend/tests/conftest.py`. Suíte passa sem rede. |
| 10 | Contato só sai por POST /api/v1/public/jobs/{id}/reveal-contact; payload público sem contato | ✓ VERIFIED | Schemas e rota corretos. |
| 11 | Ordem correta no reveal: rate limit → 404 se não publicada/expirada → Siteverify → 200 | ✓ VERIFIED | Implementado conforme D-03. |
| 12 | No login: rate limit → Siteverify 403 → bcrypt 401 → JWT 200 | ✓ VERIFIED | Ordem correta em `auth.py`. |
| 13 | LoginRequest e RevealRequest com cf_token obrigatório | ✓ VERIFIED | Schemas com validação. |
| 14 | Frontend admin com widget next-turnstile, reset por remount | ✓ VERIFIED | `frontend/app/admin/paste/ExtractForm.tsx`. |
| 15 | loginAdmin(password, cfToken) com tratamento pt-BR | ✓ VERIFIED | `frontend/lib/api.ts`. |
| 16 | Smoke test live prova chamada real à Cloudflare | ✓ VERIFIED | `backend/tests/test_turnstile_live.py` (opt-in). |

**Score:** 16/16 must-haves verificados

## Artefatos Críticos

| Artefato | Status | Detalhes |
|----------|--------|-----------|
| `backend/app/core/config.py` | ✓ VERIFIED | Fail-closed, fallbacks corretos |
| `backend/app/core/client_ip.py` | ✓ VERIFIED | Resolução proxy-aware D-10 |
| `backend/app/core/ratelimit.py` | ✓ VERIFIED | Limiter configurado corretamente |
| `backend/app/services/turnstile.py` | ✓ VERIFIED | Cliente Siteverify completo |
| `backend/app/api/v1/public.py` | ✓ VERIFIED | Endpoint reveal com proteções |
| `backend/app/api/v1/auth.py` | ✓ VERIFIED | Login protegido |
| `backend/app/schemas/job.py` | ✓ VERIFIED | Separação correta público/revelação |
| `frontend/app/admin/paste/ExtractForm.tsx` | ✓ VERIFIED | Widget integrado |

## Code Review

CR-01 (enforce_action lógica) - confuso mas funcional. CR-02 (logs httpx) - risco teórico sem evidência. CR-03 (X-Real-IP sem filtro) - decisão intencional documentada para Railway. Nenhum defeito bloqueador.

## Conclusão

**FASE 03 ATINGIU SEU OBJETIVO.** Todas as proteções implementadas no servidor conforme especificado. Testes passando (175 passed, 3 skipped), build frontend verde, prova real realizada. Pronto para prosseguir.

**Status:** passed
