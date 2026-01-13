# Data Platform

Repositório centralizado para toda a infraestrutura de dados do DestaquesGovBr.

!!! info "Repositório"
    **GitHub**: [destaquesgovbr/data-platform](https://github.com/destaquesgovbr/data-platform)

## Visão Geral

O **data-platform** unifica toda a lógica de dados que anteriormente estava distribuída em múltiplos repositórios (`scraper`, `typesense`). Ele é responsável por:

- **Coleta**: Scrapers para gov.br e EBC
- **Armazenamento**: Gerenciamento do PostgreSQL (fonte de verdade) e HuggingFace (distribuição)
- **Enriquecimento**: Integração com Cogfy para classificação temática e sumários
- **Embeddings**: Geração de vetores para busca semântica
- **Indexação**: Sincronização com Typesense

## Arquitetura

```mermaid
graph TB
    subgraph "Coleta"
        S1[Scraper Gov.br]
        S2[Scraper EBC]
    end

    subgraph "Armazenamento"
        PG[(PostgreSQL<br/>Fonte de Verdade)]
        HF[(HuggingFace<br/>Dados Abertos)]
    end

    subgraph "Processamento"
        COG[Cogfy<br/>Enriquecimento]
        EMB[Embeddings API<br/>Vetores 768-dim]
    end

    subgraph "Indexação"
        TS[Typesense<br/>Busca]
    end

    S1 --> PG
    S2 --> PG
    PG --> COG
    COG --> PG
    PG --> EMB
    EMB --> PG
    PG --> TS
    PG -->|DAG Airflow| HF
```

## Estrutura do Repositório

```
data-platform/
├── src/data_platform/
│   ├── managers/               # Gerenciadores de storage
│   │   ├── postgres_manager.py # Acesso ao PostgreSQL
│   │   ├── dataset_manager.py  # Acesso ao HuggingFace
│   │   └── storage_adapter.py  # Abstração dual-write
│   ├── scrapers/               # Scrapers de notícias
│   │   ├── scrape_manager.py   # Gov.br
│   │   └── ebc_scrape_manager.py
│   ├── cogfy/                  # Integração Cogfy
│   │   ├── cogfy_manager.py
│   │   ├── upload_manager.py
│   │   └── enrichment_manager.py
│   ├── typesense/              # Módulo Typesense
│   │   ├── client.py
│   │   ├── collection.py
│   │   └── indexer.py
│   ├── jobs/                   # Jobs de processamento
│   │   ├── typesense/sync_job.py
│   │   ├── embeddings/embedding_generator.py
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

### Scraping

```bash
# Raspar sites gov.br
data-platform scrape --start-date 2025-01-01 --end-date 2025-01-31

# Raspar sites EBC (Agência Brasil, TV Brasil)
data-platform scrape-ebc --start-date 2025-01-01
```

### Enriquecimento

```bash
# Upload para Cogfy
data-platform upload-cogfy --start-date 2025-01-01

# Buscar enriquecimento do Cogfy
data-platform enrich --start-date 2025-01-01 --force
```

### Embeddings

```bash
# Gerar embeddings para notícias
data-platform generate-embeddings --start-date 2025-01-01
```

### Typesense

```bash
# Sincronizar PostgreSQL → Typesense
data-platform sync-typesense --start-date 2025-01-01

# Sincronização completa (full reload)
data-platform sync-typesense --full-sync

# Listar collections
data-platform typesense-list

# Deletar collection
data-platform typesense-delete --confirm
```

### HuggingFace

```bash
# Sincronizar PostgreSQL → HuggingFace
data-platform sync-hf --start-date 2025-01-01
```

## Storage Adapter

O **StorageAdapter** é a camada de abstração que permite transição gradual entre backends de armazenamento.

### Modos de Operação

| Modo | Descrição |
|------|-----------|
| `POSTGRES` | Escreve apenas no PostgreSQL |
| `HUGGINGFACE` | Escreve apenas no HuggingFace (legado) |
| `DUAL_WRITE` | Escreve em ambos para transição segura |

### Configuração

```bash
# Variáveis de ambiente
STORAGE_BACKEND=postgres          # postgres | huggingface | dual_write
STORAGE_READ_FROM=postgres        # De onde ler os dados
```

### Uso no Código

```python
from data_platform.managers.storage_adapter import StorageAdapter, StorageBackend

adapter = StorageAdapter(
    backend=StorageBackend.DUAL_WRITE,
    read_from=StorageBackend.POSTGRES
)

# Insert transparente - escreve em ambos
inserted = adapter.insert(news_list, allow_update=False)

# Read - sempre do backend configurado em read_from
news = adapter.get(filters={"agency_key": "mec"}, limit=100)
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

# Cogfy
COGFY_API_KEY=xxx
COGFY_COLLECTION_ID=xxx

# Embeddings
EMBEDDINGS_API_URL=https://embeddings-api-xxx.run.app
EMBEDDINGS_API_KEY=xxx

# Storage
STORAGE_BACKEND=postgres
STORAGE_READ_FROM=postgres
```

## Workflows GitHub Actions

| Workflow | Trigger | Descrição |
|----------|---------|-----------|
| `main-workflow.yaml` | Diário (4AM UTC) | Pipeline completo: scrape → enrich → embed → sync |
| `typesense-maintenance-sync.yaml` | Diário (10AM UTC) | Sync incremental Typesense |
| `composer-deploy-dags.yaml` | Push | Deploy de DAGs no Airflow |

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
