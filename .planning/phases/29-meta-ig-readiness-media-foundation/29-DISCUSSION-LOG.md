# Phase 29: Meta/IG Readiness & Media Foundation - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-11-23
**Phase:** 29-meta-ig-readiness-media-foundation
**Areas discussed:** Origem da imagem, Card: formato e geração, Armazenamento e URL pública, Prontidão IG e token

---

## Origem da imagem

| Option | Description | Selected |
|--------|-------------|----------|
| Card gerado (Recomendado) | Sempre gerar card a partir dos dados da vaga. Simples, determinístico, sem novo campo/upload; funciona com o modelo atual de Job (sem logo). | ✓ |
| Upload na revisão + fallback | Admin pode enviar imagem na revisão; se faltar/inválida, usa card gerado. Mais flexível, mas adiciona UX de upload e armazenamento. | |
| Logo da empresa + fallback | Usar logo/arte cadastrada da empresa quando existir; senão card gerado. Exige definir de onde vem o logo (Job não tem campo hoje). | |

**User's choice:** Card gerado (Recomendado)
**Notes:** Alinha com IMAG-02 e mantém simplicidade no v1.5.

| Option | Description | Selected |
|--------|-------------|----------|
| Ao abrir revisão (Recomendado) | Gera/atualiza ao preparar o draft de revisão; preview usa a mesma imagem que será publicada. Detecta falhas cedo. | ✓ |
| Ao aprovar/publicar IG | Gera só no pipeline de publicação. Mais simples antes, mas preview exato fica mais difícil e falhas aparecem tarde. | |
| Sob demanda + cache | Endpoint gera sob demanda a partir do job_id e cacheia por hash dos dados. URL estável pode apontar para renderização cacheada. | |

**User's choice:** Ao abrir revisão (Recomendado)
**Notes:** Phase 29/30 exigem preview da imagem exata pretendida.

| Option | Description | Selected |
|--------|-------------|----------|
| Regenerar automaticamente (Recomendado) | Regera quando o draft/revisão é carregado ou quando campos relevantes mudam; o preview/publicação sempre usa a versão atual do card. | ✓ |
| Regenerar sempre no publish | Garante imagem final atual, mas o preview pode ficar defasado se algo mudar entre revisão e publicação. | |
| Você decide | Deixa a estratégia de invalidação/regeneração para planejamento/implementação, desde que o preview seja a imagem exata publicada. | |

**User's choice:** Regenerar automaticamente (Recomendado)
**Notes:** Mantém preview/publicação consistentes.

| Option | Description | Selected |
|--------|-------------|----------|
| Bloquear só Instagram (Recomendado) | Mantém independência com Facebook/site: admin pode aprovar/publicar FB sem IG, mas não publica IG até ter imagem válida. Alinha com PUBL-01. | ✓ |
| Bloquear aprovação geral | Mais simples de entender, mas acopla IG ao fluxo geral e pode travar publicação Facebook/site por problema de imagem IG. | |

**User's choice:** Bloquear só Instagram (Recomendado)
**Notes:** Preserva independência entre plataformas.

---

## Card: formato e geração

| Option | Description | Selected |
|--------|-------------|----------|
| 1080x1350 retrato (Recomendado) | 4:5, ocupa mais espaço no feed e comporta melhor título/descrição/local/salário da vaga. Bom para texto. | ✓ |
| 1080x1080 quadrado | Formato simples e seguro, mas com menos área vertical para dados da vaga. Pode exigir mais compactação de texto. | |
| Você decide | Deixa a proporção para planejamento, desde que cumpra IMAG-02 (4:5–1.91:1, JPEG sRGB, <8MB). | |

**User's choice:** 1080x1350 retrato (Recomendado)
**Notes:** Melhor para cards com texto de vaga.

| Option | Description | Selected |
|--------|-------------|----------|
| Dark brand EmpregaNoix (Recomendado) | Fundo escuro + acentos roxos, logo/nome EmpregaNoix e CTA "link na bio". Consistente com a identidade atual e legível no feed. | ✓ |
| Claro/alto contraste | Fundo claro com acentos roxos. Pode ter boa legibilidade, mas foge do visual dark atual da marca. | |
| Você decide | Define layout/identidade visual no planejamento, desde que seja determinístico, legível e compatível com IMAG-02. | |

**User's choice:** Dark brand EmpregaNoix (Recomendado)
**Notes:** Consistente com brand atual (#8b5cf6/#a78bfa, #0f0a1a/#1a1025).

| Option | Description | Selected |
|--------|-------------|----------|
| Essencial sem contato (Recomendado) | Título, empresa (se houver), cidade/remoto, tipo/contrato e salário quando disponível; CTA "link na bio". Sem WhatsApp/e-mail/telefone no card. | ✓ |
| Essencial + contato público | Inclui também contato da vaga no card. Pode facilitar, mas expõe contato diretamente na imagem pública e foge do padrão atual de proteção. | |
| Você decide | Planejamento define o conjunto exato de campos, mantendo legibilidade e sem expor segredos/tokens. | |

**User's choice:** Essencial sem contato (Recomendado)
**Notes:** Mantém padrão de proteção de contato; card público no Instagram.

| Option | Description | Selected |
|--------|-------------|----------|
| Pillow/PIL (Recomendado) | Renderização programática no Python/FastAPI, leve para deploy Railway/Render, determinística; exige cuidar de fontes e quebra de texto. | ✓ |
| HTML para imagem (Playwright) | Template HTML/CSS renderizado em imagem. Flexível visualmente, mas adiciona dependência pesada (browser) e complexidade operacional. | |
| Você decide | Planejamento/pesquisa escolhe a biblioteca, desde que gere JPEG sRGB <8MB, determinístico e compatível com o deploy atual. | |

**User's choice:** Pillow/PIL (Recomendado)
**Notes:** Leve e adequado ao deploy atual.

---

## Armazenamento e URL pública

| Option | Description | Selected |
|--------|-------------|----------|
| Endpoint público no backend (Recomendado) | Backend serve `/public/...` HTTPS com a imagem (arquivo em disco/volume ou gerada sob demanda e cacheada). Sem infra extra; depende de URL estável do backend em deploy. | ✓ |
| Object storage (R2/S3) | Upload para bucket e usar URL pública/CDN. Mais robusto e desacoplado do backend, mas adiciona credenciais, custo/limites e configuração extra. | |
| Banco (Neon bytea) | Armazena bytes no Postgres e serve por endpoint. Evita infra extra, mas aumenta uso do banco e exige cuidado com tamanho/retention. | |

**User's choice:** Endpoint público no backend (Recomendado)
**Notes:** Sem infra extra no v1.5.

| Option | Description | Selected |
|--------|-------------|----------|
| Gerar sob demanda + cache (Recomendado) | Se não houver arquivo/cache válido, gera a partir da vaga e cacheia (disco/volume). URL estável; tolera filesystem efêmero se cache puder ser reconstruído. | ✓ |
| Arquivo persistido obrigatório | Gera e salva arquivo; endpoint só lê arquivo. Simples, mas exige storage persistente confiável no ambiente de deploy. | |
| Você decide | Planejamento define cache/persistência, desde que a URL seja pública, estável e sirva a imagem exata pretendida. | |

**User's choice:** Gerar sob demanda + cache (Recomendado)
**Notes:** Card determinístico permite reconstrução.

| Option | Description | Selected |
|--------|-------------|----------|
| Por job ID com versão/hash (Recomendado) | Ex.: `/public/ig-media/{job_id}?v={hash}` ou path versionado. URL estável por versão exata; muda quando o card muda, facilitando cache e proveniência. | ✓ |
| Por job ID fixo | Ex.: `/public/ig-media/{job_id}.jpg` sempre a mesma URL. Simples, mas cache/invalidação pode ser mais delicada quando o card muda. | |
| Você decide | Planejamento define o formato, desde que seja HTTPS público, estável, sem auth e com proveniência registrada. | |

**User's choice:** Por job ID com versão/hash (Recomendado)
**Notes:** Facilita cache, proveniência e imagem exata.

| Option | Description | Selected |
|--------|-------------|----------|
| Env explícita de base pública (Recomendado) | Usar env explícita (ex.: `BACKEND_PUBLIC_URL` ou `MEDIA_PUBLIC_BASE_URL`) para montar a URL. Evita inferência errada entre frontend/backend. | ✓ |
| Reusar SITE_PUBLIC_URL | Simples se o mesmo domínio público servir a mídia, mas pode ficar errado quando frontend e backend têm domínios diferentes. | |
| Você decide | Planejamento define a configuração, desde que a URL final seja HTTPS pública, não-localhost e validada antes do publish. | |

**User's choice:** Env explícita de base pública (Recomendado)
**Notes:** Evita inferência errada entre domínios frontend/backend.

---

## Prontidão IG e token

| Option | Description | Selected |
|--------|-------------|----------|
| Estender SocialAccount (Recomendado) | Adicionar campos IG (ig_user_id, ig_username/status, readiness) na conta social existente da página. Reaproveita token/fluxo Meta atual e mantém 1 conexão por página. | ✓ |
| Registro IG separado | Criar modelo/registro próprio para Instagram ligado à conta FB. Mais flexível para futuro, mas adiciona complexidade agora sem necessidade clara no v1.5. | |
| Você decide | Planejamento define o modelo, desde que ig-user-id seja persistido, reutilize token Meta existente e não quebre Facebook. | |

**User's choice:** Estender SocialAccount (Recomendado)
**Notes:** Reaproveita modelo Meta/FB existente.

| Option | Description | Selected |
|--------|-------------|----------|
| Conectar + verificar (Recomendado) | Resolver ao concluir OAuth/seleção de página e atualizar em "Verificar agora"/status quando necessário. Dá feedback rápido e mantém estado atualizável. | ✓ |
| Só ao conectar | Resolve apenas no callback OAuth. Simples, mas pode ficar desatualizado se linkage/permissões mudarem depois. | |
| Sob demanda em toda leitura | Consulta Graph em toda chamada de status. Mais atual, mas aumenta latência, dependência externa e risco de rate limit. | |

**User's choice:** Conectar + verificar (Recomendado)
**Notes:** Equilíbrio entre atualidade e custo/latência.

| Option | Description | Selected |
|--------|-------------|----------|
| Exigir reconexão (Recomendado) | Marcar como precisa reconectar/reautorizar para obter novos escopos. Claro e seguro; reaproveita fluxo de reconexão existente no IntegrationsClient. | ✓ |
| Manter e pedir depois | Mantém conexão FB atual e só pede reconexão quando tentar usar IG. Menos atrito inicial, mas estado pode confundir o admin. | |
| Você decide | Planejamento define a migração de escopos, desde que o estado seja acionável e não quebre o Facebook conectado. | |

**User's choice:** Exigir reconexão (Recomendado)
**Notes:** Reaproveita padrão de reconexão já existente.

| Option | Description | Selected |
|--------|-------------|----------|
| Alerta + reconexão (Recomendado) | Detectar invalidação/expiração via verificação e erros de publish; marcar `needs_reconnect` com orientação clara. Simples e alinhado ao fluxo atual. | ✓ |
| Renovação automática + alerta | Tentar renovar automaticamente quando possível e cair para reconexão se falhar. Menos atrito, mas mais complexidade e casos de borda Meta. | |
| Você decide | Planejamento define a estratégia mínima segura, desde que falhas virem estado acionável e sem auto-retry cego. | |

**User's choice:** Alerta + reconexão (Recomendado)
**Notes:** Estratégia mínima segura para v1.5.

---

## OpenCode's Discretion

- Nome exato da env de base pública de mídia (explícita/documentada/validada).
- Shape exato de campos IG no `SocialAccount` e nos schemas de status.
- Layout visual detalhado do card (tipografia, espaçamento, hierarquia) dentro do dark brand.
- Estratégia de cache/TTL/invalidação interna e heurística exata de hash de versão.
- Momento técnico exato de geração no fluxo de revisão, desde que preview seja a imagem exata pretendida.

## Deferred Ideas

- Upload manual de imagem na revisão.
- Logo/arte por empresa como origem primária.
- Renovação automática de token Meta.
- Object storage/CDN dedicado para mídia IG (R2/S3).
- Stories/Reels/carrossel/vídeo, agendamento, métricas, múltiplas contas IG (já fora de escopo v1.5).
