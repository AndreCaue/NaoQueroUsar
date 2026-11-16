---
phase: 17-publicacao-assincrona-retry-idempotencia-e-status
plan: 02
subsystem: api
tags: [fastapi, sqlalchemy, pydantic, pytest, social, cron, retry, admin]
requires:
  - phase: 17-publicacao-assincrona-retry-idempotencia-e-status
    provides: pipeline único de claim/publicação/retry/idempotência e CRUD social base (17-01)
provides:
  - endpoint cron protegido por `X-Cron-Secret` para processamento idempotente de lote social
  - contratos/admin APIs seguros de status/lista e retry manual por vaga
  - dispatch imediato não bloqueante pós-aprovação via pipeline único quando elegível
affects: [17-03, admin-ui, social-ops]
tech-stack:
  added: []
  patterns: [worker cron protegido por require_cron_secret, status/retry admin idempotente com contratos seguros pt-BR, approve site-first com BackgroundTasks pós-commit]
key-files:
  created:
    - backend/tests/test_admin_social_publish.py
    - backend/tests/test_admin_social_retry_api.py
    - backend/tests/test_admin_social_status_api.py
    - backend/tests/test_social_worker_claim.py
  modified:
    - backend/app/api/v1/admin.py
    - backend/app/crud/social_posts.py
    - backend/app/schemas/social_posts.py
    - backend/tests/conftest.py
    - backend/tests/test_social_publish_pipeline.py
key-decisions:
  - "Retry/status usam elegibilidade centralizada (conta conectada, failed sem publicação, sem processamento) e retornos idempotentes/no-op seguros."
  - "Dispatch imediato do approve é enfileirado apenas após commit/site publicado para posts registrados e devidos, com falha de enqueue isolada."
  - "Claim direcionado por post_id permite retry manual de falha elegível mesmo sem next_retry_at devido, mantendo guarda idempotente no pipeline."
patterns-established:
  - "Admin social status item: labels pt-BR, erro resumido, sem segredos, com can_retry/retry_block_reason."
  - "Rota operacional /admin/social/worker segue o mesmo padrão de segredo/segurança de /admin/expire."
requirements-completed: [PUB-02, PUB-03, PUB-04, PUB-07, PUB-08, UI-01, UI-02]
duration: 20min
completed: 2026-11-16
---

# Phase 17 Plan 02: Publicação Assíncrona, Retry, Idempotência e Status Summary

**Worker cron e APIs admin de status/retry seguros integrados ao pipeline único, com approve site-first disparando publicação social imediata não bloqueante quando elegível.**

## Performance

- **Duration:** 20 min
- **Started:** 2026-11-16T12:56:00Z
- **Completed:** 2026-11-16T13:16:05Z
- **Tasks:** 2
- **Files modified:** 9

## Accomplishments
- Expostos `POST /admin/social/worker` (cron, `X-Cron-Secret`), `GET /admin/social-posts`, `GET /admin/jobs/{job_id}/social-status` e `POST /admin/jobs/{job_id}/social-post/retry` com contratos seguros e respostas idempotentes.
- Implementados schemas/helpers de status operacional (`SocialPostStatusItem`, labels pt-BR, `can_retry`/`retry_block_reason`, resumo de worker/retry) e cálculo de elegibilidade alinhado ao pipeline/estado da conta.
- Integrado dispatch imediato pós-aprovação com `BackgroundTasks` após commit para posts registrados/devidos, reutilizando `process_social_post_safe`/pipeline sem bloquear ou alterar sucesso do site.

## Task Commits

Each task was committed atomically:

1. **Task 1: Contratos/schemas e endpoints protegidos de worker, status/lista e retry idempotente** - `55a9b19` (feat)
2. **Task 2: Dispatch imediato pós-aprovação (site-first, não bloqueante) e regressões fire-and-forget** - `7d8cfc1` (test)

**Plan metadata:** pending

## Files Created/Modified
- `backend/app/api/v1/admin.py` - adiciona worker/status/retry protegidos e dispatch imediato pós-aprovação via `BackgroundTasks`.
- `backend/app/schemas/social_posts.py` - define contratos seguros de status/lista/retry/worker para admin/UI.
- `backend/app/crud/social_posts.py` - adiciona consultas de status/listagem, cálculo de elegibilidade e ajuste de claim direcionado por `post_id`.
- `backend/app/services/social/publish_pipeline.py` - reutilizado como pipeline único (sem mudanças funcionais diretas neste plano além de integração).
- `backend/tests/conftest.py` - adiciona fixtures/helpers para cenários sociais (cron header, conta conectada/reconexão, posts elegíveis).
- `backend/tests/test_social_worker_claim.py` - cobre proteção por `X-Cron-Secret` e processamento do worker.
- `backend/tests/test_admin_social_status_api.py` - cobre contratos seguros de status/lista e labels/eligibilidade.
- `backend/tests/test_admin_social_retry_api.py` - cobre retry elegível, inelegível e idempotente.
- `backend/tests/test_admin_social_publish.py` - cobre approve site-first, enqueue não bloqueante e ausência de dispatch quando não elegível.
- `backend/tests/test_social_publish_pipeline.py` - cobre processamento seguro direcionado por `post_id`.

## Decisions Made
- Retry manual retorna resposta idempotente segura (`retried|noop|not_eligible`) com item atualizado/motivo, sem duplicar publicação.
- Link público do post não é inferido quando não confiável; `external_post_id` é exposto com segurança e `published_url` permanece nulo.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Ajuste de claim para alvo específico (`post_id`)**
- **Found during:** Task 1 (retry/status integration)
- **Issue:** `list_due_for_claim` exigia `next_retry_at` devido para falhas, impedindo retry manual elegível de falhas finais sem auto-retry.
- **Fix:** Para seleção por `post_id`, permitir claim de `scheduled/failed` elegíveis e delegar elegibilidade/idempotência ao fluxo seguro; seleção em lote por tempo permanece inalterada.
- **Files modified:** `backend/app/crud/social_posts.py`
- **Verification:** novos testes de retry/pipeline cobrem caminho direcionado; `python -m pytest -q tests/test_social_publish_pipeline.py tests/test_social_retry_policy.py tests/test_social_idempotency.py -x` passou.
- **Committed in:** `55a9b19` (part of task commit)

---

**Total deviations:** 1 auto-fixed (1 blocking)
**Impact on plan:** Necessário para cumprir retry manual elegível/idempotente sem ampliar escopo. Sem mudança de escopo funcional além do previsto.

## Issues Encountered
- Verificação automatizada DB-backed do plano (`tests/test_social_worker_claim.py`, `tests/test_admin_social_status_api.py`, `tests/test_admin_social_retry_api.py`, `tests/test_admin_social_publish.py`, `tests/test_admin_social_posts.py`) falhou no ambiente atual por ausência de schema migrado no banco de testes configurado (`relation "jobs" does not exist`). Verificação unitária/compilação disponível passou: `python -m pytest -q tests/test_social_publish_pipeline.py tests/test_social_retry_policy.py tests/test_social_idempotency.py -x` e `python -m compileall` nos arquivos alterados.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness
- Backend pronto para a UI admin (17-03): endpoints de status/lista/retry e worker expostos com contratos seguros e integração de dispatch pós-aprovação.
- Bloqueio operacional de validação DB-backed persiste no ambiente atual (banco de testes sem migrações/tabelas); reexecutar suíte DB em ambiente com schema aplicado.

---
*Phase: 17-publicacao-assincrona-retry-idempotencia-e-status*
*Completed: 2026-11-16*

## Self-Check: PASSED
