---
phase: 261111-krt
plan: 01
status: complete
date: 2026-11-11
commits: [56b0b34]
---

# Quick Task 261111-krt: atualizar Next.js para 16.4.6 e migrar o lint para ESLint 9

## Resultado

`next@16.4.6` (latest) instalado no frontend, com `eslint-config-next@16.4.6` e `eslint@9.39.5` em flat config. `tsc --noEmit`, `npm run lint` e `npm run build` passam; o bloqueio `Vulnerable version of Next.js detected` deixa de ter causa, porque a linha 15.x (última = 15.5.29) não é mais usada.

## O que mudou

| Arquivo | Mudança |
|---------|---------|
| `frontend/package.json` | `next` 15.5.29 → **16.4.6**; `eslint-config-next` 15.5.29 → **16.4.6**; `eslint` 8.57.1 → **^9.39.5**; script `lint` de `next lint` → `eslint .` |
| `frontend/package-lock.json` | Regenerado (resolved `next` 16.4.6; `react`/`react-dom` continuam 19.1.1) |
| `frontend/eslint.config.mjs` | **Novo** — flat config nativo usando o export `eslint-config-next/core-web-vitals` (sem `FlatCompat`) + ignores + regras herdadas da `.eslintrc.json` |
| `frontend/.eslintrc.json` | **Removido** (formato eslintrc não é mais usado pelo ESLint 9/Next 16) |
| `frontend/tsconfig.json` | Reescrito pelo próprio `next build`: `jsx: preserve` → **`react-jsx`** (obrigatório no Next 16) e `include` ganhou `.next/dev/types/**/*.ts` |
| `frontend/next-env.d.ts` | Gerado pelo Next 16: referências a `routes.d.ts` + novo `root-params.d.ts` |

## Verificação

- `npm ls next` → `next@16.4.6` (sem `invalid`/`missing`); `eslint@9.39.5`.
- `npx tsc --noEmit` → exit 0.
- `npm run lint` → exit 0, **8 warnings** (0 erros): 6 de `react-hooks/set-state-in-effect` (regra nova do `eslint-plugin-react-hooks@7`, ver abaixo) + 2 `Unused eslint-disable directive` nas páginas legais.
- `npm run build` (com `NEXT_PUBLIC_API_URL=http://localhost:8000` e `NEXT_PUBLIC_TURNSTILE_SITE_KEY=1x00000000000000000000AA`) → exit 0, `Next.js 16.4.6 (Turbopack)`, 9 páginas geradas:

```
Route (app)
┌ ƒ /
├ ○ /_not-found
├ ○ /admin
├ ○ /admin/paste
├ ○ /admin/review
├ ○ /doacoes
├ ○ /privacidade
└ ○ /termos-de-uso
```

- `npm audit --omit=dev` → **0 vulnerabilities**. Os 8 moderate restantes são dev-only (`minimatch` na cadeia `typescript-eslint`); o `npm audit fix` sugerido *rebaixaria* `eslint-config-next` para 15.5.29, então foi recusado.

## Decisões e desvios

1. **ESLint 9, não 10.** O `eslint-config-next@16.4.6` aceita `>=9.0.0`, mas `eslint-plugin-react@7.37.5` (dependência transitiva) declara peer `^3 || … || ^9.7` e não suporta ESLint 10. Ficamos na última 9.x (9.39.5), que o npm marca como "no longer supported" — a alternativa real é o upgrade do plugin React, fora do escopo.
2. **`react-hooks/set-state-in-effect` rebaixada para `warn`.** A regra (React Compiler, nova no `eslint-plugin-react-hooks@7`) acusa 6 padrões pré-existentes e intencionais: hidratação de `localStorage` em `AdminGuard`/`ExtractForm`/`RevealContact` e "reset de estado quando a prop muda" em `EditJobDialog`/`ReviewQueue`/`ReportJobDialog`. Corrigir isso é refatoração de produto (fora do escopo de um upgrade de dependência), então a regra foi mantida visível como warning; o refactor fica como follow-up.
3. **`tsconfig.json` reescrito pelo Next.** Mudança mandatória (`jsx: react-jsx`); o reformat de arrays é ruído do próprio serializer do Next.
4. **Nenhuma mudança de comportamento de produto:** rotas, componentes e textos intactos. `next.config.mjs` (`outputFileTracingRoot`) continua válido no Next 16 e não foi tocado.
5. **Docs atualizados só onde apontam para a stack viva:** `.planning/PROJECT.md`, `AGENTS.md` e `docs/DEPLOY.md` passam a dizer Next.js 16 (`16.4.6`). Research/summaries de fases anteriores permanecem como registro histórico.

## Follow-ups

- Refatorar os 6 usos de `setState` síncrono em `useEffect` (ou manter a regra em `warn` se o padrão for aceito).
- Reavaliar ESLint 10 quando `eslint-plugin-react` suportar (hoje o peer para em `^9.7`).
- REV-08 continua aberto (páginas legais aninhadas com `<main>`/header duplicados e rodapé linkando só `/privacidade`).
- O deploy de produção continua adiado (opção B); 06-04 Task 3 segue sendo o checkpoint humano.
