# Phase 14: Fundação Social, Dados e Configuração - Research

**Researched:** 2026-11-15
**Domain:** FastAPI backend foundation (SQLAlchemy 2 async + Alembic + Pydantic Settings) for secure social publishing infrastructure (Meta/Facebook-first, extensible)
**Confidence:** HIGH

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
- **D-01:** Usar **Fernet** via biblioteca `cryptography` como abordagem de criptografia reversível/autenticada para `page_access_token` em repouso (SOC-04).
- **D-02:** Centralizar encrypt/decrypt em **serviço/utilitário dedicado** (módulo de crypto/token do domínio social) com chamadas explícitas por modelos/CRUD/fluxos; não usar criptografia transparente implícita que masque erros/vazamentos.
- **D-03:** `SOCIAL_TOKEN_ENCRYPTION_KEY` deve ser **validada no startup** (formato de chave Fernet) com falha explícita se inválida quando aplicável; falhas de descriptografia devem gerar **erro específico sem expor o token** para que fluxos futuros possam tratar reconexão (`needs_reconnect`).
- **D-04:** Persistir o token criptografado como **texto Fernet direto** na coluna de armazenamento (sem prefixo de versão/envelope na Fase 14).
- **D-05:** Modelar status com **enums nativos Postgres por domínio** (ex.: `social_account_status`, `social_post_status`), alinhados ao padrão existente de `JobStatus` em `backend/app/models/job.py`.
- **D-06:** **Criar `social_post_logs` já na Fase 14** (SOC-03 adotado): modelo + migração com FK para `social_posts`, timestamps e campos para tentativa/resultado/erro/resposta resumida, preparando auditoria/retries das fases seguintes.
- **D-07:** `social_posts.job_id` referencia `jobs.id` com **FK `ON DELETE CASCADE`**; definir `attempts` com default 0 e campos operacionais (`scheduled_at`, `next_retry_at`, `last_error`, `external_post_id`, `published_at`, etc.) com nullability/defaults consistentes com o estado do registro.
- **D-08:** Usar **`TIMESTAMP(timezone=True)`/UTC** consistente com o modelo `jobs`. Além da unicidade obrigatória **`(job_id, provider)`** em `social_posts` (SOC-02), incluir **índices operacionais** para elegibilidade/lookup previstos (ex.: status/datas em `social_posts`; provider/status/page_id conforme útil em `social_accounts`) sem indexação excessiva especulativa.
- **D-09:** Definir contrato `SocialPublisher` como **interface async** com método `publish` retornando **resultado tipado** (`PublishResult`), alinhado ao stack async do backend e ao I/O de rede futuro.
- **D-10:** `PublishResult` deve distinguir **sucesso** (incluindo `external_post_id` quando aplicável) e **falha** com categoria/motivo (ex.: transitória/permanente/unknown) e mensagem resumida segura, preparando classificação de retries (PUB-06) sem implementar worker na Fase 14.
- **D-11:** `FacebookPublisher` inicial deve ser um **stub explícito sem chamadas externas/HTTP**: respeita o contrato e retorna falha controlada ou erro explícito documentado, servindo como estrutura pronta para implementação real na Fase 17.
- **D-12:** Organizar domínio social em **`backend/app/services/social/`** (contrato/interface, tipos/resultados, `facebook.py`), mantendo modelos em `backend/app/models/` e schemas em `backend/app/schemas/` conforme convenções existentes.
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

### Deferred Ideas (OUT OF SCOPE)
None — discussão permaneceu dentro do escopo da Fase 14.
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| SOC-01 | Migração cria `social_accounts` com provider, page_id, page_name, token criptografado em repouso, status (`connected`/`needs_reconnect`/`disconnected`), `connected_at`, `token_checked_at` | Padrões de modelo/migração (`Job`, `0001_initial_jobs.py`), enums nativos por domínio (D-05), colunas/índices operacionais e token como texto Fernet (D-04) |
| SOC-02 | Migração cria `social_posts` com FK `job_id`, provider, text, status (`draft`/`scheduled`/`publishing`/`published`/`failed`/`cancelled`), `scheduled_at`, attempts, `next_retry_at`, `last_error`, `external_post_id`, `published_at`, timestamps; índice único `(job_id, provider)` para idempotência | `Mapped`/`mapped_column` + `TIMESTAMP(timezone=True)`/`server_default` como em `jobs`, `UniqueConstraint`/índices compostos, `ON DELETE CASCADE` (D-07), defaults/nullability consistentes |
| SOC-03 | Migração opcional cria `social_post_logs` (histórico de tentativas com resposta resumida da API) se adotado pela implementação | **Adotado** por decisão (D-06): modelo + migração + FK para `social_posts`, timestamps e campos de tentativa/resultado/erro/resposta resumida |
| SOC-04 | `page_access_token` é criptografado em repouso (ex.: Fernet com chave em env `SOCIAL_TOKEN_ENCRYPTION_KEY`); segredos/tokens nunca em logs, respostas de API ou frontend | `cryptography.fernet.Fernet`, serviço dedicado de crypto, validação de chave no startup/erro específico sem vazar token (D-01..D-04), tratamento de segredos em Settings/.env |
| SOC-05 | Interface `SocialPublisher` definida (contrato para publicação); `FacebookPublisher` implementa agora; arquitetura permite `InstagramPublisher` futuro sem reescrever fluxo | Contrato async tipado + `PublishResult` (D-09/D-10), stub explícito sem HTTP (D-11), pacote `app/services/social/` (D-12), desacoplamento por provider |
| SOC-06 | Config/envs documentadas em `.env.example`: `META_APP_ID`, `META_APP_SECRET`, `META_GRAPH_VERSION`, `META_OAUTH_REDIRECT_URI`, `SOCIAL_TOKEN_ENCRYPTION_KEY`, `SOCIAL_WORKER_SECRET`, `SOCIAL_MAX_ATTEMPTS`, `SOCIAL_RETRY_DELAYS`, `SITE_PUBLIC_URL` (e demais necessárias) | Extensão de `Settings` com validações condicionais/formatos/defaults (D-13..D-15), bloco social comentado em pt-BR cobrindo exatamente as variáveis listadas (D-16) |
</phase_requirements>

## Project Constraints (from AGENTS.md)

- Seguir stack/decisões fixas do projeto: backend FastAPI (Python), banco Neon (Postgres), deploy Vercel + Railway/Render; idioma pt-BR. [VERIFIED: AGENTS.md, PROJECT.md]
- Integração social v1.2: Facebook only, 1 página/1 admin, tokens/segredos só no backend criptografados, falha social não bloqueia o site, fire-and-forget, convenções existentes devem ser respeitadas. [VERIFIED: PROJECT.md, STATE.md]
- **Workflow GSD:** antes de usar ferramentas de edição/escrita, iniciar trabalho via comando GSD (`/gsd-quick`, `/gsd-debug`, `/gsd-execute-phase`); não fazer edições diretas fora do fluxo GSD sem pedido explícito. (Restrição operacional para execução/planejamento subsequente; esta pesquisa não altera arquivos de produto.) [VERIFIED: AGENTS.md]

## Summary

Phase 14 é uma fase de **fundação de backend** (dados + segurança + contratos + configuração), sem endpoints OAuth/UI/worker/publicação real. O repositório já fornece todos os padrões necessários: modelos SQLAlchemy 2 declarativos com enums nativos e `TIMESTAMP(timezone=True)` (`backend/app/models/job.py`), migrações Alembic async com enums/índices/constraints explícitos (`backend/alembic/versions/0001_initial_jobs.py`, `backend/alembic/env.py` importa modelos para metadata), `Settings` com `pydantic-settings` e `model_validator` fail-closed/condicional (`backend/app/core/config.py`), e organização de serviços por domínio (`backend/app/services/extraction/`, `turnstile.py`). A implementação deve estender esses padrões, não criar paralelos.

Os pontos sensíveis são (1) **segurança de segredos/tokens**: Fernet exige chave válida, criptografia reversível autenticada, e qualquer falha/log não pode vazar token/segredos (D-01..D-04, D-15, META-05/SOC-04); (2) **correção de schema/migração**: enums nativos por domínio, FKs/cascade, unicidade `(job_id, provider)`, defaults/nullability e índices úteis sem escopo especulativo (D-05..D-08, SOC-01..03); (3) **contrato estável para fases futuras**: `SocialPublisher` async + `PublishResult` tipado + stub explícito sem I/O externo (D-09..D-12), preparando retries/classificação sem executar worker; (4) **configuração explícita e segura**: variáveis SOC-06 exatamente cobertas, opcionais por padrão na Fase 14 mas com validação de formato quando preenchidas e parsing claro de retries (D-13..D-16).

**Primary recommendation:** Implementar em camadas pequenas e explícitas — (a) adicionar `cryptography` e um módulo dedicado `app/services/social/crypto.py` (encrypt/decrypt + exceção específica + validação de chave), (b) criar modelos/enums sociais e registrá-los em `app/models/__init__.py` e `alembic/env.py`, (c) gerar migração Alembic manual/consistente com `0001` criando enums, tabelas `social_accounts`/`social_posts`/`social_post_logs`, constraints/índices, (d) definir contrato/tipos/stub em `app/services/social/` sem HTTP, (e) estender `Settings`/`.env.example` com validações e bloco pt-BR exato de SOC-06.

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Persistência de contas/posts/logs sociais (SOC-01..03) | Database / Storage | API / Backend (ORM/migrations) | Fonte de verdade durável (Neon/Postgres) com integridade referencial, enums, unicidade e índices; backend apenas mapeia/operaciona via SQLAlchemy/Alembic. [VERIFIED: codebase + D-05..D-08] |
| Criptografia em repouso de `page_access_token` (SOC-04) | API / Backend | Database / Storage | Segredo e transformação criptográfica ficam no backend (Fernet/key em env); DB armazena apenas texto cifrado, nunca plaintext. [VERIFIED: D-01..D-04, D-15] |
| Contrato de publicação/provider abstraction (SOC-05) | API / Backend | — | Interface/resultado/stub são lógica de domínio/serviço em Python; publicação real/HTTP é futura (Fase 17) e explicitamente fora de escopo agora. [VERIFIED: D-09..D-12] |
| Configuração/envs Meta/social/worker/site (SOC-06) | API / Backend | — | `Settings` e `.env.example` são fronteira de configuração do backend; segredos nunca expostos ao frontend. [VERIFIED: D-13..D-16, config.py] |
| OAuth, UI integrações, geração/edição, worker/cron/retry operacional, publicação Graph API | — (fora de escopo Fase 14) | — | Explicitamente delegado às Fases 15–17/18; fundação deve apenas preparar estruturas/contratos/config compatíveis. [VERIFIED: CONTEXT, ROADMAP] |

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| FastAPI | 0.143.0 (pinned) | Backend framework | Stack fixo do projeto; integra Pydantic/async. [VERIFIED: backend/pyproject.toml] |
| SQLAlchemy | 2.1.4 (pinned) | ORM async / schema mapping | Padrão existente (`Mapped`, `mapped_column`, async). [VERIFIED: pyproject.toml, app/models/job.py] |
| Alembic | 1.20.0 (pinned in pyproject; 1.17.2 installed in env) | Migrations | Padrão do projeto para versionamento de schema async/Neon. [VERIFIED: pyproject.toml, alembic/env.py, local `alembic --version`] |
| asyncpg | 0.32.0 (pinned) | Async Postgres driver | Driver async atual do backend/Neon. [VERIFIED: pyproject.toml, alembic/env.py] |
| Pydantic / pydantic-settings | 2.14.1 / >=2.4.0,<3.0.0 | Validação e Settings | Base de `Settings` e schemas; validação de env/formato. [VERIFIED: pyproject.toml, config.py] |
| cryptography | 50.0.2 (latest on PyPI at research time) | Fernet token encryption (SOC-04) | Implementação recomendada/locked para Fernet (AES128-CBC+HMAC), API simples e autenticada. [CITED: https://pypi.org/project/cryptography/ | VERIFIED: CONTEXT D-01] |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| httpx | 0.28.1 (pinned) | HTTP client | **Não usar na Fase 14** (stub sem chamadas externas, D-11); relevante apenas como contexto futuro para `FacebookPublisher` real (Fase 17). [VERIFIED: pyproject.toml, D-11] |
| APScheduler | 3.10.4 (pinned) | In-process scheduling | Contexto de compatibilidade futura (worker/polling); Fase 14 não implementa publicação/retry operacional. [VERIFIED: scheduler.py, CONTEXT out-of-scope] |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Fernet (`cryptography`) | AES-GCM primitives / envelope manual | **Não permitido nesta fase**: D-01 trava Fernet; primitives aumentam risco de uso incorreto (nonce/formato) sem benefício requerido. [VERIFIED: D-01, 14-DISCUSSION-LOG] |
| Criptografia transparente no ORM | Serviço/utilitário dedicado explícito | **Não permitido**: D-02 exige chamadas explícitas para evitar mascarar erros/vazamentos. [VERIFIED: D-02] |
| Texto Fernet direto | Bytea/binário ou envelope versionado | **Não permitido agora**: D-04 trava texto direto sem prefixo/envelope na Fase 14. [VERIFIED: D-04] |

**Installation:**
```bash
# backend (adicionar dependência de runtime para SOC-04)
# pyproject.toml: incluir "cryptography==50.0.2" (ou versão compatível validada) em [project].dependencies
pip install cryptography==50.0.2
```

**Version verification:** `cryptography` verificado via PyPI JSON em 2026-11-15 (`info.version = 50.0.2`, `requires_python !=3.9.0,!=3.9.1,>=3.9`, inclui `cryptography.fernet`). Dependências backend existentes verificadas em `backend/pyproject.toml`; Alembic instalado localmente `1.17.2` (diverge do pin `1.20.0` do pyproject — usar versão do projeto/ambiente gerenciado para gerar/aplicar migrations). [CITED: https://pypi.org/pypi/cryptography/json | VERIFIED: pyproject.toml, shell]

## Architecture Patterns

### System Architecture Diagram

```text
[Admin/Operação futura (Fases 15-17)]
            |
            | (não implementado na Fase 14)
            v
+---------------------------+        +------------------------------+
| FastAPI Backend           |        | Neon Postgres                |
|  app/core/config.py       |        |  jobs                        |
|   - Settings META_/SOCIAL_|        |  social_accounts             |
|   - validação formato/key |<------>|   (token cifrado em texto)   |
|                           |  ORM   |  social_posts                |
|  app/services/social/     | Alembic|   UNIQUE(job_id, provider)   |
|   - crypto (Fernet)       |        |   FK -> jobs ON DELETE CASCADE|
|   - publisher contract    |        |  social_post_logs            |
|   - FacebookPublisher stub|        |   FK -> social_posts         |
|     (sem HTTP)            |        |  enums nativos por domínio   |
+---------------------------+        +------------------------------+

Fluxo de dado sensível (SOC-04): plaintext token (futuro, Fase 15) -> crypto.encrypt() no backend -> texto Fernet em DB; decrypt explícito somente quando necessário -> falha gera exceção específica sem expor token. Nunca em logs/respostas/frontend.
```

### Recommended Project Structure
```text
backend/
├── app/
│   ├── core/
│   │   └── config.py                 # + campos/validadores/parsers META_*, SOCIAL_*, SITE_PUBLIC_URL
│   ├── db/
│   │   └── base.py                   # Base declarativa (existente)
│   ├── models/
│   │   ├── __init__.py               # exportar novos modelos/enums sociais
│   │   ├── job.py                    # padrão de referência
│   │   ├── social_account.py         # SocialAccount + SocialAccountStatus (enum nativo)
│   │   ├── social_post.py            # SocialPost + SocialPostStatus (enum nativo)
│   │   └── social_post_log.py        # SocialPostLog (histórico tentativas)
│   ├── schemas/
│   │   └── social.py                 # (opcional na Fase 14, se útil ao contrato/tipos; manter convenção)
│   └── services/
│       └── social/
│           ├── __init__.py
│           ├── crypto.py             # encrypt/decrypt + validação de chave + exceção específica (D-02/D-03)
│           ├── publisher.py          # SocialPublisher (interface async) (D-09)
│           ├── types.py              # PublishResult/categorias/status de falha tipados (D-10)
│           └── facebook.py           # FacebookPublisher stub explícito, sem HTTP (D-11)
├── alembic/
│   ├── env.py                        # importar novos modelos para metadata/autogenerate
│   └── versions/
│       └── 0004_social_foundation.py # (nome/revisão conforme cadeia atual) migração SOC-01..03
└── .env.example                      # bloco social SOC-06 (pt-BR, placeholders, sem segredos)
```
*(Nomes de arquivos/módulos em `services/social/` podem variar dentro da convenção do backend — ver Discretion — mas o pacote e responsabilidades são obrigatórios por D-12.)*

### Pattern 1: SQLAlchemy 2 model + native Postgres enum + UTC timestamps
**What:** Declarar modelos com `Mapped`/`mapped_column`, `SAEnum(..., name=..., native_enum=True)`, `postgresql.TIMESTAMP(timezone=True)` e `server_default=text(...)`.
**When to use:** Todos os modelos sociais (SOC-01..03).
**Example:**
```python
# Source: [VERIFIED: backend/app/models/job.py]
import uuid
from datetime import datetime
from enum import Enum

from sqlalchemy import Enum as SAEnum, Index, String, Text, text
from sqlalchemy.dialects.postgresql import TIMESTAMP, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class JobStatus(str, Enum):
    pending = "pending"
    published = "published"


class Job(Base):
    __tablename__ = "jobs"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )
    status: Mapped[JobStatus] = mapped_column(
        SAEnum(JobStatus, name="job_status", native_enum=True),
        nullable=False,
        server_default=text("'pending'"),
    )
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), nullable=False, server_default=text("now()")
    )
```

### Pattern 2: Alembic async migration with explicit enum/constraints/indexes
**What:** Migração explícita criando tipos enum, tabelas, FKs, unique/indexes; `alembic/env.py` injeta `DATABASE_URL` de Settings e importa modelos.
**When to use:** Migração da fundação social (SOC-01..03).
**Example:**
```python
# Source: [VERIFIED: backend/alembic/versions/0001_initial_jobs.py, backend/alembic/env.py]
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from alembic import op

# env.py: from app.models import Job, JobStatus  # noqa: F401 (registrar metadata)

def upgrade() -> None:
    op.execute("CREATE TYPE job_status AS ENUM ('pending','published','needs_review','invalid');")
    op.create_table(
        "jobs",
        sa.Column("status", postgresql.ENUM("pending", "published", "needs_review", "invalid",
                                            name="job_status", create_type=False),
                  server_default=sa.text("'pending'"), nullable=False),
    )
    op.create_index("ix_jobs_status", "jobs", ["status"])
```

### Pattern 3: Settings validation with `model_validator` and env-driven behavior
**What:** Campos tipados em `BaseSettings` + `@model_validator(mode="after")` para regras condicionais/formatos; propriedades derivadas para parsing.
**When to use:** `META_*`, `SOCIAL_*`, `SITE_PUBLIC_URL`, validação Fernet/retries (D-13..D-16).
**Example:**
```python
# Source: [VERIFIED: backend/app/core/config.py]
from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")
    ENV: str = "dev"
    CORS_ORIGINS: str = "http://localhost:3000"

    @model_validator(mode="after")
    def _validate_cors_origins(self) -> "Settings":
        if self.ENV == "dev":
            return self
        for origin in self.cors_origins_list:
            if origin.endswith("/"):
                raise ValueError("CORS_ORIGINS não pode ter barra final ...")
        return self

    @property
    def cors_origins_list(self) -> list[str]:
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",")]
```

### Pattern 4: Fernet encrypt/decrypt with explicit service boundary
**What:** Usar `cryptography.fernet.Fernet` para gerar chave, `encrypt(bytes)->bytes(token)` e `decrypt(token)->bytes`; armazenar token como texto (`token.decode()`), validar chave com `Fernet(key)` e encapsular erros em exceção específica sem vazar segredo.
**When to use:** `app/services/social/crypto.py` (SOC-04, D-01..D-04).
**Example:**
```python
# Source: [CITED: https://cryptography.io/ (PyPI project docs snippet via pypi.org JSON) / cryptography.fernet]
from cryptography.fernet import Fernet

key = Fernet.generate_key()      # urlsafe base64-encoded 32-byte key (texto/bytes aceitos)
f = Fernet(key)
token = f.encrypt(b"secret")     # -> bytes (Fernet token, base64 urlsafe)
plain = f.decrypt(token)         # -> bytes; levanta InvalidToken se inválido/adulterado
```
*Aplicação no projeto (prescritiva):* `encrypt_token(plaintext: str, settings) -> str` retorna `token.decode()`; `decrypt_token(ciphertext: str, settings) -> str` faz `encode()`/`decrypt()` e converte exceções de token/chave em exceção de domínio específica (ex.: `SocialTokenDecryptError`) com mensagem segura, sem incluir token/chave.

### Pattern 5: Async publisher contract + typed result (no I/O in Phase 14 stub)
**What:** `Protocol`/ABC async com `async def publish(...) -> PublishResult`; resultado tipado distingue sucesso/falha categorizada; stub retorna falha controlada sem HTTP.
**When to use:** `app/services/social/publisher.py`, `types.py`, `facebook.py` (SOC-05, D-09..D-11).
**Example (prescritivo, alinhado ao stack):**
```python
# Source pattern: [ASSUMED] Python typing/async best practice; aligned with [VERIFIED: D-09..D-11]
from enum import Enum
from dataclasses import dataclass
from typing import Protocol

class PublishFailureCategory(str, Enum):
    transient = "transient"   # rede/5xx/rate limit (futuro)
    permanent = "permanent"   # token/permissão/conteúdo (futuro)
    unknown = "unknown"

@dataclass(frozen=True)
class PublishResult:
    ok: bool
    external_post_id: str | None = None
    category: PublishFailureCategory | None = None
    error_message: str | None = None  # resumo seguro, sem segredos

class SocialPublisher(Protocol):
    async def publish(self, post: "SocialPostPayload") -> PublishResult: ...
```
*`FacebookPublisher` (Fase 14):* implementar contrato e retornar falha controlada/erro explícito documentado (ex.: `ok=False, category=unknown/permanent, error_message="publicação real não implementada na Fase 14"`), **sem** `httpx`/chamadas externas.

### Anti-Patterns to Avoid
- **Criptografia implícita/mágica no ORM:** viola D-02 e pode vazar plaintext em logs/erros inesperados; usar chamadas explícitas no serviço dedicado.
- **Logar ou retornar segredos/tokens:** `META_APP_SECRET`, `SOCIAL_WORKER_SECRET`, `SOCIAL_TOKEN_ENCRYPTION_KEY`, tokens e mensagens de exceção não sanitizadas nunca devem ir a logs/respostas/frontend (D-03, D-15, SOC-04).
- **Reimplementar Fernet/crypto manualmente:** usar `cryptography` oficial (D-01).
- **Acoplar fluxo a Facebook:** contrato deve ser por provider (`SocialPublisher`) para permitir `InstagramPublisher` futuro (SOC-05).
- **Criar endpoints/UI/worker/publicação real na Fase 14:** fora de escopo (OAuth/revisão/worker/Graph API pertencem a fases 15–17).
- **Esquecer registro de modelos para Alembic:** novos modelos devem ser importados em `app/models/__init__.py` e em `alembic/env.py` (como `Job/JobStatus`) para metadata/autogenerate coerente.
- **Defaults inseguros para segredos ou variáveis especulativas extras:** `.env.example` deve cobrir exatamente SOC-06 (D-16) com placeholders sem segredos.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Criptografia autenticada de token em repouso | XOR/Base64/AES caseiro, formato próprio | `cryptography.fernet.Fernet` + serviço dedicado | Correção criptográfica, autenticação/integridade, validação de chave, menor risco de erro sutil. [VERIFIED: D-01; CITED: cryptography docs] |
| ORM/mapeamento e migrations | SQL manual solto sem tracking | SQLAlchemy 2 models + Alembic migrations | Consistência com codebase, evolução controlada de schema, enums/constraints/índices versionados. [VERIFIED: codebase] |
| Parsing/validação de settings | Leitura ad-hoc de `os.environ` espalhada | `pydantic-settings` `Settings` + validators/propriedades | Tipagem, defaults, validação centralizada e erros explícitos (padrão existente). [VERIFIED: config.py] |
| Resultados de publicação futuros | Exceções genéricas sem categoria | `PublishResult` tipado com categoria/motivo seguro | Permite retries/classificação (PUB-06) sem acoplar transporte/implementação. [VERIFIED: D-10] |

**Key insight:** Esta fase é sobre **contratos, invariantes e segurança de dados**; soluções “simples” manuais tendem a vazar segredos, quebrar migrations/enums ou acoplar o provider antes da hora.

## Runtime State Inventory

> Step 2.5: Não aplicável. Fase 14 é **greenfield de fundação** (novas tabelas/módulos/config) sem rename/refactor/migração de identificadores existentes. Não altera dados/estado operacional já registrado do sistema atual.

## Common Pitfalls

### Pitfall 1: Vazamento de token/segredo em logs, exceções ou repr
**What goes wrong:** Plaintext/ciphertext de token ou `META_APP_SECRET`/`SOCIAL_WORKER_SECRET`/`SOCIAL_TOKEN_ENCRYPTION_KEY` aparecem em logs, mensagens de erro, responses ou `__repr__`.
**Why it happens:** Uso de `str(e)` bruto, logging de objetos/config, ou exceptions que incluem payload sensível.
**How to avoid:** Exceção de decrypt específica com mensagem fixa/segura (D-03); nunca logar valores de env sensíveis; revisar `__repr__`/serialização de modelos/schemas; não expor campos de token em APIs.
**Warning signs:** `grep` por nomes de variáveis sensíveis em logs/responses de teste; mensagens de erro contendo `gAAAA`/tokens.

### Pitfall 2: Chave Fernet inválida ou ausente tratada tardiamente
**What goes wrong:** Falhas só em runtime ao criptografar/descriptografar, com erro obscuro.
**Why it happens:** Chave não validada no startup ou formato incorreto (não é base64 urlsafe 32-byte).
**How to avoid:** Validar formato/chave em `Settings`/startup conforme aplicável (D-03, D-13): tentativa controlada de instanciar `Fernet(key)`/decodificar, falha explícita e segura. Na Fase 14 as variáveis são **opcionais por padrão** (D-13) — validar **quando preenchidas** e/ou quando funcionalidade exigir, sem defaults inseguros.
**Warning signs:** `ValueError` de Fernet (“Fernet key must be 32 url-safe base64-encoded bytes”) surfando sem contexto.

### Pitfall 3: Enum nativo Postgres mal gerenciado em migrations
**What goes wrong:** Erros de criação duplicada de tipo, autogenerate inconsistente, ou mismatch entre modelo e migration.
**Why it happens:** `create_type=True` conflitando com `op.execute("CREATE TYPE ...")`, ou modelos não importados em `alembic/env.py`.
**How to avoid:** Seguir padrão de `0001_initial_jobs.py`: criar enum explicitamente e referenciar com `postgresql.ENUM(..., name='...', create_type=False)`; registrar modelos em `alembic/env.py` e `app/models/__init__.py`.
**Warning signs:** `DuplicateObject`/`type ... already exists` em migration; autogenerate tentando recriar enum.

### Pitfall 4: Unicidade/idempotência e FKs incorretas
**What goes wrong:** Possível duplicidade `(job_id, provider)` ou órfãos/inconsistência ao apagar vaga.
**Why it happens:** Esquecer `UniqueConstraint`/índice único, FK sem `ondelete='CASCADE'` ou nullability/defaults incoerentes.
**How to avoid:** Implementar exatamente D-07/D-08/SOC-02: `UniqueConstraint("job_id","provider")`, FK `jobs.id` com `ON DELETE CASCADE`, `attempts` default 0, campos operacionais com null/default alinhados ao estado.
**Warning signs:** Inserções duplicadas em testes; registros sociais sobrevivendo a delete de job (quando não desejado).

### Pitfall 5: Parsing frágil de `SOCIAL_RETRY_DELAYS`/defaults
**What goes wrong:** Config aceita valores inválidos (vazios, negativos, não inteiros) ou diverge do default exigido.
**Why it happens:** `split(",")` sem validação, espaços, ou conversão frouxa.
**How to avoid:** Helper/property em `Settings` que parseia CSV de inteiros > 0 em segundos, com default exato `300,900,3600,10800,21600` e erro claro quando preenchido incorretamente (D-14).
**Warning signs:** Lista vazia, `ValueError` genérico, ou delays fora de ordem/semântica inesperada.

### Pitfall 6: Stub do Facebook com I/O acidental ou contrato ambíguo
**What goes wrong:** Stub tenta chamar rede/SDK ou não comunica claramente falha controlada.
**Why it happens:** Reuso prematuro de cliente HTTP/SDK.
**How to avoid:** `FacebookPublisher` sem `httpx`/chamadas externas, retornando `PublishResult` de falha controlada/erro explícito documentado (D-11), respeitando assinatura async (D-09).
**Warning signs:** Dependência implícita de rede em testes unitários da Fase 14.

## Code Examples

### Fernet key validation and safe decrypt (prescritivo)
```python
# Source: [CITED: cryptography.fernet | VERIFIED: D-01..D-03]
from cryptography.fernet import Fernet, InvalidToken

class SocialTokenDecryptError(Exception):
    """Falha segura de descriptografia de token social (sem expor segredo)."""

def validate_fernet_key(key: str) -> None:
    # levanta ValueError se formato inválido (32 bytes urlsafe base64)
    Fernet(key.encode() if isinstance(key, str) else key)

def decrypt_token(ciphertext: str, key: str) -> str:
    try:
        return Fernet(key).decrypt(ciphertext.encode()).decode()
    except (InvalidToken, ValueError, TypeError) as exc:
        raise SocialTokenDecryptError("token social inválido ou chave incorreta") from exc
```

### Alembic: unique constraint + FK cascade + index (padrão)
```python
# Source pattern: [VERIFIED: backend/alembic/versions/0001_initial_jobs.py, SQLAlchemy/Alembic API usage in codebase]
op.create_table(
    "social_posts",
    sa.Column("job_id", postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column("provider", sa.String(length=32), nullable=False),
    sa.Column("attempts", sa.Integer(), nullable=False, server_default=sa.text("0")),
    sa.ForeignKeyConstraint(["job_id"], ["jobs.id"], ondelete="CASCADE"),
    sa.UniqueConstraint("job_id", "provider", name="uq_social_posts_job_provider"),
)
op.create_index("ix_social_posts_status_next_retry", "social_posts", ["status", "next_retry_at"])
```

### Settings: URL/positive-int/CSV parsing helpers (prescritivo)
```python
# Source pattern: [VERIFIED: backend/app/core/config.py]
from urllib.parse import urlparse

def _is_http_url(value: str) -> bool:
    p = urlparse(value)
    return p.scheme in {"http", "https"} and bool(p.netloc)

@property
def social_retry_delays_list(self) -> list[int]:
    raw = self.SOCIAL_RETRY_DELAYS  # default "300,900,3600,10800,21600"
    parts = [p.strip() for p in raw.split(",") if p.strip()]
    delays = [int(p) for p in parts]
    if not delays or any(d <= 0 for d in delays):
        raise ValueError("SOCIAL_RETRY_DELAYS deve conter inteiros > 0 (segundos)")
    return delays
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| SQLAlchemy 1.x / sessões sync | SQLAlchemy 2.0 style (`Mapped`, async engine/session) | Adoção do projeto (v1) | Novos modelos/migrations devem seguir 2.0; não usar padrões legados. [VERIFIED: job.py, session usage] |
| Pydantic v1 | Pydantic v2 + pydantic-settings v2 | Adoção do projeto (v1) | Validators/propriedades em `Settings` no estilo v2 (`model_validator`). [VERIFIED: config.py] |
| Acoplamento direto a provider de rede social | Contrato `SocialPublisher` + stub provider | v1.2 Phase 14 (planejado) | Permite Facebook agora e Instagram futuro sem reescrever fluxo (SOC-05). [VERIFIED: REQUIREMENTS, CONTEXT] |

**Deprecated/outdated:**
- **Tokens em plaintext / segredos no frontend:** proibido pelos requisitos/decisões (SOC-04, D-15, META-05). [VERIFIED]
- **Modelos Groq `llama-3.1-8b-instant`/`llama-3.3-70b`:** aposentados (nota em AGENTS/stack) — não afeta Fase 14, mas manter atenção ao contexto de LLM futuro. [VERIFIED: AGENTS.md]

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | `META_GRAPH_VERSION` default documentado deve ser a versão estável confirmada na documentação Meta no momento da implementação (ex.: valor atual configurável em string), sem hardcode disperso. | User Constraints (Discretion), Standard Stack/Code Examples | Baixo para Fase 14 (apenas config/doc/default string); usar versão estável vigente ao implementar para evitar drift. |
| A2 | Representação interna de `PublishResult` (dataclass vs Pydantic) e nomes exatos de exceções/módulos em `app/services/social/` podem ser escolhidos desde que cumpram D-03/D-09..D-12. | Architecture Patterns, User Constraints (Discretion) | Baixo; risco de pequenas divergências de estilo mitigado seguindo convenções existentes (`services/extraction`). |
| A3 | Índices operacionais “úteis previstos” além dos obrigatórios (ex.: `status/next_retry_at/scheduled_at` em `social_posts`, `provider/status/page_id` em `social_accounts`) são suficientes sem indexação especulativa. | Common Pitfalls/Architecture (D-08) | Baixo/médio; consultas exatas do worker virão nas fases 16–17, mas índices modestos escolhidos agora são fáceis de ajustar em migration futura. |
| A4 | Pin recomendado `cryptography==50.0.2` é adequado para Python 3.11+ do backend (PyPI declara >=3.9). | Standard Stack | Baixo; validar resolução de dependências no ambiente do projeto ao implementar. |

## Open Questions

1. **Comportamento exato de validação de `SOCIAL_TOKEN_ENCRYPTION_KEY` quando vazia na Fase 14**
   - What we know: Variáveis sociais opcionais por padrão na Fase 14 (D-13), mas D-03 exige validação de formato no startup e falha explícita se inválida quando aplicável; segredos sem defaults inseguros (D-15).
   - What's unclear: “quando aplicável” — validar sempre que não vazia (recomendado) vs exigir preenchida em determinados `ENV`.
   - Recommendation: **Validar formato sempre que o valor estiver preenchido** (fail-fast em chave inválida) e permitir vazio na Fase 14 para não bloquear ambientes que ainda não usam social, deixando exigência operacional para fases que consomem a chave; documentar claramente no `.env.example`/Settings. [ASSUMED, alinhado a D-13/D-03]

2. **Campos mínimos adicionais de `social_post_logs`**
   - What we know: D-06 exige modelo+migração com FK para `social_posts`, timestamps e campos para tentativa/resultado/erro/resposta resumida.
   - What's unclear: Nomes/tipos exatos (ex.: `attempt_number`, `status/result`, `http_status`, `response_summary`, `error_message`).
   - Recommendation: Incluir conjunto enxuto e explícito que suporte auditoria/retry futuro (tentativa, sucesso/falha ou status, mensagem/erro resumido seguro, resumo de resposta/`external_id` se houver, timestamps), sem armazenar payloads sensíveis. [ASSUMED]

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| Python | Backend tooling/runtime | ✓ | 3.13.3 (local) | — (projeto requer >=3.11) [VERIFIED: shell, pyproject] |
| pip | Instalar `cryptography`/deps | ✓ | 26.3 | — [VERIFIED: shell] |
| Alembic CLI | Gerar/aplicar migrações | ✓ | 1.17.2 (local) / 1.20.0 (pin projeto) | Usar env do projeto alinhado ao pin ao executar migrations [VERIFIED: shell, pyproject] |
| PostgreSQL/Neon (DATABASE_URL) | Aplicar/testar migrations e constraints reais | ? | — | `alembic upgrade`/testes DB-backed dependem de DB configurado; suíte DB tem gaps de reprodutibilidade herdados (STATE). [VERIFIED: STATE/PROJECT context] |
| `cryptography` package | SOC-04 (Fernet) | ✗ (não presente em pyproject hoje) | 50.0.2 disponível no PyPI | Adicionar ao `pyproject.toml`/instalar no ambiente antes de implementar/rodar. [VERIFIED: pyproject grep/absence, PyPI] |

**Missing dependencies with no fallback:**
- DB de teste migrado/reprodutível para validar migrations/integridade em CI/local de forma completa (gap herdado do v1.1). [VERIFIED: STATE.md]

**Missing dependencies with fallback:**
- `cryptography` ausente no projeto: fallback é adicionar a dependência (ação obrigatória do plano). [VERIFIED]

## Validation Architecture

> `workflow.nyquist_validation` está habilitado em `.planning/config.json` (true).

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest 9.1.1 + pytest-asyncio (>=1.0.0,<2.0.0), `asyncio_mode=auto` |
| Config file | `backend/pyproject.toml` (`[tool.pytest.ini_options]`) |
| Quick run command | `cd backend && pytest tests/test_social_*.py -x` (ou alvo equivalente criado pela fase) |
| Full suite command | `cd backend && pytest` |

### Phase Requirements → Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| SOC-01 | Schema/ORM de `social_accounts` (campos, status enum, token armazenado como texto cifrado, timestamps) | integration (DB) / unit de modelo | `cd backend && pytest tests/test_social_models.py -x` | ❌ Wave 0 |
| SOC-02 | Schema/ORM de `social_posts` (FK `jobs` com CASCADE, unicidade `(job_id,provider)`, attempts/defaults, campos/timestamps) | integration (DB) / unit de modelo | `cd backend && pytest tests/test_social_models.py -x` | ❌ Wave 0 |
| SOC-03 | Schema/ORM de `social_post_logs` com FK para `social_posts` e campos de tentativa/resultado/erro/resposta resumida | integration (DB) / unit de modelo | `cd backend && pytest tests/test_social_models.py -x` | ❌ Wave 0 |
| SOC-04 | `encrypt/decrypt` com Fernet, chave válida/ inválida, decrypt falha com exceção específica sem expor token; token persistido como texto | unit | `cd backend && pytest tests/test_social_crypto.py -x` | ❌ Wave 0 |
| SOC-05 | Contrato `SocialPublisher` async, `PublishResult` tipado (sucesso/falha categorizada), `FacebookPublisher` stub sem chamadas externas/HTTP e comportamento controlado | unit | `cd backend && pytest tests/test_social_publisher.py -x` | ❌ Wave 0 |
| SOC-06 | Settings aceitam/validam `META_*`, `SOCIAL_*`, `SITE_PUBLIC_URL` (formato quando preenchidos, defaults, parser de retries) e `.env.example` cobre exatamente variáveis exigidas | unit | `cd backend && pytest tests/test_social_config.py -x` | ❌ Wave 0 |

*Nota:* testes de integração DB dependem de `TEST_DATABASE_URL`/banco migrado (gap conhecido); testes unitários de crypto/config/publisher devem rodar sem rede/DB.

### Sampling Rate
- **Per task commit:** `cd backend && pytest tests/test_social_*.py -x` (ou subset do arquivo alterado)
- **Per wave merge:** `cd backend && pytest`
- **Phase gate:** Suíte alvo da fase verde antes de `/gsd-verify-work` (sujeito à disponibilidade de DB para testes de integração)

### Wave 0 Gaps
- [ ] `backend/tests/test_social_crypto.py` — cobre SOC-04 (Fernet, chave inválida, decrypt seguro)
- [ ] `backend/tests/test_social_publisher.py` — cobre SOC-05 (contrato async, resultado tipado, stub sem HTTP)
- [ ] `backend/tests/test_social_config.py` — cobre SOC-06 (Settings/.env.example expectativas de parsing/validação)
- [ ] `backend/tests/test_social_models.py` — cobre SOC-01/02/03 (constraints/enums/defaults; integração DB quando disponível)
- [ ] `backend/tests/conftest.py` — confirmar/estender fixtures DB/Settings se necessário (arquivo pode existir; validar na implementação)
- [ ] Framework install: `pip install cryptography==50.0.2` (e deps do projeto) — se ausente

*(Se DB de teste não estiver disponível, priorizar testes unitários determinísticos e registrar lacuna de integração como conhecida/deferida conforme padrão do projeto.)*

## Security Domain

### Applicable ASVS Categories

| ASVS Category | Applies | Standard Control |
|---------------|---------|-----------------|
| V2 Authentication | no (fase sem OAuth/login novo) | N/A nesta fase; OAuth/fluxo Meta em Fase 15. |
| V3 Session Management | no | N/A (sem sessões novas). |
| V4 Access Control | no (sem novos endpoints expostos) | N/A nesta fase; garantir que nada sensível seja exposto futuramente. |
| V5 Input Validation | yes | Validar formatos/valores de env e parsing (`META_*`, URLs http/https, inteiros>0, CSV delays) via `Settings` validators (D-13..D-15). |
| V6 Cryptography | yes | `cryptography.fernet` para criptografia autenticada em repouso; chave em env validada; nunca hand-roll; falhas sem vazar segredo (SOC-04, D-01..D-04). |

### Known Threat Patterns for {FastAPI + SQLAlchemy/Alembic + Fernet + Meta integration foundation}

| Pattern | STRIDE | Standard Mitigation |
|---------|--------|---------------------|
| Vazamento de `page_access_token`/segredos em logs, exceptions, dumps de config | Information Disclosure | Criptografar em repouso, exceções seguras, não logar valores sensíveis, não expor em schemas/respostas/frontend (SOC-04, D-03, D-15). |
| Uso de chave Fernet fraca/inválida ou hardcoded | Information Disclosure / Tampering | Validar chave (formato/url-safe base64 32 bytes), carregar via env, sem defaults inseguros (D-03, D-15). |
| Config inválida aceita silenciosamente (URLs/delays) causando falhas operacionais futuras | Tampering / Denial of Service (operacional) | Validação explícita quando preenchido + defaults seguros documentados (D-13, D-14). |
| Duplicação de publicação futura por falta de idempotência estrutural | Tampering / Repudiation (operacional) | Unicidade `(job_id, provider)` e modelagem de status/ids desde a fundação (SOC-02, D-08) — enforcement operacional em Fase 17. |

## Sources

### Primary (HIGH confidence)
- [VERIFIED: codebase] `backend/app/core/config.py` — padrões de `Settings`, `model_validator`, propriedades derivadas, tratamento de segredos/test keys.
- [VERIFIED: codebase] `backend/app/models/job.py`, `backend/app/models/__init__.py`, `backend/app/db/base.py` — padrões de modelo SQLAlchemy 2, enums nativos, timestamps UTC, índices/constraints.
- [VERIFIED: codebase] `backend/alembic/env.py`, `backend/alembic/versions/0001_initial_jobs.py`, `0002_jobs_source_snippet.py`, `0003_search_text_requirements.py` — padrão de migrations async, enums, FKs/índices, registro de modelos.
- [VERIFIED: codebase] `backend/.env.example`, `backend/pyproject.toml` — convenções de env/dependências e ausência atual de `cryptography`.
- [VERIFIED: codebase] `backend/app/services/{extraction,turnstile.py,cities.py}`, `backend/app/core/scheduler.py`, `backend/app/api/v1/{admin.py,router.py}`, `backend/app/main.py` — organização de serviços, scheduler, rotas/admin (contexto estrutural).
- [VERIFIED: planning] `.planning/phases/14-fundacao-social-dados-e-configuracao/14-CONTEXT.md`, `14-DISCUSSION-LOG.md`, `.planning/REQUIREMENTS.md`, `.planning/ROADMAP.md`, `.planning/STATE.md`, `.planning/config.json`, `AGENTS.md`.
- [CITED: https://pypi.org/pypi/cryptography/json] PyPI project metadata (cryptography 50.0.2, requires_python, Fernet usage snippet in description) — verificação de versão/capacidade em 2026-11-15.

### Secondary (MEDIUM confidence)
- [ASSUMED + aligned to verified project patterns] Representações internas idiomáticas de `Protocol`/`dataclass`/`Enum` para `SocialPublisher`/`PublishResult` em Python 3.11+ (não requer biblioteca adicional).

### Tertiary (LOW confidence)
- None.

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - versões e padrões verificados no código/projeto; `cryptography` verificado via PyPI.
- Architecture: HIGH - fundamentada em padrões existentes do backend e decisões travadas D-01..D-16.
- Pitfalls: HIGH - derivados de invariantes de segurança/DB/migrations explícitos no contexto e no código atual.

**Research date:** 2026-11-15
**Valid until:** 2026-12-15 (stack estável; revalidar `META_GRAPH_VERSION` default e versão de `cryptography` no momento da implementação)
