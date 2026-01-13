# PostgreSQL - Fonte de Verdade

O PostgreSQL (Cloud SQL) é a **fonte de verdade central** do sistema DestaquesGovBr, armazenando todas as notícias coletadas, enriquecidas e processadas.

!!! info "Cloud SQL"
    **Instância**: `destaquesgovbr-postgres`
    **Região**: `southamerica-east1` (São Paulo)
    **Versão**: PostgreSQL 15

## Schema

O banco de dados possui **4 tabelas principais** com normalização parcial.

```mermaid
erDiagram
    agencies ||--o{ news : "has"
    themes ||--o{ news : "theme_l1"
    themes ||--o{ news : "theme_l2"
    themes ||--o{ news : "theme_l3"
    themes ||--o{ news : "most_specific"

    agencies {
        int id PK
        string key UK
        string name
        string type
        string parent_key
        string url
        timestamp created_at
    }

    themes {
        int id PK
        string code UK
        string label
        string full_name
        int level
        string parent_code
        timestamp created_at
    }

    news {
        int id PK
        string unique_id UK
        int agency_id FK
        int theme_l1_id FK
        int theme_l2_id FK
        int theme_l3_id FK
        int most_specific_theme_id FK
        string title
        string url
        text content
        string summary
        vector content_embedding
        timestamp published_at
        timestamp created_at
    }

    sync_log {
        int id PK
        string operation
        string status
        json details
        timestamp created_at
    }
```

### Tabela `agencies`

Dados mestres de agências governamentais (158 registros).

| Coluna | Tipo | Descrição |
|--------|------|-----------|
| `id` | `SERIAL` | Chave primária |
| `key` | `VARCHAR(100)` | Identificador único (ex: `mec`, `saude`) |
| `name` | `VARCHAR(255)` | Nome completo da agência |
| `type` | `VARCHAR(50)` | Tipo (ministério, autarquia, etc) |
| `parent_key` | `VARCHAR(100)` | Chave da agência pai (hierarquia) |
| `url` | `VARCHAR(500)` | URL do portal da agência |
| `created_at` | `TIMESTAMP` | Data de criação |

**Índices**: `key` (unique), `parent_key`

### Tabela `themes`

Taxonomia hierárquica de temas em 3 níveis (200+ registros).

| Coluna | Tipo | Descrição |
|--------|------|-----------|
| `id` | `SERIAL` | Chave primária |
| `code` | `VARCHAR(20)` | Código hierárquico (ex: `01`, `01.01`, `01.01.01`) |
| `label` | `VARCHAR(255)` | Nome curto do tema |
| `full_name` | `VARCHAR(500)` | Nome completo incluindo hierarquia |
| `level` | `INTEGER` | Nível hierárquico (1, 2 ou 3) |
| `parent_code` | `VARCHAR(20)` | Código do tema pai |
| `created_at` | `TIMESTAMP` | Data de criação |

**Índices**: `code` (unique), `level`, `parent_code`

**Exemplo de hierarquia**:
```
01 - Economia e Finanças (level 1)
  01.01 - Política Econômica (level 2)
    01.01.01 - Política Fiscal (level 3)
```

### Tabela `news`

Notícias coletadas e enriquecidas (300k+ registros).

| Coluna | Tipo | Descrição |
|--------|------|-----------|
| **Chaves** | | |
| `id` | `SERIAL` | Chave primária |
| `unique_id` | `VARCHAR(32)` | MD5(agency + published_at + title) |
| **Foreign Keys** | | |
| `agency_id` | `INTEGER` | FK para `agencies.id` |
| `theme_l1_id` | `INTEGER` | Tema nível 1 |
| `theme_l2_id` | `INTEGER` | Tema nível 2 |
| `theme_l3_id` | `INTEGER` | Tema nível 3 |
| `most_specific_theme_id` | `INTEGER` | Tema mais específico (L3 > L2 > L1) |
| **Conteúdo** | | |
| `title` | `VARCHAR(500)` | Título da notícia |
| `url` | `VARCHAR(1000)` | URL original |
| `image_url` | `VARCHAR(1000)` | URL da imagem |
| `video_url` | `VARCHAR(1000)` | URL do vídeo |
| `category` | `VARCHAR(100)` | Categoria original do site |
| `tags` | `TEXT[]` | Tags originais do site |
| `content` | `TEXT` | Conteúdo completo em Markdown |
| `editorial_lead` | `TEXT` | Lead editorial |
| `subtitle` | `VARCHAR(500)` | Subtítulo |
| `summary` | `TEXT` | Resumo gerado pelo Cogfy |
| **Timestamps** | | |
| `published_at` | `TIMESTAMP` | Data de publicação |
| `updated_datetime` | `TIMESTAMP` | Última atualização no site |
| `extracted_at` | `TIMESTAMP` | Data de extração |
| `created_at` | `TIMESTAMP` | Data de inserção no BD |
| `updated_at` | `TIMESTAMP` | Última atualização no BD |
| **Denormalizados** | | |
| `agency_key` | `VARCHAR(100)` | Key da agência (performance) |
| `agency_name` | `VARCHAR(255)` | Nome da agência (performance) |
| **Embeddings** | | |
| `content_embedding` | `VECTOR(768)` | Embedding do conteúdo |
| `embedding_generated_at` | `TIMESTAMP` | Data de geração do embedding |

**Índices**:

- `unique_id` (unique)
- `published_at DESC` (ordenação)
- `agency_id` (filtro por agência)
- `most_specific_theme_id` (filtro por tema)
- `(agency_id, published_at DESC)` (composto)
- `agency_key` (filtro rápido)
- Full-text search: `tsvector('portuguese', title || ' ' || content)`

### Tabela `sync_log`

Log de operações de sincronização (auditoria).

| Coluna | Tipo | Descrição |
|--------|------|-----------|
| `id` | `SERIAL` | Chave primária |
| `operation` | `VARCHAR(50)` | Tipo (scrape, enrich, typesense_sync, hf_sync) |
| `status` | `VARCHAR(20)` | Status (started, completed, failed) |
| `details` | `JSONB` | Metadados (count, errors, duration) |
| `created_at` | `TIMESTAMP` | Timestamp da operação |

## Configuração Cloud SQL

### Instância

| Configuração | Valor |
|--------------|-------|
| **Nome** | `destaquesgovbr-postgres` |
| **Versão** | PostgreSQL 15 |
| **Tier** | `db-custom-1-3840` (1 vCPU, 3.75GB RAM) |
| **Storage** | 50GB SSD (auto-resize até 500GB) |
| **Região** | `southamerica-east1` |
| **Availability** | ZONAL |
| **Deletion Protection** | Habilitado |

### Rede

```mermaid
graph LR
    subgraph "VPC Network"
        PG[(Cloud SQL<br/>Private IP)]
        CR[Cloud Run<br/>Portal]
        CE[Compute Engine<br/>Typesense]
        GHA[GitHub Actions<br/>Cloud SQL Proxy]
    end

    CR -.->|VPC Connector| PG
    CE -->|Internal IP| PG
    GHA -->|SQL Proxy| PG
```

- **IP Privado**: Via VPC peering
- **Acesso externo**: Apenas via Cloud SQL Proxy

### Backup

| Configuração | Valor |
|--------------|-------|
| **Backups automáticos** | Diários às 3AM UTC |
| **Point-in-time recovery** | Habilitado (7 dias) |
| **Retenção** | 30 backups |
| **Auto-resize** | Até 500GB |

### Performance Flags

```sql
-- Conexões
max_connections = 100

-- Memória
shared_buffers = 256MB
effective_cache_size = 336MB
work_mem = 2.5MB
maintenance_work_mem = 64MB

-- Logging
log_min_duration_statement = 1000  -- Log queries > 1s
```

### Query Insights

- **Habilitado**: Sim
- **Query string length**: 1024 caracteres
- **Application tags**: Habilitadas

## Secrets

As credenciais são armazenadas no Secret Manager:

| Secret ID | Conteúdo |
|-----------|----------|
| `govbrnews-postgres-connection-string` | `postgresql://user:pass@host:5432/govbrnews` |
| `govbrnews-postgres-host` | IP privado da instância |
| `govbrnews-postgres-password` | Senha do usuário `govbrnews_app` |

## Acesso

### Pelo Código (data-platform)

```python
from data_platform.managers.postgres_manager import PostgresManager

pm = PostgresManager()  # Lê DATABASE_URL ou Secret Manager
pm.load_cache()

# Operações
news = pm.get(filters={"agency_key": "mec"}, limit=100)
pm.insert(news_list, allow_update=True)
```

### Variáveis de Ambiente

```bash
# Conexão direta (desenvolvimento)
DATABASE_URL=postgresql://govbrnews_app:xxx@10.x.x.x:5432/govbrnews

# Ou via Secret Manager (produção)
# A aplicação busca automaticamente se DATABASE_URL não estiver definida
```

### Via Cloud SQL Proxy (local)

```bash
# Instalar proxy
curl -o cloud_sql_proxy https://dl.google.com/cloudsql/cloud_sql_proxy.linux.amd64
chmod +x cloud_sql_proxy

# Conectar
./cloud_sql_proxy -instances=inspire-7-finep:southamerica-east1:destaquesgovbr-postgres=tcp:5432

# Em outro terminal
psql -h localhost -U govbrnews_app -d govbrnews
```

## Custos Estimados

| Componente | Custo/mês |
|------------|-----------|
| Instância (db-custom-1-3840) | ~$35 |
| Storage (50GB SSD) | ~$8.50 |
| Backups (30 dias) | ~$5 |
| **Total** | **~$48.50** |

## Normalização Parcial

O schema adota normalização **parcial** para balancear integridade e performance:

### Normalizado

- **agencies**: Tabela de lookup separada
- **themes**: Taxonomia hierárquica com self-reference

### Denormalizado (performance)

- `agency_key` e `agency_name` em `news`: Evita JOINs em queries frequentes
- Índice composto `(agency_id, published_at)`: Otimiza filtros combinados

### Vantagens

1. **Integridade**: FKs garantem consistência
2. **Performance**: Campos denormalizados evitam JOINs
3. **Flexibilidade**: Normalização permite queries complexas quando necessário
