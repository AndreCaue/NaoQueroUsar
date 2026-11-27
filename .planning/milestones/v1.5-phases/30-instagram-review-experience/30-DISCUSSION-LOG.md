# Phase 30: Instagram Review Experience - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-11-23
**Phase:** 30-instagram-review-experience
**Areas discussed:** Prefill da legenda IG (Instagram-tuned), Seção/toggle do Instagram no diálogo e prontidão, Preview da imagem IG no review

---

## Prefill da legenda IG (Instagram-tuned)

| Option | Description | Selected |
|--------|-------------|----------|
| (A) Reutilizar rascunho do Facebook como base | Base simples a partir do texto do Facebook (admin edita); pode ser “tuneado” para FB. | |
| (B) Gerar legenda própria para IG a partir dos dados da vaga (fluxo separado) | Mais nativa para IG, mas exige fluxo/geração adicional. | |
| (C) Prefill por template simples a partir dos campos da vaga | Título/empresa/cidade-remoto/tipo-contrato/salário quando houver + CTA; sem depender do rascunho FB como padrão. | ✓ |

**User's choice:** (C) template simples. Detalhes informados: CTA sempre “link na bio”; hashtags sugeridas iniciais `#vagas`, `#emprego`, `#cidade`, `#oportunidade` (admin pode editar). Padrão não reutiliza cegamente o rascunho do Facebook.

**Notes:** Usuário confirmou “Sim templates simples, Hastags #vagas, #emprego, #cidade, #oportunidade”.

---

## Seção/toggle do Instagram no diálogo e prontidão

| Option | Description | Selected |
|--------|-------------|----------|
| Seção abaixo de “Post para Facebook” em EditJobDialog; toggle controla visibilidade dos campos | Toggle “Publicar no Instagram desta vaga”: quando desligado, esconder legenda/preview (mostrar só toggle/contexto). | ✓ (comportamento esperado) |
| Seção visível mas desabilitada quando IG não pronto, com link para /admin/integracoes | Quando prontidão IG insuficiente, manter seção visível mas desabilitada e orientar ação em /admin/integracoes. | ✓ |

**User's choice:** Manter seção “Post para Instagram” visível mas desabilitada quando não estiver pronto, com link para `/admin/integracoes`. Toggle “Publicar no Instagram desta vaga”: quando desligado, esconder legenda e preview. Reforçado que Facebook e Instagram são independentes.

**Notes:** Usuário afirmou: “Caso não esteja funciona manter desabilitado porém visível” e “A postagem no facebook e IG devem ser indepedentes”.

---

## Preview da imagem IG no review

| Option | Description | Selected |
|--------|-------------|----------|
| (A) Preparar/buscar automaticamente ao abrir o diálogo ou ao ativar o toggle | Preview carregado automaticamente no fluxo adequado (loading/erro em pt-BR). | ✓ |
| (B) Botão manual “Atualizar preview” | Admin aciona atualização manualmente. | |
| (C) Sempre mostrar se já pronta | Depende de estado pré-existente; menos previsível sem preparo explícito. | |

**User's choice:** (A) automático. Bloqueio apenas do Instagram se imagem inválida/ausente (não bloqueia Facebook/site), alinhado a IMAG-01.

**Notes:** Usuário respondeu: “A sim bloqueio só IG”.

---

## OpenCode's Discretion

- Wording final em pt-BR de textos de ajuda/erros na seção IG (consistente com admin).
- Posicionamento/estilo do contador e avisos (respeitando design system).
- Detalhe técnico de quando chamar preparo de mídia (abrir vs toggle) desde que atenda D-06.
- Fonte de status IG na revisão (reutilizar buscas existentes vs nova busca), desde que simples e sem quebrar Facebook.

## Deferred Ideas

- Geração de legenda IG via LLM separada (além do template C) — não decidido.
- Campos avançados de IG (hashtags gerenciadas separadamente, primeiros comentários etc.) — fora de REVW-01..04.
- Alterações no pipeline assíncrono de publicação — Phase 31.
