---
date: 2026-07-03
authors:
  - nitai
categories:
  - Analytics
  - Portal
  - Dados
title: "Entidades em alta, políticas públicas e o fechamento do ciclo"
hide:
  - toc
---

# Entidades em alta, políticas públicas e o fechamento do ciclo

Em cerca de três semanas (10 de junho a 3 de julho), a plataforma fechou o ciclo transformando pesquisa em produto. Um scorer de detecção de tendências subiu de NDCG@10 0.727 para 1.000 e virou uma seção "Entidades em Alta" na home; as políticas públicas deixaram de ser texto solto e passaram a objetos de primeira classe, com ontologia, gazetteer e queries próprias; e uma release consolidada de entidades (NER v2) foi para produção. Este é o quarto e último post da série — o momento em que a canonicalização, o grafo e o agente Gobus viram aplicação no ar.

<!-- more -->

Os posts anteriores contaram a construção das fundações: a **canonicalização semântica** (entidades NER viradas conceitos canônicos, com Wikidata QID), o **grafo de entidades relacionadas** e a rede navegável, e o **agente Gobus** que investiga o gov.br via MCP. Este post é sobre o que se faz com tudo isso quando desce para o usuário final — aplicar essas fundações em funcionalidades concretas na tela de quem usa a plataforma.

---

## 1. Entidades em Alta: da pesquisa ao card na home

O arco desta funcionalidade é o melhor exemplo do ciclo inteiro: começa num loop de pesquisa autônoma, atravessa uma produtização com duas pegadinhas de deploy, e termina como um grid de cards na página `/noticias`.

### O scorer que aprendeu sozinho a chegar em 1.0

A detecção de "entidades em alta" nasceu de um experimento no padrão **autoresearch do Karpathy** ([data-platform#188](https://github.com/destaquesgovbr/data-platform/pull/188)): um agente de IA edita **apenas** o arquivo `scorer.py`, um harness fixo (`evaluate.py`) mede NDCG@10 sobre **20 janelas históricas**, e o loop guarda só as mudanças que melhoram a métrica. O caminho até a nota perfeita não foi reto:

```
 commit    NDCG@10   decisão   ideia
 d20c654   0.7276    keep      baseline: 0.6·vr + 0.4·ag
 94e8320   0.7208    discard   multiplicativo: vr × ag
 0abb318   0.7253    discard   log-transform: log1p(vr) × ag
 d767722   0.9500    keep      skip LOC + niche 1/(1+ba)
 3e971a8   0.9967    keep      hard filter agency_stagnant + semantic_novelty
 b46fb0b   0.9967    discard   +new_edge_count — sem efeito
 fea9acd   1.0000    keep      hard filters volume_ratio>1.5 + baseline_agencies≤20
```

O maior salto isolado (+22 pontos percentuais) veio de **filtrar entidades do tipo LOC** — localizações inflavam o ranking sem nunca serem positivos do oracle. A convergência final para 1.0 veio ao transformar os limites do próprio oracle (`volume_ratio > 1.5`, `baseline_agencies ≤ 20`) em filtros hard dentro do scorer. O score contínuo, usado só para ordenação interna, ficou:

```python
niche = 1 / (1 + baseline_agencies)
score = 0.40·volume_ratio + 0.25·agency_growth + 0.20·niche·volume_ratio + 0.15·semantic_novelty
```

Um detalhe de infraestrutura foi decisivo para o loop ser tolerável: dois índices novos (`024_add_trend_detection_indexes.sql`) derrubaram o carregamento de cada snapshot de **~640s para ~40s por janela**, e o experimento `trend-detection-autoresearch` (ID 4) no MLflow — com `min_instances=1` para matar cold start — registrou cada corrida com parâmetros, métricas e o próprio `scorer.py` como artefato.

### Do notebook para produção: DAG, job e as duas pegadinhas de deploy

Um scorer perfeito num experimento não serve a ninguém. A produtização ([data-platform#190](https://github.com/destaquesgovbr/data-platform/pull/190)) criou a tabela `entity_trending_scores` (migração 025, já com a coluna `volume_ratio` que o portal precisaria), empacotou o job em `jobs/trend_detection/` e agendou um DAG `compute_entity_trending` rodando **4x ao dia** (`0 */6 * * *`), com testes TDD cobrindo scorer (8 casos), persistência (4) e a estrutura do DAG (5 casos via AST).

Foi ao chegar no Composer que a realidade cobrou seu preço — duas vezes:

- **O módulo que não foi junto** ([data-platform#191](https://github.com/destaquesgovbr/data-platform/pull/191)): o step `deploy-plugins` listava submódulos explicitamente e esquecera do `trend_detection`, gerando `ModuleNotFoundError` no DAG. Foi preciso adicionar o módulo à lista (e copiá-lo manualmente para o bucket para desbloquear na hora).
- **O embedding que dava timeout** ([data-platform#192](https://github.com/destaquesgovbr/data-platform/pull/192)): em produção, as queries de embedding no `load_snapshot()` puxavam centenas de MB de vetores 768-dim pelo Cloud SQL Auth Proxy, batendo timeout consistente de **~327s**. A saída foi um parâmetro `compute_embeddings=False` (agora o default): as queries de embedding são puladas e `semantic_novelty = 0.0`. Como esse sinal responde por apenas 15% do score, os outros 85% (volume, crescimento de agências, nicho) — os discriminadores primários — seguem intactos.

### O resolver e o card

Com a tabela populada, o [graphql-api#21](https://github.com/destaquesgovbr/graphql-api/pull/21) expôs o tipo `TrendingEntityResult` (7 campos) e o resolver `trendingEntities(limit)`, lendo `entity_trending_scores` via asyncpg com clamp defensivo a 50 — e retornando `[]` graciosamente enquanto a migração 025 não estiver aplicada. No portal, o [portal#267](https://github.com/destaquesgovbr/portal/pull/267) montou o componente `TrendingEntitiesSection`: um grid 2×3 de cards com badge de crescimento (↑N×), ícone por tipo de entidade e link para `/entidades/[id]`, inserido logo após o hero da home `/noticias`. Todo o caminho tem fallback gracioso para `[]`, e o teste E2E se auto-ignora enquanto a tabela estiver vazia durante o rollout.

```
  DAG compute_entity_trending (4x/dia)
        │  scorer NDCG@10 = 1.0
        ▼
  entity_trending_scores (Postgres)
        │  resolver trendingEntities → []  se vazio
        ▼
  graphql-api  ──►  portal /noticias  ──►  grid 2×3 "Entidades em Alta"  (↑N×)
```

### E as páginas de entidade que mostravam zero artigos

Paralelo a isso, um bug embaraçoso: clicar em **qualquer** entidade canônica (`Q...` ou `dgb_...`) em `/entidades/[id]` mostrava zero artigos. A causa era sutil — o caminho antigo filtrava por `entityCanonical` no Typesense, mas o campo `entity_canonical` dos documentos ainda não fora populado (o reprocessamento segue pendente, bloqueado em infra#198). Em vez de esperar o reprocessamento, a plataforma abriu um caminho independente: o resolver `entityArticles(entityId, page, limit)` ([graphql-api#22](https://github.com/destaquesgovbr/graphql-api/pull/22)) faz JOIN de `news_entities → news` direto no Postgres, dedup por `unique_id` e ordenação por `published_at DESC`, sem tocar no Typesense. Em staging, a entidade `Q5933752` passou a retornar **7 artigos** (antes: 0). O portal ([portal#268](https://github.com/destaquesgovbr/portal/pull/268)) passou a usar esse caminho quando há `canonicalId` presente, deixando o legado fuzzy-texto intacto para os demais casos.

## 2. Políticas públicas viram objetos de primeira classe

A segunda frente foi conceitual: tratar **políticas públicas** não como palavras que aparecem em notícias, mas como entidades canônicas com metadados próprios.

### A ontologia e o gazetteer

O [data-platform#195](https://github.com/destaquesgovbr/data-platform/pull/195) trouxe o `policy_gazetteer.csv` com **mais de 40 políticas prioritárias**, cada uma classificada por domínio (SOCIAL / ECONOMIC / HEALTH / EDUCATION / SECURITY / ENVIRONMENT / GOVERNANCE) e por fase do ciclo de vida (ANNOUNCED / REGULATION / IMPLEMENTATION / EVALUATION / ROUTINE). A migração `026_policy_ontology_seed.sql` popula esses metadados no campo JSONB `extra` do `entity_registry` e insere políticas ausentes — idempotente para as existentes (UPDATE), inserindo só as que faltam (INSERT ... WHERE NOT EXISTS), com rollback seguro.

!!! note "O caso `dgb_taxa-selic`"
    A migração resolve o bug UC-09: a taxa Selic, um dos conceitos econômicos mais centrais, tinha **0 artigos NER** porque nunca fora extraída como entidade. O gazetteer a insere com `confidence=0.9` e `provenance=gazetteer`, abrindo caminho para backfill manual — um lembrete de que o NER automático tem pontos cegos que só uma curadoria explícita cobre.

### As queries

Sobre essa base, duas queries. O [graphql-api#25](https://github.com/destaquesgovbr/graphql-api/pull/25) adicionou `policyDetails(entityId)` com o tipo `PolicyDetails`, expondo os metadados de ontologia de uma política (Fase 1). O [graphql-api#27](https://github.com/destaquesgovbr/graphql-api/pull/27) adicionou `policies(domain, lifecyclePhase, limit, offset)` — o tipo `PolicyListItem` inclui a contagem de artigos via LEFT JOIN com `news_entities` — para alimentar a futura página `/politicas`. No momento do merge, a migração 026 já estava em produção com **45 políticas** com domínio e fase preenchidos, e a query traz 7 testes com mocks (sem dependência de banco).

### Dois campos editoriais de baixo custo

Aproveitando a rodada, o [graphql-api#26](https://github.com/destaquesgovbr/graphql-api/pull/26) adicionou dois campos derivados de alto valor para análise editorial (UC-07), sem custo de query extra:

- `Article.publicationHour` (`Int`): a hora 0–23, calculada em Python a partir de `publishedAt`.
- `Agency.isRepublisher` (`Boolean!`): derivado do `code`, marcando agências republicadoras (`agencia_brasil`, `tvbrasil`, `ebc`, `radioagencia_nacional`) — como single source of truth, sem duplicar a lógica nos dois resolvers que constroem `Agency`.

A suíte completa terminou com **522 testes passando**.

## 3. Polimento e a release

O ciclo fechou com uma série de correções que separam "funciona" de "funciona bem", culminando numa release.

### Analytics sem buracos

O `agencyAnalytics` com `granularity=DAY` simplesmente **omitia** os dias sem publicações, criando buracos nos gráficos. O [graphql-api#23](https://github.com/destaquesgovbr/graphql-api/pull/23) introduziu `generate_series` no SQL diário, garantindo que todo dia do intervalo apareça com `article_count=0` via `COALESCE` (MONTH e WEEK seguem com `DATE_TRUNC`). O [graphql-api#24](https://github.com/destaquesgovbr/graphql-api/pull/24) consolidou esse gap-fill junto com `entityArticles`, `trendingEntities` e um fix de `topArticles` em `trendingThemes` — que era sempre retornado vazio e passou a popular até 5 artigos representativos por tema, com fallback silencioso.

### `/busca` vazia listava um erro

A tela `/busca` **sem termo e sem filtro** exibia "Ocorreu um erro ao carregar os resultados". A causa raiz, confirmada contra o backend real, era que o resolver `search` **rejeita query vazia** (`"Query must not be empty"`). O [portal#271](https://github.com/destaquesgovbr/portal/pull/271) passou a navegar cronologicamente via `listArticles` (a query `articles`, Postgres, ordenada por `published_at desc` com dedup) — o mesmo caminho do feed `/noticias` — e trocou o cabeçalho para "Explorar notícias" quando não há query. Validado com 122k+ artigos, 17/17 testes unitários e um E2E de regressão; o [portal#272](https://github.com/destaquesgovbr/portal/pull/272) promoveu a correção de `development` para `main`.

### O 500 do clipping

Acessar `/minha-conta/clipping` em produção devolvia "Application error" (digest `1082197660`). O [portal#269](https://github.com/destaquesgovbr/portal/pull/269) revelou duas camadas:

- **Sintoma:** no `Promise.all` da página, `listFollowedListings()` era a **única** das 5 chamadas sem `try/catch` — as demais degradavam graciosamente, mas essa propagava `UNAUTHENTICATED` e derrubava o SSR.
- **Causa raiz:** o usuário tinha sessão NextAuth válida, mas o access token Keycloak enviado ao graphql-api estava expirado. Quando `refreshGovBrToken` falha, devolve o token velho com `error: 'RefreshAccessTokenError'` — porém esse erro nunca era exposto na sessão. Resultado: sessão viva com token morto.

A correção atacou as duas: `getFollows()` ganhou `try/catch → []`, e a sessão passou a expor `session.error`, com o layout de rotas logadas redirecionando para re-login quando o refresh falha.

### A release e os slides

O [portal#270](https://github.com/destaquesgovbr/portal/pull/270) consolidou tudo numa release de `development` para `main` — **9 commits entre 11 e 24 de junho** — reunindo o arco inteiro de entidades (tela da notícia enriquecida, entidades canônicas, entidades relacionadas com visualização de rede, e "Entidades em Alta" na home) mais as correções de clipping e `/entidades`. Por fim, o [docs#54](https://github.com/destaquesgovbr/docs/pull/54) publicou um [deck de 6 slides](https://destaquesgovbr.github.io/docs/apresentacoes/secom-jun2026/) (16:9, HTML inline, ~100 KB, zero dependências externas) para a apresentação **DGB × SECOM de junho/2026**, cobrindo acervo, enriquecimento com IA, ferramentas para ASCOMs, a stack API+MCP+agente e o roadmap.

!!! tip "Os slides desta apresentação"
    O deck do **DGB × SECOM de junho/2026** está embutido abaixo e também
    publicado em
    **<https://destaquesgovbr.github.io/docs/apresentacoes/secom-jun2026/>**.

<div style="position:relative;width:100%;aspect-ratio:16/9;margin:1.5rem 0;
            border-radius:8px;overflow:hidden;border:1px solid var(--md-default-fg-color--lightest);">
  <iframe src="https://destaquesgovbr.github.io/docs/apresentacoes/secom-jun2026/deck.html"
          title="Slides: DGB × SECOM junho/2026" loading="lazy" allow="fullscreen"
          style="position:absolute;inset:0;width:100%;height:100%;border:0;"></iframe>
</div>

<p><a href="https://destaquesgovbr.github.io/docs/apresentacoes/secom-jun2026/" target="_blank" rel="noopener">⛶ Abrir os slides em tela cheia →</a></p>

## Antes e depois

| | Antes | Depois |
|---|---|---|
| Entidades em alta | scorer de pesquisa (NDCG@10 0.727) | DAG 4x/dia, NDCG@10 1.0, card na home |
| Páginas `/entidades` | 0 artigos (dependia de reprocessamento) | artigos via Postgres, independente do Typesense |
| Políticas públicas | palavras soltas nas notícias | 45 entidades canônicas com domínio e ciclo de vida |
| `/busca` vazia | "Ocorreu um erro" | lista cronológica ("Explorar notícias") |
| `/minha-conta/clipping` | 500 com token expirado | degrada + re-login automático |

## Números

| Métrica | Valor |
|--------|-------|
| Scorer de tendências | NDCG@10 **0.727 → 1.000** · 20 janelas |
| Ganho isolado (filtrar LOC) | **+22 pp** |
| Load de snapshot (índices 024) | ~640s → **~40s** por janela |
| DAG `compute_entity_trending` | **4x/dia** (`0 */6 * * *`) |
| Timeout de embedding evitado | ~327s → skip (`compute_embeddings=False`) |
| Políticas na ontologia | gazetteer 40+ · **45** em produção |
| Testes (graphql-api) | **522** passando |
| Release do portal | 9 commits (11–24 jun) |

## Lições

1. **Filtro certo bate feature nova.** No scorer, o maior salto (+22 pp) não veio de um sinal novo, mas de **remover** entidades LOC do ranking; e a nota perfeita veio de copiar os limites do oracle como filtros hard. Modelar o domínio venceu adicionar complexidade.
2. **A pegadinha de produção mora no deploy, não no algoritmo.** Um scorer NDCG@10=1.0 quase não rodou por um `cp` esquecido e por um timeout de embedding de 327s. Produtizar é onde a pesquisa encontra o Cloud SQL Auth Proxy — reserve tempo para isso.
3. **Não espere o reprocessamento; abra um caminho independente.** As páginas `/entidades` foram destravadas lendo o Postgres direto, sem depender do campo do Typesense que segue pendente. Um caminho de dados alternativo entrega valor hoje sem bloquear a migração de amanhã.
4. **A curadoria cobre o ponto cego do NER.** A Selic tinha 0 artigos por nunca ser extraída; um gazetteer com `provenance` explícito conserta o que o modelo automático não vê.

O ciclo que começou com entidades NER canônicas e um grafo de relações fecha aqui, no ar e nas mãos de quem usa: tendências detectadas automaticamente e exibidas na home, políticas públicas com identidade própria e o arco de entidades reunido numa release do portal. Os follow-ups conhecidos seguem abertos — o reprocessamento do `entity_canonical` no Typesense (infra#198) e a página `/politicas` que consome a query `policies()`. Da fundação semântica à aplicação consolidada, o arco desta série mostra o mesmo padrão repetido em cada frente: pesquisar com honestidade e produtizar com paciência — da canonicalização ao grafo, do agente à aplicação.

---

*Série **A evolução da plataforma DGB (jun–jul 2026)** · post 4 de 4.*
*Post anterior: [Gobus MCP: um agente que investiga o gov.br](2026-06-30-gobus-mcp-agente-govbr.md).*

