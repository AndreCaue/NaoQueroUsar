# Phase 20: API pública de chat-search resiliente - Context

**Gathered:** 2026-11-17
**Status:** Ready for planning

<domain>
## Phase Boundary

Expor um endpoint público e protegido que recebe uma mensagem em linguagem natural (pt-BR), combina a extração de intenção da Fase 19 com a busca determinística existente e retorna interpretação transparente + resultados pagináveis no contrato público, sem expor contatos. Esta fase cobre o contrato HTTP de chat-search, proteções de abuso/custo/tempo, erros pt-BR seguros, fallback controlado em falha do LLM e sinalização explícita de suporte parcial/aproximado para filtros não nativos.

**Não** inclui: interface de chat no board, aplicação/ajuste visual da busca no frontend, pós-filtros avançados em janela candidata, busca semântica/embeddings, histórico de conversa, autenticação/login, nem suíte de testes/E2E/controles operacionais completos (UI-*/QA-* das fases 21–22), exceto decisões que impactem diretamente o contrato da API.

</domain>

<decisions>
## Implementation Decisions

### Contrato do endpoint e resposta
- **D-01:** Endpoint público `POST /api/v1/public/chat-search` (JSON), sem autenticação, dedicado ao chat de busca. Request com mensagem em linguagem natural (ex.: `message`) e parâmetros de paginação, priorizando body JSON (texto livre, limites claros) em vez de mensagem longa em query string.
- **D-02:** Resposta em envelope completo separando interpretação e resultados, preservando `JobPublic` sem contatos: `interpretation` (contrato de intenção) + `results` com paginação/itens no estilo do público (ex.: `{ items: JobPublic[], page, limit, total }`), análogo à semântica de `JobListResponse`.
- **D-03:** Paginação alinhada ao contrato público existente: aceitar `page` (>=1, default 1) e `limit` (1–50, default 20) na request; resultados refletem busca determinística equivalente a `GET /api/v1/public/jobs` / `list_published(...)` para os `applied_params` efetivos (`q`, `city`, `sort`), com `total` correspondente ao mesmo predicado.
- **D-04:** Interpretação expõe o contrato completo e server-authoritative da Fase 19: `understood`, `field_statuses` por campo (entendido/aplicado/status/motivo), `applied_params` finais (`q`/`city`/`sort`), `limitations` e `meta` conforme aplicável — permitindo à UI mostrar aplicado/ignorado/aproximado com rastreabilidade e sem afirmar filtragem inexistente.

### Proteções e limites operacionais
- **D-05:** Rate limit dedicado por configuração/env para o chat-search (bucket por IP resolvido + endpoint), aplicado somente nesta rota e independente de `reveal`/login; reutilizar `app.core.ratelimit` (`resolve_client_ip`, `key_style="endpoint"`, storage em memória) e o padrão de 429 em pt-BR com `Retry-After`.
- **D-06:** Limite curto e estrito para a mensagem no schema/validação (ex.: `message` obrigatória, trim, faixa ~1..300/500 caracteres — valor exato a definir na implementação), rejeitando entradas inválidas/excedentes com erro 4xx seguro em pt-BR.
- **D-07:** Orçamento de tempo dedicado e curto para a extração de intenção do chat (setting próprio, desacoplado de `GROQ_TIMEOUT_SECONDS` de fluxos admin); ao atingir timeout/falha do LLM, acionar fallback controlado (não segurar request longa).
- **D-08:** Mapeamento de erros seguro, sem vazar detalhes internos: validação/tamanho → 400/422 com `detail` pt-BR; rate limit → 429 (handler atual); falha/timeout/indisponibilidade do LLM → resposta 200 degradada com fallback/orientação (não erro opaco 5xx/503 ao usuário); erros internos inesperados → 500 genérico pt-BR com log server-side.

### Fallback e degradação do LLM
- **D-09:** Em falha/timeout/indisponibilidade do LLM, retornar interpretação degradada **sem resultados automáticos**: `applied_params` nulos, `results` vazio (`items=[]`, `total=0`, page/limit preservados) e orientação clara para busca manual/keywords no board — evitando exibir vagas irrelevantes como se tivessem sido interpretadas.
- **D-10:** Diferenciar causa na resposta via contrato estruturado: usar `meta`/`limitations` e motivos/reason codes (ex.: `degraded`, `degradation_reason` como `llm_unavailable` | `timeout` | `no_extractable_params` | `empty_input`) mantendo `field_statuses` coerentes, para orientar adequadamente “reformular consulta” vs “tentar depois/usar busca manual”.
- **D-11:** Incluir orientação pt-BR explícita pronta para exibição na interpretação (ex.: campo em `meta.guidance` e/ou limitações textualizadas), além de códigos/flags estruturados, garantindo mensagem segura e consistente por cenário.
- **D-12:** Priorizar resposta rápida com fallback controlado: respeitar timeout curto do chat e evitar retries longos/agressivos que atrasem o endpoint público; se não houver interpretação confiável dentro do orçamento, devolver degradação + orientação (200). Tentativas adicionais de modelo/repair só se couberem no orçamento.

### Suporte parcial e filtros não nativos
- **D-13:** Para campos sem filtro nativo completo (salário, modalidade, tipo de contrato, senioridade), aplicar **somente aproximação via `q` mapeado** + sinalização; não pós-filtrar resultados por esses campos nem afirmar filtragem estruturada inexistente. Busca determinística normal sobre `applied_params` produzidos pelo intent.
- **D-14:** Quando houver aproximação/limite, incluir aviso agregado claro em `limitations`/orientação pt-BR (ex.: faixa salarial não filtrada numericamente, apenas aproximação textual), além dos `field_statuses`/motivos por campo, para evitar interpretação errada de suporte garantido.
- **D-15:** Consultas de “vagas parecidas com uma vaga” tratadas como aproximação textual limitada: extrair termos relevantes para `q` quando possível e sinalizar explicitamente que não há similaridade semântica/vetorial garantida (abordagem limitada/seed conforme suportado, sem prometer ranking especial).
- **D-16:** Cidades/locais fora da whitelist (ex.: Campinas) nunca são inferidos para SP/RJ/BH. Aplicar apenas partes suportadas com segurança (ex.: `Remoto` quando aplicável), incluir termos úteis em `q` como aproximação quando apropriado, e marcar o restante como ignorado/aproximado com motivo; conflitos resolvidos deterministicamente sem inventar mapeamento.

### OpenCode's Discretion
- Nomes exatos de campos do request/response JSON, shape final de `meta`/guidance, e nome/valor exato do env de rate limit e timeout do chat (desde que atendam D-01..D-12 e padrões existentes).
- Valor numérico final do limite de caracteres da mensagem e mensagens pt-BR exatas de validação/guidance/limitações (claras, seguras, sem vazamento interno).
- Organização interna do endpoint/módulo (router/schema/service), reaproveitamento de `extract_and_map_intent`/intent client vs adaptação para orçamento curto, e composição de logs/métricas básicas sem PII sensível.
- Detalhes de quando incluir termos como “Campinas” em `q` vs apenas marcar limitação, desde que nunca viole whitelist/inferência agressiva e mantenha sinalização honesta.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Requisitos, escopo e decisões de produto
- `.planning/PROJECT.md` — Core value (fricção zero, sem login, contatos protegidos), constraints (Groq baixo custo, stack) e escopo do milestone v1.3.
- `.planning/REQUIREMENTS.md` — API-01..API-03 (contrato desta fase), INT-01..INT-03 (dependência atendida), UI-01..UI-03/QA-01..QA-03 (consumidores/validação posterior).
- `.planning/ROADMAP.md` §Phase 20 — Goal, success criteria 1–5 e dependência da Fase 19.
- `.planning/STATE.md` — Decisões v1.3 vigentes: LLM só extrai parâmetros; busca determinística reutiliza `GET /api/v1/public/jobs`/`list_published` e `JobPublic`; campos não nativos = suporte limitado/aproximado sinalizado.

### Contrato de intenção e busca determinística (dependências diretas)
- `.planning/phases/19-contrato-de-intencao-e-mapeamento-seguro/19-CONTEXT.md` — Decisões D-01..D-16 (schema, normalização segura, classificação por campo, `applied_params q/city/sort`, prompt seguro, empty/degraded intent).
- `backend/app/services/intent/schema.py` — `IntentContract`, `IntentLLMOutput`, `AppliedParams`, `FieldAssessment`, enums e modelos strict (understood/applied/status/reason).
- `backend/app/services/intent/parser.py` — `extract_and_map_intent`, `parse_intent`, `build_empty_intent` e degradação segura em falha/entrada vazia.
- `backend/app/services/intent/mapper.py` — Mapeamento determinístico server-authoritative (whitelist cidade/sort explícito, composição de `q`, conflitos, limitações).
- `backend/app/services/intent/client.py` — Seam Groq de intent (mensagens/delimitadores, schema/validação, cadeia de modelos/repair/fallback, `IntentExtractionError`).

### API pública, busca e proteção existentes (reuso obrigatório)
- `backend/app/api/v1/public.py` — Contrato público atual (`GET /public/jobs`, `GET /public/jobs/{id}`), uso de `list_published`, `resolve_city/sort`, `JobPublic`/`JobListResponse` sem contatos e padrões de erro.
- `backend/app/crud/jobs.py` — `list_published(...)` e predicados/ordenação/paginação determinísticos + `total` no mesmo filtro (equivalência exigida por API-01).
- `backend/app/services/cities.py` — `resolve_city`/`CITY_ALIASES` e `resolve_sort` (whitelist canônica SP/RJ/BH/Remoto).
- `backend/app/schemas/job.py` — `JobPublic`, `JobListResponse`, `ContactRevealResponse` (referência: contatos só no reveal, nunca no payload público de busca/chat).
- `backend/app/core/ratelimit.py` — `limiter`, `resolve_client_ip`, `key_style="endpoint"`, 429 pt-BR `{"detail":...}` + `Retry-After`, knobs por rota.
- `backend/app/api/v1/router.py` — Registro de routers v1 (ponto de inclusão do novo endpoint público).
- `backend/app/main.py` — App factory, CORS, registro do limiter/handler 429 e lifecycle.
- `backend/app/core/config.py` — Settings/env (`GROQ_*`, origens, limites existentes) — base para novos knobs de chat (rate limit/timeout/tamanho conforme decisão).

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `app/services/intent/*`: pipeline completo de intenção (schema strict, parser com fallback seguro, mapper determinístico, client Groq isolado) — núcleo para extrair+mapear a mensagem do chat.
- `app/crud/jobs.py:list_published` + `app/services/cities.py`: busca determinística, normalização de cidade/sort e paginação/total já consolidadas — devem ser reutilizadas para equivalência com o endpoint público.
- `app/api/v1/public.py` + `app/schemas/job.py`: padrões de resposta pública sem contato (`JobPublic`, `JobListResponse`) e tratamento de 404/erros pt-BR.
- `app/core/ratelimit.py`: limiter em memória por IP+endpoint, mensagens pt-BR e `Retry-After` — padrão para proteger o novo endpoint com knob dedicado.
- `app/core/config.py` / `app/main.py`: carregamento de settings e wiring global (CORS, limiter, lifespan) para adicionar configurações/endpoint com impacto mínimo.

### Established Patterns
- Separação router → service/crud/schemas; validação forte com Pydantic; respostas/erros públicos em pt-BR (`detail`).
- Segurança por design: contatos nunca no payload público de listagem/detalhe; rate limit e resolução de IP centralizados; input LLM tratado como não confiável no domínio de intent.
- Determinismo server-side para filtros públicos: whitelist de cidade, sort permitido, `total` calculado sobre os mesmos filtros dos itens.
- Degradação controlada preferida a falhas opacas em fluxos dependentes de LLM (ver parser/mapper de intent).

### Integration Points
- Novo endpoint público (ex.: em `backend/app/api/v1/public.py` ou router público dedicado) registrado em `app/api/v1/router.py`, aceitando mensagem+paginação e orquestrando `intent` → `applied_params` → `list_published` → envelope `interpretation+results`.
- Reuso direto de `extract_and_map_intent`/`map_intent` e, se necessário, adaptação do client/chamada para timeout dedicado do chat (sem quebrar fluxos existentes).
- Configuração de novos envs (rate limit/timeout/tamanho) em `settings`/`.env.example` conforme padrões do projeto (detalhe de nome/valores default na implementação).

</code_context>

<specifics>
## Specific Ideas

- Sem referências externas específicas além dos requisitos/roadmap e do código existente. O usuário optou pelas recomendações em todas as áreas discutidas: contrato explícito e auditável, proteção conservadora, fallback útil e honesto, e aproximação limitada sem prometer capacidades inexistentes (ex.: filtro numérico de salário, similaridade semântica).

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope.

</deferred>

---

*Phase: 20-api-publica-de-chat-search-resiliente*
*Context gathered: 2026-11-17*
