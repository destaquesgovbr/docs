---
date: 2026-06-11
authors:
  - nitai
categories:
  - NLP
  - Entidades
  - Data Science
  - Portal
title: "Entidades que viram conhecimento: NER canônico, Wikidata e a lente semântica"
hide:
  - toc
---

# Entidades que viram conhecimento: NER canônico, Wikidata e a lente semântica

Até esta rodada, uma entidade no DGB era apenas texto: "Min. da Saúde", "Ministério da Saúde" e "MS" eram três coisas diferentes para a plataforma, strings soltas presas a uma notícia e a mais nada. Em dois dias (10 e 11 de junho de 2026), a plataforma trocou esse NER "bruto" por entidades **canônicas** — cada menção passou a resolver para um nó de conhecimento com identidade estável, tipo (organização, pessoa, lugar, e agora também **Eventos** e **Políticas públicas**) e, quando possível, um **QID da Wikidata** como chave de deduplicação linked-data. No caminho, a busca de "relacionadas" deixou de ser por código de tema e virou **similaridade semântica** (com um ganho medido de ~4,3s para ~180ms), a tela da notícia ganhou chips agrupados por tipo e uma **lente semântica** que marca entidades no corpo do texto.

<!-- more -->

---

## De strings soltas a nós de conhecimento

O ponto de partida era um NER que devolvia texto e um depósito de lixo. Entidades vinham como cadeias de caracteres, variações da mesma coisa nunca se encontravam, e tudo que o modelo não sabia classificar caía num balde `MISC` que não servia para nada.

```
ANTES (NER bruto)                     DEPOIS (entidade canônica)
-----------------                     --------------------------
"Min. da Saúde"  --+                   +-- entity_registry
"Ministério da     |  strings          |     id: canônico estável
 Saúde"            |  soltas,          |     tipo: ORG
"MS"             --+  sem ligação  --> |     label: Ministério da Saúde
                                       |     wikidata: Q1519799
                                       +-- (alias --> o mesmo nó)
```

A evolução aconteceu em duas frentes que fecharam juntas: o **extrator + a pipeline de canonicalização** na camada de ciência de dados, e a **fundação canônica** (banco, índice, API e portal) que transforma esses nós em navegação real para quem lê o portal.

---

## O extrator NER evoluído e a pipeline de canonicalização

A primeira metade da história está em [data-science#26](https://github.com/destaquesgovbr/data-science/pull/26) e [data-platform#179](https://github.com/destaquesgovbr/data-platform/pull/179).

O NER saiu da chamada LLM combinada e ganhou **chamada Bedrock própria**, com modelo configurável via `NER_MODEL_ID`. Junto veio uma nova taxonomia em português que acrescenta **Eventos** e **Políticas públicas** aos tipos clássicos (organização, pessoa, lugar) — e, decisivo, um bloco explícito de "**NÃO é entidade**" no prompt, que drena o depósito `MISC` na origem em vez de deixar ruído escorrer para o índice. Cada entidade passou a sair com `forma_canonica` e `salience`, e a resposta crua do modelo passou a ser gravada em `news_llm_raw` (objeto JSONB) — o que torna o corpus **reprocessável sem re-chamar o Bedrock**.

A canonicalização propriamente dita (`canonicalization_job.py`, `canonicalization.py`, `wikidata_client.py`) trabalha por forma distinta, numa cascata com desligamentos progressivos:

```
menção (forma distinta)
     |
     v
 gazetteer (159 órgãos)  -- hit --> canonical_id
     | miss
     v
 Opus (CANON_MODEL_ID)   -- forma canônica + tipo
     |
     v
 Wikidata QID (dedup)    -- gates de confiança
     |                      + escalada contextual (PER / homônimos)
     v
 entity_registry  <-- backfill de canonical_id nas menções
```

O QID da Wikidata não é enfeite: é a **chave de deduplicação**. Duas formas diferentes que resolvem para o mesmo QID são, por definição, a mesma entidade. Para pessoas e homônimos, a pipeline aplica **gates de confiança** e uma **escalada contextual** — o guard citado no PR distingue, por exemplo, a Saúde brasileira de uma homônima estrangeira antes de fundir os nós. Tudo isso é resumível (pode parar e retomar) e faz backfill do `canonical_id` nas menções já existentes.

A fundação de dados que segura essa canonicalização veio nas **migrações 015-020** ([data-platform#179](https://github.com/destaquesgovbr/data-platform/pull/179)):

- `entity_registry` — a tabela canônica, já modelada **Neo4j-ready** (guarde esse detalhe para o próximo post);
- `entity_alias` — o resolver **determinístico** de aliases, semeado com **159 órgãos** derivados da tabela `agencies`;
- índice GIN sobre a coluna canônica, `news_llm_raw` (o cru reprocessável) e `entity_registry_seen` (o estado da canonicalização).

!!! note "O que a revisão adversarial pegou"
    A rodada de revisão adversarial não foi decorativa: em [data-platform#179](https://github.com/destaquesgovbr/data-platform/pull/179) ela flagrou e corrigiu uma **colisão de alias** e um **bug crítico de offsets em NFD** (a normalização Unicode que faz a lente apontar para o caractere certo). Em [data-science#26](https://github.com/destaquesgovbr/data-science/pull/26), 136 testes verdes com Bedrock e Wikidata mockados — sem chamadas reais, sem reprocessamento acidental. Em [data-platform#179](https://github.com/destaquesgovbr/data-platform/pull/179), 586 testes unitários verdes.

---

## A fundação canônica no Typesense e a lente semântica

Com o registro canônico pronto no Postgres, faltava expor isso ao portal — e foi onde o índice de busca precisou aprender os tipos novos.

### O indexer que perdia entidade

O Typesense ganhou os campos `entity_event`, `entity_policy` e `entity_canonical`, e o indexer passou a rotear EVENT/POLICY e a emitir o `canonical_id` ([data-platform#179](https://github.com/destaquesgovbr/data-platform/pull/179)). No caminho, um bug silencioso foi corrigido: tudo que não fosse ORG/PER/LOC — justamente os novos Eventos e Políticas — caía num `entity_misc` e **era perdido** na indexação. A lente semântica, do lado do data-platform, ganhou o feature-worker `compute_content_annotations`, que calcula **offsets determinísticos** com um mapa `folded -> original` robusto a NFD e casefold, para nunca destacar a palavra errada no corpo.

### Relacionadas por significado, não por código de tema

Na API, [graphql-api#17](https://github.com/destaquesgovbr/graphql-api/pull/17) trouxe as features calculadas para dentro do `Article` e reescreveu as "notícias relacionadas". Antes, "relacionadas" era um `OR` entre códigos de tema; agora é **similaridade semântica** via `pgvector`. O detalhe de engenharia importa: a query `get_similar_articles` foi reescrita para usar o índice **HNSW** (`ORDER BY content_embedding <=> $1::vector`, com o embedding do artigo base como literal), eliminando um `Seq Scan` que varria **~333 mil linhas**. Medido localmente, o salto foi de **~4,3s para ~180ms**.

Para não onerar listas e busca, `Article.features` é um campo **lazy**: um DataLoader por `unique_id` que só toca o `news_features` (JSONB) quando o campo é efetivamente selecionado. A assinatura GraphQL de `relatedArticles` ficou **inalterada** — a troca de mecanismo por baixo passou pelo gate anti-drift sem quebrar o portal. A mesma PR adicionou filtros por entidade e sentimento, o argumento `sort` (`RELEVANCE`/`DATE`/`TRENDING`/`VIEWS`) e o resolver público `entitySuggestions` para typeahead. **446 testes** verdes.

A camada canônica em si veio logo em seguida ([graphql-api#18](https://github.com/destaquesgovbr/graphql-api/pull/18)): `EntityType.canonicalId` + `salience`, um resolver `entity(id): EntityNode` que lê o `entity_registry`, o modo canônico do `entitySuggestions` (faceta `entity_canonical`), o filtro de busca `entityCanonical` e o `ArticleFeatures.contentAnnotations` — a lente. Todas as mudanças de SDL foram **puramente aditivas/nullable**, o que mantém o drift gate seguro. **470 testes** verdes.

!!! warning "A ordem de deploy não é opcional"
    Como o portal compila contra um snapshot do SDL, o **graphql-api tem de ser deployado antes** do portal. Os dois PRs de API deixam isso explícito, e o filtro/typeahead de entidade só retorna dados **depois** do reindex do Typesense em produção — até lá, degrada para vazio em vez de quebrar.

---

## Grupos Eventos/Políticas e a lente na tela da notícia

Do lado do portal, o trabalho veio em duas PRs. [portal#264](https://github.com/destaquesgovbr/portal/pull/264) montou a **tela da notícia enriquecida** (o componente `ArticleFeatures`, composto de `ArticleFichaBar` + `ArticleEntities`), os filtros por sentimento e entidade com ordenação na `/busca`, o `EntityMultiSelect` com typeahead alimentado por `entitySuggestions` e as primeiras páginas `/entidades/[slug]`. **484 testes** verdes.

[portal#265](https://github.com/destaquesgovbr/portal/pull/265) fechou a camada canônica na interface:

- **chips agrupados** de Eventos e Políticas Públicas, com `lib/entity-types.ts` como fonte única de cor e ícone por tipo;
- páginas `/entidades/[id-canonico]` com header vindo de `entity(id)` — nome, tipo, descrição e link para a **Wikidata** — e a lista de notícias via filtro `entityCanonical`, com fallback gracioso para os slugs de texto legados;
- a **`SemanticLens`**: a lente que marca entidades inline no corpo da notícia.

A lente merece uma nota de projeto. Ela usa uma estratégia **validate-then-split**: antes de destacar, valida que o trecho no offset corresponde de fato à entidade, e só então divide o texto — a revisão adversarial confirmou que a lente é **incapaz de destacar a palavra errada**. Ela vem **desligada por padrão**, com um toggle discreto ("ghost") e a preferência persistida em `localStorage`, para não poluir a leitura de quem não a quer. **525 testes** verdes.

| | Antes | Depois |
|---|---|---|
| Entidade | string solta na notícia | nó canônico com `id` estável |
| Variações ("MS", "Min. Saúde") | três entidades distintas | um mesmo nó (via `entity_alias`) |
| Tipos reconhecidos | ORG / PER / LOC (+ balde `MISC`) | + Eventos + Políticas; sem `MISC` |
| Identidade externa | nenhuma | QID da Wikidata (linked data) |
| Relacionadas | `OR` de códigos de tema | similaridade semântica (HNSW) |
| Entidade no corpo do texto | texto puro | lente semântica (marcação inline) |

---

## Ligando os modelos: as env vars do Bedrock

Nada disso liga sozinho. Os modelos que o NER e a canonicalização usam são configuráveis, e [infra#198](https://github.com/destaquesgovbr/infra/pull/198) fez essa fiação via Terraform: variáveis `ner_model_id` e `canon_model_id`, com `NER_MODEL_ID` indo para o `enrichment-worker` e `CANON_MODEL_ID` para o Composer (onde a futura DAG de canonicalização vai rodar, já com boto3).

A decisão de segurança aqui foi deixar os **defaults no modelo atual** (`anthropic.claude-3-haiku-20240307-v1:0`), de forma que o `terraform plan` fosse um **no-op seguro** — apenas adiciona as env vars, sem mudar comportamento. Ativar o upgrade (Sonnet 4.6 para o NER, Opus 4.8 para a canonicalização) é um passo separado e deliberado. Os IDs exatos dos inference-profiles **não foram inventados**: sem AWS CLI no ambiente, o PR documenta o padrão esperado (`us.anthropic.claude-sonnet-4-6-<rev>-v1:0` etc.) e pede confirmação da string real habilitada na conta.

!!! tip "Falha graciosa por design"
    O enrichment-worker é resiliente: se o `NER_MODEL_ID` estiver inválido, o NER **degrada** (entidades vazias) sem derrubar tema, resumo e sentimento — porque a chamada combinada desses três usa outro modelo. Um ID errado custa entidades naquele lote, não a pipeline inteira.

---

## O 403 da Wikidata (e o driver de re-NER)

O primeiro reprocessamento real, sobre uma fatia de um mês, quase entregou uma canonicalização sem a parte que a torna linked data. A Wikidata começou a devolver **HTTP 403 em todas as requisições** — nenhum QID era linkado, e a deduplicação por Wikidata simplesmente não acontecia. A causa: a Wikimedia bloqueia requisições sem um **User-Agent descritivo**.

O fix foi cirúrgico ([data-science#28](https://github.com/destaquesgovbr/data-science/pull/28)): o `wikidata_client.py` passou a enviar um `WIKIDATA_USER_AGENT` no `httpx.Client`. A verificação foi feita ao vivo — sem UA, 403; com UA, 200 — e até os primeiros QIDs saíram corretos:

```
Renan Calheiros      -> Q3623584
Ministério da Saúde  -> Q1519799
Bolsa Família        -> Q575545
```

A mesma PR trouxe `scripts/renew_ner_window.py`, um driver de re-NER de janela **resumível e capado** (newest-first) que reusa exatamente o caminho do worker — a ferramenta que conduziu o reprocessamento do mês e o backfill gradual seguinte.

---

## Números

| Métrica | Valor |
|---|---|
| Migrações de banco | 015-020 (`entity_registry`, `entity_alias`, ...) |
| Órgãos semeados no resolver de alias | 159 (a partir de `agencies`) |
| Ganho da busca de relacionadas (HNSW) | ~4,3s -> ~180ms (Seq Scan em ~333k linhas eliminado) |
| Testes (data-science#26 / data-platform#179) | 136 / 586 verdes |
| Testes (graphql-api #17 / #18) | 446 / 470 verdes |
| Testes (portal #264 / #265) | 484 / 525 verdes |

---

## Lições

1. **A chave de deduplicação tem de vir de fora.** Enquanto entidade era só texto, "MS" e "Ministério da Saúde" jamais se encontrariam. O QID da Wikidata dá um ancoradouro externo e estável — duas formas que resolvem para o mesmo QID são a mesma coisa, sem heurística frágil.
2. **Elimine o balde de lixo na origem.** Um bloco explícito de "NÃO é entidade" no prompt drena o `MISC` antes de ele virar ruído no índice — muito mais barato que filtrar depois. E o `entity_misc` que perdia Eventos e Políticas mostra que um balde também engole o que você passou a querer.
3. **Guarde o cru, reprocesse à vontade.** Gravar a resposta do modelo em `news_llm_raw` (JSONB) desacoplou o reprocessamento das chamadas ao Bedrock — a taxonomia pode evoluir sem re-pagar inferência.
4. **Integrações externas quebram em silêncio.** O 403 da Wikidata não derrubava nada: só parava de linkar QIDs. Um User-Agent descritivo resolveu, mas só foi visto porque o reprocessamento real exercitou o caminho de ponta a ponta.
5. **Falhe gracioso, deploye em ordem.** Env vars com default no modelo atual tornam o `plan` um no-op; NER inválido degrada sem derrubar tema/resumo/sentimento; e SDL aditivo/nullable com "API antes do portal" mantém o drift gate honesto.

Com o `entity_registry` no ar, cada entidade agora é um nó com identidade, tipo e, quando dá, um QID. Mas um nó sozinho é só metade da promessa: o valor real está nas **arestas** — quem aparece com quem, quais órgãos e políticas se cruzam, como esses vínculos evoluem no tempo. Não por acaso a tabela nasceu **Neo4j-ready**. O próximo post da série conta como esses nós viraram um grafo de verdade — e o backfill retroativo que trouxe o passado do gov.br para dentro dele.

---

*Série **A evolução da plataforma DGB (jun–jul 2026)** · post 1 de 4.*
*Próximo post: [O grafo do gov.br: entidades em Neo4j e o backfill retroativo](2026-06-18-grafo-entidades-backfill-neo4j.md).*
