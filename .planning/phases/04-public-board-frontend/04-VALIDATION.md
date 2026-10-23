---
phase: 4
slug: public-board-frontend
status: approved
nyquist_compliant: true
wave_0_complete: false
created: 2026-10-22
updated: 2026-10-23
---

# Phase 4 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.
> Task IDs below match the final plans (`04-01`…`04-06`), validated in
> `04-PLAN-CHECK.md` loop 3 (PASS WITH CONCERNS).

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework (backend)** | pytest 9.1.1 + pytest-asyncio (`asyncio_mode = "auto"`), 178 tests collected |
| **Config file (backend)** | `backend/pyproject.toml` (`[tool.pytest.ini_options]`, `testpaths = ["tests"]`) |
| **Framework (frontend)** | nenhum — `next build` + `next lint` + `npx tsc --noEmit` + asserções HTTP |
| **Config file (frontend)** | `frontend/.eslintrc.json`, `frontend/tsconfig.json` |
| **Quick run command** | `Push-Location backend; .\.venv\Scripts\python.exe -m pytest -q; Pop-Location` |
| **Full suite command** | backend acima + `Push-Location frontend; npm run build; npm run lint; npx --no-install tsc --noEmit; Pop-Location` |
| **Estimated runtime** | ~200 s (backend, Postgres real) + ~60 s (build) |

> **Windows/PowerShell 5.1:** não existe `uv`; o interpretador é `backend\.venv\Scripts\python.exe` (3.11.17). Não há `.venv` na raiz. Nunca usar `&&` — encadear com `;`. `npm` **só** roda com cwd = `frontend\`.
> `pytest-timeout` não está instalado → nunca passar `--timeout`.

---

## Sampling Rate

- **After every task commit:** backend `pytest -q` + `npm run lint` (em `frontend\`)
- **After every plan wave:** suite backend + `npm run build` (a rota `/` deve sair como `ƒ (Dynamic)`)
- **Before `/gsd-verify-work`:** suite verde, build verde com `/` dinâmica, board verificado no browser com seed (30 vagas)
- **Max feedback latency:** 260 segundos

---

## Per-task Verification Map

| task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| 04-01-01 | 01 | 1 | UIUX-01 | — | Tailwind v4 instalado **localmente** (sem herdar `tailwindcss@3` de `C:\Users\AndreC`) | build | `Push-Location frontend; Test-Path node_modules\tailwindcss\package.json; node -e "console.log(require('./node_modules/tailwindcss/package.json').version)"; Pop-Location` | ❌ W0 | ⬜ pending |
| 04-01-02 | 01 | 1 | UIUX-01 | — | Preflight não vaza no admin; tokens do UI-SPEC no `@theme` | build+lint | `npm run build`; `npm run lint` (cwd `frontend`) | ❌ W0 | ⬜ pending |
| 04-01-03 | 01 | 1 | UIUX-02 | — | `/doacoes` responde 200 com título | smoke | `Invoke-WebRequest http://localhost:3000/doacoes -UseBasicParsing` | ❌ W0 | ⬜ pending |
| 04-02-01 | 02 | 1 | SRCH-01 | T-04-SQLI | Migration `0003` inclui `requirements`; backfill; `updated_at` preservado e trigger reabilitado | integration | `pytest tests/test_public_search.py -k search_text` | ❌ W0 | ⬜ pending |
| 04-02-02 | 02 | 1 | SRCH-01..03 | T-04-SQLI, T-04-LIKE | `q` acento/caixa-insensível; curingas escapados; `city` slug+canonical, desconhecida ignorada; `sort` whitelist + tiebreak `id`; `total` consistente | integration | `pytest tests/test_public_search.py -q` | ❌ W0 | ⬜ pending |
| 04-02-03 | 02 | 1 | PUBL-02 | — | Seed dev-only com guarda de ambiente; default 30 (cap 60) para haver página 2; não escreve `search_text` | integration | `seed_public_demo.py --count 30` + `SELECT count(*)` | ❌ W0 | ⬜ pending |
| 04-03-01 | 03 | 2 | PUBL-01 | T-04-XSS | Contratos + fetch `no-store` + `lib/filters.ts` preserva `vaga` cru | build | `npm run build` | ❌ W0 | ⬜ pending |
| 04-03-02 | 03 | 2 | PUBL-01, PUBL-02 | T-04-XSS | SSR com títulos seedados; `/` é `ƒ (Dynamic)`; paginação real | build+smoke | `npm run build` (tabela de rotas) + `Invoke-WebRequest /` contém título | ❌ W0 | ⬜ pending |
| 04-03-03 | 03 | 2 | PUBL-03 | — | `<dialog>` nativo abre pelo card; foco/ESC/backdrop | UAT | manual (browser) | ❌ manual | ⬜ pending |
| 04-04-01 | 04 | 3 | PUBL-04 | T-04-LEAK | Cache por vaga em escopo de aba; CORS expõe `Retry-After` **em GET real** | integration | `pytest tests/test_public_api.py -k expose` | ❌ W0 | ⬜ pending |
| 04-04-02 | 04 | 3 | PUBL-04 | T-04-LEAK | Contato nunca no HTML/JSON antes do reveal; 7 estados | UAT+lint | `npm run lint` + UAT | ❌ manual | ⬜ pending |
| 04-04-03 | 04 | 3 | PUBL-03, PUBL-06 | T-04-REDIR | `?vaga=` válido fora do filtro resolve via `GET /jobs/{id}`; malformado renderiza painel no SSR sem chamar a API | smoke | `Invoke-WebRequest '/?vaga=not-a-uuid'` contém `Vaga não encontrada` | ❌ W0 | ⬜ pending |
| 04-05-01 | 05 | 4 | SRCH-01, SRCH-03 | T-04-SQLI | Toolbar debounce 300ms, chips, sort; `router.replace` sem poluir histórico | lint | `npm run lint` | ❌ W0 | ⬜ pending |
| 04-05-02 | 05 | 4 | SRCH-01..03, PUBL-01 | — | URL state ↔ API; painel "não encontrada" preservado; `jobs` (não `items`) | smoke | `Invoke-WebRequest '/?q=analista&city=sao-paulo'` | ❌ W0 | ⬜ pending |
| 04-06-01 | 06 | 5 | UIUX-03 | — | 3 slots de ADS com altura fixa, sem scripts/tracking | smoke | `Invoke-WebRequest /` → 3× `Espaço publicitário` | ❌ W0 | ⬜ pending |
| 04-06-02 | 06 | 5 | UIUX-01, PUBL-02, PUBL-03 | T-04-LEAK | `verify-ssr.ps1` (UTF-8 **com BOM**) cobre isolamento do admin, `limit=50`/`51→422`, `antigas` crescente, deep links, `Página N de` | build+script | `Push-Location frontend; npx tsc --noEmit; powershell -File scripts/verify-ssr.ps1; Pop-Location` | ❌ W0 | ⬜ pending |
| 04-06-03 | 06 | 5 | UIUX-01..03 | — | Contraste AA, hover Doações, mobile 375px, modal a11y | UAT | manual (checkpoint bloqueante, passos 1–15) | ❌ manual | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `backend/tests/test_public_search.py` — SRCH-01/02/03 + tie-break + escape de curinga + `total` + migration/`updated_at`
- [ ] `frontend/scripts/verify-ssr.ps1` — **UTF-8 com BOM**; gate executável do board
- [ ] Tailwind: `Push-Location frontend; npm install -D tailwindcss@4.3.3 @tailwindcss/postcss@4.3.3; Pop-Location` + `postcss.config.mjs`
- [ ] `backend/scripts/seed_public_demo.py` — entregável de produto (D-02), default 30, guarda `ENV`
- [ ] Migration `0003` — trigger com `requirements` + backfill + reabilitação de `jobs_updated_at`

*Gap aceito:* nenhum runner de teste no frontend (D-12a). Coberto por build + lint + `tsc --noEmit` + asserções HTTP + UAT.

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Reveal (idle → verifying → revealed / 403 / 429 / 404) | PUBL-04 | iframe do Turnstile não é dirigível sem runner headless | Abrir vaga → "Mostrar contato"; repetir com token inválido |
| Candidatura WhatsApp/e-mail | PUBL-06 | depende do app externo | Após revelar, conferir `wa.me` só com dígitos e `mailto:` igual ao e-mail |
| Contraste AA / tema | UIUX-01 | percepção visual | 6 pares do UI-SPEC: `#e2e8f0`, `#b8a9cc`, `#a78bfa`, `#facc15`, branco sobre `#7c3aed` ≥4.5:1; borda `#6d5a91` ≥3:1 |
| Hover Doações | UIUX-02 | estado transitório | amarelo só no hover; sem brilho/pulso em idle |
| Modal a11y + mobile | PUBL-03 | foco/viewport reais | TAB dentro, ESC fecha, foco volta ao card; 375px bottom sheet, X 44px |

---

## Validation Sign-Off

- [x] All tasks have `<automated>` verify or Wave 0 dependencies
- [x] Sampling continuity: no 3 consecutive tasks without automated verify
- [x] Wave 0 covers all MISSING references
- [x] No watch-mode flags
- [x] Feedback latency < 260s
- [x] `nyquist_compliant: true` set in frontmatter

**Approval:** approved 2026-10-23 (plan-check loop 3)
