# Phase 1: Backend Foundation, Data & Admin Auth - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-10-13
**Phase:** 1-Backend Foundation, Data & Admin Auth
**Areas discussed:** Autenticação do master, Schema `jobs` (detalhes), API pública de leitura, Estrutura do repo & dev local

---

## Autenticação do master

### Transporte do JWT
| Option | Description | Selected |
|--------|-------------|----------|
| Bearer JWT em header | SPA guarda em memória/sessionStorage, envia `Authorization: Bearer` | ✓ |
| httpOnly cookie | Cookie Secure/httpOnly, imune a XSS-leak, mas cross-site (Vercel↔Railway) exige CSRF/SameSite | |

**User's choice:** Bearer JWT em header
**Notes:** Front e backend em domínios distintos, cookies cross-site complicam.

### Persistência da sessão
| Option | Description | Selected |
|--------|-------------|----------|
| Token 12h + sessionStorage | Token único 12h, sobrevive a F5 na aba | ✓ |
| Token curto 1h em memória | Re-login frequente | |
| Access + refresh token | Access curto + refresh longo | |

**User's choice:** Token 12h + sessionStorage
**Notes:** Atende "sessão persiste durante o uso" sem refresh token.

### Armazenamento da senha
| Option | Description | Selected |
|--------|-------------|----------|
| Hash da senha no env | `ADMIN_PASSWORD_HASH` (bcrypt/argon2) | ✓ |
| Senha em texto no env | `ADMIN_PASSWORD` claro | |

**User's choice:** Hash da senha no env

### Proteção do login
| Option | Description | Selected |
|--------|-------------|----------|
| Deixar proteção p/ Phase 3 | Sem rate limit/Turnstile agora | ✓ |
| Rate limit básico já agora | slowapi em memória | |

**User's choice:** Deixar proteção p/ Phase 3

---

## Schema `jobs` (detalhes)

### Chave primária
| Option | Description | Selected |
|--------|-------------|----------|
| UUID | `gen_random_uuid()`, não-enumerável | ✓ |
| bigserial | IDs curtos, enumeráveis | |

**User's choice:** UUID

### Representação de city
| Option | Description | Selected |
|--------|-------------|----------|
| varchar + validação no app | Sem rigidez de DB | ✓ |
| Enum no Postgres | Consistência total, churn | |
| varchar + CHECK das 4 cidades | Defesa em profundidade, churn | |

**User's choice:** varchar + validação no app

### salary
| Option | Description | Selected |
|--------|-------------|----------|
| Texto livre (varchar) | Fiel ao pt-BR bagunçado | ✓ |
| Campos numéricos min/max | Exige parsing, habilita filtro (v2) | |

**User's choice:** Texto livre (varchar)

### Infraestrutura de busca na migração
| Option | Description | Selected |
|--------|-------------|----------|
| pg_trgm + unaccent + coluna normalizada | Busca acento-insensível pronta já | ✓ |
| Só pg_trgm agora, unaccent na Phase 4 | Migração extra depois | |
| Adiar índices p/ Phase 4 | Esquema de busca nasce tarde | |

**User's choice:** pg_trgm + unaccent + coluna normalizada

---

## API pública de leitura

### Paginação
| Option | Description | Selected |
|--------|-------------|----------|
| Offset page/limit | Simples, com total count | ✓ |
| Cursor/keyset | Mais escalável, mais código | |

**User's choice:** Offset page/limit

### Payload da lista
| Option | Description | Selected |
|--------|-------------|----------|
| Campos completos menos contato | Modal abre sem 2º request | ✓ |
| Card enxuto + detalhe à parte | Payload menor, request extra | |

**User's choice:** Campos completos menos contato

### Escopo da API na fase
| Option | Description | Selected |
|--------|-------------|----------|
| Só lista+detalhe sem filtros | Respeita fronteira da fase | ✓ |
| Já incluir filtros/busca/ordenação | Antecipa Phase 4 (scope creep) | |

**User's choice:** Só lista+detalhe sem filtros

### Vagas expiradas na leitura
| Option | Description | Selected |
|--------|-------------|----------|
| Filtrar `expires_at > now()` já agora | Board nunca mostra vaga morta | ✓ |
| Confiar só no hard-delete (Phase 6) | Simplifica agora, janela de vaga morta | |

**User's choice:** Filtrar `expires_at > now()` já agora

---

## Estrutura do repo & dev local

### Layout
| Option | Description | Selected |
|--------|-------------|----------|
| Monorepo backend/ + frontend/ | Frontend esqueleto mínimo | ✓ |
| Só backend/ nesta fase | frontend nasce na Phase 4 | |

**User's choice:** Monorepo backend/ + frontend/

### Tooling Python
| Option | Description | Selected |
|--------|-------------|----------|
| uv + pyproject.toml | Rápido, reprodutível, lockfile | ✓ |
| requirements.txt + pip/venv | Clássico, sem lockfile nativo | |

**User's choice:** uv + pyproject.toml

### Banco em dev
| Option | Description | Selected |
|--------|-------------|----------|
| Conectar direto ao Neon | Sem Docker, alinhado ao critério da fase | ✓ |
| Postgres local via Docker Compose | Isola dev, dois ambientes | |

**User's choice:** Conectar direto ao Neon

### Validação da fase
| Option | Description | Selected |
|--------|-------------|----------|
| pytest focado nos critérios (+seed) | Prova login/401/sem contato/published | ✓ |
| Seed + smoke manual | Rápido, critérios verificados à mão | |

**User's choice:** pytest focado nos critérios (+seed)

---

## OpenCode's Discretion

- Estrutura interna em camadas do FastAPI, formato de erro, logging estruturado, shape do `/health`, claims do JWT.
- Estratégia do banco de teste (branch Neon) e ferramentas de teste/CI.

## Deferred Ideas

- Turnstile no login + rate limit — Phase 3 (SECR-02/SECR-03)
- Endpoint de reveal de contato — Phase 3
- Busca/filtro/ordenação (SRCH-01..03) — Phase 4
- UI pública + tema dark — Phase 4
- Hard-delete de expiradas (14 dias) — Phase 6
- Filtro por faixa salarial (FCT-01) — v2 (exigiria salary numérico)
