# Fluxo de Dados

## Pipeline Diário

O pipeline de dados é executado diariamente às **4AM UTC** (1AM Brasília) via GitHub Actions.

### Diagrama de Sequência Completo

```mermaid
sequenceDiagram
    participant GH as GitHub Actions
    participant SC as Scraper Container
    participant GOV as Sites gov.br
    participant EBC as Sites EBC
    participant PG as PostgreSQL
    participant CF as Cogfy API
    participant EMB as Embeddings API
    participant TS as Typesense
    participant AF as Airflow (6AM UTC)
    participant HF as HuggingFace

    rect rgb(227, 242, 253)
        Note over GH,SC: ETAPA 1: Scraping gov.br
        GH->>SC: Trigger main-workflow (4AM UTC)
        SC->>GOV: Requisições HTTP (160+ sites)
        GOV-->>SC: HTML das páginas
        SC->>SC: Parse HTML → Markdown
        SC->>SC: Gera unique_id (MD5)
        SC->>PG: postgres.insert(new_articles)
    end

    rect rgb(255, 243, 224)
        Note over SC,EBC: ETAPA 2: Scraping EBC
        SC->>EBC: Requisições HTTP (sites EBC)
        EBC-->>SC: HTML das páginas
        SC->>SC: Parse especializado EBC
        SC->>PG: postgres.insert(ebc_articles, allow_update=True)
    end

    rect rgb(255, 253, 231)
        Note over SC,CF: ETAPA 3: Upload para Cogfy
        SC->>PG: get_news(date_range)
        PG-->>SC: Registros
        SC->>CF: POST /records (batch 1000)
        CF-->>SC: IDs dos registros
    end

    rect rgb(232, 245, 233)
        Note over CF: ETAPA 4: Aguarda Processamento
        Note over CF: Cogfy processa via LLM (20 min)
        CF->>CF: Classificação temática
        CF->>CF: Geração de resumo
    end

    rect rgb(252, 228, 236)
        Note over SC,PG: ETAPA 5: Enriquecimento
        SC->>CF: GET /records (busca por unique_id)
        CF-->>SC: themes + summary
        SC->>SC: Mapeia códigos → labels
        SC->>SC: Calcula most_specific_theme
        SC->>PG: postgres.update(enriched_data)
    end

    rect rgb(255, 248, 225)
        Note over SC,EMB: ETAPA 6: Embeddings
        SC->>PG: get_news_without_embeddings()
        PG-->>SC: Notícias sem vetores
        SC->>EMB: POST /embed (batch 100)
        EMB-->>SC: Vetores 768-dim
        SC->>PG: postgres.update(embeddings)
    end

    rect rgb(243, 229, 245)
        Note over TS,PG: ETAPA 7: Indexação Typesense
        GH->>TS: Trigger typesense-sync
        TS->>PG: iter_news_for_typesense()
        PG-->>TS: Batches de 5000
        TS->>TS: Upsert documentos
    end

    rect rgb(225, 245, 254)
        Note over AF,HF: ETAPA 8: Sync HuggingFace
        AF->>PG: Query novos registros
        PG-->>AF: Registros do dia anterior
        AF->>AF: Cria parquet shard
        AF->>HF: Upload shard
    end
```

## Etapas Detalhadas

### Etapa 1: Scraping gov.br

**Workflow**: `main-workflow.yaml` → job `scraper`

```bash
data-platform scrape --start-date YYYY-MM-DD --end-date YYYY-MM-DD
```

**Processo**:

1. Carrega URLs de `src/data_platform/scrapers/site_urls.yaml` (~160+ URLs)
2. Para cada URL, instancia `WebScraper`
3. Navega por páginas com paginação (`?b_start:int=N`)
4. Extrai campos: title, date, url, image, category, tags
5. Faz fetch do conteúdo completo de cada notícia
6. Converte HTML → Markdown com `markdownify`
7. Gera `unique_id = MD5(agency + published_at + title)`
8. Insere no PostgreSQL via `PostgresManager.insert()`

**Retry Logic**:
```python
@retry(tries=5, delay=2, backoff=3, jitter=(1,3))
def fetch_page(url): ...
```

### Etapa 2: Scraping EBC

**Workflow**: `main-workflow.yaml` → job `ebc-scraper`

```bash
data-platform scrape-ebc --start-date YYYY-MM-DD --end-date YYYY-MM-DD --allow-update
```

**Diferenças**:

- Scraper especializado (`EBCWebScraper`)
- Estrutura HTML diferente dos sites gov.br
- `allow_update=True` permite sobrescrever registros existentes

### Etapa 3: Upload para Cogfy

**Workflow**: `main-workflow.yaml` → job `upload-to-cogfy`

```bash
data-platform upload-cogfy --start-date YYYY-MM-DD --end-date YYYY-MM-DD
```

**Processo**:

1. Carrega artigos do PostgreSQL por intervalo de datas
2. Converte campos para formato Cogfy:

   - `published_at` → datetime UTC
   - `tags` → string JSON
3. Envia em batches de 1000 registros
4. Salva mapeamento `unique_id` ↔ `cogfy_record_id`

### Etapa 4: Processamento Cogfy

**Tempo**: ~20 minutos de delay configurado no workflow

O Cogfy executa:

- **Classificação temática** em 3 níveis usando a árvore de temas
- **Geração de resumo** via LLM

> **Nota**: A configuração do Cogfy não está em código. Screenshots serão adicionados futuramente.

### Etapa 5: Enriquecimento

**Workflow**: `main-workflow.yaml` → job `enrich-themes`

```bash
data-platform enrich --start-date YYYY-MM-DD --end-date YYYY-MM-DD
```

**Processo**:

1. Aguarda delay de 20 minutos (1200 segundos)
2. Busca registros processados no Cogfy por `unique_id`
3. Extrai campos enriquecidos:

   - `theme_1_level_1` (select) → código e label
   - `theme_1_level_2` (text) → código e label
   - `theme_1_level_3` (text) → código e label
   - `summary` (text)
4. Calcula `most_specific_theme` (prioridade: L3 > L2 > L1)
5. Atualiza PostgreSQL

### Etapa 6: Embeddings

**Workflow**: `main-workflow.yaml` → job `generate-embeddings`

```bash
data-platform generate-embeddings --start-date YYYY-MM-DD
```

**Processo**:

1. Busca notícias sem embeddings no PostgreSQL
2. Prepara texto: `title + summary` (fallback para `content`)
3. Envia para Embeddings API em batches de 100
4. Recebe vetores 768-dim do modelo `paraphrase-multilingual-mpnet-base-v2`
5. Atualiza `content_embedding` no PostgreSQL

### Etapa 7: Indexação Typesense

**Workflow**: `typesense-maintenance-sync.yaml` (10AM UTC)

```bash
data-platform sync-typesense --start-date YYYY-MM-DD
```

**Processo**:

1. Conecta ao Typesense em produção
2. Lê dados do PostgreSQL em batches de 5000
3. Faz upsert dos documentos na collection `news` (incluindo embeddings)

### Etapa 8: Sync HuggingFace

**DAG Airflow**: `sync_postgres_to_huggingface` (6AM UTC)

**Processo**:

1. Query notícias do dia anterior no PostgreSQL
2. Consulta IDs existentes no HuggingFace via Dataset Viewer API
3. Filtra apenas novos registros
4. Cria parquet shard com novos dados
5. Upload do shard para HuggingFace

→ Veja detalhes em [workflows/airflow-dags.md](../workflows/airflow-dags.md)

## Dados de Entrada e Saída

### Entrada (Sites gov.br)

```html
<!-- Estrutura típica de item de notícia -->
<article class="tileItem">
  <a href="/orgao/noticia/titulo-da-noticia">
    <h2>Título da Notícia</h2>
  </a>
  <span class="summary">Resumo...</span>
  <span class="documentPublished">01/12/2025</span>
  <img src="imagem.jpg" />
</article>
```

### Saída (PostgreSQL / News)

```json
{
  "id": 123456,
  "unique_id": "abc123def456",
  "agency_id": 45,
  "agency_key": "gestao",
  "agency_name": "Ministério da Gestão",
  "published_at": "2024-12-02T10:00:00Z",
  "updated_datetime": "2024-12-02T14:30:00Z",
  "extracted_at": "2024-12-02T07:00:00Z",
  "title": "Título da Notícia",
  "subtitle": "Subtítulo explicativo",
  "editorial_lead": "Linha fina com contexto",
  "url": "https://www.gov.br/gestao/...",
  "content": "# Título\n\nConteúdo em Markdown...",
  "image_url": "https://www.gov.br/.../imagem.jpg",
  "video_url": null,
  "category": "Notícias",
  "tags": ["tag1", "tag2"],
  "theme_l1_id": 1,
  "theme_l2_id": 5,
  "theme_l3_id": 15,
  "most_specific_theme_id": 15,
  "summary": "Resumo gerado por AI...",
  "content_embedding": [0.123, -0.456, ...],  // 768 dimensões
  "embedding_generated_at": "2024-12-02T08:00:00Z"
}
```

## Tratamento de Erros

### Scraping
- Retry com backoff exponencial (5 tentativas)
- Skip de artigos com erro (não bloqueia pipeline)
- Logs detalhados de falhas

### Cogfy
- Verificação de status antes de buscar resultados
- Fallback para valores vazios se inferência falhar

### PostgreSQL
- Connection pooling com retry
- Deduplicação por `unique_id` (ON CONFLICT)
- Transações para operações batch

### HuggingFace (Sync)
- Incremental via parquet shards
- Deduplicação via Dataset Viewer API

## Monitoramento

### GitHub Actions
- Status de cada job visível na interface
- Logs completos por etapa
- Notificações de falha

### Métricas
- Quantidade de artigos raspados por execução
- Taxa de sucesso de enriquecimento
- Tempo total de pipeline

## Execução Manual

### Scraping de período específico
```bash
# Via CLI
data-platform scrape --start-date 2024-01-01 --end-date 2024-01-31

# Via GitHub Actions
gh workflow run main-workflow.yaml \
  -f start-date=2024-01-01 \
  -f end-date=2024-01-31
```

### Enriquecimento manual
```bash
data-platform enrich --start-date 2024-01-01 --force
```

### Geração de embeddings
```bash
data-platform generate-embeddings --start-date 2024-01-01
```

### Sync Typesense
```bash
# Incremental
data-platform sync-typesense --start-date 2024-01-01

# Full reload
data-platform sync-typesense --full-sync
```

### Reload completo do Typesense (via GitHub Actions)
```bash
gh workflow run typesense-full-reload.yaml \
  -f confirm=DELETE
```

> **CUIDADO**: O full reload é destrutivo - deleta todos os dados antes de recarregar!
