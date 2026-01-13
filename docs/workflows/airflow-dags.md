# Airflow DAGs (Cloud Composer)

O projeto utiliza **Cloud Composer 3** (Apache Airflow gerenciado) para orquestração de pipelines de dados, especialmente a sincronização entre PostgreSQL e HuggingFace.

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

    subgraph "DAGs"
        DAG1[sync_postgres_to_huggingface]
        DAG2[test_postgres_connection]
    end

    subgraph "Recursos GCP"
        PG[(PostgreSQL<br/>Cloud SQL)]
        SM[Secret Manager]
        GCS[GCS Bucket<br/>DAGs]
    end

    subgraph "Externos"
        HF[(HuggingFace)]
    end

    GCS --> SCHED
    SCHED --> WORKER
    WORKER --> DAG1
    WORKER --> DAG2
    DAG1 --> PG
    DAG1 --> HF
    SM --> WORKER
```

## DAGs Disponíveis

### `sync_postgres_to_huggingface`

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

### `test_postgres_connection`

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
sqlalchemy>=1.4.52
requests>=2.31.0
pandas>=2.0.0
```

### Environment Variables

```bash
POSTGRES_HOST=10.x.x.x  # IP privado Cloud SQL
POSTGRES_PORT=5432
POSTGRES_DB=govbrnews
GCP_PROJECT_ID=inspire-7-finep
GCP_REGION=southamerica-east1
TYPESENSE_HOST=34.39.186.38
```

## Connections

As connections são gerenciadas via **Secret Manager**:

| Connection ID | Tipo | Secret |
|--------------|------|--------|
| `postgres_default` | Postgres | `airflow-connections-postgres_default` |
| `huggingface_default` | Generic | `airflow-connections-huggingface_default` |

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
```

## Deploy de DAGs

### Via GitHub Actions

O workflow `composer-deploy-dags.yaml` faz deploy automático em push:

```yaml
# .github/workflows/composer-deploy-dags.yaml
on:
  push:
    paths:
      - 'src/data_platform/dags/**'

jobs:
  deploy:
    steps:
      - name: Upload DAGs to GCS
        run: |
          gsutil -m cp -r src/data_platform/dags/* \
            gs://${{ env.COMPOSER_BUCKET }}/dags/
```

### Manual via gcloud

```bash
# Descobrir bucket do Composer
BUCKET=$(gcloud composer environments describe destaquesgovbr-composer \
    --location us-central1 \
    --format="value(config.dagGcsPrefix)")

# Upload das DAGs
gsutil -m cp -r src/data_platform/dags/* $BUCKET/
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
