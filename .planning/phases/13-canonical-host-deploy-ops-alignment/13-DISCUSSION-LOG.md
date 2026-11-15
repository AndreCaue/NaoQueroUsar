# Phase 13: Canonical Host, Deploy & Ops Alignment (BRND-04 closeout) - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-11-15
**Phase:** 13-canonical-host-deploy-ops-alignment
**Areas discussed:** Hosts canônicos e mapeamento, Escopo da configuração/alinhamento, Evidência e critérios de fechamento, Rollout, dependências e risco operacional

---

## Hosts canônicos e mapeamento

| Option | Description | Selected |
|--------|-------------|----------|
| Usar os nomes da marca (Recomendado) | Adotar `https://empreganoix.vercel.app` (frontend) e `https://empreganoix.onrender.com` (backend) como canônicos oficiais, alinhando roadmap/requirements; outros hosts viram aliases legados/mapeados com nota explícita. | ✓ |
| Usar os hosts realmente implantados hoje | Tratar os hosts atualmente em uso/registrados (ex.: os que aparecem no DEPLOY/evidências reais) como canônicos e atualizar roadmap/docs/requisitos para refletir a realidade operacional. | |
| Modelo híbrido (canônico + mapeamento) | Definir um par canônico de marca, mas aceitar hosts operacionais atuais como válidos durante transição, com mapeamento documentado e critério claro de quando o canônico passa a valer. | |

**User's choice:** Usar os nomes da marca (Recomendado)
**Notes:** Direciona CORS, URLs de API, documentação e evidência para o par de hosts da marca.

| Option | Description | Selected |
|--------|-------------|----------|
| Mapear como legados/históricos (Recomendado) | Manter como registros históricos de evidência, mas marcar como não canônicos; docs/config alvo apontam só para os hosts de marca e o mapeamento fica explícito. | ✓ |
| Manter como aliases operacionais válidos | Além do canônico de marca, documentar e (quando aplicável) aceitar esses hosts como origens/aliases válidos até migração completa. | |
| Descontinuar/ignorar fora da evidência | Não considerar legados no estado alvo; mencionar só como histórico de auditoria, sem suportá-los em CORS/docs de operação atuais. | |

**User's choice:** Mapear como legados/históricos (Recomendado)
**Notes:** Exemplos citados na discussão: `nao-quero-usar.vercel.app`, `naoquerousar.onrender.com`, `empreganoix-six.vercel.app`, `nqu-backend-x60n.onrender.com`.

| Option | Description | Selected |
|--------|-------------|----------|
| Cobertura completa de integração (Recomendado) | Incluir `CORS_ORIGINS` exata, `BACKEND_API_URL`/`NEXT_PUBLIC_API_URL`, Turnstile Hostnames do domínio canônico, e atualização de exemplos/runbook/smoke para os hosts de marca. | ✓ |
| Apenas CORS e URLs de API | Focar em origens CORS e URLs base frontend↔backend; tratar Turnstile hostnames como nota operacional separada, sem torná-lo critério central desta fase. | |
| Somente documentação/mapeamento | Registrar o alinhamento pretendido e onde configurar, sem exigir que todos os pontos de integração (ex.: Turnstile hostnames) sejam detalhados como parte do fechamento. | |

**User's choice:** Cobertura completa de integração (Recomendado)
**Notes:** Alinhamento vai além de CORS para incluir variáveis de API, Turnstile hostnames e exemplos operacionais.

| Option | Description | Selected |
|--------|-------------|----------|
| Fechar por alinhamento contratual + evidência documentada (Recomendado) | Fechar quando config/docs/runbook/alvos canônicos estiverem consistentes e o estado atual/legado estiver mapeado com evidência; execução de deploy real nos hosts canônicos fica como passo operacional externo registrado. | ✓ |
| Fechar só com deploy/smoke real nos hosts canônicos | BRND-04 só fecha após provisionar/publicar nos hosts de marca e registrar smoke gate verde nesses hosts (health, CORS, Turnstile, cron etc.). | |
| Fechamento parcial com handoff explícito | Marcar alinhamento documental/config pronto, mas deixar BRND-04 explicitamente pendente até confirmação operacional nos hosts canônicos. | |

**User's choice:** Fechar por alinhamento contratual + evidência documentada (Recomendado)
**Notes:** Permite fechamento contratual mesmo sem publicação efetiva nos canônicos no momento da execução, desde que haja mapeamento/evidência.

| Option | Description | Selected |
|--------|-------------|----------|
| Próxima área (Recomendado) | Já capturei decisões suficientes sobre canônico, legados, cobertura de integração e fechamento de BRND-04. | ✓ |
| Mais perguntas | Quero detalhar mais (ex.: domínios customizados futuros, política de redirects, naming exato em cada artefato). | |

**User's choice:** Próxima área (Recomendado)
**Notes:** Nenhum detalhamento adicional solicitado.

---

## Escopo da configuração/alinhamento

| Option | Description | Selected |
|--------|-------------|----------|
| Docs + deploy config + scripts de verificação (Recomendado) | Atualizar `docs/DEPLOY.md`, `render.yaml`, `frontend/vercel.json`/`.env.example` e exemplos/comandos em `scripts/verify-deploy.ps1` (e afins) para refletir hosts canônicos e mapeamento legado. | ✓ |
| Somente documentação/runbook | Limitar mudanças a `docs/DEPLOY.md` e notas de operação; não tocar `render.yaml`, vercel config ou scripts executáveis. | |
| Abrangente (repo + planejamento/GSD) | Além de docs/config/scripts, atualizar artefatos de planejamento relevantes (ROADMAP/REQUIREMENTS notas, audit/STATE se aplicável) para registrar o alinhamento e fechamento contratual. | |

**User's choice:** Docs + deploy config + scripts de verificação (Recomendado)
**Notes:** Foco em artefatos versionados de operação/configuração; notas de planejamento são tratadas na área de evidência/traceabilidade.

| Option | Description | Selected |
|--------|-------------|----------|
| Evitar mudanças de runtime; foco em config/docs/scripts (Recomendado) | Não alterar lógica de app; alinhar valores/configurações declarativas, exemplos e guias. Se surgir necessidade real de código, registrar como desvio explícito. | ✓ |
| Permitir ajustes mínimos e seguros de runtime | Aceitar mudanças pequenas e não comportamentais (ex.: defaults/exemplos embutidos, comentários, validações de mensagem) se necessárias para refletir hosts canônicos. | |
| Permitir mudanças de runtime conforme necessário | Autorizar alterações em backend/frontend para impor ou facilitar o alinhamento canônico, desde que dentro da fronteira da fase (sem novas features). | |

**User's choice:** Evitar mudanças de runtime; foco em config/docs/scripts (Recomendado)
**Notes:** Fronteira clara para evitar mudança comportamental no app.

| Option | Description | Selected |
|--------|-------------|----------|
| Origem única e estrita (Recomendado) | `CORS_ORIGINS` com apenas `https://empreganoix.vercel.app` (sem barra final), `NEXT_PUBLIC_API_URL`/`BACKEND_API_URL` apontando para `https://empreganoix.onrender.com`; legados fora do estado alvo. | ✓ |
| Lista explícita com canônico + legados temporários | Permitir múltiplas origens/URLs documentadas durante transição (canônico + hosts legados selecionados), com plano de remoção. | |
| Flexível conforme operação atual | Não fixar política rígida agora; documentar opções e deixar o valor final para o operador conforme o deploy existente. | |

**User's choice:** Origem única e estrita (Recomendado)
**Notes:** Estado-alvo de produção deve apontar exclusivamente para os hosts canônicos.

| Option | Description | Selected |
|--------|-------------|----------|
| Normalizar alvo, preservar histórico (Recomendado) | Atualizar instruções/exemplos/placeholders e o "estado alvo" para os hosts canônicos; manter intactas as linhas/tabelas de evidência histórica, adicionando notas de mapeamento canônico quando necessário. | ✓ |
| Reescrever tudo para o canônico | Substituir hosts antigos por canônicos em todo o documento, inclusive em registros passados, para consistência visual (pode perder fidelidade histórica). | |
| Apenas anotar sem normalizar exemplos | Adicionar notas de canonicalização, mas manter a maioria dos exemplos/valores como estão. | |

**User's choice:** Normalizar alvo, preservar histórico (Recomendado)
**Notes:** Preserva rastreabilidade das evidências anteriores.

| Option | Description | Selected |
|--------|-------------|----------|
| Próxima área (Recomendado) | Escopo de artefatos, política de runtime/código e tratamento de histórico já estão claros. | ✓ |
| Mais perguntas | Quero detalhar inclusão/exclusão de arquivos específicos (ex.: README, STATE, audit, render service name). | |

**User's choice:** Próxima área (Recomendado)
**Notes:** Sem detalhamento adicional solicitado.

---

## Evidência e critérios de fechamento

| Option | Description | Selected |
|--------|-------------|----------|
| Matriz de alinhamento + evidência histórica mapeada (Recomendado) | Criar registro que mapeia cada check (health/env/Turnstile, CORS, cron, superfícies) ao estado: verificado em host legado, alinhado contratualmente ao canônico, ou pendente de execução — citando evidências existentes (ex.: DEPLOY 2026-11-15). | ✓ |
| Exigir nova execução de verify-deploy nos canônicos | Só aceitar fechamento com `verify-deploy.ps1` (ou equivalente) executado contra `empreganoix.vercel.app/onrender.com` e registrado como verde. | |
| Checklist documental mínima | Registrar apenas que docs/config/scripts foram alinhados e listar passos para validação futura, sem matriz detalhada de checks/evidências. | |

**User's choice:** Matriz de alinhamento + evidência histórica mapeada (Recomendado)
**Notes:** Compatível com cenário sem deploy real novo nos canônicos.

| Option | Description | Selected |
|--------|-------------|----------|
| Conjunto completo do roadmap (Recomendado) | `GET /api/v1/health` (env/turnstile), preflight CORS da origem canônica, cron `/admin/expire` (401/403/503 sem segredo + 200 idempotente com segredo), e superfícies públicas/admin chave (board, legal, login/admin) — cada um com status/mapeamento. | ✓ |
| Apenas saúde, CORS e cron | Focar nos sinais de integração/ops críticos (health, CORS, cron) e tratar superfícies UI/admin como verificação implícita ou fora da matriz. | |
| Saúde e CORS apenas | Cobrir conectividade/config básica entre frontend e backend canônicos; deixar cron e superfícies para evidência operacional posterior. | |

**User's choice:** Conjunto completo do roadmap (Recomendado)
**Notes:** Cobertura alinhada aos success criteria da Phase 13.

| Option | Description | Selected |
|--------|-------------|----------|
| `docs/DEPLOY.md` + notas em REQUIREMENTS/ROADMAP (Recomendado) | Adicionar seção/matriz em `docs/DEPLOY.md` (alvo canônico + mapeamento legado + status dos checks) e refletir fechamento/caveats em `REQUIREMENTS.md` e notas do roadmap conforme critério 4. | ✓ |
| Artefato de fase em `.planning/` como fonte principal | Registrar a evidência em artefato de verificação/contexto da Phase 13 e apenas referenciar em docs operacionais/requisitos. | |
| Somente atualização de `REQUIREMENTS.md`/ROADMAP | Usar os arquivos de planejamento como registro de fechamento, sem criar/atualizar matriz operacional detalhada em `docs/DEPLOY.md`. | |

**User's choice:** `docs/DEPLOY.md` + notas em REQUIREMENTS/ROADMAP (Recomendado)
**Notes:** Mantém evidência operacional próxima do runbook.

| Option | Description | Selected |
|--------|-------------|----------|
| Marcar como fechados com nota de escopo ops (Recomendado) | Atualizar checkboxes/notas para concluído no escopo desta fase: contrato/código já verificado antes e alinhamento canônico/evidência operacional mapeada agora; explicitar que execução real em host canônico, se ausente, fica como handoff operacional. | ✓ |
| Manter pendentes até smoke real nos canônicos | Deixar SECR-12/LIFE-13 abertos mesmo com alinhamento documental/mapeamento, até haver execução verde em `empreganoix.vercel.app/onrender.com`. | |
| Fechar apenas BRND-04 e manter split residual | Concluir BRND-04 nesta fase, mas deixar SECR-12/LIFE-13 com pendência residual explícita para uma etapa operacional futura. | |

**User's choice:** Marcar como fechados com nota de escopo ops (Recomendado)
**Notes:** Preserva split ownership histórico (código/contrato antes, resíduo ops agora).

| Option | Description | Selected |
|--------|-------------|----------|
| Próxima área (Recomendado) | Tipo de evidência, checks, local de registro e semântica de fechamento já estão definidos. | ✓ |
| Mais perguntas | Quero detalhar formato exato da matriz, comandos de evidência ou tratamento de falhas parciais. | |

**User's choice:** Próxima área (Recomendado)
**Notes:** Sem detalhamento adicional solicitado.

---

## Rollout, dependências e risco operacional

| Option | Description | Selected |
|--------|-------------|----------|
| Sequência completa e segura (Recomendado) | 1) alinhar/provisionar hosts canônicos nos provedores, 2) configurar envs/CORS/Turnstile hostnames/cron secrets, 3) rebuild/redeploy frontend (NEXT_PUBLIC_*), 4) validar health/CORS/cron/superfícies com verify-deploy, 5) registrar evidência — com rollback por reversão de env/domínio. | ✓ |
| Apenas atualizar config e redeploy simples | Trocar envs/CORS/URLs e redeployar sem detalhar pré-condições como Turnstile hostnames, rebuild por variável inlinada ou validação pós-deploy. | |
| Foco só em documentação da ordem | Registrar uma ordem sugerida em alto nível, sem passos operacionais detalhados de validação/rollback. | |

**User's choice:** Sequência completa e segura (Recomendado)
**Notes:** Ordem recomendada para execução operacional futura/handoff.

| Option | Description | Selected |
|--------|-------------|----------|
| Manter alvo canônico e registrar bloqueio (Recomendado) | Preservar `empreganoix.vercel.app` / `empreganoix.onrender.com` como alvo contratual; documentar o host realmente obtido como desvio/bloqueio com mapeamento, sem trocar silenciosamente o "canônico" nos artefatos. | ✓ |
| Adotar o host disponível mais próximo como canônico | Se o nome exato falhar, promover o host real provisionado (ex.: sufixo aleatório) a novo canônico e atualizar docs/config/requisitos para esse valor. | |
| Você decide no momento da execução | Deixar a resolução em aberto para o operador/plano sem uma política pré-definida nesta discussão. | |

**User's choice:** Manter alvo canônico e registrar bloqueio (Recomendado)
**Notes:** Evita drift silencioso do contrato de marca.

| Option | Description | Selected |
|--------|-------------|----------|
| Postura completa de risco operacional (Recomendado) | Documentar: execução real pode estar pendente (dev/local), `NEXT_PUBLIC_*` exige rebuild, Turnstile hostnames/CORS precisam coincidir com a origem real, cron/scheduler dependem de envs corretos, e rollback por reversão de env/config/domínio. | ✓ |
| Apenas riscos de deploy/rebuild | Registrar somente dependências de rebuild/redeploy e sincronização de envs, sem detalhar cron, Turnstile hostnames ou estado dev/local. | |
| Mínimo necessário | Documentar apenas que a validação em produção pode ficar pendente; omitir demais riscos operacionais conhecidos. | |

**User's choice:** Postura completa de risco operacional (Recomendado)
**Notes:** Inclui riscos conhecidos do projeto (dev/local, rebuild, integrações e cron).

| Option | Description | Selected |
|--------|-------------|----------|
| Checkboxes concluídos + notas de evidência/ownership (Recomendado) | Marcar BRND-04, SECR-12 e LIFE-13 como `[x]` com nota apontando para a matriz/evidência de Phase 13 (e preservando o histórico de verificação de código/contrato das fases anteriores), além de atualizar status/notas da Phase 13 no roadmap. | ✓ |
| Só notas, sem mudar checkboxes | Adicionar comentários de alinhamento/pendências, mas manter os checkboxes como estão para evitar sinal de fechamento. | |
| Atualizar apenas o roadmap | Refletir fechamento/progresso no roadmap e deixar `REQUIREMENTS.md` sem alterações nesta fase. | |

**User's choice:** Checkboxes concluídos + notas de evidência/ownership (Recomendado)
**Notes:** Requer consistência entre `docs/DEPLOY.md`, `REQUIREMENTS.md` e `ROADMAP.md`.

| Option | Description | Selected |
|--------|-------------|----------|
| Concluir áreas (Recomendado) | Decisões de rollout, bloqueio de hostname, riscos e traceabilidade já estão claras; posso consolidar no CONTEXT.md. | ✓ |
| Mais perguntas | Quero detalhar runbooks, responsáveis, janelas de deploy ou monitoramento pós-alinhamento. | |

**User's choice:** Concluir áreas (Recomendado)
**Notes:** Usuário confirmou prontidão para gerar o contexto.

---

## OpenCode's Discretion

- Formato exato da matriz/tabela em `docs/DEPLOY.md`, nomes de seções e granularidade da redação.
- Seleção precisa de arquivos de exemplo/env dentro do escopo acordado, sem expor segredos.
- Ajustes documentais/exemplos em `scripts/verify-deploy.ps1` que preservem utilidade sem conflitar com o alvo canônico.
- Redação final das notas de caveat/handoff e referências cruzadas entre `docs/DEPLOY.md`, `REQUIREMENTS.md` e `ROADMAP.md`.

## Deferred Ideas

- Provisionamento/execução real de deploy, rebuild e smoke gate nos hosts canônicos (handoff operacional).
- Domínio próprio e redirects de produção.
- Renomeação de identificadores internos legados não voltados ao usuário (ex.: `nqu-backend`, `nqu_admin_token`).
- Detalhamento operacional adicional (responsáveis, janelas, monitoramento) não solicitado nesta discussão.
