# Roadmap: EmpregaNoix — NQU v1.1

## Overview

Continuation of v1.0 (NQU — NaoQueroUsar) under the new EmpregaNoix brand. Milestone v1.1 focuses on completing remaining work from Phases 3, 5, and 6, finalizing the 14-day expiry/hard delete lifecycle, completing the admin review area, and preparing the rebranding from NaoQueroUsar to EmpregaNoix. The core value "Procurar um emprego, não deve dar trabalho" is preserved.

## Milestone Summary

**Milestone v1.1: EmpregaNoix**

- **Goal:** Complete remaining development work from v1.0 and prepare for production deployment under the EmpregaNoix brand — contact reveal finalization, admin review enhancements, deployment infrastructure, and rebranding.
- **Target features:** Finish Phase 3 (contact reveal + anti-spam finish), Phase 5 (admin review area finish), Phase 6 (lifecycle, trust, legal & launch completeness), BRND (rebranding).
- **Key context:** Project at v1.0 with 6 phases completed/in-progress. v1.1 continues phase numbering sequentially from 7. Research completed 2026-10-13; key gaps: Groq model retirement (resolved: `openai/gpt-oss-20b`/`120b`), Turnstile placement, pending job expiry policy, admin auth model. All carried forward and addressed in this milestone.

## Phase Numbering

- Integer phases (7, 8, 9, 10): Planned milestone work
- Decimal phases (7.1, 7.2): Urgent insertions (marked with INSERTED)
- Decimal phases appear between their surrounding integers in numeric order.

## Phases

**Phase 7: Contact Reveal & Anti-Spam Completeness** — Contact reveal finalization, Turnstile server-side verify hardening, anti-spam edge cases

**Phase 8: Admin Review Area Completeness** — Admin review queue finish, approve/edit/excluir workflow, pending job management

**Phase 9: Lifecycle, Trust, Legal & Launch Completeness** — 14-day expiry hard delete, CRON_SECRET endpoint, LGPD pages, deployment infrastructure

**Phase 10: Rebranding & Launch Preparation (EmpregaNoix)** — Renomear de NaoQueroUsar para EmpregaNoix, atualizar textos, hosts, CORS, meta tags

## Phase Details

### Phase 7: Contact Reveal & Anti-Spam Completeness

**Goal:** Finalizar superfície de revelar contato e endurecer anti-spam — garantir que o endpoint de reveal está plenamente server-side gated, rate-limited e que os edge cases de Turnstile são cobertos.

**Depends on:** Phase 1 (schema/expires_at), completed Phase 3 foundation

**Requirements:** SECR-10, SECR-11, SECR-12

**Success Criteria** (what must be TRUE):

1. Endpoint `POST /api/v1/public/jobs/{id}/reveal-contact` roda exclusivamente server-side — contact fields **ausentes** do payload público de lista/detalhe; só retornados após Turnstile Siteverify bem-sucedido
2. Turnstile Siteverify é chamado com `secret`, `response` (token), `remoteip` (via `CF-Connecting-IP` ou `X-Forwarded-For` primeira parte) — validação fail-closed; tokens `timeout-or-duplicate` são tratados como 403
3. Endpoint tem rate limiting por IP — excesso de requisições é bloqueado com 429 e `Retry-After` em pt-BR; knobs `REVEAL_RATE_LIMIT=10/min` e `LOGIN_RATE_LIMIT=5/min` configurados via env
4. Turnstile widget no client usa `next-turnstile@1.0.7` com `key` para remount (nenhum `resetKey` disponível); token consumido nunca pode ser reenviado; login admin também protegido por Turnstile contra credential stuffing
5. Turnstile analytics mostram validacoes não-zero em producao; chaves de teste `1x`/`2x`/`3x` aceitas em `mode=test`, chaves de producao rejeitadas por validador fail-closed

### Phase 8: Admin Review Area Completeness

**Goal:** Terminar área de revisão admin — fila `pending`, aprovar/editar/excluir vagas com texto-fonte ao lado, publicar, com o fluxo completo colar → extrair → revisar → aprovar funcionando.

**Depends on:** Phase 1 (auth), Phase 2 (extração), Phase 4 (tema)

**Requirements:** ADMN-10, ADMN-11, ADMN-12, REVW-10, REVW-11, REVW-12

**Success Criteria** (what must be TRUE):

1. Admin autenticado (JWT no header Authorization) vê a fila de vagas com status `pending` — cards com preview do texto-fonte ao lado dos campos extraídos
2. Admin aprova uma vaga — status muda para `published` e ela passa a aparecer na home pública imediatamente; edição de campos pelo ID também persiste com validação de regra de ao menos um contato
3. Admin exclui uma vaga — remoção hard do banco; operação idempotente (exclusão duplicada é no-op); fluxo completo colar → extrair → revisar → aprovar funciona de ponta a ponta consumindo o endpoint de extração da Fase 2
4. A área admin é protegida: acesso sem sessão autenticada é negado (401); rota `/admin/extract` e rotas de CRUD exigem `Authorization: Bearer <token>`
5. Toast notifications e feedback visual para ações de approve/edit/delete; admin vê quais vagas foram descartadas vs aprovadas

### Phase 9: Lifecycle, Trust, Legal & Launch Completeness

**Goal:** Garantir que o board se mantenha honesto e seguro — vagas somem em 14 dias de forma confiável, e a plataforma tem postura de confiança/legal e deploy prontos para lançar.

**Depends on:** Phase 1 (schema/expires_at), Phase 4 (board público)

**Requirements:** LIFE-10, LIFE-11, LIFE-12, TRST-10, TRST-11, TRST-12

**Success Criteria** (what must be TRUE):

1. Cada vaga nasce com `expires_at` = `created_at` + 14 dias; server_default verificado no modelo e migration; `expires_at` é `timestamptz` computed em UTC via `NOW()` do banco; vaga futura NÃO é deletada por cron
2. Vagas `published` expiradas são hard-deleted por endpoint `/admin/expire` protegido por `X-Cron-Secret` header (ou Bearer JWT admin) — declaração idempotente em UTC; chamada duplicada não causa erro; nenhuma vaga futura é apagada
3. Vagas `pending` não revisadas também expiram após 14 dias — mesma regra de 14 dias aplicada; tabela não cresce indefinidamente
4. Páginas de privacidade (`/privacidade`), termos (`/termos-de-uso`) e aviso LGPD `"somos apenas meio de divulgação"` existem e são acessíveis; política pt-BR com 13 sections (Privacidade) e 10 sections (Termos de Uso/foro Americana/SP)
5. Visitante pode denunciar uma vaga via endpoint `/jobs/{id}/report` — motivo opcional (máx 500 chars), logs estruturados sem persistir reports; badge "Vaga revisada" aparece em vaga com status `published` e aprovada pelo master
6. Frontend (Vercel) e backend (Render) estão deployados com CORS travado à origem do front e segredos configurados por env; cold-start documentado; path de leitura pública permanece rápido quando backend está acordando (first request ~1-2s acceptable)

### Phase 10: Rebranding & Launch Preparation (EmpregaNoix)

**Goal:** Renomear a aplicação de NaoQueroUsar para EmpregaNoix em todo o frontend e infraestrutura, garantindo consistência de marca e configurações de deploy.

**Depends on:** All previous phases (3–9)

**Requirements:** BRND-01, BRND-02, BRND-03, BRND-04

**Success Criteria** (what must be TRUE):

1. Todo o texto do frontend (labels, headings, buttons, mensagens) atualizado de "NaoQueroUsar" / "NQU" para "EmpregaNoix" — incluindo meta tags, headings, alertas, Toast messages, favicons, textos estáticos
2. Slogan mantido "Procurar um emprego, não deve dar trabalho" — refletido na nova marca; atualizado em todos os lugares onde aparecia a referência antiga
3. Cores da marca consistentes: roxo principal `#8b5cf6` / `#a78bfa` para texto, fundos escuros `#0f0a1a` / `#1a1025`, botão Doações amarelo `#facc15` discreto — aplicados no novo build Tailwind v4 com `@theme` variables
4. Hosts atualizados: backend `https://empreganoix.onrender.com`, frontend `https://empreganoix.vercel.app`; CORS configurado para origens `https://empreganoix.vercel.app`; `NEXT_PUBLIC_API_BASE_URL` apontando para o novo host Render; `ALLOWED_ORIGINS` atualizado no backend
5. Deploy Vercel + Render executado com sucesso; smoke gate verde: health 200, env=prod, Turnstile mode=live, CORS preflight 200 com `Access-Control-Allow-Origin`; `CRON_SECRET` configurado em ambos os hosts; cold-start UX documentada

## Progress

**Execution Order:** Phases execute in numeric order: 7 → 8 → 9 → 10

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 7. Contact Reveal & Anti-Spam Completeness | 3/3 | ✓ Complete | 2026-11-12 |
| 8. Admin Review Area Completeness | 0/4 | Not started | |
| 9. Lifecycle, Trust, Legal & Launch Completeness | 0/4 | Not started | |
| 10. Rebranding & Launch Preparation (EmpregaNoix) | 0/4 | Not started | |

## Commit History Note

This roadmap continues from the v1.0 roadmap (Phases 1–6, completed 2026-10-15 through 2026-11-12). v1.1 phases 7–10 complete the remaining work and rebranding under the EmpregaNoix name. All v1.0 requirements (ADMN-01/02/03, EXTR-01/.../09, REVW-01/.../05, PUBL-01/.../06, SRCH-01/.../03, UIUX-01/.../03, SECR-01/.../03, LIFE-01/.../04, TRST-01/.../03) remain mapped from the previous milestone; v1.1 adds new REQ-IDs BRND-01/04 and continues the remaining ADMN-10/12, REVW-10/12, EXTR-10/12, PUBL-10/14, SRCH-10/12, SECR-10/12, LIFE-10/12, TRST-10/12 from the incomplete portions of v1.0 phases.

---

*Roadmap defined: 2026-11-12*
*Milestone v1.1: EmpregaNoix*