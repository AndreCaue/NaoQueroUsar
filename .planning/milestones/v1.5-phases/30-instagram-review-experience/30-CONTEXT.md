# Phase 30: Instagram Review Experience - Context

**Gathered:** 2026-11-23
**Status:** Ready for planning

<domain>
## Phase Boundary

Na revisão (etapa admin), o admin controla a publicação no Instagram por vaga com feedback claro antes de aprovar: seção Instagram ao lado do Facebook (com toggle e status independente), legenda editável com regras de aviso/limite, preview da imagem exata e bloqueios claros. Esta fase entrega a experiência de revisão (REVW-01..04); o pipeline assíncrono de publicação Instagram independente do Facebook é tratado na Phase 31.

</domain>

<decisions>
## Implementation Decisions

### Prefill da legenda IG (Instagram-tuned)
- **D-01:** Prefill padrão é **template simples (C)** a partir dos dados da vaga (título, empresa se houver, cidade/remoto, tipo/contrato/salário quando houver) **+ CTA sempre “link na bio”** (ex.: orientação clara de que links na legenda não são clicáveis; usar CTA no estilo “link na bio”). Não reutilizar cegamente o rascunho do Facebook como prefill padrão; o admin pode usar o texto do Facebook manualmente se quiser, mas o padrão é o template C (Instagram-tuned).
- **D-02:** Hashtags sugeridas iniciais no template: `#vagas`, `#emprego`, `#cidade`, `#oportunidade` (o admin pode editar/remover). O template deve ser conciso e adequado ao Instagram.

### Seção/toggle no diálogo de revisão e prontidão
- **D-03:** Seção **“Post para Instagram”** fica **abaixo** de **“Post para Facebook”** no `EditJobDialog` (mesmo diálogo de revisão). Publicações Facebook e Instagram são **independentes** (falha/estado de uma não bloqueia a outra no fluxo de revisão/publicação conforme guardrails do projeto).
- **D-04:** Toggle **“Publicar no Instagram desta vaga”** (por vaga). Quando **desligado**, **esconder** legenda e preview (mostrar apenas o toggle/contexto mínimo). Quando **ligado**, exibir controles da legenda e preview da imagem IG.
- **D-05:** Se o Instagram **não estiver pronto** em Integrações (conta/link/escopos/prontidão insuficiente), a seção permanece **visível mas desabilitada**, com texto explicativo em pt-BR e **link para `/admin/integracoes`** (ação clara de correção/reconexão). Não esconder a seção nesse caso.

### Preview da imagem IG e validação (IMAG-01)
- **D-06:** Preview da imagem exata do Instagram: **carregar/preparar automaticamente** ao abrir o diálogo (quando aplicável) ou ao **ativar** o toggle (escolha A). Exibir estados de **loading** e **erro/mensagem em pt-BR** se a imagem não estiver preparada/inválida.
- **D-07:** **Bloqueio só do Instagram**: não é possível salvar/aprovar/publicar com Instagram habilitado sem imagem válida conforme contrato IMAG-01 (Phase 29); isso **não bloqueia** aprovação/publicação do Facebook nem do site. Mensagens e validações devem deixar isso claro.

### Regras de legenda (REVW-02/REVW-03)
- **D-08:** Edição de legenda Instagram com **contador ao vivo `N/2200`**; **não permitir salvar/aprovar** legenda acima do limite (2200). Validação também no backend quando aplicável.
- **D-09:** **Aviso** (não bloqueante, salvo o limite) quando a legenda tiver **>30 hashtags** (contagem por tokens `#...`). Exibir **orientação clara** de que **links na legenda não são clicáveis** e usar CTA no estilo **“link na bio”**.

### OpenCode's Discretion
- Wording final em pt-BR dos textos de ajuda/erros na seção IG (desde que claros e consistentes com o padrão do admin).
- Detalhes de UX do contador/avisos (posicionamento, estilo visual) respeitando o design system existente (Tailwind, dark/púrpura).
- Estratégia técnica exata para “preparar automaticamente” (chamar endpoint de preparo/media da Phase 29 ao abrir vs ao togglar) desde que atenda D-06 e não gere chamadas desnecessárias excessivas.
- Se o status Instagram exibido na revisão reutiliza dados já buscados no `ReviewQueue`/`EditJobDialog` ou exige nova busca — escolher a abordagem mais simples e coerente com o código atual, sem quebrar o fluxo Facebook.

### Folded Todos
- Nenhum (nenhum todo cruzado com esta fase foi dobrado no passo de cross-reference).

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Escopo e requisitos da fase
- `.planning/ROADMAP.md` — Phase 30: “Instagram Review Experience” (goal, depends_on Phase 29, requisitos REVW-01..04, critérios de sucesso, notas de research/decisões).
- `.planning/REQUIREMENTS.md` — Seção “Review UI Instagram” (REVW-01..04) e traceability para Phase 30.
- `.planning/PROJECT.md` — Core value, restrições v1.5 (independência IG/Facebook, sem Stories/Reels/carrossel/agendamento/métricas/múltiplas contas), decisões abertas globais.
- `.planning/STATE.md` — Posição atual, foco em Phase 30, blockers/concerns v1.5 (decisões de mídia/token já endereçadas em parte pela Phase 29; ver Phase 29).

### Contratos e base da Phase 29 (obrigatório)
- `.planning/phases/29-meta-ig-readiness-media-foundation/29-CONTEXT.md` — Decisões D-01..D-16 (card gerado sempre, formato 1080x1350 JPEG, serving por URL pública HTTPS com versão/hash, prontidão IG em Integrações, bloqueio só IG, etc.). Esta fase consome esses contratos.
- `backend/app/api/v1/admin.py` — Endpoint(s) de preparo/mídia IG (ex.: `POST /admin/jobs/{job_id}/instagram/media/prepare`) e fluxo admin relacionado.
- `backend/app/services/social/image_media.py` — Lógica de preparo/validação de mídia IG e mensagens/erros seguros.
- `backend/app/schemas/social_media.py` — Schemas de mídia/preparo IG.
- `backend/app/services/social/meta_oauth.py`, `backend/app/schemas/social_integrations.py`, `frontend/app/admin/integracoes/IntegrationsClient.tsx` — Prontidão IG e estados acionáveis (usados para decidir UI desabilitada + link).

### Revisão/admin atual (ponto de integração)
- `frontend/app/admin/review/ReviewQueue.tsx` — Fila de revisão, fetch de status social (Facebook hoje), ações de aprovar/editar/excluir.
- `frontend/app/admin/review/EditJobDialog.tsx` — Diálogo de edição/revisão com seção “Post para Facebook” (draft, status, salvar/regenerar, modo publicação no contexto atual). **Ponto principal para adicionar “Post para Instagram”.**
- `frontend/components/admin/ReviewRow.tsx` — Linha da fila (badge/status social exibido; pode precisar refletir status IG independente no futuro, mas Phase 30 foca em REVW-01..04 no diálogo/experiência de revisão conforme escopo).
- `frontend/lib/api.ts` — Cliente API admin (funções para social draft/status, jobs; estender para IG conforme necessário).
- `backend/app/api/v1/social_posts.py` (e rotas relacionadas a rascunho/status social) — Contratos atuais de social post/draft (referência para extensão IG sem quebrar Facebook).

### Pesquisa v1.5 (contexto)
- `.planning/research/SUMMARY.md`, `.planning/research/ARCHITECTURE.md`, `.planning/research/PITFALLS.md`, `.planning/research/STACK.md`, `.planning/research/FEATURES.md` — Diretrizes e armadilhas (legenda IG, limites, mídia, independência de plataformas).

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `frontend/app/admin/review/EditJobDialog.tsx`: já implementa seção “Post para Facebook” com carregamento de rascunho/status, geração/salvamento, validações e feedback em pt-BR; servir de padrão de layout/UX para a nova seção IG (com adaptações: toggle, legenda 2200, aviso hashtags, preview de imagem).
- `frontend/app/admin/review/ReviewQueue.tsx`: orquestra fila, tabs, badges de status social; entender como status independente por plataforma será exibido (REVW-01 menciona status independente).
- `backend/app/services/social/image_media.py` + endpoint de preparo em `backend/app/api/v1/admin.py`: preparar/validar mídia IG e obter URL/estado para preview (Phase 29).
- Prontidão IG em Integrações (`frontend/app/admin/integracoes/IntegrationsClient.tsx`, schemas/backend): fonte de verdade para exibir seção IG desabilitada + link quando não pronto.

### Established Patterns
- Fluxo admin protegido por JWT; erros de auth tratam redirect para login (padrão já usado em ReviewQueue/EditJobDialog).
- Mensagens e toasts em pt-BR; estados de loading/erro explícitos.
- Independência site-first/social: alterações de IG não devem quebrar fluxo Facebook/site.
- Mídia IG: URL pública HTTPS com versão/hash (Phase 29); preview deve refletir a imagem exata pretendida.

### Integration Points
- `EditJobDialog.tsx`: adicionar bloco “Post para Instagram” abaixo do bloco Facebook, com toggle, campos condicionais (legenda, preview), integração com API de preparo de mídia e (futuramente) com dados de draft/status IG.
- `frontend/lib/api.ts`: novas funções/endpoints para ler/salvar dados de rascunho/estado IG no contexto de revisão (conforme contratos definidos no planejamento), respeitando independência do Facebook.
- Backend: endpoints/schemas para legenda IG, toggle/publicar-IG-por-vaga, vínculo com job/social draft IG e validações (limite 2200, regras de pré-validação de imagem antes de permitir fluxo IG habilitado) — detalhes em planos da Phase 30.
- Exibição de status por plataforma na revisão (REVW-01): pode exigir extensão de respostas/status atuais (Facebook) para incluir estado IG.

</code_context>

<specifics>
## Specific Ideas

- “Postagens no Facebook e IG devem ser independentes” (confirmado pelo usuário durante discussão).
- Prefill IG: template simples com hashtags sugeridas `#vagas`, `#emprego`, `#cidade`, `#opportunidade` e CTA sempre “link na bio”.
- Quando IG não pronto: seção **visível mas desabilitada** com link para `/admin/integracoes` (não esconder).
- Preview IG: **automático** ao abrir/ativar conforme fluxo (escolha A), com bloqueio só do Instagram se imagem inválida.

</specifics>

<deferred>
## Deferred Ideas

- Geração automática de legenda IG via LLM separada do Facebook (fluxo “gerar com IA” específico para IG) — não decidido; pode ser avaliado em fase futura se o template C for insuficiente.
- Exibir/editar múltiplos campos avançados de IG (hashtags gerenciadas separadamente, primeiros comentários etc.) — fora do escopo REVW-01..04.
- Qualquer alteração no pipeline de publicação assíncrona (retry, containers Graph, etc.) — Phase 31.

### Reviewed Todos (not folded)
- Nenhum todo revisado foi adiado para outras fases nesta discussão (cross-reference não encontrou itens relevantes).

</deferred>

---

*Phase: 30-instagram-review-experience*
*Context gathered: 2026-11-23*