# Deferred Items — Phase 03 (contact-reveal-anti-spam)

Descobertas fora do escopo dos planos da fase, encontradas durante a execução
do plano 03-04. **Não corrigidas aqui** — o escopo dos planos não as cobre e a
regra de escopo do executor proíbe mexer em falhas pré-existentes de arquivos
não relacionados.

| # | Categoria | Item | Por que ficou para trás | Quando resolver |
|---|-----------|------|-------------------------|----------------|
| D-1 | Dependências / segurança | **RESOLVIDO em 2026-11-03.** `next` atualizado de `15.5.3` → `15.5.29` (patch, sem major; stack Next 15 preservada) e adicionados `overrides` de `postcss` (`^8.5.32`) e `sharp` (`^0.35.5`) no `frontend/package.json`. `npm audit` caiu de **1 critical / 2 high / 18 moderate** para **0 critical / 0 high / 18 moderate**; os 18 moderate restantes são todos da cadeia ESLint (dev-only, não vai para produção). Validado com `npm run lint`, `npx tsc --noEmit` e `npm run build` (Next 15.5.29, build OK). | O plano 03-04 proíbe explicitamente alterar a versão do Next/React (`frontend/package.json` só ganha o `next-turnstile`), e a decisão de stack é do usuário. Bump de Next em fase HIGH RISK é mudança arquitetural (Regra 4), não desvio automático. | Resolvido antes da Phase 6, por decisão do usuário |
| D-2 | Tooling | `frontend/tsconfig.json` está modificado na working tree (só reformatação: `lib`/`paths`/`include` quebrados em múltiplas linhas + `"target": "ES2017"` adicionado). Mudança **pré-existente** a este plano. | Alteração deliberadamente deixada fora do versionamento pelo executor: não pertence a nenhum plano da fase. | Revisitar com o bump de Next (D-1), já que o `target`/`lib` SHOULD ser alinhados com a versão nova |
| D-3 | Tooling | Aviso do Next: "inferred your workspace root" — existem dois lockfiles (`C:\Users\AndreC\package-lock.json` e `frontend/package-lock.json`), então o Next escolhe a raiz errada para o `outputFileTracingRoot`. | O `frontend/package-lock.json` é deliberadamente **não rastreado** pelo git neste repositório; o lockfile da home está fora do projeto. | Phase 6 (deploy) — definir `outputFileTracingRoot` no `next.config` ao configurar a Vercel |

---

*Criado durante a execução do plano 03-04 (2026-10-21).*
