# Arquitetura GCP

> Infraestrutura do DestaquesGovbr no Google Cloud Platform.

**Repositório**: [github.com/destaquesgovbr/destaquesgovbr-infra](https://github.com/destaquesgovbr/destaquesgovbr-infra) (privado)

## Visão Geral

A infraestrutura é gerenciada via **Terraform** e consiste em:

```mermaid
flowchart TB
    subgraph "Google Cloud Platform"
        subgraph "Networking"
            VPC[VPC Network]
            SUB[Subnet us-east1]
            FW[Firewall Rules]
        end

        subgraph "Compute"
            CR[Cloud Run<br/>Portal Next.js]
            CE[Compute Engine<br/>Typesense]
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
    SA -->|Push| AR

    CR -->|VPC Connector| VPC
    VPC --> CE
```

---

## Componentes

### 1. Cloud Run (Portal)

| Propriedade | Valor |
|-------------|-------|
| Serviço | `destaquesgovbr-portal` |
| Região | `us-east1` |
| CPU | 1 |
| Memória | 512Mi |
| Min instances | 0 |
| Max instances | 10 |
| Concurrency | 80 |

**Características:**
- Serverless (escala automática)
- VPC Connector para acesso ao Typesense
- HTTPS automático

### 2. Compute Engine (Typesense)

| Propriedade | Valor |
|-------------|-------|
| Nome | `typesense-server` |
| Tipo | `e2-medium` |
| Região | `us-east1-b` |
| Disco | 50GB SSD |
| IP | Interno (VPC) |

**Características:**
- VM dedicada para Typesense
- Persistência de dados em disco
- Acesso via VPC (não exposto à internet)

### 3. Artifact Registry

| Propriedade | Valor |
|-------------|-------|
| Repositório | `destaquesgovbr` |
| Região | `us-east1` |
| Formato | Docker |

**Imagens:**
- `portal` - Imagem do portal Next.js

### 4. Secret Manager

Secrets armazenadas:

- `typesense-api-key` - API Key do Typesense
- Outras credenciais sensíveis

### 5. VPC Network

| Propriedade | Valor |
|-------------|-------|
| Nome | `destaquesgovbr-vpc` |
| Subnet | `10.0.0.0/24` |
| Região | `us-east1` |

**Firewall Rules:**
- SSH interno
- Typesense (8108) interno
- HTTPS (443) externo para Cloud Run

---

## Diagrama de Rede

```mermaid
flowchart LR
    subgraph "Internet"
        U[Usuários]
    end

    subgraph "GCP - us-east1"
        subgraph "VPC 10.0.0.0/24"
            CR[Cloud Run<br/>Portal]
            VC[VPC Connector]
            TS[Compute Engine<br/>Typesense<br/>10.0.0.x]
        end
    end

    U -->|HTTPS| CR
    CR -->|VPC Connector| VC
    VC -->|:8108| TS
```

---

## Custos Estimados

| Componente | Custo/mês |
|------------|-----------|
| Compute Engine (Typesense) | ~$55 |
| Cloud Run (Portal) | ~$12-17 |
| Artifact Registry | ~$1 |
| VPC Connector | ~$2 |
| **Total** | **~$70-75** |

> Valores aproximados. Podem variar com uso.

---

## Regiões e Zonas

| Recurso | Região/Zona |
|---------|-------------|
| VPC | global |
| Subnet | us-east1 |
| Cloud Run | us-east1 |
| Compute Engine | us-east1-b |
| Artifact Registry | us-east1 |

**Por que us-east1?**
- Menor latência para Brasil
- Disponibilidade de recursos
- Custo competitivo

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
gcloud compute ssh typesense-server --zone=us-east1-b

# Verificar Typesense
curl http://localhost:8108/health
```

---

## Monitoramento

### Cloud Run

```bash
# Status do serviço
gcloud run services describe destaquesgovbr-portal --region=us-east1

# Logs
gcloud run services logs read destaquesgovbr-portal --region=us-east1

# Métricas (via Console)
# Console > Cloud Run > destaquesgovbr-portal > Metrics
```

### Compute Engine

```bash
# Status da VM
gcloud compute instances describe typesense-server --zone=us-east1-b

# Logs do sistema
gcloud compute ssh typesense-server --zone=us-east1-b -- sudo journalctl -u typesense

# Métricas (via Console)
# Console > Compute Engine > typesense-server > Monitoring
```

---

## Backup e Recuperação

### Typesense Data

```bash
# SSH no servidor
gcloud compute ssh typesense-server --zone=us-east1-b

# Backup do diretório de dados
sudo tar -czvf /tmp/typesense-backup.tar.gz /var/lib/typesense/data

# Download do backup
gcloud compute scp typesense-server:/tmp/typesense-backup.tar.gz . --zone=us-east1-b
```

### Recuperação

1. Parar Typesense
2. Restaurar dados do backup
3. Reiniciar Typesense
4. Verificar integridade

---

## Escalabilidade

### Cloud Run (Portal)

- **Automático**: Escala de 0 a 10 instâncias
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

---

## Links Relacionados

- [Terraform Guide](./terraform-guide.md) - Como gerenciar a infraestrutura
- [Secrets e IAM](./secrets-iam.md) - Permissões e credenciais
- [Deploy Portal](../workflows/portal-deploy.md) - Workflow de deploy
- [Typesense Data](../workflows/typesense-data.md) - Carga de dados
