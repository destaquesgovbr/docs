# Airflow DAGs (Cloud Composer)

O projeto utiliza **Cloud Composer 3** (Apache Airflow gerenciado) para orquestração de pipelines de dados: scraping de notícias (repo `scraper`), sincronização entre PostgreSQL e HuggingFace (repo `data-platform`), e reconciliação de eventos (repo `data-science`).

!!! info "Cloud Composer"
    **Ambiente**: `destaquesgovbr-composer`
    **Região**: `us-central1`
    **Versão**: Composer 3 / Airflow 3.x

## Arquitetura

```mermaid
graph TB
    subgraph "Cloud Composer"
        SCHED[Scheduler]
        WORKER[Workers<br/>1-3 instâncias]
        UI[Web UI]
        TRIGGER[Triggerer]
    end

    subgraph "DAGs (data-platform)"
        DAG1[sync_postgres_to_huggingface]
        DAG2[test_postgres_connection]
    end

    subgraph "DAGs (data-science)"
        DAG5[reconciliation_dlq]
        DAG6[replay_bronze_events]
    end

    subgraph "DAGs (scraper)"
        DAG3[~158x scrape_agency]
        DAG4[scrape_ebc]
    end

    subgraph "Recursos GCP"
        PG[(PostgreSQL<br/>Cloud SQL)]
        SM[Secret Manager]
        GCS[GCS Bucket<br/>DAGs]
        BRONZE[(GCS Bronze<br/>Parquet)]
        PUBSUB[Pub/Sub Topics]
    end

    subgraph "Externos"
        HF[(HuggingFace)]
    end

    GCS --> SCHED
    SCHED --> WORKER
    WORKER --> DAG1
    WORKER --> DAG2
    WORKER --> DAG3
    WORKER --> DAG4
    WORKER --> DAG5
    WORKER --> DAG6
    DAG1 --> PG
    DAG1 --> HF
    DAG3 -->|HTTP POST| CR[Cloud Run<br/>Scraper API]
    DAG4 -->|HTTP POST| CR
    DAG5 -->|Pub/Sub Pull| PUBSUB
    DAG5 -->|Republish| PUBSUB
    DAG6 -->|BigQuery Query| BRONZE
    DAG6 -->|Republish| PUBSUB
    CR --> PG
    SM --> WORKER
```

## Organização de DAGs no Bucket

O Composer armazena DAGs de múltiplos repos em subdiretórios do mesmo bucket:

```
gs://{COMPOSER_BUCKET}/dags/
├── data-platform/                    # DAGs do repo data-platform
│   ├── sync_postgres_to_huggingface.py
│   └── test_postgres_connection.py
├── data-science/                     # DAGs do repo data-science
│   ├── reconciliation_dlq.py
│   └── replay_bronze_events.py
└── scraper/                          # DAGs do repo scraper
    ├── scrape_agencies.py            # ~158 DAGs dinâmicas
    ├── scrape_ebc.py
    └── config/
        └── site_urls.yaml
```

Cada repo tem seu próprio workflow `composer-deploy-dags.yaml` que faz `gsutil rsync` para seu subdiretório.

## DAGs Disponíveis

### DAGs do Scraper (repo `scraper`)

#### `scrape_{agency_key}` (~158 DAGs dinâmicas)

Cada agência gov.br gera uma DAG de scraping independente.

| Configuração | Valor |
|--------------|-------|
| **Schedule** | `*/15 * * * *` (a cada 15 min) |
| **Catchup** | Desabilitado |
| **Retries** | 2 (com backoff de 5 min) |
| **Timeout** | 15 min |

Cada DAG faz HTTP POST para a Scraper API no Cloud Run (`POST /scrape/agencies` com a agência específica).

#### `scrape_ebc`

DAG para scraping dos sites EBC (Agência Brasil, TV Brasil).

| Configuração | Valor |
|--------------|-------|
| **Schedule** | `*/15 * * * *` (a cada 15 min) |
| **Retries** | 2 (com backoff de 5 min) |

Faz HTTP POST para `POST /scrape/ebc` no Cloud Run.

→ Veja [Módulo Scraper](../modulos/scraper.md) para detalhes da API e do repo.

### DAGs do Data Science (repo `data-science`)

#### `reconciliation_dlq`

Reconcilia mensagens na Dead-Letter Queue após correção de bugs.

| Configuração | Valor |
|--------------|-------|
| **Schedule** | Manual (`None`) |
| **Catchup** | Desabilitado |
| **Retries** | 1 (com backoff de 5 min) |
| **Tags** | `reconciliation`, `pubsub`, `dlq` |

#### Fluxo de Execução

```mermaid
sequenceDiagram
    participant A as Airflow
    participant DLQ as DLQ Subscription
    participant TOPIC as Main Topic
    participant WORKER as Enrichment Worker

    A->>DLQ: Pull messages (limit=1000)
    DLQ-->>A: Messages batch
    
    loop For each message
        A->>A: Decode base64 payload
        A->>TOPIC: Republish to main topic
    end
    
    TOPIC->>WORKER: Process (retry with fix)
    WORKER-->>TOPIC: Success (200)
```

**Uso**: Trigger manual após correção de bugs no worker para reprocessar mensagens falhadas.

→ Veja [Dead-Letter Queue Guide](./pub-sub-deadletter.md) para detalhes de DLQ management.

#### `replay_bronze_events`

Reprocessa eventos da Bronze Layer (GCS Parquet) para Silver Layer (PostgreSQL).

| Configuração | Valor |
|--------------|-------|
| **Schedule** | Manual (`None`) |
| **Catchup** | Desabilitado |
| **Retries** | 2 (com backoff exponencial) |
| **Tags** | `replay`, `bronze`, `recovery` |
| **Parameters** | `start_date`, `end_date`, `topic` |

#### Fluxo de Execução

```mermaid
sequenceDiagram
    participant A as Airflow
    participant BQ as BigQuery
    participant BRONZE as GCS Bronze Layer
    participant TOPIC as Pub/Sub Topic
    participant WORKER as Worker

    A->>BQ: Query external table<br/>(date range filter)
    BQ->>BRONZE: Read Parquet files
    BRONZE-->>BQ: Events batch
    BQ-->>A: Rows (e.g., 5000)
    
    loop Batch of 100 events
        A->>TOPIC: Publish events
    end
    
    TOPIC->>WORKER: Process batch
    WORKER-->>TOPIC: Success
```

**Cenários de Uso**:

1. **Perda de dados na Silver Layer**: Reprocessar eventos de um período específico
2. **Correção de lógica de enriquecimento**: Reprocessar com nova versão do worker
3. **Backfill**: Processar dados históricos com novos workers

**Exemplo de Trigger**:

```python
# Via Airflow CLI
airflow dags trigger replay_bronze_events \
  --conf '{"start_date": "2026-05-01", "end_date": "2026-05-05", "topic": "dgb.news.scraped"}'
```

→ Veja [Bronze Layer GCS](../modulos/bronze-layer-gcs.md) para detalhes da arquitetura Bronze.

---

### DAGs do Data Platform (repo `data-platform`)

#### `sync_postgres_to_huggingface`

Sincroniza notícias do PostgreSQL para o HuggingFace diariamente.

| Configuração | Valor |
|--------------|-------|
| **Schedule** | `0 6 * * *` (6 AM UTC) |
| **Catchup** | Desabilitado |
| **Retries** | 3 (com backoff exponencial) |
| **Tags** | `sync`, `huggingface`, `postgres`, `daily` |

#### Fluxo de Execução

```mermaid
sequenceDiagram
    participant A as Airflow
    participant PG as PostgreSQL
    participant API as HuggingFace API
    participant HF as HuggingFace Dataset

    A->>PG: Query notícias do dia anterior
    PG-->>A: Registros (ex: 500)

    A->>API: Consulta IDs existentes via Dataset Viewer
    API-->>A: IDs já sincronizados (ex: 480)

    Note over A: Filtra apenas novos (ex: 20)

    A->>A: Cria parquet shard
    A->>HF: Upload do shard
    HF-->>A: Commit confirmado

    A->>HF: Upload para dataset reduzido
```

#### Abordagem Incremental

A DAG utiliza uma abordagem de **append incremental via parquet shards** para evitar problemas de memória:

1. **Consulta IDs existentes** via Dataset Viewer API (sem baixar o dataset completo)
2. **Cria parquet shard** apenas com novos registros
3. **Upload direto** via `huggingface_hub`

**Vantagens**:
- Memória: ~10MB (apenas novos registros) vs ~1-2GB (dataset completo)
- Deduplicação automática
- Commits atômicos por dia

#### Estrutura do Shard

```
data/train-{YYYY-MM-DD}-{HHMMSS}.parquet
```

Exemplo: `data/train-2025-01-10-060532.parquet`

#### Colunas Sincronizadas

```python
HF_COLUMNS = [
    "unique_id", "agency", "published_at", "updated_datetime", "extracted_at",
    "title", "subtitle", "editorial_lead", "url", "content",
    "image", "video_url", "category", "tags",
    "theme_1_level_1", "theme_1_level_1_code", "theme_1_level_1_label",
    "theme_1_level_2_code", "theme_1_level_2_label",
    "theme_1_level_3_code", "theme_1_level_3_label",
    "most_specific_theme_code", "most_specific_theme_label",
    "summary"
]
```

#### Datasets Atualizados

| Dataset | Colunas | Uso |
|---------|---------|-----|
| `nitaibezerra/govbrnews` | Todas (24) | Análise completa |
| `nitaibezerra/govbrnews-reduced` | 4 (published_at, agency, title, url) | Listagens rápidas |

#### `test_postgres_connection`

DAG de teste para verificar conectividade com o PostgreSQL.

| Configuração | Valor |
|--------------|-------|
| **Schedule** | Manual (`None`) |
| **Uso** | Validação pós-deploy |

## Configuração do Composer

### Workloads

| Componente | CPU | Memória | Storage | Instâncias |
|------------|-----|---------|---------|------------|
| Scheduler | 0.5 | 2GB | 2GB | 1 |
| Web Server | 1 | 2GB | 2GB | 1 |
| Worker | 1 | 2GB | 2GB | 1-3 (auto) |
| Triggerer | 0.5 | 2GB | - | 1 |
| DAG Processor | 0.5 | 2GB | 1GB | 1 |

### Airflow Config Overrides

```python
{
    # Secret Manager Backend
    "secrets-backend": "airflow.providers.google.cloud.secrets.secret_manager.CloudSecretManagerBackend",
    "secrets-backend_kwargs": {
        "connections_prefix": "airflow-connections",
        "variables_prefix": "airflow-variables",
        "project_id": "inspire-7-finep"
    },

    # Timezone
    "core-default_timezone": "America/Sao_Paulo",

    # Web UI
    "webserver-rbac": "True",
    "webserver-authenticate": "True",
}
```

### PyPI Packages

```
psycopg2-binary>=2.9.9
apache-airflow-providers-postgres>=5.10.2
apache-airflow-providers-google>=10.14.0
google-cloud-pubsub>=2.18.0
google-cloud-bigquery>=3.11.0
sqlalchemy>=1.4.52
requests>=2.31.0
pyyaml>=6.0
```

### Environment Variables

```bash
# PostgreSQL
POSTGRES_HOST=10.x.x.x  # IP privado Cloud SQL
POSTGRES_PORT=5432
POSTGRES_DB=govbrnews

# GCP
GCP_PROJECT_ID=destaques-govbr
GCP_REGION=southamerica-east1

# Pub/Sub Topics (Event-Driven)
PUBSUB_TOPIC_SCRAPED=dgb.news.scraped
PUBSUB_TOPIC_ENRICHED=dgb.news.enriched
PUBSUB_TOPIC_EMBEDDED=dgb.news.embedded

# Bronze Layer (Medallion)
GCS_BRONZE_BUCKET=destaques-govbr-bronze
BIGQUERY_BRONZE_DATASET=bronze

# External
TYPESENSE_HOST=34.39.186.38
```

## Connections

As connections são gerenciadas via **Secret Manager**:

| Connection ID | Tipo | Secret |
|--------------|------|--------|
| `postgres_default` | Postgres | `airflow-connections-postgres_default` |
| `huggingface_default` | Generic | `airflow-connections-huggingface_default` |
| `gcp_pubsub_default` | Google Cloud | `airflow-connections-gcp_pubsub_default` |
| `bigquery_default` | Google BigQuery | `airflow-connections-bigquery_default` |

### Formato das Connections

```json
// postgres_default
{
    "conn_type": "postgres",
    "host": "10.x.x.x",
    "port": 5432,
    "schema": "govbrnews",
    "login": "govbrnews_app",
    "password": "xxx"
}

// huggingface_default
{
    "conn_type": "generic",
    "password": "hf_xxx"  // Token HuggingFace
}

// gcp_pubsub_default (usa Application Default Credentials)
{
    "conn_type": "google_cloud_platform",
    "project_id": "destaques-govbr"
}

// bigquery_default (usa Application Default Credentials)
{
    "conn_type": "google_cloud_platform",
    "project_id": "destaques-govbr",
    "dataset": "bronze"
}
```

## Deploy de DAGs

### Via GitHub Actions

Cada repo tem seu próprio workflow `composer-deploy-dags.yaml` que sincroniza para o subdiretório correspondente:

**Repo `data-platform`**:
```bash
gsutil -m rsync -r -d src/data_platform/dags/ gs://{BUCKET}/dags/data-platform/
```

**Repo `data-science`**:
```bash
gsutil -m rsync -r -d dags/ gs://{BUCKET}/dags/data-science/
```

**Repo `scraper`**:
```bash
gsutil -m rsync -r -d dags/ gs://{BUCKET}/dags/scraper/
```

### Manual via gcloud

```bash
# Descobrir bucket do Composer
BUCKET=$(gcloud composer environments describe destaquesgovbr-composer \
    --location us-central1 \
    --format="value(config.dagGcsPrefix)")

# Upload das DAGs do data-platform
gsutil -m rsync -r -d src/data_platform/dags/ $BUCKET/data-platform/

# Upload das DAGs do data-science
gsutil -m rsync -r -d dags/ $BUCKET/data-science/

# Upload das DAGs do scraper
gsutil -m rsync -r -d dags/ $BUCKET/scraper/
```

## Monitoramento

### Acessar Web UI

```bash
# Obter URL do Airflow
gcloud composer environments describe destaquesgovbr-composer \
    --location us-central1 \
    --format="value(config.airflowUri)"
```

### Logs

```bash
# Ver logs de uma DAG run
gcloud composer environments run destaquesgovbr-composer \
    --location us-central1 \
    dags list-runs -- -d sync_postgres_to_huggingface
```

### Métricas

O Composer exporta métricas para Cloud Monitoring:

- `composer.googleapis.com/environment/dag_processing/total_parse_time`
- `composer.googleapis.com/environment/worker/task_success_count`
- `composer.googleapis.com/environment/worker/task_failed_count`

## Troubleshooting

### DAG não aparece na UI

1. Verificar se o arquivo foi copiado para o bucket:
   ```bash
   gsutil ls $BUCKET/dags/
   ```

2. Verificar logs do DAG Processor:
   ```bash
   gcloud composer environments run destaquesgovbr-composer \
       --location us-central1 \
       tasks log-read -- -d sync_postgres_to_huggingface -t sync_news_to_huggingface
   ```

### Erro de conexão com PostgreSQL

1. Verificar se a connection existe no Secret Manager
2. Verificar se o Composer tem acesso ao Cloud SQL via VPC

### Erro de memória (OOM)

- A abordagem incremental resolve isso
- Se persistir, aumentar `memory_gb` dos workers no Terraform

## Custos Estimados

| Componente | Custo/mês |
|------------|-----------|
| Cloud Composer (SMALL) | ~$100-150 |
| GCS (DAGs bucket) | ~$1 |
| **Total** | **~$100-150** |

!!! tip "Otimização de Custos"
    O Composer está em `us-central1` (não `southamerica-east1`) para reduzir custos. A latência adicional é aceitável para jobs batch.
