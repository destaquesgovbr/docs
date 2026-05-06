# Scraper API - Cloud Run

**API FastAPI para scraping de notícias gov.br** hospedada no Google Cloud Run e orquestrada por Airflow DAGs.

---

## Visão Geral

A **Scraper API** é um serviço HTTP que encapsula a lógica de scraping de sites governamentais brasileiros (~155 agências gov.br + EBC). A API roda no **Cloud Run** e é chamada por **~156 DAGs Airflow** (Cloud Composer) que distribuem o scraping ao longo do tempo.

### Arquitetura

```mermaid
graph TB
    subgraph Cloud Composer
        DAG1[scrape_mec<br/>offset: 0min]
        DAG2[scrape_saude<br/>offset: 1min]
        DAG3[scrape_mre<br/>offset: 2min]
        DAGN[~155 DAGs<br/>distribuídas]
        DAGEBC[scrape_ebc<br/>offset: 0min]
    end
    
    subgraph Cloud Run
        API[Scraper API<br/>FastAPI]
    end
    
    subgraph Scraping
        WS1[WebScraper<br/>gov.br]
        WS2[EBCWebScraper<br/>Agência Brasil/TV Brasil]
    end
    
    subgraph Storage
        PG[(PostgreSQL<br/>Silver Layer)]
    end
    
    DAG1 -->|HTTP POST<br/>IAM Auth| API
    DAG2 -->|HTTP POST<br/>IAM Auth| API
    DAG3 -->|HTTP POST<br/>IAM Auth| API
    DAGN -->|HTTP POST<br/>IAM Auth| API
    DAGEBC -->|HTTP POST<br/>IAM Auth| API
    
    API -->|agency_key| WS1
    API -->|EBC sites| WS2
    
    WS1 -->|Fetch HTML| SITE1[Sites gov.br]
    WS2 -->|Fetch HTML| SITE2[agenciabrasil.ebc.com.br<br/>tvbrasil.ebc.com.br]
    
    WS1 -->|Parse → Markdown| PG
    WS2 -->|Parse → Markdown| PG
    
    style API fill:#f9a825
    style WS1 fill:#66bb6a
    style WS2 fill:#66bb6a
    style PG fill:#c0c0c0
```

---

## Endpoints

### POST `/scrape/agencies`

Raspa sites gov.br (aceita lista de agências e intervalo de datas).

**Request**:
```json
{
  "start_date": "2025-01-01",
  "end_date": "2025-01-02",
  "agencies": ["mec", "saude", "mre"],
  "allow_update": false,
  "sequential": true
}
```

**Parâmetros**:
- `start_date` (required): Data inicial (formato `YYYY-MM-DD`)
- `end_date` (optional): Data final, default = `start_date`
- `agencies` (optional): Lista de agency keys, default = todas as agências ativas
- `allow_update` (optional): Permite atualizar artigos existentes, default = `false`
- `sequential` (optional): Processa agências sequencialmente (vs paralelo), default = `true`

**Response** (200 OK):
```json
{
  "status": "completed",
  "start_date": "2025-01-01",
  "end_date": "2025-01-02",
  "articles_scraped": 450,
  "articles_saved": 420,
  "agencies_processed": ["mec", "saude", "mre"],
  "errors": [],
  "message": "Scraping completed"
}
```

**Response** (207 Multi-Status - sucesso parcial):
```json
{
  "status": "partial",
  "start_date": "2025-01-01",
  "end_date": "2025-01-01",
  "articles_scraped": 320,
  "articles_saved": 320,
  "agencies_processed": ["mec", "saude"],
  "errors": [
    {
      "agency": "mre",
      "error": "Connection timeout after 30s"
    }
  ],
  "message": "Completed with 1 error(s)"
}
```

**Response** (500 Internal Server Error - falha completa):
```json
{
  "status": "failed",
  "start_date": "2025-01-01",
  "end_date": "2025-01-01",
  "articles_scraped": 0,
  "articles_saved": 0,
  "agencies_processed": [],
  "errors": [
    {
      "agency": "mec",
      "error": "PostgreSQL connection refused"
    }
  ],
  "message": "All agencies failed"
}
```

---

### POST `/scrape/ebc`

Raspa sites EBC (Agência Brasil, TV Brasil, etc.).

**Request**:
```json
{
  "start_date": "2025-01-01",
  "end_date": "2025-01-02",
  "agencies": ["agenciabrasil", "tvbrasil"],
  "allow_update": false,
  "sequential": true
}
```

**Parâmetros**: Mesmos que `/scrape/agencies`.

**Response**: Mesma estrutura que `/scrape/agencies`.

---

### GET `/health`

Health check endpoint.

**Response**:
```json
{
  "status": "ok"
}
```

---

## Implementação

### Stack Tecnológico

| Componente | Tecnologia |
|-----------|-----------|
| **Framework** | FastAPI |
| **Runtime** | Python 3.12 |
| **Web Server** | Uvicorn |
| **Database** | PostgreSQL 15 |
| **Deploy** | Cloud Run |
| **Orquestração** | Cloud Composer (Airflow) |

### Estrutura de Código

```python
# src/govbr_scraper/api.py

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI(
    title="DestaquesGovBr Scraper API",
    description="HTTP wrapper for gov.br and EBC news scrapers",
    version="1.0.0",
)

class ScrapeAgenciesRequest(BaseModel):
    start_date: str
    end_date: str | None = None
    agencies: list[str] | None = None
    allow_update: bool = False
    sequential: bool = True

class ScrapeResponse(BaseModel):
    status: str  # "completed", "partial", "failed"
    start_date: str
    end_date: str
    articles_scraped: int = 0
    articles_saved: int = 0
    agencies_processed: list[str] = []
    errors: list[AgencyError] = []
    message: str

@app.post("/scrape/agencies", response_model=ScrapeResponse)
def scrape_agencies(req: ScrapeAgenciesRequest):
    from govbr_scraper.storage import StorageAdapter
    from govbr_scraper.scrapers.scrape_manager import ScrapeManager
    
    storage = StorageAdapter()
    manager = ScrapeManager(storage)
    
    metrics = manager.run_scraper(
        agencies=req.agencies,
        min_date=req.start_date,
        max_date=req.end_date or req.start_date,
        sequential=req.sequential,
        allow_update=req.allow_update,
    )
    
    # Determinar status e HTTP code
    errors = [AgencyError(**e) for e in metrics.get("errors", [])]
    if errors and not metrics["agencies_processed"]:
        status, http_status = "failed", 500
    elif errors:
        status, http_status = "partial", 207
    else:
        status, http_status = "completed", 200
    
    return JSONResponse(
        content=ScrapeResponse(...).model_dump(),
        status_code=http_status
    )
```

### Fluxo de Scraping

```mermaid
sequenceDiagram
    participant A as Airflow DAG
    participant API as Scraper API
    participant SM as ScrapeManager
    participant WS as WebScraper
    participant PG as PostgreSQL

    A->>API: POST /scrape/agencies<br/>{agencies: ["mec"], start_date: "2025-01-01"}
    API->>SM: run_scraper(agencies=["mec"])
    
    loop For each agency
        SM->>WS: scrape(agency="mec", date="2025-01-01")
        WS->>WS: Fetch HTML from gov.br
        WS->>WS: Parse HTML → Extract articles
        WS->>WS: Convert HTML → Markdown
        WS->>PG: INSERT INTO news (...)
        PG-->>WS: Success
        WS-->>SM: Metrics (articles_scraped, articles_saved)
    end
    
    SM-->>API: Aggregated metrics + errors
    API-->>A: ScrapeResponse (status, metrics, errors)
```

---

## Deployment

### Dockerfile

```dockerfile
FROM python:3.12-slim

WORKDIR /app

# System dependencies (minimal: only what scrapers + postgres need)
RUN apt-get update && apt-get install -y \
    build-essential gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Poetry
RUN pip install --no-cache-dir poetry

# Copy dependency files first (leverage Docker layer caching)
COPY pyproject.toml poetry.lock ./

# Configure Poetry to not create virtual environments
RUN poetry config virtualenvs.create false

# Install dependencies (without the package itself)
RUN poetry install --no-root --no-interaction --no-ansi

# Copy source code
COPY CLAUDE.md ./
COPY src/ src/

# Install the package itself
RUN poetry install --no-interaction --no-ansi

ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

EXPOSE 8080

CMD ["uvicorn", "govbr_scraper.api:app", "--host", "0.0.0.0", "--port", "8080"]
```

### Cloud Run Deploy

```bash
# Build e push da imagem
gcloud builds submit \
  --tag gcr.io/destaques-govbr/scraper-api:latest \
  --project=destaques-govbr

# Deploy no Cloud Run
gcloud run deploy scraper-api \
  --image gcr.io/destaques-govbr/scraper-api:latest \
  --platform=managed \
  --region=southamerica-east1 \
  --memory=2Gi \
  --cpu=2 \
  --min-instances=0 \
  --max-instances=10 \
  --timeout=600 \
  --concurrency=10 \
  --no-allow-unauthenticated \
  --set-env-vars=DATABASE_URL=postgresql://...,STORAGE_BACKEND=postgres,LOG_LEVEL=INFO
```

**Configurações importantes**:
- `--no-allow-unauthenticated`: Apenas Airflow (via IAM) pode chamar
- `timeout=600` (10 min): Scraping pode demorar para múltiplas agências
- `memory=2Gi`: HTML parsing e markdown conversion precisam de memória
- `min-instances=0`: Cold start aceitável (DAGs rodam a cada 10 min)

### GitHub Actions Workflow

```yaml
# .github/workflows/scraper-api-deploy.yaml
name: Deploy Scraper API to Cloud Run

on:
  push:
    branches: [main]
    paths:
      - 'src/**'
      - 'docker/**'
      - 'pyproject.toml'
      - 'poetry.lock'

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - id: auth
        uses: google-github-actions/auth@v2
        with:
          credentials_json: ${{ secrets.GCP_SA_KEY }}
      
      - name: Set up Cloud SDK
        uses: google-github-actions/setup-gcloud@v2
      
      - name: Build and push image
        run: |
          gcloud builds submit \
            --tag gcr.io/destaques-govbr/scraper-api:${{ github.sha }} \
            --tag gcr.io/destaques-govbr/scraper-api:latest
      
      - name: Deploy to Cloud Run
        run: |
          gcloud run deploy scraper-api \
            --image gcr.io/destaques-govbr/scraper-api:${{ github.sha }} \
            --region southamerica-east1 \
            --platform managed
```

---

## Orquestração com Airflow

### DAG Factory Pattern

A API é chamada por **~155 DAGs dinâmicas**, uma por agência gov.br:

```python
# dags/scrape_agencies.py

def create_scraper_dag(agency_key: str, agency_url: str, minute_offset: int = 0):
    """Factory que cria uma DAG de scraping para uma agência."""
    
    @dag(
        dag_id=f"scrape_{agency_key}",
        description=f"Scrape notícias de {agency_key}",
        schedule=f"{minute_offset}/10 * * * *",  # A cada 10 min, offset distribuído
        start_date=datetime(2025, 1, 1),
        catchup=False,
        max_active_runs=1,
        tags=["scraper", "govbr", agency_key],
        default_args={
            "retries": 2,
            "retry_delay": timedelta(minutes=5),
            "execution_timeout": timedelta(minutes=10),
        },
    )
    def scraper_dag():
        
        @task
        def scrape(**context):
            import httpx
            import google.oauth2.id_token
            from airflow.models import Variable
            
            scraper_api_url = Variable.get("scraper_api_url")
            
            # Token IAM para autenticação no Cloud Run
            token = google.oauth2.id_token.fetch_id_token(
                google.auth.transport.requests.Request(),
                scraper_api_url
            )
            
            logical_date = context["logical_date"]
            
            # Chamar API
            response = httpx.post(
                f"{scraper_api_url}/scrape/agencies",
                json={
                    "start_date": logical_date.strftime("%Y-%m-%d"),
                    "agencies": [agency_key],
                    "allow_update": False,
                    "sequential": True,
                },
                headers={"Authorization": f"Bearer {token}"},
                timeout=600,
            )
            
            response.raise_for_status()
            result = response.json()
            
            # Log métricas
            logger.info(
                f"Scraping {agency_key}: {result['articles_scraped']} scraped, "
                f"{result['articles_saved']} saved"
            )
            
            return result
        
        scrape()
    
    return scraper_dag()


# Gerar DAGs dinamicamente
agencies = _load_agencies_config()  # Carrega de site_urls.yaml

for idx, (key, url) in enumerate(agencies.items()):
    minute_offset = idx % 10  # Distribui: offset 0-9 (minutos)
    dag_instance = create_scraper_dag(key, url, minute_offset)
    globals()[f"scrape_{key}"] = dag_instance
```

### Distribuição Temporal

**Problema**: ~155 DAGs rodando simultaneamente podem sobrecarregar Cloud Run e sites gov.br.

**Solução**: Distribuir DAGs ao longo da janela de 10 minutos usando `minute_offset`:

```
Minuto 0: scrape_mec, scrape_mds, ... (~16 DAGs)
Minuto 1: scrape_saude, scrape_fazenda, ... (~16 DAGs)
Minuto 2: scrape_mre, scrape_agricultura, ... (~16 DAGs)
...
Minuto 9: scrape_educacao, scrape_turismo, ... (~15 DAGs)
```

**Cálculo**:
```python
minute_offset = idx % 10  # idx é o índice da agência (0-154)
schedule = f"{minute_offset}/10 * * * *"  # Cron: A cada 10 min, offset {minute_offset}
```

**Resultado**: ~16 DAGs por minuto, reduz pico de requisições de 155 → 16 simultâneas.

---

## Configuração

### Variáveis de Ambiente (Cloud Run)

```bash
# PostgreSQL
DATABASE_URL=postgresql://user:pass@10.x.x.x:5432/govbrnews

# Storage
STORAGE_BACKEND=postgres  # Sempre postgres para o scraper

# Logging
LOG_LEVEL=INFO
```

### Variáveis Airflow

```bash
# Via Airflow UI ou CLI
airflow variables set scraper_api_url "https://scraper-api-xxx.a.run.app"
```

### IAM Permissions

**Service Account da DAG** precisa:
```yaml
roles:
  - roles/run.invoker  # Chamar Cloud Run API
```

**Service Account do Cloud Run** precisa:
```yaml
roles:
  - roles/cloudsql.client  # Conectar ao PostgreSQL via Cloud SQL Proxy
```

---

## site_urls.yaml - Dual Configuration

### Problema

O arquivo `site_urls.yaml` existe em **dois locais**:
1. `src/govbr_scraper/scrapers/config/site_urls.yaml` (usado pela API)
2. `dags/config/site_urls.yaml` (usado pelas DAGs Airflow)

**Por que?**
- DAGs são autocontidas e não importam código Python da API
- API Cloud Run empacota `src/` na imagem Docker
- Mantém separação entre orquestração (DAGs) e execução (API)

### Sincronização

**Sempre edite**: `src/govbr_scraper/scrapers/config/site_urls.yaml` (fonte)

**Depois copie**:
```bash
cp src/govbr_scraper/scrapers/config/site_urls.yaml dags/config/site_urls.yaml
```

### Validação CI

```python
# tests/unit/test_config_sync.py

def test_site_urls_yaml_files_are_in_sync():
    """Valida que os dois arquivos site_urls.yaml estão sincronizados."""
    source = "src/govbr_scraper/scrapers/config/site_urls.yaml"
    copy = "dags/config/site_urls.yaml"
    
    with open(source) as f1, open(copy) as f2:
        source_content = f1.read()
        copy_content = f2.read()
    
    assert source_content == copy_content, \
        f"Files out of sync! Run: cp {source} {copy}"
```

**CI bloqueia PRs** com arquivos dessincronizados.

---

## Monitoramento

### Métricas Cloud Monitoring

```yaml
# Latência de scraping
- name: scraper_api_latency_p95
  metric: run.googleapis.com/request_latencies
  filter: resource.service_name="scraper-api"
  threshold: P95 > 300s
  
# Taxa de erro
- name: scraper_api_error_rate
  metric: run.googleapis.com/request_count
  filter: metric.response_code_class="5xx"
  threshold: > 2%
  
# Cold starts
- name: scraper_api_cold_starts
  metric: run.googleapis.com/container/startup_latencies
  threshold: P95 > 10s
```

### Logs Estruturados

```python
# Em api.py
logger.info(f"Scraping agencies: {req.agencies or 'ALL'} from {req.start_date} to {end}")
logger.error(f"Scraping failed: {e}")

# Em ScrapeManager
logger.info(f"Scraped {agency_key}: {articles_scraped} articles")
logger.warning(f"Failed to scrape {agency_key}: {error}")
```

### Dashboard Grafana

```yaml
# Query para monitorar throughput
- expr: |
    rate(scraper_api_requests_total[5m])
  legendFormat: "Scraping Requests/sec"

# Query para artigos raspados
- expr: |
    sum(rate(articles_scraped_total[5m]))
  legendFormat: "Articles Scraped/sec"
```

---

## Troubleshooting

### Problema: API retorna 500 "All agencies failed"

**Causa**: PostgreSQL inacessível.

**Solução**:
```bash
# Verificar logs do Cloud Run
gcloud logging read \
  "resource.type=cloud_run_revision AND \
   resource.labels.service_name=scraper-api AND \
   severity>=ERROR" \
  --limit=50

# Verificar conectividade PostgreSQL
gcloud sql instances describe destaques-govbr-postgres
```

---

### Problema: DAG falha com "403 Forbidden"

**Causa**: Service Account da DAG não tem `roles/run.invoker`.

**Solução**:
```bash
# Identificar SA da DAG
SA_EMAIL=$(gcloud composer environments describe destaquesgovbr-composer \
  --location us-central1 \
  --format="value(config.nodeConfig.serviceAccount)")

# Adicionar role
gcloud run services add-iam-policy-binding scraper-api \
  --region=southamerica-east1 \
  --member="serviceAccount:${SA_EMAIL}" \
  --role="roles/run.invoker"
```

---

### Problema: Múltiplas DAGs falhando simultaneamente

**Causa**: Cloud Run atingiu `max-instances` ou sites gov.br instáveis.

**Solução**:
```bash
# Aumentar max-instances
gcloud run services update scraper-api \
  --max-instances=20 \
  --region=southamerica-east1

# Verificar status de sites gov.br manualmente
curl -I https://www.mec.gov.br/ultimas-noticias
```

---

## Custos Estimados

### Cálculo

| Item | Quantidade | Custo Unitário | Custo Mensal |
|------|-----------|---------------|--------------|
| **Cloud Run (requests)** | ~156 DAGs × 4.320/mês (10min) | $0.40/million | $0.27 |
| **Cloud Run (CPU time)** | 30s/request × 673k | $0.000024/GB-s | $483.84 |
| **Cloud Run (memory)** | 2Gi × 30s × 673k | $0.0000025/GiB-s | $50.47 |
| **Total** | - | - | **~$534.58/mês** |

**Assumptions**:
- 156 DAGs × 6 runs/hora × 24h × 30 dias = ~673k requests/mês
- Scraping duration ~30s/agência
- 2GiB memory allocation

**Otimizações**:
- Reduzir para 1GiB se scraping for otimizado
- Aumentar `concurrency` para processar mais requests por container

---

## Referências

### Interna
- [Módulo Scraper](../modulos/scraper.md)
- [Airflow DAGs](./airflow-dags.md)
- [Scraper Pipeline](./scraper-pipeline.md)

### Externa
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Cloud Run Authentication](https://cloud.google.com/run/docs/authenticating/service-to-service)
- [Airflow DAG Factory Pattern](https://www.astronomer.io/blog/dynamically-generating-dags/)

---

**Última atualização**: 06/05/2026  
**Responsável**: Equipe Scraper - DestaquesGovbr  
**Status**: ✅ Em Produção