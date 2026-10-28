# Phase 6: Lifecycle, Trust, Legal & Launch - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents. Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-10-27
**Phase:** 6-lifecycle-trust-legal-launch
**Areas discussed:** Agendamento do hard delete; Expirar vagas pending; Badge e report; Paginas legais / LGPD

---

## Agendamento do hard delete (LIFE-02/LIFE-04)

| Option | Description | Selected |
|--------|-------------|----------|
| APScheduler no processo do backend | BackgroundScheduler no FastAPI. Simples, mas reiniciar perde o agendamento. | OK |
| Endpoint protegido por CRON_SECRET + cron externo | Endpoint + scheduler externo (Railway/Render). Catch-up via infra externa. | OK |
| Ambos (agendado + endpoint) | Job no processo + endpoint CRON_SECRET para catch-up/manual. | OK |

**User's choice:** APScheduler no processo do backend

**Notes:** Combinado com sweep diario as 03:00 UTC + endpoint protegido por CRON_SECRET para trigger manual/catch-up (LIFE-04).

### Follow-up: combinacao agendamento/catch-up

| Option | Description | Selected |
|--------|-------------|----------|
| Diario 03:00 UTC + endpoint CRON_SECRET | Sweep diario fixo no APScheduler + endpoint CRON_SECRET para catch-up/manual. Robusto a reinicios. | OK |
| A cada hora + endpoint CRON_SECRET | Sweep a cada hora + endpoint. Mais responsivo, custo de query maior. | OK |
| No boot do container + endpoint CRON_SECRET | Sweep no startup + endpoint. Zero agendador externo. | OK |

**User's choice:** Diario 03:00 UTC + endpoint CRON_SECRET

---

## Expirar vagas pending (LIFE-01/LIFE-03/LIFE-02)

| Option | Description | Selected |
|--------|-------------|----------|
| Mesma regra: expires_at = criacao + 14d | Qualquer job (pending ou published) nasce com expires_at = created_at + 14d; pending nao revisado simplesmente 'expira'. | OK |
| SLA proprio de revisao | Expira pending por SLA de revisao, independente do clock de 14 dias. | OK |
| Pendentes nao expiram | Só published expiram e sao hard-deleted. | OK |

**User's choice:** Mesma regra: expires_at = criacao + 14d

| Option | Description | Selected |
|--------|-------------|----------|
| Tudo expirado: published + pending | Hard delete cobre publicadas e pending expiradas (hard delete total das expiradas). | OK |
| So published (pending expirado fica registro morto) | Hard delete so de published; pending expirado permanece. | OK |
| So published, pending vira needs_review/invalid | Not revisado apos expiracao -> invalid; mantem rastro. | OK |

**User's choice:** Tudo expirado: published + pending

---

## Badge e report (TRST-01/TRST-02)

### Badge "Vaga revisada" (TRST-01)

| Option | Description | Selected |
|--------|-------------|----------|
| Automatico por status | Badge deriva do status published (unico path que passa por aprovacao manual). Sem campo extra no Job. | OK |
| Campo revisado_em no Job | Exigir/marker campo reviewed_at/reviewed_by no Job na aprovacao. Mais auditavel, duplica info do status. | OK |

**User's choice:** Automatico por status

### Report de visitante (TRST-02)

| Option | Description | Selected |
|--------|-------------|----------|
| Endpoint + tabela reports | POST /public/jobs/{id}/report com job_id + motivo; persistencia em tabela reports. Rastreio consultavel pelo master. | OK |
| Endpoint + log estruturado | Endpoint grava log estruturado no backend sem tabela nova. Sem persistencia consultavel; suficiente para MVP. | OK |
| Report anonimo sem follow-up | Endpoint registra log do report anonimo; sem follow-up automatico. | OK |

**User's choice:** Endpoint + log estruturado

---

## Paginas legais / LGPD (TRST-03)

| Option | Description | Selected |
|--------|-------------|----------|
| Paginas separadas por rota | Rotas publicas dedicadas: /privacidade, /termos, /lgpd. | OK |
| Pagina unica com secoes | Uma pagina com secoes (privacidade, termos, aviso LGPD). | OK |
| Paginas estaticas server-rendered | Paginas simples estaticas sem API, reutilizando padrao publico. | OK |

**User's choice:** Pagina unica com secoes

---

## OpenCode's Discretion

- Mecanica exata da rota do endpoint `CRON_SECRET` e nome do secret (`CRON_SECRET`) no Settings.
- Copy/texto das paginas legais (redacao juridica pendente — task humana, fora de codigo).
- Estrategia de retry/fallback do hard delete (falha transiente).

## Deferred Ideas

- Deploy real (Vercel + Railway/Render): CORS travado, segredos, cold-start (sucesso 5 de SC).
- Chaves Cloudflare reais + wiring de deploy.
- PIX real / doacoes; AdSense / consentimento LGPD; limiter distribuido; SEO avancado; alerts/retention (v2).
- Revisao juridica (advogado brasileiro) antes do lancamento — task humana.
- `/gsd-research-phase` para scheduler externo, Neon CU-hour, free-tiers Render/Railway.

## Deferred (fora do escopo da fase)

- Nenhum item fora do dominio capturado durante esta discussao.

---

*Phase: 6-lifecycle-trust-legal-launch*
*Discussion log: 2026-10-27*
