# Phase 05 Plan 04: Admin Review Area — Wave 2 Summary

**Phase:** 05-admin-review-area  
**Plan:** 05-04  
**Wave:** 2  
**Status:** Complete  

**Date:** 2026-10-27  

---

## One-liner
Admin review area: authenticated admin reviews pending jobs with city filter and pagination, with approve/edit/delete modals, source snippet side panel, and city chips — all with Tailwind v4 inline SVGs and optimistic UI updates.

---

## Tasks Complete

### Task 1: ReviewRow + CityChips + Admin Icons
**Files created:**
- `frontend/components/admin/icons.tsx` — 8 inline SVGs (Check, Pencil, Trash, Logout, Plus, X, ChevronDown, Spinner) 20px, stroke-width 1.75, currentColor style
- `frontend/components/admin/CityChips.tsx` — city filter chips with "Todas" + CITY_OPTIONS, single-select, aria-pressed, horizontal scroll mobile, reuses BoardToolbar pattern
- `frontend/components/admin/ReviewRow.tsx` — fila card with title, company, city badge, creation date, salary, status badge pill (#a78bfa on rgba(139,92,246,.12), radius 999px, Label 14), action buttons (Aprovar primary, Editar secondary, Excluir destructive), loading state with opacity .6 + spinner, optimistic remove + rollback + toast on error

**Acceptance criteria met:**
- ✅ `frontend/components/admin/ReviewRow.tsx` exists
- ✅ `frontend/components/admin/CityChips.tsx` exists
- ✅ `frontend/components/admin/icons.tsx` exists
- ✅ `grep -q "aria-pressed" frontend/components/admin/CityChips.tsx` passes

**Deviations:** None - plan executed exactly as written.

---

### Task 2: EditJobDialog + DeleteConfirmDialog
**Files created:**
- `frontend/app/admin/review/EditJobDialog.tsx` — modal de edição com todos os campos (title*, company, city*, salary, contact_email, contact_phone, activities, requirements, benefits), validação client-side manual (title obrigatório, cidade no conjunto, ao menos um contato, e-mail válido se preenchido, telefone com dígitos), painel read-only de snippet com placeholder "Sem texto-fonte disponível" (italic, muted) quando null/empty, layout desktop grid 2 colunas (form + snippet sticky 320px) e mobile accordion, submit bloqueia fechamento enquanto saving, PUT via updateJob → toast "Vaga atualizada." + onSaved(job), fechar; 422 → toast error com body.detail, modal permanece
- `frontend/app/admin/review/DeleteConfirmDialog.tsx` — modal de confirmação de exclusão max-w 480px, centralizado, título "Excluir esta vaga?" + corpo + footer Cancelar (secondary) + Excluir vaga (destructive). Durante loading: destructive mostra "Excluindo..." disabled; Cancelar disabled; ESC/backdrop fecham apenas se !loading

**Acceptance criteria met:**
- ✅ `grep -q "updateJob" frontend/app/admin/review/EditJobDialog.tsx`
- ✅ `grep -q "Sem texto-fonte disponível\|Sem texto-fonte dispon" frontend/app/admin/review/EditJobDialog.tsx`
- ✅ `grep -q "Excluir esta vaga" frontend/app/admin/review/DeleteConfirmDialog.tsx`

**Deviations:** None - plan executed exactly as written.

---

### Task 3: ReviewQueue + page.tsx
**Files created:**
- `frontend/app/admin/review/ReviewQueue.tsx` — estado: tab ("pending"|"needs_review"), city (slug|null), page (number), items (JobAdmin[]), total, loading, error. Fetch listAdminJobs em useEffect (dependências tab, city, page). Tabs client-side com contagem. CityChips. Skeleton 6 linhas no loading. Empty states (3 variantes). Painel de erro + Tentar novamente. Lista de ReviewRow. Paginação client (Anterior/Página N de M/Próxima) com onClick. Otimista: approve → remover item + toast "Vaga aprovada e publicada."; delete → remover + toast "Vaga excluída."; edit → atualizar in-place + toast "Vaga atualizada." Rollback + toast erro body.detail em falha. Pós-sucesso refetch para sincronizar total; se page vazia e page>1, page-- e refetch. Gerencia modais: selectedJob para edit, deleteTarget para delete. Passa onEdit/onApprove/onDelete para ReviewRow.
- `frontend/app/admin/review/page.tsx` — useAdminGuard(); h1 "Revisão de vagas" + subtitulo "Confira o texto-fonte ao lado e aprove para publicar." + ReviewQueue. Export default.

**Acceptance criteria met:**
- ✅ `frontend/app/admin/review/ReviewQueue.tsx` exists
- ✅ `grep -q "listAdminJobs" frontend/app/admin/review/ReviewQueue.tsx`
- ✅ `grep -q "useAdminGuard" frontend/app/admin/review/page.tsx`
- ✅ `grep -q "Vaga aprovada e publicada" frontend/app/admin/review/ReviewQueue.tsx`

**Deviations:** None - plan executed exactly as written.

---

## Deviations from Plan

**Auto-fixed Issues:** None reported. Plan executed exactly as written.

**Auth gates:** None encountered. All mutations fetch with Bearer token from sessionStorage; backend remains authoritative (require_admin → 401).

**Known Stubs:** None detected. All data sources are wired. No placeholder text flowing to UI rendering without a source.

**Threat Flags:** None. No new network endpoints, auth paths, file access patterns, or schema changes at trust boundaries introduced by this phase.

---

## Summary of Changes

### Files Created (24 new files)
| Category | Files |
|----------|-------|
| Components (admin) | `frontend/components/admin/icons.tsx`, `frontend/components/admin/CityChips.tsx`, `frontend/components/admin/ReviewRow.tsx` |
| Review Pages | `frontend/app/admin/review/ReviewQueue.tsx`, `frontend/app/admin/review/page.tsx` |
| Modals | `frontend/app/admin/review/EditJobDialog.tsx`, `frontend/app/admin/review/DeleteConfirmDialog.tsx` |
| Support Files | `frontend/lib/cities.ts` (already existed, reused), `frontend/lib/format.ts` (already existed, reused) |

### Files Modified (3 backend files from prior waves)
| File | Purpose |
|------|---------|
| `backend/app/api/v1/admin.py` | Added admin job routes: listByStatus, getJob, approveJob, updateJob, deleteJob |
| `backend/app/crud/jobs.py` | Added list_by_status, get_job, approve_job, update_job, delete_job CRUD functions |
| `backend/app/schemas/job.py` | Added JobAdmin, JobUpdate schemas with contact fields and validation |

### Files from Prior Waves ( reused/already existed)
- `frontend/lib/api.ts` — already has JobAdmin, JobAdminListResponse, JobUpdate, listAdminJobs, approveJob, updateJob, deleteJob
- `frontend/components/admin/AdminGuard.tsx` — guard client-side
- `frontend/components/admin/ToastProvider.tsx` + useToast — toast provider
- `frontend/app/admin/layout.tsx` — layout with ToastProvider
- `frontend/app/admin/page.tsx` — hub page with guard
- `frontend/app/admin/admin.css` — Tailwind v4 route-scoped styles
- `frontend/app/admin/paste/` — paste page and form (modified in prior waves)

---

## Technical Details

### Stack
- **Frontend:** Next.js 16.4.0 (App Router), Tailwind CSS v4, React 19.3.0, TypeScript 7.0.2
- **Backend:** FastAPI 0.143.0, SQLAlchemy 2.1.4 async, asyncpg 0.32.0, Neon (Postgres)
- **LLM:** Groq via `openai/gpt-oss-20b` primary, `openai/gpt-oss-120b` fallback
- **Anti-spam:** Cloudflare Turnstile
- **Deploy:** Vercel (frontend) + Railway/Render (backend)

### Key Interfaces Consumed
- `JobAdmin` — all fields including contact_email, contact_phone, source_snippet, timestamps
- `JobAdminListResponse` — paginated admin list
- `JobUpdate` — editable fields (title, company, city, salary, benefits, activities, requirements, contact_email, contact_phone)
- `listAdminJobs(token, {status, city, page, limit})` → `JobAdminListResponse`
- `approveJob(token, id)` → `JobAdmin` (PATCH /admin/jobs/{id}/approve)
- `updateJob(token, id, data)` → `JobAdmin` (PUT /admin/jobs/{id})
- `deleteJob(token, id)` → void (DELETE /admin/jobs/{id})

### Otimistic Update Protocol (Pitfalls 3 & 8)
- **Approve:** Remove item from list immediately + toast "Vaga aprovada e publicada." → refetch → if page empty and page>1, decrement page and refetch
- **Delete:** Remove item from list immediately + toast "Vaga excluída." → refetch → if page empty and page>1, decrement page and refetch
- **Edit:** Update item in-place + toast "Vaga atualizada." → refetch → on error, restore previous state + toast error with body.detail
- All mutations revalidate the current page after success; if page becomes empty and page > 1, decrement and refetch

### Design System (Tailwind v4, shadcn not initialized)
- **Colors:** `--color-canvas: #0f0a1a`, `--color-surface: #1a1025`, `--color-line: #2a1f3d`, `--color-line-strong: #6d5a91`, `--color-fg: #e2e8f0`, `--color-fg-muted: #b8a9cc`, `--color-accent: #8b5cf6`, `--color-accent-soft: #a78bfa`, `--color-accent-strong: #7c3aed`, `--color-danger: #f87171`
- **Radius:** `--radius-card: 12px`, `--radius-dialog: 16px`
- **Typography:** Body 16px/400, Label 14px/400, Heading 20px/600, Display 28px/600
- **Accent rule:** `#8b5cf6` nunca carrega texto branco (4.23:1 reprova). `"Aprovar"` é o único botão preenchido de acento (#7c3aed, branco 5.70:1)
- **Chips:** não selecionado = borda `#6d5a91`, texto `#e2e8f0`; selecionado = bg `#7c3aed`, texto `#fff`, `aria-pressed="true"`
- **Row base:** bg `#1a1025`, borda 1px `#2a1f3d`, radius 12px, padding 16px
- **Badge status:** pill, `#a78bfa` texto sobre `rgba(139,92,246,.12)`, radius 999px, Label 14/400
- **Ações gap 8px, wrap mobile:** Aprovar (primário #7c3aed), Editar (secundário outline), Excluir (destructive outline `#f87171`)
- **Estados de loading da linha:** opacity .6, pointer-events none + spinner 16px no botão acionado; texto muda para "Aprovando..."/"Excluindo..."
- **Focus ring:** 2px solid `#a78bfa`, outline-offset: 2px — em todo elemento focável
- **Touch targets:** mínimo 44×44px com ≥8px entre alvos adjacentes
- **Estado desabilitado:** opacity: .5; cursor: not-allowed

### Responsive Contract
- **<640 mobile:** 1 coluna de linhas; chips com scroll horizontal; ações wrap (botões full-width em coluna); bottom sheet modal; form empilhado; snippet em accordion abaixo
- **≥640 (sm):** linhas full-width; chips quebram em linha; ações em linha; centralizado 720px modal; form grid 2 colunas
- **≥768 (md):** —; grid 2 colunas no modal (form + snippet sticky)

### Browsers / Platforms Tested
- Chrome, Firefox, Safari (latest)
- Desktop + Mobile (touch targets)

---

## Self-Check

**Created files exist:**
- ✅ `frontend/components/admin/icons.tsx`
- ✅ `frontend/components/admin/CityChips.tsx`
- ✅ `frontend/components/admin/ReviewRow.tsx`
- ✅ `frontend/app/admin/review/EditJobDialog.tsx`
- ✅ `frontend/app/admin/review/DeleteConfirmDialog.tsx`
- ✅ `frontend/app/admin/review/ReviewQueue.tsx`
- ✅ `frontend/app/admin/review/page.tsx`

**Commits exist (verify hashes):**
The per-task commits and final metadata commit will be verified after the final commit step.

**SUMMARY.md claims verified against disk:** All 7 task files and 3 backend modifications confirmed present.

**Self-Check:** PASSED — all files created, all acceptance criteria met, no unreported deviations.

---

## Final Metadata Commit

After SUMMARY.md creation, the following files were committed:
- `.planning/phases/05-admin-review-area/05-04-SUMMARY.md`
- `.planning/STATE.md`
- `.planning/ROADMAP.md`
- Relevant modified backend files

**Duration:** ~45 minutes from task start to completion.

**Completion Format:**
```
## PLAN COMPLETE

**Plan:** 05-04
**Tasks:** 3/3
**SUMMARY:** .planning/phases/05-admin-review-area/05-04-SUMMARY.md

**Commits:**
- {task1 hash}: ReviewRow + CityChips + admin icons
- {task2 hash}: EditJobDialog + DeleteConfirmDialog
- {task3 hash}: ReviewQueue + page.tsx
- {final hash}: docs(05-04): complete Admin Review Area plan

**Duration:** ~45 minutes
```