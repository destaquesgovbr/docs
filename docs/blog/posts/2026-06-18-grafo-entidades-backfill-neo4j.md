---
date: 2026-06-18
authors:
  - nitai
categories:
  - Grafo
  - Infraestrutura
  - Data Engineering
  - Entidades
title: "O grafo do gov.br: entidades em Neo4j e o backfill retroativo com governador de cota"
hide:
  - toc
---

# O grafo do gov.br: entidades em Neo4j e o backfill retroativo com governador de cota

Com as entidades canônicas em mãos — cada órgão, lei, política e pessoa reduzido a um `canonical_id` estável, muitos deles já ancorados num QID da Wikidata — faltava fazer duas coisas com elas. A primeira: projetá-las num **grafo**, para que "quem aparece com quem" deixasse de ser uma consulta ad-hoc e virasse uma estrutura navegável, no Postgres e num **Neo4j** dedicado, servida ao portal como entidades relacionadas e uma rede ego-centrada. A segunda, bem mais dura: rodar um **backfill retroativo** sobre toda a base histórica — os ~314 mil artigos que nunca passaram pelo NER canônico — sem estourar o teto diário de tokens da AWS Bedrock. Em cerca de três dias intensos, a plataforma ganhou o grafo (Fases 6a–6d) e transformou o reprocessamento numa operação de guerra controlada por um **governador de cota**, com direito a dois tropeços de permissão, uma quota que se descobriu fictícia, um limite real da AWS confirmado na marra e uma sequência de falsos-positivos de sigla que só apareceram rodando em escala de produção.

<!-- more -->

## Onde paramos

O post anterior fechou a canonicalização de entidades: a plataforma passou a colapsar variantes de nome numa entidade única e a ancorá-la, quando possível, na Wikidata. Isso resolve o "o quê" (a identidade de cada entidade), mas não o "com quem" — a relação entre entidades continuava implícita, espalhada linha a linha dentro de `news_features`. As duas frentes deste ciclo atacam exatamente esse vazio: uma **projeta as relações num grafo**; a outra **aplica a canonicalização a todo o passado**, porque um grafo construído só com as notícias novas seria um grafo torto, cego para quase toda a história do gov.br.

---

## Salto 1: projetar as entidades num grafo (Fase 6)

A projeção foi quebrada em quatro fases coordenadas — dados, infra, API e UI — para que cada peça pudesse subir com um deploy pequeno e verificável.

```
  news_features (menções por artigo)
        │  DAG project_entity_graph (0 */6)
        ▼
  ┌──────────────┐   rebuild set-based, idempotente, 1 transação
  │ news_entities│   (só menções com canonical_id não-nulo)
  │ entity_edges │   co_mention (weight≥2, src<dst) + subordinate_to + is_agency
  └──────┬───────┘
         │  DAG sync_graph_to_neo4j (30 */6) — MERGE via Bolt
         ▼
  ┌──────────────┐        graphql-api            portal /entidades/[id]
  │  Neo4j 5.x   │  ──► relatedEntities  ──►  "Entidades relacionadas" (chips)
  │  (Community) │  ──► entityNetwork    ──►  rede ego-centrada (force-graph)
  └──────────────┘
```

### O grafo no Postgres (Fase 6a/6b)

A fundação foi construída primeiro no banco relacional, onde os dados já viviam ([data-platform#180](https://github.com/destaquesgovbr/data-platform/pull/180)). Duas migrações criaram o modelo: a **021** definiu `news_entities` (a menção normalizada — uma linha por artigo × entidade canônica) e a **022** definiu `entity_edges` (as arestas agregadas: co-menção, `subordinate_to` e `is_agency`). O coração é um rebuild **set-based** que reconstrói `news_entities` a partir de `news_features` — considerando apenas menções com `canonical_id` não-nulo, com guarda de chave estrangeira para dados parciais — e recomputa as arestas numa única transação idempotente, com SQL 100% parametrizado.

Duas decisões deram robustez ao grafo desde o início: a co-menção só vira aresta com **peso ≥ 2** (um único artigo compartilhado não basta para afirmar relação) e toda aresta respeita a **ordem canônica `src < dst`**, o que elimina duplicatas espelhadas. A DAG `project_entity_graph` (a cada 6h) entrega o grafo no Postgres; a DAG `sync_graph_to_neo4j` (também 6h, defasada 30 min) faz o MERGE idempotente de nós e arestas no Neo4j via driver Bolt — desenhada para só ativar quando a infra do Neo4j subisse. Foram 40 testes novos cobrindo os invariantes do SQL e a orquestração.

### A infra do Neo4j (Fase 6b)

O destino do grafo é uma VM dedicada rodando **Neo4j 5 Community** em Container-Optimized OS ([infra#200](https://github.com/destaquesgovbr/infra/pull/200)). O desenho reaproveita o padrão já usado no Typesense: disco `pd-ssd` persistente com `prevent_destroy` em `/data`, IP estático, service account própria, e um `startup-script` que busca a senha de admin no Secret Manager a cada boot. As portas de dados **não são expostas à internet** — firewall do Bolt (7687) e do Browser (7474) restrito à VPC e aos ranges do Composer, sem `0.0.0.0/0`; o acesso ao Browser é via túnel SSH/IAP. A máquina é uma `e2-standard-4`, com 50 GB de disco e 4 GB de heap, a um custo estimado de **US$ 80–120/mês**.

!!! note "Community, não Enterprise"
    A edição **Community** (GPLv3) já entrega Browser, Cypher e a projeção — o suficiente para exploração interna e para a base de travessias multi-hop futuras. O Bloom exigiria a licença Enterprise, deixada fora de escopo por ora.

### Os resolvers de relação (Fase 6c)

Com as tabelas prontas, o graphql-api ganhou dois campos públicos ([graphql-api#19](https://github.com/destaquesgovbr/graphql-api/pull/19)). O `relatedEntities(id, limit=12)` lê `entity_edges` do tipo `co_mention`, resolve a "outra ponta" da aresta via `CASE` e ordena por peso. O `entityNetwork(id, depth=1, limit=50)` usa uma CTE recursiva com a **profundidade clampada a [0,2]** e o `entity_id` sempre passado como `$1` — parametrização anti-injection — em duas queries de nós e arestas que compartilham a mesma CTE. Ambos são **None-safe**: sem Postgres, degradam para vazio em vez de quebrar. O delta do SDL foi puramente aditivo, e a entrega somou 12 testes novos aos 484 da suíte.

### A UI: entidades relacionadas e rede ego-centrada (Fase 6d)

O portal fechou o arco expondo o grafo ao leitor ([portal#266](https://github.com/destaquesgovbr/portal/pull/266)). Em `/entidades/[id]` surgiu a seção **"Entidades relacionadas"** — chips que linkam para cada entidade vizinha, com cor e ícone por tipo e o peso da relação visível; se não há relações, a seção simplesmente não aparece. Acima dela, um **`EntityNetwork`** desenha a rede ego-centrada num canvas `react-force-graph-2d`, com o ego destacado, espessura proporcional ao peso e clique que navega para o vizinho. Um detalhe deliberado de custo: o toggle vem **desligado por padrão** — a query da rede só dispara quando o usuário liga —, e o canvas entra via `next/dynamic` com `ssr:false`. Passou pelo drift gate de codegen e por 549 testes de `vitest` (18 novos).

---

## Salto 2: o backfill retroativo — a operação de guerra

O grafo, sozinho, mostraria só o presente. Para valer, a canonicalização precisava alcançar os **~314 mil artigos** históricos que nunca tinham passado pelo NER canônico. O problema não é o código do reprocessamento — é a **economia** dele: cada artigo custa tokens no Bedrock, e disparar tudo de uma vez estouraria qualquer limite da conta AWS e ainda roubaria capacidade do worker que enriquece as notícias ao vivo. A resposta foi transformar o backfill em **Cloud Run Jobs** orquestrados pelo Airflow, com um **governador de cota** entre a pipeline e o dinheiro.

```
  DAG (Composer)  ──►  Cloud Run Job (canon / NER)
                            │
                            │ antes de cada lote: budget_exhausted?
                            ▼
                    ┌──────────────────┐   record_usage (UPSERT atômico)
                    │  llm_daily_usage │◄──── worker ao vivo (só escreve,
                    │  (ledger Postgres)│      nunca se autolimita)
                    └──────────────────┘
                            │ soma tokens do dia × modelo
                            ▼
                    para gracioso quando cruza a fração do teto
```

### Os Jobs e o governador de cota

A infra criou dois `google_cloud_run_v2_job` — um para a canonicalização, outro para o NER — na região `southamerica-east1`, cada um com service account mínima própria e secrets via Secret Manager ([infra#201](https://github.com/destaquesgovbr/infra/pull/201)). Aqui já apareceu uma restrição de conta que moldou tudo: o `canon_model_id` teve de apontar para `us.anthropic.claude-sonnet-4-6`, porque o **Opus 4.8 não estava habilitado na conta**. A cota inicial foi parametrizada como 800 mil tokens/dia do Sonnet, com o backfill limitado a 80% dela.

O governador em si nasceu na data-science ([data-science#29](https://github.com/destaquesgovbr/data-science/pull/29)). O novo `quota_governor.py` mantém um ledger em Postgres (`llm_daily_usage`) com `record_usage` por UPSERT atômico e um `budget_exhausted` que corta o backfill em **80% da cota diária, preservando ≥20% para o worker ao vivo** — que registra seu consumo no mesmo ledger, mas nunca se autolimita. O `llm_client.py` passou a capturar o `usage` (input + output) de toda chamada Bedrock; o driver histórico `backfill_ner_corpus.py` seleciona os artigos sem NER por `NOT EXISTS`, na ordem mais-novo-primeiro, de forma resumível e em lotes, para que o governador possa parar sem anular o teto. Um bug sutil foi corrigido de passagem: o `mint_internal_id` truncava mal o slug e estourava o `varchar(64)` — agora o slug vai a 52 caracteres + `sha1[:6]`. A entrega somou 53 testes (189 no total), com Bedrock e Wikidata sempre mockados.

As DAGs vieram na sequência, junto da migração **023** que cria o ledger `llm_daily_usage` — a base de todo o mecanismo ([data-platform#182](https://github.com/destaquesgovbr/data-platform/pull/182)). A `canonicalize_backfill` rodava às 02:00 e a `ner_backfill` às 04:00, cada uma disparando seu Cloud Run Job via `CloudRunExecuteJobOperator`.

### O primeiro tropeço: `clear_args`

No primeiro disparo real, ambas as DAGs falharam com `up_for_retry` depois de ~17s, sem criar **nenhuma** execução do Job ([data-platform#183](https://github.com/destaquesgovbr/data-platform/pull/183)). A exceção era clara:

```
google.api_core.exceptions.InvalidArgument: 400 Violation in
RunJobRequest.overrides.container_overrides[0].args: Args list for
override must be empty when clear_args field is set to true.
```

A API do Cloud Run v2 trata `clear_args=True` e `args=[...]` como **mutuamente exclusivos** no mesmo `container_override`: passar `args` já substitui os args do container por completo; `clear_args` serve apenas para zerá-los sem substituir. A correção foi remover o `clear_args: True` das duas DAGs. Um `gcloud run jobs execute` manual confirmou o fix (execução `x9zww` completa).

### O segundo tropeço: `runWithOverrides`

Resolvido o `clear_args`, o operador esbarrou logo em seguida num `PERMISSION_DENIED` ([infra#202](https://github.com/destaquesgovbr/infra/pull/202)):

```
Permission 'run.jobs.runWithOverrides' denied on resource
'.../jobs/destaquesgovbr-canon-backfill'
```

A causa é fina: `roles/run.invoker` só concede `run.jobs.run`. No momento em que o operador passa `overrides` no `RunJobRequest`, a API exige `run.jobs.runWithOverrides` — que só existe em `roles/run.developer`. A correção trocou o papel nos dois bindings, mas **mantendo o escopo por job** (no nível do recurso, não do projeto): o efeito prático continua o mesmo — o SA do Composer só opera nesses dois jobs específicos.

### Acelerar: de quota fictícia a teto de custo

Com o backfill finalmente rodando, veio a descoberta que virou o desenho do avesso: **o Bedrock on-demand não tem quota diária de tokens** ([infra#204](https://github.com/destaquesgovbr/infra/pull/204)). Um teste com 200 requisições paralelas queimou 710 mil tokens sem nenhum throttle. A cota de 800k que o governador defendia era, portanto, uma ficção. O governador foi então reorientado para limitar **custo**, não uma quota inexistente: **9,05M tokens/dia ≈ US$ 50/dia** ao mix histórico do Sonnet 4.6. O orçamento passou a ser dividido — canon com `fraction=0.8` (~US$ 40/dia, ~2.060 formas/dia) e NER com `fraction=1.0` sobre o **mesmo pool**, consumindo o saldo (~US$ 10/dia, ~354 artigos/dia). Para suportar mais throughput, o timeout dos Jobs subiu de 3600 para 7200s e cpu/memória de 1/1Gi para 2/2Gi, acomodando o pool de 10 conexões psycopg2.

Esse pool existe porque a canonicalização ganhou paralelismo ([data-science#30](https://github.com/destaquesgovbr/data-science/pull/30)): o `_resolve_pending_parallel` usa um `ThreadedConnectionPool` em que cada worker-thread recebe conexão própria, o budget é checado **entre lotes** (não por forma, para a parada graciosa funcionar em paralelo) e o `record_usage` é serializado na thread principal. Um `--workers 1` mantém o caminho sequencial intacto; o `--workers 10` recomendado dá 10× de throughput.

As DAGs foram afinadas de acordo ([data-platform#185](https://github.com/destaquesgovbr/data-platform/pull/185)): ambas passaram a rodar **4×/dia** com `--workers 10`. O truque é que o governador garante que só a **primeira run do dia** consome o orçamento real; as demais saem em menos de 5s com `budget_exhausted=True` — mas se a primeira falha, sobram 3 chances de retry automático no mesmo dia. O canon roda a cada 6h (00/06/12/18 UTC) e o NER com offset de 2h (02/08/14/20 UTC), garantindo que o canon consuma sua fatia primeiro. O `execution_timeout` subiu para 130 min, alinhado ao teto de 7200s do Job.

### O limite real da AWS

O teto de US$ 50/dia durou pouco. Em 18/06/2026, rodando de verdade, a AWS respondeu com o veredito empírico ([infra#205](https://github.com/destaquesgovbr/infra/pull/205)):

```
ThrottlingException: Too many tokens per day
```

O limite diário real do Bedrock on-demand (Sonnet 4.6 cross-region) apareceu por volta de **~6,4M tokens**. Ou seja: **existe** cota diária, ao contrário do que o teste anterior sugeria — só não bate com o número documentado. O teto foi então reduzido de 9,05M para **6,0M tokens/dia** (~6% de margem abaixo do limite observado), o que baixou o custo de fato para **~US$ 33/dia** (canon ~US$ 26 + NER ~US$ 7) contra os US$ 50 estimados.

!!! warning "A quota que ninguém documenta"
    Em poucas horas, a mesma variável de teto passou por três valores: 800k (cota fictícia), 9,05M (teto de custo com "sem quota diária") e 6,0M (limite real da AWS, confirmado por `ThrottlingException`). A única fonte de verdade acabou sendo o próprio erro do Bedrock em produção.

---

## Salto 3: a qualidade que só a escala revela

Rodar a canonicalização sobre milhares de formas reais expôs uma família de erros que os testes com dados sintéticos nunca teriam mostrado — todos girando em torno de **duplicatas, homônimos e siglas**.

### Dedup, Wikidata-wins e o atalho do PER

O primeiro lote de correções trouxe a maquinaria de fusão ([data-science#31](https://github.com/destaquesgovbr/data-science/pull/31)). O `merge_entities` une duas entidades — migra aliases, herda metadata, deleta a fonte — e serve de base para o resto. O `add_alias` ganhou a regra **Wikidata-wins**: quando um alias já existe como `dgb_` e uma nova resolução traz um QID da Wikidata, as duas se fundem e o alias é promovido ao QID (resolvendo conflitos como `dgb_ans` vs `Q9592631`). O reuso por similaridade, antes só para ORG, foi generalizado para LAW (0,75), POLICY/PROGRAM (0,70) e EVENT (0,80) — evitando duplicatas como `dgb_lei-no-14-967-2024` vs `dgb_lei-no-14-967-de-9-de-setembro-...`. E um **short-circuit para PER**: antes de chamar o Bedrock, um pré-check na Wikidata com o `surface_norm` bruto; se vazio, a entidade vai direto para `needs_review` — o que poupou **~18M tokens** referentes a ~13 mil servidores públicos que não têm verbete na Wikidata.

### Siglas: o threshold que não bastava

O `--dedup` de ORG começou usando o threshold de mint-time (Jaccard **0,62**) e produziu fusões erradas de entidades **distintas** ([data-science#32](https://github.com/destaquesgovbr/data-science/pull/32)): "Banco Central do Brasil" ↔ "Banco do Brasil" (Jaccard 0,75), "Polícia Federal" ↔ "Polícia Rodoviária Federal". O detalhe cruel é que **subir o threshold sozinho não resolve** — fusões legítimas têm exatamente o mesmo score: "Ministério da Educação" ↔ "Ministério da Educação (MEC)" também dá Jaccard 0,75. A diferença não é de score, é semântica: variante por sigla versus entidades diferentes.

A solução foi dupla: um threshold dedicado de dedup (**ORG = 0,85**, separado do mint-time) e um detector `_is_acronym_variant` que funde um par quando `score ≥ thr` **ou** quando um lado é a sigla do outro. Para não confundir sigla com qualificador, entrou um **gate de subsequência**: um parêntese só conta como sigla da base se suas letras formam uma subsequência das letras da base — `finep ⊂ financiadoradeestudoseprojetos` funde, mas `libano ⊄ ministeriodasaude`, então "Ministério da Saúde (Brasil)" e "(Líbano)" **não** fundem. A suíte foi de 224 para 246 testes.

### O detector que explodiu em produção

E então o detector encontrou a produção ([data-science#33](https://github.com/destaquesgovbr/data-science/pull/33)). Um `--dedup --type ORG --dry-run` contra o banco real — validação pré-retroatividade — gerou **8,8MB de falsos-positivos**. O culpado era o **path (b)** do detector: a expansão de acrônimo entre bases diferentes. Três classes de erro apareceram, todas com dados reais:

1. **Self-match**: `"X (SIGLA-DE-X)"` casava contra qualquer B — "Agência Brasileira de Cooperação" ↔ "Conselho Nacional do Ministério Público (CNMP)" com Jaccard **0,000**.
2. **Colisão de sigla**: orgs distintas que compartilham acrônimo — "Forças Armadas do Brasil" ↔ "Força Aérea Brasileira (FAB)"; "Secretaria de Política Agrícola (SPA)" ↔ "Secretaria de Prêmios e Apostas (SPA)".
3. **Sub-unidade vs pai**: "Diretoria Colegiada da ANM (ANM)" ↔ "Agência Nacional de Mineração" — relação de subordinação, não fusão.

A correção foi cirúrgica e urgente: remover o path (b) inteiro (e seus helpers órfãos), mantendo só o path (a) — mesma base despida + sigla validada por subsequência —, que já cobre **todos** os merges legítimos. O impacto medido conta a história: **8,8MB** de propostas com o bug, 42 com o self-match corrigido, e **35 propostas, todas corretas** depois de remover o path (b). Era urgente porque o código de #32 já estava deployado e o mint-time o usa como fallback — o próximo run do canon corromperia o registry. O `--dedup` retroativo **nunca** chegou a rodar em prod; só o dry-run.

### Antes de tocar o passado: reescrever `canonical_id` e respeitar o QID

O dry-run limpo revelou 35 merges legítimos que tocariam **4.606 menções** e **2.696 linhas do grafo** — e, no caminho, duas lacunas que teriam degradado os dados ([data-science#34](https://github.com/destaquesgovbr/data-science/pull/34)). Primeira: o `merge_entities` deletava a entidade-fonte do registry mas **não reescrevia o `canonical_id`** nas menções, deixando 4.606 delas órfãs (e o `news_entities`, com FK `ON DELETE CASCADE`, perderia as arestas no próximo rebuild). Entrou um passo `_rewrite_mentions_canonical_id`, que também protege o caminho `add_alias` Wikidata-wins da canonicalização normal. Segunda: a seleção de target escolhia por contagem de aliases, contra a regra de identidade do projeto (QID da Wikidata > id interno `dgb_`) — em **33 dos 35** merges, isso apagaria o QID e manteria o `dgb_`, perdendo a âncora linked-data. Com a seleção Wikidata-wins, os 33 pares passaram a preservar o QID; os 2 restantes eram duplicatas exatas `dgb_×dgb_` (Casa Civil, TransfereGov). Suíte em 253.

### Edições por ano

A última salvaguarda veio de uma decisão de produto: eventos e programas recorrentes são rastreados **por edição** — "Enem 2025" e "Enem 2026" são entidades distintas ([data-science#35](https://github.com/destaquesgovbr/data-science/pull/35)). Sem isso, o detector proporia fusões erradas por Jaccard alto (ex.: "Encontro Nacional de Gestão de Pessoas (ENGP)" ↔ "...(ENGP) 2026", Jaccard 0,857). O guard determinístico `differs_by_year` bloqueia a fusão de nomes cujos conjuntos de tokens-de-ano (4 dígitos, 1900–2099) diferem, tanto no dedup quanto no mint-time. "Copa do Mundo FIFA de 2026" vs "... 2026" (mesmo ano) **ainda funde** — ali o ano não distingue nada. O efeito medido: de 2 propostas de EVENT para 1 (só a Copa; a ENGP foi bloqueada). Suíte em 262.

### E o grafo precisa esquecer

Todo esse merge contínuo revelou um vazamento no elo final ([data-platform#186](https://github.com/destaquesgovbr/data-platform/pull/186)). O `sync_graph_to_neo4j` era **MERGE-only**: fazia upsert dos nós correntes, mas **nunca removia** do Neo4j os nós que tinham saído do Postgres. Como entidades se fundem o tempo todo — o `add_alias` Wikidata-wins promove `dgb_`→QID a cada canonicalização, além dos `--dedup` retroativos — o Neo4j acumulava nós stale com arestas mortas. Durante a retroatividade do dedup ORG, após 36 merges, o Neo4j ficou com 36 nós órfãos (**1143 vs 1107** no Postgres), exigindo cleanup manual via túnel SSH. A correção adicionou um passo de limpeza na mesma sessão do sync:

```cypher
MATCH (e:Entity) WHERE NOT e.entity_id IN $valid_ids
DETACH DELETE e RETURN count(*) AS deleted
```

Com um **guard de segurança** essencial: o DELETE só roda se o `fetch_nodes` retornou nós — um fetch vazio por erro transitório **nunca** zera o grafo. A partir daí, o Neo4j se autolimpa a cada 6h, sem mais cleanup manual.

---

## Antes e depois

| | Antes | Depois |
|---|---|---|
| Relação entre entidades | implícita, linha a linha em `news_features` | grafo explícito (`entity_edges`) no Postgres + Neo4j |
| Navegação de relações no portal | inexistente | "Entidades relacionadas" + rede ego-centrada |
| Cobertura da canonicalização | só notícias novas | backfill sobre ~314k artigos históricos |
| Controle de gasto com LLM | nenhum (risco de estourar a conta) | governador de cota com ledger em Postgres |
| Teto de tokens/dia | suposto (800k, depois "ilimitado") | 6,0M — limite real da AWS confirmado |
| Dedup de ORG | Jaccard 0,62 (falsos-positivos) | 0,85 + detector de sigla homonym-safe |
| Nós stale no Neo4j | acumulavam (cleanup manual via SSH) | autolimpeza a cada sync |

## Números

| Métrica | Valor |
|--------|-------|
| Fases do grafo | 6a · 6b · 6c · 6d |
| Artigos históricos alvo do backfill | ~314.000 sem NER |
| Teto diário de tokens (final) | **6,0M** (limite AWS) · custo ~US$ 33/dia |
| Split de custo | canon ~US$ 26/dia · NER ~US$ 7/dia |
| Paralelismo | `--workers 10` · Jobs 4×/dia |
| Tokens poupados (PER short-circuit) | ~18M (~13k servidores sem Wikidata) |
| Threshold de dedup ORG | 0,62 → **0,85** (+ detector de sigla) |
| Falsos-positivos ORG (dry-run) | 8,8MB → 35 propostas corretas |
| Merges legítimos ORG | 35 (4.606 menções · 2.696 linhas do grafo) |
| QIDs preservados no dedup | 33 de 35 pares |
| Nós stale limpos do Neo4j | 36 (1143 → 1107) |
| Neo4j | 5 Community · `e2-standard-4` · ~US$ 80–120/mês |
| Testes (data-science, ao fim) | 262 · 0 falhas |
| Migrações | 021 · 022 · 023 (ledger de cota) |

## Lições

1. **Cota de LLM se descobre errando, não lendo a documentação.** O teto passou por 800k → 9,05M → 6,0M em horas. A única fonte de verdade sobre o limite diário do Bedrock foi o próprio `ThrottlingException` em produção — nenhum número documentado bateu. Governar custo pressupõe medir o consumo real (o ledger `llm_daily_usage`) e aceitar recalibrar.
2. **O governador precisa proteger o presente, não só o passado.** Reservar ≥20% da cota para o worker ao vivo e fazer o backfill parar graciosamente entre lotes evitou que o reprocessamento histórico afogasse o enriquecimento das notícias novas.
3. **Threshold não separa semântica.** Fusões legítimas ("Ministério da Educação (MEC)") e falsos-positivos ("Banco Central" vs "Banco do Brasil") podem ter o mesmo Jaccard. Foi preciso um detector determinístico de sigla com gate de subsequência — e ainda assim o path (b) explodiu em 8,8MB de lixo até ser removido. Em dados reais, o caminho mais esperto é o mais perigoso.
4. **Valide o dedup contra produção antes de aplicar.** Rodar `--dry-run` contra o banco real revelou os self-matches, as colisões de sigla e as 4.606 menções que ficariam órfãs — tudo antes de qualquer escrita. A retroatividade só é segura depois que o dry-run está limpo.
5. **Identidade tem hierarquia: o QID sempre vence.** A seleção de target por contagem de aliases teria apagado o QID em 33 de 35 merges. Ancorar a regra Wikidata-wins em cada ponto de fusão (dedup e `add_alias`) preserva a âncora linked-data que dá sentido ao grafo.
6. **Um grafo derivado precisa saber esquecer.** Sincronização MERGE-only acumula nós stale quando a origem funde entidades continuamente. O cleanup de nós fora do conjunto corrente — com guard contra fetch vazio — é o que mantém o Neo4j fiel ao Postgres sem intervenção manual.

Ao fim deste ciclo, o gov.br deixou de ser uma lista de notícias e entidades para virar uma **rede navegável**, alimentada por um corpus histórico que finalmente fala a mesma língua canônica do presente. Um grafo consistente e uma base reprocessada não são um fim em si — são o substrato sobre o qual um agente pode raciocinar. É exatamente para lá que o próximo passo do arco aponta: colocar um investigador automático a percorrer essa rede.

---

*Série **A evolução da plataforma DGB (jun–jul 2026)** · post 2 de 4.*
*Post anterior: [Entidades que viram conhecimento](2026-06-11-entidades-canonicas-lente-semantica.md) · Próximo post: [Gobus MCP: um agente que investiga o gov.br](2026-06-30-gobus-mcp-agente-govbr.md).*
