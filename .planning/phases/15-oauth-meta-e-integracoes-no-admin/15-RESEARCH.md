# Phase 15: OAuth Meta e Integrações no Admin - Research

**Researched:** 2026-11-15
**Domain:** FastAPI backend (Meta/Facebook OAuth + Graph API integration) + Next.js admin UI (App Router) for secure single-page connection management
**Confidence:** HIGH

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
- **D-01:** Gerar e validar `state` anti-CSRF como **token assinado/stateless com expiração** no backend (sem persistência em tabela para o `state`), rejeitando callback com assinatura inválida, expirado ou adulterado.
- **D-02:** Experiência em **redirect na mesma aba**: ação "Conectar" inicia endpoint backend autenticado que redireciona ao Meta; o callback processa no backend e redireciona de volta à página de Integrações com resultado seguro (sucesso/erro/cancelamento/etapa pendente).
- **D-03:** Em cancelamento ou falha no callback/troca de tokens, **redirecionar com erro seguro** para a UI de Integrações (indicador/código genérico, sem segredos/tokens); nada deve ser persistido como conectado. Logs no backend devem conter apenas detalhes seguros.
- **D-04:** Modelo de proteção: **início autenticado + callback validado por `state`**. `/oauth/start` (ou equivalente) exige admin autenticado (JWT, conforme padrão atual). `/oauth/callback` aceita redirect do navegador sem `Authorization` Bearer, mas só conclui a operação se o `state` assinado/TTL for válido, executando troca/validação/persistência inteiramente no backend.
- **D-05:** Se `/me/accounts` retornar múltiplas páginas, exigir **escolha explícita na UI** antes de salvar; se retornar uma única página elegível, o fluxo pode concluir automaticamente após validação (mantendo a garantia de salvar apenas 1 página).
- **D-06:** Ao concluir nova conexão/seleção ou reconexão com conexão já existente, **substituir a conexão ativa** para manter uma única página/conexão vigente (1 página/1 admin), atualizando página/tokens/metadados conforme aplicável.
- **D-07:** Ao desconectar, **remover credenciais e marcar desconectado**: limpar/remover o token criptografado utilizável e atualizar/remover o registro de forma que nenhum segredo reutilizável permaneça e a UI indique ausência de conexão.
- **D-08:** Para suportar seleção explícita quando houver múltiplas páginas, usar **etapa pendente intermediada pelo backend**: o callback cria estado pendente seguro (lista de páginas disponíveis sem tokens, associada ao fluxo) e redireciona a UI para carregar/confirmar a seleção via endpoint autenticado antes de persistir tokens/conexão final.
- **D-09:** Validar token/página **no callback (ao concluir/confirmar conexão)** e **sob demanda** quando o admin abrir/atualizar status ou acionar "Verificar agora" em Integrações (sem jobs periódicos nesta fase).
- **D-10:** Política de transição para `needs_reconnect`: marcar apenas em **falhas definitivas** confirmadas (token inválido/expirado, permissões revogadas/insuficientes, página inacessível). **Falhas transitórias** (rede, 5xx, timeout/rate limit temporário na verificação) não devem derrubar uma conexão previamente válida; devem retornar erro de verificação seguro para a UI.
- **D-11:** Endpoint(s) de status devem expor **payload completo e seguro** para a UI (sem tokens/segredos): estado (`connected`/`needs_reconnect`/`disconnected`), identificador e nome da página (quando houver), datas relevantes (ex.: conectado/verificado), indicação de seleção pendente se aplicável, e alerta/motivo resumido seguro em erro/reconexão.
- **D-12:** Ações de recuperação/verificação: oferecer **"Reconectar"** (reinicia fluxo OAuth e, ao concluir, substitui a conexão ativa conforme D-06) e **"Verificar agora"** (revalida sob demanda e atualiza status/alerta conforme D-09/D-10).
- **D-13:** Criar **nova página dedicada de Integrações** com item de navegação claro no admin (consistente com a estrutura atual em `frontend/app/admin/*` e layout), em vez de embutir em tela existente.
- **D-14:** A UI deve representar **estados completos com CTAs claros**: desconectado (Conectar), seleção de página pendente (listar/confirmar página), conectado (exibir nome/status da página, Verificar agora, Desconectar), requer reconexão (alerta + Reconectar), além de loading/erros de ação.
- **D-15:** A ação **"Desconectar" exige confirmação** na UI antes de chamar o backend.
- **D-16:** Ao retornar do redirect do OAuth (sucesso, erro, cancelamento ou seleção pendente), exibir **banner/alerta contextual** ao carregar, atualizar o status exibido e manter feedback consistente com os padrões visuais/componentes do admin.

### OpenCode's Discretion
- Nomes, paths e formato exato dos endpoints/routes backend e frontend para OAuth/integrações (desde que respeitem proteção, escopo e ausência de segredos no cliente).
- Formato interno do `state` assinado, TTL, claims mínimos e segredo/chave usados para assinatura/verificação (seguro, server-side).
- Mecanismo de armazenamento temporário da etapa pendente de seleção (em memória/processo, DB, cache ou estrutura assinada efêmera) desde que não exponha tokens, tenha expiração/limpeza adequada e suporte o fluxo autenticado de confirmação.
- Campos exatos retornados por `/debug_token`/Graph usados para decidir validade, permissões e `needs_reconnect`, e redação de mensagens de erro/alerta resumidas e seguras.
- Estrutura de módulos/serviços/schemas no backend (ex.: service de OAuth/Meta, integração em router admin ou router dedicado) e composição de componentes/hooks na UI admin, seguindo convenções existentes.
- Copy, ícones e detalhes visuais da tela de Integrações, desde que alinhados ao tema/padrões do admin e aos estados/ações definidos.

### Deferred Ideas (OUT OF SCOPE)
None — discussion stayed within phase scope.
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| META-01 | Backend expõe endpoints OAuth Meta: iniciar (gera `state` anti-CSRF e redireciona), callback (valida `state`, troca code→user token→long-lived token, lista páginas via `/me/accounts`, obtém page access token), desconectar, status | OAuth flow/state/callback/start patterns, token exchange chain, `/me/accounts` selection/persistence, protected start/status/disconnect and unauthenticated-but-state-validated callback |
| META-02 | Permissões mínimas solicitadas: `pages_show_list`, `pages_manage_posts`, `pages_read_engagement`; usa versão fixa/configurável da Graph API (`META_GRAPH_VERSION`, estável confirmada na doc) | Scope set and versioned Graph URLs from `settings.META_GRAPH_VERSION`; permission reference confirms availability |
| META-03 | Fluxo suporta seleção da Página quando houver mais de uma; salva apenas uma única Página/conexão (único admin) | `/me/accounts` handling, pending-selection step (D-05/D-08), single-active-connection replacement (D-06) |
| META-04 | Page token derivado de long-lived user token é validado (ex.: `/debug_token`); token inválido/expirado marca conta `needs_reconnect` e gera alerta no painel | `/debug_token` fields/app access token usage, definitive vs transient failure classification (D-10), on-demand validation points (D-09) |
| META-05 | App Secret e tokens permanecem somente no backend; nenhuma credencial exposta ao frontend | Backend-only Graph calls, encrypted-at-rest storage, safe status payloads, no tokens in URLs/logs/responses |
| META-06 | Tela/seção admin "Integrações" permite conectar/desconectar Facebook, exibe status da conexão, nome da página e alerta de reconexão necessária | New admin route/nav, stateful UI with CTAs/banners/confirm dialog, authenticated API consumption from existing frontend patterns |
</phase_requirements>

## Project Constraints (from AGENTS.md)

- **Stack fixa:** Backend FastAPI (Python) + SQLAlchemy 2 async/Alembic + Neon Postgres; Frontend Next.js 16 (App Router) + Tailwind/dark mode; Cloudflare Turnstile disponível no ecossistema; deploy Vercel + Railway/Render. [VERIFIED: AGENTS.md, pyproject.toml, package.json context]
- **Produto/locale:** pt-BR, admin único (master), 1 página/1 admin para integração social, Facebook only nesta fase/milestone, falha social não pode bloquear o site. [VERIFIED: AGENTS.md, PROJECT/ROADMAP/REQUIREMENTS]
- **Segurança:** App Secret/tokens/segredos somente no backend; `page_access_token` criptografado em repouso; nunca expor segredos em logs, respostas de API ou frontend. [VERIFIED: AGENTS.md, 14-CONTEXT, 14-RESEARCH, crypto.py/config.py]
- **Padrões existentes obrigatórios:** seguir convenções atuais de `Settings` (pydantic-settings/validators), modelos SQLAlchemy 2 (`Mapped`, enums nativos, `TIMESTAMP(timezone=True)`), auth JWT via `require_admin`/`Authorization: Bearer`, organização de serviços por domínio (`app/services/social/`), admin em `frontend/app/admin/*` com layout compartilhado e helpers em `frontend/lib/api.ts`/`lib/auth.ts`. [VERIFIED: codebase]
- **GSD workflow enforcement:** edições de produto devem ocorrer via fluxo GSD (`/gsd-execute-phase` etc.); esta pesquisa produz apenas `15-RESEARCH.md` conforme solicitado. [VERIFIED: AGENTS.md]

## Summary

Phase 15 estende a fundação da Fase 14 (`SocialAccount`, `SocialAccountStatus`, `services/social/crypto.py`, `META_*`/`SOCIAL_*` em `Settings`) para entregar um fluxo OAuth Meta completo e seguro, sem publicação/worker (Fases 16–17). O núcleo técnico é um fluxo **server-mediated**: `start` autenticado gera `state` assinado/stateless (D-01) e redireciona para o Login Dialog; `callback` (sem Bearer, mas protegido por `state`) troca `code` por tokens, resolve página(s), valida e persiste conexão; endpoints autenticados expõem status/ações (`status`, `verify`, `disconnect`, confirmação de seleção pendente) consumidos por uma nova página `admin/integracoes` com estados/CTAs claros (D-13..D-16).

A cadeia Meta correta para Page token durável é: `code` → short-lived user token (`GET /oauth/access_token?code=...`) → long-lived user token (`GET /oauth/access_token?grant_type=fb_exchange_token&fb_exchange_token=...`) → `GET /me/accounts` (ou `/PAGE_ID?fields=access_token,name` se necessário) com user token long-lived para obter page access token adequado; validar com `GET /debug_token` usando app access token (`{META_APP_ID}|{META_APP_SECRET}`) e checar validade/escopos/perfil antes de marcar conectado. [CITED: Meta access-tokens/get-long-lived, debug_token, social-sdk/community guides corroborating official behavior]. A implementação deve usar sempre `META_GRAPH_VERSION` configurável na construção de URLs/paths (D-02/META-02), nunca hardcode disperso.

Os riscos principais são segurança e consistência de estado: `callback` é endpoint de browser sem JWT (exigência de redirect), então a validação criptográfica/expiração do `state` é a barreira anti-CSRF/forgery; tokens nunca podem ir a query params de retorno para UI, logs ou payloads; seleção pendente com múltiplas páginas não pode persistir tokens em local inseguro; e falhas transitórias de verificação sob demanda não podem degradar conexão válida para `needs_reconnect` (D-10). A recomendação é encapsular OAuth/Graph em `app/services/social/meta_oauth.py` (ou módulo equivalente) + schemas/rotas dedicadas, com respostas seguras e testes unitários/mocks de HTTP.

**Primary recommendation:** Implementar OAuth como orquestração backend-only (state assinado JWT curto, callback validado por state, troca para long-lived user token antes de `/me/accounts`, page token criptografado via `crypto.py`, validação por `/debug_token` com app token) e uma UI admin dedicada que consome apenas payloads sanitizados e reage a códigos de retorno seguros do redirect.

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Início OAuth autenticado, geração/validação de `state`, callback e troca de tokens | API / Backend (FastAPI) | — | Segredos (`META_APP_SECRET`, tokens) e verificação anti-CSRF devem permanecer server-side (META-05, D-01/D-04). [VERIFIED: CONTEXT, config.py, deps.py] |
| Chamadas Graph (`oauth/access_token`, `/me/accounts`, `/debug_token`) e decisão de elegibilidade/validade | API / Backend (service layer) | External (Meta Graph API) | I/O externo e interpretação de validade/permissões pertencem ao backend; UI nunca fala com Graph. [CITED: Meta docs; VERIFIED: D-09/D-10] |
| Persistência de conexão ativa única, status e timestamps | Database / Storage (Neon/Postgres) | API / Backend (ORM) | `SocialAccount` é a fonte de verdade (`connected/needs_reconnect/disconnected`, `page_*`, token cifrado, `connected_at`, `token_checked_at`). [VERIFIED: social_account.py] |
| Seleção pendente quando houver múltiplas páginas (sem tokens expostos) | API / Backend | Database / Storage ou store efêmero server-side | Etapa intermediada pelo backend (D-08) exige estado seguro/expirável e confirmação autenticada antes de persistir conexão final. [VERIFIED: D-05/D-08] |
| Tela de Integrações, navegação, banners/CTAs/confirmação e consumo de status/ações | Frontend Server/Client (Next.js admin) | — | UX/admin sob `frontend/app/admin/*`; ações autenticadas via Bearer do `sessionStorage` usando padrões existentes. [VERIFIED: admin layout/page/api/auth patterns] |
| Publicação de posts, worker, retries operacionais, UI por vaga | — (fora de escopo Fase 15) | — | Pertencem às Fases 16–17. [VERIFIED: ROADMAP/REQUIREMENTS] |

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| FastAPI | 0.143.0 | Rotas OAuth/status/disconnect/verify/select, redirects e validação de dependências | Stack fixo do backend. [VERIFIED: pyproject.toml] |
| SQLAlchemy | 2.1.4 | Ler/gravar `SocialAccount` (substituição de conexão ativa, status/timestamps) | ORM/padrão existente do projeto. [VERIFIED: pyproject.toml, social_account.py] |
| Pydantic / pydantic-settings | 2.14.1 / >=2.4.0,<3.0.0 | Schemas de request/response seguros, parsing/validação de env/config | Padrão do backend (`Settings`, schemas). [VERIFIED: pyproject.toml, config.py] |
| httpx | 0.28.1 | Chamadas HTTP ao Graph API (token exchange, `/me/accounts`, `/debug_token`) | Já presente; cliente HTTP async adequado para FastAPI. [VERIFIED: pyproject.toml] |
| cryptography (Fernet) | 50.0.2 | Criptografar `page_access_token` em repouso via serviço existente | Implementação locked da Fase 14. [VERIFIED: crypto.py, pyproject.toml] |
| PyJWT | 2.15.1 | Base para token assinado/stateless de `state` (HS256/JWS-like claims com TTL) e alinhamento com auth existente | Já usado para JWT admin (`core/security.py`); evita nova dependência para assinatura simples. [VERIFIED: pyproject.toml, security.py] |
| Next.js (App Router) + React | 16.x + 19.x | Página `admin/integracoes`, navegação, estados client-side e feedback | Stack fixa do frontend/admin. [VERIFIED: AGENTS.md, admin files] |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| `secrets` / `hmac` (stdlib) | stdlib | Nonces/ids auxiliares se necessário | Complementar assinatura/identificadores; não substituir validação criptográfica do `state`. [ASSUMED stdlib] |
| APScheduler | 3.10.4 | — | **Não usar na Fase 15** (sem jobs periódicos por D-09). [VERIFIED: CONTEXT, pyproject.toml] |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| `state` assinado/stateless (D-01) | Persistir `state` em tabela | **Não permitido** por D-01; stateless com TTL reduz estado persistido para anti-CSRF. |
| `PyJWT` para assinar `state` | `itsdangerous` / HMAC manual | Possível, mas adiciona dependência ou código extra; `PyJWT` já existe e suporta claims/expiração. [ASSUMED - escolha de conveniência] |
| Callback browser + redirect seguro (D-02/D-04) | Popup + postMessage | Mudaria UX/fluxo; redirect na mesma aba é decisão locked. |
| Seleção pendente em store assinado efêmero/DB transitória | Guardar tokens em cookie/localStorage | **Proibido** por segurança (META-05/D-08); tokens devem permanecer no backend. |

**Installation:**
```bash
# Nenhuma dependência nova obrigatória identificada.
# Backend já possui: httpx, PyJWT, cryptography, fastapi/sqlalchemy.
# Frontend não requer nova lib para esta fase (usar fetch/helpers existentes).
```

**Version verification:** versões do backend confirmadas em `backend/pyproject.toml` (FastAPI 0.143.0, httpx 0.28.1, PyJWT 2.15.1, cryptography 50.0.2, SQLAlchemy 2.1.4). `META_GRAPH_VERSION` default atual em `Settings` é `v21.0` (configurável, validado como string de env). [VERIFIED: pyproject.toml, config.py]

## Architecture Patterns

### System Architecture Diagram

```text
[Admin UI: /admin/integracoes (browser)]
   |  (1) click "Conectar" (Bearer JWT no start request)
   v
[GET /api/v1/admin/integrations/meta/oauth/start] --auth--> valida admin -> gera state assinado/TTL
   | 302 redirect
   v
[facebook.com/v{META_GRAPH_VERSION}/dialog/oauth?client_id&redirect_uri&scope&state&response_type=code]
   |  user consente/cancela (mesma aba)
   v
[GET /api/v1/admin/integrations/meta/oauth/callback?code|error&state]  (sem Bearer)
   |  valida state (assinatura+exp) -> troca code->short user token -> long-lived user token
   |  -> GET /me/accounts (long-lived user token) -> resolve 1 ou N páginas
   |  -> valida token/página (/debug_token, app token)
   |      ├─ 1 página elegível: criptografa page token, upsert/substitui SocialAccount connected, 302 -> /admin/integracoes?result=connected
   |      ├─ N páginas: cria pendência segura SEM tokens -> 302 -> /admin/integracoes?result=select_page&pending=...
   |      └─ erro/cancel: nada persistido como conectado -> 302 -> /admin/integracoes?result=error&reason=safe_code
   v
[Admin UI carrega status seguro] <----(GET autenticado)---- [GET /status]
   ├─ selection pending -> GET /pending-pages + POST /select-page (autenticado)
   ├─ connected -> POST /verify (sob demanda) / POST /disconnect (com confirmação)
   └─ needs_reconnect/disconnected -> CTA Reconectar/Conectar
```

### Recommended Project Structure
```text
backend/app/
├── api/v1/
│   ├── admin.py                         # existente (jobs/expire) — manter
│   ├── integrations.py                  # NOVO: rotas Meta/OAuth/status/verify/select/disconnect
│   └── router.py                        # incluir integrations router
├── schemas/
│   └── social_integrations.py           # NOVO: status payload, pending pages, select request/response seguros
├── services/social/
│   ├── crypto.py                        # existente (reusar)
│   ├── meta_oauth.py                    # NOVO: state, token exchange, /me/accounts, debug_token, regras D-09/D-10
│   └── meta_graph.py                    # (opcional) client fino httpx/versionado
├── models/
│   └── social_account.py                # existente (reusar/substituir ativo, limpar token no disconnect)
└── core/
    └── config.py                        # existente (META_*, JWT_SECRET etc.)

frontend/
├── app/admin/
│   ├── layout.tsx                       # adicionar link "Integrações"
│   ├── page.tsx                         # opcional: card/link para Integrações
│   └── integracoes/
│       ├── page.tsx                     # NOVO: página dedicada
│       └── IntegrationsClient.tsx       # NOVO (client): fetch status/ações, banners, estados/CTAs
├── components/admin/                    # reusar ToastProvider/diálogos/padrões se útil
└── lib/
    └── api.ts                           # adicionar helpers Meta integrations (Bearer + ApiError)
```

### Pattern 1: Server-mediated OAuth with signed stateless `state` (D-01/D-02/D-04)
**What:** `start` (autenticado) cria `state` assinado com TTL curto e claims mínimas (ex.: `purpose`, `iat/exp`, nonce) usando segredo server-side; redireciona para `https://www.facebook.com/{META_GRAPH_VERSION}/dialog/oauth` com `client_id`, `redirect_uri`, `state`, `scope`, `response_type=code`. `callback` rejeita ausência/assinatura inválida/expiração e nunca confia em sessão frontend.
**When to use:** META-01, anti-CSRF do callback browser.
**Example:**
```python
# Source pattern: [VERIFIED: PyJWT usage in backend/app/core/security.py]
# + [CITED: Meta Manual Login Flow - state required for CSRF protection]
import uuid
from datetime import datetime, timedelta, timezone
import jwt
from fastapi.responses import RedirectResponse

META_OAUTH_STATE_TTL_SECONDS = 10 * 60

def build_meta_oauth_state(secret: str) -> str:
    now = datetime.now(timezone.utc)
    claims = {
        "purpose": "meta_oauth",
        "nonce": str(uuid.uuid4()),
        "iat": now,
        "exp": now + timedelta(seconds=META_OAUTH_STATE_TTL_SECONDS),
    }
    return jwt.encode(claims, secret, algorithm="HS256")

def validate_meta_oauth_state(state: str, secret: str) -> dict:
    return jwt.decode(state, secret, algorithms=["HS256"])  # PyJWTError -> reject

# redirect_uri must match app config; META_GRAPH_VERSION is configurable
def dialog_url(graph_version: str, app_id: str, redirect_uri: str, state: str) -> str:
    scope = "pages_show_list,pages_manage_posts,pages_read_engagement"
    return (
        f"https://www.facebook.com/{graph_version}/dialog/oauth"
        f"?client_id={app_id}&redirect_uri={redirect_uri}"
        f"&state={state}&response_type=code&scope={scope}"
    )
```

### Pattern 2: Correct token exchange chain before persisting page connection (META-01/META-03/META-04)
**What:** Trocar `code` por user token, **trocar por long-lived user token** (`grant_type=fb_exchange_token`), depois listar páginas com user token long-lived (`/me/accounts`) e validar token/página (`/debug_token`). Persistir apenas page access token selecionado, criptografado.
**When to use:** Callback sucesso e confirmação de seleção pendente.
**Example:**
```python
# Source: [CITED: Meta "Get a Long-Lived User Access Token" / "Get a Long-Lived Page Access Token"]
# [CITED: /debug_token reference - app access token required]
# GET /{v}/oauth/access_token?client_id=...&redirect_uri=...&client_secret=...&code=...
# GET /{v}/oauth/access_token?grant_type=fb_exchange_token&client_id=...&client_secret=...&fb_exchange_token={short_user_token}
# GET /{v}/me/accounts?fields=id,name,access_token,tasks&access_token={long_lived_user_token}
# GET /{v}/debug_token?input_token={page_access_token}&access_token={app_id}|{app_secret}

async def exchange_code_for_long_lived_user_token(...): ...
async def list_pages(long_lived_user_token: str, graph_version: str): ...  # returns pages w/ access_token (server-only)
async def debug_token(input_token: str, app_id: str, app_secret: str, graph_version: str): ...
```

### Pattern 3: Pending page selection intermediated by backend without exposing tokens (D-05/D-08)
**What:** Se `/me/accounts` retornar >1 página elegível, o callback armazena **apenas metadados seguros** para confirmação autenticada (ex.: ids/nomes e referência opaca/assinada de curta duração para recuperar tokens server-side, ou registro transitório com expiração). UI recebe apenas `result=select_page` e lista páginas sem tokens; `POST /select-page` autenticado resolve token correspondente no backend, valida e persiste.
**When to use:** Múltiplas páginas retornadas.
**Example (prescritivo):**
```text
Opção recomendada (simples e segura): tabela transitória `social_oauth_pending` (ou equivalente) com
- id/nonce opaco, expires_at curto (ex. 10-15 min), provider='facebook'
- payload cifrado/seguro server-side contendo candidatos {page_id,page_name,page_access_token}
- criada no callback; consumida/invalidada no select/disconnect/expiração; nunca retornada ao frontend
UI lista páginas via GET autenticado que retorna SOMENTE {page_id,page_name} da pendência válida.
```
*Alternativa aceitável por discrição:* token pendente assinado contendo apenas referência/nonce para blob cifrado server-side; **não** embutir page tokens em JWT retornado ao browser.

### Pattern 4: Definitive vs transient verification outcomes (D-09/D-10)
**What:** No callback/confirmação e em "Verificar agora"/carregamento de status (sob demanda), tratar falhas:
- **Definitivas** (`is_valid=false`, token expirado/revogado, permissão ausente/revogada, página inacessível confirmada) → persistir `needs_reconnect`, limpar/invalidar uso conforme política segura e expor alerta resumido.
- **Transitórias** (timeout, rede, 5xx, rate limit temporário) → **não** alterar conexão válida para `needs_reconnect`; retornar erro seguro de verificação e manter último estado válido.
**When to use:** `verify` endpoint e validação no callback.
**Example:**
```python
# [ASSUMED classification logic derived from D-10 + Meta debug_token/error behavior]
def classify_verification_failure(exc_or_response) -> str:
    # returns "definitive" | "transient"
    # definitive: debug_token.is_valid == False, known auth/permission invalidation signals
    # transient: httpx.TimeoutException, connection errors, 5xx, 429
    ...
```

### Pattern 5: Admin UI states driven by safe status payload (D-11/D-14/D-16)
**What:** Página client (`"use client"`) sob `AdminGuard`/layout atual carrega status autenticado (`Authorization: Bearer <sessionStorage token>`), interpreta `status`, `pending_selection`, `page_name/page_id`, datas e `alert`; lê `searchParams` de retorno do callback para banner contextual; ações chamam helpers em `frontend/lib/api.ts` (estilo `ApiError`).
**When to use:** `/admin/integracoes`.
**Example:**
```ts
// Source pattern: [VERIFIED: frontend/lib/api.ts, frontend/components/admin/AdminGuard.tsx, ToastProvider]
export interface MetaIntegrationStatus {
  status: "connected" | "needs_reconnect" | "disconnected";
  provider: "facebook";
  page_id: string | null;
  page_name: string | null;
  connected_at: string | null;
  token_checked_at: string | null;
  pending_selection: boolean;
  alert: { code: string; message: string } | null; // safe summary only
}

// start: open backend start URL via same-tab navigation after authenticated preflight,
// or fetch start endpoint that returns redirect URL (discretion) while keeping start authenticated.
// callback returns redirect to /admin/integracoes?result=connected|error|cancelled|select_page
```

### Anti-Patterns to Avoid
- **Expor tokens/segredos ao frontend:** nunca retornar `access_token`, `META_APP_SECRET`, `SOCIAL_TOKEN_ENCRYPTION_KEY`, nem incluir tokens em query params de redirect de retorno.
- **Confiar no callback sem validar `state`:** callback deve falhar fechado se `state` ausente/inválido/expirado (D-01/D-03/D-04).
- **Salvar page token de `/me/accounts` obtido com user token curto sem exchange long-lived:** reduz durabilidade/consistência; seguir cadeia de long-lived user token antes de obter/persistir token de página. [CITED: Meta long-lived tokens docs]
- **Marcar `needs_reconnect` em timeout/5xx transitório:** viola D-10 e gera ruído operacional.
- **Persistir mais de uma conexão ativa:** sempre substituir/normalizar para 1 registro ativo (D-06) em transação.
- **Implementar polling/jobs periódicos nesta fase:** D-09 exige validação no callback e sob demanda apenas.
- **Criar endpoint público de start/disconnect/verify/select:** start/status/verify/select/disconnect devem exigir `require_admin`; apenas callback é browser redirect sem Bearer porém protegido por `state`.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Criptografia de page token em repouso | Armazenar plaintext, base64, ou cifra própria | `app.services.social.crypto` (Fernet) + `SOCIAL_TOKEN_ENCRYPTION_KEY` | Já implementado, autenticado e com erros seguros (SOC-04/D-04). [VERIFIED] |
| Assinatura/expiração de credenciais temporárias | `base64(json)` ou HMAC ad-hoc frágil | `PyJWT` (ou primitiva criptográfica equivalente já auditada) com `exp` e validação estrita | Evita bypass de anti-CSRF/TTL; alinhado ao padrão JWT do projeto. [VERIFIED pattern] |
| Parsing/validação de config Meta | `os.environ` espalhado | `Settings` (`core/config.py`) | Validação centralizada, defaults e segurança já estabelecidos. [VERIFIED] |
| Cliente HTTP ad-hoc sem timeout/tratamento | `urllib` sem política | `httpx` com timeout explícito e tratamento de erros transitórios/permanentes | Robustez e testabilidade (mock via transport/respx/httpx MockTransport se adotado). [VERIFIED dep] |
| Lógica de conexão social duplicada em rotas/UI | Regras espalhadas em handlers/componentes | Serviço de domínio (`services/social/meta_oauth.py`) + payload de status único | Garante consistência D-06/D-07/D-09/D-10 e reduz vazamento de segredos. |

**Key insight:** OAuth Meta nesta fase é principalmente um problema de **confiança, estado e sigilo** (state, tokens, classificação de falhas), não de UI complexa; centralizar regras no backend e expor contratos seguros simplifica planejamento e evita regressões.

## Runtime State Inventory

> Step 2.5: Não aplicável. Fase 15 é feature greenfield sobre fundação existente (novos endpoints/UI/fluxo); não é rename/refactor/migração de identificadores.

## Common Pitfalls

### Pitfall 1: `state` válido em formato mas contexto incorreto
**What goes wrong:** Callback aceita qualquer token assinado não expirado, mesmo se emitido para outro propósito.
**Why it happens:** Falta de claim de propósito/audiência (ex.: `purpose=meta_oauth`).
**How to avoid:** Incluir e validar claims mínimas (`purpose`, `exp`, nonce/iat) e algoritmo fixo (`HS256`), rejeitando qualquer mismatch.
**Warning signs:** Testes conseguem reutilizar tokens de outros fluxos/contextos.

### Pitfall 2: Page token persistido sem exchange para long-lived user token
**What goes wrong:** Conexão expira cedo ou falha de forma inesperada.
**Why it happens:** Usar user token de curta duração (do `code`) para chamar `/me/accounts` e salvar page token derivado curto.
**How to avoid:** Sempre `fb_exchange_token` antes de `/me/accounts`; validar resultado e timestamps via `/debug_token` quando aplicável. [CITED: Meta long-lived tokens]
**Warning signs:** `needs_reconnect` frequente logo após conectar; `expires_at` curto em debug.

### Pitfall 3: Vazamento de token em logs, redirects ou payloads
**What goes wrong:** `access_token`, `code` sensível em logs detalhados, ou tokens enviados ao browser.
**Why it happens:** Logging de URL completa/respostas Graph, retorno de pendência com tokens, ou query params de retorno ricos.
**How to avoid:** Sanitizar logs (sem query sensível/corpos), usar códigos de resultado genéricos no redirect (`result/error`), payloads de status/pending apenas com metadados seguros (D-03/D-11/META-05).
**Warning signs:** `access_token`, `EAAB`, `client_secret` ou `code=` aparecem em logs/tests snapshots.

### Pitfall 4: Seleção pendente não expira ou não é consumida atomicamente
**What goes wrong:** Confirmação reaproveita estado antigo, seleciona página incorreta, ou deixa tokens temporários órfãos.
**Why it happens:** Store sem TTL/limpeza, sem invalidação após sucesso/cancelamento/substituição.
**How to avoid:** TTL curto + invalidação em `select/disconnect/reconnect`; transação ao persistir conexão ativa única (D-06/D-08).
**Warning signs:** Pendências antigas continuam válidas; múltiplos registros "ativos".

### Pitfall 5: Falha transitória derruba conexão válida
**What goes wrong:** Timeout/5xx em "Verificar agora" marca `needs_reconnect` indevidamente.
**Why it happens:** Classificação única de erro sem distinguir definitivo vs transitório.
**How to avoid:** Implementar política D-10 explicitamente: só falhas definitivas confirmadas alteram para `needs_reconnect`; transitórias retornam erro de verificação seguro e preservam estado.
**Warning signs:** Instabilidade de rede causa perda de conexão.

### Pitfall 6: Callback e rotas com proteção incorreta
**What goes wrong:** `start/verify/disconnect/select` acessíveis sem auth, ou callback exige Bearer e quebra redirect do Meta.
**Why it happens:** Reuso incorreto de `require_admin` em todas as rotas OAuth.
**How to avoid:** `start`, `status`, `verify`, `select`, `disconnect` com `Depends(require_admin)`; `callback` público no nível HTTP mas com validação obrigatória de `state` assinado/TTL e checks server-side (D-04).
**Warning signs:** 401 no callback; ações sensíveis funcionam sem token.

### Pitfall 7: Mismatch de `redirect_uri` ou Graph version/config
**What goes wrong:** Troca de `code` falha (`redirect_uri` deve ser idêntica) ou chamadas vão para versão inconsistente.
**Why it happens:** Montar URL manualmente em múltiplos lugares, divergência entre env e app Meta.
**How to avoid:** Centralizar construção de URLs/paths usando `META_GRAPH_VERSION`, `META_OAUTH_REDIRECT_URI`, `META_APP_ID/SECRET` de `Settings`; validar preenchimento quando fluxo for usado (erro seguro).
**Warning signs:** Erros OAuth apenas em produção; `redirect_uri` diferente entre start/callback exchange.

## Code Examples

Verified patterns from official sources and existing codebase:

### Dialog redirect + state (anti-CSRF)
```text
// Source: [CITED: Meta Manual Login Flow - https://developers.facebook.com/docs/facebook-login/guides/advanced/manual-flow/]
GET https://www.facebook.com/{graph-api-version}/dialog/oauth
  ?client_id={app-id}
  &redirect_uri={redirect-uri}
  &state={state-param}
  &response_type=code
  &scope=pages_show_list,pages_manage_posts,pages_read_engagement
```

### Exchange code -> long-lived user token -> pages
```bash
# Source: [CITED: Meta Long-Lived Tokens - https://developers.facebook.com/documentation/facebook-login/guides/access-tokens/get-long-lived]
# 1) code -> user token
curl -G "https://graph.facebook.com/{v}/oauth/access_token" \
  -d "client_id={app-id}" \
  -d "redirect_uri={redirect-uri}" \
  -d "client_secret={app-secret}" \
  -d "code={code}"

# 2) short-lived user token -> long-lived user token
curl -G "https://graph.facebook.com/{v}/oauth/access_token" \
  -d "grant_type=fb_exchange_token" \
  -d "client_id={app-id}" \
  -d "client_secret={app-secret}" \
  -d "fb_exchange_token={short-lived-user-token}"

# 3) long-lived user token -> pages/page tokens (server-only)
curl -G "https://graph.facebook.com/{v}/me/accounts" \
  -d "fields=id,name,access_token,tasks" \
  -d "access_token={long-lived-user-token}"
```

### Validate token with app access token
```bash
# Source: [CITED: Meta Debug Token - https://developers.facebook.com/docs/graph-api/reference/debug_token/]
curl -G "https://graph.facebook.com/{v}/debug_token" \
  -d "input_token={page-or-user-access-token}" \
  -d "access_token={app-id}|{app-secret}"
# Inspect: data.is_valid, data.expires_at, data.scopes, data.granular_scopes, data.type
```

### Existing backend patterns to follow
```python
# Source: [VERIFIED: backend/app/api/v1/admin.py, backend/app/deps.py]
@router.get("/jobs", dependencies=[Depends(require_admin)]) ...
claims: dict = Depends(require_admin)

# Source: [VERIFIED: backend/app/services/social/crypto.py]
from app.services.social.crypto import encrypt_token, decrypt_token, SocialTokenDecryptError
page_access_token = encrypt_token(plain_page_token, settings.SOCIAL_TOKEN_ENCRYPTION_KEY)

# Source: [VERIFIED: frontend/lib/api.ts]
# - use API base from NEXT_PUBLIC_API_URL, Authorization: Bearer <token>, ApiError/readError
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| `GET /oauth/access_token` com response implícita/fluxos antigos | OAuth com `response_type=code`, `state` anti-CSRF e troca server-side de code/tokens | Consolidado nas práticas atuais do Facebook Login | `state` e server-side exchange são obrigatórios para segurança desta fase. [CITED: Meta manual flow] |
| Persistir user tokens curtos para operações de página | Exchange para long-lived user token e obtenção de page token via `/me/accounts` | Prática atual documentada por Meta | Maior estabilidade; base correta para validação/reconexão. [CITED: Meta long-lived tokens] |
| Assumir conexão válida sem rechecagem explícita | Validar com `/debug_token` e revalidar sob demanda | Prática atual recomendada para debug/validade | Permite detectar revogação/expiração e aplicar `needs_reconnect` com critério. [CITED: debug_token] |

**Deprecated/outdated:**
- **Confiar em versões/scopes hardcoded sem config:** fase exige `META_GRAPH_VERSION` configurável e escopos mínimos definidos (META-02). [VERIFIED: REQUIREMENTS/CONTEXT]
- **Expor tokens em cliente ou logs:** incompatível com SOC-04/META-05 e decisões do projeto. [VERIFIED]

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | `state` pode ser implementado como JWT assinado com `PyJWT` + TTL curto usando segredo server-side (ex.: `JWT_SECRET` ou segredo dedicado), desde que stateless e validado estritamente | Architecture Patterns / Discretion | Baixo; se política de segredo exigir separação, usar chave dedicada em env futura sem mudar contrato |
| A2 | Mecanismo recomendado para pendência de seleção (D-08) é registro transitório server-side com expiração e payload cifrado/sem exposição de tokens, consumido por endpoints autenticados | Architecture Patterns | Médio-baixo; implementação pode optar por store equivalente desde que cumpra segurança/TTL/atomicidade |
| A3 | Validação mínima no callback/verify considera `debug_token.data.is_valid`, escopos necessários presentes, e `expires_at/data_access_expires_at` quando aplicável; falhas definitivas só quando confirmadas | Common Pitfalls / META-04 | Médio; API Meta pode retornar sinais variados — classificador deve ser conservador (transitório quando incerto) conforme D-10 |
| A4 | `start` autenticado pode ser consumido por navegação browser com Bearer via fetch que obtém URL de redirect (ou padrão equivalente) mantendo proteção de início | UI/Backend integration | Médio; detalhes de UX/técnica dependem do client atual, mas proteção e redirect same-tab são obrigatórios |
| A5 | `META_GRAPH_VERSION` default `v21.0` permanece aceitável como configurável; valor exato estável a usar em produção deve ser confirmado no ambiente/app Meta no momento da execução | Standard Stack / State of the Art | Baixo para planejamento; ajustar env sem mudança estrutural |

## Open Questions (RESOLVED)

1. **Armazenamento da pendência de múltiplas páginas (D-08)** — **RESOLVED**
   - Decision: usar **tabela transitória DB dedicada `social_oauth_pending`** (migration/model) com `nonce` opaco, `pages_payload_encrypted`, `expires_at` e `consumed_at`, criada no callback e consumida atomicamente na confirmação/expiração.
   - Rationale: atende D-08 (backend-mediated, sem tokens no frontend), suporta expiração/limpeza e múltiplos workers/restarts melhor que memória; payload sensível (incluindo page tokens candidatos) permanece cifrado server-side. Alinhado aos planos 15-01/15-02.

2. **Forma de acionar `oauth/start` a partir da UI mantendo Bearer** — **RESOLVED**
   - Decision: endpoint `start` autenticado (`require_admin`) retorna **JSON com `redirect_url`** (URL do Meta Dialog montada no backend); o client chama via `fetch` com Bearer e executa navegação na mesma aba com `window.location.assign(redirect_url)`.
   - Rationale: preserva proteção de início autenticado (D-04) e UX de redirect na mesma aba (D-02) sem depender de Bearer em navegação top-level direta. Alinhado aos planos 15-02/15-03.

3. **Comportamento exato quando faltam envs Meta obrigatórios para iniciar OAuth** — **RESOLVED**
   - Decision: `start` (e operações que dependem de config Meta, quando aplicável) realiza checagem explícita de envs obrigatórios (`META_APP_ID`, `META_APP_SECRET`, `META_OAUTH_REDIRECT_URI`, `META_GRAPH_VERSION`) e falha de forma segura com erro operacional genérico pt-BR (ex.: `"Integração com Facebook não configurada"`), sem expor valores/segredos.
   - Rationale: evita vazamento de configuração/segredos (META-05/D-03) e fornece sinalização operacional clara; callback/status continuam retornando apenas códigos/mensagens seguras. Alinhado aos planos 15-01/15-02.

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| Python | Backend runtime/tests | ✓ | 3.13.3 (local) | — [VERIFIED: shell] |
| Node.js / npm | Frontend admin dev/build | ✓ (assumed by repo toolchain) | — | — [ASSUMED] |
| `httpx` | Graph API calls | ✓ | 0.28.1 | — [VERIFIED: pyproject.toml] |
| `PyJWT` | `state` signing/JWT patterns | ✓ | 2.15.1 | — [VERIFIED: pyproject.toml] |
| `cryptography` | Token encryption at rest | ✓ | 50.0.2 | — [VERIFIED: pyproject.toml] |
| Meta App (`META_APP_ID`, `META_APP_SECRET`) + redirect URI configurada | OAuth start/callback/token exchange/debug | ? | — | Mock Graph em testes; fluxo real bloqueado sem credenciais/app setup (fase 18 cobre roteiro manual). [VERIFIED: env/config; META-01..04] |
| Rede/HTTPS acesso ao Graph/Facebook | OAuth e validações sob demanda | ? | — | Tratar falhas transitórias sem degradar conexão válida (D-10); testes automatizados devem mockar. [VERIFIED: D-10] |
| DB migrado/acessível (Neon/Postgres) | Persistir/atualizar `social_accounts` e eventual pendência | ? | — | Gap herdado de reprodutibilidade DB-backed; testes unitários devem mockar camada de persistência quando necessário. [VERIFIED: STATE.md] |

**Missing dependencies with no fallback:**
- Credenciais/configuração real do app Meta e redirect autorizado para validação end-to-end real (substituível por mocks em dev/CI, mas necessário para aceite manual). [VERIFIED]

**Missing dependencies with fallback:**
- DB de teste migrado/reprodutível (herdado): usar testes unitários com mocks de HTTP/DB para cobrir lógica crítica nesta fase. [VERIFIED: STATE.md]

## Validation Architecture

> `workflow.nyquist_validation` está habilitado (`.planning/config.json`: `workflow.nyquist_validation: true`).

### Test Framework
| Property | Value |
|----------|-------|
| Framework | Backend: pytest 9.1.1 + pytest-asyncio (`asyncio_mode=auto`); Frontend: Vitest/Playwright existentes no stack (foco unitário/componente conforme escopo) |
| Config file | `backend/pyproject.toml` (`[tool.pytest.ini_options]`); frontend configs no projeto (se aplicável) |
| Quick run command | `cd backend && pytest -x` (ou alvo focado `tests/test_meta_*` / `tests/test_integrations_*` criado pela fase) |
| Full suite command | `cd backend && pytest` (e suíte frontend relevante se alterada) |

### Phase Requirements → Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| META-01 | `start` autenticado gera `state` assinado/TTL e redirect Meta; `callback` valida `state`, troca code→tokens, resolve páginas e persiste/pendencia com redirects seguros; `disconnect`/`status` expostos | unit/integration (mock Graph + DB/session) | `cd backend && pytest tests/test_meta_oauth_flow.py -x` | ❌ Wave 0 |
| META-02 | Scopes mínimos (`pages_show_list,pages_manage_posts,pages_read_engagement`) e URLs versionadas por `META_GRAPH_VERSION` | unit | `cd backend && pytest tests/test_meta_oauth_flow.py -k scopes -x` | ❌ Wave 0 |
| META-03 | Seleção explícita com múltiplas páginas, auto-conclusão com 1 página, persistência de apenas 1 conexão ativa (substituição) | unit/integration (mock) | `cd backend && pytest tests/test_meta_oauth_flow.py -k selection -x` | ❌ Wave 0 |
| META-04 | Validação via `/debug_token` no callback/confirmação e sob demanda; falha definitiva -> `needs_reconnect`; transitória preserva estado válido | unit (HTTP mocked) | `cd backend && pytest tests/test_meta_oauth_validation.py -x` | ❌ Wave 0 |
| META-05 | Nenhum token/segredo em payloads, redirects de retorno, ou logs de erro; page token armazenado criptografado | unit/security assertions | `cd backend && pytest tests/test_meta_oauth_security.py -x` | ❌ Wave 0 |
| META-06 | UI Integrações renderiza estados/CTAs corretos, confirmação de desconexão, banners por `result`, consumo de payload seguro | frontend component/unit (Vitest) + smoke manual | `cd frontend && npx vitest run app/admin/integracoes` (se criado) | ❌ Wave 0 |

### Sampling Rate
- **Per task commit:** testes focados do arquivo/área alterada (ex.: `pytest tests/test_meta_oauth_*.py -x` e/ou Vitest alvo)
- **Per wave merge:** `cd backend && pytest`; suíte frontend relevante
- **Phase gate:** Full suite verde antes de `/gsd-verify-work` (com lacunas DB/browser registradas se aplicável)

### Wave 0 Gaps
- [ ] `backend/tests/test_meta_oauth_flow.py` — start/callback/state/scopes/single-vs-multi page/redirects seguros
- [ ] `backend/tests/test_meta_oauth_validation.py` — `/debug_token` parsing, definitive vs transient, `needs_reconnect`
- [ ] `backend/tests/test_meta_oauth_security.py` — sanitização de payload/log/redirect e criptografia no persist
- [ ] `backend/tests/test_integrations_api.py` — auth guards (`require_admin`) para status/verify/select/disconnect e contrato de status seguro
- [ ] `frontend/app/admin/integracoes/*` + testes de UI (Vitest/RTL) — estados, CTAs, confirmação, banners (se cobertura automatizada for adotada na fase)
- [ ] Infra de mock HTTP (ex.: `httpx` MockTransport/respx conforme padrão do repo) para Graph API — sem chamadas reais em CI

## Security Domain

### Applicable ASVS Categories

| ASVS Category | Applies | Standard Control |
|---------------|---------|-----------------|
| V2 Authentication | yes | Reusar auth admin existente (JWT/Bearer + `require_admin`) para start/status/verify/select/disconnect; callback protegido por `state` assinado/TTL (D-04). |
| V3 Session Management | partial | Sessão admin já baseada em JWT em `sessionStorage`; não introduzir sessão nova; garantir não vazar credenciais em redirects/UI. |
| V4 Access Control | yes | Endpoints sensíveis restritos ao admin único; uma única conexão ativa; confirmação antes de desconectar. |
| V5 Input Validation | yes | Validar `state`, params de callback (`code/error/state`), seleção de página (id pertencente à pendência válida), e envs/URLs de integração. |
| V6 Cryptography | yes | `cryptography.fernet` para tokens em repouso, assinatura de `state` com segredo server-side e expiração; nunca hand-roll. |

### Known Threat Patterns for {FastAPI + Meta OAuth + Graph API}
| Pattern | STRIDE | Standard Mitigation |
|---------|--------|---------------------|
| CSRF/forgery no callback OAuth | Spoofing / Tampering | `state` assinado/stateless com TTL, claim de propósito e validação estrita antes de qualquer troca/persistência (D-01/D-04). |
| Vazamento de `code`/access token/app secret em logs, URLs ou UI | Information Disclosure | Chamadas Graph server-side, redirects de retorno apenas com códigos seguros, sanitização de logs, payloads sem segredos (D-03/D-11/META-05). |
| Fixação/substituição indevida de conexão (múltiplas páginas/contas) | Tampering / Elevation of privilege (operacional) | Confirmação explícita de página (D-05), pendência intermediada segura (D-08), substituir conexão ativa única atomicamente (D-06). |
| Degradação indevida por falha transitória | Denial of Service (operacional) / Tampering de estado | Classificar definitivo vs transitório; só definitivo marca `needs_reconnect` (D-10). |
| Uso de token inválido/revogado sem detecção | Spoofing / Repudiation operacional | Validar via `/debug_token` no callback/confirmação e sob demanda; registrar `token_checked_at` e alerta seguro (META-04/D-09/D-11). |

## Sources

### Primary (HIGH confidence)
- [VERIFIED: codebase] `.planning/phases/15-oauth-meta-e-integracoes-no-admin/15-CONTEXT.md` — decisões D-01..D-16 e escopo locked/discretion/deferred.
- [VERIFIED: codebase] `.planning/REQUIREMENTS.md`, `.planning/ROADMAP.md` (Phase 15), `.planning/STATE.md`, `.planning/PROJECT.md`, `AGENTS.md` — requisitos META-01..06, critérios de sucesso, constraints e convenções.
- [VERIFIED: codebase] Fase 14: `.planning/phases/14-fundacao-social-dados-e-configuracao/14-CONTEXT.md`, `14-RESEARCH.md`; `backend/app/models/social_account.py`; `backend/app/services/social/{crypto.py,__init__.py,types.py,publisher.py,facebook.py}`; `backend/app/core/config.py`; `backend/.env.example`.
- [VERIFIED: codebase] Backend patterns: `backend/app/api/v1/{router.py,admin.py,auth.py}`, `backend/app/deps.py`, `backend/app/core/security.py`, `backend/app/db/session.py`, `backend/pyproject.toml`.
- [VERIFIED: codebase] Frontend admin patterns: `frontend/app/admin/{layout.tsx,page.tsx,paste/page.tsx}`, `frontend/components/admin/{AdminGuard.tsx,ToastProvider.tsx,LogoutButton.tsx}`, `frontend/lib/{api.ts,auth.ts}`.
- [CITED: Meta docs] Manual Login Flow / `state` anti-CSRF: https://developers.facebook.com/docs/facebook-login/guides/advanced/manual-flow/
- [CITED: Meta docs] Long-lived tokens, `fb_exchange_token`, `/accounts` page tokens: https://developers.facebook.com/documentation/facebook-login/guides/access-tokens/get-long-lived
- [CITED: Meta docs] Debug Token (`/debug_token`, `input_token`, `access_token` app token, fields `is_valid/scopes/granular_scopes/expires_at`): https://developers.facebook.com/docs/graph-api/reference/debug_token/
- [CITED: Meta docs] Permissions reference (inclui `pages_show_list`, `pages_manage_posts`, `pages_read_engagement`): https://developers.facebook.com/docs/permissions/

### Secondary (MEDIUM confidence)
- [CITED: Community/SDK docs corroborating official flow] `social-sdk.dev` Facebook/Page token guides (cadeia login->long-lived->/me/accounts, `debug_token` uso): https://social-sdk.dev/docs/platforms/facebook , https://social-sdk.dev/guides/facebook-page-access-token

### Tertiary (LOW confidence)
- None.

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - versões e padrões verificados no repositório; dependências necessárias já presentes.
- Architecture: HIGH - fundamentada em decisões locked D-01..D-16, fundação da Fase 14 e fluxo OAuth/Graph documentado oficialmente.
- Pitfalls: HIGH - derivados de requisitos de segurança/estado (META-04/05, D-03/D-10) e comportamento conhecido de tokens/redirects Meta.

**Research date:** 2026-11-15
**Valid until:** 2026-12-15 (revalidar `META_GRAPH_VERSION` estável e eventuais mudanças de permissões/comportamento Meta no momento da implementação)