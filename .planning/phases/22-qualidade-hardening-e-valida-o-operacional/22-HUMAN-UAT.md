---
status: complete
phase: 22-qualidade-hardening-e-valida-o-operacional
source:
  - 22-VERIFICATION.md
  - 22-MANUAL-UAT.md
  - 22-04-PLAN.md
  - 23-01-SUMMARY.md
  - 23-02-SUMMARY.md
  - .planning/debug/city-filter-and-chat-ignores-registered-city.md
updated: 2026-11-20T00:00:00Z
---

# Phase 22 — Human UAT (estado final aceito e rastreável)

**Verification status (reconciliado em 23-03):** artefato em estado final aceito e rastreável. Must-haves automatizados da fase 22 permanecem verificados (ver `22-VERIFICATION.md`); correções de hardening/fechamento aplicadas em 22-04, 23-01 e 23-02 foram incorporadas como contexto. Itens executados/aprovados anteriormente foram preservados; itens não executáveis nesta sessão foram resolvidos por **deferimento aceito por item** (D-10/D-12), sem inventar execução runtime/UI.
**Blocking automated gaps:** nenhum conhecido.
**Primary runbook:** `22-MANUAL-UAT.md` (roteiro preservado; resolução por item registrada em 23-03).

## Current Test

[testing complete — estado final reconciliado; sem retestes pendentes não resolvidos]

## Atualização de gap closure e hardening (22-04, 23-01, 23-02)

- **22-04 (fix aplicado):** promoção determinística de texto de cidade suportada para filtro canônico `city=<slug>` no toolbar (limpando `q` quando há correspondência exata por label/slug/canônico/alias, case/acento-insensível) e fallback determinístico server-side no mapper de intenção para detectar cidades whitelist SP/RJ/BH/Remoto em `raw_text` quando `candidate.city` está ausente, com salvaguardas de conflito/whitelist e `applied_params`/`field_statuses` coerentes.
- **23-01 (hardening CL-01):** remoção de `\brio\b` ambíguo no fallback raw-text de Rio de Janeiro, preservando detecção segura via `\brj\b` e `\brio\s+de\s+janeiro\b`, evitando falsos positivos como "Rio Grande do Sul"/"Rio Branco" sem ampliar whitelist (testes determinísticos em `backend/tests/test_intent_mapper.py`; commits `8d0c621`/`27e1a8c`).
- **23-02 (CL-05, contexto):** hardening frontend do chat (`chatSearch` com parse defensivo de JSON em 200 → `ApiError` pt-BR seguro; `canApplyChatToBoard` baseado em normalização útil, evitando apply no-op para cidade-only não normalizável) e melhorias focadas de foco/a11y (foco inicial no diálogo ao abrir e restauração de foco ao fechar detalhe aberto a partir de resultado do chat). **Deferimento residual D-14 propagado:** focus-trap completo no diálogo custom do chat não implementado (ver seção "Deferred A11y Residual").
- **Evidência automatizada preservada:** `frontend/lib/cities.ts` (`resolveCitySlugFromText`), `frontend/components/board/BoardToolbar.tsx`, `frontend/lib/cities.test.ts`; `backend/app/services/intent/mapper.py` (`_detect_city_from_raw_text` e hardening RJ), `backend/tests/test_intent_mapper.py`, `backend/tests/test_intent_parser.py`; correções/testes 23-02 (`frontend/lib/api.ts`, `frontend/lib/chatApply.ts`, `frontend/lib/chatApply.test.ts`). **Nenhuma nova execução manual/runtime/UI foi realizada nesta reconciliação.**

## Resolved / Deferred Items

### 1. Revalidar caso reportado (toolbar e chat) + roteiro manual/UAT guiado

- **Test:** Executar `22-MANUAL-UAT.md` com foco na revalidação do caso reportado: (a) digitar/enviar nome ou alias de cidade suportada cadastrada na busca do board (ex.: "São Paulo", "sp") e confirmar que a URL/estado aplica `city=<slug>` (não permanece indevidamente como `?q=<city-name>`) e retorna vagas correspondentes quando existirem; (b) enviar no chat mensagem com cidade suportada cadastrada (ex.: "vagas em São Paulo") e confirmar interpretação/`applied_params`/`field_statuses` com cidade aplicada (não ignorada como `missing`/`not_in_whitelist` indevidamente), resultados coerentes e sem contatos. Complementarmente, executar os casos 1–6 quando viável.
- **Expected:** Caso reportado deixa de reproduzir nos cenários suportados; demais casos críticos registram `pass` (ou justificativa objetiva) mantendo privacidade/contratos e não-regressão.
- **Why human:** QA-02 (D-04) exige validação UI/E2E viável por roteiro manual/UAT guiado; correção automatizada não substitui evidência operacional/runtime.
- **result:** deferred (aceito por item)
- **reported (histórico):** "O toolbar não está reconhecendo a cidade que corresponde a uma vaga cadastrada, está utilizando ?q=city-name  e retornando nada. O chat-bot também não reconhece a cidade que está cadastrada no banco retornando um status como ignorado ."
- **severity:** major
- **Resolução (23-03):** **deferimento aceito por item**.
  - **Motivo (inviabilidade):** ambiente integrado indisponível nesta execução de fechamento documental (sem backend/frontend em runtime, sem banco/dados de vagas por cidade e sem navegador/sessão para reprodução operacional do fluxo toolbar/chat).
  - **Risco residual:** divergência ponta a ponta em ambiente real (configuração, dados, integrações, UX/foco/comportamento de browser) pode persistir apesar das correções 22-04/23-01 e da cobertura determinística automatizada.
  - **Condição/ação futura:** executar `22-MANUAL-UAT.md` item 0 e este item 1 em ambiente integrado com dados reais/cadastrados por cidade, registrando evidência objetiva de `city=<slug>` aplicado na URL/estado e interpretação correta do chat sem marcação indevida como ignorada (atualizar artefatos e audit trail com o resultado observado).

### 2. Validar kill-switch fim-a-fim percebido na UI

- **Test:** Definir `CHAT_SEARCH_ENABLED=false` (reiniciar/recarregar conforme ambiente) e validar status, endpoint e comportamento no board.
- **Expected:** `GET /api/v1/public/chat-search/status` retorna `enabled:false`; `POST /api/v1/public/chat-search` responde 200 controlado (`chat_disabled`, guidance pt-BR, `applied_params` nulos, `results` vazio, sem contatos/internos); frontend oculta launcher/painel do chat sem bloquear render; busca manual/filtros/paginação/detalhe/revelação continuam utilizáveis.
- **Why human:** Contrato/gating cobertos por testes, mas percepção de UX em runtime (ocultação real, ausência de bloqueio visual, navegação manual fluida) depende de ambiente/config reais.
- result: pass

### 3. Confirmar experiência integrada em degradação/sem resultados e não-regressão

- **Test:** Simular timeout/indisponibilidade/sem parâmetros extraíveis e consultas sem correspondência no ambiente integrado.
- **Expected:** Guidance pt-BR segura sem detalhes internos, sem aplicação automática indevida ao board, atalho/caminho para busca manual funcional e contatos revelados apenas no fluxo canônico.
- **Why human:** Copy, foco, transições, estados e abertura de detalhe a partir do chat exigem validação manual no navegador/contexto real.
- result: pass

## Deferred A11y Residual (propagado de 23-02, D-14)

- **Sub-item:** focus-trap completo no diálogo custom do chat (contenção de ciclo Tab/Shift+Tab).
- **Implementado (viável):** foco inicial no diálogo ao abrir e restauração de foco ao fechar detalhe aberto a partir de resultado do chat.
- **Justificativa:** trap/contenção de foco robusto em diálogo custom aumenta complexidade e risco de regressão de interação/teclado; escopo de 23-02 limitou-se a melhorias focadas e viáveis.
- **Risco residual:** usuários de teclado/leitor de tela podem mover foco para elementos fora do diálogo enquanto ele estiver aberto.
- **Condição/ação futura:** introduzir focus-trap/contenção dedicada (ou primitiva com gerenciamento de foco) no componente de chat com validação manual de teclado/a11y antes de considerar o sub-item encerrado.

## Summary

total: 3
passed: 2
issues: 0
pending: 0
skipped: 0
blocked: 0
deferred_accepted: 1

## Gaps

- truth: "Busca manual (toolbar/filtros) e chat reconhecem corretamente a cidade de vagas cadastradas; filtro de cidade aplica `city` suportado (não como `q` indevido) e o chat não marca cidade cadastrada como ignorada quando aplicável."
  status: deferred_accepted
  reason: "Histórico (user report) mitigado por 22-04 + hardening 23-01 com testes determinísticos. Reteste runtime/manual não executado nesta sessão; **deferimento aceito por item** registrado com rastreabilidade."
  severity: major
  test: 1
  motivo: "Ambiente integrado indisponível (sem backend/frontend/DB/dados/navegador) para revalidação operacional nesta execução."
  risco_residual: "Possível divergência ponta a ponta em runtime real (config/dados/UX) apesar de correções e testes determinísticos."
  condicao_acao_futura: "Executar revalidação manual/runtime do item 1 (e `22-MANUAL-UAT.md` item 0) em ambiente integrado com vagas por cidade; registrar evidência objetiva e atualizar artefatos de fechamento."
  root_cause: "Duas causas relacionadas (diagnosticadas): (1) Toolbar/manual sempre gravava `q` e não promovia nome/alias de cidade suportada para `city`; `q` não consulta `Job.city`. (2) Mapper não detectava SP/RJ/BH em `raw_text` quando `candidate.city` ausente; risco adicional de `\\brio\\b` ambíguo mitigado em 23-01. Ver `.planning/debug/city-filter-and-chat-ignores-registered-city.md`."
  artifacts:
    - path: "frontend/lib/cities.ts"
      issue: "Inclui `resolveCitySlugFromText` (detecção exata, case/acento-insensível, aliases seguros) — correção aplicada, reteste runtime deferido por item."
    - path: "frontend/components/board/BoardToolbar.tsx"
      issue: "Promove texto de cidade suportada para `city=<slug>` limpando `q` — correção aplicada, reteste runtime deferido por item."
    - path: "backend/app/services/intent/mapper.py"
      issue: "Fallback determinístico `_detect_city_from_raw_text` para whitelist SP/RJ/BH/Remoto com conflito seguro + hardening RJ sem `\\brio\\b` ambíguo — correção aplicada, reteste runtime deferido por item."
    - path: "backend/tests/test_intent_mapper.py"
      issue: "Cobertura determinística para fallback/salvaguardas e falsos positivos RJ preservada/adicionada."
    - path: "frontend/lib/cities.test.ts"
      issue: "Cobertura determinística para resolução de cidade no frontend."
  debug_session: ".planning/debug/city-filter-and-chat-ignores-registered-city.md"

## Operational Notes

- `22-SECURITY.md` (Phase 22) não existe neste momento de reconciliação; criação/tratamento formal como artefato de segurança rastreável é objeto de CL-05 (23-04), sem marcar gap de implementação não tratado neste documento.
- Evidências automatizadas determinísticas e artefatos QA-01/QA-02/QA-03 permanecem presentes; validações runtime/UI não executadas nesta sessão foram registradas como deferimento aceito por item com motivo, risco residual e condição/ação futura (D-12).
- Residual de a11y/foco propagado de 23-02 (D-14): focus-trap completo do diálogo custom do chat permanece deferido por viabilidade/escopo (ver "Deferred A11y Residual").
