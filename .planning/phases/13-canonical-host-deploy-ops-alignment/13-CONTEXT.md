# Phase 13: Canonical Host, Deploy & Ops Alignment (BRND-04 closeout) - Context

**Gathered:** 2026-11-15
**Status:** Ready for planning

<domain>
## Phase Boundary

Eliminar o drift de host canônico e de configuração de deploy/operação para que frontend, backend, CORS, documentação e evidência reflitam de forma consistente o contrato pretendido do EmpregaNoix. Esta fase fecha o gap operacional/contratual de **BRND-04** e o resíduo de evidência/alinhamento de **SECR-12** e **LIFE-13** apontados pela auditoria do milestone.

**Em escopo:** definir e alinhar os hosts canônicos de marca; atualizar artefatos de configuração/docs/scripts no repositório para refletir o estado-alvo canônico; mapear hosts legados/históricos sem reescrever evidências passadas; produzir matriz/registro de evidência de alinhamento (com mapeamento para evidências existentes quando execução real não ocorrer nos canônicos); atualizar `REQUIREMENTS.md` e notas/status do roadmap para refletir fechamento com ownership/caveats explícitos.

**Fora de escopo:** novas funcionalidades de produto, mudanças de comportamento de runtime no app, compra/configuração de domínio próprio, reabertura do contrato T-06-01 (`/admin/expire` apenas `X-Cron-Secret`), fechamento de gaps de fases não relacionadas (ex.: Phase 11), e execução de deploy real como requisito implícito quando houver bloqueio externo (a execução pode permanecer como handoff operacional documentado conforme decisões desta fase).

</domain>

<decisions>
## Implementation Decisions

### Hosts canônicos e mapeamento
- **D-01:** Adotar os nomes de marca como **hosts canônicos oficiais** de produção: frontend `https://empreganoix.vercel.app` e backend `https://empreganoix.onrender.com`. Roadmap/requisitos/docs/config-alvo devem refletir esses hosts como canônicos.
- **D-02:** Hosts/domínios já registrados em evidências ou usados anteriormente (ex.: `https://nao-quero-usar.vercel.app`, `https://naoquerousar.onrender.com`, `https://empreganoix-six.vercel.app`, `https://nqu-backend-x60n.onrender.com`) devem ser tratados como **legados/históricos e não canônicos**, com mapeamento explícito preservando a fidelidade das evidências existentes.
- **D-03:** Cobertura operacional **completa** no alinhamento: além de CORS, explicitar/alinhar `CORS_ORIGINS`, `BACKEND_API_URL`/`NEXT_PUBLIC_API_URL`, Turnstile Hostnames do domínio canônico, e exemplos/runbook/scripts de smoke para os hosts de marca.
- **D-04:** **BRND-04 pode ser fechado por alinhamento contratual + evidência documentada** quando os serviços não estiverem efetivamente publicados nos hosts canônicos no momento da execução. Config/docs/runbook/alvos canônicos devem ficar consistentes e o estado atual/legado mapeado com evidência; deploy/smoke real nos hosts canônicos, se ausente, fica como passo operacional externo registrado (não bloquear o fechamento contratual desta fase).

### Escopo da configuração/alinhamento
- **D-05:** Escopo de artefatos no repositório: **docs + deploy config + scripts de verificação**. Atualizar (no mínimo, conforme aplicável) `docs/DEPLOY.md`, `render.yaml`, `frontend/vercel.json`, `frontend/.env.example` e exemplos/comandos em `scripts/verify-deploy.ps1` para refletir hosts canônicos e mapeamento legado.
- **D-06:** **Evitar mudanças de runtime** em backend/frontend; foco em configuração declarativa, documentação, exemplos e scripts. Se surgir necessidade real de alteração de código de runtime, tratar como desvio explícito e mínimo, mantendo-se dentro da fronteira da fase (sem novas features).
- **D-07:** Política de valores de produção **estrita e de origem única** no estado-alvo: `CORS_ORIGINS` contendo apenas `https://empreganoix.vercel.app` (sem barra final, sem wildcard), e `NEXT_PUBLIC_API_URL`/`BACKEND_API_URL` apontando para `https://empreganoix.onrender.com`. Hosts legados não devem compor o estado-alvo de CORS/URLs.
- **D-08:** Ao alinhar documentos, **normalizar o estado-alvo e exemplos operacionais para os hosts canônicos, preservando o histórico**. Não reescrever linhas/tabelas de evidência histórica para "parecer canônico"; adicionar notas/mapeamento canônico onde necessário para interpretar registros legados.

### Evidência e critérios de fechamento
- **D-09:** Registrar evidência como **matriz de alinhamento + evidência histórica mapeada** (não exigir nova execução de `verify-deploy.ps1` nos canônicos se eles não estiverem provisionados/publicados). Cada item deve indicar status como verificado em host legado, alinhado contratualmente ao canônico, ou pendente de execução operacional, com referências às evidências existentes (ex.: registros em `docs/DEPLOY.md`).
- **D-10:** A matriz deve cobrir o **conjunto completo do roadmap**: `GET /api/v1/health` (status/env/Turnstile), preflight CORS da origem canônica, endpoint de cron `/admin/expire` (rejeição sem/errada credencial conforme fail-closed + idempotência com `X-Cron-Secret` correto), e superfícies públicas/admin chave relevantes (board, páginas legais, login/admin) com status/mapeamento.
- **D-11:** Fonte principal de registro: **`docs/DEPLOY.md` + notas em `REQUIREMENTS.md` e roadmap**. Incluir em `docs/DEPLOY.md` seção/matriz de alvo canônico, mapeamento de hosts legados e status dos checks; refletir fechamento/caveats e ownership em `.planning/REQUIREMENTS.md` e atualizar status/notas da Phase 13 em `.planning/ROADMAP.md` conforme o critério 4.
- **D-12:** **SECR-12 e LIFE-13** devem ser marcados como **fechados com nota de escopo ops** nesta fase: o lado de código/contrato foi verificado em fases anteriores e o resíduo de alinhamento canônico/evidência operacional é coberto/mapeado agora. Se a execução real em hosts canônicos estiver ausente, registrar como handoff operacional explícito na nota/evidência (sem reabrir T-06-01).

### Rollout, dependências e risco operacional
- **D-13:** Recomendar **sequência operacional completa e segura** para aplicação futura: (1) alinhar/provisionar hosts canônicos nos provedores, (2) configurar envs/CORS/Turnstile Hostnames/segredos de cron, (3) rebuild/redeploy do frontend (variáveis `NEXT_PUBLIC_*` são inlinadas no build), (4) validar health/CORS/cron/superfícies com `scripts/verify-deploy.ps1` (ou equivalente), (5) registrar evidência — com rollback por reversão de env/config/domínio.
- **D-14:** Se o nome exato do host canônico não puder ser provisionado, **manter o alvo canônico e registrar bloqueio**: preservar `empreganoix.vercel.app` / `empreganoix.onrender.com` como alvo contratual nos artefatos; documentar o host realmente obtido como desvio/bloqueio com mapeamento explícito, sem trocar silenciosamente o canônico.
- **D-15:** Documentar **postura completa de risco operacional**: execução real pode permanecer pendente (projeto mantido em desenvolvimento/local), `NEXT_PUBLIC_*` exige rebuild, Turnstile Hostnames e CORS devem coincidir com a origem real, cron/scheduler dependem de envs/segredos corretos, cold-start/scheduler split permanecem considerações operacionais conhecidas, e rollback ocorre por reversão de env/config/domínio.
- **D-16:** Atualizar **checkboxes para concluído + notas de evidência/ownership** em `REQUIREMENTS.md` para **BRND-04, SECR-12 e LIFE-13**, apontando para a matriz/evidência de Phase 13 e preservando o histórico de verificações anteriores (código/contrato). Atualizar também o status/notas da Phase 13 em `ROADMAP.md`.

### OpenCode's Discretion
- Formato exato da matriz/tabela em `docs/DEPLOY.md`, nomes das seções e nível de detalhe textual, desde que cubra os checks de D-10 e o mapeamento canônico↔legado.
- Seleção precisa de arquivos de exemplo/env a ajustar dentro do escopo de D-05 (ex.: `.env.example`, `.env.local.example`, notas em `README` se estritamente necessárias para consistência operacional), sem introduzir segredos.
- Estratégia de edição para scripts de verificação (parâmetros/exemplos/defaults documentais) que preserve utilidade para hosts legados históricos quando apropriado, sem conflitar com o alvo canônico.
- Redação final das notas de caveat/handoff em `REQUIREMENTS.md`, `ROADMAP.md` e `docs/DEPLOY.md`, desde que preserve D-04, D-08, D-12, D-14 e D-15.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Escopo, auditoria e requisitos (ownership desta fase)
- `.planning/ROADMAP.md` §"Phase 13: Canonical Host, Deploy & Ops Alignment (BRND-04 closeout)" — goal, dependências, requisitos (`BRND-04`, `SECR-12`, `LIFE-13`), success criteria e status/progresso a atualizar.
- `.planning/REQUIREMENTS.md` — definições e estado atual de `BRND-04` (gap closure Phase 13), `SECR-12` e `LIFE-13` (split ownership: código/contrato reconciliado antes; resíduo de host/deploy/evidência nesta fase), além do resumo de gap closure.
- `.planning/v1.1-MILESTONE-AUDIT.md` — gaps autoritativos: mismatch de hosts canônicos vs registrados (`empreganoix.vercel.app`/`empreganoix.onrender.com` vs hosts efetivos), risco de alinhamento env/CORS/API e caveats de fluxo lifecycle/ops.
- `.planning/PROJECT.md` — constraints fixas (Next.js/FastAPI/Neon/Groq/Turnstile, deploy Vercel+Render, pt-BR, dark mode, admin único, operação em desenvolvimento/local conforme decisões registradas).
- `.planning/STATE.md` — contexto acumulado: deploy local/dev mantido, evidências de smoke registradas em hosts não canônicos, decisões de hardening (T-06-01, cron secret, `NEXT_PUBLIC_*` inlined no build, `verify-deploy.ps1`).

### Evidência e runbook operacional
- `docs/DEPLOY.md` — runbook de produção, arquitetura, CORS, cron de catch-up, cold-start, gate `scripts/verify-deploy.ps1`, rollback e **Registro de verificação** (inclui falha 2026-11-12 e aprovação 2026-11-15 em hosts legados/não canônicos); fonte principal para matriz de alinhamento canônico e mapeamento histórico (D-08, D-09, D-11).
- `scripts/verify-deploy.ps1` — checks e parâmetros de smoke (health/env/Turnstile, CORS allow/deny, board/legal/API, cron 401/403/503 e idempotência, leak, cold-start); exemplos/alvos devem refletir canônico sem perder utilidade documental.
- `render.yaml` — blueprint Render (serviço, região, comandos, env vars declaradas, `autoDeploy: false`, `healthCheckPath`) a alinhar ao estado-alvo canônico quando aplicável.
- `.github/workflows/expire-cron.yml` (se presente) — referência operacional do catch-up por `X-Cron-Secret` (não alterar contrato; manter coerência com docs).

### Frontend (configuração de host/API e deploy)
- `frontend/lib/api.ts` — resolução de `NEXT_PUBLIC_API_URL` (build-time) e cliente de chamadas admin/públicas; mudanças de runtime evitadas (D-06), mas exemplos/env guidance devem ser canônicos.
- `frontend/lib/jobs.ts` — fetch server-side do board usando `BACKEND_API_URL`/`NEXT_PUBLIC_API_URL` com timeout/caching; relevante para implicações de alinhamento de URL em docs/runbook.
- `frontend/vercel.json` — config Vercel versionada.
- `frontend/.env.example` — valores/exemplos de `NEXT_PUBLIC_API_URL`, `BACKEND_API_URL`, `NEXT_PUBLIC_TURNSTILE_SITE_KEY` a normalizar para o alvo canônico.
- `frontend/.env.local.example` (se existir) — exemplo local; alinhar apenas se necessário para consistência sem expor segredos.
- `frontend/next.config.mjs` — configuração Next (revisar apenas se necessário para consistência documental/config; sem mudanças de runtime desnecessárias).

### Backend (CORS/ops) e contexto de fases anteriores
- `backend/app/main.py` — CORS middleware e carregamento de `settings.cors_origins_list`; contrato de CORS/headers expostos é referência para docs/alinhamento (sem reabrir comportamento).
- `backend/app/core/config.py` — validação/settings de `CORS_ORIGINS`, Turnstile e env; referência para política estrita documentada.
- `.planning/phases/10-rebranding-launch-preparation-empreganoix/10-CONTEXT.md`, `10-03-SUMMARY.md`, `10-04-SUMMARY.md`, `10-VERIFICATION.md` — contexto de rebrand/deploy e evidência aprovada em hosts registrados (caveat de canonicalização).
- `.planning/phases/09-lifecycle-trust-legal-launch-completeness/09-VERIFICATION.md` — evidência/contrato de lifecycle/cron (`X-Cron-Secret`-only, T-06-01) cujo resíduo ops é tratado aqui.
- `.planning/phases/12-reconcile-phase-9-lifecycle-trust-verification-contracts/12-CONTEXT.md` — padrão de reconciliação, split ownership e notas de caveat/handoff.

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `docs/DEPLOY.md` já contém runbook completo, tabela de **Registro de verificação** e seções de CORS/cron/cold-start/rollback — base natural para inserir matriz canônico↔legado e notas de alinhamento preservando histórico.
- `scripts/verify-deploy.ps1` implementa o gate de checks exigidos pelo roadmap (health/env/Turnstile, CORS allow/deny, cron fail-closed/idempotente, superfícies, leak/cold-start) e pode ser referenciado como evidência/procedimento.
- `render.yaml` e `frontend/vercel.json`/env examples concentram a configuração versionada de deploy e URLs públicas.

### Established Patterns
- Frontend lê `NEXT_PUBLIC_API_URL` no build e `BACKEND_API_URL` no server-side (`frontend/lib/api.ts`, `frontend/lib/jobs.ts`); mudanças de host exigem atualização de env + rebuild/redeploy (decisão já conhecida no projeto).
- Backend aplica CORS a partir de `settings.cors_origins_list` com `allow_credentials=False` e expõe `Retry-After` (`backend/app/main.py`).
- Verificação/fechamento em fases anteriores usa notas de caveat, split ownership e referências explícitas a evidências (padrão de Phase 11/12/09-10).

### Integration Points
- `docs/DEPLOY.md` — matriz de alinhamento canônico, mapeamento de hosts legados e interpretação das evidências históricas.
- `render.yaml`, `frontend/vercel.json`, `frontend/.env.example`, `scripts/verify-deploy.ps1` — estado-alvo canônico de hosts/URLs/CORS/exemplos.
- `.planning/REQUIREMENTS.md` e `.planning/ROADMAP.md` — fechamento de BRND-04 e resíduo ops de SECR-12/LIFE-13 com notas de evidência/ownership.

</code_context>

<specifics>
## Specific Ideas

- Canônico de marca é o alvo contratual mesmo se a infraestrutura real ainda estiver em hosts legados/sufixados; desvios de provisionamento devem ser registrados, não normalizados silenciosamente.
- Evidência histórica (ex.: smoke gate aprovado em 2026-11-15 contra `https://empreganoix-six.vercel.app` + `https://nqu-backend-x60n.onrender.com`) deve ser preservada e reinterpretada via mapeamento para o alvo canônico.
- O projeto pode permanecer em desenvolvimento/local nesta fase; o fechamento aceito é contratual/documental com handoff operacional explícito quando não houver execução real nos canônicos.

</specifics>

<deferred>
## Deferred Ideas

- Provisionamento/execução real de deploy, rebuild e smoke gate nos hosts canônicos `empreganoix.vercel.app` / `empreganoix.onrender.com` (handoff operacional; bloqueios de conta/provedor/nomes indisponíveis documentados).
- Compra/configuração de domínio próprio e redirects/aliases de produção — fora desta fase.
- Renomeação de identificadores internos legados não voltados ao usuário (ex.: nome do serviço Render `nqu-backend`, chaves de storage) — não exigida para fechamento de BRND-04/SECR-12/LIFE-13.
- Revalidação Nyquist ou novas validações automatizadas além do escopo de alinhamento/evidência desta fase.

### Reviewed Todos (not folded)
Nenhum todo pendente/revisado para esta fase.

</deferred>

---

*Phase: 13-canonical-host-deploy-ops-alignment*
*Context gathered: 2026-11-15*
