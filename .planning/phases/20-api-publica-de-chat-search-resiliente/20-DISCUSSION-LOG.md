# Phase 20: API pública de chat-search resiliente - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-11-17
**Phase:** 20-api-publica-de-chat-search-resiliente
**Areas discussed:** Contrato do endpoint e resposta, Proteções e limites operacionais, Fallback e degradação do LLM, Suporte parcial e filtros não nativos

---

## Contrato do endpoint e resposta

| Option | Description | Selected |
|--------|-------------|----------|
| POST JSON em `/public/chat-search` (Recomendado) | Request com mensagem em body JSON (+ paginação), alinhado a texto livre e proteções de tamanho; resposta com interpretação + resultados. | ✓ |
| POST em `/public/jobs/search` com body JSON | Mesmo modelo sob namespace de jobs, menos explícito para chat/intenção. | |
| GET com query params (`q_text`/`message`, `page`, `limit`) | Estilo próximo a `/public/jobs`, mas frágil para mensagem NL longa (tamanho/encoding/cache/proxies). | |

**User's choice:** POST JSON em `/public/chat-search` (Recomendado)
**Notes:** Endpoint público do board, sem auth, entrada principal é mensagem em linguagem natural.

| Option | Description | Selected |
|--------|-------------|----------|
| Envelope completo: intent + paginação + items (Recomendado) | `interpretation` (understood, field_statuses, applied_params, limitations, meta?) + `results` ({items: JobPublic[], page, limit, total}), preservando contrato público sem contatos. | ✓ |
| Retornar IntentContract “achatado” no topo + items/page/limit/total | Mistura domínios no nível raiz; mapeamento completo ainda necessário. | |
| Interpretation resumida + resultados completos | Mais enxuto, mas perde rastreabilidade detalhada aplicado/ignorado/aproximado por campo. | |

**User's choice:** Envelope completo: intent + paginação + items (Recomendado)
**Notes:** Reutiliza semântica de `JobListResponse` em `results` e expõe contrato de intenção para UI.

| Option | Description | Selected |
|--------|-------------|----------|
| Mesmo contrato de paginação do público (Recomendado) | `page` >=1 default 1, `limit` 1–50 default 20; busca via `list_published` com params aplicados para equivalência determinística e `total` coerente. | ✓ |
| Sem paginação no chat (sempre primeira página/top N) | Mais simples, porém não atende bem contrato paginável/total de API-01. | |
| Cursor/offset próprio diferente do público | Adiciona complexidade e foge da consistência com busca pública existente. | |

**User's choice:** Mesmo contrato de paginação do público (Recomendado)
**Notes:** Alinhado a `GET /api/v1/public/jobs`.

| Option | Description | Selected |
|--------|-------------|----------|
| Expor contrato completo do intent (Recomendado) | `understood`, `field_statuses` por campo, `applied_params` finais, `limitations`/avisos — server-authoritative (Fase 19). | ✓ |
| Só `applied_params` + `limitations` resumidas | Menos detalhe para explicar motivos por campo; enfraquece transparência. | |
| Incluir também confiança/score do LLM por campo | Não definido no contrato atual; risco de complexidade/falsa precisão. | |

**User's choice:** Expor contrato completo do intent (Recomendado)
**Notes:** Garante auditabilidade e evita inventar suporte.

---

## Proteções e limites operacionais

| Option | Description | Selected |
|--------|-------------|----------|
| Limite dedicado por env para chat (Recomendado) | Novo knob (ex.: `CHAT_SEARCH_RATE_LIMIT`) por IP+endpoint, independente de reveal/login; reusa limiter/memória/429 pt-BR+Retry-After. | ✓ |
| Reusar o mesmo limite/config do reveal | Simples, mas acopla políticas e custo de fluxos diferentes. | |
| Limite fixo hardcoded no código | Menos operável; difícil ajustar sem mudança de código. | |

**User's choice:** Limite dedicado por env para chat (Recomendado)
**Notes:** Controle de abuso/custo sintonizável.

| Option | Description | Selected |
|--------|-------------|----------|
| Limite curto e estrito no schema (Recomendado) | `message` obrigatória/trim com faixa curta (~1..300/500 chars), validação → 4xx pt-BR seguro. | ✓ |
| Limite mais alto (ex.: 1000–2000 chars) | Mais custo/latência e superfície de abuso sem benefício claro para MVP. | |
| Sem limite explícito de tamanho (apenas timeout) | Risco de custo/DoS; não atende “limites de tamanho”. | |

**User's choice:** Limite curto e estrito no schema (Recomendado)
**Notes:** Consultas do MVP são frases curtas.

| Option | Description | Selected |
|--------|-------------|----------|
| Timeout dedicado e curto para chat (Recomendado) | Setting próprio (desacoplado de `GROQ_TIMEOUT_SECONDS`), timeout curto → fallback controlado. | ✓ |
| Reusar `GROQ_TIMEOUT_SECONDS` global | Tuning conflita entre admin e chat público. | |
| Sem timeout próprio (depender só de infra/proxy) | Menos controle e risco de respostas lentas/opacas. | |

**User's choice:** Timeout dedicado e curto para chat (Recomendado)
**Notes:** Prioridade para resposta rápida no endpoint público.

| Option | Description | Selected |
|--------|-------------|----------|
| Validação 4xx, LLM degradado via fallback 200, interno 500 genérico (Recomendado) | 400/422 pt-BR para input inválido; 429 padrão; falha/timeout LLM → 200 com fallback/orientação; 500 genérico sem vazar detalhes. | ✓ |
| Retornar 503/502 quando LLM falhar, com mensagem pt-BR | Erro opaco ao usuário em vez de fallback utilizável. | |
| Propagar detalhes do erro do provedor no `detail` (debug) | Vaza detalhes internos/terceiros; inaceitável em endpoint público. | |

**User's choice:** Validação 4xx, LLM degradado via fallback 200, interno 500 genérico (Recomendado)
**Notes:** Erros seguros e experiência sem fricção.

---

## Fallback e degradação do LLM

| Option | Description | Selected |
|--------|-------------|----------|
| Intenção degradada + sem resultados automáticos + orientação (Recomendado) | `applied_params` nulos, `results` vazio, orientação para busca manual/keywords; evita vagas irrelevantes. | ✓ |
| Intenção degradada + busca ampla padrão (recentes) + orientação | Pode confundir como resultado interpretado; precisa sinalização forte. | |
| Tentar fallback heurístico simples (keywords) sem LLM e buscar | Lógica paralela e risco de inconsistência/complexidade. | |

**User's choice:** Intenção degradada + sem resultados automáticos + orientação (Recomendado)
**Notes:** Parser já degrada para intenção segura em falhas.

| Option | Description | Selected |
|--------|-------------|----------|
| Sinalizar causa no contrato via `meta`/`limitations` e motivos (Recomendado) | Diferenciar `llm_unavailable`/`timeout` vs `no_extractable_params`/`empty_input` com flags/motivos estruturados; 200 controlado. | ✓ |
| Usar HTTP diferente (200 vazio vs 503) para diferenciar | Conflita com fallback controlado sem erro opaco; complica cliente. | |
| Mensagem de orientação única genérica para todos os casos | Menos útil para reformular vs tentar depois. | |

**User's choice:** Sinalizar causa no contrato via `meta`/`limitations` e motivos (Recomendado)
**Notes:** Permite orientação específica por cenário.

| Option | Description | Selected |
|--------|-------------|----------|
| Campo de orientação pt-BR explícito na interpretação (Recomendado) | `meta.guidance`/limitações textualizadas prontas para exibição + códigos estruturados. | ✓ |
| Apenas códigos/flags estruturados, sem texto pronto | API menos autoexplicativa; risco de inconsistência na UI. | |
| Orientação só em HTTP/status ou header | Pouca nuance para resposta 200 rica. | |

**User's choice:** Campo de orientação pt-BR explícito na interpretação (Recomendado)
**Notes:** Consistência para consumo na Fase 21.

| Option | Description | Selected |
|--------|-------------|----------|
| Priorizar resposta rápida com fallback controlado (Recomendado) | Respeitar timeout curto; evitar retries longos/agressivos; devolver degradação 200 se não houver interpretação a tempo. | ✓ |
| Tentar exaustivamente toda cadeia de modelos/retries antes de falhar | Pode estourar latência/custo e piorar UX pública. | |
| Falhar rápido com erro 5xx/503 em qualquer problema de LLM | Ignora fallback controlado exigido. | |

**User's choice:** Priorizar resposta rápida com fallback controlado (Recomendado)
**Notes:** Cadeia de modelos/repair só dentro do orçamento.

---

## Suporte parcial e filtros não nativos

| Option | Description | Selected |
|--------|-------------|----------|
| Somente aproximação via `q` mapeado + sinalização (Recomendado) | Usa `applied_params.q`/status do intent e busca determinística normal; sem pós-filtro por salário/modalidade/contrato/senioridade. | ✓ |
| `q` mapeado + pós-filtro leve em janela candidata limitada | Pode melhorar precisão, mas adiciona complexidade e risco sobre `total`/falsos negativos; exige cuidado. | |
| Rejeitar/ignorar totalmente esses filtros (sem usar em `q`) | Desperdiça sinal útil e piora relevância para exemplos MVP. | |

**User's choice:** Somente aproximação via `q` mapeado + sinalização (Recomendado)
**Notes:** Consistente com D-08/D-10 da Fase 19 e API-03.

| Option | Description | Selected |
|--------|-------------|----------|
| Aviso agregado claro quando houver aproximação/limite (Recomendado) | `limitations`/mensagem pt-BR agregada quando campo aproximado/ignorado por falta de suporte nativo, além de motivos por campo. | ✓ |
| Confiar só em `field_statuses` por campo, sem aviso agregado | Risco de usuário assumir filtragem garantida. | |
| Adicionar flag booleana simples `partial_support: true/false` apenas | Insuficiente sem explicar o quê/por quê (pode ser complementar). | |

**User's choice:** Aviso agregado claro quando houver aproximação/limite (Recomendado)
**Notes:** Transparência explícita (ex.: salário não filtrado numericamente).

| Option | Description | Selected |
|--------|-------------|----------|
| Aproximação por palavras-chave extraídas em `q` + limitação explícita (Recomendado) | “Vagas parecidas” tratadas por termos textuais quando possível; sinalizar ausência de similaridade semântica/vetorial garantida. | ✓ |
| Não tentar e orientar reformulação para termos concretos | Mais honesto, porém menos útil quando há descrição aproveitável. | |
| Prometer vagas parecidas com ranking especial no backend atual | Exige capacidade inexistente; violaria suporte limitado/sinalizado. | |

**User's choice:** Aproximação por palavras-chave extraídas em `q` + limitação explícita (Recomendado)
**Notes:** Abordagem limitada/seed conforme suportado (QA-01).

| Option | Description | Selected |
|--------|-------------|----------|
| Aplicar só partes suportadas com segurança e sinalizar o resto (Recomendado) | Cidade fora da whitelist (ex.: Campinas) nunca mapeada para SP/RJ/BH; aplicar suportado (ex.: Remoto) quando aplicável, usar termos úteis em `q` se apropriado e marcar restante ignorado/aproximado com motivo. | ✓ |
| Ignorar cidade inteira se qualquer parte for fora da whitelist | Pode descartar parte suportada válida (“remoto”), piorando recall. | |
| Forçar mapeamento de Campinas para São Paulo (ou mais próximo) | Inferência agressiva proibida; retornos incorretos. | |

**User's choice:** Aplicar só partes suportadas com segurança e sinalizar o resto (Recomendado)
**Notes:** Exemplo MVP: “analista de dados Campinas ou remoto 6-10k” — remoto aplicável, Campinas/salário com suporte parcial e sinalização.

---

## OpenCode's Discretion

Nomes exatos de campos JSON/request-response, shape final de `meta`/guidance, valores/nome exatos de envs (rate limit/timeout/tamanho), copy pt-BR exata de validações/guidance/limitações, organização interna do endpoint e detalhes de budget de retries/cadeia dentro do timeout — desde que respeitem as decisões travadas.

## Deferred Ideas

None — discussion stayed within phase scope.
