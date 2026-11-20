---
phase: 22
slug: qualidade-hardening-e-valida-o-operacional
status: verified
threats_open: 0
asvs_level: 1
created: 2026-11-20
audited: 2026-11-20
---

# Phase 22 — Security

> Per-phase security contract: controles, ameaças, riscos residuais e trilha de auditoria para o chat-search público e hardening operacional.

---

## Trust Boundaries

| Boundary | Description | Data Crossing |
|----------|-------------|---------------|
| Browser público → `POST /api/v1/public/chat-search` | Mensagem NL e parâmetros de paginação enviados por usuário não confiável; endpoint público sem autenticação. | `ChatSearchRequest` (`message`, `page`, `limit`) entra; resposta retorna interpretação (`IntentContract`) + resultados `JobPublic` sem contatos. |
| Browser público → `GET /api/v1/public/chat-search/status` | Consulta operacional de disponibilidade do chat (sinal simples para UI). | Requisição sem payload sensível; resposta `{"enabled": boolean}`. |
| Chat-search API → seam de intenção (LLM/config) e → busca determinística pública | Texto não confiável é interpretado por seam controlado com timeout/validação; parâmetros efetivos aplicados consultam apenas busca determinística do board (`list_published`) com contrato público. | `applied_params` (`q`, `city`, `sort`) e paginação cruzam para consulta determinística; nenhum contato/PII sensível é injetado na resposta do chat. |
| Resposta do chat → UI pública / fluxo canônico de detalhe-reveal | Interpretação, limitações/guidance e itens `JobPublic` são exibidos como conteúdo público; contato permanece fora do chat. | Somente dados públicos de vaga cruzam para UI do chat; revelação de contato continua no fluxo canônico dedicado (fora deste payload). |
| Operação/logs ↔ observabilidade | Eventos operacionais do chat-search registrados para suporte/controle sem expor conteúdo sensível. | `logger.info("chat_search", extra={outcome,reason,latency_ms,results_count,total,page,limit})`; sem `payload.message`, sem `contact_email`/`contact_phone`, sem segredos/internos. |

---

## Threat Register

| Threat ID | Category (ASVS L1 / STRIDE) | Component | Disposition | Mitigation | Status |
|-----------|------------------------------|-----------|-------------|------------|--------|
| T-22-01 | V4/V5 / DoS (abuso/custo) | `backend/app/api/v1/public.py` (`@router.post("/chat-search")`), `backend/app/core/ratelimit.py`, `backend/app/schemas/chat.py`, `backend/app/core/config.py` | mitigate | Rate limit dedicado por IP/endpoint via `@limiter.limit(chat_search_limit)` (`CHAT_SEARCH_RATE_LIMIT`, `SafeLimiter key_style="endpoint"`), limites de entrada/paginação (`message` trim/obrigatória com max `CHAT_SEARCH_MAX_MESSAGE_CHARS`, `page>=1`, `limit` 1-50), e timeout dedicado de interpretação (`CHAT_SEARCH_INTENT_TIMEOUT_SECONDS`) propagado ao seam. Erros de validação/requisição retornam pt-BR seguro (400/422 conforme contrato de validação FastAPI/Pydantic). | closed |
| T-22-02 | V5 / Tampering, Reliability | `backend/app/api/v1/public.py`, `backend/app/services/intent/parser.py`/client seam, `backend/app/schemas/chat.py` | mitigate | Entrada não confiável tratada com validação de schema e fallback/degradação segura: falhas/timeout/indisponibilidade/ausência de parâmetros extraíveis retornam 200 controlado com `meta.degraded=true`, `degradation_reason`, guidance pt-BR, `applied_params` nulos quando apropriado e `results` vazio; erros inesperados viram 500 genérico pt-BR sem expor internals (stack/provider). | closed |
| T-22-03 | Operational control / Availability | `backend/app/core/config.py`, `backend/app/api/v1/public.py` (`GET /chat-search/status`, short-circuit), frontend consumers (gating) | mitigate | Kill-switch operacional `CHAT_SEARCH_ENABLED` (default true) exposto por status e aplicado no endpoint: quando desativado, retorna resposta controlada `chat_disabled` com guidance para busca manual, sem chamada ao LLM/DB de busca de vagas para o fluxo do chat; board público/listagem manual permanece independente (`GET /api/v1/public/jobs`). | closed |
| T-22-04 | Integrity / Tampering (query semantics) | `backend/app/api/v1/public.py`, `backend/app/crud/jobs.py`, `backend/app/services/intent/*` | mitigate | LLM/seam apenas extrai parâmetros; busca executada deterministicamente com `list_published(session, page, limit, q=applied.q, city=applied.city, sort=(applied.sort or "recentes"))` usando `applied_params` efetivos. Resposta serializa itens como `JobPublic` e mantém `total/page/limit` consistentes com o contrato público. | closed |
| T-22-05 | V4 / Information Disclosure (privacy) | `backend/app/schemas/chat.py`, `backend/app/api/v1/public.py`, contratos públicos (`JobPublic`) | mitigate | Chat-search não expõe contatos no payload: resultados usam `JobPublic` (sem `contact_email`/`contact_phone`) e interpretação/metadados não incluem dados de contato; revelação de contato permanece no fluxo canônico dedicado fora do chat. Testes/evidências da fase cobrem ausência de contatos em respostas do chat. | closed |
| T-22-06 | Logging / Information Disclosure (PII/sensitive content) | `backend/app/api/v1/public.py` logging/observabilidade | mitigate | Logging operacional estruturado em `finally` registra apenas `outcome`, `reason`, `latency_ms`, `results_count`, `total`, `page`, `limit` (sem `payload.message`, sem PII, sem contatos, sem segredos). Tratamento de falhas usa mensagens seguras ao usuário e logs técnicos sem conteúdo sensível do usuário. (sem PII / no PII no payload/log operacional do chat-search.) | closed |
| T-22-07 | V5 / Integrity of interpretation signaling | `backend/app/services/intent/mapper.py`, `backend/app/api/v1/public.py` | mitigate | Suporte parcial/aproximado e limites (campos não nativos, whitelist de cidade, ausência de filtros garantidos) são sinalizados em `field_statuses`/`limitations`/`meta.guidance`; não se afirma filtragem estruturada inexistente nem se inferem cidades fora da whitelist. | closed |

*Disposition: mitigate (control implemented/documented) / accept (documented residual risk) / transfer.*
*Status: open / closed.*

---

## Accepted Risks Log

| ID | Risk | Justification | Residual Impact | Future Condition / Action |
|----|------|---------------|-----------------|---------------------------|
| AR-22-01 | Validações manuais/runtime/browser (UAT guiado, percepção UI fim-a-fim de kill-switch/degradação, cenários integrados com dados/restart/env) não integralmente executadas nesta sessão de fechamento documental. | `22-HUMAN-UAT.md` e `22-MANUAL-UAT.md` foram reconciliados em 23-03 com **deferimento aceito por item** (motivo: ambiente/runtime/dados/browser/infra indisponíveis), preservando passes históricos e evidências automatizadas. | Risco residual baixo a moderado de divergência operacional/UX em ambiente real apesar de contratos, testes e hardening existentes. | Executar roteiro manual/UAT em ambiente integrado/controlado por item e registrar evidências objetivas; atualizar artefatos de verificação/segurança conforme resultados. |
| AR-22-02 | Dependência de pré-requisitos de ambiente para execução DB-backed completa em todos os subsets de teste quando aplicável. | Suites determinísticas/mockadas e evidências históricas existem; execução DB-backed completa depende de banco de testes migrado/configurado. | Risco residual baixo de regressão específica de integração DB não observada no ambiente atual. | Rodar suites DB-backed em ambiente migrado e anexar evidência de execução. |
| AR-22-03 | Limites inerentes do escopo MVP documentados (whitelist de cidades suportadas, campos não nativos sem filtro estruturado garantido, busca textual determinística sem similaridade semântica/vetorial/link-ID). | Limitações são parte explícita do contrato (sinalização em interpretação/guidance/limitations e matrizes QA), não falha de controle. | Expectativa do usuário pode exceder capacidades suportadas se guidance for ignorada. | Manter sinalização clara em contrato/UI/docs; evoluir capacidades apenas com mudança explícita de escopo/contrato e validação correspondente. |

---

## Security Audit Trail

| Audit Date | Threats Total | Closed | Open | Run By |
|------------|---------------|--------|------|--------|
| 2026-11-20 | 7 | 7 | 0 | gsd-executor (Phase 23, CL-05/D-15) |

### Notes

- Revisão baseada em controles implementados e artefatos existentes: `backend/app/api/v1/public.py` (status/kill-switch, rate limit, timeout, validação, fallback/degradação, busca determinística `list_published`, logging sem `payload.message`), `backend/app/core/config.py` (`CHAT_SEARCH_ENABLED`, limites/timeouts), `backend/app/schemas/chat.py` (`JobPublic`/contrato), `backend/app/core/ratelimit.py`, e evidências `22-VERIFICATION.md`, `22-MVP-EXAMPLES.md`, `22-HUMAN-UAT.md`, `22-MANUAL-UAT.md`, `22-VALIDATION.md`.
- Contatos não expostos no chat (`JobPublic` sem `contact_email`/`contact_phone`) e logging operacional sem PII/conteúdo sensível confirmados por contrato/código e evidências documentadas; sem afirmação de validação runtime adicional nesta sessão.

---

## Sign-Off

- [x] All threats have a disposition (mitigate / accept / transfer)
- [x] Accepted risks documented in Accepted Risks Log
- [x] `threats_open: 0` confirmed
- [x] `status: verified` set in frontmatter

**Approval:** verified (2026-11-20, documentação rastreável baseada em controles e evidências existentes; deferimentos runtime aceitos por item registrados em artefatos da fase 22)