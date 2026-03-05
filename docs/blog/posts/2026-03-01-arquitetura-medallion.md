---
date: 2026-03-01
authors:
  - nitai
categories:
  - Arquitetura
  - Data Engineering
  - BigQuery
title: "Arquitetura Medallion: dados em camadas com Feature Store JSONB"
hide:
  - toc
---

# Arquitetura Medallion: dados em camadas com Feature Store JSONB

Em um único dia, formalizamos a arquitetura de dados do DGB com o padrão Medallion (Bronze/Silver/Gold), implementamos as fases 0 a 3, migramos o Composer para `southamerica-east1` e adicionamos sentiment analysis e entity extraction ao enrichment — tudo sem downtime. **12 PRs** em **5 repos**, incluindo o primeiro ADR do projeto.

<!-- more -->

---

## O que é o Medallion e por que agora

O pipeline do DGB cresceu organicamente: scraper → PostgreSQL → Typesense → Portal. Mas com Pub/Sub (post anterior) disparando eventos em cadeia, os dados passaram a fluir por múltiplos caminhos simultaneamente. Sem uma estrutura clara de camadas, era questão de tempo até confundir dado bruto com dado enriquecido.

O padrão [Medallion](https://www.databricks.com/glossary/medallion-architecture) organiza os dados em três camadas:

```
Bronze (raw)          Silver (cleaned)       Gold (enriched)
─────────────         ──────────────         ───────────────
Dado como veio        Normalizado,           Classificado,
do scraper            deduplicado            com features
                                             prontas para consumo
```

## ADR-001: a decisão documentada

[`docs#35`](https://github.com/destaquesgovbr/docs/pull/35) formalizou a decisão como o primeiro Architecture Decision Record do projeto. O ADR define:

- **Bronze**: dados brutos no GCS (Parquet) + BigQuery external tables
- **Silver**: dados limpos no PostgreSQL (`news` table existente, já normalizada)
- **Gold**: features derivadas em `news_features` (JSONB) — themes, sentiment, entities, embeddings

A decisão-chave: **Feature Store leve via JSONB no PostgreSQL**, sem introduzir um sistema dedicado. O campo `features JSONB` permite adicionar novas features sem migrations.

## Implementação: fases 0-3

### Fase 0 — Fundação (GCS + BigQuery)

- Bucket `dgb-data-lake` com lifecycle tiering automático (Standard → Nearline 90d → Coldline 365d)
- BigQuery dataset `bronze` com external tables sobre o GCS
- IAM granular: scraper só escreve, Composer lê

### Fase 1 — Bronze Ingestion

- DAG `bronze_news_ingestion`: exporta `news` do PostgreSQL para Parquet no GCS, particionado por data
- DDL BigQuery para views sobre os Parquet files

### Fase 2 — Feature Store

- Tabela `news_features` no PostgreSQL com colunas `unique_id`, `features JSONB`, timestamps
- DAGs de backfill para popular features existentes (themes, summary)

### Fase 3 — Gold Analytics

- DAG `sync_analytics_to_bigquery`: pageviews e engagement do Umami para BigQuery
- DAG `export_gold_features`: features agregadas para análise no BigQuery

### PRs coordenados

| PR | Repo | Escopo |
|----|------|--------|
| [`docs#35`](https://github.com/destaquesgovbr/docs/pull/35) | docs | ADR-001 |
| [`data-platform#98`](https://github.com/destaquesgovbr/data-platform/pull/98) | data-platform | Fases 0-3 completas (DAGs, jobs, SQL, testes) |
| [`infra#98`](https://github.com/destaquesgovbr/infra/pull/98) | infra | Terraform: GCS bucket, BigQuery dataset, IAM |
| [`data-science#22`](https://github.com/destaquesgovbr/data-science/pull/22) | data-science | Enrichment: sentiment + entities para Feature Store |
| [`data-platform#99`](https://github.com/destaquesgovbr/data-platform/pull/99) | data-platform | Fix SQL BigQuery + deploy de DAGs |
| [`data-platform#100`](https://github.com/destaquesgovbr/data-platform/pull/100) | data-platform | Fix dialeto SQLAlchemy + tipos Parquet |

## Migração do Composer para southamerica-east1

Aproveitando a janela de mudanças, migramos o Cloud Composer de `us-central1` para `southamerica-east1` — consolidando todos os recursos GCP na mesma região:

- [`infra#97`](https://github.com/destaquesgovbr/infra/pull/97) — Terraform: novo Composer na região correta
- [`reusable-workflows#4`](https://github.com/destaquesgovbr/reusable-workflows/pull/4) — atualiza região no workflow compartilhado
- [`data-platform#97`](https://github.com/destaquesgovbr/data-platform/pull/97) — docs atualizados
- [`infra#99`](https://github.com/destaquesgovbr/infra/pull/99), [`infra#100`](https://github.com/destaquesgovbr/infra/pull/100) — fixes de permissões IAM

## Enrichment expandido: sentiment + entities

[`data-science#22`](https://github.com/destaquesgovbr/data-science/pull/22) estendeu o enrichment worker para extrair, do **mesmo prompt Bedrock** (custo marginal zero):

- **Sentiment**: positivo/negativo/neutro com score de confiança
- **Entities**: pessoas, organizações, locais mencionados na notícia

Os resultados vão para o Feature Store (`news_features.features` JSONB), prontos para consumo pelo portal e por análises no BigQuery.

## Números

| Métrica | Valor |
|---------|-------|
| PRs mergeados | 12 |
| Repos tocados | 5 |
| DAGs novas | 4 (bronze ingestion, sync analytics, export gold, backfill) |
| Tabelas criadas | 2 (news_features, BigQuery external) |
| Custo incremental estimado | +$2-4/mês |
| Downtime | 0 |

---

*Próximo post: [Analytics, Auth e Portal v1.0.0](2026-03-03-portal-v1.md)*
