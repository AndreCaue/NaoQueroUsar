---
phase: 261111-krt
plan: 01
type: execute
wave: 1
depends_on: []
files_modified:
  - frontend/package.json
  - frontend/package-lock.json
  - frontend/eslint.config.mjs
  - frontend/.eslintrc.json
autonomous: true
requirements: []   # quick task — sem IDs de ROADMAP; escopo vem da tarefa 261111-krt
user_setup: []

must_haves:
  truths:
    - "npm ls next resolve exatamente 16.4.6 (latest) e o build nao emite mais 'Vulnerable version of Next.js detected'"
    - "O lint roda em ESLint 9 flat config (eslint.config.mjs) sem depender de 'next lint' (removido no Next 16)"
    - "npx tsc --noEmit, npm run lint e npm run build passam no Next 16.4.6"
    - "React/React DOM permanecem em 19.1.1 (peer ^19.0.0 do Next 16 satisfeito) e nenhuma funcionalidade/rota e removida"
  artifacts:
    - path: "frontend/package.json"
      provides: "next + eslint-config-next 16.4.6, eslint ^9, script lint = eslint ."
      contains: "\"next\": \"16.4.6\""
    - path: "frontend/package-lock.json"
      provides: "Lockfile regenerado resolvendo next 16.4.6"
      contains: "node_modules/next"
    - path: "frontend/eslint.config.mjs"
      provides: "Flat config compatibilizando next/core-web-vitals em ESLint 9"
      contains: "core-web-vitals"
  key_links:
    - from: "frontend/eslint.config.mjs"
      to: "eslint-config-next/core-web-vitals"
      via: "FlatCompat.extends"
      pattern: "core-web-vitals"
    - from: "frontend/package.json"
      to: "frontend/eslint.config.mjs"
      via: "script lint"
      pattern: "eslint \\."
---

<objective>
Atualizar o frontend para `next@16.4.6` (latest) e migrar o lint para ESLint 9 em flat config, desbloqueando o build do Vercel que recusa a linha 15.x com "Vulnerable version of Next.js detected".

Purpose: a 15.5.29 ja e a ultima 15.x e ainda assim o deploy e bloqueado; a unica saida alinhada ao pedido do usuario e subir para a major atual. O Next 16 removeu `next lint` e o `eslint-config-next@16` exige `eslint >= 9`, entao o upgrade de dependencia arrasta a migracao da configuracao de lint.

Output: `package.json`/`package-lock.json` em 16.4.6 + eslint 9, `eslint.config.mjs` substituindo `.eslintrc.json`, e verificacao `tsc`/`lint`/`build`.

Sem mudanca de comportamento de produto: nenhuma rota, texto ou componente alterado.
</objective>

<tasks>

<task type="auto">
  <name>Task 1: Instalar Next 16.4.6 + ESLint 9</name>
  <files>frontend/package.json, frontend/package-lock.json</files>
  <action>
    Em `frontend/`: `npm install next@16.4.6 eslint-config-next@16.4.6` e `npm install -D eslint@^9`. Ajustar o script `lint` para `eslint .`. Manter `react`/`react-dom` em 19.1.1 (peer do Next 16 aceita ^19.0.0) e os `overrides` de postcss/sharp existentes.
  </action>
  <verify>`node -e "console.log(require('./node_modules/next/package.json').version)"` imprime 16.4.6; `npm ls next eslint` sem `invalid`/`missing`.</verify>
  <done>next 16.4.6 instalado e lockfile regenerado.</done>
</task>

<task type="auto">
  <name>Task 2: Migrar lint para flat config</name>
  <files>frontend/eslint.config.mjs, frontend/.eslintrc.json</files>
  <action>
    Remover `.eslintrc.json` e criar `eslint.config.mjs` com `FlatCompat` estendendo `next/core-web-vitals`, preservando as regras desligadas que a config antiga tinha (`react/react-in-jsx-scope`, `react/jsx-uses-react`). Adicionar `eslint` a devDependencies (feito na Task 1) e `.next`/`node_modules` aos ignores.
  </action>
  <verify>`npx eslint --print-config app/layout.tsx` executa sem erro de config e `npm run lint` roda (exit 0 ou apenas warnings preexistentes).</verify>
  <done>Lint roda em ESLint 9 sem `next lint`.</done>
</task>

<task type="auto">
  <name>Task 3: Validar build no Next 16</name>
  <files>frontend/next.config.mjs (somente se necessario)</files>
  <action>
    Rodar `npx tsc --noEmit`, `npm run lint` e `npm run build` com `NEXT_PUBLIC_API_URL=http://localhost:8000` e `NEXT_PUBLIC_TURNSTILE_SITE_KEY=1x00000000000000000000AA`. Registrar no SUMMARY as 10 rotas geradas e qualquer aviso de deprecacao do Next 16.
  </action>
  <verify>Build conclui com sucesso e lista as rotas `/`, `/admin`, `/admin/paste`, `/admin/review`, `/doacoes`, `/privacidade`, `/termos-de-uso`, `/_not-found`.</verify>
  <done>tsc + lint + build verdes em 16.4.6.</done>
</task>

</tasks>

<verification>
- `npm ls next` = 16.4.6
- `npx tsc --noEmit` exit 0
- `npm run lint` exit 0
- `npm run build` exit 0 com as rotas esperadas
- Nenhuma alteracao fora de `frontend/package.json`, `frontend/package-lock.json`, `frontend/eslint.config.mjs` (e remocao de `.eslintrc.json`)
</verification>
