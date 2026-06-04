# ADR-002: Fachada GraphQL única para acesso a dados

- **Status**: Aceita
- **Data**: 2026-06-04
- **Autor**: Nitai Bezerra

## Contexto

Até 2026, cada consumidor da plataforma falava **direto** com os backends de
dados:

- O **portal** lia/escrevia Firestore (clippings, marketplace, push, usuários) via
  Firebase Admin SDK, consultava PostgreSQL para temas/órgãos e o Typesense para
  busca — tudo em rotas REST internas (`/api/clipping`, `/api/clippings`,
  `/api/push`, `/api/widgets`) e Server Components com acesso direto.
- Os **workers de dados** (feature-worker, typesense-sync-worker, bronze-writer)
  liam o PostgreSQL `govbrnews` diretamente via `DATABASE_URL`/asyncpg.

### Problemas identificados

1. **Acoplamento ao formato dos backends.** Cada consumidor conhecia o schema do
   Firestore (camelCase, locais de coleção), o SQL do Postgres e o índice do
   Typesense. Mudar qualquer backend vazava para vários repos.
2. **Lógica e autenticação duplicadas.** Regras de autoria, permissões e
   validação de JWT ficavam reimplementadas em cada rota REST do portal.
3. **Contrato implícito e não-tipado.** Sem um schema único, divergências entre
   o que o cliente esperava e o que o backend entregava só apareciam em runtime
   (e, como se viu na R1, às vezes só no browser).
4. **Difícil de evoluir.** Adicionar um campo significava tocar portal + rotas +
   acesso a dados, sem um ponto único de versionamento.

## Decisão

Introduzir um serviço **`graphql-api`** (Strawberry GraphQL + FastAPI, Cloud Run)
como **fachada de dados única**. Todos os consumidores passam a falar GraphQL com
esse serviço, que é o único a conhecer Firestore/PostgreSQL/Typesense.

### Princípios

- **Schema tipado e code-first**, derivado do código Python; o SDL é a referência
  versionada (gerado a cada build).
- **Auth centralizada** em duas camadas: JWT de usuário (Keycloak) e OIDC de
  service account (workers). Permissões declarativas por campo.
- **Subscriptions-first** para clippings (relação usuário↔clipping via
  `subscriptions` com `role`), suportando o marketplace sem duplicação.
- **Rollout por feature flag** (GrowthBook `graphql.*`), com fallback REST mantido
  durante a transição e removido no cleanup pós-estabilização.
- **Streaming via SSE** (`/graphql/stream`) para o agente de IA, com passthrough
  OIDC ao clipping worker.

### Escopo da R1 (entregue)

- Portal migrado (atrás de flags) para clippings, marketplace, push, widgets,
  busca e agente.
- Superfície **interna** para os workers já exposta no schema (`newsById`,
  `newsForTypesense`, `newsBatchForBigquery`, `upsertFeatures`, …) — a migração
  dos workers em si é um follow-up.

## Alternativas consideradas

- **Manter REST por endpoint.** Rejeitada: perpetua o contrato implícito e a
  duplicação de auth; sem introspecção nem tipos.
- **Manter acesso direto aos backends.** Rejeitada: é exatamente o acoplamento que
  motivou a mudança.
- **gRPC.** Descartada para o portal (browser/Next.js); GraphQL casa melhor com o
  cliente web e com a necessidade de seleção de campos e subscriptions.

## Consequências

### Positivas

- Consumidores desacoplados do formato dos backends; um ponto único de evolução.
- Autenticação e regras de negócio centralizadas e testáveis.
- Contrato tipado e introspectável; a referência de schema é gerada do código.

### Negativas / riscos

- **Risco de drift cliente↔schema.** Materializou-se na R1 (operações do portal
  escritas contra um schema planejado, não o implementado). Mitigação: o gate de
  validação passou a ser **E2E no browser** (Playwright contra portal+graphql-api),
  não `curl` headless — porque o `curl` mascara CSP e o código TypeScript do
  cliente. Catálogo de bugs: `graphql-api/_plan/R1-DRIFT-CATALOG.md`.
- **CSP do portal precisa liberar a origin do serviço** (`connect-src`) — foi a
  causa-raiz nº 1 da R1.
- **Camada extra** entre cliente e dados: uma latência adicional e mais um serviço
  para operar (mitigado por DataLoaders e cache por request).

## Status de adoção

- **Portal:** migrado em staging (R1), atrás de flags; produção segue o RUNBOOK-R1.
- **Workers:** ainda acessam o PostgreSQL diretamente; migração para a fachada é o
  próximo passo de desacoplamento.
- Referência do serviço: [módulo GraphQL API](../../modulos/graphql-api.md).
