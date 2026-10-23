---
phase: 4
slug: public-board-frontend
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-10-22
---

# Phase 4 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework (backend)** | pytest 9.1.1 + pytest-asyncio 1.x (`asyncio_mode = "auto"`) |
| **Config file (backend)** | `backend/pyproject.toml` (`[tool.pytest.ini_options]`, `testpaths = ["tests"]`) |
| **Framework (frontend)** | nenhum — `next build` + `next lint` + asserções HTTP |
| **Config file (frontend)** | `frontend/.eslintrc.json`, `frontend/tsconfig.json` |
| **Quick run command** | `.\.venv\Scripts\python.exe -m pytest -q` (em `backend/`) |
| **Full suite command** | `backend/`: `.\.venv\Scripts\python.exe -m pytest -q`; `frontend/`: `npm run build` e `npm run lint` |
| **Estimated runtime** | ~200 s (backend, contra Postgres real) + ~60 s (build) |

> **Windows/PowerShell:** não há `uv` instalado; o interpretador do venv é `.\.venv\Scripts\python.exe`. Nunca usar `&&` — encadear com `;`.

---

## Sampling Rate

- **After every task commit:** `.\.venv\Scripts\python.exe -m pytest -q` (backend) e `npm run lint` (frontend)
- **After every plan wave:** suite backend + `npm run build` (a rota `/` deve aparecer como `ƒ (Dynamic)`)
- **Before `/gsd-verify-work`:** suite backend verde, build verde com `/` dinâmica, board verificado no browser com seed
- **Max feedback latency:** 260 segundos

---

## Per-task Verification Map

| task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| 04-01-01 | 01 | 1 | UIUX-01 | — | Preflight não vaza no `/admin/*`; tokens do UI-SPEC aplicados | build+lint | `npm run build`; `npm run lint` | ❌ W0 (Tailwind) | ⬜ pending |
| 04-02-01 | 02 | 2 | PUBL-01, PUBL-02 | T-04-XSS | Card renderiza campos de `JobPublic`; nada de `dangerouslySetInnerHTML` | smoke | `Invoke-WebRequest http://localhost:3000/` → contém título seedado + "Ver a vaga" | ❌ W0 | ⬜ pending |
| 04-02-02 | 02 | 2 | PUBL-01 | — | `/` é dinâmica (`ƒ`), não estática | build | `npm run build` → tabela de rotas mostra `ƒ /` | ✅ comando existe | ⬜ pending |
| 04-03-01 | 03 | 3 | PUBL-03, PUBL-04 | T-04-LEAK | Contato ausente do HTML até o reveal; 403/404/429 tratados | manual | UAT no browser (Turnstile não é dirigível headless) | ❌ manual | ⬜ pending |
| 04-03-02 | 03 | 3 | PUBL-06 | — | `wa.me` só com dígitos; `mailto:` igual ao e-mail revelado | manual | inspeção do `href` no devtools | ❌ manual | ⬜ pending |
| 04-03-03 | 03 | 3 | PUBL-03 | T-04-REDIR | `?vaga=` é parseado como UUID, usado só como chave de busca | integration | `?vaga=<uuid>` renderiza o detalhe; uuid inválido não vira URL | ❌ W0 | ⬜ pending |
| 04-04-01 | 04 | 4 | SRCH-01 | T-04-SQLI, T-04-LIKE | `q` acento/caixa-insensível, curingas escapados | integration | `.\.venv\Scripts\python.exe -m pytest tests/test_public_search.py -q` | ❌ W0 | ⬜ pending |
| 04-04-02 | 04 | 4 | SRCH-02 | T-04-SQLI | `city` por whitelist; desconhecida ignorada (sem 400); AND com `q` | integration | mesmo arquivo | ❌ W0 | ⬜ pending |
| 04-04-03 | 04 | 4 | SRCH-03 | — | `sort` whitelist; default `recentes`; ordem determinística (`id` tiebreak) | integration | mesmo arquivo (`-k tie_break`) | ❌ W0 | ⬜ pending |
| 04-05-01 | 05 | 5 | UIUX-02 | — | "Doações" → `/doacoes` (nunca `#`) | smoke | `Invoke-WebRequest http://localhost:3000/doacoes` → 200 | ❌ W0 | ⬜ pending |
| 04-05-02 | 05 | 5 | UIUX-03 | — | 3 slots de ADS com altura fixa | smoke | `Invoke-WebRequest http://localhost:3000/` → 3 ocorrências de "Espaço publicitário" | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `backend/tests/test_public_search.py` — SRCH-01/02/03 + tie-break + escape de curinga + consistência de `total` (reusar fixtures `app`, `db_session`, `fake_turnstile` de `conftest.py`; inserir linhas pela sessão para compartilhar a transação)
- [ ] `frontend/scripts/verify-ssr.ps1` (opcional, ~20 linhas) — asserções `Invoke-WebRequest` do gate de fase
- [ ] Tailwind: `npm install -D tailwindcss@4.3.3 @tailwindcss/postcss@4.3.3` + `postcss.config.mjs`
- [ ] `backend/scripts/seed_public_demo.py` — entregável de produto (D-02), com guarda de ambiente; os smokes dependem dele
- [ ] Migration `0003` — trigger incluindo `requirements` + backfill (o teste de integração verifica `search_text` com termo de `requirements`)

*Gap aceito:* nenhum runner de teste no frontend (D-12a). Coberto por build + lint + asserções HTTP + UAT manual.

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Reveal do contato (idle → verifying → revealed / 403 / 429 / 404) | PUBL-04 | O iframe do Turnstile não é dirigível sem runner headless | Abrir a vaga, clicar "Mostrar contato", confirmar o contato; repetir com token inválido para ver "tente novamente" |
| Candidatura por WhatsApp/e-mail | PUBL-06 | Depende do contato revelado e do app externo | Após revelar, inspecionar `href` do WhatsApp (só dígitos) e do e-mail |
| Contraste e tema | UIUX-01 | Percepção visual + foco por teclado | Navegar por Tab; conferir `#a78bfa` em texto, `#7c3aed` em CTA com branco, Doações amarelo |
| Acessibilidade do modal | PUBL-03 | Comportamento de foco/ESC/backdrop | Abrir com teclado, TAB dentro, ESC fecha, foco volta ao card |
| Modal em mobile | PUBL-03 | Precisa de viewport real | Devtools 375px: bottom sheet, scroll interno, X 44px |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 260s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
