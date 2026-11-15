# Phase 14: Fundação Social, Dados e Configuração - Context

**Gathered:** 2026-11-15
**Status:** Ready for planning

<domain>
## Phase Boundary

Criar a fundação persistente e segura no backend para a integração social do EmpregaNoix (Facebook agora, arquitetura preparada para Instagram futuro), sem alterar o fluxo público do site.

**Em escopo (Fase 14):** migrações/modelos para `social_accounts`, `social_posts` e `social_post_logs` (SOC-03 adotado), armazenamento criptografado em repouso de `page_access_token`, contrato `SocialPublisher` e `FacebookPublisher` inicial em modo stub/estrutura pronta, e configuração/envs documentadas (`META_*`, `SOCIAL_*`, `SITE_PUBLIC_URL` etc.) alinhadas às convenções do backend.

**Fora de escopo:** fluxo OAuth/seleção de página e UI de integrações (Fase 15), geração/edição/aprovação do post social e integração com revisão (Fase 16), publicação real no Graph API, worker/cron, retries/idempotência operacional e UI de status/retry (Fase 17), testes/docs de fechamento (Fase 18), Instagram, múltiplas páginas, sincronização de edição/remoção de posts e qualquer exposição de segredos ao frontend/logs.

</domain>

<decisions>
## Implementation Decisions

### Criptografia de tokens (repouso)
- **D-01:** Usar **Fernet** via biblioteca `cryptography` como abordagem de criptografia reversível/autenticada para `page_access_token` em repouso (SOC-04).
- **D-02:** Centralizar encrypt/decrypt em **serviço/utilitário dedicado** (módulo de crypto/token do domínio social) com chamadas explícitas por modelos/CRUD/fluxos; não usar criptografia transparente implícita que masque erros/vazamentos.
- **D-03:** `SOCIAL_TOKEN_ENCRYPTION_KEY` deve ser **validada no startup** (formato de chave Fernet) com falha explícita se inválida quando aplicável; falhas de descriptografia devem gerar **erro específico sem expor o token** para que fluxos futuros possam tratar reconexão (`needs_reconnect`).
- **D-04:** Persistir o token criptografado como **texto Fernet direto** na coluna de armazenamento (sem prefixo de versão/envelope na Fase 14).

### Modelo de dados e migrações social
- **D-05:** Modelar status com **enums nativos Postgres por domínio** (ex.: `social_account_status`, `social_post_status`), alinhados ao padrão existente de `JobStatus` em `backend/app/models/job.py`.
- **D-06:** **Criar `social_post_logs` já na Fase 14** (SOC-03 adotado): modelo + migração com FK para `social_posts`, timestamps e campos para tentativa/resultado/erro/resposta resumida, preparando auditoria/retries das fases seguintes.
- **D-07:** `social_posts.job_id` referencia `jobs.id` com **FK `ON DELETE CASCADE`**; definir `attempts` com default 0 e campos operacionais (`scheduled_at`, `next_retry_at`, `last_error`, `external_post_id`, `published_at`, etc.) com nullability/defaults consistentes com o estado do registro.
- **D-08:** Usar **`TIMESTAMP(timezone=True)`/UTC** consistente com o modelo `jobs`. Além da unicidade obrigatória **`(job_id, provider)`** em `social_posts` (SOC-02), incluir **índices operacionais** para elegibilidade/lookup previstos (ex.: status/datas em `social_posts`; provider/status/page_id conforme útil em `social_accounts`) sem indexação excessiva especulativa.

### Contrato SocialPublisher e stub Facebook
- **D-09:** Definir contrato `SocialPublisher` como **interface async** com método `publish` retornando **resultado tipado** (`PublishResult`), alinhado ao stack async do backend e ao I/O de rede futuro.
- **D-10:** `PublishResult` deve distinguir **sucesso** (incluindo `external_post_id` quando aplicável) e **falha** com categoria/motivo (ex.: transitória/permanente/unknown) e mensagem resumida segura, preparando classificação de retries (PUB-06) sem implementar worker na Fase 14.
- **D-11:** `FacebookPublisher` inicial deve ser um **stub explícito sem chamadas externas/HTTP**: respeita o contrato e retorna falha controlada ou erro explícito documentado, servindo como estrutura pronta para implementação real na Fase 17.
- **D-12:** Organizar domínio social em **`backend/app/services/social/`** (contrato/interface, tipos/resultados, `facebook.py`), mantendo modelos em `backend/app/models/` e schemas em `backend/app/schemas/` conforme convenções existentes.

### Config, settings e .env.example social
- **D-13:** Adicionar em `backend/app/core/config.py` (`Settings`) campos tipados para `META_*`, `SOCIAL_*` e `SITE_PUBLIC_URL` com **validação de formato quando preenchidos** (URLs, inteiros > 0, delays parseáveis), **opcionais por padrão** na Fase 14, com erros claros para uso futuro.
- **D-14:** `SOCIAL_MAX_ATTEMPTS` como `int` (default **5**) e `SOCIAL_RETRY_DELAYS` como **CSV de segundos** (default **`300,900,3600,10800,21600`**, correspondendo a 5min/15min/1h/3h/6h) com parser/helper em Settings; documentar formato e defaults no `.env.example`.
- **D-15:** Validar formato **http/https** para `SITE_PUBLIC_URL` e `META_OAUTH_REDIRECT_URI` quando preenchidos. Tratar `META_APP_SECRET`, `SOCIAL_WORKER_SECRET` e `SOCIAL_TOKEN_ENCRYPTION_KEY` como **segredos sensíveis** (apenas backend, nunca em logs/respostas/frontend), sem defaults inseguros.
- **D-16:** `backend/.env.example` deve cobrir **exatamente as variáveis de SOC-06** — `META_APP_ID`, `META_APP_SECRET`, `META_GRAPH_VERSION`, `META_OAUTH_REDIRECT_URI`, `SOCIAL_TOKEN_ENCRYPTION_KEY`, `SOCIAL_WORKER_SECRET`, `SOCIAL_MAX_ATTEMPTS`, `SOCIAL_RETRY_DELAYS`, `SITE_PUBLIC_URL` — com comentários em pt-BR, placeholders sem segredos e defaults seguros quando cabível; evitar variáveis especulativas extras.

### OpenCode's Discretion
- Nomes exatos de classes/funções/módulos dentro de `app/services/social/` e convenções de import/export, desde que sigam o padrão do backend.
- Representação interna detalhada de `PublishResult`/categorias (enums, dataclasses/pydantic, campos auxiliares) e formato exato da exceção específica de falha de descriptografia, mantendo as garantias de D-10/D-03.
- Detalhamento fino de colunas/índices adicionais estritamente úteis aos requisitos SOC-01/02/03 e às consultas previstas (D-08), sem ampliar escopo funcional.
- Redação/comentários do bloco social no `.env.example` e mensagens de validação, preservando cobertura de D-16 e segurança de segredos.
- Escolha da versão estável de `META_GRAPH_VERSION` como default documentado, alinhada à doc Meta no momento da implementação (META-02), sem hardcode disperso.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Escopo e requisitos da fase
- `.planning/ROADMAP.md` §"Phase 14: Fundação Social, Dados e Configuração" — goal, depends_on, requisitos `SOC-01..SOC-06`, critérios de sucesso e limites de escopo.
- `.planning/REQUIREMENTS.md` — definições de `SOC-01` a `SOC-06` (fundação social, dados e configuração) e rastreabilidade da v1.2.
- `.planning/PROJECT.md` — core value, decisões/constraints do milestone v1.2 (Facebook only, 1 página/1 admin, tokens/segredos só no backend criptografados, falha social não bloqueia o site, fire-and-forget, convenções) e stack fixo.
- `.planning/STATE.md` — posição atual do milestone, contexto acumulado e pendências herdadas (inspecionar repo antes de planejar, seguir convenções).

### Padrões existentes do backend (obrigatório seguir)
- `backend/app/core/config.py` — `Settings` (pydantic-settings), validações fail-closed/condicionais existentes, propriedades derivadas e convenções de env.
- `backend/app/models/job.py` — padrão de modelos SQLAlchemy 2 (`Mapped`, `mapped_column`), enums nativos, `TIMESTAMP(timezone=True)`, defaults `server_default`/constraints/índices.
- `backend/app/models/__init__.py` — registro/exportação de modelos.
- `backend/app/db/base.py` — `DeclarativeBase` do projeto.
- `backend/alembic/env.py` — configuração async do Alembic, import de modelos para metadata/autogenerate e injeção de `DATABASE_URL`.
- `backend/alembic/versions/0001_initial_jobs.py` — convenção de migrações existentes (estrutura de referência).
- `backend/.env.example` — formato/comentários atuais de variáveis de ambiente do backend.
- `backend/pyproject.toml` — dependências atuais (verificar inclusão de `cryptography` ao implementar D-01).

### Integração/serviços e contexto operacional relacionado
- `backend/app/services/` — convenções de organização de serviços (ex.: `extraction/`, `turnstile.py`, `cities.py`) relevantes para `app/services/social/` (D-12).
- `backend/app/core/scheduler.py` — padrão atual de agendamento/execução em background e separação de clock vs operação (contexto para fundação compatível com worker futuro, sem implementar PUB nesta fase).
- `backend/app/api/v1/admin.py` e `backend/app/api/v1/router.py` — convenções de rotas/admin protegidas (referência estrutural; Fase 14 não deve expor segredos/tokens).

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `backend/app/models/job.py`: exemplo canônico de modelo com enum nativo (`JobStatus`), colunas `TIMESTAMP(timezone=True)` com `server_default`, constraints (`CheckConstraint`) e índices — base direta para `social_accounts`/`social_posts`/`social_post_logs`.
- `backend/app/core/config.py`: `BaseSettings` com `model_validator` e propriedades derivadas (`cors_origins_list`, `turnstile_mode`) — padrão para adicionar/parsing/validação de `META_*`, `SOCIAL_*`, `SITE_PUBLIC_URL`, retries e chave Fernet.
- `backend/app/db/base.py` + `backend/alembic/env.py`: base declarativa e fluxo async de migração já configurados; novos modelos devem ser importados para metadata conforme padrão atual.

### Established Patterns
- SQLAlchemy 2.0 declarativo com `Mapped[...]`/`mapped_column`, tipos Postgres explícitos (`UUID`, `TIMESTAMP(timezone=True)`, enums nativos) e defaults no banco.
- Alembic async com URL vinda de settings (nunca hardcoded) e `statement_cache_size=0` para compatibilidade Neon/PgBouncer.
- Validação/configuração centralizada em `Settings` (pydantic-settings), com comportamento condicionado por ambiente e falhas explícitas para configurações inseguras/inválidas.
- Serviços organizados em `backend/app/services/` por domínio/capacidade; integrações externas encapsuladas (ex.: Turnstile, extração).

### Integration Points
- `backend/app/models/` e `backend/app/models/__init__.py`: registrar novos modelos sociais para uso por Alembic/ORM.
- `backend/alembic/versions/`: nova migração da fundação social (tabelas, enums, constraints, índices, FKs) seguindo convenções existentes.
- `backend/app/core/config.py` e `backend/.env.example`: superfície de configuração Meta/social/worker/site (SOC-06) e validação de formatos/defaults.
- `backend/app/services/social/`: novo pacote para contrato `SocialPublisher`, `PublishResult`/tipos e stub `FacebookPublisher` (sem acoplamento de provider, pronto para evolução nas fases 15–17).

</code_context>

<specifics>
## Specific Ideas

- Sem requisitos específicos adicionais além das decisões capturadas; seguir as escolhas recomendadas registradas (Fernet + serviço dedicado, enums nativos, `social_post_logs` incluído, `ON DELETE CASCADE`, contrato async tipado com stub explícito, retries em CSV de segundos e cobertura exata de SOC-06).

</specifics>

<deferred>
## Deferred Ideas

None — discussão permaneceu dentro do escopo da Fase 14.

</deferred>

---

*Phase: 14-fundacao-social-dados-e-configuracao*
*Context gathered: 2026-11-15*
