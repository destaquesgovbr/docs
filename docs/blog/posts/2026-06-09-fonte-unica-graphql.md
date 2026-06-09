---
date: 2026-06-09
authors:
  - nitai
categories:
  - Arquitetura
  - GraphQL
  - Refatoração
  - Testes
title: "Fonte única de dados: o desacoplamento BD→GraphQL e os bugs que só o navegador pegou"
hide:
  - toc
---

# Fonte única de dados: o desacoplamento BD→GraphQL e os bugs que só o navegador pegou

Cinco dias depois de a [fachada GraphQL](2026-06-04-fachada-graphql-dgb.md) entrar no ar, ela ainda dividia o trabalho com o passado: o portal falava GraphQL, sim — mas atrás de feature flags, com fallback REST por baixo, e várias páginas públicas ainda liam o Firestore e o Typesense direto. Existir não era o suficiente; faltava ser o **único** caminho. Este post conta a história de cortar esse último cabo — Fases 1 a 4 do desacoplamento — e de como um punhado de bugs que o `build` jurava não existir só apareceu quando um navegador de verdade exercitou o caminho `browser → portal → graphql-api`.

<!-- more -->

!!! tip "O serviço que virou fonte única"
    Tudo o que este post descreve é servido pelo **graphql-api**, agora em
    `v1.0.0`. A referência de schema (gerada do código) e o playground GraphiQL
    estão em **<https://destaquesgovbr.github.io/graphql-api/>**.

---

## Onde a fachada parou

O [post anterior](2026-06-04-fachada-graphql-dgb.md) terminou com uma lista de follow-ups sob o título honesto de "desacoplar o resto". O diagnóstico era que a fachada, sozinha, não desacopla nada enquanto o consumidor mantém dois caminhos abertos:

```
                      ┌──────── caminho novo ────────┐
   Portal Next.js ──┤                                 ├──> graphql-api ──> backends
                      └──────── caminho legado ───────┘         │
                              (REST + Firestore/Typesense direto via firebase-admin)
```

Esse desenho tem um custo escondido: o caminho legado **mascara** problemas. Um clipping criado pela fachada podia não aparecer numa página cujo SSR ainda lia a coleção antiga do Firestore — e a suíte passava verde, porque os dois caminhos discordavam em silêncio. Enquanto os dois existem, "funciona" não quer dizer "está certo": quer dizer "pelo menos um dos caminhos respondeu".

A meta desta rodada foi fechar o desenho num fio só:

```
   Portal Next.js ──> graphql-api ──> Firestore · PostgreSQL · Typesense
```

Sem flag, sem fallback, sem `firebase-admin` no portal público.

---

## As fases

O trabalho foi quebrado em fases de poucos arquivos cada, para caber em poucos deploys de produção e para que cada etapa tivesse um gate E2E real antes da seguinte.

### Fase 1B — SSR das features sem Firestore

As páginas das features (clipping, marketplace) ainda renderizavam no servidor lendo o Firestore direto via `firebase-admin`. Foram migradas para resolvers GraphQL ([portal#248](https://github.com/destaquesgovbr/portal/pull/248)), apoiadas por novos resolvers SSR do lado do serviço — `release`, `myFollowedListings`, passthrough do Telegram e um `digestPreview` computado no servidor ([graphql-api#11](https://github.com/destaquesgovbr/graphql-api/pull/11)).

### Fase 2A/2B — conteúdo público sem Typesense direto

O coração do portal — landing, busca, página de artigo, temas, órgãos, feeds e os artigos de um release — lia o Typesense direto. A Fase 2A criou no serviço o arquivo `public_content.py` com os resolvers que faltavam ([graphql-api#12](https://github.com/destaquesgovbr/graphql-api/pull/12)):

- **`relatedArticles`** — "artigos recentes do mesmo tema", servido pelo Typesense por _theme-code_ (OR entre os níveis L1/L2/L3, dedup por `content_hash`). Foi batizado de `relatedArticles` de propósito, para não colidir com o resolver **interno** `similarArticles`, que é por embeddings no Postgres — são mecanismos diferentes.
- **`themeArticleCounts`** — contagem por tema num período, via `group_by` no índice.
- **`releaseArticles`** — os artigos de um release, com a mesma autorização do `release(id)` (público quando o listing fonte está ativo).
- **`estimateRecorteCount`** — estimativa de quantos artigos um recorte renderia.

Com os campos prontos, a Fase 2B trocou todas essas páginas para a fachada ([portal#249](https://github.com/destaquesgovbr/portal/pull/249)), e a Fase 2C adicionou um spec E2E público novo que dirige `/noticias`, `/busca`, `/artigos/[id]`, `/temas/[label]` e `/orgaos/[key]` com dados derivados dinamicamente do próprio índice.

### Fase 4 — apagar o legado

Com tudo migrado e validado, as rotas REST que sobravam foram **removidas** ([portal#251](https://github.com/destaquesgovbr/portal/pull/251)): `/api/clipping`, `/api/clippings`, `/api/push`, `/api/widgets` e o `clipping-worker.ts`. Antes disso, a cauda do R1 já tinha cortado as feature flags e o fallback REST, deixando o GraphQL como caminho único e ligando push/widgets ([portal#243](https://github.com/destaquesgovbr/portal/pull/243)).

Os **feeds RSS/JSON** (`/feed.*`, `…/feed.{json,xml}`) e `/api/auth/**` foram mantidos de propósito — feeds têm assinantes externos; auth é do NextAuth. Removê-los junto seria quebrar consumidores de fora.

---

## Build verde, runtime vermelho

Aqui está a parte que vale a história. Todas as fases passavam no `pnpm build`, no `tsc`, no `vitest` com mocks e no codegen sem drift. E mesmo assim, ao apontar a suíte E2E para o graphql-api **de produção**, o caminho real desmoronou em pontos que nenhuma dessas verificações conseguia enxergar.

**O erro de fronteira RSC.** No Next.js, um módulo `'use client'` vira uma _client reference_; chamar uma factory exportada por ele a partir do servidor estoura — `Attempted to call createGraphQLContentService from the server but it's on the client`. As server actions importavam o factory do `index.ts` `'use client'`, não do módulo server-safe. O `build` **não pega** isso: só explode em runtime. A correção foi importar `createGraphQL*Service` de `@/services/X/graphql` em 15 arquivos. Sem o E2E no navegador, isso teria ido para produção verde.

**A chave que não podia ler.** A busca quebrou em cascata contra o Typesense real, cada bug só visível com tráfego de verdade:

- O datasource subia `TypesenseDatasource()` sem cliente ([graphql-api#14](https://github.com/destaquesgovbr/graphql-api/pull/14)).
- `get_article_by_id` chamava `.retrieve()` — mas a API key é _search-only_ e devolvia `401`. Reescrito para buscar via `.documents.search()` com `filter_by` ([#14](https://github.com/destaquesgovbr/graphql-api/pull/14)).
- A coleção estava hardcoded como `'articles'` e dava `404`; o índice real é `news` (`COLLECTION_NAME`) ([graphql-api#15](https://github.com/destaquesgovbr/graphql-api/pull/15)).
- `published_at` é Unix em segundos, não ISO — `'int' object has no attribute 'isoformat'`. A busca foi roteada inteira pelo `search_articles`, que já trata timestamps, coleção, filtros e dedup ([graphql-api#16](https://github.com/destaquesgovbr/graphql-api/pull/16)).

**A autorização que diferia por campo.** As páginas públicas de release usavam `clipping.releases`, que é _auth-gated_ (levanta `UNAUTHENTICATED`), quando o caminho público correto era `MarketplaceListing.releases` via `listListingReleases`. Verde no teste autenticado, `403` para o visitante anônimo.

**O efeito colateral de rodar o gate.** Rodar o E2E repetidas vezes disparou o _lockout_ de brute-force do Keycloak (Direct Access Grant). A correção não foi afrouxar o Keycloak, e sim fazer os testes **compartilharem o token do bot** — cache em memória → arquivo → refresh → password grant ([portal#250](https://github.com/destaquesgovbr/portal/pull/250)). E o próprio fix do RSC quebrou 6 arquivos de teste que mockavam `@/services/content` em vez de `…/content/graphql` — pego pelo CI, corrigido junto.

O fio condutor: **mock testa o que você imaginou; o navegador testa o que existe.** `curl` no graphql-api headless mascara o caminho real porque pula a fronteira RSC, o CSP e o cliente TypeScript do portal. O gate de verdade é o E2E no browser — e foi ele que transformou oito "deploys verdes que dariam pau em produção" em oito PRs de correção antes da promoção.

---

## Antes e depois

| | Antes | Depois |
|---|---|---|
| Caminho de dados do portal | REST + GraphQL (flag) + Firestore/Typesense direto | **só GraphQL** |
| `firebase-admin` no portal público | lê coleções no SSR | removido |
| Cliente Typesense no portal | busca/artigos/temas direto | removido |
| Feature flags de rollout | 5 (clippings, marketplace, agent, push, widgets) | 0 — caminho único |
| Rotas REST de feature | `/api/clipping(s)`, `/api/push`, `/api/widgets` | apagadas (feeds mantidos) |
| Contrato cliente↔dados | implícito, divergência em runtime | schema tipado, gate anti-drift no codegen |

---

## Números

| Métrica | Valor |
|--------|-------|
| Fases entregues | 1B · 2A · 2B · 2C · 4 (+ cauda R1) |
| E2E `e2e/graphql` contra produção | **25 passed · 2 skipped · 0 failed** |
| Bugs reais pegos pelo gate E2E | 8 (RSC, 4× busca, auth de release, lockout, mocks) |
| Commits na release de produção | 22 ([portal#253](https://github.com/destaquesgovbr/portal/pull/253)) |
| Deploys de produção no graphql-api | ~5 (fases batidas para minimizar) |
| Versões publicadas | portal **v6.0.0** · graphql-api **v1.0.0** |
| PRs graphql-api | #9 · #10 · #11 · #12 · #13 · #14 · #15 · #16 |
| PRs portal | #243 · #245–#251 · #253 |

---

## Lições

1. **Dois caminhos não é transição, é dívida com juros.** Enquanto o fallback existe, ele esconde o estado real — um caminho responde pelo outro e a suíte fica verde mentindo. O desacoplamento só acontece de fato quando o legado é **apagado**, não desabilitado.
2. **`build` valida sintaxe; só o runtime no navegador valida a fronteira.** O erro RSC, os bugs da chave search-only, o tipo do timestamp, a autorização por campo — nenhum apareceu no `build`, no `tsc` ou no `vitest` com mocks. Apareceram quando um browser de verdade percorreu `portal → graphql-api → Typesense`. Esse é o gate.
3. **Mock testa a sua hipótese; produção testa a realidade.** Os mocks assumiam a coleção `articles`, o `.retrieve()`, o ISO. O índice real tinha `news`, key _search-only_ e Unix seconds. Rodar o E2E contra o serviço de produção foi o que revelou a diferença.
4. **Quando o gate dói, conserte o gate — não o sistema.** O lockout do Keycloak foi resolvido compartilhando sessão entre os testes, não afrouxando a política de brute-force. O teste passou a ser bom cidadão do mesmo backend que protege.
5. **Fatie para deployar pouco.** Quebrar em fases de poucos arquivos manteve cada deploy completo e auditável, e deu um gate E2E entre cada uma — o que tornou possível atribuir cada bug a uma mudança específica.

A fachada agora não é mais uma opção entre duas: é **o** caminho. Próximo passo do arco continua sendo tirar os _workers_ de dados do Postgres direto — rastreado no Epic [docs#46](https://github.com/destaquesgovbr/docs/issues/46). Um só fio para os dados do DGB, e ele passa pelo schema.
