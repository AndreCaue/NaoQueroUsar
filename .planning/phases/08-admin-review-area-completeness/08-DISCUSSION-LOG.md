# Phase 8: Admin Review Area Completeness - Discussion Log

**Audit trail only.** Do not use as input to planning, research, or execution agents. Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-11-12
**Phase:** 08-Admin Review Area Completeness
**Areas discussed:** Full end-to-end flow

---

## Full end-to-end flow

| Option | Description | Selected |
|--------|-------------|----------|
| **Valid outcome — return summary with saved_pending=0, discarded=[...], appropriate alerts; frontend shows 'Nenhuma vaga encontrada no texto'** | The extraction is successful but no jobs could be parsed from the pasted text. This is a valid business outcome, not an error. | ✓ |
| Treat as error — return 422 or 503 if no jobs extracted | If no jobs are extracted, it's considered a failure and the endpoint returns an error response. | |
| **Auto-deduplication — if same text is pasted, suppress duplicate and notify admin** | If the same text is pasted twice, the system suppresses the duplicate and shows a notification to the admin. | ✓ |
| Allow duplicates — each paste creates a new pending job; admin reviews and decides | No automatic deduplication. If the same text is pasted twice, two separate jobs are created with status `pending`. | |
| **Block edit if both contacts cleared — show error 'Vaga precisa ter ao menos um contato (email ou telefone)' (422)** | The DB CHECK `at_least_one_contact` prevents saving without a contact. The backend catches the IntegrityError and returns this pt-BR message. | ✓ |
| Allow the edit — the existing contact values are preserved even if the form clears them | The `JobUpdate` schema only applies provided fields. If contact_email and contact_phone are not included in the payload, the existing values remain unchanged in the DB. | |
| **Optimistic update — immediately remove the approved item from the pending queue; then refetch the list in background** | The admin sees the item disappear from the queue instantly, providing instant feedback. If the refetch fails, the item reappears. This is the pattern used in Phase 5 D-13. | ✓ |
| Wait for API response then refresh the list | The admin waits for the approve endpoint's 200 response, then the list is refetched from the server. The pending queue stays unchanged until the refetch completes. | |

**User's choice:** All four questions answered as marked above (✓). The user confirmed the decisions for the full end-to-end flow of the admin review area.

**Notes:** Decisions D-E2E-01 through D-E2E-10 capture the full end-to-end flow behavior for Phase 8: extraction with 0 results, auto-deduplication of pastes, contact validation on edit, and optimistic update after approval. All carried forward from codebase analysis of backend (`backend/app/api/v1/extract.py`, `backend/app/api/v1/admin.py`) and frontend patterns (Phase 5 Toast, api.ts admin functions). Prior decisions from Phases 1-5 carried forward without re-asking (auth via JWT, at_least_one_contact CHECK, city filter set, Turnstile integration, 14-day expiry).

---

## OpenCode's Discretion

- Estrutura de arquivos/componentes da fila admin e do modal de edição (`components/admin/` ou similar), nomes de helpers de fetch.
- Mecânica exata do toast (posicionamento, animação, z-index) e da atualização otimista (rollback em erro).
- Como o hub `/admin` se comporta quando não autenticado (redireciona para login ou mostra login inline).
- Paginação visual (controles vs "Ver mais") na fila admin — reusar o padrão da Phase 4 (JobGrid/Pagination) se fizer sentido.
- Empty state da fila (copy pt-BR) e estado de loading (skeleton).
- Validação client-side do form de edição (zod) e mensagens de erro (renderizar `body.detail` verbatim, padrão Phase 4).
- Se a aba "Precisam correção" é uma rota separada ou tab client-side.

## Deferred Ideas

- Aprovação em lote (checkbox + "Aprovar selecionadas") — descartado nesta fase; se o volume justificar, considerar depois.
- Ação "Rejeitar" (→`invalid` ou →`needs_review`) — descartado; excluir cobre o caso.
- Reversão published→pending ("Despublicar") — descartado; aprovação definitiva.
- Busca por texto livre na fila admin — Descartado (filtro por cidade basta).
- Middleware Next.js server-side para proteção admin — Descartado (token é Bearer em sessionStorage).
- Biblioteca de toast externa (sonner/react-hot-toast) — Descartado; componente próprio.
- Ciclo de vida / expiração hard-delete 14 dias — Phase 6.
- Chaves reais do Cloudflare + wiring de deploy — Phase 6.