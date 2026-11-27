# Project Retrospective

*A living document updated after each milestone. Lessons feed forward into future planning.*

## Milestone: v1.5 — Integração Instagram na Revisão

**Shipped:** 2026-11-27
**Phases:** 5 | **Plans:** 11 | **Tasks:** 27

### What Was Built
- Prontidão Meta/Instagram aditiva no fluxo Meta/Facebook existente: persistência de readiness `ig-user-id`, contratos pt-BR seguros de status/verify, base de mídia (schemas/migration) e UX admin em Integrações com estados acionáveis.
- Card IG determinístico 1080x1350 com serving público HTTPS versionado, validação/proveniência IMAG-01 e documentação operacional META-03 (escopos, App Review/roles/tasks, setup/verificação, env vars).
- Experiência de revisão Instagram por vaga: toggle independente, legenda Template C determinística/editável, contador `N/2200`, aviso >30 hashtags, CTA “link na bio”, preview exato e bloqueio aplicável só ao Instagram.
- Pipeline Graph Instagram 2 passos assíncrono e isolado do Facebook: polling limitado, mapeamento seguro de erros, reconciliação de ambiguidade sem retry cego, rate/content limit acionável sem retry storm, auditoria/status seguros por plataforma.
- Hardening HARD-01 + regressão Facebook green e reconciliação de auditoria/bookkeeping (Phase 33) com evidência objetiva, sem execução fabricada.

### What Worked
- Reaproveitar a base Meta/Facebook existente (token/conta/fluxos) reduziu escopo e evitou regressão estrutural.
- Separar contrato (Phase 29), UX de revisão (30), pipeline (31) e hardening/reconciliação (32/33) manteve dependências claras e permitiu fechar lacunas de auditoria sem retrabalho funcional grande.
- Tratar ambiguidade/rate limit como estados seguros e acionáveis (sem retry cego/storm) alinhou implementação com risco operacional real da Graph API.

### What Was Inefficient
- Artefatos de verificação/validação/Nyquist ficaram parciais/stale em alguns pontos, exigindo Phase 33 de reconciliação documental.
- Confirmações live Meta (readiness real, HTTPS público acessível pela Meta, OAuth reconnect, App Review/roles/tasks) permanecem handoffs manuais; evidência automatizada não cobre o ambiente externo.
- O CLI de milestone/completion introduziu encoding/format drift em arquivos de planejamento, exigindo correção manual.

### Patterns Established
- Publicação social por provider deve ser isolada: falha/limite/ambiguidade em uma plataforma não bloqueia nem corrompe a outra.
- Mídia para Instagram deve ser tratada como contrato explícito: imagem válida, URL pública HTTPS acessível pela Meta, versão/hash rastreável e preview exato antes de publicar.
- Ambiguidade de publicação exige reconciliação antes de nova tentativa automática; rate/content limit vira estado acionável, nunca retry storm.
- Fechamentos de auditoria devem separar evidência automatizada de handoffs live e nunca fabricar execução manual.

### Key Lessons
1. Integrações com APIs externas precisam de “safe states” de primeira classe (ambíguo, rate-limited, reconnect-required), não apenas happy-path.
2. Bookkeeping de verificação (VERIFICATION/VALIDATION/traceability) deve ser atualizado no mesmo ciclo do gap closure para evitar auditoria stale.
3. Para mídia servida a terceiros (Meta), validar reachability pública e configuração de ambiente (`MEDIA_PUBLIC_BASE_URL`) é parte do DoD operacional.

### Cost Observations
- Model mix: not tracked
- Sessions: not tracked
- Notable: 111 commits / 161 files in v1.4..HEAD; milestone close required manual cleanup after CLI encoding drift.

---

## Cross-Milestone Trends

### Process Evolution

| Milestone | Sessions | Phases | Key Change |
|-----------|----------|--------|------------|
| v1.5 | not tracked | 5 | Added dedicated reconciliation phase (33) to close audit bookkeeping with objective evidence |

### Cumulative Quality

| Milestone | Tests | Coverage | Zero-Dep Additions |
|-----------|-------|----------|-------------------|
| v1.5 | not tracked | not tracked | not tracked |

### Top Lessons (Verified Across Milestones)

1. Do not fabricate runtime/manual evidence; record explicit handoffs and accepted residuals.
2. Keep social/publication flows isolated and fail-safe across providers.
