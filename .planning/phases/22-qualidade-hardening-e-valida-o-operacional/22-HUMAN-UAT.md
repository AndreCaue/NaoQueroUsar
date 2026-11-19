---
status: partial
phase: 22-qualidade-hardening-e-valida-o-operacional
source:
  - 22-VERIFICATION.md
  - 22-MANUAL-UAT.md
  - 22-04-PLAN.md
updated: 2026-11-18T23:59:00Z
---

# Phase 22 — Human UAT (Revalidação pendente)

**Verification status:** human_needed (5/5 automated must-haves verificados anteriormente; gap reportado recebeu implementação/fix em 22-04)  
**Blocking automated gaps:** nenhum conhecido após 22-04 (pendente revalidação manual/runtime)  
**Primary runbook:** `22-MANUAL-UAT.md` (casos guiados atualizados para revalidação do caso reportado)

## Current Test

[awaiting manual retest / revalidação pendente]

## Atualização de gap closure (22-04)

- **Fix aplicado (pendente revalidação manual em runtime):** promoção determinística de texto de cidade suportada para filtro canônico `city=<slug>` no toolbar (limpando `q` quando há correspondência exata por label/slug/canônico/alias, case/acento-insensível) e fallback determinístico server-side no mapper de intenção para detectar cidades whitelist SP/RJ/BH/Remoto em `raw_text` quando `candidate.city` está ausente, com salvaguardas de conflito/whitelist e `applied_params`/`field_statuses` coerentes.
- **Evidência automatizada adicionada/atualizada (22-04):** `frontend/lib/cities.ts` (`resolveCitySlugFromText`), `frontend/components/board/BoardToolbar.tsx`, `frontend/lib/cities.test.ts`; `backend/app/services/intent/mapper.py` (`_detect_city_from_raw_text`), `backend/tests/test_intent_mapper.py`, `backend/tests/test_intent_parser.py` (regressão), além de tentativa de caso DB-backed em `backend/tests/test_chat_search_api.py` (ambiente-dependente; ver SUMMARY/execução). **Nenhuma aprovação manual/runtime é reivindicada aqui.**

## Pending Human Verification Items

### 1. Revalidar caso reportado (toolbar e chat) + roteiro manual/UAT guiado

- **Test:** Executar `22-MANUAL-UAT.md` com foco na revalidação do caso reportado: (a) digitar/enviar nome ou alias de cidade suportada cadastrada na busca do board (ex.: "São Paulo", "sp") e confirmar que a URL/estado aplica `city=<slug>` (não permanece indevidamente como `?q=<city-name>`) e retorna vagas correspondentes quando existirem; (b) enviar no chat mensagem com cidade suportada cadastrada (ex.: "vagas em São Paulo") e confirmar interpretação/`applied_params`/`field_statuses` com cidade aplicada (não ignorada como `missing`/`not_in_whitelist` indevidamente), resultados coerentes e sem contatos. Complementarmente, executar os casos 1–6 quando viável.
- **Expected:** Caso reportado deixa de reproduzir nos cenários suportados; demais casos críticos registram `pass` (ou justificativa objetiva) mantendo privacidade/contratos e não-regressão.
- **Why human:** QA-02 (D-04) exige validação UI/E2E viável por roteiro manual/UAT guiado; correção automatizada não substitui evidência operacional/runtime.
- **result:** [pending retest]
- **reported (histórico):** "O toolbar não está reconhecendo a cidade que corresponde a uma vaga cadastrada, está utilizando ?q=city-name  e retornando nada. O chat-bot também não reconhece a cidade que está cadastrada no banco retornando um status como ignorado ."
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
issues: 0
pending: 1
skipped: 0
blocked: 0

## Gaps

- truth: "Busca manual (toolbar/filtros) e chat reconhecem corretamente a cidade de vagas cadastradas; filtro de cidade aplica `city` suportado (não como `q` indevido) e o chat não marca cidade cadastrada como ignorada quando aplicável."
  status: retest_required
  reason: "Histórico (user report): toolbar usava `?q=city-name` sem promover cidade suportada e chat podia marcar cidade cadastrada como ignorada em cenários de extração ausente/incorreta. Fix aplicado em 22-04 (toolbar promotion + fallback raw-text mapper SP/RJ/BH/Remoto com salvaguardas) com testes determinísticos adicionados; **reteste manual/runtime pendente** para confirmar comportamento no ambiente integrado."
  severity: major
  test: 1
  root_cause: "Duas causas relacionadas (diagnosticadas): (1) Toolbar/manual sempre gravava `q` e não promovia nome/alias de cidade suportada para `city`; `q` não consulta `Job.city`. (2) Mapper não detectava SP/RJ/BH em `raw_text` quando `candidate.city` ausente. Ver `.planning/debug/city-filter-and-chat-ignores-registered-city.md`."
  artifacts:
    - path: "frontend/lib/cities.ts"
      issue: "Agora inclui `resolveCitySlugFromText` (detecção exata, case/acento-insensível, aliases seguros) — **pendente retest**."
    - path: "frontend/components/board/BoardToolbar.tsx"
      issue: "Agora promove texto de cidade suportada para `city=<slug>` limpando `q` — **pendente retest**."
    - path: "backend/app/services/intent/mapper.py"
      issue: "Agora inclui fallback determinístico `_detect_city_from_raw_text` para whitelist SP/RJ/BH/Remoto com conflito seguro — **pendente retest**."
    - path: "backend/tests/test_intent_mapper.py"
      issue: "Cobertura determinística adicionada para fallback/salvaguardas (ausente-candidato, conflitos, não-whitelist)."
    - path: "frontend/lib/cities.test.ts"
      issue: "Cobertura determinística adicionada para resolução de cidade no frontend."
  missing:
    - "Revalidação manual/runtime do caso reportado (toolbar e chat) em ambiente integrado com dados de vagas por cidade."
  debug_session: ".planning/debug/city-filter-and-chat-ignores-registered-city.md"

## Operational Notes

- `SECURITY.md` ausente no diretório da fase; se enforcement de segurança for requerido antes de avançar, executar `/gsd-secure-phase 22`.
- Evidências automatizadas determinísticas e artefatos QA-01/QA-02/QA-03 estão presentes; pendência principal é validação operacional/manual em runtime (incluindo revalidação do gap reportado). Status honesto: fix aplicado, pending manual revalidation.
