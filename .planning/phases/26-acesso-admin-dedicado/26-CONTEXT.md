# Phase 26: Acesso Admin Dedicado - Context

**Gathered:** 2026-11-22
**Status:** Ready for planning

<domain>
## Phase Boundary

Separar o login admin em uma página dedicada e manter a entrada pública discreta, sem alterar o modelo de autenticação nem a proteção das rotas admin. Esta fase entrega: página de login admin dedicada (separada da página de paste/revisão), fluxo de autenticação funcional por essa página, redirecionamentos coerentes para sessão ausente/ativa, e link discreto para o login na página de Política de Privacidade. Não inclui cadastro/multiusuário, mudanças no contrato de auth do backend, nem novos recursos admin.

</domain>

<decisions>
## Implementation Decisions

### Fluxo e redirecionamentos
- **D-01:** A página dedicada de login fica em `/admin/login`, dentro do namespace admin.
- **D-02:** Após autenticar com sucesso, redirecionar para a página solicitada originalmente (return-to) quando existir; caso contrário, fallback para `/admin`.
- **D-03:** Quando um usuário sem sessão acessa uma rota admin protegida, redirecionar para `/admin/login` preservando o destino de retorno.
- **D-04:** Quando já autenticado, abrir `/admin/login` redireciona para `/admin` (ou para o retorno válido, se aplicável). Ao sair (logout), redirecionar para `/admin/login`.

### Entrada discreta na Política de Privacidade
- **D-05:** O link fica no rodapé do conteúdo da Política de Privacidade, abaixo do aviso final (disclaimer box).
- **D-06:** Peso visual discreto: texto pequeno e suave, cor muted/baixa ênfase, sem botão ou ícone chamativo.
- **D-07:** O texto do link é "Acesso administrativo".
- **D-08:** Apresentação em linha própria, pequena e muted, abaixo do box de aviso.

### Experiência da página de login
- **D-09:** Layout focado no login, sem navegação admin (sem Publicações/Integrações/Sair enquanto deslogado), com branding mínimo.
- **D-10:** Conteúdo direto e objetivo: título claro, campo de senha e botão Entrar; sem texto longo.
- **D-11:** Incluir um link discreto para voltar ao site público.
- **D-12:** Linguagem visual alinhada ao visual admin atual (tema escuro/canvas/surface/accent).

### OpenCode's Discretion
- Copy exata do título/subtexto da página de login, desde que direta e objetiva.
- Implementação técnica do parâmetro de retorno (nome/validação/sanitização) e regras de fallback seguro.
- Espaçamento, tipografia e detalhes responsivos, mantendo o peso visual discreto definido.
- Microcopy de loading/erro além dos padrões já existentes, sem alterar o contrato de autenticação.
- Estrutura exata de componentes/arquivos para separar login do fluxo de paste, respeitando os comportamentos decididos.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Escopo e requisitos da fase
- `.planning/ROADMAP.md` §"Phase 26: Acesso Admin Dedicado" — Goal, depends on, requirements ADMN-01/ADMN-02, success criteria e UI hint.
- `.planning/REQUIREMENTS.md` §"Acesso Admin" — ADMN-01 (login dedicado separado do paste/revisão) e ADMN-02 (link discreto na Política de Privacidade).
- `.planning/PROJECT.md` §"Current Milestone: v1.4 Polimento UX e Admin" — contexto do milestone e restrição de não perder fricção zero do candidato.

### Fluxo admin/auth atual (código)
- `frontend/app/admin/page.tsx` — painel admin atual e destino natural pós-login.
- `frontend/app/admin/layout.tsx` — shell admin atual (header/nav/logout) que não deve aparecer no login deslogado.
- `frontend/app/admin/paste/page.tsx` — página de paste; hoje hospeda o fluxo de extração.
- `frontend/app/admin/paste/ExtractForm.tsx` — login atual embutido (senha + Turnstile + sessão em sessionStorage) e fluxo de extração; base para separar responsabilidades.
- `frontend/components/admin/AdminGuard.tsx` — guard client-side atual; hoje redireciona ausência de token para `/admin/paste`.
- `frontend/components/admin/LogoutButton.tsx` — logout atual; hoje hard-navigate para `/admin/paste`.
- `frontend/lib/api.ts` (`loginAdmin`) — contrato de login frontend para `POST /api/v1/auth/login` com `password` e `cf_token`.
- `frontend/lib/auth.ts` — chave de sessão `nqu_admin_token` em sessionStorage.
- `backend/app/api/v1/auth.py` — endpoint de login admin (rate limit, Turnstile server-side, verificação de senha, JWT).
- `backend/app/schemas/auth.py` — contrato `LoginRequest`/`TokenResponse`.
- `backend/app/core/security.py` — autenticação por senha hash + JWT HS256.

### Entrada pública discreta
- `frontend/app/(public)/privacidade/page.tsx` — página onde o link discreto "Acesso administrativo" deve ser inserido abaixo do aviso final.

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `frontend/app/admin/paste/ExtractForm.tsx`: já implementa login com Turnstile, tratamento de erro, loading e armazenamento de token; pode ser base para extrair/reusar o formulário de login na página dedicada.
- `frontend/components/admin/AdminGuard.tsx`: guard central de rotas admin; ponto natural para redirecionamento para `/admin/login` com return-to.
- `frontend/lib/api.ts` `loginAdmin` / `frontend/lib/auth.ts` `TOKEN_KEY`: contrato e chave de sessão já estabelecidos; manter compatibilidade.
- `backend/app/api/v1/auth.py` + `TurnstileVerifier`: backend já exige Turnstile server-side e rate limit no login; não precisa mudar o contrato para esta fase.

### Established Patterns
- Rotas admin em `frontend/app/admin/*` com layout compartilhado (`admin/layout.tsx`) e proteção client-side via `useAdminGuard`.
- Sessão admin em `sessionStorage` (`nqu_admin_token`), lida após mount para evitar SSR mismatch.
- Logout e alguns fluxos de erro usam `window.location.replace("/admin/paste")` para limpar estado em memória — esses destinos devem ser revisados para `/admin/login`.
- Página de Privacidade é conteúdo estático público em `frontend/app/(public)/privacidade/page.tsx`, com aviso final em box no rodapé do artigo.

### Integration Points
- `frontend/app/admin/login/*` (novo): página dedicada de login e, se necessário, layout/componente para estado deslogado sem nav admin.
- `frontend/components/admin/AdminGuard.tsx`: mudar alvo de redirect e capturar destino pretendido.
- `frontend/components/admin/LogoutButton.tsx` e handlers 401 em admin (ex.: review): alinhar redirecionamento para `/admin/login`.
- `frontend/app/admin/paste/ExtractForm.tsx`: remover papel de login principal; manter extração para sessão autenticada.
- `frontend/app/(public)/privacidade/page.tsx`: adicionar link discreto "Acesso administrativo" abaixo do aviso final.

</code_context>

<specifics>
## Specific Ideas

No specific product references — seguir as decisões capturadas e os padrões visuais/estruturais existentes do admin.

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope.

</deferred>

---

*Phase: 26-acesso-admin-dedicado*
*Context gathered: 2026-11-22*
