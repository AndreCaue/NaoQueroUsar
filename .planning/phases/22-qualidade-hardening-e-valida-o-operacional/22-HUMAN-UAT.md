---
status: diagnosed
phase: 22-qualidade-hardening-e-valida-o-operacional
source:
  - 22-VERIFICATION.md
  - 22-MANUAL-UAT.md
updated: 2026-11-18T12:45:00Z
---

# Phase 22 — Human UAT (Pending Verification)

**Verification status:** human_needed (5/5 automated must-haves verified)  
**Blocking automated gaps:** none found  
**Primary runbook:** `22-MANUAL-UAT.md` (detailed guided cases)

## Current Test

[testing complete]

## Pending Human Verification Items

### 1. Executar roteiro manual/UAT guiado completo

- **Test:** Executar `22-MANUAL-UAT.md` (casos 1–6) em ambiente com backend/frontend e dados de teste.
- **Expected:** Todos os casos críticos registram `pass` (ou justificativa objetiva): board manual sem login, fluxo chat habilitado, interpretação/limites/`carregar mais`/aplicar, detalhe/revelação canônica sem contatos no chat, estados degradado/sem resultados com busca manual, e cenários com `CHAT_SEARCH_ENABLED=false`.
- **Why human:** QA-02 (D-04) exige validação básica de UI/E2E viável por roteiro manual/UAT guiado (sem Playwright/RTL). O runbook existe, mas os resultados permanecem pendentes.
- **result:** issue
- **reported:** "O toolbar não está reconhecendo a cidade que corresponde a uma vaga cadastrada, está utilizando ?q=city-name  e retornando nada. O chat-bot também não reconhece a cidade que está cadastrada no banco retornando um status como ignorado ."
- **severity:** major

### 2. Validar kill-switch fim-a-fim percebido na UI

- **Test:** Definir `CHAT_SEARCH_ENABLED=false` (reiniciar/recarregar conforme ambiente) e validar status, endpoint e comportamento no board.
- **Expected:** `GET /api/v1/public/chat-search/status` retorna `enabled:false`; `POST /api/v1/public/chat-search` responde 200 controlado (`chat_disabled`, guidance pt-BR, `applied_params` nulos, `results` vazio, sem contatos/internos); frontend oculta launcher/painel do chat sem bloquear render; busca manual/filtros/paginação/detalhe/revelação continuam utilizáveis.
- **Why human:** Contrato/gating cobertos por testes, mas percepção de UX em runtime (ocultação real, ausência de bloqueio visual, navegação manual fluida) depende de ambiente/config reais.
- **result:** pass

### 3. Confirmar experiência integrada em degradação/sem resultados e não-regressão

- **Test:** Simular timeout/indisponibilidade/sem parâmetros extraíveis e consultas sem correspondência no ambiente integrado.
- **Expected:** Guidance pt-BR segura sem detalhes internos, sem aplicação automática indevida ao board, atalho/caminho para busca manual funcional e contatos revelados apenas no fluxo canônico.
- **Why human:** Copy, foco, transições, estados e abertura de detalhe a partir do chat exigem validação manual no navegador/contexto real.
- **result:** pass

## Summary

total: 3
passed: 2
issues: 1
pending: 0
skipped: 0
blocked: 0

## Gaps

- truth: "Busca manual (toolbar/filtros) e chat reconhecem corretamente a cidade de vagas cadastradas; filtro de cidade aplica `city` suportado (não como `q` indevido) e o chat não marca cidade cadastrada como ignorada quando aplicável."
  status: failed
  reason: "User reported: O toolbar não está reconhecendo a cidade que corresponde a uma vaga cadastrada, está utilizando ?q=city-name  e retornando nada. O chat-bot também não reconhece a cidade que está cadastrada no banco retornando um status como ignorado ."
  severity: major
  test: 1
  root_cause: "Duas causas relacionadas: (1) Toolbar/manual: o input de busca sempre grava `q` (commit({ q })) e nunca promove nome/alias de cidade suportada para `city`; filtros/URL não inferem `city` a partir de `q` e o backend aplica `q` apenas em `Job.search_text` (title/company/activities/requirements, sem `Job.city`), então `?q=<cidade>` não casa com vagas cujo match está só na coluna `city`. (2) Chat: `_resolve_city_safe` resolve cidade do candidato contra whitelist e só faz fallback em `raw_text` para remoto quando `candidate.city` está ausente; não detecta SP/RJ/BH (nomes/aliases comuns) no texto cru, gerando `ignorado` (`missing`/`not_in_whitelist`/conflito) quando a extração omite ou erra a cidade suportada."
  artifacts:
    - path: "frontend/components/board/BoardToolbar.tsx"
      issue: "Busca textual sempre commitada como `q`; cidade só aplicada via chips (`commit({ city })`), sem detecção/promoção de cidade suportada."
    - path: "frontend/lib/filters.ts"
      issue: "Normaliza/serializa `q` e `city` de forma independente; sem inferência de `city` a partir de `q`."
    - path: "frontend/lib/cities.ts"
      issue: "Fonte de slugs/labels/canônicos suportados (SP/RJ/BH/Remoto) para toolbar/filtros."
    - path: "backend/app/api/v1/public.py"
      issue: "Listagem pública trata `q` e `city` separadamente; chat retorna `field_statuses`/aplicação conforme interpretação mapeada."
    - path: "backend/app/crud/jobs.py"
      issue: "`_published_filters`: `city` filtra `Job.city`; `q` filtra apenas `search_text`."
    - path: "backend/app/models/job.py"
      issue: "`city` e `search_text` são colunas distintas (cidade não integra `search_text`)."
    - path: "backend/app/services/intent/mapper.py"
      issue: "`_resolve_city_safe` sem fallback em `raw_text` para SP/RJ/BH quando `candidate.city` ausente; pode marcar cidade como ignorada."
    - path: "backend/app/services/intent/parser.py"
      issue: "Orquestra extração + mapeamento; qualidade/ausência de `candidate.city` impacta resultado final."
    - path: "backend/app/services/cities.py"
      issue: "Resolução/whitelist canônica de cidades suportadas usada no mapeamento."
  missing:
    - "No toolbar/busca manual: detectar texto correspondente a cidade suportada (label/slug/canônico/alias, case/acento-insensível) e aplicar como `city=<slug>` (com regra clara de precedência vs `q`) em vez de enviar apenas `q`."
    - "No chat/mapper: fallback determinístico server-side para detectar cidades whitelist SP/RJ/BH em `raw_text` quando `candidate.city` ausente/ambíguo-seguro, preservando salvaguardas (sem inventar cidade fora da whitelist, sem conflitos multi-cidade inseguros) e refletindo `applied_params`/`field_statuses` corretos."
    - "Cobertura de testes determinísticos (UI/filtros se aplicável, mapper/parser/chat API com LLM mockado) e revalidação manual do caso reportado (toolbar e chat)."
  debug_session: ".planning/debug/city-filter-and-chat-ignores-registered-city.md"

## Operational Notes

- `SECURITY.md` ausente no diretório da fase; se enforcement de segurança for requerido antes de avançar, executar `/gsd-secure-phase 22`.
- Evidências automatizadas determinísticas e artefatos QA-01/QA-02/QA-03 estão presentes; pendência principal é validação operacional/manual em runtime.
