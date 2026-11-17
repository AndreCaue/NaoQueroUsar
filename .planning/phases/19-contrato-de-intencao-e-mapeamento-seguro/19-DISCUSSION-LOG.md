# Phase 19: Contrato de intenção e mapeamento seguro - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-11-17
**Phase:** 19-contrato-de-intencao-e-mapeamento-seguro
**Areas discussed:** Schema e campos da intenção, Normalização e mapeamento seguro, Classificação aplicado/ignorado/aproximado, Reuso do pipeline LLM e robustez

---

## Schema e campos da intenção

| Option | Description | Selected |
|--------|-------------|----------|
| Campo único `q` normalizado | Uma string pronta (cargo+keywords) alinhada ao `q` existente; simples e determinístico. | ✓ |
| Separar `cargo` e `keywords[]` e compor `q` | Intenção mais rica, mas exige regra explícita de composição/ordem no mapeamento. | |
| Manter ambos (`q` + campos atômicos) | Mais rastreabilidade para aplicado/aproximado, porém schema/validação maiores. | |

**User's choice:** Campo único `q` normalizado (Recomendado)
**Notes:** Base para mapear em `q` reaproveitando `list_published(q=...)`/`search_text` atual.

| Option | Description | Selected |
|--------|-------------|----------|
| `null`/omitido por padrão | Ausente = não filtrar/não assumir; só preencher se declarado ou claramente implicado. | ✓ |
| Defaults úteis inferidos (ex.: sort recentes) | Pode ajudar UX, mas risco de inventar; exigiria marcar inferência explicitamente. | |
| Você decide por campo | Definir política campo a campo (default seguro implícito vs sempre nulo). | |

**User's choice:** `null`/omitido por padrão (Recomendado)
**Notes:** Alinhado a INT-01/02 (sem inventar).

| Option | Description | Selected |
|--------|-------------|----------|
| `salary_min`/`salary_max` numéricos + `currency` BRL | Normaliza faixas/“k/mil” em números; fácil validar e classificar como aproximado/ignorado no mapeamento. | ✓ |
| Texto livre normalizado em `salary_text` | Preserva expressão original, mas difícil comparar/filtrar e pouco estruturado. | |
| Ambos: números + texto original | Máxima fidelidade/rastreio; mais campos e regras de consistência. | |

**User's choice:** `salary_min`/`salary_max` numéricos + `currency` BRL (Recomendado)
**Notes:** Hoje não há filtro nativo de salário.

| Option | Description | Selected |
|--------|-------------|----------|
| Enums fixos + campo `raw` opcional | Modalidade/contrato/senioridade com validação forte e mapeamento claro. | ✓ |
| Strings livres normalizadas | Flexível para pt-BR variado, mas aumenta ambiguidade e dificulta classificação consistente. | |
| Você decide (OpenCode) | Escolher granularidade dos enums/categorias conforme capacidade real de mapeamento. | |

**User's choice:** Enums fixos + campo `raw` opcional (Recomendado)
**Notes:** Suporte nativo de filtro limitado hoje.

---

## Normalização e mapeamento seguro

| Option | Description | Selected |
|--------|-------------|----------|
| Mapear só variações óbvias/seguras | Siglas/nomes claros e “home office/remoto”→Remoto; sem inferir cidade fora da whitelist. | ✓ |
| Inferência agressiva de cidade/UF/municípios | Tenta resolver mais casos, mas arrisca mapear fora da whitelist/errado. | |
| Você decide (OpenCode) | Definir tabela de aliases e regra para cidade nula vs mapeada vs aproximada. | |

**User's choice:** Mapear só variações óbvias/seguras (Recomendado)
**Notes:** Compatível com `resolve_city`/whitelist SP/RJ/BH/Remoto.

| Option | Description | Selected |
|--------|-------------|----------|
| Só inferir quando explícito; senão `null` | Ausência de pedido explícito não força valor (sem inventar preferência). | ✓ |
| Default sempre `recentes` no schema de intenção | Prático, mas registra intenção sem pedido explícito. | |
| Você decide (OpenCode) | Definir gatilhos textuais exatos para `antigas`/`recentes`. | |

**User's choice:** Só inferir quando explícito; senão `null` (Recomendado)
**Notes:** Mapeamento válido `recentes`/`antigas` (`resolve_sort`).

| Option | Description | Selected |
|--------|-------------|----------|
| Regra determinística: priorizar o mais específico/seguro e sinalizar conflito | Nunca aplicar filtros incompatíveis; registrar status/motivo por parâmetro. | ✓ |
| Pedir desambiguação ao usuário (sem executar filtro ambíguo) | Mais correto em alguns casos, mas adiciona fluxo conversacional/estado. | |
| Última instrução vence (`last-write-wins`) | Simples, porém pode surpreender e mascarar conflito. | |

**User's choice:** Regra determinística: priorizar o mais específico/seguro e sinalizar conflito (Recomendado)
**Notes:** Ex.: sort conflitante → não aplicado/ignorado; cidade whitelist explícita vence ambiguidade.

| Option | Description | Selected |
|--------|-------------|----------|
| Incluir termos textuais relevantes em `q` e marcar como aproximado quando aplicável | Aproveita `search_text` para recall textual; explicita ausência de filtro estruturado. | ✓ |
| Nunca promover não nativos para `q`, só relatar ignorado/solicitado | Evita resultados enganadores, mas perde utilidade prática. | |
| Você decide por tipo de termo (OpenCode) | Política fina (ex.: keywords/senioridade em `q`; salário numérico não). | |

**User's choice:** Incluir termos textuais relevantes em `q` e marcar como aproximado quando aplicável (Recomendado)
**Notes:** Sem afirmar filtragem nativa inexistente.

---

## Classificação aplicado/ignorado/aproximado

| Option | Description | Selected |
|--------|-------------|----------|
| Status por campo + motivo curto | `{valor entendido, valor aplicado, status aplicado|ignorado|aproximado, reason}` verificável. | ✓ |
| Só lista de campos em 3 buckets | Simples, mas perde granularidade por parâmetro. | |
| Você decide (OpenCode) | Formato exato desde que preserve status verificável e motivo. | |

**User's choice:** Status por campo + motivo curto (Recomendado)
**Notes:** Base para UI/API das fases seguintes.

| Option | Description | Selected |
|--------|-------------|----------|
| Aproximado se influenciou `q`/estratégia textual; ignorado se não pôde ser usado | Critério explícito, sem prometer filtragem. | ✓ |
| Marcar quase tudo não nativo como aproximado | Pode soar como filtro aplicado indevidamente. | |
| Marcar quase tudo não nativo como ignorado | Conservador, mas subestima valor quando termos foram usados em `q`. | |

**User's choice:** Aproximado se influenciou `q`/estratégia textual; ignorado se não pôde ser usado (Recomendado)
**Notes:** “Remoto” pode ser aplicado como cidade se mapeado à whitelist.

| Option | Description | Selected |
|--------|-------------|----------|
| Sim: separar “entendido” e “aplicado” | Expõe params finais (`q`, `city`, `sort`) para auditar equivalência determinística. | ✓ |
| Só “entendido” com status, sem params finais explícitos | Dificulta auditar o que realmente rodou na busca. | |
| Você decide (OpenCode) | Incluir params aplicados finais se necessário para rastreabilidade. | |

**User's choice:** Sim: separar “entendido” e “aplicado” (Recomendado)
**Notes:** Relevante para INT-03 e equivalência na Fase 20.

| Option | Description | Selected |
|--------|-------------|----------|
| Flags/motivos estruturados por campo + aviso agregado | Vocabulário padronizável e testável para suporte parcial. | ✓ |
| Apenas texto livre de aviso no nível da resposta | Difícil de validar/testar e inconsistente. | |
| Você decide (OpenCode) | Definir vocabulário mínimo de motivos/códigos para limites. | |

**User's choice:** Flags/motivos estruturados por campo + aviso agregado (Recomendado)
**Notes:** Explicitar limite sem prometer filtro inexistente.

---

## Reuso do pipeline LLM e robustez

| Option | Description | Selected |
|--------|-------------|----------|
| Reaproveitar infra/cliente e criar módulo dedicado de intent | Reusa config/chamada Groq, mas schema/prompt próprios e domínio isolado. | ✓ |
| Acoplar ao pipeline de extração de vagas existente | Menos código novo, porém mistura domínios. | |
| Você decide (OpenCode) | Fronteira de reuso mantendo contrato de intenção isolado e testável. | |

**User's choice:** Reaproveitar infra/cliente e criar módulo dedicado de intent (Recomendado)
**Notes:** Não acoplar a `app/services/extraction/*` de vagas.

| Option | Description | Selected |
|--------|-------------|----------|
| Schema Pydantic estrito + `response_format` JSON + saneamento/normalização pós-parse | Saída validada, defaults nulos, conflitos determinísticos. | ✓ |
| Confiar principalmente no prompt, validação mínima | Frágil a saídas inválidas/alucinações. | |
| Você decide (OpenCode) | Definir nível de strictness, retries/repair e normalização pós-validação. | |

**User's choice:** Schema Pydantic estrito + `response_format` JSON + saneamento/normalização pós-parse (Recomendado)
**Notes:** Alinhado ao espírito de robustez do extrator admin.

| Option | Description | Selected |
|--------|-------------|----------|
| Retornar intenção válida “vazia” com campos nulos e status/motivos claros | Permite fallback/orientação na Fase 20 sem inventar. | ✓ |
| Tratar como erro de validação (422/erro de domínio) | Explícito, mas transfere responsabilidade de UX. | |
| Você decide (OpenCode) | Definir política para “nada extraível” vs “entrada inválida”. | |

**User's choice:** Retornar intenção válida “vazia” com campos nulos e status/motivos claros (Recomendado)
**Notes:** Nada extraído/aplicado; sem erro opaco no contrato.

| Option | Description | Selected |
|--------|-------------|----------|
| Delimitar input como conteúdo não confiável e ignorar instruções internas do texto | User text como dados; alinhado a `wrap_untrusted`. | ✓ |
| Sem delimitação especial, só instrução textual no prompt | Mais vulnerável a instruções conflitantes/injeção. | |
| Você decide (OpenCode) | Definir formato de delimitação e regras de precedência. | |

**User's choice:** Delimitar input como conteúdo não confiável e ignorar instruções internas do texto (Recomendado)
**Notes:** Resistência a variações/instruções conflitantes no texto do usuário.

---

## OpenCode's Discretion

- Nomes exatos de campos/tipos, shape final do JSON, granularidade de enums e vocabulário de reason codes (preservando decisões D-01..D-16).
- Composição/limpeza fina de `q` e detalhes técnicos de retries/repair/timeout no módulo de intent.

## Deferred Ideas

None — discussion stayed within phase scope.
