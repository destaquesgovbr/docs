---
date: 2026-06-30
authors:
  - nitai
categories:
  - MCP
  - IA
  - Infraestrutura
  - Analytics
title: "Gobus MCP: um agente que investiga o gov.br — do Cloud Run ao forecast"
hide:
  - toc
---

# Gobus MCP: um agente que investiga o gov.br — do Cloud Run ao forecast

Em pouco menos de duas semanas — de 19 de junho a 1 de julho de 2026 — a plataforma DGB ganhou uma nova porta: o **Gobus MCP**, um servidor que abre todo o acervo enriquecido de notícias do governo a agentes de IA como o Claude. Não é mais um endpoint humano; é uma interface para uma máquina que raciocina. Com ele, um agente passou a poder perguntar "o que o MEC comunicou esta semana?", "essa política está em qual fase?", "há algum pico anômalo de cobertura?" e "quais temas devem crescer nos próximos dias?" — e responder consultando dados reais, não a própria memória. Este post conta o nascimento do Gobus: as quatro queries GraphQL que o alimentam, o provisionamento no Cloud Run, o site de documentação, as duas fases de capacidades analíticas, e — o fio mais honesto da história — a saga do transporte, um bug de sessão que só apareceu quando subagentes começaram a usar o servidor de verdade.

<!-- more -->

## O que é MCP, e por que o gov.br precisa dele

O **Model Context Protocol (MCP)** é um protocolo aberto que deixa um agente de IA usar ferramentas e consultar dados externos de forma padronizada e segura — em vez de cada integração ser costurada à mão, o agente "descobre" o que pode fazer e chama funções bem definidas. Na prática: o Claude conectado ao Gobus enxerga um catálogo de _tools_ (ações), _resources_ (dados) e _prompts_ (fluxos guiados), e escolhe o que usar para responder à pergunta do usuário.

O desenho do Gobus tem uma regra de ouro: **o MCP consulta exclusivamente o GraphQL**. Nada de acesso direto a Postgres, Typesense ou Neo4j. O servidor MCP é uma camada fina de tradução — a inteligência de dados continua vivendo atrás do `graphql-api`, o caminho único consolidado no [post anterior](2026-06-18-grafo-entidades-backfill-neo4j.md).

```
   Claude / agente de IA
        │  MCP  (tools · resources · prompts)
        ▼
   ┌──────────────────┐
   │    Gobus MCP      │   Cloud Run · southamerica-east1
   │    (FastMCP)      │   SA dedicada: run.invoker (mínimo)
   └────────┬─────────┘
            │  GraphQL  (ÚNICO caminho de leitura)
            ▼
   ┌──────────────────┐
   │    graphql-api    │
   └────────┬─────────┘
            │
      ┌─────┼───────────┬────────────┐
      ▼     ▼           ▼            ▼
   Postgres Typesense  Neo4j     embeddings
```

## As queries que alimentam o Gobus

Antes do servidor existir, o GraphQL precisou aprender a falar a língua da análise. Foram adicionadas **4 novas queries** ([graphql-api#20](https://github.com/destaquesgovbr/graphql-api/pull/20)), cada uma sustentando um tipo de investigação que o agente faria:

- **`agencyAnalytics`** — métricas de publicação por agência e período (via `DATE_TRUNC GROUP BY` no Postgres): volume, sentimento e legibilidade, na granularidade DAY / WEEK / MONTH.
- **`trendingThemes`** — temas em crescimento, comparando duas janelas do Typesense (recente vs. baseline), com `growth_score = window_daily / baseline_daily`.
- **`entityCoverage`** — série temporal de menções de uma entidade canônica por agência (`news_entities JOIN news`).
- **`entitySearch`** — resolução _fuzzy_ de nomes de entidade: match exato em `entity_alias` em UNION com `pg_trgm` sobre o `entity_registry`, ordenado por confiança.

Essas quatro queries são o pré-requisito de tudo o que veio depois — o Gobus só é tão capaz quanto o schema que consulta. A entrega chegou com **13 testes** passando localmente cobrindo os novos resolvers de analytics e de entidades.

## Do Terraform ao ar: o Cloud Run e os quatro fixes de infra

O servidor foi provisionado inteiramente por Terraform ([infra#206](https://github.com/destaquesgovbr/infra/pull/206)): um serviço Cloud Run `destaquesgovbr-gobus-mcp` em `southamerica-east1`, com uma **service account dedicada** de permissão mínima — apenas `roles/run.invoker` na `graphql-api`, nada além. Um Artifact Registry próprio (com imagem placeholder, para o CI/CD do repo `gobus-mcp` substituir), a URL da `graphql-api` injetada por referência (sem hardcode), acesso público via HTTPS (a autenticação fica a cargo do cliente MCP) e **sem `min_instances`** — escala a zero quando ninguém está investigando.

O primeiro obstáculo apareceu no CI, não na aplicação. O deploy falhava com `Permission 'iam.serviceAccounts.getAccessToken' denied`: o repositório `gobus-mcp` simplesmente não estava registrado no **Workload Identity Federation** como caller autorizado. A correção seguiu o mesmo padrão de todos os outros repos e liberou o primeiro deploy real ([infra#207](https://github.com/destaquesgovbr/infra/pull/207)).

Depois vieram três fixes que só a operação revelou — o tipo de detalhe que nenhum tutorial antecipa:

!!! warning "Cada `terraform apply` desfazia o deploy"
    A imagem do serviço voltava sozinha para o placeholder `hello:latest` a cada `apply`, apagando o que o CI/CD havia publicado — a revisão em produção rodava o placeholder apesar de existir imagem real no Artifact Registry. A causa: o Terraform gerencia a **configuração** do serviço, mas o CI/CD gerencia a **imagem**. A solução é o padrão canônico para esse conflito — `lifecycle { ignore_changes = [template[0].containers[0].image] }` ([infra#209](https://github.com/destaquesgovbr/infra/pull/209)). O mesmo PR removeu a env var `MCP_TRANSPORT=sse`, já ignorada pelo `server.py` desde o fix de uma race condition — o transporte passou a ser determinado pelo `PORT` que o Cloud Run injeta.

Os outros dois fixes de infra são inseparáveis da história do transporte — e é para ela que vamos agora.

## A saga do transporte: um 404 que só os subagentes viam

Este é o fio mais instrutivo da entrega. O Gobus nasceu com transporte **SSE** (Server-Sent Events), e SSE é _stateful_: cada cliente abre uma sessão cujo ID vive na **memória de uma instância**. Isso tem uma consequência imediata em Cloud Run — se houver mais de uma instância, o `POST /messages/` pode cair numa instância diferente da que abriu o `GET /sse`, e o protocolo estoura com `-32602`. A defesa foi limitar o serviço a **`max_instance_count = 1`** ([infra#210](https://github.com/destaquesgovbr/infra/pull/210)): uma instância só, sessão sempre em casa.

Funcionou — até os subagentes entrarem em cena.

!!! warning "HTTP 404 — Could not find session"
    Subagentes que faziam **múltiplas chamadas MCP sequenciais** falhavam na segunda com `404 Could not find session` ([gobus-mcp#4](https://github.com/destaquesgovbr/gobus-mcp/issues/4)). O padrão era cruel: a primeira chamada estabelecia a sessão e funcionava; entre uma chamada e outra o stream SSE de um subagente efêmero fechava; a segunda chamada não achava mais a sessão. Na sessão principal do Claude Code tudo ia bem, porque o cliente mantém o stream aberto de forma persistente. Além disso, todo deploy invalidava todas as sessões ativas de uma vez.

A primeira reação foi um paliativo de infra: o timeout default do Cloud Run é de **300s (5 min)**, e ele encerrava a stream SSE justamente durante sessões de subagente com chamadas espaçadas. O timeout foi elevado para **3600s**, o máximo suportado pela plataforma ([infra#211](https://github.com/destaquesgovbr/infra/pull/211)). Ajudou, mas não curou a doença — o problema não era o tempo, era o **estado em memória**.

O plano de cura óbvio era migrar para **streamable-http**, o transporte _stateless_ do FastMCP 3.x, onde cada request é independente. Mas a primeira tentativa (commit `8588d02`) bateu num muro de compatibilidade: o FastMCP 3.x fala a spec MCP **2025-03-26** (baseada em POST), enquanto o cliente do Claude Code daquele momento falava a spec **2024-11-05** (GET + SSE). Incompatibilidade total — o servidor novo não conversava com o cliente existente.

A saída foi engenhosa: **servir os dois protocolos ao mesmo tempo** ([gobus-mcp#5](https://github.com/destaquesgovbr/gobus-mcp/pull/5)). Com o salto de FastMCP 2.9 → 3.x e a flag `stateless_http=True`, o `/mcp` passou a processar cada POST de forma independente — sem session ID, sem expiração. E o `/sse` legado foi mantido para compatibilidade, implementado manualmente com um `SseServerTransport` registrado como `custom_route` (o FastMCP 3.x não cria o `/sse` sozinho):

| Endpoint | Spec | Comportamento |
|---|---|---|
| `/mcp` | 2025-03-26 | Stateless HTTP: cada POST independente, sem sessão |
| `/sse` | 2024-11-05 | SSE stream + POST `/messages` (backward-compat) |

O `.mcp.json` passou a apontar para `/mcp`, com o `/sse` como rede de segurança caso o cliente ainda não suportasse a spec nova. A entrega chegou com **48 testes** unitários verdes.

E o desfecho — o mais honesto de todos. Depois de toda essa engenharia de transporte HTTP, a resposta prática para o Claude Code acabou sendo **rodar o MCP em modo `stdio` local**, porque os endpoints HTTP ainda tinham bugs no CLI. A issue [gobus-mcp#4](https://github.com/destaquesgovbr/gobus-mcp/issues/4) foi fechada como _wontfix_, com o `stdio` local documentado como transporte recomendado ([gobus-mcp#6](https://github.com/destaquesgovbr/gobus-mcp/pull/6)). O trabalho no dual transport não foi perdido — deixou o servidor pronto para o dia em que o HTTP stateless for a via padrão, e liberou conceitualmente o `max_instance_count=1`. Mas a lição ficou: **a arquitetura mais elegante nem sempre é a que o cliente do dia consegue usar.**

!!! tip "Para conectar no Claude Code hoje"
    O caminho recomendado é `stdio` local — sem sessão que expira, sem stream que cai entre chamadas de subagente. Os endpoints HTTP (`/mcp` e `/sse`) continuam disponíveis para clientes remotos.

## Fase 1 e Fase 2: de leitor a analista

Com o transporte domado, o Gobus deixou de ser só um leitor de notícias e virou um analista. Duas fases, ambas construídas com **TDD obrigatório** (testes antes da implementação) e ancoradas nos achados do EXPERIMENTO_V3.

**Fase 1** ([gobus-mcp#6](https://github.com/destaquesgovbr/gobus-mcp/pull/6)) trouxe capacidades de legibilidade e de políticas públicas:

- `gobus_get_readability_recommendations(agency_key, days, limit)` — diagnóstico de legibilidade por agência, com o gap até a meta Flesch e recomendações de estilo.
- `gobus_get_policy_lifecycle(policy_name, date_from)` — o ciclo de vida comunicacional de uma política pública: fases, âncoras narrativas e em que fase ela está agora.
- Um MCP App novo, `ui://readability-dashboard` — um dashboard HTML/SVG autocontido, sem CDN externo.

**Fase 2** ([gobus-mcp#7](https://github.com/destaquesgovbr/gobus-mcp/pull/7)) fechou o arco do título — do Cloud Run ao **forecast** — com 3 tools e 2 resources:

- `gobus_detect_anomalies(sensitivity)` — detecta **picos sustentados** (temas que crescem em ambas as janelas 3d/21d e 7d/28d) e **cobertura concentrada** (entidades com alto `volumeRatio` e poucas agências cobrindo), com limiares por sensibilidade high / medium / low.
- `gobus_forecast_trends(horizon_days, limit)` — um score composto ponderado sobre 3 janelas (3d / 7d / 21d), com **momentum** (acelerando / desacelerando / estável) e **confiança** (nº de janelas que concordam). Traz até uma nota sobre o viés de borda de fim de semana na janela de 3 dias.
- `gobus_score_article(unique_id)` — uma nota editorial de 0 a 10, combinando **legibilidade (50%) + concisão (30%) + densidade de entidades (20%)**, comparada ao benchmark de 90 dias da própria agência.
- `gobus://readability-report` — JSON de legibilidade por agência, ordenado pelo gap até a meta (Flesch 50).
- `gobus://health/pipelines` — health-check dos pipelines frágeis (trendingScore, sentimento, legibilidade): `OK | DEGRADED | DEAD`.

A Fase 2 rendeu **15 testes novos**, chegando a **90 no total** (red→green). E deixou uma armadilha documentada: o blueprint pedia `trendingThemes { label baselineCount }`, mas a introspecção do schema real mostrou `themeLabel` e `baselineDailyAvg`. As queries foram escritas com os nomes reais — porque um blueprint desatualizado quebra em runtime, não em tempo de build.

## O agente precisa aprender a usar as ferramentas

Ter tools não basta. Uma investigação sobre o estado da arte de agentes que consomem MCP (jun/2026) apontou um problema surpreendente: **o MCP entrega o _quê_, mas não o _quando_ e o _como_** ([gobus-mcp#2](https://github.com/destaquesgovbr/gobus-mcp/issues/2)). Um agente "limpo", sem system prompt, conectado ao Gobus tem acesso a todas as tools — mas não sabe encadeá-las na ordem certa.

O dado que mais chama atenção veio de um paper (arxiv 2602.14878): **97,1% das descrições de tools MCP têm problemas**, e **56% não descrevem sequer o propósito com clareza**. Como a string de `description` é o principal sinal que o modelo usa para escolher a tool e os argumentos, descrições vagas levam direto a chamadas erradas. A issue estabeleceu quatro alavancas de melhoria:

1. **Auditar as descrições** das tools contra 6 componentes — propósito, parâmetros, retorno, efeitos colaterais, exemplos e restrições — com atenção especial a pré-condições (ex.: `resolve_entity` é pré-requisito de qualquer operação de entidade).
2. **Uma skill host-side** (`.claude/skills/gobus.md`) que ensina o agente _quando_ acionar cada fluxo — o mapa UC → tool principal → tools auxiliares — sem depender de o usuário conhecer os nomes dos prompts.
3. **Controlar o tamanho do contexto** em respostas grandes — um `max_nodes` (default 20) em `get_entity_network` e um `summary_only` em `get_entity_profile`.
4. **Instruir paralelismo explícito** nos prompts — chamadas independentes (como `search_news` + `get_agency_analytics`) podem rodar em paralelo, e o prompt deve dizer isso.

É a diferença entre publicar uma API e projetar uma **experiência de agente**.

## A casa da documentação

Um servidor para IA precisa de documentação para humanos. O repo `gobus-mcp` ganhou um site MkDocs Material co-localizado, no mesmo padrão da `graphql-api` — **20 páginas** cobrindo as 7 tools, 3 resources e 4 prompts, além de casos de uso, arquitetura e deploy, com build limpo sob `mkdocs build --strict` ([gobus-mcp#1](https://github.com/destaquesgovbr/gobus-mcp/pull/1)). E a documentação central ganhou um módulo dedicado, com diagrama Mermaid do fluxo Claude ↔ Gobus MCP ↔ graphql-api, tabela de capacidades e snippets de conexão (HTTP em produção e `stdio` local) ([docs#53](https://github.com/destaquesgovbr/docs/pull/53)).

!!! note "As contagens crescem por fase"
    O site (7 tools · 3 resources · 4 prompts) retrata o Gobus no seu lançamento. As Fases 1 e 2 acrescentaram 5 tools e 2 resources a essa superfície — a documentação profunda acompanha em [destaquesgovbr.github.io/gobus-mcp](https://destaquesgovbr.github.io/gobus-mcp/).

## Antes e depois

| | Antes | Depois |
|---|---|---|
| Acesso de IA ao acervo gov.br | inexistente | servidor MCP (tools · resources · prompts) |
| Caminho de dados do MCP | — | só GraphQL (sem Postgres/Typesense/Neo4j direto) |
| Transporte | SSE stateful, sessão em memória | `/mcp` stateless + `/sse` legado; `stdio` local para o CLI |
| Subagentes com N chamadas | 404 na 2ª chamada | funciona (stdio / stateless) |
| Timeout Cloud Run | 300s (matava a stream) | 3600s (máximo) |
| Deploy vs. Terraform | `apply` resetava a imagem | `ignore_changes` na imagem |
| Capacidades | leitura de notícias | + legibilidade, políticas, anomalias, forecast, score |

## Números

| Métrica | Valor |
|---|---|
| Novas queries GraphQL | **4** ([graphql-api#20](https://github.com/destaquesgovbr/graphql-api/pull/20)) |
| Tools MCP | 7 iniciais · +2 na Fase 1 · +3 na Fase 2 |
| Resources · Prompts | 3 (+2 na Fase 2) · 4 |
| Testes | 13 (graphql-api) · 48 (dual transport) · **90** no total (gobus-mcp) |
| Specs MCP suportadas | `2025-03-26` (/mcp) + `2024-11-05` (/sse) |
| Timeout Cloud Run | 300s → **3600s** |
| Instâncias Cloud Run | `max_instance_count = 1` (SSE stateful) |
| Páginas de documentação | **20** ([gobus-mcp#1](https://github.com/destaquesgovbr/gobus-mcp/pull/1)) |
| Qualidade de descrições de tools (paper) | 97,1% com problemas · 56% sem propósito claro |
| Região · Runtime | `southamerica-east1` · Cloud Run · FastMCP 3.x |

## Lições

1. **A regra "só GraphQL" pagou dividendos.** Manter o MCP sem acesso direto aos bancos fez do servidor uma camada fina e substituível — toda a lógica de dados continua num único ponto auditável, e o Gobus herda de graça tudo o que o `graphql-api` já sabe.
2. **O bug de sessão só existia com o usuário real.** SSE stateful funcionava na sessão principal e desmoronava em subagentes efêmeros. Nenhum teste unitário pegaria isso — foi preciso um agente de verdade, fazendo chamadas espaçadas, para o `404 Could not find session` aparecer.
3. **A arquitetura elegante nem sempre é a viável hoje.** O dual transport foi a solução tecnicamente correta, mas o que destravou o Claude Code foi o pragmático `stdio` local. Vale construir para o futuro _e_ desbloquear o presente.
4. **Terraform gerencia config; CI/CD gerencia imagem.** Sem `ignore_changes` na imagem, cada `apply` desfazia silenciosamente o deploy. É o padrão canônico quando duas automações tocam o mesmo recurso.
5. **Um blueprint desatualizado quebra em runtime.** Confiar no `themeLabel`/`baselineDailyAvg` reais em vez do `label`/`baselineCount` do documento evitou uma falha que só apareceria com o agente já em produção — a introspecção do schema é a fonte da verdade.
6. **Dar tools ao agente é metade do trabalho.** As descrições, a skill host-side e os hints de paralelismo são o que transforma um catálogo de funções numa experiência de agente que de fato investiga o gov.br.

O Gobus saiu do zero a um analista com forecast em menos de duas semanas. O próximo passo do arco é colocar essas capacidades a serviço de perguntas reais — entidades em alta, o ciclo de vida das políticas públicas e o fechamento do trabalho iniciado aqui.

---

*Série **A evolução da plataforma DGB (jun–jul 2026)** · post 3 de 4.*
*Post anterior: [O grafo do gov.br](2026-06-18-grafo-entidades-backfill-neo4j.md) · Próximo post: [Entidades em alta, políticas públicas e o fechamento do ciclo](2026-07-03-entidades-alta-politicas-fechamento.md).*
