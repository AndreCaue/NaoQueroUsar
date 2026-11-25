# Phase 31: Independent Publish Pipeline - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-11-25
**Phase:** 31-independent-publish-pipeline
**Areas discussed:** Modelo de execução FB+IG, Estados IG 2-passos/ambiguidade

---

## Modelo de execução FB+IG

### Q1: Como o worker/ciclo deve processar Facebook e Instagram para garantir independência (PUBL-01) com o mínimo de acoplamento?

| Option | Description | Selected |
|--------|-------------|----------|
| Ciclo por provider (Recomendado) | Generalizar o ciclo para receber/iterar providers (ex.: facebook, instagram), mantendo claim/processamento por item e contadores agregados; falha de um post/provider não afeta o outro. Reaproveita worker/cron e o padrão atual de `list_due_for_claim(provider=...)`. | ✓ |
| Claim único multi-provider | Remover filtro de provider no claim e despachar por `post.provider` dentro do processamento. Simplifica a fila, mas exige dispatcher interno mais genérico e cuidado extra com contadores/locks mistos. | |
| Ciclos separados por provider | Manter ciclos/entrypoints distintos para FB e IG (worker ou chamadas separadas). Isola bem operacionalmente, mas duplica orquestração e pode divergir comportamento com o tempo. | |
| You decide | Deixo o OpenCode escolher a estrutura mais simples que preserve PUBL-01 e os padrões atuais de claim/retry/idempotência. | |

**User's choice:** Ciclo por provider (Recomendado)
**Notes:** Nenhuma nota adicional.

### Q2: Como os gatilhos existentes (worker cron `/admin/social/worker` e retry/dispatch por `post_id`) devem tratar providers após generalizar o ciclo?

| Option | Description | Selected |
|--------|-------------|----------|
| Worker drena todos; retry infere provider (Recomendado) | `/admin/social/worker` processa todos os providers suportados (fb+ig) em blocos independentes na mesma invocação, agregando contadores; retry/dispatch por `post_id` carrega o post e usa seu `provider`. Mantém endpoint simples e respeita PUBL-01. | ✓ |
| Worker por provider explícito | Worker aceita parâmetro/provider (ou endpoints separados) e processa só o provider pedido; retry também exige provider. Dá controle operacional, mas aumenta superfície/configuração de cron/admin. | |
| Worker único FB+IG sempre separado externamente | Mantém endpoint atual só FB e cria endpoint/cron separado para IG. Isola execução, mas duplica contratos operacionais e risco de esquecimento em deploy. | |
| You decide | Deixo o OpenCode escolher o modelo de trigger mais simples e seguro para operar FB+IG independentemente. | |

**User's choice:** Worker drena todos; retry infere provider (Recomendado)
**Notes:** Nenhuma nota adicional.

### Q3: Qual fronteira de código você prefere para suportar FB e IG sem acoplar regras específicas?

| Option | Description | Selected |
|--------|-------------|----------|
| Core compartilhado + handler por provider (Recomendado) | Manter núcleo comum de claim/attempt/log/idempotência/backoff e extrair um handler/adapter por provider (conta/credenciais, payload, publisher, mapeamento de erros). Reaproveita `SocialPublisher`/`PublishResult` e isola bugs de IG do FB. | ✓ |
| Pipelines separados por provider | Criar pipeline IG paralelo ao FB, copiando estrutura e ajustando regras. Isolamento máximo, mas duplica lógica sensível (idempotência, ambiguidade, logs seguros) e aumenta risco de divergência. | |
| Dispatcher simples dentro do pipeline atual | Adicionar condicionais `if provider == ...` no `publish_pipeline.py` atual. Menos arquivos agora, mas tende a crescer rápido com PUBL-02/04/05 e dificulta manter independência clara. | |
| You decide | Deixo o OpenCode escolher a fronteira mais simples que preserve isolamento e reutilize os padrões existentes. | |

**User's choice:** Core compartilhado + handler por provider (Recomendado)
**Notes:** Nenhuma nota adicional.

### Q4: Como reportar resultado do worker quando ele drenar FB e IG na mesma invocação?

| Option | Description | Selected |
|--------|-------------|----------|
| Agregado + breakdown por provider (Recomendado) | Manter contadores totais para compatibilidade e adicionar breakdown por provider (facebook/instagram) no response/log. Facilita operação sem quebrar consumidores atuais; cada provider roda em bloco isolado. | ✓ |
| Só agregado total | Preservar exatamente o formato atual de contadores somando FB+IG. Menos mudança de contrato, mas operador perde visibilidade rápida de qual plataforma falhou. | |
| Só por provider, sem total compatível | Retornar estrutura separada por provider e remover/alterar formato atual. Mais explícito, mas pode quebrar testes/consumidores do worker. | |
| You decide | Deixo o OpenCode escolher o formato de resultado mais seguro para compatibilidade e observabilidade. | |

**User's choice:** Agregado + breakdown por provider (Recomendado)
**Notes:** Nenhuma nota adicional.

### Q5: Como o claim deve tratar posts com `publish_enabled=false` (ex.: IG desativado na revisão após agendamento/rascunho)?

| Option | Description | Selected |
|--------|-------------|----------|
| Ignorar no claim (Recomendado) | `list_due_for_claim` só considera posts elegíveis com `publish_enabled=true`; posts desativados não são claimados nem mutados pelo worker. Evita publicar algo que o admin desligou e mantém estado atual para reativação manual. | ✓ |
| Claimar e bloquear com erro seguro | Worker claima o post, marca como falha/bloqueado com mensagem segura "publicação desativada". Dá visibilidade no histórico, mas gera mutação/ruído para uma escolha intencional do admin. | |
| Cancelar automaticamente | Ao detectar `publish_enabled=false` em item elegível, mudar status para `cancelled`. Torna explícito, mas é destrutivo e pode surpreender se o admin reativar depois. | |
| You decide | Deixo o OpenCode escolher o comportamento mais seguro e previsível para publish_enabled. | |

**User's choice:** Ignorar no claim (Recomendado)
**Notes:** Nenhuma nota adicional.

### Q6: No fluxo de aprovação/dispatch imediato, como disparar publicação quando FB e IG estiverem habilitados?

| Option | Description | Selected |
|--------|-------------|----------|
| Dispatch independente por post/provider (Recomendado) | Para cada `social_post` elegível (fb/ig), disparar processamento independente (background/worker) por `post_id`; falha/timeout em um não afeta o outro. Alinha com PUBL-01 e com o modelo atual de `process_social_post_safe(post_id)`. | ✓ |
| Dispatch sequencial no mesmo background task | Processar FB e depois IG no mesmo task, isolando exceções. Simples, mas compartilha o mesmo ciclo de vida do task e pode atrasar o segundo provider. | |
| Só cron/worker periódico, sem dispatch imediato | Aprovação apenas marca/agenda e o worker periódico drena depois. Mais simples, mas aumenta latência percebida para “publicar agora”. | |
| You decide | Deixo o OpenCode escolher o modo de dispatch imediato mais seguro e consistente com o comportamento atual. | |

**User's choice:** Dispatch independente por post/provider (Recomendado)
**Notes:** Nenhuma nota adicional.

### Q7: Quando o post IG está elegível, mas a integração IG não está pronta (sem conta pronta, token inválido, needs_reconnect), qual comportamento do pipeline?

| Option | Description | Selected |
|--------|-------------|----------|
| Falha final com erro acionável (Recomendado) | Marcar como `failed` final (sem auto-retry) com mensagem segura em pt-BR orientando reconexão/verificação em Integrações, como o FB faz hoje. Evita retry storm e deixa estado claro ao admin. | ✓ |
| Falha retryable até reconectar | Manter em retry automático com backoff enquanto não reconectar. Pode gerar tentativas inúteis e ruído; só seria aceitável com limite rígido. | |
| Deixar agendado/bloqueado sem tentativa | Não tentar publicar e manter item pendente com estado bloqueado. Evita falha, mas exige novo estado/semântica e pode esconder que houve tentativa esperada. | |
| You decide | Deixo o OpenCode escolher o comportamento mais seguro, alinhado ao padrão atual e ao PUBL-05. | |

**User's choice:** Falha final com erro acionável (Recomendado)
**Notes:** Nenhuma nota adicional.

### Q8: Dentro de uma mesma invocação do worker, FB e IG devem ser processados como?

| Option | Description | Selected |
|--------|-------------|----------|
| Sequencial por provider, isolado (Recomendado) | Processar um provider por vez (ex.: FB depois IG), cada um em bloco isolado com seus próprios claims/processamentos. Simples, previsível e suficiente para o volume esperado. | ✓ |
| Paralelo por provider | Processar FB e IG em paralelo na mesma invocação. Pode reduzir latência total, mas aumenta complexidade de concorrência, conexões DB e diagnóstico de falhas. | |
| Intercalado por post (fila única) | Claimar posts de ambos providers numa ordem única e processar misturado. Maximiza uso da fila, mas torna mais difícil isolar e raciocinar sobre limites por provider. | |
| You decide | Deixo o OpenCode escolher a estratégia de ordenação mais segura para o volume e isolamento necessários. | |

**User's choice:** Sequencial por provider, isolado (Recomendado)
**Notes:** Nenhuma nota adicional.

---

## Estados IG 2-passos/ambiguidade

### Q1: Se houver timeout/resultado ambíguo após criar o container IG (ou antes de confirmar publish), como o pipeline deve se recuperar?

| Option | Description | Selected |
|--------|-------------|----------|
| Bloquear para verificação/reconciliação (Recomendado) | Persistir `container_id`/IDs conhecidos, marcar estado ambíguo seguro sem auto-retry, e exigir verificação/reconciliação (manual ou ação explícita) antes de nova tentativa. Elimina risco de duplicação cega conforme PUBL-04. | ✓ |
| Retomar só pelo mesmo container após check seguro | Se houver `container_id`, permitir retomada automática apenas após checagem de status conclusiva do container/publicação (sem criar novo container). Mais automatizado, mas exige máquina de estados cuidadosa. | |
| Falhar final e exigir novo fluxo manual | Tratar ambiguidade como falha final sem reuso de container; admin decide republicar manualmente. Simples, mas pode perder chance de reconciliação segura e aumenta trabalho operacional. | |
| You decide | Deixo o OpenCode escolher a estratégia mais segura contra duplicação, dentro de PUBL-04. | |

**User's choice:** Bloquear para verificação/reconciliação (Recomendado)
**Notes:** Nenhuma nota adicional.

### Q2: Onde persistir IDs/estado do fluxo IG (container, post/mídia publicada, permalink) para auditoria e reconciliação (PUBL-03)?

| Option | Description | Selected |
|--------|-------------|----------|
| Colunas explícitas em `social_posts` (Recomendado) | Adicionar campos dedicados (ex.: container id, permalink, IDs/estado de publicação IG) além dos campos atuais; `external_post_id` pode representar o ID final publicado. Facilita consulta, auditoria e lógica de reconciliação. | ✓ |
| JSON/metadata genérico | Armazenar payload/metadata IG em um campo JSON único. Flexível, mas menos tipado, mais difícil de consultar/indexar e mais propenso a drift. | |
| Apenas em logs de tentativa | Guardar IDs somente em `social_post_logs`. Mantém tabela simples, mas dificulta saber o estado atual canônico para retry/reconciliação. | |
| You decide | Deixo o OpenCode escolher o modelo de persistência mais claro para auditoria e segurança operacional. | |

**User's choice:** Colunas explícitas em `social_posts` (Recomendado)
**Notes:** Nenhuma nota adicional.

### Q3: No fluxo de 2 passos, quando o pipeline deve consultar o status do container antes do publish?

| Option | Description | Selected |
|--------|-------------|----------|
| Polling limitado quando necessário (Recomendado) | Após criar container, consultar status só quando necessário (ex.: não concluído/in_progress), com limite curto de tentativas/espera dentro do orçamento de timeout; se expirar sem conclusão segura, tratar como ambíguo/bloqueado. Alinha com PUBL-02. | ✓ |
| Sempre checar status uma vez | Sempre fazer um check de status antes do publish, mesmo se não indicado. Mais simples, mas adiciona chamada extra em todos os casos e ainda precisa lidar com in_progress. | |
| Não checar status; tentar publish direto | Pular polling e ir direto para publish, tratando erros conforme resposta. Menos chamadas, mas pode falhar mais em containers ainda processando e complicar tratamento de timeout. | |
| You decide | Deixo o OpenCode escolher a estratégia de status check mais segura dentro do timeout e das regras da Graph API. | |

**User's choice:** Polling limitado quando necessário (Recomendado)
**Notes:** Nenhuma nota adicional.

### Q4: Como representar um caso ambíguo IG no modelo/status para o admin e para o bloqueio de retry automático?

| Option | Description | Selected |
|--------|-------------|----------|
| `failed` + bloqueio de reconciliação (Recomendado) | Reusar status `failed` com erro seguro específico e metadados de reconciliação (container/IDs conhecidos, motivo bloqueado). Preserva enum atual e o padrão já usado no Facebook, exigindo ação explícita antes de retry. | ✓ |
| Novo status dedicado `ambiguous` | Adicionar status explícito no enum/modelo para ambiguidade. Fica muito claro na UI/auditoria, mas exige migration, atualização de schemas, filtros, transições e testes em vários pontos. | |
| `publishing` travado até reconciliação | Manter em `publishing` como sinal de pendência. Evita novo status de falha, mas confunde "em andamento" com "precisa ação humana" e complica claims/timeout. | |
| You decide | Deixo o OpenCode escolher a representação mais clara e segura, minimizando churn desnecessário. | |

**User's choice:** `failed` + bloqueio de reconciliação (Recomendado)
**Notes:** Nenhuma nota adicional.

### Q5: Quando o admin acionar retry manual em um post IG ambíguo com `container_id` conhecido, o que o sistema deve fazer?

| Option | Description | Selected |
|--------|-------------|----------|
| Reconciliar antes de publicar (Recomendado) | Antes de qualquer novo publish, consultar status/resultado do container ou mídia publicada; se já publicado, registrar IDs/permalink e concluir; se container pronto, publicar o mesmo container; se expirado/inválido, falhar com orientação segura. Nunca criar novo container cegamente. | ✓ |
| Permitir retry manual normal (novo ciclo) | Tratar como retry comum e deixar o pipeline decidir. Mais simples, mas corre risco de criar novo container/publicação se não houver guarda específica para ambiguidade IG. | |
| Bloquear retry até marcação manual externa | Não permitir retry no sistema até alguém confirmar fora da plataforma. Mais seguro contra bugs, mas operacionalmente pesado e lento. | |
| You decide | Deixo o OpenCode escolher o fluxo de retry manual mais seguro contra duplicação. | |

**User's choice:** Reconciliar antes de publicar (Recomendado)
**Notes:** Nenhuma nota adicional.

### Q6: Como tratar orçamento de tempo no fluxo IG de 2 passos (criar container, checar status, publicar)?

| Option | Description | Selected |
|--------|-------------|----------|
| Orçamento limitado por tentativa (Recomendado) | Definir timeout por chamada HTTP e um orçamento total limitado por tentativa; se estourar após ponto crítico (ex.: container criado/publicação enviada), marcar ambíguo/bloqueado para reconciliação. Evita worker preso e respeita PUBL-02. | ✓ |
| Só timeout por chamada HTTP | Aplicar timeout individual nas chamadas Graph, sem orçamento total explícito. Simples, mas várias esperas/polls podem alongar demais a tentativa. | |
| Esperar até concluir (sem orçamento curto) | Dar mais tempo para container ficar pronto/publicar. Pode reduzir falsos ambíguos, mas prende worker e aumenta risco operacional. | |
| You decide | Deixo o OpenCode definir o orçamento de timeout mais seguro para operação e reconciliação. | |

**User's choice:** Orçamento limitado por tentativa (Recomendado)
**Notes:** Nenhuma nota adicional.

### Q7: Como classificar respostas do container IG (FINISHED/IN_PROGRESS/ERROR/EXPIRED) no pipeline?

| Option | Description | Selected |
|--------|-------------|----------|
| Conclusivo segue fluxo; inconclusivo bloqueia (Recomendado) | `FINISHED` segue para publish; `IN_PROGRESS` entra em polling limitado; `ERROR/EXPIRED` vira falha conclusiva (nova tentativa pode criar novo container, se elegível e sem ambiguidade de publish); timeout/inconclusivo vira ambíguo bloqueado. Alinha com PUBL-02/PUBL-04. | ✓ |
| Qualquer falha de container vira ambígua | Tratar ERROR/EXPIRED/timeout tudo como ambíguo. Mais conservador contra duplicação, mas cria muitos casos manuais desnecessários. | |
| ERROR/EXPIRED sempre retry automático imediato | Recriar container automaticamente. Pode ser seguro quando publish não ocorreu, mas precisa garantir que não houve publish ambíguo; arriscado se classificação for imprecisa. | |
| You decide | Deixo o OpenCode escolher a classificação mais segura e operacional. | |

**User's choice:** Conclusivo segue fluxo; inconclusivo bloqueia (Recomendado)
**Notes:** Nenhuma nota adicional.

### Q8: Após publish IG bem-sucedido, como tratar o permalink?

| Option | Description | Selected |
|--------|-------------|----------|
| Buscar best-effort na mesma tentativa (Recomendado) | Depois de obter o ID da mídia publicada, tentar buscar permalink em chamada separada; se falhar, manter post como publicado com ID e sem permalink (sem reverter sucesso). Atende PUBL-03 "quando disponível". | ✓ |
| Não buscar permalink no pipeline | Persistir apenas IDs e status; permalink fica ausente até consulta futura/manual. Mais simples, mas reduz valor operacional/auditoria imediata. | |
| Buscar sob demanda na UI/status | Buscar permalink quando admin abrir status. Evita custo no publish, mas adiciona dependência Graph em leituras e pode falhar quando token/rede estiverem ruins. | |
| You decide | Deixo o OpenCode escolher o momento mais seguro e útil para capturar permalink. | |

**User's choice:** Buscar best-effort na mesma tentativa (Recomendado)
**Notes:** Nenhuma nota adicional.

### Q9: Na UI/operação admin, como expor a ação para casos IG ambíguos bloqueados?

| Option | Description | Selected |
|--------|-------------|----------|
| Reusar retry com semântica de reconciliação (Recomendado) | Manter ação de retry, mas com texto/estado deixando claro que será feita reconciliação segura (checar status/IDs antes de publicar). Aproveita endpoint/padrão atual, reduz nova superfície. | ✓ |
| Ação separada "Reconciliar/Verificar" | Criar ação distinta para ambíguos. Mais explícito, mas adiciona novo endpoint/estado/UI e duplica parte do fluxo de retry. | |
| Sem ação no sistema; só orientação externa | Apenas mostrar mensagem para verificar no Instagram/Meta. Seguro, mas ruim de operar e não aproveita IDs já persistidos. | |
| You decide | Deixo o OpenCode escolher a forma mais clara e segura para o operador. | |

**User's choice:** Reusar retry com semântica de reconciliação (Recomendado)
**Notes:** Nenhuma nota adicional.

### Q10: Qual granularidade de auditoria por tentativa você quer para o fluxo IG de 2 passos?

| Option | Description | Selected |
|--------|-------------|----------|
| Eventos principais por tentativa (Recomendado) | Registrar resultado final da tentativa e resumos seguros dos passos principais (criação container, status check, publish, busca permalink), sem payloads sensíveis. Bom equilíbrio entre depuração e segurança. | ✓ |
| Apenas resultado final da tentativa | Manter um log simples por tentativa como hoje. Menos ruído, mas dificulta diagnosticar em qual passo do 2-passos falhou. | |
| Log detalhado de cada chamada HTTP | Registrar cada request/response relevante. Máximo detalhe, mas maior risco de vazar dados sensíveis e mais volume de logs. | |
| You decide | Deixo o OpenCode escolher a granularidade segura e útil para auditoria. | |

**User's choice:** Eventos principais por tentativa (Recomendado)
**Notes:** Nenhuma nota adicional.

### Q11: Casos IG ambíguos bloqueados devem expirar automaticamente depois de algum tempo, ou permanecer bloqueados até ação humana?

| Option | Description | Selected |
|--------|-------------|----------|
| Permanecer até verificação/reconciliação (Recomendado) | Mantém estado seguro indefinidamente até o admin/fluxo de reconciliação confirmar o resultado. Evita qualquer duplicação tardia por retry automático. | ✓ |
| Expirar e virar retryable após janela | Após X horas/dias, liberar nova tentativa automática. Reduz intervenção manual, mas reintroduz risco se a publicação original tiver sido concluída fora da visibilidade. | |
| Expirar e marcar como falha final definitiva | Fechar automaticamente após janela sem publicar. Evita duplicação, mas pode perder publicação válida que só precisava reconciliação. | |
| You decide | Deixo o OpenCode escolher a política de expiração mais segura. | |

**User's choice:** Permanecer até verificação/reconciliação (Recomendado)
**Notes:** Nenhuma nota adicional.

### Q12: Se a reconciliação detectar que o container/mídia IG já foi publicado com sucesso, o que o sistema deve fazer?

| Option | Description | Selected |
|--------|-------------|----------|
| Atualizar local como publicado (Recomendado) | Registrar IDs/permalink/timestamps, marcar `published`, limpar erro ambíguo e anexar log de reconciliação. Mantém auditoria consistente sem nova publicação. | ✓ |
| Apenas informar o admin, sem atualizar estado | Mostrar diagnóstico, mas deixar o registro ambíguo/falhado. Evita escrita automática, mas mantém estado incorreto e confuso. | |
| Atualizar só após confirmação manual extra | Exigir que admin confirme antes de gravar o estado publicado. Mais cauteloso, mas adiciona fricção desnecessária quando a evidência da Graph é conclusiva. | |
| You decide | Deixo o OpenCode escolher o comportamento mais seguro e consistente para reconciliação. | |

**User's choice:** Atualizar local como publicado (Recomendado)
**Notes:** Nenhuma nota adicional.

---

## OpenCode's Discretion

- Rate limit e limite diário (PUBL-05): área não discutida; OpenCode deve cumprir PUBL-05 (classificação 2207042/rate limit, `content_publishing_limit` como autoridade runtime quando aplicável, sem retry storm, estado acionável).
- Status e auditoria no admin (PUBL-03): superfície UI/API detalhada não discutida; OpenCode deve cumprir PUBL-03 (status por plataforma, erro seguro, IDs/permalink quando disponíveis, tentativas/timestamps, histórico/auditoria sem segredos).
- Nomes exatos de campos/colunas, shape de breakdown do worker, orçamentos numéricos de timeout/polling e wording pt-BR exato, desde que seguros e consistentes.

## Deferred Ideas

- Rate limit e limite diário (PUBL-05) — não discutido nesta sessão; requisitos continuam obrigatórios.
- Status e auditoria no admin (PUBL-03) — detalhes de UI não discutidos; requisitos continuam obrigatórios.
- Agendamento avançado, múltiplas contas IG, Stories/Reels/carrossel, métricas/analytics, inbox de comentários/DMs — fora do escopo v1.5.
