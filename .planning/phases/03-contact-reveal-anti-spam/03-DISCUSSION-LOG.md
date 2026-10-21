# Phase 3: Contact Reveal & Anti-Spam - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-10-21
**Phase:** 03-contact-reveal-anti-spam
**Areas discussed:** Fricção do visitante no reveal, Política de rate limit, Chave Turnstile ausente: fail-closed ou fail-open, Turnstile no login: sempre ou progressivo

---

## Fricção do visitante no reveal

### O que o visitante vê do Turnstile

| Option | Description | Selected |
|--------|-------------|----------|
| Só aparece se o Turnstile desconfiar (interaction-only) | Widget roda em background; humano comum passa sem ver nada. Reveal = 1 clique, alinhado ao core value "sem fricção". | ✓ |
| Checkbox visível (modo managed) | Visitante vê "Verificando se você é humano" e marca o checkbox. 1 clique extra, mais explícito e fácil de depurar. | |
| Badge fixo, sem interação (non-interactive) | Selo "Protegido por Cloudflare", sem checkbox e sem desafio manual. Mais simples, mas o Turnstile não consegue exigir interação em casos suspeitos. | |

**User's choice:** Só aparece se o Turnstile desconfiar (interaction-only)
**Notes:** Widget em modo interaction-only também foi escolhido depois para a tela de login do admin (área 4).

### Escopo de frontend desta fase

| Option | Description | Selected |
|--------|-------------|----------|
| Só backend + widget do login (recomendado) | A fase entrega o endpoint + o widget do login do admin. O reveal público é verificado por pytest e a UI real fica na Phase 4. | ✓ |
| Incluir página pública mínima de teste | Página simples em /revelar-teste com o botão "Mostrar contato" + widget, para validar o fluxo real (Siteverify de verdade, analytics > 0). | |
| Backend + login + modal real de reveal | Entrega a página pública completa do reveal, antecipando boa parte da Phase 4. | |

**User's choice:** Só backend + widget do login (recomendado)
**Notes:** Implicação registrada: a única prova real do Siteverify nesta fase é o login do admin — o dashboard do Cloudflare deve mostrar validações > 0 por causa dele.

### Ordem das verificações no endpoint de reveal

| Option | Description | Selected |
|--------|-------------|----------|
| 404 (vaga inexistente) antes do Turnstile | Ordem: rate limit → busca da vaga (404) → Siteverify (403). IDs são UUID, sem oráculo prático de existência, e o atacante não gasta chamadas da Cloudflare com IDs falsos. | ✓ |
| Turnstile antes de tudo (403 primeiro) | Quem não provou ser humano nunca descobre se a vaga existe. Custo: cada tentativa paga uma ida à Cloudflare, inclusive de scrapers. | |
| 403 e 404 com a mesma resposta | Sem oráculo nenhum, a custo de um round-trip extra à Cloudflare em toda request. | |

**User's choice:** 404 (vaga inexistente) antes do Turnstile

### Reabertura do modal após revelar

| Option | Description | Selected |
|--------|-------------|----------|
| Novo Turnstile a cada abertura | Token é single-use: o servidor já consumiu no reveal anterior. Mais simples e o contato nunca fica no cliente além do momento do reveal. | |
| Manter o contato em memória enquanto a aba estiver aberta | Depois de um reveal legítimo, o contato fica em memória (não em storage) e reabrir o modal mostra direto. | ✓ |
| Guardar em sessionStorage (sobrevive a F5) | Persiste na aba mesmo após F5 — exatamente o "contato no payload do cliente" que o Pitfall 7 combatte. | |

**User's choice:** Manter o contato em memória enquanto a aba estiver aberta

### Escopo do cache em memória

| Option | Description | Selected |
|--------|-------------|----------|
| Só para a vaga já revelada (recomendado) | Cache por job_id: reabrir a vaga X mostra o contato direto; abrir a vaga Y ainda pede token novo (o anterior foi consumido). | ✓ |
| Libera a aba inteira | Uma vez verificado, todas as vagas da aba são reveladas sem novo widget — enfraquece o single-use do Cloudflare. | |

**User's choice:** Só para a vaga já revelada (recomendado)

---

## Política de rate limit

### Janela e granularidade

| Option | Description | Selected |
|--------|-------------|----------|
| Por IP, janela de 1 minuto (recomendado) | 10/min no reveal, 5/min no login, por IP, ambos por env. Simples, ajustável sem deploy. | ✓ |
| Por IP, 1 minuto + teto diário | Janela de 1 minuto E teto diário (ex.: 100/dia) por IP — o teto diário é o que derruba um scraper em ritmo lento. | |
| Por IP, janela de 1 hora | Mais rígido contra raspagem, mas pune o visitante legítimo que fica comparando vagas por mais de 1 minuto. | |

**User's choice:** Por IP, janela de 1 minuto (recomendado)

### O que o contador conta

| Option | Description | Selected |
|--------|-------------|----------|
| Conta todas as tentativas (recomendado) | Cada request conta, mesmo com token inválido. Sem isso, um bot inunda o Siteverify de graça e o custo do ataque cai no nosso bolso. | ✓ |
| Dois contadores (tentativas + sucessos) | Bucket de tentativas (ex.: 20/min) + bucket de revelações bem-sucedidas (ex.: 10/min). Mais justo com o visitante legítimo, mais configuração. | |
| Só as bem-sucedidas | O visitante legítimo nunca é penalizado por uma falha, mas o scraper não paga por inundar a Cloudflare. | |

**User's choice:** Conta todas as tentativas (recomendado)

### Onde vive o contador

| Option | Description | Selected |
|--------|-------------|----------|
| Memória do processo (recomendado) | slowapi com backend in-memory: zero infra, zero custo. Zera a cada restart/deploy e vale por processo. | ✓ |
| Banco Neon (tabela) | Sobrevive a restart/deploy e vale para qualquer número de workers, ao custo de uma escrita no banco a cada request e mais uma migração. | |
| Híbrido (memória + teto no banco) | Cobre os dois casos, ao custo de mais uma migração e dois lugares para olhar quando algo der errado. | |

**User's choice:** Memória do processo (recomendado)

### Risco de CGNAT (milhares de celulares num IP)

| Option | Description | Selected |
|--------|-------------|----------|
| Só limite por IP (recomendado) | Limite por IP com Retry-After curto e mensagem pt-BR (já no UI-SPEC). Simples e zero estado extra. | ✓ |
| Limite por IP + cookie anônimo de 1ª parte | O visitante ganha um "crédito" próprio; o scraper esbarra no limite por IP. | |
| Limite por IP + tolerância para IP já bloqueado | IP que já foi bloqueado uma vez passa a receber limite maior. | |

**User's choice:** Só limite por IP (recomendado)
**Notes:** Risco aceito conscientemente (visitantes legítimos de CGNAT carregado podem ser barrados). Anotado em D-09 como ponto de ajuste via env.

### Bucket compartilhado entre reveal e login

| Option | Description | Selected |
|--------|-------------|----------|
| Buckets separados por rota (recomendado) | Um visitante que raspa o reveal não trava o login do master — e o master nunca é afetado pelo tráfego público. | ✓ |
| Um bucket global por IP | Protege o IP como um todo, mas o scrape público pode trancar o master fora do próprio login. | |

**User's choice:** Buckets separados por rota (recomendado)

---

## Chave Turnstile ausente: fail-closed ou fail-open

### Comportamento do app sem chave

| Option | Description | Selected |
|--------|-------------|----------|
| Falha no startup fora de dev (recomendado) | Em ENV != dev, a ausência da chave derruba o startup (igual ao D-05 da Fase 1). Em dev, a chave de teste pública é o default. | ✓ |
| Falha no startup em qualquer ambiente | Mais simples de explicar, mas obriga o dev a configurar a chave de teste à mão antes de rodar qualquer coisa. | |
| Falha por requisição (403 sempre) | O app sobe, mas toda requisição que precisa de Turnstile responde 403. O health check continua verde. | |
| Flag TURNSTILE_ENFORCE (escape hatch) | Existe escape hatch — exatamente o tipo de atalho que alguém liga numa urgência e esquece. | |

**User's choice:** Falha no startup fora de dev (recomendado)

### Segredo default em dev

| Option | Description | Selected |
|--------|-------------|----------|
| Chave de teste em dev + bloqueio de teste em prod (recomendado) | Default em dev = 1x…AA (sempre aprova); em prod o validator rejeita as chaves de teste conhecidas. | ✓ |
| Chave de teste em dev, sem bloqueio em prod | Nada impede que o .env.example seja copiado com a chave de teste: o app sobe, aprova tudo e ninguém percebe. | |
| Dev exige chave real do Cloudflare | Zero chance de chave de teste escapar pra prod, mas ninguém roda o projeto local sem setup. | |

**User's choice:** Chave de teste em dev + bloqueio de teste em prod (recomendado)

### Siteverify fora do ar (rede / HTTP 5xx)

| Option | Description | Selected |
|--------|-------------|----------|
| Falha fechada em qualquer erro (recomendado) | 403 "verificação indisponível" + log de alerta. Scraper nunca passa; o custo é que uma indisponibilidade momentânea bloqueia visitantes legítimos. | ✓ |
| Modo degradado após N falhas | Assume que a Cloudflare está fora e libera o contato, com alerta alto. Fail-open controlado, precisa ser muito bem calibrado. | |
| Falha aberta | Libera o contato durante a indisponibilidade — o scraper também passa, e a fase perde o sentido quando o ataque é mais provável. | |

**User's choice:** Falha fechada em qualquer erro (recomendado)

### Como o master percebe a proteção desligada em produção

| Option | Description | Selected |
|--------|-------------|----------|
| Logs + /health reportando o status (recomendado) | WARNING de startup + error-codes por falha + /health com o status do Turnstile (sem vazar o segredo). | ✓ |
| Só logs | Mais simples, mas o sinal depende de alguém olhar o log. | |
| Logs + /health + banner na área admin | Mais visível para o master, mas mais superfície de frontend nesta fase. | |

**User's choice:** Logs + /health reportando o status (recomendado)

---

## Turnstile no login: sempre ou progressivo

### Exigência do widget no login

| Option | Description | Selected |
|--------|-------------|----------|
| Sempre, incondicional (recomendado) | SECR-03 diz "Turnstile também protege o login" — sem exceções. A senha nunca é checada sem token válido. | ✓ |
| Progressivo: só após 1 senha errada | O master loga sem fricção; o ataque de credential stuffing encontra o widget na segunda tentativa. | |
| Progressivo: só após 3 senhas erradas | Menor fricção, mas o atacante ganha 3 palpites grátis por IP. | |

**User's choice:** Sempre, incondicional (recomendado)

### Aparência do widget na tela de login

| Option | Description | Selected |
|--------|-------------|----------|
| Interaction-only também no login (recomendado) | Mesma escolha do reveal: só aparece se o Turnstile desconfiar. Consistente. | ✓ |
| Checkbox visível no login | Dá ao master a confirmação visual de que a proteção anti-bot está viva. | |

**User's choice:** Interaction-only também no login (recomendado)

### Ordem: senha vs Turnstile no login

| Option | Description | Selected |
|--------|-------------|----------|
| Turnstile antes da senha (recomendado) | A senha nunca é comparada sem token válido (ASVS V2: Turnstile + rate limit in front of bcrypt verify). Custo: senha errada consome o token e o master resolve o widget de novo. | ✓ |
| Senha antes do Turnstile | Erro de senha não gasta o token; o atacante ganha comparações de senha de graça (limitadas a 5/min). | |

**User's choice:** Turnstile antes da senha (recomendado)

### Fallback quando o Turnstile está indisponível no login

| Option | Description | Selected |
|--------|-------------|----------|
| Sem fallback — fail closed (recomendado) | Login recusado com mensagem pt-BR clara; o master sabe que é a Cloudflare, não a senha. Consistente com a decisão de fail-closed. | ✓ |
| Fallback com senha + alerta | O master nunca fica trancado fora — mas o scraper também passa durante a indisponibilidade. | |
| Fallback só em dev | Fallback apenas em dev/CI; em prod, sempre fail closed. | |

**User's choice:** Sem fallback — fail closed (recomendado)

---

## OpenCode's Discretion

- Forma exata da resposta de reveal (nomes dos campos) e se o backend devolve o contato cru ou já com `wa.me`/`mailto`.
- Shape estendido do `/health` e nível de detalhe do warning de startup.
- Estrutura interna de arquivos (`app/core/client_ip.py`, `app/core/ratelimit.py`, `app/services/turnstile.py`) e nomes exatos dos schemas de reveal.
- Nomes exatos dos env vars e formato dos limites.
- Mecânica do `key_func` do slowapi, handler de 429 em pt-BR e reset do store in-memory entre testes.
- Se o `hostname` do Siteverify é checado condicionalmente ou sempre.
- Se `TURNSTILE_SITE_KEY` (backend) é lido do env ou fixado no widget.

## Deferred Ideas

- UI do reveal no frontend (botão "Mostrar contato", modal, cache em memória por vaga, `wa.me`/`mailto`) — **Phase 4** (PUBL-04/PUBL-06), conforme D-01/D-04 e o 03-UI-SPEC.
- Página pública mínima para verificar o reveal de ponta a ponta — **Phase 4** (decidido explicitamente NÃO fazer nesta fase).
- Conta Cloudflare + widget de produção e o plug das env vars no Vercel/Railway — **Phase 6** (deploy).
- Limiter distribuído (Redis ou tabela) se o backend sair de 1 worker — **Phase 6**.
- Denúncia de vaga / relatório de abuso (TRST-02) e páginas legais (TRST-03) — **Phase 6**.
- Higiene de tooling: `uv` ausente no ambiente, `uv.lock` do backend sem regeneração — dívida já registrada no STATE.md.
