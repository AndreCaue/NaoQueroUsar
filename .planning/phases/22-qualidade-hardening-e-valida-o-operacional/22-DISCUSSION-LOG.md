# Phase 22: Qualidade, hardening e validação operacional - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-11-17
**Phase:** 22-qualidade-hardening-e-valida-o-operacional
**Areas discussed:** Validação dos exemplos MVP (QA-01), Suíte automatizada e E2E/UI viável (QA-02), Controles operacionais e kill-switch (QA-03)

---

## Validação dos exemplos MVP (QA-01)

| Option | Description | Selected |
|--------|-------------|----------|
| Híbrido: matriz + testes-alvo (Recomendado) | Criar uma matriz versionada em `.planning/phases/22-...` descrevendo entrada/interpretação esperada/aplicado-ignorado-aproximado/limitações e, quando determinístico, cobrir os casos com testes automatizados (intent/chat com LLM mockado/fixtures). Dá evidência legível e regressão executável. | ✓ |
| Matriz documental como evidência principal | Focar em um documento de validação detalhado (roteiro + resultados esperados/observados e lacunas) para os 5 exemplos; automação só onde já existir ou for trivial. Menos garantia de regressão, mais leve de executar no ambiente atual. | |
| Testes automatizados como evidência principal | Codificar os exemplos-alvo como casos de teste/fixtures executáveis (mockando LLM) e registrar lacunas em asserts/saída; documentação mínima de apoio. Forte contra regressão, mas pode ser menos legível para revisão operacional. | |

**User's choice:** Híbrido: matriz + testes-alvo (Recomendado)
**Notes:** Evidência deve cobrir os 5 exemplos-alvo do MVP com combinações e lacunas explícitas.

| Option | Description | Selected |
|--------|-------------|----------|
| Seed textual + limitação explícita (Recomendado) | Validar como consulta em linguagem natural que descreve/referencia uma vaga (termos extraídos para `q`), documentando/testando que não há busca vetorial/semântica e que a resposta sinaliza aproximação/limite. Sem suporte a link/ID de vaga como seed nesta fase. | ✓ |
| Cobrir variações textuais e registrar “não suportado” para seed por vaga/link | Validar apenas o melhor esforço via texto descritivo e marcar explicitamente como lacuna qualquer forma de “parecida com ESTA vaga/link”, refletindo honestamente no documento/testes. | |
| OpenCode decide o enquadramento suportado | Deixar a implementação escolher a abordagem limitada mais fiel ao contrato atual (INT/API), desde que o caso esteja validado e as lacunas fiquem explícitas na matriz/testes. | |

**User's choice:** Seed textual + limitação explícita (Recomendado)
**Notes:** Aplica ao exemplo “vagas parecidas com uma vaga”; sem similaridade semântica/vetorial nem seed por link/ID.

| Option | Description | Selected |
|--------|-------------|----------|
| Contrato esperado + resultado observado (Recomendado) | Para cada exemplo: mensagem, interpretação/`applied_params` e status por campo esperados, resultado/`limitations`/guidance esperados, e evidência observada (referência a teste automatizado e/ou execução/fixture documentada) com lacunas explícitas. | ✓ |
| Checklist de aceite comportamental | Registrar critérios de aceite em linguagem clara (o que deve/não deve acontecer) e marcar pass/fail por exemplo com notas de lacuna; menos detalhado no contrato JSON, mais direto para revisão humana. | |

**User's choice:** Contrato esperado + resultado observado (Recomendado)
**Notes:** Base de evidência “validada” por exemplo.

---

## Suíte automatizada e E2E/UI viável (QA-02)

| Option | Description | Selected |
|--------|-------------|----------|
| Script/manual guiado + helpers testados (Recomendado) | Manter UI sem infra nova de browser/E2E: validar fluxo básico via roteiro manual/UAT versionado (abrir chat, enviar, ver interpretação/resultados, aplicar/abrir detalhe) e garantir testes automatizados de lógica pura de UI (ex.: mapeamento/apply). Mais viável no ambiente atual, sem garantia de regressão de DOM. | ✓ |
| Adicionar smoke E2E de navegador (Playwright) | Introduzir Playwright e cobrir um smoke mínimo do fluxo de chat no board (se viável localmente/CI). Maior confiança de integração UI, porém adiciona setup/dependências e custo de manutenção. | |
| Testes de componente/integração UI (Vitest + RTL) | Configurar testes de componentes React para o chat (render/estados/interações com client mockado), sem navegador real. Boa cobertura de comportamento de UI, mas exige adaptar ambiente de testes frontend atual. | |

**User's choice:** Script/manual guiado + helpers testados (Recomendado)
**Notes:** Frontend atual possui Vitest (node) apenas para helpers; sem Playwright/RTL configurados.

| Option | Description | Selected |
|--------|-------------|----------|
| Fechar lacunas e consolidar suíte existente (Recomendado) | Aproveitar/revisar os testes existentes (`intent_*`, `test_chat_search_api.py`) e adicionar apenas casos faltantes (ex.: cenários MVP determinísticos, combinações, limites/guidance) para garantir cobertura explícita e executável. Evita duplicação. | ✓ |
| Reescrever/expandir suíte dedicada aos cenários MVP | Criar uma suíte nova orientada aos exemplos QA-01 (mesmo que sobreponha testes atuais) para deixar a rastreabilidade direta por cenário. Mais verboso, maior esforço. | |

**User's choice:** Fechar lacunas e consolidar suíte existente (Recomendado)
**Notes:** LLM deve ser mockado nos testes de intent/chat-search.

---

## Controles operacionais e kill-switch (QA-03)

| Option | Description | Selected |
|--------|-------------|----------|
| Flag de config/env fim-a-fim (Recomendado) | Um toggle operacional (ex.: env/config) lido pelo backend: endpoint retorna estado “desativado” de forma segura/controlada; frontend consulta/sinaliza e oculta ou desabilita a entrada do chat. Desativar não afeta listagem/busca manual do board. (Escopo exato do sinal ao frontend é detalhe de implementação.) | ✓ |
| Kill-switch só no backend (endpoint) | Backend bloqueia/degrada o endpoint quando desligado; UI pode permanecer visível mas sempre cair em estado de indisponível/guidance para busca manual. Mais simples no frontend, porém expõe controle só no uso. | |
| Kill-switch só no frontend (ocultar UI) | Desativar apenas a interface do chat; endpoint segue ativo. Evita uso pela UI, mas não contém abuso/custo direto na API — geralmente insuficiente como controle operacional completo. | |

**User's choice:** Flag de config/env fim-a-fim (Recomendado)
**Notes:** Com chat desativado ou degradado, o board público deve permanecer utilizável para busca/listagem manual.

| Option | Description | Selected |
|--------|-------------|----------|
| Logs estruturados de evento/resultado (Recomendado) | Registrar eventos operacionais sem conteúdo da mensagem do usuário (ex.: resultado sucesso/degradado/desativado, motivo de degradação/timeout, latência/duração, contagens de resultados ou flags, status HTTP/rate limit) para diagnóstico e ajuste seguro. Sem métricas externas obrigatórias. | ✓ |
| Logs mínimos + contadores/métricas básicas internas | Além de logs sem PII, expor/acumular métricas simples (contagem por outcome, taxa de degradação/429, latência) no formato viável do projeto. Útil para operação, pode exigir pequeno mecanismo de agregação. | |
| Somente logs de erro/indisponibilidade | Registrar apenas falhas, timeouts e estado desativado, com mínimo de contexto. Mais simples, porém com pouca visibilidade de uso/custos/latência normal. | |

**User's choice:** Logs estruturados de evento/resultado (Recomendado)
**Notes:** Observabilidade sem PII sensível; não registrar conteúdo da mensagem do usuário.

---

## OpenCode's Discretion

Nomes/localização exata e formato dos artefatos de validação (matriz QA-01, roteiro manual/UAT QA-02) desde que versionados na fase e rastreáveis; seleção precisa dos casos de teste a adicionar/consolidar sem duplicação; nomes/valores exatos de env/config do kill-switch, forma de sinalizar estado ao frontend e shape segura da resposta “chat desativado”; campos/formato dos logs estruturados sem PII; pequenos ajustes de copy pt-BR/estados de UI para refletir desativação com orientação para busca manual; e definição prática de viabilidade de execução no ambiente do projeto.

## Deferred Ideas

None — discussion stayed within phase scope.
