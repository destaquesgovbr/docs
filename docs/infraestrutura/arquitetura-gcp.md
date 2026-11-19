# Arquitetura GCP

> Infraestrutura do DestaquesGovbr no Google Cloud Platform.

**Repositório**: [github.com/destaquesgovbr/infra](https://github.com/destaquesgovbr/infra) (privado)

## Visão Geral

A infraestrutura é gerenciada via **Terraform** e consiste em:

```mermaid
flowchart TB
    subgraph "Google Cloud Platform"
        subgraph "Networking"
            VPC[VPC Network]
            SUB[Subnet southamerica-east1]
            FW[Firewall Rules]
        end

        subgraph "Databases"
            PG[(Cloud SQL<br/>PostgreSQL 15)]
        end

        subgraph "Compute"
            CR[Cloud Run<br/>Portal Next.js]
            EMB[Cloud Run<br/>Embeddings API]
            CE[Compute Engine<br/>Typesense]
        end

        subgraph "Orchestration"
            CC[Compute Engine<br/>Airflow 3.1 próprio<br/>LB HTTPS + IAP]
        end

        subgraph "Storage & Registry"
            AR[Artifact Registry<br/>Docker Images]
            SM[Secret Manager<br/>Credentials]
        end

        subgraph "Identity"
            SA[Service Accounts]
            WIF[Workload Identity<br/>GitHub OIDC]
        end
    end

    GH[GitHub Actions] -->|OIDC| WIF
    WIF -->|Impersonate| SA
    SA -->|Deploy| CR
    SA -->|Deploy| EMB
    SA -->|Push| AR

    CR -->|VPC Connector| VPC
    EMB -->|VPC Connector| VPC
    CC -->|VPC| VPC
    VPC --> CE
    VPC --> PG
```

---

## Componentes

### 1. Cloud SQL (PostgreSQL) - Fonte de Verdade

| Propriedade | Valor |
|-------------|-------|
| Instância | `destaquesgovbr-postgres` |
| Versão | PostgreSQL 15 |
| Região | `southamerica-east1` |
| Tier | `db-f1-micro` (upgrade planejado) |
| vCPU | 1 |
| Memória | 3.75 GB |
| Disco | 50GB SSD (auto-resize até 500GB) |
| Backup | Diário com PITR 7 dias |

**Características:**
- Fonte de verdade central do sistema
- Private IP (acesso apenas via VPC)
- Backups automáticos diários
- Point-in-time recovery (7 dias)

→ Veja detalhes em [PostgreSQL](../arquitetura/postgresql.md)

### 2. Airflow próprio (Compute Engine)

| Propriedade | Valor |
|-------------|-------|
| VM | `destaquesgovbr-airflow` (e2-standard-2, Debian 12, sem IP público) |
| Versão | Airflow 3.1.8, LocalExecutor, em docker compose |
| Zona | `southamerica-east1-a` |
| UI | `https://airflow.dgb.app.gov.br` (LB HTTPS + IAP) |
| Bucket | `gs://destaquesgovbr-airflow` (`dags/`, `plugins/`, `logs/`) |
| Service Account | `destaquesgovbr-composer` (nome herdado do Composer) |

**DAGs** (todas em BRT):
- `scrape_agencies` e `scrape_ebc`: scraping a cada 2 h, das 06h às 22h
- DAGs do `data-platform` (trending, clusters, grafo de entidades, syncs para o BigQuery, backfills), `dispatch_clippings` (clipping) e `sync_postgres_to_huggingface` (data-publishing, 06h)

**Características:**
- Substituiu o Cloud Composer em 18/11/2026 (~US$ 738/mês → ~US$ 110/mês)
- GitOps: compose, env e startup-script vêm do Terraform pelo metadata da VM
- Postgres de metadados num disco de dados com snapshot diário
- Alerta "Airflow sem heartbeat" e alertas de memória/disco (Ops Agent) no Telegram

→ Veja detalhes em [Airflow DAGs](../workflows/airflow-dags.md)

### 3. Cloud Run (Portal)

| Propriedade | Valor |
|-------------|-------|
| Serviço | `portal` |
| Região | `southamerica-east1` |
| CPU | 1 |
| Memória | 512Mi |
| Min instances | 0 |
| Max instances | 10 |
| Concurrency | 80 |

**Características:**
- Serverless (escala automática)
- VPC Connector para acesso ao Typesense
- HTTPS automático

### 4. Cloud Run (Embeddings API)

| Propriedade | Valor |
|-------------|-------|
| Serviço | `embeddings-api` |
| Região | `southamerica-east1` |
| CPU | 2 |
| Memória | 4Gi |
| Min instances | 0 |
| Max instances | 5 |

**Características:**
- Modelo: `paraphrase-multilingual-mpnet-base-v2`
- Vetores 768-dim
- VPC Connector para acesso ao PostgreSQL
- GPU opcional para maior throughput

### 4b. Cloud Run (GraphQL API)

| Propriedade | Valor |
|-------------|-------|
| Serviço | `destaquesgovbr-graphql-api` |
| Região | `southamerica-east1` |
| Stack | Strawberry GraphQL + FastAPI (Python 3.12) |
| Min instances | 0 |

**Características:**

- Fachada de dados única (Firestore + PostgreSQL + Typesense) — ver
  [ADR-002](../arquitetura/adrs/adr-002-fachada-graphql.md) e o
  [módulo GraphQL API](../modulos/graphql-api.md).
- Auth: JWT do Keycloak (usuários) + OIDC do Google (service accounts/workers).
- Env vars geridas pelo Terraform; SSE em `/graphql/stream` para o agente de IA.
- IAM: a SA do portal e a SA do graphql-api têm `roles/run.invoker` onde
  necessário (ex.: graphql-api → clipping worker para o passthrough do agente).

### 5. Compute Engine (Typesense)

| Propriedade | Valor |
|-------------|-------|
| Nome | `typesense-server` |
| Tipo | `e2-medium` |
| Região | `southamerica-east1-a` |
| Disco | 50GB SSD |
| IP | Interno (VPC) |

**Características:**
- VM dedicada para Typesense
- Suporte a busca vetorial (768-dim)
- Persistência de dados em disco
- Acesso via VPC (não exposto à internet)

### 6. Artifact Registry

| Propriedade | Valor |
|-------------|-------|
| Repositório | `destaquesgovbr` |
| Região | `southamerica-east1` |
| Formato | Docker |

**Imagens:**
- `portal` - Imagem do portal Next.js
- `data-platform` - Imagem do data platform
- `embeddings-api` - Imagem da API de embeddings
- `destaquesgovbr-graphql-api` - Imagem da fachada GraphQL

### 7. Secret Manager

Secrets armazenadas:

| Secret | Descrição |
|--------|-----------|
| `postgres-host` | IP privado do Cloud SQL |
| `postgres-password` | Senha do banco |
| `typesense-api-key` | API Key do Typesense |
| `cogfy-api-key` | API Key do Cogfy |
| `cogfy-collection-id` | ID da collection Cogfy |
| `hf-token` | Token HuggingFace (write) |

### 8. VPC Network

| Propriedade | Valor |
|-------------|-------|
| Nome | `destaquesgovbr-vpc` |
| Subnet | `10.0.0.0/24` |
| Região | `southamerica-east1` |

**Firewall Rules:**
- SSH interno
- Typesense (8108) interno
- PostgreSQL (5432) interno
- HTTPS (443) externo para Cloud Run

---

## Diagrama de Rede

```mermaid
flowchart LR
    subgraph "Internet"
        U[Usuários]
        HF[(HuggingFace)]
    end

    subgraph "GCP - southamerica-east1"
        subgraph "VPC 10.0.0.0/24"
            CR[Cloud Run<br/>Portal]
            EMB[Cloud Run<br/>Embeddings API]
            VC[VPC Connector]
            TS[Compute Engine<br/>Typesense<br/>10.0.0.x]
            PG[(Cloud SQL<br/>PostgreSQL<br/>10.0.0.y)]
            CC[Compute Engine<br/>Airflow próprio]
        end
    end

    U -->|HTTPS| CR
    CR -->|VPC Connector| VC
    VC -->|:8108| TS
    VC -->|:5432| PG
    EMB -->|VPC Connector| VC
    CC -->|:5432| PG
    CC -->|Sync| HF
```

---

## Custos Estimados

| Componente | Custo/mês |
|------------|-----------|
| Cloud SQL (PostgreSQL) | ~$48 |
| Airflow próprio (VM + discos + LB) | ~$106-113 |
| Compute Engine (Typesense) | ~$64 |
| Cloud Run (Portal) | ~$10 |
| Cloud Run (Embeddings API) | ~$5 |
| Artifact Registry | ~$1 |
| VPC Connector | ~$2 |
| Secret Manager | ~$1 |
| **Total** | **~$230-280** |

> Valores aproximados. Podem variar com uso.

---

## Regiões e Zonas

| Recurso | Região/Zona |
|---------|-------------|
| VPC | global |
| Subnet | southamerica-east1 |
| Cloud SQL | southamerica-east1 |
| Cloud Run | southamerica-east1 |
| Airflow (VM) | southamerica-east1-a |
| Compute Engine | southamerica-east1-a |
| Artifact Registry | southamerica-east1 |

**Por que southamerica-east1 (São Paulo)?**
- Menor latência para usuários brasileiros
- Conformidade com dados do governo
- Disponibilidade de recursos

---

## Fluxo de Deploy

```mermaid
sequenceDiagram
    participant DEV as Developer
    participant GH as GitHub
    participant WIF as Workload Identity
    participant AR as Artifact Registry
    participant CR as Cloud Run

    DEV->>GH: git push main
    GH->>WIF: Request OIDC token
    WIF-->>GH: SA credentials
    GH->>AR: docker push
    GH->>CR: gcloud run deploy
    CR->>AR: Pull image
    CR-->>GH: Deploy complete
```

---

## Acesso SSH ao Typesense

```bash
# Via gcloud
gcloud compute ssh typesense-server --zone=southamerica-east1-a

# Verificar Typesense
curl http://localhost:8108/health
```

---

## Acesso ao PostgreSQL

```bash
# Via Cloud SQL Proxy (desenvolvimento local)
cloud_sql_proxy -instances=PROJECT_ID:southamerica-east1:destaquesgovbr-postgres=tcp:5432

# Conectar
psql -h localhost -U admin -d destaquesgovbr

# Via gcloud (admin)
gcloud sql connect destaquesgovbr-postgres --user=admin
```

---

## Acesso ao Airflow

UI: [https://airflow.dgb.app.gov.br](https://airflow.dgb.app.gov.br), pelo IAP, com conta Google da equipe.

A VM não tem IP público: a CLI do Airflow só é alcançada por SSH via IAP, no container do scheduler.

```bash
gcloud compute ssh destaquesgovbr-airflow --zone=southamerica-east1-a \
  --project=inspire-7-finep --tunnel-through-iap

# Na VM: listar DAGs
sudo docker exec airflow-airflow-scheduler-1 airflow dags list

# Na VM: trigger manual de DAG (muda estado; combine com a equipe)
sudo docker exec airflow-airflow-scheduler-1 airflow dags trigger sync_postgres_to_huggingface
```

---

## Monitoramento

### Cloud SQL

```bash
# Status da instância
gcloud sql instances describe destaquesgovbr-postgres

# Métricas (via Console)
# Console > SQL > destaquesgovbr-postgres > Monitoring
```

### Cloud Run

```bash
# Status do serviço
gcloud run services describe portal --region=southamerica-east1

# Logs
gcloud run services logs read portal --region=southamerica-east1
```

### Airflow (VM)

```bash
# Status da VM
gcloud compute instances describe destaquesgovbr-airflow --zone=southamerica-east1-a

# Logs dos containers (scheduler, dag-processor, api-server)
gcloud logging read 'logName="projects/inspire-7-finep/logs/gcplogs-docker-driver"' \
  --project=inspire-7-finep --freshness=1h --limit=20 --format='value(timestamp,jsonPayload.message)'

# Logs das tasks (GCS, 30 dias)
gcloud storage ls gs://destaquesgovbr-airflow/logs/
```

### Compute Engine

```bash
# Status da VM
gcloud compute instances describe typesense-server --zone=southamerica-east1-a

# Logs do sistema
gcloud compute ssh typesense-server --zone=southamerica-east1-a -- sudo journalctl -u typesense
```

---

## Backup e Recuperação

### PostgreSQL (Cloud SQL)

```bash
# Backups são automáticos (diários)
# Listar backups
gcloud sql backups list --instance=destaquesgovbr-postgres

# Restaurar de um backup
gcloud sql backups restore BACKUP_ID \
  --restore-instance=destaquesgovbr-postgres \
  --backup-instance=destaquesgovbr-postgres
```

### Typesense Data

```bash
# SSH no servidor
gcloud compute ssh typesense-server --zone=southamerica-east1-a

# Backup do diretório de dados
sudo tar -czvf /tmp/typesense-backup.tar.gz /var/lib/typesense/data

# Download do backup
gcloud compute scp typesense-server:/tmp/typesense-backup.tar.gz . --zone=southamerica-east1-a
```

---

## Escalabilidade

### Cloud SQL

- **Vertical**: Upgrade de tier (db-f1-micro → db-g1-small → db-custom)
- **Read replicas**: Disponível se necessário
- **Disk auto-resize**: Habilitado (até 500GB)

### Airflow (VM)

- **Vertical**: trocar `airflow_machine_type` (ex.: e2-highmem-2 se a memória apertar), com stop/start
- **Concorrência**: `parallelism` do LocalExecutor (8) e limites por DAG (ex.: 4 agências ao mesmo tempo no scraping)

### Cloud Run

- **Automático**: Escala de 0 a N instâncias
- **Cold start**: ~2-3 segundos
- **Ajustes**: Via Terraform ou Console

### Typesense

- **Manual**: Upgrade de máquina se necessário
- **Atual**: e2-medium (2 vCPU, 4GB RAM)
- **Recomendado para crescimento**: e2-standard-4

---

## Segurança

### Rede

- Typesense **não exposto** à internet
- PostgreSQL **não exposto** à internet
- Acesso apenas via VPC Connector
- Firewall restritivo

### Identidade

- Workload Identity Federation (sem service account keys)
- Princípio do menor privilégio
- Rotação automática de credenciais

### Secrets

- Armazenados no Secret Manager
- Versionamento automático
- Acesso auditado

### Dados

- Backups automáticos do Cloud SQL
- Criptografia em repouso (padrão GCP)
- Criptografia em trânsito (TLS)

---

## Terraform (Arquivos Principais)

| Arquivo | Conteúdo |
|---------|----------|
| `main.tf` | Providers e configurações globais |
| `network.tf` | VPC, subnets, firewall |
| `cloud_sql.tf` | PostgreSQL |
| `airflow-base.tf`, `airflow.tf`, `airflow-lb.tf` | Airflow próprio: bucket, Artifact Registry, secrets, VM, disco de dados, LB HTTPS + IAP |
| `cloud_run.tf` | Portal e Embeddings API |
| `compute.tf` | Typesense VM |
| `iam.tf` | Service accounts e Workload Identity |
| `secrets.tf` | Secret Manager |
| `artifact_registry.tf` | Registry Docker |

---

## Links Relacionados

- [PostgreSQL](../arquitetura/postgresql.md) - Banco de dados central
- [Terraform Guide](./terraform-guide.md) - Como gerenciar a infraestrutura
- [Secrets e IAM](./secrets-iam.md) - Permissões e credenciais
- [Deploy Portal](../workflows/portal-deploy.md) - Workflow de deploy
- [Typesense Data](../workflows/typesense-data.md) - Carga de dados
- [Airflow DAGs](../workflows/airflow-dags.md) - Pipelines de orquestração
