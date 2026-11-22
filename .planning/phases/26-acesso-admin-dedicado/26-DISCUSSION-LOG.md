# Phase 26: Acesso Admin Dedicado - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-11-22
**Phase:** 26-acesso-admin-dedicado
**Areas discussed:** Fluxo e redirecionamentos, Entrada discreta na Privacidade, Experiência da página de login

---

## Fluxo e redirecionamentos

| Option | Description | Selected |
|--------|-------------|----------|
| `/admin/login` (Recomendado) | Fica dentro do namespace admin, alinhado com as rotas atuais (/admin/paste, /admin/review). Simples de proteger e manter. | ✓ |
| `/login` (fora de /admin) | Separa login do namespace admin; pode exigir ajuste de layout/guard para tratar rota fora de /admin. | |
| Você decide | Deixa a escolha de rota para o planejamento, desde que seja uma página dedicada e separada do paste/revisão. | |

**User's choice:** `/admin/login` (Recomendado)
**Notes:** Nenhuma.

| Option | Description | Selected |
|--------|-------------|----------|
| Página solicitada ou /admin (Recomendado) | Se chegou por redirecionamento, volta à página pretendida; caso contrário, cai no painel /admin. Bom equilíbrio entre contexto e previsibilidade. | ✓ |
| Sempre /admin | Sempre aterrissa no painel admin após login, independente de onde tentou entrar. Simples e previsível. | |
| Sempre /admin/paste | Vai direto para a extração de vagas, que é o fluxo principal atual. Pula o painel. | |

**User's choice:** Página solicitada ou /admin (Recomendado)
**Notes:** Nenhuma.

| Option | Description | Selected |
|--------|-------------|----------|
| Redirecionar para /admin/login com retorno (Recomendado) | Envia para /admin/login e, após login, volta para a página que ele tentou acessar. Consistente com a decisão anterior. | ✓ |
| Redirecionar para /admin/login sem retorno | Sempre vai para /admin/login e, após login, segue o destino padrão (/admin). Mais simples, mas perde o contexto. | |

**User's choice:** Redirecionar para /admin/login com retorno (Recomendado)
**Notes:** Nenhuma.

| Option | Description | Selected |
|--------|-------------|----------|
| Redirecionar login para /admin; logout vai para /admin/login (Recomendado) | Se já está logado, /admin/login redireciona para /admin (ou retorno). Ao sair, volta para a página dedicada de login. Fluxo limpo. | ✓ |
| Redirecionar login para /admin; logout vai para a home pública | Evita tela de login após sair; admin volta ao site público. Para entrar de novo, usa o link discreto na Privacidade. | |
| Permitir re-login em /admin/login; logout vai para /admin/login | Mesmo logado pode ver o formulário (útil para trocar sessão). Logout volta à página de login. | |

**User's choice:** Redirecionar login para /admin; logout vai para /admin/login (Recomendado)
**Notes:** Nenhuma.

---

## Entrada discreta na Privacidade

| Option | Description | Selected |
|--------|-------------|----------|
| No rodapé do conteúdo, abaixo do aviso final (Recomendado) | Um link pequeno e discreto após o bloco de aviso no fim da página. Fácil de achar se procurar, sem chamar atenção no fluxo de leitura. | ✓ |
| Dentro da seção 13 (Contato) | Fica junto ao e-mail de contato, como uma linha pequena extra. Mais contextual, mas um pouco mais visível dentro do conteúdo. | |
| No texto do aviso final (disclaimer box) | Incorporado como texto/link discreto dentro do próprio box de aviso no rodapé. Bem discreto, mas mistura com o aviso legal. | |

**User's choice:** No rodapé do conteúdo, abaixo do aviso final (Recomendado)
**Notes:** Nenhuma.

| Option | Description | Selected |
|--------|-------------|----------|
| Texto pequeno e suave (Recomendado) | Link em texto menor, cor muted/baixa ênfase, sem botão ou ícone chamativo. Perceptível ao procurar, sem competir com o conteúdo. | ✓ |
| Texto muted padrão | Mesmo estilo de links secundários do site, só posicionado de forma discreta. Mais fácil de notar. | |
| Quase invisível até hover/foco | Muito baixo contraste por padrão, ganha visibilidade no hover/foco. Máximo de discrição, mas pode ficar difícil de encontrar. | |

**User's choice:** Texto pequeno e suave (Recomendado)
**Notes:** Nenhuma.

| Option | Description | Selected |
|--------|-------------|----------|
| Acesso administrativo (Recomendado) | Neutro e discreto; deixa claro para quem procura, sem parecer call-to-action. | ✓ |
| Área do administrador | Um pouco mais explícito sobre o destino, ainda sóbrio. | |
| Login admin | Direto e curto. Menos formal, mas claro. | |

**User's choice:** Acesso administrativo (Recomendado)
**Notes:** Nenhuma.

| Option | Description | Selected |
|--------|-------------|----------|
| Linha própria, pequena e muted (Recomendado) | Fica em uma linha separada abaixo do box de aviso, com espaçamento discreto. Fácil de identificar como link isolado. | ✓ |
| Texto pequeno no fim do aviso | Aparece como uma pequena linha de texto ainda dentro da área inferior, mas fora do box principal. Diferença sutil de agrupamento. | |
| Você decide | Deixa o detalhe de formatação para o planejamento/implementação, mantendo discrição. | |

**User's choice:** Linha própria, pequena e muted (Recomendado)
**Notes:** Nenhuma.

---

## Experiência da página de login

| Option | Description | Selected |
|--------|-------------|----------|
| Foco no login, sem navegação admin (Recomendado) | Página limpa e centralizada, com branding mínimo (EmpregaNoix) e só o formulário de login. Sem links de Publicações/Integrações/Sair enquanto deslogado. | ✓ |
| Dentro do shell admin atual | Reaproveita o layout admin existente (header/nav). Mais consistente com o admin, mas mostra navegação que não faz sentido antes do login. | |
| Você decide | Deixa a estrutura visual para o planejamento, desde que seja uma página de login dedicada e clara. | |

**User's choice:** Foco no login, sem navegação admin (Recomendado)
**Notes:** Nenhuma.

| Option | Description | Selected |
|--------|-------------|----------|
| Direto e objetivo (Recomendado) | Título claro (ex.: acesso admin), campo de senha e botão Entrar. Sem texto longo; foco na ação. | ✓ |
| Direto com contexto curto | Inclui uma linha breve explicando que é a área de curadoria/administração do EmpregaNoix, além do formulário. | |
| Você decide | Deixa o texto/copy para o planejamento, mantendo tom discreto e funcional. | |

**User's choice:** Direto e objetivo (Recomendado)
**Notes:** Nenhuma.

| Option | Description | Selected |
|--------|-------------|----------|
| Sim, link discreto para voltar ao site (Recomendado) | Inclui um link pequeno (ex.: voltar para vagas/home). Ajuda quem chegou ali por engano sem poluir a página. | ✓ |
| Apenas o logo/link EmpregaNoix para home | Usa só o branding como âncora para voltar ao site, sem link textual extra. | |
| Sem link de volta | Página totalmente focada no login; voltar fica por navegação do navegador. Mais minimalista. | |

**User's choice:** Sim, link discreto para voltar ao site (Recomendado)
**Notes:** Nenhuma.

| Option | Description | Selected |
|--------|-------------|----------|
| Visual admin atual (Recomendado) | Mantém o mesmo tema escuro/estilo do admin (bg-canvas, surface, accent), reforçando que é uma área administrativa. Consistente com o restante do admin. | ✓ |
| Visual do site público | Usa a linguagem visual da área pública. Pode parecer mais "integrado" ao site, mas menos distinto como área admin. | |
| Você decide | Deixa a escolha visual para o planejamento, desde que fique claro e funcional. | |

**User's choice:** Visual admin atual (Recomendado)
**Notes:** Nenhuma.

## OpenCode's Discretion

- Copy exata do título/subtexto da página de login, mantendo tom direto e objetivo.
- Implementação técnica de return-to (parâmetro, validação e fallback seguro).
- Detalhes de espaçamento/tipografia/responsividade, preservando discrição e clareza.
- Microcopy de loading/erro além dos padrões existentes, sem mudar contrato de auth.

## Deferred Ideas

None — discussion stayed within phase scope.
