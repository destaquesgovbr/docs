# Data Platform

Repositório centralizado para toda a infraestrutura de dados do DestaquesGovBr.

!!! info "Repositório"
    **GitHub**: [destaquesgovbr/data-platform](https://github.com/destaquesgovbr/data-platform)

!!! note "Arquitetura Atualizada (27/02/2026)"
    Pipeline migrado para **event-driven** com AWS Bedrock. Cogfy descontinuado.

## Visão Geral

O **data-platform** é responsável por armazenamento, workers de processamento event-driven e sincronização de dados do DestaquesGovBr. A coleta (scraping) é feita pelo repo standalone [scraper](https://github.com/destaquesgovbr/scraper).

- **Armazenamento**: Gerenciamento do PostgreSQL (fonte de verdade) e HuggingFace (distribuição)
- **Workers Event-Driven**: Enrichment (AWS Bedrock), Embeddings e Typesense Sync via Pub/Sub
- **Batch Jobs**: Sincronização HuggingFace e exports via DAGs Airflow

## Arquitetura

```mermaid
graph TB
    subgraph "Coleta (repo scraper)"
        S[Scraper API<br/>Cloud Run]
        DAG_S[DAGs Airflow<br/>~158 agências + EBC]
    end

    subgraph "Event Mesh (Pub/Sub)"
        PS1{{dgb.news.scraped}}
        PS2{{dgb.news.enriched}}
        PS3{{dgb.news.embedded}}
    end

    subgraph "Armazenamento"
        PG[(PostgreSQL<br/>Fonte de Verdade)]
        HF[(HuggingFace<br/>Dados Abertos)]
    end

    subgraph "Workers Event-Driven (data-science + embeddings repos)"
        EW[Enrichment Worker<br/>Cloud Run]
        BEDROCK[AWS Bedrock<br/>Claude 3 Haiku]
        EAPI[Embeddings Worker<br/>Cloud Run]
        TSW[Typesense Sync<br/>Worker Cloud Run]
    end

    subgraph "Indexação"
        TS[Typesense<br/>Busca]
    end

    DAG_S -->|HTTP POST| S
    S -->|INSERT + publish| PG
    S -->|publish| PS1
    PS1 -->|push| EW
    EW -->|LLM| BEDROCK
    EW -->|UPDATE + publish| PG
    EW -->|publish| PS2
    PS2 -->|push| EAPI
    EAPI -->|UPDATE + publish| PG
    EAPI -->|publish| PS3
    PS2 -->|push| TSW
    PS3 -->|push| TSW
    TSW -->|fetch + upsert| TS
    TSW <-->|read| PG
    PG -->|DAG Airflow| HF
```

## Estrutura do Repositório

```
data-platform/
├── src/data_platform/
│   ├── managers/               # Gerenciadores de storage
│   │   ├── postgres_manager.py # Acesso ao PostgreSQL
│   │   ├── dataset_manager.py  # Acesso ao HuggingFace
│   │   └── storage_adapter.py
│   ├── cogfy/                  # Integração Cogfy
│   │   ├── cogfy_manager.py
│   │   ├── upload_manager.py
│   │   └── enrichment_manager.py
│   ├── typesense/              # Módulo Typesense
│   │   ├── client.py
│   │   ├── collection.py
│   │   └── indexer.py
│   ├── jobs/                   # Jobs de processamento
│   │   ├── enrichment/
│   │   ├── embeddings/
│   │   ├── typesense/sync_job.py
│   │   └── hf_sync/
│   ├── models/                 # Modelos Pydantic
│   │   └── news.py
│   ├── dags/                   # DAGs Airflow
│   │   └── sync_postgres_to_huggingface.py
│   └── cli.py                  # Interface de linha de comando
├── tests/
├── scripts/
└── pyproject.toml
```

## CLI - Comandos Disponíveis

!!! warning "Comandos Descontinuados"
    Comandos `upload-cogfy` e `enrich` foram removidos após migração para AWS Bedrock (27/02/2026). Processamento agora é event-driven via workers.

### Reprocessamento Manual

```bash
# Reprocessar artigos sem enriquecimento
# (republicar eventos no Pub/Sub via gcloud CLI)
gcloud pubsub topics publish dgb.news.scraped \
  --message='{"unique_id":"abc123"}' \
  --attribute=agency_key=educacao

# Reprocessar embeddings
# (republicar eventos no Pub/Sub)
gcloud pubsub topics publish dgb.news.enriched \
  --message='{"unique_id":"abc123"}'
```

### Typesense

```bash
# Listar collections
data-platform typesense-list

# Deletar collection
data-platform typesense-delete --confirm

# Full reload (via script interno do Typesense Sync Worker)
# Não mais via CLI do data-platform
```

### HuggingFace

```bash
# Sincronizar PostgreSQL → HuggingFace
# (rodado via DAG Airflow, não CLI)
data-platform sync-hf --start-date 2025-01-01
```

## PostgresManager

Gerenciador de acesso ao PostgreSQL com connection pooling e cache.

### Características

- **Connection Pooling**: Min 1, Max 10 conexões
- **Cache em Memória**: Agências e temas carregados na inicialização
- **Batch Operations**: Inserts otimizados com `execute_values()`
- **Conflict Handling**: Suporte a `ON CONFLICT DO UPDATE`

### Exemplo de Uso

```python
from data_platform.managers.postgres_manager import PostgresManager

pm = PostgresManager()
pm.load_cache()  # Carrega agências/temas em memória

# Inserir notícias
news_list = [NewsInsert(...), ...]
inserted = pm.insert(news_list, allow_update=True)

# Buscar notícias
news = pm.get(
    filters={"agency_key": "mec"},
    limit=100,
    order_by="published_at DESC"
)

pm.close_all()
```

## Variáveis de Ambiente

```bash
# PostgreSQL
DATABASE_URL=postgresql://user:pass@host:5432/govbrnews

# HuggingFace
HF_TOKEN=hf_xxx
HF_REPO_ID=destaquesgovbr/govbrnews

# Typesense
TYPESENSE_HOST=34.39.186.38
TYPESENSE_PORT=8108
TYPESENSE_API_KEY=xxx

# AWS Bedrock (Enrichment Worker - repo data-science)
AWS_ACCESS_KEY_ID=xxx
AWS_SECRET_ACCESS_KEY=xxx
AWS_REGION=us-east-1
BEDROCK_MODEL_ID=anthropic.claude-3-haiku-20240307-v1:0

# Pub/Sub (Workers)
GCP_PROJECT_ID=destaquesgovbr
PUBSUB_TOPIC_SCRAPED=dgb.news.scraped
PUBSUB_TOPIC_ENRICHED=dgb.news.enriched
PUBSUB_TOPIC_EMBEDDED=dgb.news.embedded
```

## Workflows GitHub Actions

!!! note "Workflows Atualizados (27/02/2026)"
    Workflow `main-workflow.yaml` descontinuado. Processamento agora é event-driven via Cloud Run workers.

| Workflow | Trigger | Descrição | Status |
|----------|---------|-----------|--------|
| `main-workflow.yaml` | ~~Diário (4AM UTC)~~ | ~~Pipeline de enrichment~~ | Descontinuado |
| `composer-deploy-dags.yaml` | Push | Deploy de DAGs no Airflow | Ativo |
| `workers-deploy.yaml` | Push | Deploy de workers Cloud Run | Ativo |

## Instalação e Desenvolvimento

```bash
# Clonar
git clone https://github.com/destaquesgovbr/data-platform.git
cd data-platform

# Instalar com Poetry
poetry install

# Rodar testes
poetry run pytest

# Rodar linters
poetry run black src/ tests/
poetry run ruff check src/ tests/
poetry run mypy src/
```

## Documentação Adicional

O repositório possui documentação interna em `docs/`:

- `docs/architecture/overview.md` - Arquitetura do sistema
- `docs/database/schema.md` - Schema PostgreSQL
- `docs/typesense/` - Documentação do Typesense
- `docs/development/setup.md` - Setup de desenvolvimento

## Recursos Externos

- **HuggingFace Dataset**: [nitaibezerra/govbrnews](https://huggingface.co/datasets/nitaibezerra/govbrnews)
- **Portal**: [destaques.gov.br](https://destaques.gov.br)
