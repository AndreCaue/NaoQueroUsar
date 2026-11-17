# Feature Research

**Domain:** Chatbot de busca de vagas por linguagem natural (NL job search) em job board/agregador existente
**Researched:** 2026-11-17
**Confidence:** MEDIUM (síntese de padrões comuns do domínio; buscas web retornaram indisponíveis neste ambiente — validar com referências de produto durante planejamento)

## Contexto e escopo (milestone v1.3)

Subsequente ao EmpregaNoix (board público sem login). **Já existe:** busca keyword `q` (título/empresa/atividades/requisitos), filtro cidade (SP, RJ, BH, Remoto), ordenação por data, paginação, modal/detalhe, revelação protegida de contato, curadoria/admin e pipeline de extração.

**Foco exclusivo das novas features:** interface de chat para busca em linguagem natural, extração de parâmetros (cargo, senioridade, cidade, remoto/híbrido/presencial, faixa salarial, tipo de contrato, palavras-chave), aplicação nos filtros/busca existentes, retorno de vagas relevantes, combinações de filtros e “vagas parecidas” (limitado/futuro conforme viável). **Restrição crítica:** o LLM **não** recebe centenas de vagas — apenas extrai parâmetros/intenção para JSON estruturado e validado.

## Feature Landscape

### Table Stakes (Users Expect These)

Recursos que usuários assumem existir em um chat de busca de vagas. Ausência faz o recurso parecer quebrado ou inútil.

| Feature | Why Expected | Complexity | Notes / Dependencies on existing |
|---------|--------------|------------|----------------------------------|
| Entrada em linguagem natural (pt-BR) com envio rápido | Usuário espera “digitar como fala” em vez de montar filtros manualmente | LOW | UI (drawer/modal) client-side; texto livre enviado ao endpoint de chat-search. Depende apenas de novo componente frontend. |
| Extração de intenção/parâmetros para JSON estruturado e validado | Padrão de NL-to-search: converter frase em filtros executáveis sem inventar dados | MEDIUM | LLM (Groq, reuso/baixo custo) + schema rígido (Pydantic/Zod) + defaults seguros. **Sem corpus de vagas no prompt.** Campos-alvo: cargo, senioridade, cidade (whitelist), modalidade, faixa salarial, tipo contrato, palavras-chave, ordenação. |
| Aplicação segura à busca/filtros existentes | Resultado precisa refletir o que o usuário pediu usando a fonte de verdade atual | MEDIUM | Mapear para `GET /api/v1/public/jobs` / `crud.list_published` (`q`, cidade, sort, paginação). Normalizar cidade para whitelist (SP/RJ/BH/Remoto); ignorar/avisar valores fora. Dependência direta do comportamento atual de `q` e filtros. |
| Exibição do que o sistema entendeu (parâmetros interpretados) | Transparência: usuário confia quando vê filtros aplicados e pode corrigir | LOW | Mostrar chips/resumo (cargo, cidade, modalidade etc.) na UI do chat. Não requer mudança de backend além de retornar interpretação. |
| Lista de resultados relevantes no próprio chat com acesso ao detalhe | Expectativa de “perguntei e vi vagas” sem sair do fluxo | LOW-MEDIUM | Reusar cards/lista compacta e abrir modal/detalhe existente; payload público `JobPublic` **sem contatos** (revelação protegida continua no fluxo atual). |
| Suporte a combinações básicas de filtros na mesma frase | Consultas reais misturam atributos (“dev jr remoto SP”) | MEDIUM | Depende de extração multi-slot + merge correto com `q`/city/sort. Campos não nativos (salário/modalidade/contrato) exigem estratégia incremental (mapeamento textual em `q`, pós-filtro controlado no subconjunto retornado, ou extensão limitada de filtros) — documentar lacunas. |
| Resposta quando não há resultados (empty state útil) | Comportamento esperado em busca; evita tela “morta” | LOW | Mensagem clara + sugestão de relaxar filtros (ex.: ampliar cidade/remover senioridade). UI apenas. |
| Baixa latência percebida e estados de carregamento/erro | Chat lento ou silencioso parece quebrado | MEDIUM | Timeout no endpoint, loading indicator, mensagens de erro amigáveis/rate-limit. Proteções básicas (rate limit/timeout) no endpoint público. |
| Preservação de privacidade/fricção zero | Core value do produto: sem login para buscar | LOW | Endpoint público; sem histórico persistente obrigatório no MVP; não pedir cadastro. Contato continua protegido pelo mecanismo existente. |

### Differentiators (Competitive Advantage)

Recursos que melhoram conversão/confiança além do básico, alinhados ao core value (“encontrar vaga e contato em segundos, sem fricção”).

| Feature | Value Proposition | Complexity | Notes / Dependencies on existing |
|---------|-------------------|------------|----------------------------------|
| Interpretação tolerante a variações pt-BR e gírias leves (ex.: “home office”, “CLT”, “estágio”) | Reduz esforço do usuário mobile e aumenta recall sem cadastro/configuração | MEDIUM | Léxico/sinônimos e normalização no prompt/schema (modalidade/contrato/senioridade); mapear para termos buscáveis no `q` quando não houver coluna dedicada. |
| Refinamento conversacional leve na mesma sessão (ajustar pedido) | Permite “na verdade em BH” sem recomeçar, mantendo rapidez | MEDIUM | Manter contexto curto no frontend (últimos parâmetros) e reenviar; sem memória server-side longa no MVP. Depende de UX do drawer/modal. |
| Sugestões de “vagas parecidas” quando busca exata é fraca (limitado) | Evita dead-end e ajuda descoberta, comum em buscadores modernos | MEDIUM-HIGH | **Escopo limitado/futuro:** relaxar 1 constraint por vez (ex.: remover cidade específica mantendo `q`, ou ampliar keywords) usando queries existentes; **não** usar embeddings/LLM sobre corpus no MVP. Rotular como “sugestões próximas”. |
| Resumo curto do porquê dos resultados (grounded nos parâmetros) | Aumenta confiança de que o match veio dos filtros, não “mágica” opaca | LOW | Templatear texto a partir dos parâmetros extraídos/efetivamente aplicados (sem LLM adicional no resultado). |
| Atalhos/exemplos de consulta (chips) no chat vazio | Onboarding instantâneo sem tutorial; útil para mobile | LOW | UI estática alinhada aos exemplos de MVP do milestone. |

### Anti-Features (Commonly Requested, Often Problematic)

Recursos que parecem bons, mas conflitam com restrições do produto (custo, performance, sem login, LLM sem corpus).

| Feature | Why Requested | Why Problematic | Alternative |
|---------|---------------|-----------------|-------------|
| Enviar lista de centenas de vagas ao LLM para “escolher as melhores” | Parece mais “inteligente”/semântico | Viola restrição explícita; alto custo/latência; risco de alucinação e vazamento de dados desnecessário | LLM só extrai parâmetros → busca determinística no backend (`list_published`/filtros). “Parecidas” via relaxamento controlado de filtros. |
| Ranking semântico/embeddings completos no MVP | Melhor matching além de keyword | Infra/custo/complexidade (índice vetorial, pipeline) desproporcional ao volume (100–500/mês) e ao milestone | Melhorar normalização de keywords/sinônimos e relaxamento de filtros; considerar embeddings em milestone futuro se métricas justificarem. |
| Chatbot multi-turn longo com memória persistente por usuário | Experiência “assistente pessoal” | Exige identificação/armazenamento, aumenta custo e complexidade; conflita com fricção zero | Contexto efêmero de sessão no cliente (última interpretação) e refinamentos curtos. |
| Clarifying questions obrigatórias antes de buscar | Máxima precisão de slots | Adiciona atrito; usuários querem resultado rápido | Buscar imediatamente com melhor esforço + mostrar parâmetros entendidos + permitir ajuste rápido. Perguntar só em casos extremos de ambiguidade total (opcional). |
| Agente que “se candidata”/envia mensagens em nome do usuário | Automação total | Fora de escopo, riscos legais/spam, exige integrações e contas | Manter fluxo atual: encontrar vaga e revelar contato para candidatura manual. |
| Inventar/normalizar salário, empresa ou modalidade ausentes nos dados | Preencher lacunas para parecer completo | Quebra confiança e pode induzir erro; dados vêm de curadoria | Exibir apenas campos disponíveis (`JobPublic`); parâmetros não suportados devem ser declarados como limitação na resposta. |
| Expor contatos no payload/resposta do chat | Conveniência | Contraria proteção anti-scraping/fluxo de revelação existente | Retornar `JobPublic` sem contatos; “ver contato” usa mecanismo protegido atual no detalhe. |

## Feature Dependencies

```
[Schema de extração + validação + normalização pt-BR/whitelist]
    └──requires──> [LLM provider/estratégia (Groq) + prompt/JSON]
                         └──requires──> [Config/env, timeout, tratamento de falhas]

[Endpoint público chat-search (interpretação + resultados)]
    └──requires──> [Schema de extração]
    └──requires──> [Busca pública existente: GET /api/v1/public/jobs / crud.list_published (q, city, sort, paginação)]
    └──requires──> [Rate limit/timeout/proteção básica]

[Aplicação de parâmetros não nativos (salário/modalidade/contrato)]
    └──requires──> [Decisão incremental: mapear para q / pós-filtro / extensão controlada]
    └──enhances──> [Combinações de filtros na mesma frase]

[UI de chat (drawer/modal mobile-first)]
    └──requires──> [Endpoint público chat-search]
    └──requires──> [Componentes de lista/card/modal/detalhe existentes]
    └──requires──> [Fluxo de revelação de contato existente (sem expor no payload)]

[“Vagas parecidas” (limitado)]
    └──requires──> [Busca existente + lógica de relaxamento de constraints]
    └──conflicts──> [Embeddings/ranking LLM sobre corpus no MVP]
```

### Dependency Notes

- **Endpoint chat-search requires busca existente:** a consulta determinística deve reutilizar `list_published`/filtros atuais para garantir consistência, paginação e regras de publicação/expiração.
- **Extração requires validação rígida:** nunca confiar em saída livre do LLM; validar tipos/enums/whitelist e descartar campos inventados.
- **Parâmetros não nativos enhances combinações:** salário/modalidade/contrato podem não ter colunas/filtros nativos hoje — sem estratégia incremental, combinações que os incluam degradam silenciosamente; é necessário declarar aplicação parcial.
- **UI requires fluxo de contato existente:** chat pode levar ao detalhe, mas não pode substituir/contornar a revelação protegida.
- **“Vagas parecidas” conflicts com LLM-sobre-corpus:** aproximação deve ser por relaxamento determinístico, não por re-ranking com todas as vagas no prompt.

## MVP Definition

### Launch With (v1.3)

Mínimo para validar busca NL sem fricção, respeitando custo/performance e reuso da busca existente.

- [ ] **Extração NL → JSON validado (sem inventar)** — cargo, senioridade, cidade whitelist, modalidade, remoto/híbrido/presencial, faixa salarial, tipo contrato, palavras-chave, ordenação; normalização segura e descarte de fora do domínio.
- [ ] **Endpoint público de chat-search** — recebe texto, aplica timeout/rate limit, retorna interpretação + resultados pagináveis (`JobPublic`) com erros/empty states tratados.
- [ ] **Mapeamento para busca existente** — aplicar `q`/cidade/sort/paginação em `list_published`; estratégia incremental explícita para campos não nativos (ex.: incluir termos no `q` e/ou pós-filtro controlado) com lacunas documentadas na resposta.
- [ ] **UI de chat (drawer/modal mobile-first)** — entrada, loading/erro, exibição de parâmetros entendidos e lista de vagas com acesso a detalhe/link; exemplos de consulta do MVP.
- [ ] **Cobertura dos exemplos de uso do MVP** — validar combinações definidas; registrar quais parâmetros são suportados total/parcialmente.

### Add After Validation (v1.x)

- [ ] **Refinamento conversacional leve** — reutilizar última interpretação no cliente para ajustes rápidos (“só remoto”, “muda para RJ”). Trigger: usuários repetem buscas do zero.
- [ ] **“Vagas parecidas” via relaxamento determinístico** — remover/afrouxar 1 constraint e sinalizar aproximação. Trigger: alta taxa de zero resultados em consultas válidas.
- [ ] **Telemetria mínima de qualidade (agregada, sem PII)** — contagem de buscas, taxa de vazio, uso de sugestões. Trigger: necessidade de calibrar prompt/mapeamentos.

### Future Consideration (v2+)

- [ ] **Busca semântica/embeddings** — adiar até volume/qualidade justificar custo/infra; requer pipeline de indexação e avaliação.
- [ ] **Suporte nativo a salário/modalidade/contrato no modelo/filtros** — evolução de schema/índices se campos se tornarem estruturados e confiáveis na curadoria.
- [ ] **Memória/histórico opt-in** — exigiria decisões de identidade/privacidade; conflita com fricção zero no curto prazo.

## Feature Prioritization Matrix

| Feature | User Value | Implementation Cost | Priority |
|---------|------------|---------------------|----------|
| Extração NL → JSON validado (LLM só parâmetros) | HIGH | MEDIUM | P1 |
| Endpoint chat-search + rate limit/timeout + mapeamento à busca existente | HIGH | MEDIUM | P1 |
| UI chat com parâmetros entendidos + resultados (`JobPublic`) + detalhe | HIGH | MEDIUM | P1 |
| Combinações de filtros com estratégia para campos não nativos (parcial documentado) | HIGH | MEDIUM-HIGH | P1 |
| Empty states, erros e baixa latência percebida | MEDIUM | LOW-MEDIUM | P1 |
| Refinamento leve de contexto no cliente | MEDIUM | MEDIUM | P2 |
| “Vagas parecidas” por relaxamento determinístico (limitado) | MEDIUM | MEDIUM | P2 |
| Chips/exemplos e resumo grounded dos filtros aplicados | MEDIUM | LOW | P2 |
| Telemetria agregada de qualidade | MEDIUM | LOW-MEDIUM | P3 |
| Busca semântica/embeddings/ranking por LLM sobre corpus | MEDIUM | HIGH | P3 (anti-feature no MVP) |

**Priority key:**
- P1: Must have for launch (v1.3)
- P2: Should have, add when possible
- P3: Nice to have, future consideration

## Competitor Feature Analysis

| Feature | Padrão em job boards/assistentes (Indeed, LinkedIn, Google Jobs e chats de busca) | Nosso enfoque (EmpregaNoix v1.3) |
|---------|----------------------------------------------------------------------------------|----------------------------------|
| Entrada NL | Barra/chat aceita frases; alguns sugerem prompts | Chat simples pt-BR em drawer/modal, mobile-first, sem login |
| Extração de filtros | Inferência de cargo/local/remoto/senioridade; nem sempre transparente | JSON estruturado validado, **LLM não vê vagas**, mostrar parâmetros entendidos |
| Aplicação de filtros | Mapeamento para facets/filtros nativos da plataforma | Reuso de `GET /api/v1/public/jobs`/`list_published`; incremental para campos não nativos com lacunas explícitas |
| Resultados | Lista ranqueada com resumo e link/detalhe | `JobPublic` sem contato + acesso a modal/detalhe e revelação protegida existente |
| Refinamento | Follow-ups ajustam busca; às vezes exige conta para salvar | Refinamento leve sem persistência/conta (P2) |
| “Vagas parecidas” | Recomendações/semântica/ML em grande escala | Apenas relaxamento determinístico limitado (P2/futuro), sem corpus no LLM |
| Privacidade/atrito | Frequentemente empurra login/alertas | Zero fricção: buscar e ver resultados sem cadastro (core value) |

## Sources

- `.planning/PROJECT.md` (contexto do produto, milestone v1.3, restrições e busca existente) — HIGH (primário)
- Conhecimento de domínio sobre padrões de NL search/slot filling em job boards e chatbots de busca (intent → structured filters → retrieval → apresentação) — MEDIUM, **não verificado com fontes externas neste ambiente** (ferramenta de websearch sem resultados)
- Recomendação: validar durante planejamento com documentação/comportamento público de buscadores de vagas (ex.: Google Jobs, Indeed, LinkedIn) e testes com usuários pt-BR

---
*Feature research for: Chatbot de busca de vagas por linguagem natural (EmpregaNoix v1.3)*
*Researched: 2026-11-17*
