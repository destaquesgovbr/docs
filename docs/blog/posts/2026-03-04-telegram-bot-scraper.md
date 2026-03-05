---
date: 2026-03-04
authors:
  - nitai
categories:
  - Telegram
  - Scraper
  - Push Notifications
title: "Bot Telegram e scraper resiliente: push notifications v2 e otimização de coleta"
hide:
  - toc
---

# Bot Telegram e scraper resiliente: push notifications v2 e otimização de coleta

O pipeline event-driven disparava notificações web push, mas faltava o canal mais direto: Telegram. Em paralelo, o scraper ganhou otimizações que cortaram requests HTTP pela metade e corrigiram agências com falha persistente. **~12 PRs** em **5 repos**, incluindo 2 repos novos (`push-notifications`, `telegram-bot`) e infraestrutura completa no Cloud Run.

<!-- more -->

---

## Push Notifications v2

O serviço `push-notifications` já existia desde o post do Pub/Sub, mas a v1 era mínima: recebia evento, mandava web push para todos os subscribers. A v2 trouxe personalização real.

### Filtros expandidos + auth

[`push-notifications#1`](https://github.com/destaquesgovbr/push-notifications/pull/1):

- **Filtros granulares**: themes L2/L3, tags e keywords (v1 só tinha L1)
- **Cooldown de 15min** entre notificações para o mesmo subscriber (anti-spam)
- **`user_id` opcional** para vincular subscriptions a usuários autenticados
- **Migração de dados**: converte theme labels existentes para codes

### Notificações Telegram com formato rico

[`push-notifications#2`](https://github.com/destaquesgovbr/push-notifications/pull/2):

- `telegram_sender.py` com envio de foto (`sendPhoto`) + fallback para texto (`sendMessage`)
- Formato rico: agência, categoria, título, resumo, data e link
- Handler despacha por canal: webpush vs telegram
- Migração: colunas `channel`, `chat_id`, `username` em `push_subscriptions`

---

## Bot Telegram: @destaquesgovbr_bot

O bot permite que usuários se inscrevam em agências, temas e keywords via menus inline — zero digitação exceto para busca.

### Arquitetura

```
Telegram API
  └→ Webhook POST /telegram/webhook
       └→ bot.py: handle_update()
            ├→ /start → menu principal
            ├→ Seguir Agências → keyboard com TOP_AGENCIES + busca
            ├→ Seguir Temas → keyboard paginado (8/página, L1→L2)
            └→ Keywords → entrada de texto livre
```

O bot compartilha o banco `govbrnews` (tabela `push_subscriptions`) com o serviço `push-notifications`. Comunicação é via shared DB — sem chamadas diretas entre serviços.

### Infra Cloud Run

[`infra#116`](https://github.com/destaquesgovbr/infra/pull/116) criou toda a infraestrutura:

| Recurso | Detalhe |
|---------|---------|
| Service Account | `destaquesgovbr-tg-bot` |
| Artifact Registry | `destaquesgovbr-telegram-bot` (cleanup 30d) |
| Secret Manager | `telegram-bot-token`, `telegram-webhook-secret` |
| Cloud Run | Webhook mode, scale-to-zero |
| WIF binding | Deploy via GitHub Actions |

---

## Scraper resiliente

### Known URL fence

[`scraper#12`](https://github.com/destaquesgovbr/scraper/pull/12) — a otimização mais impactante do scraper:

1. Antes de scrapear uma agência, consulta URLs recentes no PostgreSQL
2. Artigos com URL já conhecida: **skip sem fetch** (economia de HTTP request)
3. **3 artigos consecutivos conhecidos = parada antecipada** ("fence")

Na prática: se as 3 primeiras notícias da listagem já são conhecidas, o scraper para de processar a página. Para a maioria das agências, isso significa scrapear 3-5 artigos em vez de 20-30. Redução de ~60% nos HTTP requests.

Backward-compatible: sem `known_urls`, comportamento idêntico ao anterior. 11 testes unitários cobrem os cenários.

### URLs de agências com falha persistente

[`scraper#14`](https://github.com/destaquesgovbr/scraper/pull/14) — corrigiu 4 das 12 agências com falha persistente:

| Agência | Problema | Correção |
|---------|----------|----------|
| `ctir` | URL com `/2025` hardcoded | Removido sufixo de ano |
| `sri` | URL profunda com path longo | Simplificado para `/noticias` |
| `hfa` | `?b_start:int=0` duplicado pelo scraper | Removido query param |
| (4a) | URL inacessível | Corrigida |

### Referências HuggingFace em logs

[`scraper#8`](https://github.com/destaquesgovbr/scraper/pull/8) (Mauricio) — cleanup de referências ao HuggingFace nos logs do scraper (legado da época em que o scraper fazia upload direto).

---

## Números

| Métrica | Valor |
|---------|-------|
| PRs mergeados | ~12 |
| Repos tocados | 5 (push-notifications, infra, scraper, telegram-bot, portal) |
| Repos novos no pipeline | 2 (push-notifications, telegram-bot) |
| HTTP requests economizados | ~60% (known URL fence) |
| Agências corrigidas | 4 |

---

## Situação atual do pipeline

Após esta semana de posts (26/fev → 4/mar), o pipeline completo é:

```
~155 Agências Gov.BR
  └→ Scraper (Cloud Run, 10min, known URL fence)
       └→ PostgreSQL INSERT + Pub/Sub event
            ├→ Enrichment Worker (Bedrock → themes, summary, sentiment, entities)
            │     └→ dgb.news.enriched
            │          ├→ Embeddings Worker (local model → vector)
            │          ├→ Federation Worker (ActivityPub → Fediverso)
            │          ├→ Push Notifications (web push + Telegram)
            │          └→ Typesense Sync (busca semântica)
            └→ Bronze Ingestion (GCS Parquet → BigQuery)

Portal v1.0.0 (Next.js)
├── Busca semântica (Typesense)
├── Google OAuth (NextAuth.js)
├── Push Notifications (VAPID + Service Worker)
├── Bot Telegram (@destaquesgovbr_bot)
├── Umami Analytics (IAP-protected)
├── GrowthBook Feature Flags
└── Feeds RSS/Atom/JSON
```

De monolito batch a pipeline event-driven com 8+ serviços — em 7 dias, ~75 PRs, 11 repos.
