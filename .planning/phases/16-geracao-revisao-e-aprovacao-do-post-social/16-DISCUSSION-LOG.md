# Phase 16: Geração, Revisão e Aprovação do Post Social - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-11-15
**Phase:** 16-geracao-revisao-e-aprovacao-do-post-social
**Areas discussed:** Ciclo do rascunho social, Editor e agendamento na revisão, Aprovar vaga + registrar post social (seguro), Conteúdo, URL pública e política sem contato

---

## Ciclo do rascunho social

| Option | Description | Selected |
|--------|-------------|----------|
| Sob demanda no editor (Recomendado) | O revisor abre a vaga e clica em "Gerar post"/"Gerar rascunho". Evita chamadas Groq ao listar a fila e gera/salva draft apenas quando necessário. | ✓ |
| Ao abrir o editor da vaga | Gera automaticamente se não existir draft ao abrir o editor; adiciona espera/possível falha de LLM a cada abertura inicial. | |
| Em lote/automático na fila | Gera drafts em background para itens da fila; aumenta custo/complexidade e chamadas sem ação explícita. | |
| You decide (OpenCode) | Definir automaticamente o melhor ponto de geração. | |

**User's choice:** Sob demanda no editor (Recomendado)
**Notes:** Integrado ao fluxo de revisão; geração explícita pelo revisor.

| Option | Description | Selected |
|--------|-------------|----------|
| Upsert do draft + regenerar sobrescreve (Recomendado) | Um único `social_post` por vaga/provider (`facebook`): gerar/editar/regenerar atualiza o mesmo registro em `draft`. | ✓ |
| Upsert, mas confirmar antes de sobrescrever edição | Pede confirmação se draft já editado manualmente antes de regenerar. | |
| Recriar/substituir registro a cada geração | Apaga/recria o registro ao gerar; arriscado e conflita com unicidade. | |
| You decide (OpenCode) | Escolher estratégia segura e simples compatível com unicidade. | |

**User's choice:** Upsert do draft + regenerar sobrescreve (Recomendado)
**Notes:** Respeitar unicidade `(job_id, provider)`.

| Option | Description | Selected |
|--------|-------------|----------|
| Serviço de post com Groq + template local (Recomendado) | Serviço dedicado reaproveita Groq/config existente; fallback por template determinístico se LLM falhar — revisão nunca bloqueada. | ✓ |
| Só template nesta fase, IA depois | Apenas template; não atende POST-01 completo. | |
| LLM obrigatório sem fallback automático | Bloqueia em falha; contraria fallback/revisão nunca bloqueada. | |
| You decide (OpenCode) | Definir abordagem que cumpra POST-01/02 com menor risco. | |

**User's choice:** Serviço de post com Groq + template local (Recomendado)
**Notes:** Reuso de `backend/app/services/extraction/client.py`/config Groq como referência; texto pt-BR com CTA+link.

| Option | Description | Selected |
|--------|-------------|----------|
| Sempre usar estado atual salvo da vaga (Recomendado) | Gerar/regenerar a partir do `Job` persistido mais recente (após salvar edições). | ✓ |
| Usar snapshot do momento da primeira geração | Fixa dados iniciais; pode desalinhar com edições posteriores. | |
| Usar valores do formulário mesmo sem salvar | Usa estado não persistido; pode divergir do que será aprovado. | |
| You decide (OpenCode) | Fonte de dados mais consistente com fluxo salvar/editar/aprovar. | |

**User's choice:** Sempre usar estado atual salvo da vaga (Recomendado)
**Notes:** Evitar divergência entre vaga publicada e post.

---

## Editor e agendamento na revisão

| Option | Description | Selected |
|--------|-------------|----------|
| Seção no EditJobDialog (Recomendado) | Adicionar seção "Post para redes sociais" dentro do modal de edição existente (`EditJobDialog.tsx`). | ✓ |
| Painel/modal dedicado de post social | Dialog separado acessado pela linha; mais navegação entre vaga e post. | |
| Página/detalhe própria por vaga na revisão | Nova rota/tela; mudança maior na estrutura `/admin/review`. | |
| You decide (OpenCode) | Equilíbrio entre coesão e clareza. | |

**User's choice:** Seção no EditJobDialog (Recomendado)
**Notes:** Manter contexto da vaga + texto-fonte.

| Option | Description | Selected |
|--------|-------------|----------|
| Conjunto completo essencial (Recomendado) | Textarea, contador ~700, gerar/regenerar com loading, preview simples, indicadores de origem/erro/fallback. | ✓ |
| Mínimo: editar + regenerar + contador | Sem preview reduzido; atende básico. | |
| Editor rico com validações extras | Avisos/bloqueios/formatação assistida; mais complexidade. | |
| You decide (OpenCode) | Controles suficientes para POST-03 com implementação enxuta. | |

**User's choice:** Conjunto completo essencial (Recomendado)
**Notes:** Inclui preview e indicadores de fallback/erro.

| Option | Description | Selected |
|--------|-------------|----------|
| Toggle Agora/Agendar com datetime em SP (Recomendado) | Padrão "Publicar agora"; "Agendar" com data/hora em `America/Sao_Paulo`, persistida de forma inequívoca. | ✓ |
| Sempre agendar com "agora" como atalho | Campo único pré-preenchido; menos explícito. | |
| Apenas "publicar agora" nesta fase | Não atende POST-04/agendamento. | |
| You decide (OpenCode) | UX que cumpra POST-04 com clareza. | |

**User's choice:** Toggle Agora/Agendar com datetime em SP (Recomendado)
**Notes:** Fuso `America/Sao_Paulo` explícito na UI.

| Option | Description | Selected |
|--------|-------------|----------|
| Salvar explicitamente no draft (Recomendado) | Ação explícita persiste texto e modo/horário; aprovação usa último estado salvo. | ✓ |
| Auto-salvar alterações do editor | Debounce/auto-save; exige tratamento de concorrência/erros. | |
| Salvar/aplicar apenas no momento de aprovar | Enviar junto na aprovação; dificulta draft salvo/retomada (POST-02). | |
| You decide (OpenCode) | Consistência entre o que se vê/edita e o que é aprovado. | |

**User's choice:** Salvar explicitamente no draft (Recomendado)
**Notes:** Aprovação deve consumir o draft/agendamento salvos.

---

## Aprovar vaga + registrar post social (seguro)

| Option | Description | Selected |
|--------|-------------|----------|
| Publicar site primeiro; social em etapa separada best-effort (Recomendado) | Job publicado independentemente; `social_post` registrado em passo/transação separado com aviso em falha. | ✓ |
| Tudo na mesma transação (tudo-ou-nada) | Erro social desfaz publicação da vaga. | |
| Exigir draft válido e bloquear approve se social falhar | Bloqueia publicação do site em falhas sociais. | |
| You decide (OpenCode) | Garantir independência estrita. | |

**User's choice:** Publicar site primeiro; social em etapa separada best-effort (Recomendado)
**Notes:** Critério crítico: falha social nunca bloqueia o site.

| Option | Description | Selected |
|--------|-------------|----------|
| Sempre `scheduled` com horário apropriado (Recomendado) | Agora ⇒ `scheduled_at=agora`; agendado ⇒ `scheduled_at` futuro (de `America/Sao_Paulo`). | ✓ |
| Agora ⇒ `publishing`, agendado ⇒ `scheduled` | Pode conflitar com semântica do worker. | |
| Manter `draft` até o worker processar | Não registra aprovado/agendado. | |
| You decide (OpenCode) | Compatível com modelo atual e fase 17. | |

**User's choice:** Sempre `scheduled` com horário apropriado (Recomendado)
**Notes:** Registro aprovado como `scheduled` para consumo do worker na Fase 17.

| Option | Description | Selected |
|--------|-------------|----------|
| Publicar vaga e pular/avisar sobre social (Recomendado) | Sem draft ou falha best-effort ⇒ vaga publicada, social não registrado/avisado. | ✓ |
| Tentar gerar template best-effort ao aprovar | Criar template no approve sem LLM; mais lógica implícita. | |
| Bloquear aprovação sem draft salvo | Contraria não bloqueio do site. | |
| You decide (OpenCode) | Preservar publicação do site e clareza de estado. | |

**User's choice:** Publicar vaga e pular/avisar sobre social (Recomendado)
**Notes:** Vaga no site nunca depende de draft/registro social.

| Option | Description | Selected |
|--------|-------------|----------|
| Congelar texto ao aprovar/registrar (Recomendado) | Ao virar `scheduled` aprovado, texto tratado como final para envio; edição de conteúdo desabilitada. | ✓ |
| Permitir editar até o envio (fase 17) | Flexível, mas risco de concorrência/divergência. | |
| Congelar apenas após `published` (pós-envio real) | Permite alterações após aprovação/agendamento. | |
| You decide (OpenCode) | Consistência entre aprovação e envio (POST-05). | |

**User's choice:** Congelar texto ao aprovar/registrar (Recomendado)
**Notes:** Conteúdo aprovado deve corresponder ao que será enviado.

---

## Conteúdo, URL pública e política sem contato

| Option | Description | Selected |
|--------|-------------|----------|
| Usar `SITE_PUBLIC_URL/?vaga=<job_id>` (Recomendado) | Reaproveita deep-link público existente (`?vaga=<uuid>`). | ✓ |
| Criar/assumir rota dedicada `/vagas/<id>` | Pode exigir nova rota/página. | |
| Tornar o formato/path configurável | Mais flexível, maior superfície de config. | |
| You decide (OpenCode) | Compatível com frontend atual e `SITE_PUBLIC_URL`. | |

**User's choice:** Usar `SITE_PUBLIC_URL/?vaga=<job_id>` (Recomendado)
**Notes:** Alinhado a `frontend/app/(public)/page.tsx`.

| Option | Description | Selected |
|--------|-------------|----------|
| Template objetivo com campos-chave (Recomendado) | Cargo/cidade/salário/destaques quando couber, CTA+link, 3–5 hashtags, emojis moderados, ~700 chars. | ✓ (com correção) |
| Template mínimo (título + cidade + link) | Mais simples, menos informativo. | |
| Template longo/detalhado | Risco de exceder ~700 chars. | |
| You decide (OpenCode) | Equilíbrio e consistência com POST-01/02. | |

**User's choice:** Template objetivo com campos-chave (Recomendado), com correção do usuário
**Notes:** **Correção explícita do usuário (livre):** "Na publicação da vaga em rede sociais não deverá conter nome da empresa e nem qualquer tipo de contato seja numero de telefone ou email, invés disso havera um link para redirecionar para o website". Template/prompt/preview devem omitir **empresa** e **contatos**.

| Option | Description | Selected |
|--------|-------------|----------|
| Flag de ambiente no backend (Recomendado) | Config em `Settings`/`.env.example`, padrão desativado; aplicada centralmente. | ✓ |
| Toggle por post na UI de revisão | Controle por post; mais UX/estado. | |
| Não configurável nesta fase (sempre sem contato) | Não atende "configurável" de POST-06. | |
| You decide (OpenCode) | Configurabilidade simples e documentada, padrão sem contato. | |

**User's choice:** Flag de ambiente no backend (Recomendado)
**Notes:** Padrão sem contato; documentar e aplicar centralmente.

| Option | Description | Selected |
|--------|-------------|----------|
| Aplicar regra central + link obrigatório com validação (Recomendado) | Omitir empresa/contato conforme política em geração/template/preview; validar `SITE_PUBLIC_URL` e tratar ausência de forma clara/acionável sem bloquear site. | ✓ |
| Confiar no prompt/LLM para omitir contato | Risco de vazamento acidental. | |
| Permitir gerar sem link quando faltar config | Não atende presença consistente do link. | |
| You decide (OpenCode) | Aplicação robusta da política e do link. | |

**User's choice:** Aplicar regra central + link obrigatório com validação (Recomendado)
**Notes:** Sanitização/regra central no backend para evitar vazamento de empresa/contato e garantir link.

---

## OpenCode's Discretion

- Nomes/paths exatos de endpoints, schemas e organização de módulos (ex.: serviço de geração em `backend/app/services/social/`).
- Conversão/persistência exata de `America/Sao_Paulo` para `scheduled_at` e representação de "publicar agora".
- Redação exata do prompt/template, escolha de hashtags, truncamento para ~700 chars e detalhes visuais da seção no `EditJobDialog`.
- Nome/formato/documentação da env var de política configurável e mensagens de erro/aviso.
- Contrato de resposta da aprovação para comunicar sucesso da vaga vs aviso/falha social best-effort.
- Mecanismo de bloqueio de edição do texto quando `scheduled` aprovado (UI/validação backend).

## Deferred Ideas

- Publicação real/worker/cron/retries/idempotência/status e retry manual (Fase 17, UI-01/02, PUB-*).
- Testes automatizados/manuais e documentação operacional/App Review (Fase 18) e carry-over de gaps v1.1.
- Detalhes finos não discutidos (contrato exato de APIs/payloads, UX específica para `SITE_PUBLIC_URL` ausente, nome exato da env var) a definir no planejamento/pesquisa dentro do escopo.
