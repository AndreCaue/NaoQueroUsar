# Framework Selection — Phase 22

**Phase:** 22 — qualidade-hardening-e-valida-o-operacional  
**Goal:** Validar, endurecer e operacionalizar o chatbot público de busca de vagas (já implementado nas Phases 19–21) sem regredir a experiência pública existente.  
**Question:** "What AI/LLM framework is right for this project/phase?"

## Project & Codebase Signals (scan)

- **Backend:** FastAPI 0.143.0, Pydantic 2.14.1, SQLAlchemy 2.1.4, Groq Python SDK `groq==1.7.0`, httpx 0.28.1, APScheduler (pyproject.toml).
- **Frontend:** Next.js 16.4.6, React 19, TypeScript 5.9, Vitest, Cloudflare Turnstile.
- **Existing AI integration (Phases 19–21):** intent extraction via Groq (`openai/gpt-oss-20b` default, configurable) in `backend/app/services/intent/{client,parser,mapper,schema}.py`. **LLM extrai apenas parâmetros**; busca é determinística sobre `list_published`/`GET /api/v1/public/jobs`; resposta pública `JobPublic` sem contatos; proteções (rate limit, limites de tamanho/tempo), fallback/guidance seguro em pt-BR.
- **Phase 22 scope:** QA/hardening/operacional (QA-01 matriz+evidência, QA-02 consolidar suíte automatizada com LLM mockado + UI flow viável sem Playwright/RTL novo, QA-03 kill-switch/config fim-a-fim + logs/métricas sem PII). **Sem** novos recursos de IA voltados ao usuário, sem busca semântica/vetorial, sem memória persistente, sem novos filtros nativos garantidos.

## Interview

Skipped (≤6 questions not needed): system type, provider, stage, language, priority e constraints já estão definidos no contexto do projeto/fase e pelo código existente. O chatbot já está implementado com arquitetura deliberada (extração estruturada + mapeamento/busca determinística); Phase 22 não introduz novo sistema de IA a ser escolhido.

## Decision

**No new AI framework adoption for Phase 22.** A stack mínima atual (Groq SDK direto + Pydantic para contrato/validação + orquestração própria determinística) é a escolha correta e deve ser mantida/endurecida.

### Rationale
- **Fit com arquitetura existente:** o contrato v1.3 exige LLM apenas para extração de parâmetros em JSON estrito, com schema server-side, defaults seguros e busca determinística reutilizando `list_published`. Frameworks de orquestração/agentes (LangChain, LlamaIndex, PydanticAI, etc.) adicionariam abstração e superfície de falha sem benefício para um fluxo single-turn, schema-bound e já implementado.
- **Fit com escopo de Phase 22:** objetivos são validação documentada, cobertura automatizada (com seams mockáveis), kill-switch e observabilidade sem PII. Isso favorece código explícito/testável (cliente/parser/mapper já separados) em vez de migrar para framework.
- **Fit com constraints:** baixo custo/latência, provider configurável (Groq padrão), sem corpus no prompt, sem contatos no payload, fricção zero no board público, sem infra nova. Manter Groq SDK + Pydantic preserva controle fino de timeout/fallback/limites e evita lock-in adicional.

### Hard constraints applied
- Sem exposição de contatos no payload do chat; sem busca semântica/vetorial/memória persistente (exclui stacks RAG/vetor/agente stateful).
- Sem novos filtros nativos garantidos além de suporte limitado/aproximado.
- Sem regressão do board público; kill-switch deve manter busca/listagem manual utilizável.
- Reuso stack fixa do projeto (FastAPI, Next.js 16, Neon, Groq, Turnstile) e infra viável (sem Playwright/RTL nova nesta fase).

## Outputs

```
FRAMEWORK_RECOMMENDATION:
  primary: Keep current stack — Groq Python SDK (groq==1.7.0) + Pydantic 2 (schema/validation) with existing deterministic intent→search pipeline (no new orchestration framework)
  rationale: Phase 22 hardens an already-implemented single-turn NL→structured-intent→deterministic-search chatbot (Phases 19-21). The direct Groq SDK + Pydantic contract gives strict JSON extraction, server-authoritative mapping, easy mocking/timeouts/fallbacks, and minimal abstraction—best fit for QA, kill-switch, and PII-free observability without regressing the public board. Higher-level frameworks add complexity with no gain for this constrained flow.
  alternative: Instructor (thin structured-output layer over the LLM client) — only if future phases need stronger/typed extraction ergonomics without adopting full agent orchestration
  alternative_reason: Can reduce prompt/parse glue while staying close to Pydantic models, but is unnecessary churn for a hardening-only phase on a working implementation.
  system_type: Conversational Assistant / Chatbot (NL search over an existing board; single-turn intent extraction + deterministic retrieval, not agentic/memory/RAG)
  model_provider: Model-agnostic/configurable (default Groq openai/gpt-oss-20b; seam already isolated in intent client)
  eval_concerns: intent_extraction_accuracy, schema_compliance_no_hallucinated_fields, mapping_correctness_and_safe_defaults, partial_support_approximation_signaling, fallback_degradation_and_safe_errors_ptBR, privacy_no_contacts_no_query_PII_in_logs, latency_timeout_rate_limit_behavior, kill_switch_does_not_regress_manual_board
  hard_constraints: [no_contact_exposure_in_chat, no_semantic_vector_search, no_persistent_memory, no_new_guaranteed_native_filters, preserve_frictionless_public_board, keep_fixed_project_stack, no_new_test_infra_Playwright_or_RTL]
  existing_ecosystem: {backend: [fastapi==0.143.0, groq==1.7.0, pydantic==2.14.1, sqlalchemy==2.1.4, httpx==0.28.1, slowapi, apscheduler], frontend: [next==16.4.6, react==19, vitest, next-turnstile], llm: [Groq API, default openai/gpt-oss-20b via env GROQ_MODEL], architecture: [intent client/parser/mapper/schema, POST /api/v1/public/chat-search, deterministic list_published]}
```

## Display

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
 FRAMEWORK RECOMMENDATION
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

◆ Primary Pick: Keep current stack — Groq Python SDK (`groq==1.7.0`) + Pydantic 2 (no new orchestration framework)
  Phase 22 is hardening/QA/ops for the chatbot já entregue (Phases 19–21): extração single-turn em JSON estrito + mapeamento/busca determinística sobre `list_published`. O SDK Groq direto com contratos Pydantic mantém controle de schema/timeout/fallback/mocks e observabilidade sem PII, com mínima abstração e sem risco de regressão ao board público — adequado para QA-01/02/03, não para introduzir um novo framework de agentes.

◆ Alternative: Instructor (camada fina de structured output sobre o cliente LLM)
  Só se fases futuras exigirem ergonomia tipada mais forte na extração; desnecessário como churn em fase de hardening.

◆ System Type Classified: Conversational Assistant / Chatbot (NL search: intent extraction + deterministic retrieval, single-turn)
◆ Key Eval Dimensions: intent_extraction_accuracy, schema_compliance_no_hallucinated_fields, mapping_correctness_and_safe_defaults, partial_support_approximation_signaling, fallback_degradation_and_safe_errors_ptBR, privacy_no_contacts_no_query_PII_in_logs, latency_timeout_rate_limit_behavior, kill_switch_does_not_regress_manual_board
