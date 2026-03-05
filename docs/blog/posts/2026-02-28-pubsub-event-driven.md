---
date: 2026-02-28
authors:
  - nitai
categories:
  - Arquitetura
  - Pub/Sub
  - Cloud Run
  - Pipeline
title: "De DAGs batch para event-driven: a migração Pub/Sub em 48 horas"
hide:
  - toc
---

# De DAGs batch para event-driven: a migração Pub/Sub em 48 horas

Dois dias depois de desmembrar o monolito, o pipeline inteiro de processamento de notícias ganhou uma nova arquitetura: event-driven com Pub/Sub. Scrapers publicam eventos, workers processam em cadeia, e o que antes rodava a cada 15 minutos via DAGs agora reage em segundos. Foram **~25 PRs** em **8 repos**, com 3 workers novos, 1 repo novo (`push-notifications`), e a aposentadoria do Cogfy como motor de enriquecimento.

<!-- more -->

---

## Contexto: o gargalo do batch

No post anterior, contamos como o monolito `data-platform` foi desmembrado em repos especializados. Cada um deployava suas DAGs no Composer, e o Airflow orquestrava tudo com schedules de 10-15 minutos. Funcionava, mas tinha dois problemas:

1. **Latência**: uma notícia scrapeada às 10:01 só era enriquecida às 10:15, indexada às 10:30 e publicada no Fediverso às 10:45. Quase uma hora de delay.
2. **Acoplamento temporal**: cada DAG precisava "adivinhar" quando a anterior teria terminado. Slots, retries e dependências cross-DAG viravam uma teia frágil.

A solução estava no plano [`PUBSUB-EVENT-DRIVEN.md`](https://github.com/destaquesgovbr/data-platform/blob/main/_plan/PUBSUB-EVENT-DRIVEN.md): trocar o modelo pull (DAG consulta o banco) por push (evento dispara processamento).

---

## Quinta-feira (27/fev): preparando o terreno

### AWS Bedrock para LLM

Antes de montar o pipeline event-driven, precisávamos resolver o enriquecimento via LLM. O Cogfy (serviço externo que usávamos para classificação temática) tinha se tornado um gargalo — lento, sem controle de prompt, e caro. A decisão: migrar para AWS Bedrock com Claude 3 Haiku, chamado diretamente.

No repo `data-science`, dois PRs construíram a DAG `enrich_news_llm`:
- [`data-science#15`](https://github.com/destaquesgovbr/data-science/pull/15) — DAG + plugin com `NewsClassifier`, taxonomia de temas e job completo (fetch → classify → update PG)
- [`data-science#16`](https://github.com/destaquesgovbr/data-science/pull/16) — fix no prompt para forçar geração do campo `summary` (o Haiku 3 omitia sem instrução explícita)

Na infra:
- [`infra#89`](https://github.com/destaquesgovbr/infra/pull/89) — Terraform para boto3 no Composer + secret `aws_bedrock` no Secret Manager
- [`infra#90`](https://github.com/destaquesgovbr/infra/pull/90) — refactor: gerenciar a secret version manualmente (credenciais AWS fora do state do Terraform)

E a limpeza correspondente:
- [`data-platform#92`](https://github.com/destaquesgovbr/data-platform/pull/92) — remove toda a integração com Cogfy do pipeline

### Ambiente local Airflow

Em paralelo, três repos ganharam ambiente de desenvolvimento local com Astro CLI, consolidando o padrão que o `activitypub-server` tinha inaugurado na semana anterior:
- [`scraper#6`](https://github.com/destaquesgovbr/scraper/pull/6)
- [`embeddings#5`](https://github.com/destaquesgovbr/embeddings/pull/5)
- [`data-publishing#1`](https://github.com/destaquesgovbr/data-publishing/pull/1)

### Scraper: refactoring e campo `active`

- [`scraper#5`](https://github.com/destaquesgovbr/scraper/pull/5) — unificação de patterns dos managers (remove código duplicado)
- [`scraper#4`](https://github.com/destaquesgovbr/scraper/pull/4) (Miguel) — campo `active` no YAML das agências para habilitar/desabilitar sem deletar

---

## Sexta-feira (28/fev): o dia do Pub/Sub

Este foi o dia mais intenso. Em ~14 horas, a infraestrutura Pub/Sub foi criada, 4 workers foram implementados, e as DAGs batch foram aposentadas.

### A infraestrutura (manhã)

Tudo começou com o Terraform. O PR [`infra#91`](https://github.com/destaquesgovbr/infra/pull/91) criou toda a malha:

```
Topics                          Subscriptions → Workers
─────────────────────────────────────────────────────────
dgb.news.scraped        ──→     enrichment-worker (data-science)
                         ──→     typesense-sync (data-platform)
dgb.news.enriched       ──→     embeddings-api (embeddings)
                         ──→     federation-web (activitypub-server)
                         ──→     push-notifications
dgb.news.embedded              (terminal — future use)
```

Cada topic tem um DLQ (dead-letter queue) correspondente. Push subscriptions com OIDC authentication. Retry policy com backoff exponencial (10s → 600s). Tudo parametrizado.

Claro, o primeiro `terraform apply` não passou. Dois fixes rápidos:
- [`infra#92`](https://github.com/destaquesgovbr/infra/pull/92) — SA do GitHub Actions precisava de `pubsub.editor`
- [`infra#93`](https://github.com/destaquesgovbr/infra/pull/93) — upgrade para `pubsub.admin` (faltava `setIamPolicy` para DLQs)

### Os workers (tarde)

Com a infraestrutura no ar, os workers foram implementados em paralelo — cada um no seu repo, cada um reutilizando a lógica já existente:

**Typesense Sync Worker** — [`data-platform#93`](https://github.com/destaquesgovbr/data-platform/pull/93)
Recebe evento de `dgb.news.scraped`, faz upsert no Typesense. Zero duplicação: reutiliza `_build_typesense_query`, `prepare_document` e `get_client` existentes. Dockerfile para Cloud Run.

**Enrichment Worker** — [`data-science#18`](https://github.com/destaquesgovbr/data-science/pull/18)
Recebe de `dgb.news.scraped`, classifica via Bedrock (temas + summary), atualiza PostgreSQL, publica `dgb.news.enriched`. Reutiliza `NewsClassifier` e `update_news_enrichment`. Processamento idempotente.

**Embeddings Worker** — [`embeddings#6`](https://github.com/destaquesgovbr/embeddings/pull/6)
Endpoint `POST /process` no `embeddings-api` existente. Recebe de `dgb.news.enriched`, gera embedding com modelo local (sem HTTP hop), atualiza PG, publica `dgb.news.embedded`.

**Federation Worker** — [`activitypub-server#9`](https://github.com/destaquesgovbr/activitypub-server/pull/9)
Migração completa: a DAG `federation_publish` do Airflow foi substituída por `POST /process` com Pub/Sub push. Busca artigo do banco, insere na fila de publicação com `ON CONFLICT DO NOTHING`. A DAG e o `docker-compose.yml` do Astro CLI foram removidos.

E um fix na infra que só apareceu em runtime:
- [`infra#94`](https://github.com/destaquesgovbr/infra/pull/94) — subscription de embeddings apontava para service errado (`embeddings_worker` vs `embeddings_api`)

### O scraper publica eventos

A peça que conecta tudo: [`scraper#9`](https://github.com/destaquesgovbr/scraper/pull/9). Adicionou `EventPublisher` com graceful degradation — publica em `dgb.news.scraped` após cada INSERT no PostgreSQL. Se a env var `PUBSUB_TOPIC_NEWS_SCRAPED` não existe, é no-op (backward compatible).

### DAGs aposentadas

Com os workers no ar, as DAGs batch de enriquecimento, embeddings e federation foram removidas:
- [`data-science#20`](https://github.com/destaquesgovbr/data-science/pull/20) — remove `enrich_news_llm` DAG
- [`embeddings#7`](https://github.com/destaquesgovbr/embeddings/pull/7) — remove embeddings DAG

### Push Notifications: o novo membro do pipeline

O evento `dgb.news.enriched` ganhou mais um subscriber: push notifications. Neste dia, a infra foi criada:
- [`infra#95`](https://github.com/destaquesgovbr/infra/pull/95) — subscription Pub/Sub para federation
- [`infra#96`](https://github.com/destaquesgovbr/infra/pull/96) — Cloud Run service `push-notifications` com Pub/Sub, VAPID keys no Secret Manager

### Documentação

- [`docs#34`](https://github.com/destaquesgovbr/docs/pull/34) — página de arquitetura dos Pub/Sub workers no docs site

---

## O antes e depois

### Antes (27/fev): batch com DAGs

```
Scraper (15min) → enrich DAG (10min) → embeddings DAG (10min) → federation DAG (10min)
                                                                → typesense DAG (10min)
Latência total: ~45-60 minutos
```

### Depois (28/fev): event-driven com Pub/Sub

```
Scraper INSERT
  └→ dgb.news.scraped
       ├→ Enrichment Worker (~5s) → dgb.news.enriched
       │     ├→ Embeddings Worker (~3s) → dgb.news.embedded
       │     ├→ Federation Worker (~2s)
       │     └→ Push Notifications (~1s)
       └→ Typesense Sync (~2s)

Latência total: ~10-15 segundos
```

---

## Números

| Métrica | Valor |
|---------|-------|
| PRs mergeados | ~25 |
| Repos tocados | 8 (infra, data-platform, data-science, embeddings, scraper, activitypub-server, push-notifications, docs) |
| Workers criados | 4 (enrichment, typesense-sync, embeddings, federation) |
| Topics Pub/Sub | 3 + 4 DLQs |
| DAGs aposentadas | 3 |
| Latência: antes → depois | ~45min → ~15s |
| Dias | 2 |

---

## Lições

1. **Infraestrutura primeiro, workers depois.** Criar os topics, subscriptions e DLQs no Terraform antes de escrever uma linha de código nos workers permitiu validar a topologia completa. Os workers foram "só" implementar `POST /process`.

2. **Graceful degradation desbloqueia deploys independentes.** O `EventPublisher` do scraper com no-op quando a env var não existe permitiu mergear o PR do scraper antes da infra Pub/Sub estar no ar. Cada peça deployou no seu ritmo.

3. **Reutilizar lógica existente é o superpoder de repos bem decompostos.** Cada worker reutilizou funções que já existiam (classificador, prepare_document, get_client). O desmembramento da semana anterior pagou dividendos imediatos.

4. **DLQs são seguro barato.** Configurar dead-letter queues desde o dia zero custou 10 linhas extras de Terraform e já salvou mensagens perdidas nos primeiros dias.

5. **De 45 minutos para 15 segundos.** A mudança de arquitetura mais impactante do projeto até agora. Não foi otimização — foi mudança de paradigma.

---

*Próximo post: [Arquitetura Medallion — dados em camadas com Feature Store JSONB](2026-03-01-arquitetura-medallion.md)*
