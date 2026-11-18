---
status: complete
phase: 20-api-publica-de-chat-search-resiliente
source: 20-01-SUMMARY.md, 20-02-SUMMARY.md
started: 2026-11-17T23:29:35Z
updated: 2026-11-17T23:29:35Z
---

## Current Test

[testing complete]

## Tests

### 1. Busca em linguagem natural retorna interpretação e resultados
expected: Ao enviar `POST /api/v1/public/chat-search` com JSON contendo `message` em pt-BR (ex.: cargo/cidade/ordenação) e paginação opcional (`page`, `limit`), a resposta é 200 com envelope `interpretation` + `results`. `interpretation` mostra entendimento/aplicação server-authoritative (`applied_params` com `q`/`city`/`sort` quando aplicável, `field_statuses`, `limitations`/`meta` conforme necessário) e `results` traz `{ items, page, limit, total }` com vagas publicadas não expiradas equivalentes à busca determinística para os `applied_params` efetivos.
result: pass

### 2. Resultados do chat-search são públicos e sem contato
expected: Os itens em `results.items` seguem o contrato público (`JobPublic`) e não expõem campos de contato (ex.: `contact_email`, `contact_phone`) nem outras formas de revelar contato; apenas dados públicos da vaga são retornados.
result: pass

### 3. Mensagem inválida ou excedente retorna erro pt-BR seguro
expected: Requisições com `message` ausente/vazia (após trim) ou acima do tamanho máximo permitido são rejeitadas com erro 4xx (400/422) e `detail` em pt-BR, sem vazar detalhes internos/stack do servidor ou do provedor LLM.
result: pass

### 4. Rate limit dedicado do chat-search
expected: Exceder o limite dedicado da rota `POST /api/v1/public/chat-search` (bucket por IP+endpoint, independente de reveal/login) retorna 429 com mensagem `detail` em pt-BR e cabeçalho `Retry-After`, sem quebrar o contrato de erros públicos.
result: pass

### 5. Falha/timeout/indisponibilidade do LLM degrada com segurança (sem busca automática)
expected: Se a extração de intenção falhar, expirar (timeout curto dedicado) ou o LLM ficar indisponível, a API responde 200 (não 5xx/503 opaco) com interpretação degradada: `meta.degraded=true`, `degradation_reason` apropriado (ex.: `llm_unavailable`/`timeout`), `meta.guidance` clara em pt-BR para usar busca manual/palavras-chave, `applied_params` sem filtros automáticos aplicados e `results` vazio (`items=[]`, `total=0`, page/limit preservados) — sem exibir vagas como interpretadas automaticamente.
result: pass

### 6. Mensagem sem parâmetros extraíveis não dispara busca automática
expected: Quando a mensagem não permite extrair parâmetros confiáveis, a resposta é 200 degradada/orientada (ex.: `degradation_reason`/limitação `no_extractable_params`, `meta.guidance` em pt-BR para reformular ou usar busca manual), com `results` vazio (`items=[]`, `total=0`) e sem inventar filtros ou rodar busca ampla automática.
result: pass

### 7. Suporte parcial/aproximação é sinalizado explicitamente
expected: Para pedidos envolvendo campos sem filtro estruturado garantido (salário, modalidade, tipo de contrato, senioridade) ou similares/parecidas, a interpretação aplica no máximo aproximação textual segura (ex.: via `q`) quando cabível e sinaliza limitações/avisos em pt-BR (`field_statuses`, `limitations` e/ou `meta.guidance`) sem afirmar filtragem numérica/estruturada ou similaridade semântica inexistente.
result: pass

### 8. Cidade fora da whitelist não é inferida incorretamente
expected: Ao citar local fora da whitelist suportada (ex.: Campinas) ou casos ambíguos, o sistema não infere SP/RJ/BH indevidamente. Partes seguras podem ser aplicadas (ex.: `Remoto` se explícito) e/ou termos usados como aproximação textual quando apropriado, mas o campo de cidade não suportado é marcado como ignorado/aproximado com motivo/limitação clara, mantendo respostas determinísticas e honestas.
result: pass

## Summary

total: 8
passed: 8
issues: 0
pending: 0
skipped: 0

## Gaps

[none yet]
