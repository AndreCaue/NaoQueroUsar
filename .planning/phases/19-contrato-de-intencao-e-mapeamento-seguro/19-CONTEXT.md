# Phase 19: Contrato de intenção e mapeamento seguro - Context

**Gathered:** 2026-11-17
**Status:** Ready for planning

<domain>
## Phase Boundary

Converter consultas em linguagem natural (pt-BR) em um **contrato de intenção estruturado, validado e rastreável**, mapeável com segurança para a busca pública determinística existente (`GET /api/v1/public/jobs` / `crud.list_published`) sem inventar filtros. Esta fase define o schema/extração/normalização/classificação (INT-01..INT-03): o que foi entendido, o que foi efetivamente aplicado (`q`, cidade whitelist SP/RJ/BH/Remoto, `sort` permitido) e o que foi ignorado/aproximado, explicitando limites quando não há suporte nativo. **Não** implementa o endpoint HTTP público, UI de chat, pós-filtro em janela, rate limit de endpoint nem testes E2E (fases 20–22).

</domain>

<decisions>
## Implementation Decisions

### Schema e campos da intenção
- **D-01:** Texto principal de busca representado como **campo único `q` normalizado** (cargo + palavras-chave combinados), alinhado ao parâmetro `q` consumido por `list_published`/`search_text` (`title + company + activities + requirements`).
- **D-02:** Campos não declarados e não claramente implicados ficam **`null`/omitidos por padrão** (sem inventar informação). Ausência não cria filtro nem viés de busca.
- **D-03:** Faixa salarial modelada de forma estruturada: **`salary_min` / `salary_max` numéricos + `currency` (BRL)**, normalizando expressões pt-BR (“>= 8k”, “6–10k”, “até 5 mil”, “R$ 3.500”) quando declaradas.
- **D-04:** **Modalidade, tipo de contrato e senioridade** modelados como **enums fixos + campo `raw` opcional** (preserva expressão original para rastreabilidade). Validação forte; granularidade exata dos enums fica a critério da implementação desde que cubra os casos do contrato/mapeamento.

### Normalização e mapeamento seguro
- **D-05:** **Cidade** normalizada apenas por **variações óbvias/seguras** para a whitelist real (`São Paulo`, `Rio de Janeiro`, `Belo Horizonte`, `Remoto`), compatível com `resolve_city`/aliases existentes. Sem inferência agressiva/inventada (ex.: municípios fora da whitelist não viram cidade mapeada). “Home office/remoto” pode mapear para `Remoto` quando claro; “híbrido/presencial” não viram cidade fora da whitelist.
- **D-06:** **Sort** inferido **somente quando explícito** no pedido; caso contrário permanece `null` no contrato de intenção (defaults seguros aplicados no mapeamento/consumo, sem registrar preferência inventada). Mapeamento válido: `recentes` / `antigas` (compatível com `resolve_sort`).
- **D-07:** **Conflitos** (ex.: sort conflitante, múltiplas cidades/intenções incompatíveis, instruções contraditórias) resolvidos por **regra determinística** priorizando o mais específico/seguro e **sinalizando o conflito**; nunca aplicar filtros incompatíveis simultaneamente. Cada parâmetro deve refletir status/motivo coerente.
- **D-08:** Campos/termos **sem suporte nativo** (ex.: salário, modalidade, contrato, senioridade) podem **incluir termos textuais relevantes em `q`** quando útil para recall, mas devem ser **marcados como aproximados quando aplicável** — sem afirmar filtragem estruturada inexistente. Evitar poluir `q` com ruído sem valor de busca.

### Classificação aplicado/ignorado/aproximado
- **D-09:** Taxonomia verificável **por parâmetro/campo** com status + motivo curto: registrar ao menos **valor entendido**, **valor aplicado** (quando houver), **status** (`aplicado` | `ignorado` | `aproximado`) e **reason/motivo**.
- **D-10:** Critério de status para campos não nativos: **`aproximado`** se o pedido influenciou `q`/estratégia textual efetiva; **`ignorado`** se não pôde ser usado. Nunca prometer filtragem inexistente. (Ex.: `Remoto` pode ser `aplicado` como cidade se mapeado à whitelist; “CLT/pleno/React” usados em `q` tendem a `aproximado`; faixa salarial sem aplicação real tende a `ignorado` ou equivalente explícito conforme suporte.)
- **D-11:** O contrato deve **separar “entendido” de “aplicado”** e expor os **parâmetros efetivamente aplicados** na busca determinística (`q`, `city`, `sort` / equivalentes finais), permitindo auditar equivalência com `list_published`.
- **D-12:** Suporte parcial/limitado explicitado por **flags/motivos estruturados por campo + aviso agregado** (vocabulário/códigos padronizáveis, ex.: aproximação textual vs filtro não suportado), evitando apenas texto livre ambíguo.

### Reuso do pipeline LLM e robustez
- **D-13:** **Reaproveitar infraestrutura Groq/cliente/config existente** (`GROQ_*`, padrões de chamada/timeout/fallback) e criar **módulo dedicado de intent** com **schema Pydantic e prompt próprios** para extração de parâmetros de busca — **sem acoplar** ao pipeline de extração de vagas (`app/services/extraction/*` de jobs). Fronteira de reuso: utilitários/cliente/config, domínio isolado e testável.
- **D-14:** Garantia de JSON estrito e segurança server-side: **schema Pydantic estrito + `response_format` JSON (structured outputs quando aplicável) + saneamento/normalização pós-parse**. Defaults nulos/seguros; validação de enums/ranges/whitelist; conflitos resolvidos por regra determinística. Prompt tolerante a variações pt-BR e resistente a instruções conflitantes.
- **D-15:** Entrada **vazia, genérica ou sem parâmetros extraíveis** (“me ajuda”, “quero emprego”): retornar **intenção válida “vazia”** com campos nulos e **status/motivos claros** indicando que nada foi extraído/aplicado (permite fallback/orientação controlada na Fase 20, sem inventar e sem erro opaco no contrato).
- **D-16:** **Prompt seguro**: tratar o texto do usuário como **conteúdo não confiável/dados** (delimitação de input, ignorar instruções internas no texto), no espírito do `wrap_untrusted`/delimitação usada no extrator admin.

### OpenCode's Discretion
- Nomes exatos de campos/tipos Pydantic, shape final do JSON (desde que preserve D-01..D-12: entendido vs aplicado, status/motivo por parâmetro, params finais `q/city/sort`).
- Granularidade e valores dos **enums** de modalidade/contrato/senioridade e vocabulário de **reason codes** (padronizado e testável).
- Estratégia de composição/limpeza de `q` (normalização, remoção de ruído, inclusão seletiva de termos não nativos) sem violar D-08.
- Detalhes de reutilização técnica do cliente Groq (retries/repair/timeout) alinhados aos padrões existentes e às necessidades da intenção.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Requisitos e escopo
- `.planning/PROJECT.md` — Core value, constraints (Groq baixo custo, sem fricção/sem login, contatos protegidos), milestone v1.3.
- `.planning/REQUIREMENTS.md` — INT-01..INT-03 (contrato desta fase), API-01..03/UI-01..03/QA-01..03 (consumidores do contrato).
- `.planning/ROADMAP.md` — Phase 19 goal/success criteria e dependências (19→20→21→22).
- `.planning/STATE.md` — Decisões v1.3: LLM só extrai parâmetros; busca determinística reutiliza contrato público; campos não nativos = suporte limitado/aproximado sinalizado.

### Busca pública determinística (alvo do mapeamento)
- `backend/app/api/v1/public.py` — Contrato `GET /api/v1/public/jobs` (`q`, `city`, `sort`, paginação) e modelo `JobPublic`/`JobListResponse` (sem contatos).
- `backend/app/crud/jobs.py` — `list_published(...)` / predicados de busca e ordenação efetivos (equivalência determinística exigida em INT-03/API-01).
- `backend/app/services/cities.py` — `resolve_city`/`CITY_ALIASES` e `resolve_sort` (whitelist SP/RJ/BH/Remoto, slugs/acentos).
- `backend/app/schemas/job.py` — Schemas públicos (`JobPublic`, `JobListResponse`) e regra de não exposição de contato.

### Infra de extração LLM existente (reuso de padrões)
- `backend/app/core/config.py` — Configurações `GROQ_*` e timeouts/caps relevantes.
- `backend/app/services/extraction/client.py` — Padrões de chamada Groq, wrapping/delimitação de input não confiável, cadeia de modelos/fallback.
- `backend/app/services/extraction/extractor.py` — Padrões de grounding/normalização/classificação/robustez (referência, não acoplar domínio de vagas).
- `backend/app/services/extraction/schema.py` — Exemplo de schemas Pydantic estritos para saída LLM.
- `backend/app/api/v1/extract.py` — Exemplo de endpoint admin síncrono com validação/erros pt-BR (contraste: chat-search público será fase 20).

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `app/services/cities.py` (`resolve_city`, `resolve_sort`, `CITY_ALIASES`): whitelist e normalização canônica de cidade/sort — base para mapeamento seguro (D-05/D-06).
- `app/crud/jobs.py` (`list_published`, filtros de `q`/`city`/`sort`): implementação determinística alvo; params aplicados do contrato devem ser equivalentes.
- `app/api/v1/public.py` + `app/schemas/job.py` (`JobPublic`, `JobListResponse`): contrato público sem contatos que a Fase 20 deve preservar.
- Infra Groq/config (`app/core/config.py`, `app/services/extraction/client.py`): cliente, modelos, timeouts e padrões de chamadas estruturadas reutilizáveis para intent (D-13/D-14).
- Padrões de robustez do extrator (`wrap_untrusted`, validação/saneamento, classificação): referência para prompt seguro e pós-processamento, aplicados a um domínio distinto.

### Established Patterns
- Busca pública: filtro por whitelist/normalização + `q` textual sobre `search_text`, ordenação `recentes|antigas`, paginação com `total`; respostas públicas sem contato.
- Extração LLM atual: saída JSON validada com Pydantic, normalização/grounding e classificação com motivos/alertas; tratamento de limites/timeouts.
- Configuração por env (`.env`/settings) e mensagens/erros em pt-BR.

### Integration Points
- Novo módulo de intent (ex.: `app/services/intent/` ou equivalente) consumido pela futura API de chat-search (Fase 20) para produzir: intenção entendida + params aplicados + classificação por campo.
- Mapeamento deve gerar inputs compatíveis com `list_published(session, q=..., city=..., sort=...)` e ser serializável na resposta da Fase 20 junto a `JobPublic`.
- Reuso de config Groq existente; eventuais novos limites/timeouts de intent devem coexistir com caps de extração admin.

</code_context>

<specifics>
## Specific Ideas

- Sem referências externas específicas além dos requisitos/roadmap e do comportamento já existente da busca pública e do extrator admin. Implementação aberta a abordagens padrão desde que respeite as decisões travadas (sem inventar, determinístico, limites explícitos).

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope.

</deferred>

---

*Phase: 19-contrato-de-intencao-e-mapeamento-seguro*
*Context gathered: 2026-11-17*
