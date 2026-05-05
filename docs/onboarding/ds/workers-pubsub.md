# Template: Criando Workers Pub/Sub

Guia prático para criar novos workers que processam eventos Google Cloud Pub/Sub no DestaquesGovbr.

---

## 📋 Quando Criar um Worker

Crie um novo worker Pub/Sub quando precisar:

- ✅ Processar eventos assíncronos (scraping, enrichment, indexação)
- ✅ Escalar horizontalmente (Cloud Run auto-scaling)
- ✅ Garantir entrega confiável (retry automático, DLQ)
- ✅ Desacoplar componentes (event-driven architecture)

**Não use Pub/Sub para**:
- ❌ Requisições síncronas (use HTTP REST/GraphQL)
- ❌ Queries de leitura (use cache ou API)
- ❌ Operações que exigem resposta imediata ao usuário

---

## 🏗️ Template Base

### 1. Estrutura de Diretórios

```
seu-worker/
├── app.py                # FastAPI application
├── handler.py            # Lógica de processamento
├── Dockerfile
├── requirements.txt
├── .env.example
└── tests/
    └── test_handler.py
```

### 2. `app.py` - FastAPI Application

```python
from fastapi import FastAPI, Request, HTTPException
from handler import process_message
import base64
import json
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Seu Worker")

@app.post("/")
async def handle_pubsub_push(request: Request):
    """
    Endpoint que recebe mensagens Pub/Sub push.
    
    Formato do envelope Pub/Sub:
    {
        "message": {
            "data": "base64-encoded-json",
            "attributes": {
                "trace_id": "...",
                "entity_id": "..."
            },
            "messageId": "...",
            "publishTime": "2026-05-05T10:00:00Z"
        },
        "subscription": "projects/.../subscriptions/..."
    }
    """
    try:
        envelope = await request.json()
        
        # 1. Parse envelope
        message = envelope.get('message', {})
        message_id = message.get('messageId', 'unknown')
        attributes = message.get('attributes', {})
        trace_id = attributes.get('trace_id', message_id)
        
        # 2. Decode base64 data
        data_b64 = message.get('data', '')
        if not data_b64:
            raise ValueError("Empty message data")
        
        data_json = base64.b64decode(data_b64).decode('utf-8')
        payload = json.loads(data_json)
        
        logger.info(f"[{trace_id}] Processing message {message_id}")
        
        # 3. Process message
        result = await process_message(payload, trace_id)
        
        logger.info(f"[{trace_id}] Success: {result}")
        
        # 4. ACK (200 OK)
        return {"status": "success", "trace_id": trace_id, "result": result}
        
    except json.JSONDecodeError as e:
        # 4xx = ACK (não retenta)
        logger.error(f"[{trace_id}] Invalid JSON: {e}")
        raise HTTPException(status_code=400, detail="Invalid JSON payload")
        
    except ValueError as e:
        # 4xx = ACK (não retenta)
        logger.error(f"[{trace_id}] Validation error: {e}")
        raise HTTPException(status_code=400, detail=str(e))
        
    except Exception as e:
        # 5xx = NACK (retenta)
        logger.exception(f"[{trace_id}] Processing error: {e}")
        raise HTTPException(status_code=500, detail="Internal processing error")

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "version": "1.0.0"}
```

### 3. `handler.py` - Lógica de Processamento

```python
import asyncio
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

async def process_message(payload: Dict[str, Any], trace_id: str) -> Dict[str, Any]:
    """
    Processa a mensagem Pub/Sub.
    
    Args:
        payload: Dados da mensagem (já decodificados)
        trace_id: ID de rastreamento para logs
    
    Returns:
        Resultado do processamento
    
    Raises:
        ValueError: Se payload inválido (4xx, ACK)
        Exception: Se erro de processamento (5xx, NACK)
    """
    # 1. Validar payload
    validate_payload(payload)
    
    # 2. Verificar idempotência
    if is_already_processed(payload.get('entity_id')):
        logger.info(f"[{trace_id}] Already processed, skipping")
        return {"status": "skipped", "reason": "already_processed"}
    
    # 3. Processar
    result = await do_processing(payload, trace_id)
    
    # 4. Persistir resultado
    await persist_result(result, trace_id)
    
    # 5. Publicar evento downstream (opcional)
    await publish_downstream_event(result, trace_id)
    
    return {"status": "processed", "entity_id": payload['entity_id']}

def validate_payload(payload: Dict[str, Any]):
    """
    Valida payload da mensagem.
    
    Raises:
        ValueError: Se payload inválido
    """
    required_fields = ['entity_id', 'data']
    
    for field in required_fields:
        if field not in payload:
            raise ValueError(f"Missing required field: {field}")
    
    # Validações específicas
    if not isinstance(payload['entity_id'], str):
        raise ValueError("entity_id must be string")

def is_already_processed(entity_id: str) -> bool:
    """
    Verifica se entidade já foi processada (idempotência).
    
    Implementações comuns:
    - Verificar campo no banco de dados (e.g., enriched_at IS NOT NULL)
    - Verificar em cache Redis
    - Verificar arquivo em GCS
    """
    # Exemplo com PostgreSQL
    # return db.exists(f"SELECT 1 FROM entities WHERE id = '{entity_id}' AND processed = true")
    return False  # Implementar conforme necessidade

async def do_processing(payload: Dict[str, Any], trace_id: str) -> Dict[str, Any]:
    """
    Lógica principal de processamento.
    
    IMPORTANTE: Implemente retry internamente se necessário.
    """
    logger.info(f"[{trace_id}] Processing entity {payload['entity_id']}")
    
    # Simular processamento
    await asyncio.sleep(0.5)
    
    # Retornar resultado
    return {
        "entity_id": payload['entity_id'],
        "processed_data": "...",
        "timestamp": "2026-05-05T10:00:00Z"
    }

async def persist_result(result: Dict[str, Any], trace_id: str):
    """Persiste resultado no banco de dados."""
    logger.info(f"[{trace_id}] Persisting result")
    # Implementar conforme necessidade

async def publish_downstream_event(result: Dict[str, Any], trace_id: str):
    """Publica evento downstream (opcional)."""
    # from google.cloud import pubsub_v1
    # publisher = pubsub_v1.PublisherClient()
    # topic_path = publisher.topic_path('project-id', 'downstream-topic')
    # publisher.publish(topic_path, json.dumps(result).encode('utf-8'))
    pass
```

### 4. `Dockerfile`

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY app.py handler.py ./

# Expose port
EXPOSE 8080

# Run with Uvicorn
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8080", "--workers", "1"]
```

### 5. `requirements.txt`

```
fastapi==0.109.0
uvicorn[standard]==0.27.0
google-cloud-pubsub==2.19.0
google-cloud-logging==3.9.0
# Adicione suas dependências específicas
```

---

## ⚙️ Configuração Pub/Sub

### 1. Criar Tópico

```bash
gcloud pubsub topics create seu-topic-name \
  --project=seu-project-id
```

### 2. Criar Subscription com Push

```bash
gcloud pubsub subscriptions create seu-worker-sub \
  --topic=seu-topic-name \
  --push-endpoint=https://seu-worker-xxx.a.run.app \
  --ack-deadline=600 \
  --retry-policy-minimum-backoff=10s \
  --retry-policy-maximum-backoff=600s \
  --dead-letter-topic=seu-topic-name-dlq \
  --max-delivery-attempts=5
```

**Parâmetros importantes**:
- `--ack-deadline`: Tempo máximo de processamento (segundos)
- `--retry-policy-minimum-backoff`: Delay inicial entre retries
- `--retry-policy-maximum-backoff`: Delay máximo entre retries
- `--max-delivery-attempts`: Tentativas antes de ir para DLQ

### 3. Criar Dead-Letter Queue (DLQ)

```bash
# Criar tópico DLQ
gcloud pubsub topics create seu-topic-name-dlq

# Criar subscription pull para inspeção manual
gcloud pubsub subscriptions create seu-topic-name-dlq-sub \
  --topic=seu-topic-name-dlq
```

---

## 🚀 Deploy no Cloud Run

### 1. Build e Push da Imagem

```bash
# Build
docker build -t gcr.io/seu-project-id/seu-worker:latest .

# Push
docker push gcr.io/seu-project-id/seu-worker:latest
```

### 2. Deploy

```bash
gcloud run deploy seu-worker \
  --image=gcr.io/seu-project-id/seu-worker:latest \
  --platform=managed \
  --region=us-east1 \
  --memory=2Gi \
  --cpu=1 \
  --min-instances=1 \
  --max-instances=10 \
  --timeout=600 \
  --concurrency=80 \
  --allow-unauthenticated \
  --set-env-vars="PROJECT_ID=seu-project-id,ENVIRONMENT=production"
```

**Parâmetros recomendados**:
- `--min-instances=1`: Evita cold starts (crítico para Pub/Sub push)
- `--timeout=600`: Deve ser < que `ack-deadline`
- `--concurrency=80`: Requisições simultâneas por instância

---

## 🔍 Padrões de Idempotência

### Opção 1: Verificar Campo no DB

```python
def is_already_processed(entity_id: str) -> bool:
    """Verifica se campo NOT NULL no banco."""
    import psycopg2
    conn = psycopg2.connect(os.getenv('DATABASE_URL'))
    cursor = conn.cursor()
    cursor.execute(
        "SELECT 1 FROM entities WHERE id = %s AND processed_field IS NOT NULL",
        (entity_id,)
    )
    return cursor.fetchone() is not None
```

### Opção 2: Cache Redis

```python
import redis

redis_client = redis.Redis(host='localhost', port=6379, db=0)

def is_already_processed(entity_id: str) -> bool:
    """Verifica se existe no Redis."""
    key = f"processed:{entity_id}"
    return redis_client.exists(key)

def mark_as_processed(entity_id: str):
    """Marca como processado no Redis (TTL 7 dias)."""
    key = f"processed:{entity_id}"
    redis_client.setex(key, 604800, "1")
```

### Opção 3: GCS Checkpoint Files

```python
from google.cloud import storage

storage_client = storage.Client()
bucket = storage_client.bucket('seu-bucket-checkpoints')

def is_already_processed(entity_id: str) -> bool:
    """Verifica se arquivo existe no GCS."""
    blob = bucket.blob(f"processed/{entity_id}")
    return blob.exists()

def mark_as_processed(entity_id: str):
    """Cria arquivo checkpoint no GCS."""
    blob = bucket.blob(f"processed/{entity_id}")
    blob.upload_from_string("processed")
```

---

## 🧪 Testes

### `tests/test_handler.py`

```python
import pytest
from handler import process_message, validate_payload

@pytest.mark.asyncio
async def test_process_message_success():
    """Testa processamento bem-sucedido."""
    payload = {
        "entity_id": "test-123",
        "data": {"field": "value"}
    }
    trace_id = "test-trace-123"
    
    result = await process_message(payload, trace_id)
    
    assert result["status"] == "processed"
    assert result["entity_id"] == "test-123"

def test_validate_payload_missing_field():
    """Testa validação com campo faltando."""
    payload = {"entity_id": "test-123"}  # falta 'data'
    
    with pytest.raises(ValueError, match="Missing required field: data"):
        validate_payload(payload)

def test_validate_payload_invalid_type():
    """Testa validação com tipo inválido."""
    payload = {"entity_id": 123, "data": {}}  # entity_id deve ser string
    
    with pytest.raises(ValueError, match="entity_id must be string"):
        validate_payload(payload)
```

### Teste Local com Pub/Sub Emulator

```bash
# Instalar emulador
gcloud components install pubsub-emulator

# Iniciar emulador
gcloud beta emulators pubsub start --project=test-project

# Em outro terminal, configurar variáveis
export PUBSUB_EMULATOR_HOST=localhost:8085
export PUBSUB_PROJECT_ID=test-project

# Publicar mensagem de teste
python -c "
from google.cloud import pubsub_v1
import json, base64

publisher = pubsub_v1.PublisherClient()
topic_path = publisher.topic_path('test-project', 'test-topic')

data = json.dumps({'entity_id': 'test-123', 'data': {}})
publisher.publish(topic_path, base64.b64encode(data.encode()).decode().encode())
print('Published test message')
"
```

---

## 📊 Monitoramento

### Métricas Essenciais

```python
from google.cloud import monitoring_v3
import time

client = monitoring_v3.MetricServiceClient()
project_name = f"projects/{project_id}"

def record_processing_latency(trace_id: str, latency_ms: int):
    """Registra latência de processamento."""
    series = monitoring_v3.TimeSeries()
    series.metric.type = "custom.googleapis.com/worker/processing_latency"
    series.resource.type = "global"
    
    point = series.points.add()
    point.value.int64_value = latency_ms
    point.interval.end_time.seconds = int(time.time())
    
    client.create_time_series(request={"name": project_name, "time_series": [series]})

def record_error(trace_id: str, error_type: str):
    """Registra erro."""
    # Similar ao acima
    pass
```

### Alertas Recomendados

| Métrica | Threshold | Ação |
|---------|-----------|------|
| `error_rate` | > 1% | Página time on-call |
| `processing_latency_p95` | > 30s | Investigar performance |
| `dlq_message_count` | > 10 | Reprocessar manualmente |
| `cold_start_count` | > 5/hour | Aumentar min-instances |

---

## 🐛 Troubleshooting

### Problema: Mensagens não são processadas

**Diagnóstico**:
```bash
# Verificar subscription
gcloud pubsub subscriptions describe seu-worker-sub

# Verificar logs do Cloud Run
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=seu-worker" --limit=50
```

### Problema: Muitas mensagens na DLQ

**Diagnóstico**:
```bash
# Listar mensagens DLQ
gcloud pubsub subscriptions pull seu-topic-name-dlq-sub --limit=10
```

**Replay**:
```bash
# Republicar após fix
gcloud pubsub subscriptions pull seu-topic-name-dlq-sub --limit=100 --format=json | \
  jq -r '.[] | .message.data' | \
  while read data; do
    gcloud pubsub topics publish seu-topic-name --message="$data"
  done
```

---

## ✅ Checklist de Criação

- [ ] Estrutura de diretórios criada
- [ ] `app.py` com FastAPI implementado
- [ ] `handler.py` com lógica de processamento
- [ ] Validação de payload implementada
- [ ] Idempotência implementada
- [ ] Testes unitários escritos
- [ ] Dockerfile criado
- [ ] Tópico Pub/Sub criado
- [ ] Subscription com push configurada
- [ ] DLQ configurada
- [ ] Worker deployed no Cloud Run
- [ ] Métricas e alertas configurados
- [ ] Teste end-to-end realizado

---

## 📚 Referências

- [Google Cloud Pub/Sub Documentation](https://cloud.google.com/pubsub/docs)
- [Cloud Run Documentation](https://cloud.google.com/run/docs)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [News Enrichment Worker](../../modulos/news-enrichment-worker.md) - Exemplo real

---

**Última atualização**: 05/05/2026  
**Responsável**: Equipe Data Science - DestaquesGovbr