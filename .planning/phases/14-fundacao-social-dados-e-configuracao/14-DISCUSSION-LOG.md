# Phase 14: Fundação Social, Dados e Configuração - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-11-15
**Phase:** 14-fundacao-social-dados-e-configuracao
**Areas discussed:** Criptografia de tokens (repouso), Modelo de dados e migrações social, Contrato SocialPublisher e stub Facebook, Config, settings e .env.example social

---

## Criptografia de tokens (repouso)

| Option | Description | Selected |
|--------|-------------|----------|
| Fernet (`cryptography`) (Recomendado) | Usar `cryptography.fernet.Fernet` (AES-128-CBC+HMAC, tokens autenticados). Simples, battle-tested, fácil de validar chave/env; adiciona dependência `cryptography`. Bom para segredo único por env. | ✓ |
| AES-GCM com `cryptography` | Usar primitives AES-GCM (AEAD) via `cryptography` para mais controle (nonce/tags). Também seguro, mas exige implementação/cuidados maiores (nonce único, formato do blob). Depende de `cryptography`. | |
| Envelope simples (chave + HMAC próprio) | Implementar camada mínima própria sobre primitives. Evita API de alto nível, mas aumenta risco de erro criptográfico e manutenção; só se houver motivo forte. | |
| You decide | Deixa o OpenCode escolher a abordagem mais segura e simples alinhada ao stack/deploy atual. | |

**User's choice:** Fernet (`cryptography`) (Recomendado)
**Notes:** Base para criptografia reversível/autenticada de `page_access_token` em repouso.

| Option | Description | Selected |
|--------|-------------|----------|
| Serviço utilitário dedicado (Recomendado) | Criar módulo/serviço (ex.: `app/core/crypto.py` ou `app/services/social/token_crypto.py`) com funções `encrypt_token`/`decrypt_token` usando settings; modelos/CRUD usam esse serviço explicitamente. Fronteira clara e testável. | ✓ |
| TypeDecorator/coluna transparente no model | Usar `TypeDecorator` SQLAlchemy para criptografar ao gravar e descriptografar ao ler automaticamente. Conveniente, mas pode mascarar custos/erros e exige cuidado extra para não serializar claro acidentalmente. | |
| Helpers soltos nos pontos de uso | Chamar Fernet diretamente em cada endpoint/CRUD. Mais rápido agora, mas duplica lógica e aumenta risco de vazamento/uso inconsistente. | |

**User's choice:** Serviço utilitário dedicado (Recomendado)
**Notes:** Fronteira explícita para evitar vazamento em logs/serialização e facilitar reuso (OAuth/worker).

| Option | Description | Selected |
|--------|-------------|----------|
| Validar chave no startup + erro explícito (Recomendado) | `Settings`/serviço valida formato Fernet na inicialização (falha cedo se inválida quando configurada/obrigatória) e decrypt inválido levanta exceção específica (sem vazar token), para o fluxo futuro marcar `needs_reconnect`. Evita estado silenciosamente quebrado. | ✓ |
| Validação preguiçosa (lazy) | Só valida ao usar encrypt/decrypt. Startup sobe mesmo com chave ruim, mas erro aparece tarde (no primeiro uso). Mais permissivo, menos previsível. | |
| Permitir vazio em dev e exigir fora de dev | Seguir padrão do Turnstile: chave opcional em dev/test local e obrigatória/validada fora de dev. Útil para DX, desde que caminhos sem social não quebrem. Pode combinar com validação no startup. | |

**User's choice:** Validar chave no startup + erro explícito (Recomendado)
**Notes:** Priorizar falha explícita/segura; decrypt inválido deve permitir tratamento futuro de reconexão sem expor segredo.

| Option | Description | Selected |
|--------|-------------|----------|
| Texto Fernet direto (Recomendado) | Armazenar o token Fernet (string/base64 urlsafe) em coluna `Text`/`String` como gerado; descriptografia espera esse formato. Simples e suficiente para chave única atual. | ✓ |
| Texto com prefixo de versão (ex.: `v1:`) | Prefixar o valor salvo (ex.: `v1:<fernet>` ou envelope JSON) para suportar rotação/migração futura de algoritmo/chave sem ambiguidade. Leve overhead agora, mais flexível depois. | |
| Binário (bytea) nativo | Guardar bytes criptografados em coluna binária. Evita conversão de encoding, mas foge um pouco do uso textual típico do Fernet e pode complicar inspeção/migração. | |

**User's choice:** Texto Fernet direto (Recomendado)
**Notes:** Formato simples na Fase 14, sem envelope/prefixo de versão.

---

## Modelo de dados e migrações social

| Option | Description | Selected |
|--------|-------------|----------|
| Enums nativos por domínio (Recomendado) | Criar enums nativos separados (ex.: `social_account_status`, `social_post_status`) como em `JobStatus`, com valores/constraints explícitos. Tipagem forte no banco e consistência com o projeto. Requer migração cuidadosa para evoluir valores. | ✓ |
| VARCHAR + CHECK constraint | Armazenar status como texto com `CHECK` dos valores permitidos. Mais simples para evoluir valores em migrações futuras, menos acoplado a tipos enum do Postgres. | |
| VARCHAR simples (validação na aplicação) | Sem enum/check no banco, apenas validação no backend. Flexível, mas perde garantia de integridade no nível do schema. | |

**User's choice:** Enums nativos por domínio (Recomendado)
**Notes:** Alinhado ao padrão existente (`JobStatus`).

| Option | Description | Selected |
|--------|-------------|----------|
| Criar já na Fase 14 (Recomendado) | Incluir modelo + migração de `social_post_logs` agora (com FK para `social_posts`, timestamps, status/código/erro/resposta resumida). Deixa a base pronta para retries/auditoria das fases 16–17 sem nova migração estrutural depois. | ✓ |
| Adiar (não criar agora) | Não criar tabela/logs na Fase 14; registrar decisão de adiar. Fases futuras adicionam migração se/quando necessário. Mantém fundação mínima, mas pode exigir mudança de schema depois. | |
| Criar migração/tabela, uso opcional depois | Provisionar a estrutura agora, mas sem assumir escrita/uso imediato no código da Fase 14. Meio-termo entre preparo e escopo mínimo. | |

**User's choice:** Criar já na Fase 14 (Recomendado)
**Notes:** SOC-03 tratado como adotado na fundação.

| Option | Description | Selected |
|--------|-------------|----------|
| FK com `ON DELETE CASCADE` + campos com defaults claros (Recomendado) | `job_id` referencia `jobs.id` com cascade: apagar a vaga remove o registro social local (histórico local some junto). `attempts` default 0, timestamps/status com defaults consistentes, `scheduled_at/next_retry_at/last_error/external_post_id/published_at` nullable conforme estado. Simples e evita órfãos. | ✓ |
| FK com `ON DELETE SET NULL` (preservar histórico local) | Manter `social_posts` mesmo sem a vaga (job_id nullable após delete) para auditoria/histórico local. Preserva rastreio, mas complica consultas/semântica de unicidade `(job_id,provider)` quando job some. | |
| Sem FK rígida (apenas job_id indexado) | Não impor constraint de chave estrangeira; guardar `job_id` como UUID. Máxima flexibilidade, mas perde integridade referencial no banco. | |

**User's choice:** FK com `ON DELETE CASCADE` + campos com defaults claros (Recomendado)
**Notes:** Considera hard delete de vagas e fire-and-forget no Facebook; evita órfãos locais.

| Option | Description | Selected |
|--------|-------------|----------|
| Índices operacionais + TIMESTAMPTZ consistente (Recomendado) | Usar `TIMESTAMP(timezone=True)`/UTC (como `jobs`) para campos de tempo. Em `social_posts`: índices para elegibilidade do worker (ex.: `status`, `scheduled_at`, `next_retry_at`) e/ou composto útil; em `social_accounts`: índice/lookup por `provider` (+ status/page_id conforme necessário). Balanceado para consultas previstas. | ✓ |
| Mínimo agora (só o que SOC exige) | Criar apenas unicidade `(job_id, provider)` e índices óbvios; deixar otimizações de worker/lookup para migração da fase que implementar o polling. Menos suposições agora, possível ajuste depois. | |
| Índices amplos desde já (quase todas colunas de filtro) | Indexar status, datas, provider, page_id, external_post_id etc. antecipadamente. Pode ajudar leituras, mas adiciona custo de escrita/manutenção sem carga real ainda. | |

**User's choice:** Índices operacionais + TIMESTAMPTZ consistente (Recomendado)
**Notes:** Preparar consultas de OAuth/status e elegibilidade futura do worker sem sobre-indexar.

---

## Contrato SocialPublisher e stub Facebook

| Option | Description | Selected |
|--------|-------------|----------|
| Interface async com método `publish` + resultado tipado (Recomendado) | Definir contrato async (ex.: `async def publish(...) -> PublishResult`) recebendo dados necessários do post/conta; retornar objeto de resultado com sucesso/id externo ou falha tipada. Alinha ao I/O de rede futuro e facilita testes/stub. | ✓ |
| Interface sync simples (chamada bloqueante) | Método síncrono retornando dict/valor simples. Mais simples agora, mas tende a conflitar com chamadas HTTP async e execução em worker/event loop depois. | |
| Contrato mínimo `publish` retornando bool/None | Assinatura bem enxuta (sucesso/falha simples) sem payload estruturado. Pouco acoplamento inicial, mas pode forçar refatoração quando precisar de `external_post_id`, erro e classificação de retry. | |

**User's choice:** Interface async com método `publish` + resultado tipado (Recomendado)
**Notes:** Compatível com FastAPI/SQLAlchemy async e evolução para publicação real.

| Option | Description | Selected |
|--------|-------------|----------|
| Resultado com categoria de erro (Recomendado) | Modelar resultado tipado distinguindo sucesso (com `external_post_id`) e falha com categoria/motivo (ex.: transient/permanent/unknown) + mensagem resumida segura. Prepara retries/idempotência sem implementar worker agora. | ✓ |
| Apenas sucesso/erro genérico agora | Retornar sucesso ou erro simples (mensagem/código bruto) e adiar taxonomia para a fase de publicação/retry. Menos estrutura agora, maior ajuste no contrato depois. | |
| Exceções tipadas por classe (sem result object rico) | Usar exceções específicas (ex.: `TransientPublishError`, `PermanentPublishError`) em vez de payload de resultado. Claro para controle de fluxo, mas precisa convenção consistente de captura/log. | |

**User's choice:** Resultado com categoria de erro (Recomendado)
**Notes:** Antecipar classificação transitória/permanente útil em PUB-06.

| Option | Description | Selected |
|--------|-------------|----------|
| Stub explícito sem chamada externa (Recomendado) | Implementar classe/método conforme contrato, mas sem HTTP: retorna resultado de falha controlada (ex.: "not implemented"/provider unavailable) ou lança erro explícito documentado, nunca chamando a API. Seguro e deixa ponto claro para fase 17. | ✓ |
| Esqueleto com cliente HTTP preparado (sem enviar) | Montar estrutura/config de client/endpoint/headers mas não executar publicação real (ou atrás de flag). Aproxima da implementação final, porém adiciona código morto/complexidade prematura na fundação. | |
| Implementação mínima já chamando Graph API se configurado | Adiantar parte da chamada real na Fase 14. Antecipa fase 17 e foge do escopo de "fundação/stub", aumentando risco antes de OAuth/worker/review estarem prontos. | |

**User's choice:** Stub explícito sem chamada externa (Recomendado)
**Notes:** Estrutura pronta, sem efeitos colaterais/rede na Fase 14.

| Option | Description | Selected |
|--------|-------------|----------|
| `app/services/social/` (Recomendado) | Criar pacote de serviço social (ex.: `publisher.py`/interface, `types.py` ou `results.py`, `facebook.py`) mantendo integração/provider encapsulados em `services`, alinhado a `services/extraction` e `services/turnstile.py`. Modelos/schemas seguem em `app/models` e `app/schemas`. | ✓ |
| Pacote dedicado `app/publishers/` | Separar publishers em diretório próprio de domínio (interface + providers). Fica bem explícito para Instagram futuro, mas introduz nova convenção/top-level além de `services`. | |
| Misturar em `app/core`/arquivos utilitários | Colocar contrato/stub junto de config/core helpers. Mais rápido, porém espalha responsabilidade de domínio social em módulos de infraestrutura. | |

**User's choice:** `app/services/social/` (Recomendado)
**Notes:** Segue convenções existentes de serviços no backend.

---

## Config, settings e .env.example social

| Option | Description | Selected |
|--------|-------------|----------|
| Campos tipados com validação de formato, opcionais por padrão (Recomendado) | Adicionar `META_*`, `SOCIAL_*`, `SITE_PUBLIC_URL` como settings tipados (strings/ints) com defaults seguros/vazios onde apropriado; validar formato quando preenchidos (URL, inteiro>0, lista de delays parseável). Não exigir tudo no boot agora, mas preparar validações/erros claros para uso futuro. Alinha ao caráter de fundação. | ✓ |
| Obrigatórias/estritas fora de dev (fail-closed) | Exigir variáveis sociais críticas fora de dev já na Fase 14 (como Turnstile/CORS). Mais seguro contra deploy mal configurado, porém pode quebrar ambientes que ainda não usarão integração social. | |
| Strings soltas sem validação específica | Apenas declarar campos sem regras de formato/parse (além de tipos básicos). Mínimo esforço agora, mas empurra erros de configuração para runtime das fases 15–17. | |

**User's choice:** Campos tipados com validação de formato, opcionais por padrão (Recomendado)
**Notes:** Fundação flexível no boot, com validação quando configurado.

| Option | Description | Selected |
|--------|-------------|----------|
| Inteiro + lista de segundos (CSV) (Recomendado) | `SOCIAL_MAX_ATTEMPTS` como int (default 5) e `SOCIAL_RETRY_DELAYS` como string CSV em segundos (ex.: `300,900,3600,10800,21600`) com parser/helper em Settings. Explícito, fácil de validar e independente de unidade textual. Documentar no `.env.example`. | ✓ |
| Lista de durações legíveis (ex.: `5m,15m,1h,3h,6h`) | Aceitar sufixos de tempo e converter internamente. Mais amigável de ler/editar, mas exige parser adicional e testes de formato. | |
| Apenas constantes/defaults no código (env só override simples) | Definir delays padrão fixos no código e permitir talvez só `SOCIAL_MAX_ATTEMPTS` via env. Menos configurável agora, mas simplifica parsing; pode limitar ajuste operacional citado no milestone. | |

**User's choice:** Inteiro + lista de segundos (CSV) (Recomendado)
**Notes:** Default 5 tentativas e `300,900,3600,10800,21600` (5min/15min/1h/3h/6h).

| Option | Description | Selected |
|--------|-------------|----------|
| Validar URLs e tratar segredos como sensíveis (Recomendado) | Validar formato de URL (http/https) quando preenchido para `SITE_PUBLIC_URL`/redirect URI; manter segredos apenas em Settings/backend (nunca em respostas/logs/frontend) e documentar claramente no `.env.example`. Sem defaults inseguros para segredos. Alinha a SOC-04/06 e práticas atuais. | ✓ |
| Sem validação de URL (aceitar qualquer string) | Guardar valores como strings livres e validar só no uso nas fases de OAuth/publicação. Mais tolerante, mas erros de config (barra final, esquema errado) aparecem tarde. | |
| Defaults de desenvolvimento para facilitar boot local | Preencher exemplos/defaults locais automáticos para URLs/segredos de dev. Pode acelerar setup, mas aumenta risco de confusão com valores reais e de vazar padrões; exige cuidado para não virar comportamento implícito em prod. | |

**User's choice:** Validar URLs e tratar segredos como sensíveis (Recomendado)
**Notes:** Segredos (`META_APP_SECRET`, `SOCIAL_WORKER_SECRET`, `SOCIAL_TOKEN_ENCRYPTION_KEY`) nunca expostos; sem defaults inseguros.

| Option | Description | Selected |
|--------|-------------|----------|
| Cobrir exatamente SOC-06 com comentários e defaults seguros (Recomendado) | Incluir todas as vars listadas em SOC-06 (`META_APP_ID`, `META_APP_SECRET`, `META_GRAPH_VERSION`, `META_OAUTH_REDIRECT_URI`, `SOCIAL_TOKEN_ENCRYPTION_KEY`, `SOCIAL_WORKER_SECRET`, `SOCIAL_MAX_ATTEMPTS`, `SOCIAL_RETRY_DELAYS`, `SITE_PUBLIC_URL`), com descrições em pt-BR, placeholders sem segredos e defaults recomendados (ex.: retries/versão) quando cabível. Evita variáveis extras sem necessidade. | ✓ |
| SOC-06 + variáveis extras antecipadas (futuras fases) | Adicionar também chaves que possam ser úteis depois (ex.: flags de provider, timeouts específicos) já agora. Pode adiantar convenções, mas arrisca config especulativa fora do escopo da fundação. | |
| Mínimo absoluto (só nomes, sem comentários/defaults) | Listar variáveis sem documentação de formato/uso. Menor esforço, mas reduz clareza operacional e vai contra o objetivo de config documentada. | |

**User's choice:** Cobrir exatamente SOC-06 com comentários e defaults seguros (Recomendado)
**Notes:** Documentação objetiva e alinhada ao escopo da Fase 14.

---

## OpenCode's Discretion

- Nomes exatos de classes/funções/módulos dentro de `app/services/social/` e convenções de import/export.
- Representação interna detalhada de `PublishResult`/categorias e formato exato da exceção de falha de descriptografia.
- Detalhamento fino de colunas/índices adicionais estritamente úteis aos requisitos SOC-01/02/03 e consultas previstas.
- Redação de comentários/mensagens de validação em `.env.example` e Settings.
- Escolha da versão estável de `META_GRAPH_VERSION` como default documentado.

## Deferred Ideas

None — discussion stayed within phase scope.
