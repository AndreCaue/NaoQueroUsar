# 22 — MVP Examples (QA-01)

**Phase:** 22-qualidade-hardening-e-valida-o-operacional  
**Requisitos:** QA-01 (principal), suporte QA-02/QA-03  
**Data:** 2026-11-18  
**Escopo:** matriz versionada dos 5 exemplos-alvo do MVP com **Contrato esperado + Resultado observado**, evidências rastreáveis e lacunas explícitas, sem afirmar capacidades não suportadas.

## Notas de contrato (fatos)

- **Busca determinística:** `POST /api/v1/public/chat-search` mapeia intenção de forma server-authoritative e consulta `list_published(...)` com `applied_params` efetivos (`q`, `city` whitelist, `sort` explícito). Equivalência de resultados/`total` deve ser comparada a `GET /api/v1/public/jobs` para os mesmos parâmetros aplicados.
- **Privacidade:** resultados do chat usam apenas `JobPublic` (sem `contact_email`/`contact_phone`); revelação de contato permanece no fluxo canônico.
- **Filtros nativos suportados (aplicação determinística):** `q` textual, `city` apenas whitelist (`São Paulo`, `Rio de Janeiro`, `Belo Horizonte`, `Remoto`) e `sort` apenas quando explícito (`recentes`/`antigas`). Demais campos não possuem filtro estruturado/nativo garantido.
- **"Vagas parecidas com uma vaga":** tratado como **seed textual limitado** (termos extraídos para `q` conforme contrato atual), **sem similaridade semântica/vetorial e sem suporte a seed por link/ID de vaga**. Deve sinalizar aproximação/limite.
- **Campinas:** fora da whitelist suportada (`São Paulo`, `Rio de Janeiro`, `Belo Horizonte`, `Remoto`) -> não inferida/aplicada como cidade (`not_in_whitelist`/ignorada) e deve ser sinalizada.
- **Campos não nativos aproximados/sinalizados:** `salário`, `modalidade`, `tipo de contrato`, `senioridade` não possuem filtragem estruturada/nativa garantida; podem ser apenas entendidos, aproximados textualmente em `q` e/ou sinalizados (`textual_approximation_in_q`, `unsupported_structured_filter`, `non_native_fields_limited`), nunca afirmar filtragem inexistente.

## Evidências automatizadas rastreáveis

| Evidência | Arquivo / caso | Cobertura | Resultado observado (execução) |
|---|---|---|---|
| Mapper MVP 1 | `backend/tests/test_intent_mapper.py::test_mvp_dev_pleno_sp_salary_not_native` | SP whitelist, `salary` `unsupported_structured_filter`, senioridade aproximada/textual em `q` | PASS (suite intent pura, `python -m pytest -q tests/test_intent_schema.py tests/test_intent_mapper.py tests/test_intent_parser.py tests/test_intent_client.py`) |
| Mapper MVP 2 | `backend/tests/test_intent_mapper.py::test_mvp_remoto_frontend_react_clt_textual_approximation` | Remoto aplicado com segurança, React/CLT como aproximação textual em `q` (campos não nativos não garantidos) | PASS (suite intent pura) |
| Mapper MVP 3 | `backend/tests/test_intent_mapper.py::test_mvp_parecidas_com_vaga_seed_textual_limitado_sem_link_id` | "parecidas" = seed textual em `q` apenas; sem semântica/vetor/link/ID | PASS (suite intent pura) |
| Mapper MVP 4 | `backend/tests/test_intent_mapper.py::test_mvp_analista_dados_campinas_ou_remoto_salary_combo` | `Campinas` `not_in_whitelist`/ignorada, combinação com remoto/salário sinalizada por campo conforme contrato | PASS (suite intent pura) |
| Mapper MVP 5 | `backend/tests/test_intent_mapper.py::test_mvp_estagio_marketing_digital_em_sp` | SP whitelist aplicada, termos de estágio/marketing/digital refletidos sem filtros inventados | PASS (suite intent pura) |
| API chat-search MVP 1 | `backend/tests/test_chat_search_api.py::test_mvp_dev_pleno_sp_salary_equivalence_and_no_contacts` | Interpretação + equivalência a `GET /api/v1/public/jobs` (`applied_params`), `JobPublic` sem contatos, salário não nativo | PASS (`python -m pytest -q tests/test_chat_search_api.py tests/test_ratelimit.py`, ambiente com DB de testes) |
| API chat-search MVP 2 | `backend/tests/test_chat_search_api.py::test_mvp_remoto_frontend_react_clt_textual_approximation` | Remoto/termos textuais, equivalência determinística, sem contatos | PASS (suíte DB-backed) |
| API chat-search MVP 3 | `backend/tests/test_chat_search_api.py::test_mvp_parecidas_seed_textual_limitado_no_semantic_link_id` | Seed textual limitado em `q`, sem semântica/vetor/link/ID, resposta segura | PASS (suíte DB-backed) |
| API chat-search MVP 4 | `backend/tests/test_chat_search_api.py::test_mvp_campinas_ou_remoto_salary_partial_support_signaled` | `Campinas` não aplicada (`not_in_whitelist`), salário não nativo, suporte parcial sinalizado, sem contatos | PASS (suíte DB-backed) |
| API chat-search MVP 5 | `backend/tests/test_chat_search_api.py::test_mvp_estagio_marketing_digital_sp_equivalence` | SP aplicada + equivalência determinística, sem contatos | PASS (suíte DB-backed) |
| Contratos críticos existentes | `backend/tests/test_chat_search_api.py` (degradação, privacidade, rate limit, disabled/logging), `backend/tests/test_ratelimit.py` | Privacidade (`JobPublic` sem contatos), timeout/`llm_unavailable`/`no_extractable_params`, `chat_disabled`, limites/rate limit | PASS (suíte DB-backed executada neste ambiente; intent/rate-limit puros também verificados) |

> Execuções automatizadas observadas neste ambiente: suites intent puras (30 passed) e suites DB-backed chat/rate-limit (33 passed), com LLM mockado e sem chamadas externas. Em ambientes sem DB de testes configurado/migrado, a execução DB-backed permanece dependente de pré-requisito.

> Observação: execuções DB-backed não foram afirmadas como concluídas sem ambiente. Os casos MVP de API estão implementados como testes determinísticos com `extract_and_map_intent` mockado e devem ser executados em ambiente com banco de testes migrado.

**Atualização de rastreabilidade (22-04, gap closure; revalidação manual pendente):** correção determinística para reconhecimento de cidade suportada cadastrada — toolbar/manual promove texto exato (label/slug/canônico/alias, case/acento-insensível) para `city=<slug>` (`frontend/lib/cities.ts` `resolveCitySlugFromText`, `frontend/components/board/BoardToolbar.tsx`, `frontend/lib/cities.test.ts`) e mapper aplica fallback seguro em `raw_text` para SP/RJ/BH/Remoto quando `candidate.city` ausente, com salvaguarda de conflito multi-cidade (`backend/app/services/intent/mapper.py` `_detect_city_from_raw_text`, `backend/tests/test_intent_mapper.py`; regressão `backend/tests/test_intent_parser.py`). Limites MVP permanecem inalterados: **Campinas** continua fora da whitelist (`not_in_whitelist`), campos não nativos (salário/modalidade/tipo de contrato/senioridade) continuam sem filtragem estruturada/nativa garantida (apenas aproximação/sinalização conforme contrato), e "parecidas com uma vaga" permanece **seed textual limitado** em `q` sem similaridade semântica/vetorial e sem seed por link/ID. Revalidação runtime/integrada do caso reportado segue pendente em `22-HUMAN-UAT.md`/`22-MANUAL-UAT.md`.

---

## 1) `dev pleno SP salário >= 8k`

### Entrada (mensagem)
- `dev pleno SP salário >= 8k`

### Interpretação esperada
- **`understood`:** intenção de vaga dev, senioridade pleno, cidade SP, salário mínimo ~8000 BRL.
- **`applied_params` esperados:** `city = "São Paulo"` (whitelist/normalização segura), `q` textual aplicado com termos úteis (ex.: `dev`, `pleno`) conforme composição determinística, `sort = null` (não explícito).
- **`field_statuses`/motivos relevantes:**
  - `city`: `aplicado` (normalizado para whitelist).
  - `seniority`: `aproximado` com `reason_code = "textual_approximation_in_q"` (sem filtro estruturado nativo garantido).
  - `salary`: `ignorado` com `reason_code = "unsupported_structured_filter"` e `applied = null` (nunca filtro salarial nativo).
  - `sort`: `ignorado` (`not_explicit`) se não houver pedido explícito.
- **Limitações/`meta.guidance` esperadas:** suporte parcial/não nativo para salário/senioridade sinalizado (`non_native_fields_limited`, `unsupported_structured_filter`, `textual_approximation_in_q` conforme aplicável); sem afirmar filtragem salarial inexistente.

### Resultados esperados
- Busca determinística equivalente a `GET /api/v1/public/jobs` para os `applied_params` efetivos (ex.: `q` aplicado, `city=sao-paulo`, `sort=recentes` default quando `sort` não aplicado).
- Resposta com `results.items` como `JobPublic` sem `contact_email`/`contact_phone`, com `page/limit/total` consistentes.
- Nenhum filtro salarial estruturado aplicado.

### Lacunas explícitas
- Faixa salarial **não** possui filtro nativo/garantido (apenas entendida/sinalizada).
- Senioridade **não** é filtro estruturado nativo garantido (apenas aproximação textual em `q` quando aplicável).

### Contrato esperado + Resultado observado
- **Contrato esperado:** cidade SP aplicada com segurança; salário entendido porém não aplicado como filtro estruturado; senioridade aproximada textualmente; resultados equivalentes ao board público sem contatos.
- **Resultado observado:** contrato de mapeamento determinístico validado por `backend/tests/test_intent_mapper.py::test_mvp_dev_pleno_sp_salary_not_native` (PASS, suite intent pura). Equivalência/privacidade de API validada por `backend/tests/test_chat_search_api.py::test_mvp_dev_pleno_sp_salary_equivalence_and_no_contacts` (PASS, suíte DB-backed com LLM mockado).

### Evidência
- `backend/tests/test_intent_mapper.py` (`test_mvp_dev_pleno_sp_salary_not_native`)
- `backend/tests/test_chat_search_api.py` (`test_mvp_dev_pleno_sp_salary_equivalence_and_no_contacts`, mock de `extract_and_map_intent`)

---

## 2) `remoto frontend React preferência CLT`

### Entrada (mensagem)
- `remoto frontend React preferência CLT`

### Interpretação esperada
- **`understood`:** preferência remota, termos de tecnologia (React/frontend) e preferência contratual CLT.
- **`applied_params` esperados:** `city = "Remoto"` quando mapeável com segurança pela whitelist/comportamento suportado; `q` textual com termos relevantes (ex.: `frontend`, `React`, `CLT`) conforme aproximação textual determinística; `sort = null` se não explícito.
- **`field_statuses`/motivos relevantes:**
  - `city` e/ou `work_mode`: aplicação segura de remoto conforme contrato (ex.: cidade `Remoto` na whitelist e sinalização coerente de modalidade quando aplicável).
  - `contract_type` (CLT): `aproximado` com `reason_code = "textual_approximation_in_q"` quando influenciar `q` (sem filtro contratual nativo garantido).
  - `salary`: ausente/não aplicável.

### Resultados esperados
- Resultados determinísticos equivalentes a `GET /api/v1/public/jobs` para `applied_params` efetivos (ex.: `city=remoto`, `q` aplicado, `sort=recentes` default).
- `JobPublic` sem contatos; paginação/total consistentes.

### Lacunas explícitas
- Modalidade e tipo de contrato **não** são filtros estruturados nativos garantidos; podem ser apenas aproximados textualmente em `q` e/ou sinalizados.
- "Preferência CLT" não implica filtragem contratual garantida.

### Contrato esperado + Resultado observado
- **Contrato esperado:** remoto aplicado com segurança quando suportado; React/CLT refletidos como busca/aproximação textual sem prometer filtro nativo de contrato/modalidade além do contrato atual.
- **Resultado observado:** mapeamento determinístico validado por `backend/tests/test_intent_mapper.py::test_mvp_remoto_frontend_react_clt_textual_approximation` (PASS, suite intent pura). Equivalência/privacidade de API validada por `backend/tests/test_chat_search_api.py::test_mvp_remoto_frontend_react_clt_textual_approximation` (PASS, suíte DB-backed com LLM mockado).

### Evidência
- `backend/tests/test_intent_mapper.py` (`test_mvp_remoto_frontend_react_clt_textual_approximation`)
- `backend/tests/test_chat_search_api.py` (`test_mvp_remoto_frontend_react_clt_textual_approximation`)

---

## 3) `vagas parecidas com uma vaga`

### Entrada (mensagem)
- `vagas parecidas com uma vaga` (consulta NL descrevendo/referenciando vaga de forma textual)

### Interpretação esperada
- **Tratamento obrigatório:** **seed textual limitado** (termos extraídos para `q` conforme contrato atual), **sem similaridade semântica/vetorial e sem suporte a seed por link/ID de vaga**.
- **`applied_params` esperados:** `q` textual derivado de termos extraídos (quando houver) como aproximação; `city = null`, `sort = null` salvo sinal explícito suportado.
- **`field_statuses`/limitações/`meta.guidance`:** deve sinalizar aproximação/limite (não afirmar capacidade semântica, vetorial, por similaridade de vaga, nem por `link/ID`).

### Resultados esperados
- Se houver `q` textual aplicado, busca determinística equivalente a `GET /api/v1/public/jobs` para esse `q` (aproximação textual), com `JobPublic` sem contatos.
- Se não houver parâmetros extraíveis/aplicáveis, resposta degradada segura sem resultados automáticos, com guidance para busca manual (conforme contrato de degradação).

### Lacunas explícitas
- **Não há similaridade semântica/vetorial.**
- **Não há suporte a seed por link/ID de vaga.**
- Qualquer "similaridade" é apenas aproximação textual via `q` (seed textual limitado).

### Contrato esperado + Resultado observado
- **Contrato esperado:** apenas seed textual em `q` (quando possível), com limitações explícitas; nunca afirmar semântica/vetor/link/ID.
- **Resultado observado:** mapeamento determinístico (seed textual em `q`, sem campos/metadados de semântica/link/ID) validado por `backend/tests/test_intent_mapper.py::test_mvp_parecidas_com_vaga_seed_textual_limitado_sem_link_id` (PASS, suite intent pura). Contrato de API (mockado) para seed textual limitado validado por `backend/tests/test_chat_search_api.py::test_mvp_parecidas_seed_textual_limitado_no_semantic_link_id` (PASS, suíte DB-backed com LLM mockado).

### Evidência
- `backend/tests/test_intent_mapper.py` (`test_mvp_parecidas_com_vaga_seed_textual_limitado_sem_link_id`)
- `backend/tests/test_chat_search_api.py` (`test_mvp_parecidas_seed_textual_limitado_no_semantic_link_id`)

---

## 4) `analista de dados Campinas ou remoto 6–10k`

### Entrada (mensagem)
- `analista de dados Campinas ou remoto 6–10k`

### Interpretação esperada
- **`understood`:** cargo/área `analista de dados`, cidades mencionadas `Campinas` e `remoto`, faixa salarial 6–10k.
- **`applied_params` esperados (conforme contrato atual):** `q` textual com termos úteis (ex.: `analista`, `dados`) quando aplicável; `city` **não** aplicada como `Campinas` (fora da whitelist) e, no cenário determinístico coberto (candidato indica cidade `Campinas`), `Remoto` não é promovido automaticamente como cidade aplicada -> `applied_params.city = null`; `sort = null` se não explícito.
- **`field_statuses`/motivos relevantes (por campo):**
  - `city` (`Campinas`): `ignorado` com `reason_code = "not_in_whitelist"` (não aplicada).
  - `salary` (6–10k): `ignorado` com `reason_code = "unsupported_structured_filter"` e `applied = null` (sem filtro salarial nativo).
  - `q`: `aplicado`/normalizado quando houver termos textuais úteis.
  - `work_mode`/modalidade (se entendido como remoto no texto): pode permanecer não aplicado como filtro estruturado ou sinalizado conforme mapeamento determinístico; combinação deve explicitar que não há garantia de filtragem nativa de modalidade além do suporte de cidade whitelist.
- **Limitações/`meta.guidance` esperadas:** suporte parcial/combinação com lacunas sinalizadas (ex.: `not_in_whitelist`, `unsupported_structured_filter`, e/ou limitações de campos não nativos conforme contrato).

### Resultados esperados
- Busca determinística equivalente a `GET /api/v1/public/jobs` para `applied_params` efetivos (sem cidade Campinas aplicada; sem filtro salarial nativo; `q` aplicado quando houver).
- `JobPublic` sem contatos; `page/limit/total` consistentes.
- Sem resultados automáticos garantidos para "Campinas" como filtro de cidade suportado.

### Lacunas explícitas
- **`Campinas` fora da whitelist suportada** (`São Paulo`, `Rio de Janeiro`, `Belo Horizonte`, `Remoto`) -> `not_in_whitelist`/ignorada e sinalizada.
- **Faixa salarial 6–10k** não possui filtragem estruturada/nativa garantida.
- Combinação "Campinas ou remoto": o contrato atual não garante seleção automática segura da alternativa remota como filtro de cidade quando a cidade candidata não é whitelisted; comportamento deve ser lido por campo (aplicado vs ignorado/aproximado/sinalizado), sem inventar filtro.

### Contrato esperado + Resultado observado
- **Contrato esperado:** `Campinas` rejeitada por whitelist (`not_in_whitelist`), salário não nativo ignorado, termos textuais aplicáveis em `q`, limitações explícitas por campo.
- **Resultado observado:** mapeamento determinístico validado por `backend/tests/test_intent_mapper.py::test_mvp_analista_dados_campinas_ou_remoto_salary_combo` (PASS, suite intent pura) cobrindo `not_in_whitelist` e salário não nativo sem filtros inventados. Resposta/contrato de API para combinação e sinalização de suporte parcial validado por `backend/tests/test_chat_search_api.py::test_mvp_campinas_ou_remoto_salary_partial_support_signaled` (PASS, suíte DB-backed com LLM mockado).

### Evidência
- `backend/tests/test_intent_mapper.py` (`test_mvp_analista_dados_campinas_ou_remoto_salary_combo`)
- `backend/tests/test_chat_search_api.py` (`test_mvp_campinas_ou_remoto_salary_partial_support_signaled`)

---

## 5) `estágio marketing digital em SP`

### Entrada (mensagem)
- `estágio marketing digital em SP`

### Interpretação esperada
- **`understood`:** estágio em marketing digital na cidade SP.
- **`applied_params` esperados:** `city = "São Paulo"` (whitelist), `q` textual com termos como `estágio`/`marketing`/`digital` conforme mapeamento suportado, `sort = null` se não explícito.
- **`field_statuses`/motivos relevantes:**
  - `city`: `aplicado` (normalizado para whitelist).
  - `seniority` (estágio): pode ser entendido e refletido como aproximação textual em `q` (`aproximado`, `textual_approximation_in_q`) ou conforme regra determinística aplicável, **sem filtro estruturado nativo garantido**.
  - Demais campos não informados/não aplicáveis: `ignorado` com motivo claro.

### Resultados esperados
- Busca determinística equivalente a `GET /api/v1/public/jobs` para `applied_params` efetivos (`q` aplicado, `city=sao-paulo`, `sort=recentes` default).
- `JobPublic` sem contatos; paginação/total consistentes.

### Lacunas explícitas
- Senioridade/nível (ex.: estágio) não possui filtro estruturado nativo garantido; uso textual é aproximação/sinalização, não filtragem nativa garantida.

### Contrato esperado + Resultado observado
- **Contrato esperado:** SP aplicada com segurança; termos de estágio/marketing/digital refletidos no entendimento/`q` suportado sem inventar filtros.
- **Resultado observado:** mapeamento determinístico validado por `backend/tests/test_intent_mapper.py::test_mvp_estagio_marketing_digital_em_sp` (PASS, suite intent pura). Equivalência/privacidade de API validada por `backend/tests/test_chat_search_api.py::test_mvp_estagio_marketing_digital_sp_equivalence` (PASS, suíte DB-backed com LLM mockado).

### Evidência
- `backend/tests/test_intent_mapper.py` (`test_mvp_estagio_marketing_digital_em_sp`)
- `backend/tests/test_chat_search_api.py` (`test_mvp_estagio_marketing_digital_sp_equivalence`)

---

## Resumo de lacunas obrigatórias (QA-01)

- **"parecidas com uma vaga"** = **seed textual limitado** em `q`; **sem similaridade semântica/vetorial e sem suporte a seed por link/ID de vaga**.
- **`Campinas`** fora da whitelist (`São Paulo`, `Rio de Janeiro`, `Belo Horizonte`, `Remoto`) -> `not_in_whitelist`/ignorada e sinalizada.
- **`salário`, `modalidade`, `tipo de contrato`, `senioridade`**: sem filtragem estruturada/nativa garantida; apenas entendimento/aproximação textual em `q` e/ou sinalização, nunca afirmar filtragem inexistente.
- **Combinações** (ex.: Campinas ou remoto 6–10k): avaliar e documentar **por campo** o que é aplicado vs ignorado/aproximado conforme contrato determinístico atual.
