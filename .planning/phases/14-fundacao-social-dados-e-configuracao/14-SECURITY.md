---
phase: 14
slug: fundacao-social-dados-e-configuracao
status: verified
threats_open: 0
asvs_level: 1
created: 2026-11-15
---

# Phase 14 — Security

> Per-phase security contract: threat register, accepted risks, and audit trail.

**Phase:** 14 — fundacao-social-dados-e-configuracao  
**ASVS Level:** 1 (default; audited against Phase 14 PLAN threat register)  
**Status:** verified (all declared threats closed by mitigation evidence or documented accepted risk)  
**Threats Open:** 0

---

## Trust Boundaries

| Boundary | Description | Data Crossing |
|----------|-------------|---------------|
| operator/env → backend config | Variáveis de ambiente/social/Meta entram no processo; valores malformados ou segredos vazados podem comprometer segurança/operação futura | Config, segredos/chaves/tokens (sensível) |
| backend config → logs/responses | Configurações sensíveis não devem atravessar para observabilidade exposta ou APIs/frontend | Segredos, chaves, tokens (não deve vazar) |
| plaintext token → crypto service | Transformação sensível de token; falhas não podem vazar segredo | Token plaintext/ciphertext/chave |
| backend/ORM → database | Modelos e migração definem integridade e onde dados sensíveis (token cifrado) serão persistidos | Metadados sociais, token cifrado, logs de tentativa |
| jobs data → social_posts | Relação entre vaga e post social; deleção de vaga impacta registros dependentes | IDs e integridade referencial |
| backend social services → provedores externos (futuro) | Contrato/stub atual não deve abrir caminho para chamadas não controladas; resultados devem ser seguros | Payloads/resultados de publicação (futuro) |

---

## Threat Register

| Threat ID | Category | Component | Disposition | Mitigation | Status | Evidence |
|-----------|----------|-----------|-------------|------------|--------|----------|
| T-14-01 | Tampering | `backend/app/core/config.py` (`SITE_PUBLIC_URL`, `META_OAUTH_REDIRECT_URI`, retries) | mitigate | Validação http/https e inteiros/CSV > 0 quando preenchidos; falha explícita | closed | `backend/app/core/config.py:87-104,122-146` valida URLs http/https com netloc, `SOCIAL_MAX_ATTEMPTS > 0`, parsing estrito de `SOCIAL_RETRY_DELAYS`; defaults `5` e `300,900,3600,10800,21600`. |
| T-14-02 | Information Disclosure | `backend/app/core/config.py`, `backend/.env.example` (segredos Meta/social/token key) | mitigate | Sem defaults inseguros, sem log/eco de valores, placeholders no `.env.example`, validação Fernet sem expor chave | closed | `backend/app/core/config.py:76-84,111-118` (segredos vazios por padrão, validação Fernet sem ecoar chave); `backend/.env.example:34-48` (SOC-06 pt-BR, placeholders, orientação backend-only). |
| T-14-03 | Denial of Service | config social malformada | accept | Variáveis opcionais por padrão na Fase 14; falhas explícitas apenas quando valores preenchidos/consumidos (risco aceito e documentado) | closed | `backend/app/core/config.py:76-119` (opcional por padrão + validação fail-fast quando fornecido). Risco residual aceito em AR-14-01; reavaliar nas Fases 15–17. |
| T-14-04 | Tampering | `social_posts` idempotência | mitigate | `UniqueConstraint("job_id","provider")`, status/ids explícitos e base para idempotência futura | closed | `backend/app/models/social_post.py:30-37,72-78`; `backend/alembic/versions/0004_social_foundation.py:123-126,168-169` (`uq_social_posts_job_provider`). |
| T-14-05 | Information Disclosure | `social_accounts.page_access_token` | mitigate | Coluna destinada a texto cifrado Fernet; sem plaintext em schema; boundary explícito de crypto | closed | `backend/app/models/social_account.py:29` (`page_access_token` como `Text`); `backend/app/services/social/crypto.py:19-33` (encrypt/decrypt explícitos). |
| T-14-06 | Tampering | integridade referencial social↔jobs | mitigate | FKs com `ON DELETE CASCADE` | closed | `backend/app/models/social_post.py:30-33`, `backend/app/models/social_post_log.py:19-22`, `backend/alembic/versions/0004_social_foundation.py:123,154-156`. |
| T-14-07 | Repudiation | histórico de tentativas sociais | mitigate | `social_post_logs` com tentativa/resultado/erro/resposta resumida e timestamps | closed | `backend/app/models/social_post_log.py:11-42`; `backend/alembic/versions/0004_social_foundation.py:128-175` (tabela, colunas e índices). |
| T-14-08 | Information Disclosure | `backend/app/services/social/crypto.py` | mitigate | Fernet oficial, encrypt/decrypt explícitos, erro de decrypt seguro, sem log/eco de segredos | closed | `backend/app/services/social/crypto.py:3-33` (`validate_fernet_key`, `encrypt_token`, `decrypt_token`, `SocialTokenDecryptError` com mensagem fixa; mapeia `InvalidToken/ValueError/TypeError`). |
| T-14-09 | Spoofing/Tampering (chave inválida) | `crypto.py` / key handling | mitigate | Validação de chave via `Fernet` e tratamento seguro; alinhado à validação em Settings | closed | `backend/app/services/social/crypto.py:10-16`; `backend/app/core/config.py:111-118`. |
| T-14-10 | Elevation of Privilege / Data exfil (futuro) | `FacebookPublisher` stub / contrato | mitigate | Stub sem `httpx`/HTTP/SDK, mensagem segura, contrato/resultados tipados | closed | `backend/app/services/social/facebook.py:1-19` (async stub sem I/O externo, retorno controlado); `backend/app/services/social/types.py`, `publisher.py` (contrato/categorias tipadas). Busca em `backend/app/services/social/`: sem `httpx`/`requests`. |
| T-14-11 | Denial of Service | uso indevido do stub | accept | Stub retorna falha controlada explícita sem I/O externo; impacto operacional real tratado nas fases 15–17 (risco aceito e documentado) | closed | `backend/app/services/social/facebook.py:13-19` (`ok=False`, `category=unknown`, mensagem segura). Risco residual aceito em AR-14-02; reavaliar nas Fases 15–17. |

---

## Accepted Risks Log

| Risk ID | Threat Ref | Rationale | Accepted By | Date | Scope / Reassessment | Compensating Controls |
|---------|------------|-----------|-------------|------|-----------------------|-----------------------|
| AR-14-01 | T-14-03 | Variáveis sociais opcionais na Fase 14; má configuração pode afetar recursos sociais futuros, mas não bloqueia fluxos centrais atuais. Falhas explícitas só ocorrem quando valores são fornecidos/consumidos. | gsd-security-auditor (user-approved flow) | 2026-11-15 | Reavaliar nas Fases 15–17 quando OAuth/publicação/worker consumirem config; exigir runbooks/health checks quando ativos. | Defaults opcionais; validação fail-fast de URLs/inteiros/CSV/chave Fernet quando preenchidos; `.env.example` com placeholders; sem dependência externa social obrigatória no runtime da Fase 14. |
| AR-14-02 | T-14-11 | `FacebookPublisher` é stub intencional sem rede na Fase 14; pode retornar falhas controladas, mas sem chamadas externas/timeouts por este componente. Disponibilidade de provedor, retries/rate-limit reais são fora de escopo até fases de implementação. | gsd-security-auditor (user-approved flow) | 2026-11-15 | Reavaliar na Fase 17 (e pontos de integração 15/16) com retries limitados, timeouts, salvaguardas de worker e monitoramento antes de publicação social em produção. | Retorno tipado e controlado com mensagem segura; sem `httpx`/HTTP/SDK; contrato provider-agnostic preparado para categorização de falhas. |

---

## Unregistered Flags

From SUMMARY `## Threat Flags`:
- 14-01-SUMMARY.md: none reported
- 14-02-SUMMARY.md: none reported
- 14-03-SUMMARY.md: `None - no new network endpoints, auth paths, file access patterns, or trust-boundary schema changes introduced beyond planned internal social service scaffolding.`

**Unregistered flags:** none.

---

## Security Audit Trail

| Audit Date | Threats Total | Closed | Open | Run By |
|------------|---------------|--------|------|--------|
| 2026-11-15 | 11 | 11 | 0 | gsd-security-auditor (subagent ses_e1f0b534bffeLLKRg5BdfeknR2), orchestrated via gsd-secure-phase |

---

## Sign-Off

- [x] All threats have a disposition (mitigate / accept / transfer)
- [x] Accepted risks documented in Accepted Risks Log
- [x] `threats_open: 0` confirmed
- [x] `status: verified` set in frontmatter

**Approval:** verified 2026-11-15
