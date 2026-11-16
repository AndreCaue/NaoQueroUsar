---
phase: 17-publicacao-assincrona-retry-idempotencia-e-status
plan: 03
subsystem: ui
tags: [nextjs, react, typescript, admin, social, status, retry]
requires:
  - phase: 17-publicacao-assincrona-retry-idempotencia-e-status
    provides: APIs admin seguras de status/lista/retry social e contratos do worker (17-02)
provides:
  - cliente admin tipado para status/lista/retry de publicações sociais
  - status social por vaga na fila e no diálogo de revisão com badge/erro/link/retry elegível
  - página admin "Publicações no Facebook" com listagem operacional e navegação dedicada
affects: [admin-review, admin-social-ops, phase-17-closeout]
tech-stack:
  added: []
  patterns: [status social admin em pt-BR com contratos seguros, retry single-flight idempotente, navegação admin dedicada para acompanhamento social]
key-files:
  created:
    - frontend/app/admin/social-posts/page.tsx
    - frontend/app/admin/social-posts/SocialPostsClient.tsx
  modified:
    - frontend/lib/api.ts
    - frontend/app/admin/review/EditJobDialog.tsx
    - frontend/app/admin/review/ReviewQueue.tsx
    - frontend/components/admin/ReviewRow.tsx
    - frontend/app/admin/layout.tsx
    - frontend/app/admin/page.tsx
key-decisions:
  - "Fila de revisão obtém status social por vaga sob demanda com cache local por job id e tratamento de 401, evitando refetch infinito e mantendo varredura rápida."
  - "Retry no diálogo e na visão de publicações segue single-flight + feedback idempotente/no-op usando a resposta do backend, sem expor segredos/payloads."
patterns-established:
  - "Bloco 'Status da publicação no Facebook' com labels pt-BR, helpers por estado, link externo seguro e CTA de retry apenas quando elegível."
  - "Página operacional simples de publicações sociais com loading/erro/empty, orientação de reconexão e navegação para revisão/integrações."
requirements-completed: [UI-01, UI-02]
duration: 18min
completed: 2026-11-16
---

# Phase 17 Plan 03: Publicação Assíncrona, Retry, Idempotência e Status Summary

**UI admin para acompanhamento e operação da publicação social: status/badges/erros/links e retry elegível na revisão/edição, mais visão dedicada de publicações consumindo os contratos seguros de 17-02.**

## Performance

- **Duration:** 18 min
- **Started:** 2026-11-16T13:20:00Z
- **Completed:** 2026-11-16T13:38:00Z
- **Tasks:** 2
- **Files modified:** 8

## Accomplishments
- Adicionados tipos e chamadas admin em `frontend/lib/api.ts` para status por vaga, listagem de publicações sociais e retry idempotente (`getSocialStatus`, `getAdminSocialPosts`, `retrySocialPost`) alinhados aos contratos de 17-02.
- Integrado bloco "Status da publicação no Facebook" no `EditJobDialog` com badges pt-BR, estados/erros seguros, horário agendado/publicado quando aplicável, link `Ver post no Facebook` (`target="_blank" rel="noopener noreferrer"`), orientação `Abrir Integrações` para `/admin/integracoes` e `Tentar novamente` apenas para casos elegíveis com single-flight e feedback idempotente.
- Adicionados indicadores sociais compactos na fila de revisão (`ReviewRow`/`ReviewQueue`) e nova rota `/admin/social-posts` com listagem operacional, estados loading/erro/empty, links/ações e navegação no layout/painel admin.

## Task Commits

Each task was committed atomically:

1. **Task 1: Cliente API social e status/retry integrados à revisão e edição (UI-01/UI-02)** - `008fac1` (feat)
2. **Task 2: Nova visão/lista de publicações sociais e navegação admin (UI-01/UI-02)** - `85885ee` (feat)

**Plan metadata:** pending

## Files Created/Modified
- `frontend/lib/api.ts` - adiciona contratos/tipos e funções autenticadas para status, listagem e retry social.
- `frontend/app/admin/review/EditJobDialog.tsx` - exibe status social seguro, link publicado, retry elegível/idempotente e orientação de reconexão.
- `frontend/app/admin/review/ReviewQueue.tsx` - carrega status social por vaga para a fila com tratamento de autenticação.
- `frontend/components/admin/ReviewRow.tsx` - renderiza badge compacto de status social relevante por vaga.
- `frontend/app/admin/social-posts/page.tsx` - cria página admin "Publicações no Facebook" com intro operacional.
- `frontend/app/admin/social-posts/SocialPostsClient.tsx` - implementa visão/lista com estados, badges, erros/links, retry elegível e navegação auxiliar.
- `frontend/app/admin/layout.tsx` - adiciona link de navegação para `/admin/social-posts`.
- `frontend/app/admin/page.tsx` - adiciona card de acesso a publicações sociais no painel.

## Decisions Made
- Exibir retry e orientações estritamente conforme elegibilidade/motivos retornados pelo backend, mantendo feedback idempotente sem sugerir edição/remoção de post no Facebook.
- Reutilizar padrões existentes de autenticação/admin UI (401 -> sessão expirada/redirecionamento, toasts, loading/erro) para consistência e segurança.

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
- `cd frontend && npm run lint` concluiu com exit code 0, mas reportou warnings pré-existentes e novos avisos `react-hooks/set-state-in-effect` nos componentes alterados/novos (sem erros de lint).

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness
- Phase 17 fica funcional no admin para visibilidade e retry operacional das publicações sociais (UI-01/UI-02), alinhada aos contratos seguros do backend.
- Validações humanas/runtime end-to-end (Meta conectado, publicação real/agendada, retry em ambiente integrado) permanecem recomendadas conforme estado operacional do projeto.

---
*Phase: 17-publicacao-assincrona-retry-idempotencia-e-status*
*Completed: 2026-11-16*

## Self-Check: PASSED

- FOUND: frontend/lib/api.ts
- FOUND: frontend/app/admin/review/EditJobDialog.tsx
- FOUND: frontend/app/admin/review/ReviewQueue.tsx
- FOUND: frontend/components/admin/ReviewRow.tsx
- FOUND: frontend/app/admin/social-posts/page.tsx
- FOUND: frontend/app/admin/social-posts/SocialPostsClient.tsx
- FOUND: frontend/app/admin/layout.tsx
- FOUND: frontend/app/admin/page.tsx
- FOUND commit: 008fac1
- FOUND commit: 85885ee
- `cd frontend && npm run lint` exited 0 (warnings only)
