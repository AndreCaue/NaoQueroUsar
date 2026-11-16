# Phase 17: Publicação Assíncrona, Retry, Idempotência e Status - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-11-16
**Phase:** 17-publicacao-assincrona-retry-idempotencia-e-status
**Areas discussed:** Disparo e processamento, Retry e falhas, Idempotência e duplicatas, Status e ações no admin

---

## Disparo e processamento

| Option | Description | Selected |
|--------|-------------|----------|
| Imediata + cron (Recomendado) | Dispara tentativa assíncrona logo após aprovar (sem bloquear resposta) e o cron/worker continua como rede de segurança para retries/agendados. | ✓ |
| Só pelo worker/cron | A aprovação apenas deixa o post elegível (scheduled); a publicação ocorre no próximo ciclo do cron (1-5 min). | |
| You decide | Deixe o OpenCode escolher a abordagem mais adequada ao código e deploy atuais. | |

**User's choice:** Imediata + cron (Recomendado)
**Notes:** Para "Publicar agora", priorizar entrega rápida sem bloquear a aprovação.

| Option | Description | Selected |
|--------|-------------|----------|
| Reusar CRON_SECRET (Recomendado) | Mesmo padrão de /admin/expire (header X-Cron-Secret/require_cron_secret), um único segredo de cron para jobs operacionais. | ✓ |
| SOCIAL_WORKER_SECRET separado | Usar o segredo SOCIAL_WORKER_SECRET já previsto na config para isolar o worker social dos demais crons. | |
| You decide | Definir o esquema de autenticação mais consistente com a segurança e config atuais. | |

**User's choice:** Reusar CRON_SECRET (Recomendado)
**Notes:** Manter consistência com endpoint operacional existente.

| Option | Description | Selected |
|--------|-------------|----------|
| Sim, pipeline único (Recomendado) | Reaproveita a mesma lógica de lock/claim, transições de status, logging e idempotência para tentativa imediata e cron. | ✓ |
| Não, caminhos separados | Tentativa imediata implementada à parte do worker; exige cuidado extra para não divergir em locks/retries. | |
| You decide | Escolher o desenho que melhor equilibra segurança contra duplicatas e simplicidade. | |

**User's choice:** Sim, pipeline único (Recomendado)
**Notes:** Unificar claim/publicação para reduzir risco de duplicatas e divergência.

| Option | Description | Selected |
|--------|-------------|----------|
| Agendados + retries vencidos (Recomendado) | Processa posts em scheduled com scheduled_at <= agora e posts failed elegíveis a retry com next_retry_at <= agora (respeitando limite). | ✓ |
| Incluir recuperação de 'publishing' travado | Além dos anteriores, recupera itens presos em publishing por tempo excessivo para evitar jobs órfãos. | |
| You decide | Definir o critério de elegibilidade mais seguro para operação no Render/cron. | |

**User's choice:** Agendados + retries vencidos (Recomendado)
**Notes:** Critério de elegibilidade base focado em agendados e retries vencidos.

---

## Retry e falhas

| Option | Description | Selected |
|--------|-------------|----------|
| Transitória vs permanente (Recomendado) | Transitórias (rede, 5xx, timeout/rate limit) entram em backoff até o limite; permanentes falham sem retry automático. | ✓ |
| Quase tudo com retry | Tentar retry automático para a maioria dos erros, confiando no limite de tentativas para parar. | |
| You decide | Definir classificação segura alinhada ao Graph API e às configs existentes. | |

**User's choice:** Transitória vs permanente (Recomendado)
**Notes:** Usar backoff configurável e evitar retries inúteis em falhas definitivas.

| Option | Description | Selected |
|--------|-------------|----------|
| Falha bloqueante até reconectar (Recomendado) | Registrar falha não-retryable/bloqueada com erro resumido orientando reconexão; sem loop automático sem conexão válida. | ✓ |
| Manter em retry automático | Continuar agendando retries pelo backoff mesmo sem conexão válida. | |
| You decide | Escolher o comportamento mais claro e seguro para o admin. | |

**User's choice:** Falha bloqueante até reconectar (Recomendado)
**Notes:** Conta desconectada/needs_reconnect não deve gerar retries automáticos sem efeito.

| Option | Description | Selected |
|--------|-------------|----------|
| Failed final, retry só manual (Recomendado) | Marca como failed sem next_retry_at automático; permite "Tentar novamente" manual quando elegível. | ✓ |
| Continuar tentando indefinidamente | Ignora limite prático e segue reagendando. | |
| You decide | Definir comportamento consistente com as configs de retry/backoff. | |

**User's choice:** Failed final, retry só manual (Recomendado)
**Notes:** Respeitar SOCIAL_MAX_ATTEMPTS/SOCIAL_RETRY_DELAYS.

| Option | Description | Selected |
|--------|-------------|----------|
| Mensagem amigável pt-BR (Recomendado) | Exibir resumo claro e seguro em português, sem detalhes sensíveis ou payloads brutos. | ✓ |
| Resumo técnico sanitizado | Mostrar código/motivo técnico resumido (sanitizado) para diagnóstico mais direto. | |
| You decide | Escolher o formato mais útil para operação de um admin único. | |

**User's choice:** Mensagem amigável pt-BR (Recomendado)
**Notes:** Erro resumido deve orientar ação (ex.: reconectar, tentar depois).

---

## Idempotência e duplicatas

| Option | Description | Selected |
|--------|-------------|----------|
| Claim atômico no banco (Recomendado) | Selecionar elegíveis com FOR UPDATE SKIP LOCKED e transicionar para publishing antes de chamar a Graph API. | ✓ |
| Somente checagens de status | Confiar em leituras/condições sem lock de claim forte. | |
| You decide | Adotar o mecanismo mais robusto conforme a stack Postgres/SQLAlchemy atual. | |

**User's choice:** Claim atômico no banco (Recomendado)
**Notes:** Evitar concorrência entre cron, tentativa imediata e retry manual.

| Option | Description | Selected |
|--------|-------------|----------|
| No-op seguro (Recomendado) | Com external_post_id/publicado, não reenviar; reconciliar estado/timestamps com segurança. | ✓ |
| Tentar publicar novamente | Reenviar mesmo com ID externo existente. | |
| You decide | Garantir comportamento idempotente alinhado ao requisito de não duplicar. | |

**User's choice:** No-op seguro (Recomendado)
**Notes:** Reexecuções e cliques repetidos não devem criar duplicatas.

| Option | Description | Selected |
|--------|-------------|----------|
| Evitar duplicata (Recomendado) | Em sucesso remoto incerto, não republicar automaticamente; registrar estado/alerta e exigir verificação/retry manual consciente. | ✓ |
| Priorizar publicar | Permitir nova tentativa automática mesmo com incerteza. | |
| You decide | Escolher mitigação idempotente mais adequada ao risco operacional. | |

**User's choice:** Evitar duplicata (Recomendado)
**Notes:** Preferência explícita por não duplicar em cenários ambíguos.

| Option | Description | Selected |
|--------|-------------|----------|
| Sim, mesmo fluxo (Recomendado) | "Tentar novamente" reaproveita pipeline/locks e só executa quando elegível; ignora cliques repetidos. | ✓ |
| Fluxo dedicado sem claim | Implementar retry manual separado. | |
| You decide | Definir abordagem mais segura para ação manual. | |

**User's choice:** Sim, mesmo fluxo (Recomendado)
**Notes:** Retry manual deve ser idempotente e consistente com o worker.

---

## Status e ações no admin

| Option | Description | Selected |
|--------|-------------|----------|
| No fluxo de revisão/edição (Recomendado) | Exibir status social no contexto da vaga em revisão (card/linha e/ou diálogo). | ✓ |
| Nova visão de vagas/publicações | Criar área/listagem admin para acompanhar vagas com status social. | |
| You decide | Escolher local com menor complexidade coerente. | |

**User's choice:** No fluxo de revisão/edição (Recomendado)
**Notes:** Manter status próximo ao contexto de draft/aprovação quando possível.

| Option | Description | Selected |
|--------|-------------|----------|
| Mapear todos os estados (Recomendado) | Rótulos pt-BR para sem rascunho, rascunho, agendado, publicando, publicado (com link), falhou (com erro) e cancelado. | ✓ |
| Apenas publicado/falhou/agendado | Mostrar só estados mais operacionais. | |
| You decide | Definir conjunto de badges mais útil. | |

**User's choice:** Mapear todos os estados (Recomendado)
**Notes:** Incluir erro resumido e link do post quando publicado.

| Option | Description | Selected |
|--------|-------------|----------|
| Falhas elegíveis com conta conectada (Recomendado) | Habilitar para falhas não publicadas com integração conectada; desabilitar/ocultar quando publicado, em processamento, agendado futuro normal ou reconexão necessária. | ✓ |
| Só após esgotar retries automáticos | Permitir retry manual apenas em failed final. | |
| You decide | Definir regras de elegibilidade seguras e consistentes. | |

**User's choice:** Falhas elegíveis com conta conectada (Recomendado)
**Notes:** Ação manual deve respeitar elegibilidade e estado da integração.

| Option | Description | Selected |
|--------|-------------|----------|
| Nova lista de posts/vagas sociais (Recomendado) | Visão simples no admin para acompanhar agendado/publicado/falhou, ver link/erro e retentar quando elegível. | ✓ |
| Seção por vaga nas Integrações | Mostrar registros sociais vinculados dentro da área de Integrações. | |
| Somente no contexto atual de revisão | Não criar nova visão; pode limitar acompanhamento pós-aprovação. | |

**User's choice:** Nova lista de posts/vagas sociais (Recomendado)
**Notes:** Necessário para acompanhar e retentar posts depois que a vaga sai da fila de revisão.

---

## OpenCode's Discretion

- Detalhes de endpoints/payloads/paths, agendamento da tentativa imediata, batch/limites por ciclo, mapeamento fino de erros Graph para categorias/textos pt-BR, uso de `social_post_logs`, derivação do link público do post e composição visual da UI admin, desde que alinhados às decisões D-01..D-15 e sem expor segredos.

## Deferred Ideas

- Recuperação automática avançada de itens presos em `publishing` (não selecionada como critério base nesta discussão).
- Instagram, múltiplas páginas/admins, métricas/insights, sincronização de edição/remoção de posts.
- Testes, documentação operacional/App Review e fechamento de gaps/evidências v1.1 (Phase 18).
