# Requirements: EmpregaNoix

**Defined:** 2026-11-17
**Core Value:** Qualquer pessoa encontra uma vaga e o contato para se candidatar em segundos — sem cadastro, sem login, sem fricção.

## v1.3 Requirements

Requirements for milestone v1.3 (Chatbot Inteligente de Busca de Vagas). Each maps to roadmap phases.

### Intent Extraction (INT)

- [ ] **INT-01**: Usuário pode enviar uma consulta em linguagem natural (pt-BR) e o sistema extrai parâmetros estruturados em JSON estrito e validado (ex.: cargo/palavras-chave, senioridade, cidade, modalidade remoto/híbrido/presencial, faixa salarial min/max, tipo de contrato, ordenação), sem inventar informações não declaradas/implicadas.
- [ ] **INT-02**: A extração usa provider LLM configurável de baixo custo (reuso Groq/config existente como padrão) com schema/validação server-side (Pydantic), defaults nulos/seguros e prompt robusto para tolerar variações pt-BR e resistir a instruções conflitantes no texto do usuário.
- [ ] **INT-03**: O sistema normaliza e mapeia parâmetros extraídos para a busca existente de forma segura (ex.: `q`, cidade apenas na whitelist SP/RJ/BH/Remoto, `sort` permitido), separando/relatando o que foi **aplicado**, **ignorado** ou **aproximado** quando não houver suporte nativo.

### Chat Search API (API)

- [ ] **API-01**: Existe endpoint público de chat-search que recebe a mensagem do usuário, executa extração→mapeamento→busca determinística reutilizando a lógica/contrato de `GET /api/v1/public/jobs` / `list_published`, e retorna interpretação + resultados pagináveis/limitados em formato público (`JobPublic`, sem contatos) com `total`.
- [ ] **API-02**: O endpoint público possui proteções de abuso/custo e resiliência: rate limit por IP, limites de tamanho/tempo (request/timeout), erros pt-BR seguros e fallback controlado (ex.: orientação para busca manual/keyword) em falha/timeout/indisponibilidade do LLM.
- [ ] **API-03**: Para campos sem filtro nativo completo no MVP (ex.: faixa salarial, modalidade, tipo de contrato/senioridade conforme capacidade atual), o sistema aplica estratégia explícita e limitada (mapeamento em `q` e/ou pós-filtro em janela candidata limitada) e sinaliza suporte parcial/aproximado sem afirmar filtragem inexistente.

### Chat UI (UI)

- [ ] **UI-01**: Usuário acessa uma interface de chat simples (drawer/modal), mobile-first e sem login, a partir do board público, com envio de mensagem, estados de carregamento/erro e boa percepção de performance.
- [ ] **UI-02**: A interface exibe os parâmetros entendidos/aplicados/ignorados-aproximados e apresenta resultados relevantes (título, empresa, local, salário quando disponível, acesso ao detalhe/link) reutilizando o fluxo atual de detalhe e revelação de contato (contatos nunca expostos no payload do chat).
- [ ] **UI-03**: Usuário pode aplicar/ajustar a busca entendida no board canônico (URL/filtros existentes) quando aplicável, preservando o comportamento atual de busca/listagem sem fricção.

### Quality & Hardening (QA)

- [ ] **QA-01**: O MVP cobre os exemplos-alvo do milestone com comportamento validado e documentado (incluindo combinações e lacunas explícitas): dev pleno SP salário >= 8k; remoto frontend React preferência CLT; vagas parecidas com uma vaga (abordagem limitada/seed por texto/link conforme suportado); analista de dados Campinas ou remoto 6–10k; estágio marketing digital em SP.
- [ ] **QA-02**: Existem testes automatizados cobrindo extração/mapeamento/normalização e API de chat-search (com LLM mockado) e validação básica do fluxo de UI/E2E conforme viável no ambiente do projeto.
- [ ] **QA-03**: O sistema possui controles operacionais mínimos para o chat (config/feature toggle ou kill-switch, logs/métricas básicas sem PII sensível) para permitir desativação/ajuste seguro em caso de abuso, custo ou degradação, sem regredir o board público existente.

## v2 Requirements

Deferred to future release. Tracked but not in current roadmap.

### Chat Search Enhancements

- **CHAT-V2-01**: Busca semântica/embeddings/"vagas parecidas" com ranking vetorial sobre corpus (avaliar custo/infra/qualidade).
- **CHAT-V2-02**: Refinamento conversacional com histórico persistente/conta (conflita com fricção zero no MVP).
- **CHAT-V2-03**: Promoção de salário/modalidade/contrato/senioridade para campos/filtros nativos indexados quando dados/curadoria justificarem.
- **CHAT-V2-04**: Recomendação personalizada por perfil e alertas/salvamento de buscas.

## Out of Scope

Explicitly excluded. Documented to prevent scope creep.

| Feature | Reason |
|---------|--------|
| LLM ler/rankear centenas de vagas (corpus no prompt) | Custo/latência/alucinação; decisão explícita: LLM apenas extrai parâmetros |
| Memória de conversa longa/histórico persistente avançado | Fora do MVP; adiciona complexidade/estado/fricção |
| Recomendação personalizada baseada em perfil do usuário | Requer identidade/dados adicionais; fora do MVP |
| Aplicação automática em vagas / integração LinkedIn/WhatsApp | Fora do MVP e do core atual |
| Expor contatos no payload do chat | Viola proteção/fluxo atual de revelação; contatos continuam protegidos |
| Carry-over v1.2/v1.1 (PUB-01..08, handoffs TEST-04/DOC-01/AUD-05, lacunas EXTR/PUBL/SRCH/UIUX) | Explicitamente excluído deste milestone por decisão de escopo (focar no chatbot); tratar em ciclo dedicado |
| Busca semântica/embeddings completa no MVP | Infra/custo desproporcional agora; considerar após validação |

## Traceability

Which phases cover which requirements. Updated during roadmap creation.

| Requirement | Phase | Status |
|-------------|-------|--------|
| INT-01 | Phase [TBD] | Pending |
| INT-02 | Phase [TBD] | Pending |
| INT-03 | Phase [TBD] | Pending |
| API-01 | Phase [TBD] | Pending |
| API-02 | Phase [TBD] | Pending |
| API-03 | Phase [TBD] | Pending |
| UI-01 | Phase [TBD] | Pending |
| UI-02 | Phase [TBD] | Pending |
| UI-03 | Phase [TBD] | Pending |
| QA-01 | Phase [TBD] | Pending |
| QA-02 | Phase [TBD] | Pending |
| QA-03 | Phase [TBD] | Pending |

**Coverage:**
- v1.3 requirements: 12 total
- Mapped to phases: 0 (pending roadmap)
- Unmapped: 12 ⚠️

---
*Requirements defined: 2026-11-17*
*Last updated: 2026-11-17 after initial definition*
