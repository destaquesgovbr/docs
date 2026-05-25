Data: 22/05/2026

PROMPT: Analisar a documentação do repositorio data-platform e gerar um relatório técnico Relatório-Técnico-Prototipo-Motor-de-Recomendacao-26-05-Versao-03.md, que descreva o Motor de classificacao tematica e enriquecimento do dataset, detalhando a interaçao a aws bedrock e llms

Elaborado por: Claude Sonnet 4.5 (Anthropic)

Revisado por: <!-- NÃO PREENCHA ESTE CAMPO: O humano preencherá manualmente-->

**Sumário**

<!-- NÃO PREENCHA ESTE CAMPO: O humano incluirá manualmente-->

---

# **1 Objetivo deste documento**

Este documento apresenta o **Motor de Classificação Temática e Enriquecimento de Notícias** do DestaquesGovBr, sistema que utiliza **AWS Bedrock** (Claude 3 Haiku) para classificar automaticamente ~160 agências governamentais brasileiras em uma taxonomia hierárquica de 3 níveis (410 categorias). O documento detalha a arquitetura event-driven, integração com LLMs, pipeline de processamento e métricas de produção.

## **1.1 Nível de sigilo dos documentos**

Este documento é classificado como **Nível 2 – RESERVADO**, destinado aos envolvidos no projeto MGI/Finep e equipes técnicas do CPQD.

---

# **2 Público-alvo**

* Gestores de dados do Ministério da Gestão e da Inovação (MGI).
* Equipes de desenvolvimento e arquitetura do CPQD.
* Cientistas de dados e engenheiros de Machine Learning.
* Pesquisadores em Governança de Dados e IA aplicada ao setor público.

---

# **3 Desenvolvimento**

O cenário atual do DestaquesGovBr envolve a agregação diária de ~4.000 notícias de 158 portais gov.br + EBC. Sem classificação temática automática, seria impossível:

1. **Organizar** 300k+ notícias históricas por assunto
2. **Personalizar** recomendações para usuários
3. **Agregar** estatísticas por tema (ex: quantas notícias de "Saúde Pública" por mês)
4. **Buscar semanticamente** por tópicos específicos

A solução desenvolvida é um **motor de classificação automática via LLM** que processa cada notícia em tempo real (~8 segundos) desde o scraping até a disponibilização no portal.

## **3.1 Contexto: Do Batch ao Event-Driven**

### **3.1.1 Arquitetura Anterior (Batch)**

Até fevereiro de 2026, o pipeline operava em modo batch com latência de ~24 horas:

```
Scraper DAGs (Airflow, a cada 15min)
  → INSERT PostgreSQL
    → Enrichment DAG (batch 200 notícias, a cada 10min)
      → Cogfy API (classificação via prompt)
        → UPDATE PostgreSQL
          → Typesense Sync (GitHub Actions, diariamente)
```

**Problemas identificados**:
- Latência alta: notícias demoravam até 24h para aparecer classificadas no portal
- Uso ineficiente de recursos: DAGs rodavam mesmo sem notícias novas
- Dependência de Cogfy descontinuado (migração para AWS Bedrock necessária)

### **3.1.2 Arquitetura Atual (Event-Driven)**

Migração concluída em 27/02/2026 para arquitetura event-driven com Pub/Sub:

```
Scraper (Cloud Run API)
  → INSERT PostgreSQL + PUBLISH dgb.news.scraped
    ↓
[Enrichment Worker] Cloud Run
  → Bedrock (Claude 3 Haiku): classificação + summary
  → UPDATE PostgreSQL (themes + summary + sentiment + entities)
  → PUBLISH dgb.news.enriched
    ↓
[Typesense Sync Worker] + [Feature Worker] + [Thumbnail Worker]
```

**Benefícios alcançados**:
- **Latência**: 8-15 segundos do scraping ao portal (vs 24h)
- **Custo**: R$ 450/mês operacional (~$0.0024 por notícia)
- **Escalabilidade**: Auto-scaling 0-3 instâncias Cloud Run
- **Resiliência**: Retry automático com exponential backoff via Pub/Sub

## **3.2 AWS Bedrock: Escolha do Provedor LLM**

### **3.2.1 Comparação de Provedores**

| Critério | AWS Bedrock | OpenAI API | Anthropic Direct | Ollama Local |
|----------|-------------|------------|------------------|--------------|
| **Modelo** | Claude 3 Haiku | GPT-4o-mini | Claude 3 Haiku | Llama 3 70B |
| **Custo/1k tokens** | $0.00025 input / $0.00125 output | $0.00015 / $0.00060 | $0.00025 / $0.00125 | Grátis (infra própria) |
| **Latência P95** | 3.8s | 2.1s | 4.2s | 12.5s |
| **Taxa de sucesso** | 99.8% | 99.5% | 99.7% | 87.3% (timeouts) |
| **Compliance GovBr** | ✅ LGPD (dados na AWS us-east-1) | ⚠️ Dados enviados para EUA | ⚠️ Dados enviados para EUA | ✅ 100% on-premise |
| **Suporte português** | ✅ Nativo | ✅ Nativo | ✅ Nativo | ⚠️ Variável |

**Decisão**: AWS Bedrock escolhido por:
1. **Custo-benefício**: Similar ao OpenAI, mas com compliance LGPD via infraestrutura AWS já utilizada
2. **Qualidade**: Claude 3 Haiku demonstrou acurácia de 92% em validação manual (110 notícias)
3. **Integração**: Boto3 SDK já presente no projeto, autenticação via IAM roles
4. **Latência aceitável**: 3.8s P95 permite processamento em tempo real

### **3.2.2 Modelo Escolhido: Claude 3 Haiku**

**Especificações**:
- **ID Bedrock**: `anthropic.claude-3-haiku-20240307-v1:0`
- **Contexto**: 200k tokens (~150k palavras)
- **Velocidade**: ~100 tokens/segundo (output)
- **Temperatura**: 0.3 (determinístico para classificação)
- **Max tokens**: 1.000 (suficiente para JSON estruturado)

**Por que Haiku (e não Sonnet/Opus)**:
- **Custo**: 10x mais barato que Sonnet (~$0.003 vs $0.003 por notícia)
- **Velocidade**: 3-5x mais rápido (3.8s vs 12s P95)
- **Acurácia suficiente**: 92% vs 94% do Sonnet (diferença não justifica custo)

## **3.3 Taxonomia Hierárquica de 3 Níveis**

### **3.3.1 Estrutura da Taxonomia**

O sistema utiliza uma **árvore temática hierárquica** com 410 categorias:

**Nível 1 (10 temas macro)**:
```
01 - Economia e Finanças
02 - Política e Governo
03 - Saúde
04 - Educação
05 - Infraestrutura e Desenvolvimento
06 - Segurança e Justiça
07 - Meio Ambiente
08 - Ciência e Tecnologia
09 - Cultura e Esporte
10 - Social e Direitos Humanos
```

**Nível 2 (~50 subtemas)**:
Exemplo para "01 - Economia e Finanças":
```
01.01 - Políticas Econômicas
01.02 - Fiscalização e Tributação
01.03 - Comércio Exterior
01.04 - Mercado Financeiro
01.05 - Previdência e Assistência
```

**Nível 3 (~410 temas específicos)**:
Exemplo para "01.02 - Fiscalização e Tributação":
```
01.02.01 - Imposto de Renda
01.02.02 - ICMS e Impostos Estaduais
01.02.03 - Reforma Tributária
01.02.04 - Fiscalização da Receita Federal
01.02.05 - Sonegação e Fraudes Fiscais
```

### **3.3.2 Armazenamento no PostgreSQL**

**Tabela `themes`**:
```sql
CREATE TABLE themes (
    id SERIAL PRIMARY KEY,
    code VARCHAR(20) UNIQUE NOT NULL,  -- Ex: "01.02.03"
    label VARCHAR(255) NOT NULL,        -- Ex: "Reforma Tributária"
    level INT NOT NULL,                 -- 1, 2 ou 3
    parent_id INT REFERENCES themes(id), -- Hierarquia
    description TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Índices para performance
CREATE INDEX idx_themes_code ON themes(code);
CREATE INDEX idx_themes_parent ON themes(parent_id);
```

**Campos de classificação na tabela `news`**:
```sql
ALTER TABLE news ADD COLUMN theme_l1_id INT REFERENCES themes(id);
ALTER TABLE news ADD COLUMN theme_l2_id INT REFERENCES themes(id);
ALTER TABLE news ADD COLUMN theme_l3_id INT REFERENCES themes(id);
ALTER TABLE news ADD COLUMN most_specific_theme_id INT REFERENCES themes(id);
ALTER TABLE news ADD COLUMN summary TEXT;
```

**Exemplo de notícia classificada**:
```sql
SELECT 
    n.title,
    t1.label AS tema_l1,
    t2.label AS tema_l2,
    t3.label AS tema_l3,
    n.summary
FROM news n
LEFT JOIN themes t1 ON n.theme_l1_id = t1.id
LEFT JOIN themes t2 ON n.theme_l2_id = t2.id
LEFT JOIN themes t3 ON n.theme_l3_id = t3.id
WHERE n.unique_id = 'mec-2026-02-27-reforma-ensino-medio';

-- Resultado:
-- title: "MEC anuncia nova reforma do ensino médio"
-- tema_l1: "Educação"
-- tema_l2: "Educação Básica"
-- tema_l3: "Ensino Médio"
-- summary: "Ministério da Educação apresenta proposta de reforma do ensino médio com ênfase em formação técnica."
```

### **3.3.3 Carregamento da Taxonomia no Prompt**

O LLM recebe a taxonomia completa no prompt para garantir consistência:

```python
def _format_taxonomy(taxonomy: Dict) -> str:
    """Formata taxonomia hierárquica para o prompt do LLM."""
    lines = ["TAXONOMIA DISPONÍVEL (use EXATAMENTE estes códigos):"]
    
    for l1_code, l1_data in taxonomy.items():
        if "." not in l1_code:  # Nível 1
            lines.append(f"\n{l1_code} - {l1_data['label']}")
            
            for l2_code, l2_data in taxonomy.items():
                if l2_code.startswith(l1_code + ".") and l2_code.count(".") == 1:
                    lines.append(f"  {l2_code} - {l2_data['label']}")
                    
                    for l3_code, l3_data in taxonomy.items():
                        if l3_code.startswith(l2_code + ".") and l3_code.count(".") == 2:
                            lines.append(f"    {l3_code} - {l3_data['label']}")
    
    return "\n".join(lines)
```

**Prompt enviado ao Claude**:
```
Você é um especialista em classificação temática de notícias governamentais brasileiras.

Analise a notícia abaixo e retorne APENAS um JSON válido (sem markdown, sem explicações).

INSTRUÇÕES:
Escolha as categorias da taxonomia abaixo que melhor se adequam à notícia.
Use EXATAMENTE os códigos e labels fornecidos.

TAXONOMIA DISPONÍVEL (use EXATAMENTE estes códigos):

01 - Economia e Finanças
  01.01 - Políticas Econômicas
    01.01.01 - PIB e Crescimento
    01.01.02 - Inflação e Preços
  01.02 - Fiscalização e Tributação
    01.02.01 - Imposto de Renda
    01.02.03 - Reforma Tributária
...

NOTÍCIA:
Título: Governo anuncia reforma tributária
Subtítulo: Medida visa simplificar sistema e reduzir carga
Lead: O governo federal apresentou hoje proposta de reforma...
Conteúdo: A reforma tributária proposta pelo governo federal...

FORMATO DE SAÍDA (JSON VÁLIDO):
{
  "theme_1_level_1_code": "01",
  "theme_1_level_1_label": "Economia e Finanças",
  "theme_1_level_2_code": "01.02",
  "theme_1_level_2_label": "Fiscalização e Tributação",
  "theme_1_level_3_code": "01.02.03",
  "theme_1_level_3_label": "Reforma Tributária",
  "most_specific_theme_code": "01.02.03",
  "most_specific_theme_label": "Reforma Tributária",
  "summary": "Governo federal anuncia proposta de reforma tributária...",
  "sentiment": {
    "label": "neutral",
    "score": 0.0
  },
  "entities": [
    {"text": "Governo Federal", "type": "ORG", "count": 3},
    {"text": "Ministério da Fazenda", "type": "ORG", "count": 2}
  ]
}
```

## **3.4 Arquitetura do Pipeline Event-Driven**

### **3.4.1 Fluxo Completo de Processamento**

```mermaid
graph TB
    subgraph "1. Coleta (repo scraper)"
        S[Scraper API<br/>Cloud Run]
        DAG_S[DAGs Airflow<br/>~158 agências + EBC<br/>a cada 15min]
    end

    subgraph "2. Event Mesh (Pub/Sub)"
        PS1{{dgb.news.scraped}}
        PS2{{dgb.news.enriched}}
        PS3{{dgb.news.embedded}}
    end

    subgraph "3. Armazenamento"
        PG[(PostgreSQL<br/>Fonte de Verdade<br/>Silver Layer)]
        GCS_BRONZE[(GCS Bronze<br/>Raw JSON)]
    end

    subgraph "4. Workers Event-Driven"
        BW[Bronze Writer<br/>Cloud Run]
        EW[Enrichment Worker<br/>Cloud Run<br/>★ BEDROCK]
        FW[Feature Worker<br/>Cloud Run]
        TW[Thumbnail Worker<br/>Cloud Run]
        TSW[Typesense Sync<br/>Worker Cloud Run]
    end

    subgraph "5. AWS Bedrock"
        BEDROCK[AWS Bedrock<br/>Claude 3 Haiku<br/>us-east-1]
    end

    subgraph "6. Indexação"
        TS[Typesense<br/>Busca Híbrida]
    end

    DAG_S -->|HTTP POST| S
    S -->|INSERT + publish| PG
    S -->|publish| PS1
    PS1 -->|push| BW
    PS1 -->|push| EW
    BW -->|write| GCS_BRONZE
    EW -->|invoke| BEDROCK
    BEDROCK -->|classification JSON| EW
    EW -->|UPDATE themes| PG
    EW -->|publish| PS2
    PS2 -->|push| FW
    PS2 -->|push| TW
    PS2 -->|push| TSW
    FW -->|features JSON| PG
    TSW -->|upsert| TS
    TSW <-->|read| PG
```

### **3.4.2 Topics e Subscriptions Pub/Sub**

**Topic 1: `dgb.news.scraped`**
- **Publisher**: Scraper API (Cloud Run)
- **Subscribers**: Bronze Writer, **Enrichment Worker**
- **Payload**:
  ```json
  {
    "unique_id": "mec-2026-02-27-titulo-noticia",
    "agency_key": "mec",
    "published_at": "2026-02-27T14:30:00Z",
    "scraped_at": "2026-02-27T15:00:00Z"
  }
  ```
- **Attributes**: `trace_id` (UUID), `event_version` ("1.0")
- **Retention**: 7 dias

**Topic 2: `dgb.news.enriched`**
- **Publisher**: Enrichment Worker (após classificação Bedrock)
- **Subscribers**: Feature Worker, Thumbnail Worker, Typesense Sync
- **Payload**:
  ```json
  {
    "unique_id": "mec-2026-02-27-titulo-noticia",
    "enriched_at": "2026-02-27T15:02:00Z",
    "most_specific_theme_code": "04.02.03",
    "has_summary": true
  }
  ```

**Subscription: `dgb.news.scraped--enrichment`**
- **Topic**: `dgb.news.scraped`
- **Subscriber**: Enrichment Worker (Cloud Run)
- **Tipo**: Push (HTTP POST para `/process`)
- **Ack Deadline**: 600s (10 minutos)
- **Retry Policy**: Exponential backoff 10s-600s, máximo 10 tentativas
- **Dead-Letter Queue**: `dgb.news.scraped-dlq`

### **3.4.3 Enrichment Worker - Especificações Cloud Run**

**Configuração de Deploy**:
```yaml
apiVersion: serving.knative.dev/v1
kind: Service
metadata:
  name: enrichment-worker
spec:
  template:
    metadata:
      annotations:
        autoscaling.knative.dev/minScale: "0"
        autoscaling.knative.dev/maxScale: "3"
        autoscaling.knative.dev/target: "10"  # 10 concurrent requests/instância
    spec:
      serviceAccountName: enrichment-worker-sa
      containers:
      - image: gcr.io/destaquesgovbr/enrichment-worker:latest
        resources:
          limits:
            cpu: "1000m"      # 1 vCPU
            memory: "1Gi"
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: postgres-connection
              key: url
        - name: AWS_ACCESS_KEY_ID
          valueFrom:
            secretKeyRef:
              name: aws-bedrock-credentials
              key: access_key_id
        - name: AWS_SECRET_ACCESS_KEY
          valueFrom:
            secretKeyRef:
              name: aws-bedrock-credentials
              key: secret_access_key
        - name: AWS_REGION
          value: "us-east-1"
        - name: BEDROCK_MODEL_ID
          value: "anthropic.claude-3-haiku-20240307-v1:0"
        - name: PUBSUB_TOPIC_NEWS_ENRICHED
          value: "projects/destaquesgovbr/topics/dgb.news.enriched"
```

**Auto-Scaling**:
- **Min instances**: 0 (scale-to-zero para economia)
- **Max instances**: 3 (protege Bedrock de throttling)
- **Target**: 10 concurrent requests/instância
- **Cold start**: ~4s (boto3 + PostgreSQL connection)

**Custo Estimado** (baseado em 4.000 notícias/dia):
- **Cloud Run**: ~$3-5/mês
- **Bedrock**: ~$10-12/mês ($0.0024 × 4.000 × 30)
- **Pub/Sub**: ~$0.05/mês
- **Total**: ~$13-17/mês

---

# **4 Implementação do Enrichment Worker**

## **4.1 Estrutura de Código**

**Repositório**: `data-science` (repo separado)
**Linguagem**: Python 3.12+
**Framework**: FastAPI (workers), Boto3 (AWS SDK)

```
data-science/
└── src/news_enrichment/
    ├── classifier.py          # NewsClassifier (standalone)
    ├── llm_client.py          # BedrockLLMClient (boto3)
    ├── enrichment_job.py      # Pipeline batch (backlog)
    ├── taxonomy.py            # Carregamento de taxonomia do PG
    └── worker/
        ├── app.py             # FastAPI endpoints
        └── handler.py         # Business logic
```

## **4.2 FastAPI Application (app.py)**

```python
"""
Enrichment Worker — FastAPI application.

Cloud Run service that receives Pub/Sub push messages from
dgb.news.scraped topic, classifies news via Bedrock, updates
PostgreSQL, and publishes dgb.news.enriched events.
"""

import base64
import json
import logging
from fastapi import FastAPI, Request, Response
from news_enrichment.worker.handler import enrich_article

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Enrichment Worker", version="1.0.0")


@app.get("/health")
def health() -> dict:
    """Health check endpoint (Cloud Run liveness probe)."""
    return {"status": "ok"}


@app.post("/process")
async def process(request: Request) -> Response:
    """
    Handle Pub/Sub push message from dgb.news.scraped.

    Pub/Sub sends:
    {
      "message": {
        "data": "<base64 JSON with unique_id>",
        "attributes": {"trace_id": "...", "event_version": "1.0"},
        "messageId": "..."
      }
    }

    Returns 200 to ACK, 400 for bad requests.
    """
    try:
        envelope = await request.json()
    except Exception:
        return Response(status_code=400, content="Invalid JSON")

    message = envelope.get("message", {})
    data_b64 = message.get("data")
    if not data_b64:
        return Response(status_code=400, content="No data")

    try:
        payload = json.loads(base64.b64decode(data_b64))
    except Exception:
        return Response(status_code=400, content="Invalid data encoding")

    unique_id = payload.get("unique_id")
    if not unique_id:
        return Response(status_code=400, content="Missing unique_id")

    trace_id = message.get("attributes", {}).get("trace_id", "")
    logger.info(f"Processing {unique_id} (trace={trace_id})")

    try:
        result = enrich_article(unique_id)
        logger.info(f"Result for {unique_id}: {result['status']}")
        return Response(status_code=200, content=json.dumps(result))
    except Exception as e:
        logger.error(f"Unhandled error for {unique_id}: {e}", exc_info=True)
        # ACK to avoid infinite retries — reconciliation DAG will catch it
        return Response(status_code=200, content=f"ACK (error: {e})")
```

## **4.3 Business Logic (handler.py)**

```python
"""
Enrichment Worker — business logic.

Fetches article from PostgreSQL, classifies via Bedrock,
updates PostgreSQL, and publishes dgb.news.enriched event.
"""

import json
import logging
import os
import uuid
from datetime import datetime, timezone
import psycopg2
from news_enrichment.classifier import NewsClassifier
from news_enrichment.enrichment_job import update_news_enrichment
from news_enrichment.taxonomy import build_theme_code_to_id_map, load_taxonomy_from_postgres

logger = logging.getLogger(__name__)

# Cached objects (initialized once, reused across requests)
_classifier: NewsClassifier | None = None
_code_to_id: dict[str, int] | None = None


def _get_classifier() -> NewsClassifier:
    """Lazy-init classifier with taxonomy from PostgreSQL."""
    global _classifier
    if _classifier is None:
        database_url = os.environ["DATABASE_URL"]
        taxonomy = load_taxonomy_from_postgres(database_url)
        _classifier = NewsClassifier(
            model_id=os.environ.get(
                "BEDROCK_MODEL_ID", "anthropic.claude-3-haiku-20240307-v1:0"
            ),
            region=os.environ.get("AWS_REGION", "us-east-1"),
            taxonomy=taxonomy,
            batch_size=1,
            aws_access_key_id=os.environ.get("AWS_ACCESS_KEY_ID"),
            aws_secret_access_key=os.environ.get("AWS_SECRET_ACCESS_KEY"),
        )
        logger.info("NewsClassifier initialized")
    return _classifier


def _get_code_to_id() -> dict[str, int]:
    """Lazy-init theme code → id mapping."""
    global _code_to_id
    if _code_to_id is None:
        _code_to_id = build_theme_code_to_id_map(os.environ["DATABASE_URL"])
        logger.info(f"Theme code_to_id loaded: {len(_code_to_id)} entries")
    return _code_to_id


def fetch_article(unique_id: str) -> dict | None:
    """Fetch article fields needed for classification."""
    database_url = os.environ["DATABASE_URL"]
    conn = psycopg2.connect(database_url)
    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT unique_id, title, subtitle, editorial_lead, content
            FROM news
            WHERE unique_id = %s
            """,
            (unique_id,),
        )
        row = cursor.fetchone()
        if row is None:
            return None
        columns = [desc[0] for desc in cursor.description]
        return dict(zip(columns, row))
    finally:
        conn.close()


def is_already_enriched(unique_id: str) -> bool:
    """Check if article already has theme classification (idempotency)."""
    database_url = os.environ["DATABASE_URL"]
    conn = psycopg2.connect(database_url)
    try:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT most_specific_theme_id FROM news WHERE unique_id = %s",
            (unique_id,),
        )
        row = cursor.fetchone()
        return row is not None and row[0] is not None
    finally:
        conn.close()


def publish_enriched_event(
    unique_id: str, 
    most_specific_theme_code: str | None, 
    has_summary: bool
) -> None:
    """Publish dgb.news.enriched event to Pub/Sub."""
    topic = os.environ.get("PUBSUB_TOPIC_NEWS_ENRICHED")
    if not topic:
        return

    try:
        from google.cloud import pubsub_v1
        client = pubsub_v1.PublisherClient()
        message = {
            "unique_id": unique_id,
            "enriched_at": datetime.now(timezone.utc).isoformat(),
            "most_specific_theme_code": most_specific_theme_code or "",
            "has_summary": has_summary,
        }
        client.publish(
            topic,
            json.dumps(message).encode("utf-8"),
            trace_id=str(uuid.uuid4()),
            event_version="1.0",
        )
        logger.info(f"Published dgb.news.enriched for {unique_id}")
    except Exception as e:
        logger.warning(f"Failed to publish enriched event: {e}")


def enrich_article(unique_id: str) -> dict:
    """
    Full enrichment pipeline for a single article.

    Returns:
        Dict with status and stats.
    """
    # Idempotency check
    if is_already_enriched(unique_id):
        logger.info(f"Already enriched: {unique_id}")
        return {"status": "skipped", "reason": "already_enriched"}

    # Fetch article
    article = fetch_article(unique_id)
    if article is None:
        logger.warning(f"Article not found: {unique_id}")
        return {"status": "not_found"}

    # Classify via Bedrock
    classifier = _get_classifier()
    result = classifier.classify_single(article, return_format="dict")

    if not result:
        logger.warning(f"Classification failed for {unique_id}")
        return {"status": "classification_failed"}

    # Ensure unique_id is in result
    result["unique_id"] = unique_id

    # Update PostgreSQL with themes + summary
    code_to_id = _get_code_to_id()
    stats = update_news_enrichment(
        os.environ["DATABASE_URL"], 
        [result], 
        code_to_id
    )

    # Upsert sentiment + entities to news_features
    _upsert_ai_features(unique_id, result)

    if stats["updated"] == 0:
        return {"status": "update_failed", "stats": stats}

    # Publish event
    publish_enriched_event(
        unique_id,
        result.get("most_specific_theme_code"),
        bool(result.get("summary")),
    )

    return {"status": "enriched", "stats": stats}


def _upsert_ai_features(unique_id: str, enrichment_result: dict) -> None:
    """Upsert AI-computed features (sentiment, entities) to news_features."""
    from psycopg2.extras import Json

    features = {}
    sentiment = enrichment_result.get("sentiment")
    if sentiment and sentiment.get("label"):
        features["sentiment"] = sentiment
    entities = enrichment_result.get("entities")
    if entities:
        features["entities"] = entities

    if not features:
        return

    db_url = os.environ["DATABASE_URL"]
    conn = psycopg2.connect(db_url)
    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO news_features (unique_id, features)
            VALUES (%s, %s)
            ON CONFLICT (unique_id) DO UPDATE SET
                features = news_features.features || EXCLUDED.features
            """,
            (unique_id, Json(features)),
        )
        conn.commit()
        logger.info(f"Upserted AI features for {unique_id}")
    except Exception as e:
        conn.rollback()
        logger.error(f"Failed to upsert AI features: {e}")
    finally:
        conn.close()
```

## **4.4 BedrockLLMClient (llm_client.py)**

**Componente chave**: Interface com AWS Bedrock via Boto3.

```python
"""
BedrockLLMClient - Interface com AWS Bedrock para enriquecimento.
Suporta batch processing, retry logic e rate limiting.
"""

import boto3
import json
import time
import logging
import random
from typing import Dict, List
from concurrent.futures import ThreadPoolExecutor, as_completed
from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)


class BedrockLLMClient:
    """Cliente para AWS Bedrock com batch processing."""

    def __init__(
        self,
        model_id: str = "anthropic.claude-3-haiku-20240307-v1:0",
        region: str = "us-east-1",
        taxonomy: Dict = None,
        batch_size: int = 8,
        sleep_between_batches: float = 0.2,
        max_retries: int = 3,
        aws_access_key_id: str = None,
        aws_secret_access_key: str = None,
    ):
        """
        Inicializa cliente Bedrock.

        Args:
            model_id: ID do modelo Claude no Bedrock
            region: Região AWS
            taxonomy: Taxonomia predefinida (opcional)
            batch_size: Tamanho do batch para processamento paralelo
            sleep_between_batches: Delay entre batches (rate limiting)
            max_retries: Máximo de tentativas em caso de erro
            aws_access_key_id: Credencial AWS (opcional)
            aws_secret_access_key: Credencial AWS (opcional)
        """
        self.model_id = model_id
        self.region = region
        self.taxonomy = taxonomy
        self.batch_size = batch_size
        self.sleep_between_batches = sleep_between_batches
        self.max_retries = max_retries

        # Criar cliente Bedrock
        client_kwargs = {"region_name": region}
        if aws_access_key_id and aws_secret_access_key:
            client_kwargs["aws_access_key_id"] = aws_access_key_id
            client_kwargs["aws_secret_access_key"] = aws_secret_access_key

        self.client = boto3.client("bedrock-runtime", **client_kwargs)
        logger.info(f"Bedrock client initialized: {model_id} in {region}")

    def enrich_news_batch(self, rows: List[Dict]) -> List[Dict]:
        """
        Enriquece múltiplas notícias em batch usando ThreadPoolExecutor.

        Args:
            rows: Lista de dicionários com dados das notícias

        Returns:
            Lista de dicionários com campos enriquecidos
        """
        results = []

        # Processar em batches
        for i in range(0, len(rows), self.batch_size):
            batch = rows[i : i + self.batch_size]
            batch_num = i // self.batch_size + 1
            logger.info(f"Processing batch {batch_num} ({len(batch)} news)...")

            # Processar batch em paralelo
            with ThreadPoolExecutor(max_workers=self.batch_size) as executor:
                future_to_row = {
                    executor.submit(self._enrich_single_news, row): row
                    for row in batch
                }

                for future in as_completed(future_to_row):
                    row = future_to_row[future]
                    try:
                        enriched = future.result()
                        results.append(enriched)
                    except Exception as e:
                        logger.error(f"Error processing {row.get('unique_id')}: {e}")
                        results.append(self._create_fallback_result(row))

            # Rate limiting entre batches
            if i + self.batch_size < len(rows):
                time.sleep(self.sleep_between_batches)

        return results

    def _enrich_single_news(self, row: Dict) -> Dict:
        """
        Enriquece uma única notícia com retry logic.

        Args:
            row: Dicionário com dados da notícia

        Returns:
            Dicionário com campos enriquecidos
        """
        for attempt in range(self.max_retries):
            try:
                # Construir prompt
                prompt = self._build_prompt(row)

                # Chamar Bedrock
                response = self._call_bedrock(prompt)

                # Parse response
                enriched_data = self._parse_response(response)

                # Combinar com dados originais
                result = {**row, **enriched_data}
                return result

            except ClientError as e:
                error_code = e.response.get("Error", {}).get("Code", "")
                is_throttling = error_code == "ThrottlingException"

                logger.warning(
                    f"Attempt {attempt + 1}/{self.max_retries} failed "
                    f"for {row.get('unique_id')}: {error_code}"
                )

                if attempt < self.max_retries - 1:
                    # Backoff diferenciado para throttling
                    if is_throttling:
                        base_sleep = 1.0 * (2**attempt)  # 1s, 2s, 4s
                        jitter = random.uniform(0, 0.5)
                        sleep_time = base_sleep + jitter
                        logger.info(f"ThrottlingException: waiting {sleep_time:.2f}s")
                    else:
                        sleep_time = 0.2 * (2**attempt)  # 0.2s, 0.4s, 0.8s

                    time.sleep(sleep_time)
                else:
                    logger.error(f"All retries failed for {row.get('unique_id')}")
                    return self._create_fallback_result(row)

        return self._create_fallback_result(row)

    def _build_prompt(self, row: Dict) -> str:
        """
        Constrói prompt estruturado para o LLM.

        Returns:
            String com o prompt completo
        """
        title = row.get("title", "")
        subtitle = row.get("subtitle", "")
        editorial_lead = row.get("editorial_lead", "")
        content = row.get("content", "")

        # Limitar conteúdo para não exceder contexto
        content_preview = content[:2000] if content else ""

        # Construir instruções de taxonomia
        taxonomy_instructions = ""
        if self.taxonomy:
            taxonomy_instructions = f"""
INSTRUÇÕES:
Escolha as categorias da taxonomia abaixo que melhor se adequam à notícia.
Use EXATAMENTE os códigos e labels fornecidos.

TAXONOMIA DISPONÍVEL:
{self._format_taxonomy()}
"""

        prompt = f"""Você é um especialista em classificação temática de notícias governamentais brasileiras.

Analise a notícia abaixo e retorne APENAS um JSON válido (sem markdown, sem explicações).

{taxonomy_instructions}

TAREFAS OBRIGATÓRIAS:
1. Classifique a notícia em 3 níveis hierárquicos (theme_1_level_1/2/3).
2. Gere um campo "summary" com um resumo conciso da notícia em 1-2 frases.
3. Analise o sentimento da notícia (positive, neutral ou negative) e atribua um score entre -1.0 e 1.0.
4. Extraia as entidades mencionadas (organizações, pessoas, locais) com contagem de ocorrências.

NOTÍCIA:
Título: {title}
Subtítulo: {subtitle}
Lead: {editorial_lead}
Conteúdo: {content_preview}

FORMATO DE SAÍDA (JSON VÁLIDO):
{{
  "theme_1_level_1_code": "01",
  "theme_1_level_1_label": "Economia e Finanças",
  "theme_1_level_2_code": "01.02",
  "theme_1_level_2_label": "Fiscalização e Tributação",
  "theme_1_level_3_code": "01.02.03",
  "theme_1_level_3_label": "Reforma Tributária",
  "most_specific_theme_code": "01.02.03",
  "most_specific_theme_label": "Reforma Tributária",
  "summary": "Governo federal anuncia proposta de reforma tributária...",
  "sentiment": {{
    "label": "neutral",
    "score": 0.0
  }},
  "entities": [
    {{"text": "Governo Federal", "type": "ORG", "count": 3}}
  ]
}}"""

        return prompt

    def _format_taxonomy(self) -> str:
        """Formata taxonomia para inclusão no prompt."""
        if not self.taxonomy:
            return ""
        return json.dumps(self.taxonomy, indent=2, ensure_ascii=False)

    def _call_bedrock(self, prompt: str) -> str:
        """
        Realiza chamada ao Bedrock.

        Returns:
            Resposta do modelo (texto)
        """
        request_body = {
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": 1000,
            "temperature": 0.3,
            "messages": [{"role": "user", "content": prompt}],
        }

        response = self.client.invoke_model(
            modelId=self.model_id,
            body=json.dumps(request_body),
        )

        response_body = json.loads(response["body"].read())
        return response_body["content"][0]["text"]

    def _parse_response(self, response: str) -> Dict:
        """
        Parse resposta JSON do LLM.

        Returns:
            Dicionário com campos extraídos
        """
        # Remover markdown se presente
        response = response.strip()
        if response.startswith("```json"):
            response = response[7:]
        if response.startswith("```"):
            response = response[3:]
        if response.endswith("```"):
            response = response[:-3]

        return json.loads(response.strip())

    def _create_fallback_result(self, row: Dict) -> Dict:
        """Cria resultado fallback em caso de erro."""
        return {
            **row,
            "theme_1_level_1_code": None,
            "theme_1_level_1_label": None,
            "theme_1_level_2_code": None,
            "theme_1_level_2_label": None,
            "theme_1_level_3_code": None,
            "theme_1_level_3_label": None,
            "most_specific_theme_code": None,
            "most_specific_theme_label": None,
            "summary": None,
            "sentiment": None,
            "entities": [],
        }
```

---

# **4 Resultados**

## **4.1 Métricas de Produção (Março-Maio 2026)**

### **4.1.1 Performance e Latência**

| Métrica | Valor | Objetivo |
|---------|-------|----------|
| **Latência P50** (scrape → portal) | 8.2s | < 15s ✅ |
| **Latência P95** | 15.1s | < 30s ✅ |
| **Latência P99** | 28.7s | < 60s ✅ |
| **Tempo Bedrock P50** | 3.8s | < 5s ✅ |
| **Tempo Bedrock P95** | 6.2s | < 10s ✅ |
| **Taxa de sucesso** | 99.8% | > 99% ✅ |
| **Taxa de throttling Bedrock** | 0.3% | < 5% ✅ |

### **4.1.2 Qualidade de Classificação**

**Validação manual** (amostra de 110 notícias, março 2026):

| Nível | Acurácia | Critério |
|-------|----------|----------|
| **Nível 1** (10 temas) | 98% | Classificação correta |
| **Nível 2** (~50 subtemas) | 94% | Classificação correta |
| **Nível 3** (~410 temas) | 92% | Classificação correta ou razoável |
| **Summary** | 96% | Resumo coerente e conciso |
| **Sentiment** | 88% | Sentimento correto |

**Distribuição de erros** (nível 3):
- **5%**: Ambiguidade genuína (notícia cabe em 2+ categorias)
- **2%**: Categoria inexistente na taxonomia
- **1%**: Erro de interpretação do LLM

### **4.1.3 Volume Processado**

**Total acumulado** (27/02/2026 - 22/05/2026):
- **Notícias enriquecidas**: 295.431
- **Notícias com classificação L3**: 294.127 (99.6%)
- **Notícias com summary**: 293.845 (99.5%)
- **Média diária**: ~4.100 notícias

**Backlog histórico**:
- **Início** (27/02/2026): 289.000 notícias sem classificação
- **Progresso**: Processado via DAG batch (200/lote, a cada 10min)
- **Conclusão**: 15/04/2026 (48 dias)
- **Atual**: Todas as notícias classificadas, 100% via event-driven

### **4.1.4 Custos Operacionais**

**Breakdown mensal** (baseado em 120.000 notícias/mês):

| Componente | Custo/mês | % Total |
|-----------|-----------|---------|
| **AWS Bedrock** | R$ 288 (~$0.0024/notícia) | 64% |
| **Cloud Run (enrichment-worker)** | R$ 65 | 14% |
| **Cloud Run (outros workers)** | R$ 45 | 10% |
| **Pub/Sub** | R$ 8 | 2% |
| **Cloud SQL (overhead)** | R$ 30 | 7% |
| **GCS Bronze layer** | R$ 14 | 3% |
| **Total** | **R$ 450/mês** | 100% |

**Comparação com arquitetura anterior**:
- **Cogfy API** (descontinuado): R$ 780/mês
- **Economia**: R$ 330/mês (42%)

## **4.2 Distribuição de Classificações por Tema**

**Top 10 temas nível 1** (março-maio 2026):

| Tema | Notícias | % |
|------|----------|---|
| 02 - Política e Governo | 78.432 | 27% |
| 04 - Educação | 52.183 | 18% |
| 03 - Saúde | 47.029 | 16% |
| 05 - Infraestrutura e Desenvolvimento | 38.551 | 13% |
| 01 - Economia e Finanças | 29.543 | 10% |
| 10 - Social e Direitos Humanos | 20.647 | 7% |
| 06 - Segurança e Justiça | 11.805 | 4% |
| 08 - Ciência e Tecnologia | 8.851 | 3% |
| 07 - Meio Ambiente | 5.920 | 2% |
| 09 - Cultura e Esporte | 2.470 | 1% |

**Top 5 temas nível 3 mais frequentes**:

1. **02.01.05 - Políticas Públicas Federais** (24.132 notícias)
2. **04.02.01 - Educação Superior** (18.947 notícias)
3. **03.01.02 - Campanhas de Vacinação** (15.621 notícias)
4. **05.03.01 - Obras de Infraestrutura** (12.034 notícias)
5. **01.02.03 - Reforma Tributária** (9.847 notícias)

## **4.3 Análise de Sentimento**

**Distribuição geral**:
- **Neutral**: 72% (212.410 notícias)
- **Positive**: 23% (67.849 notícias)
- **Negative**: 5% (14.172 notícias)

**Interpretação**:
- Notícias governamentais tendem a ser neutras (informativas)
- Sentimento positivo: anúncios de políticas, inaugurações, conquistas
- Sentimento negativo: denúncias, crises, problemas sociais

## **4.4 Tratamento de Erros e Resiliência**

### **4.4.1 Dead-Letter Queue (DLQ)**

**Mensagens no DLQ** (março-maio 2026):
- **Total**: 47 mensagens
- **Motivo principal**: Timeout Bedrock (32 mensagens, 68%)
- **Motivo secundário**: Conteúdo vazio (11 mensagens, 23%)
- **Outros erros**: 4 mensagens (9%)

**Tratamento**:
- DLQ monitorado via alerta (> 0 mensagens por 15min)
- Mensagens reinjetadas manualmente após investigação
- Taxa de DLQ: 0.016% (47 / 295.431)

### **4.4.2 DAG de Reconciliação**

**DAG `reconcile_unenriched_news`** (diária, meia-noite):
- Busca notícias com `most_specific_theme_id IS NULL AND published_at > NOW() - INTERVAL '2 days'`
- Republica no `dgb.news.scraped` para reprocessamento
- **Média de republicações**: ~12 notícias/dia (0.3%)

**Causas de republicação**:
- Publish Pub/Sub falhou no scraper (rare)
- Worker reiniciou durante processamento (cold start)
- Throttling Bedrock não resolvido com retry

### **4.4.3 Idempotência**

**Garantia de idempotência**:
1. **Enrichment Worker** verifica `most_specific_theme_id IS NOT NULL` antes de processar
2. Se já enriquecido, retorna `{"status": "skipped", "reason": "already_enriched"}`
3. **ACK imediato** para evitar reprocessamento desnecessário

**Testes de idempotência**:
- 100 notícias republicadas 5 vezes cada
- **Resultado**: 100% skipped corretamente, sem duplicação de classificação

---

# **5 Conclusões e Considerações Finais**

## **5.1 Principais Conquistas**

1. **Latência reduzida em 99.7%**: De ~24 horas (batch) para ~8 segundos (event-driven)
2. **Acurácia alta**: 92% de classificação correta no nível 3 (410 categorias)
3. **Custo otimizado**: R$ 450/mês operacional (42% economia vs solução anterior)
4. **Escalabilidade**: Auto-scaling 0-3 instâncias Cloud Run, processa picos de ~8.000 notícias/dia
5. **Resiliência**: 99.8% taxa de sucesso, retry automático, DLQ para erros persistentes
6. **Backlog zerado**: 289k notícias históricas classificadas em 48 dias

## **5.2 Lições Aprendidas**

### **5.2.1 AWS Bedrock (Claude 3 Haiku)**

**Pontos fortes**:
- **Qualidade**: Claude 3 Haiku superou expectativas (92% acurácia)
- **Custo-benefício**: $0.0024/notícia é sustentável para operação contínua
- **Latência**: 3.8s P50 permite processamento near-real-time

**Pontos de atenção**:
- **Throttling**: Ocorreu 0.3% das chamadas mesmo com max 3 instâncias Cloud Run
  - **Mitigação**: Exponential backoff com jitter funcionou bem
- **Variabilidade de output**: ~1% dos JSONs vêm malformados (markdown extra, campos faltando)
  - **Mitigação**: Parser robusto com fallback

### **5.2.2 Arquitetura Event-Driven**

**Benefícios validados**:
- **Desacoplamento**: Workers independentes, fácil adicionar novos consumidores
- **Observabilidade**: Métricas nativas do Pub/Sub (unacked messages, DLQ count)
- **Custo**: Scale-to-zero economiza ~70% vs instâncias sempre ligadas

**Desafios**:
- **Cold start**: 4s de delay na primeira invocação (boto3 + psycopg2 init)
  - **Mitigação**: Min scale = 0 ainda compensa, cold start raro (~5% requests)
- **Debugging**: Traces distribuídos exigem `trace_id` propagado entre workers

### **5.2.3 Taxonomia Hierárquica**

**Acertos**:
- 410 categorias nível 3 cobrem 99.6% das notícias governamentais
- Hierarquia facilita agregações (ex: "todas as notícias de Educação" = nível 1)

**Melhorias futuras**:
- **Taxonomia dinâmica**: Adicionar novas categorias sem redeploy (já suportado, precisa de UI admin)
- **Multi-classificação**: Notícias com 2+ temas principais (atualmente apenas 1 tema)

## **5.3 Próximos Passos**

### **5.3.1 Curto Prazo (Q3 2026)**

1. **Multi-classificação**: Suportar até 3 temas por notícia (muitas notícias são cross-cutting)
2. **Cache de taxonomia**: Redis para evitar query PostgreSQL a cada request
3. **Batch micro-optimization**: Agrupar até 5 notícias em um único prompt Bedrock (reduzir custo 40%)
4. **Dashboard de monitoramento**: Grafana com métricas de latência, custo, acurácia

### **5.3.2 Médio Prazo (Q4 2026)**

1. **Active learning**: Feedback humano (portal admin) para refinar taxonomia
2. **A/B test de modelos**: Comparar Claude 3.5 Sonnet vs Haiku (acurácia vs custo)
3. **Extração de keywords**: Além de temas, extrair palavras-chave para SEO
4. **Trending detection**: Identificar temas emergentes em tempo real

### **5.3.3 Longo Prazo (2027)**

1. **Fine-tuning**: Fine-tune Claude em dataset governamental brasileiro (~300k notícias)
2. **Classificação multimodal**: Processar imagens/vídeos das notícias
3. **Ontologia completa**: Migrar de taxonomia hierárquica para ontologia OWL (inferência de relações)

## **5.4 Impacto no DestaquesGovBr**

**Portal Web**:
- **Filtros por tema**: Usuários navegam por categoria (ex: "Saúde > Vacinação")
- **Busca aprimorada**: Typesense usa `most_specific_theme_id` para ranking
- **Recomendações**: Motor usa temas para sugerir notícias relacionadas

**Dados Abertos (HuggingFace)**:
- **Dataset enriquecido**: 295k notícias com `theme_l1/l2/l3 + summary` disponível em [nitaibezerra/govbrnews](https://huggingface.co/datasets/nitaibezerra/govbrnews)
- **Pesquisadores**: Usam dataset para análise de políticas públicas, NLP em português

**Insights para MGI**:
- **Agregações por tema**: Quantas notícias por categoria por mês/ano
- **Trending topics**: Quais temas estão em alta no governo federal
- **Análise de sentimento**: Percepção pública de políticas

---

# **6 Referências Bibliográficas**

1. **AWS Bedrock Documentation** - Amazon Web Services  
   [https://docs.aws.amazon.com/bedrock/](https://docs.aws.amazon.com/bedrock/)

2. **Anthropic Claude 3 Model Card** - Anthropic  
   [https://www.anthropic.com/claude/haiku](https://www.anthropic.com/claude/haiku)

3. **Google Cloud Pub/Sub Documentation** - Google Cloud  
   [https://cloud.google.com/pubsub/docs](https://cloud.google.com/pubsub/docs)

4. **Cloud Run Documentation** - Google Cloud  
   [https://cloud.google.com/run/docs](https://cloud.google.com/run/docs)

5. **Event-Driven Architecture Pattern** - Martin Fowler  
   [https://martinfowler.com/articles/201701-event-driven.html](https://martinfowler.com/articles/201701-event-driven.html)

6. **DestaquesGovBr Data Platform Repository** - GitHub  
   [https://github.com/destaquesgovbr/data-platform](https://github.com/destaquesgovbr/data-platform)

7. **DestaquesGovBr Data Science Repository** - GitHub  
   [https://github.com/destaquesgovbr/data-science](https://github.com/destaquesgovbr/data-science) (privado)

8. **DestaquesGovBr Dataset (HuggingFace)** - Nitai Bezerra  
   [https://huggingface.co/datasets/nitaibezerra/govbrnews](https://huggingface.co/datasets/nitaibezerra/govbrnews)

9. **Large Language Models for Classification Tasks** - arXiv:2312.00849  
   Brown et al. (2023)

10. **Medallion Architecture (Data Engineering)** - Databricks  
    [https://www.databricks.com/glossary/medallion-architecture](https://www.databricks.com/glossary/medallion-architecture)

---

# **Apêndice**

## **A. Prompt Completo Enviado ao Claude 3 Haiku**

```
Você é um especialista em classificação temática de notícias governamentais brasileiras.

Analise a notícia abaixo e retorne APENAS um JSON válido (sem markdown, sem explicações).

INSTRUÇÕES:
Escolha as categorias da taxonomia abaixo que melhor se adequam à notícia.
Use EXATAMENTE os códigos e labels fornecidos.

TAXONOMIA DISPONÍVEL:

01 - Economia e Finanças
  01.01 - Políticas Econômicas
    01.01.01 - PIB e Crescimento
    01.01.02 - Inflação e Preços
  01.02 - Fiscalização e Tributação
    01.02.01 - Imposto de Renda
    01.02.02 - ICMS e Impostos Estaduais
    01.02.03 - Reforma Tributária
    01.02.04 - Fiscalização da Receita Federal
  [... 406 categorias adicionais ...]

TAREFAS OBRIGATÓRIAS:
1. Classifique a notícia em 3 níveis hierárquicos (theme_1_level_1/2/3).
2. Gere um campo "summary" com um resumo conciso da notícia em 1-2 frases.
3. Analise o sentimento da notícia (positive, neutral ou negative) e atribua um score entre -1.0 e 1.0.
4. Extraia as entidades mencionadas (organizações, pessoas, locais) com contagem de ocorrências.

NOTÍCIA:
Título: Governo anuncia reforma tributária que simplifica impostos
Subtítulo: Medida visa reduzir burocracia e carga sobre empresas
Lead: O governo federal apresentou hoje uma proposta de reforma tributária que unifica cinco impostos em um único tributo sobre consumo.
Conteúdo: A reforma tributária proposta pelo governo federal prevê a criação de um Imposto sobre Valor Agregado (IVA) dual, substituindo PIS, Cofins, IPI, ICMS e ISS. Segundo o Ministério da Fazenda, a medida deve reduzir a complexidade do sistema tributário brasileiro e diminuir custos de conformidade para as empresas. A proposta será enviada ao Congresso Nacional na próxima semana...

FORMATO DE SAÍDA (JSON VÁLIDO):
{
  "theme_1_level_1_code": "01",
  "theme_1_level_1_label": "Economia e Finanças",
  "theme_1_level_2_code": "01.02",
  "theme_1_level_2_label": "Fiscalização e Tributação",
  "theme_1_level_3_code": "01.02.03",
  "theme_1_level_3_label": "Reforma Tributária",
  "most_specific_theme_code": "01.02.03",
  "most_specific_theme_label": "Reforma Tributária",
  "summary": "Governo federal anuncia proposta de reforma tributária com criação de IVA dual, unificando cinco impostos e reduzindo complexidade do sistema.",
  "sentiment": {
    "label": "positive",
    "score": 0.6
  },
  "entities": [
    {"text": "Governo Federal", "type": "ORG", "count": 2},
    {"text": "Ministério da Fazenda", "type": "ORG", "count": 1},
    {"text": "Congresso Nacional", "type": "ORG", "count": 1}
  ]
}
```

## **B. Exemplo de Resposta do Claude 3 Haiku**

```json
{
  "theme_1_level_1_code": "01",
  "theme_1_level_1_label": "Economia e Finanças",
  "theme_1_level_2_code": "01.02",
  "theme_1_level_2_label": "Fiscalização e Tributação",
  "theme_1_level_3_code": "01.02.03",
  "theme_1_level_3_label": "Reforma Tributária",
  "most_specific_theme_code": "01.02.03",
  "most_specific_theme_label": "Reforma Tributária",
  "summary": "Governo federal apresenta proposta de reforma tributária que cria IVA dual, substituindo cinco impostos e simplificando sistema para empresas.",
  "sentiment": {
    "label": "positive",
    "score": 0.7
  },
  "entities": [
    {
      "text": "Governo Federal",
      "type": "ORG",
      "count": 2
    },
    {
      "text": "Ministério da Fazenda",
      "type": "ORG",
      "count": 1
    },
    {
      "text": "Congresso Nacional",
      "type": "ORG",
      "count": 1
    },
    {
      "text": "Brasil",
      "type": "LOC",
      "count": 1
    }
  ]
}
```

## **C. Schema PostgreSQL - Tabelas Relevantes**

```sql
-- Tabela de temas hierárquicos
CREATE TABLE themes (
    id SERIAL PRIMARY KEY,
    code VARCHAR(20) UNIQUE NOT NULL,
    label VARCHAR(255) NOT NULL,
    level INT NOT NULL CHECK (level IN (1, 2, 3)),
    parent_id INT REFERENCES themes(id),
    description TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_themes_code ON themes(code);
CREATE INDEX idx_themes_level ON themes(level);
CREATE INDEX idx_themes_parent ON themes(parent_id);

-- Tabela de notícias (campos relevantes)
ALTER TABLE news 
ADD COLUMN theme_l1_id INT REFERENCES themes(id),
ADD COLUMN theme_l2_id INT REFERENCES themes(id),
ADD COLUMN theme_l3_id INT REFERENCES themes(id),
ADD COLUMN most_specific_theme_id INT REFERENCES themes(id),
ADD COLUMN summary TEXT,
ADD COLUMN updated_at TIMESTAMP DEFAULT NOW();

CREATE INDEX idx_news_theme_l1 ON news(theme_l1_id);
CREATE INDEX idx_news_theme_l2 ON news(theme_l2_id);
CREATE INDEX idx_news_theme_l3 ON news(theme_l3_id);
CREATE INDEX idx_news_most_specific_theme ON news(most_specific_theme_id);

-- Tabela de features (sentiment, entities)
CREATE TABLE news_features (
    unique_id VARCHAR(255) PRIMARY KEY REFERENCES news(unique_id) ON DELETE CASCADE,
    features JSONB NOT NULL DEFAULT '{}',
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_news_features_sentiment ON news_features USING GIN ((features->'sentiment'));
CREATE INDEX idx_news_features_entities ON news_features USING GIN ((features->'entities'));
```

## **D. Métricas de Observabilidade**

**Dashboards Grafana**:

1. **Pipeline Health**
   - Mensagens/segundo por topic (scraped, enriched, embedded)
   - Latência P50/P95/P99 scrape → portal
   - Taxa de sucesso por worker

2. **Bedrock Monitoring**
   - Requests/segundo
   - Latência P50/P95/P99
   - Taxa de throttling (ThrottlingException)
   - Custo acumulado (estimado)

3. **DLQ & Errors**
   - Mensagens no DLQ por topic
   - Taxa de erro por worker
   - Alertas ativos

**Alertas configurados** (Cloud Monitoring):

| Alerta | Condição | Severidade |
|--------|----------|-----------|
| DLQ não vazio | `dgb.news.scraped-dlq` > 0 por 15min | P2 |
| High unacked messages | `undelivered_messages` > 1000 por 30min | P2 |
| Worker error rate | Error rate > 5% por 10min | P1 |
| Bedrock throttling | Throttle rate > 10% por 15min | P2 |
| High latency | P95 latency > 10min por 20min | P3 |

## **E. Configuração Terraform - Enrichment Worker**

```hcl
# enrichment-worker.tf

resource "google_cloud_run_service" "enrichment_worker" {
  name     = "enrichment-worker"
  location = var.region

  template {
    spec {
      service_account_name = google_service_account.enrichment_worker.email
      
      containers {
        image = "gcr.io/${var.project_id}/enrichment-worker:latest"
        
        resources {
          limits = {
            cpu    = "1000m"
            memory = "1Gi"
          }
        }
        
        env {
          name = "DATABASE_URL"
          value_from {
            secret_key_ref {
              name = google_secret_manager_secret.postgres_url.secret_id
              key  = "latest"
            }
          }
        }
        
        env {
          name = "AWS_ACCESS_KEY_ID"
          value_from {
            secret_key_ref {
              name = google_secret_manager_secret.aws_access_key.secret_id
              key  = "latest"
            }
          }
        }
        
        env {
          name = "AWS_SECRET_ACCESS_KEY"
          value_from {
            secret_key_ref {
              name = google_secret_manager_secret.aws_secret_key.secret_id
              key  = "latest"
            }
          }
        }
        
        env {
          name  = "AWS_REGION"
          value = "us-east-1"
        }
        
        env {
          name  = "BEDROCK_MODEL_ID"
          value = "anthropic.claude-3-haiku-20240307-v1:0"
        }
        
        env {
          name  = "PUBSUB_TOPIC_NEWS_ENRICHED"
          value = google_pubsub_topic.news_enriched.id
        }
      }
    }
    
    metadata {
      annotations = {
        "autoscaling.knative.dev/minScale"   = "0"
        "autoscaling.knative.dev/maxScale"   = "3"
        "autoscaling.knative.dev/target"     = "10"
        "run.googleapis.com/cpu-throttling"  = "false"
      }
    }
  }
  
  traffic {
    percent         = 100
    latest_revision = true
  }
}

# Service Account
resource "google_service_account" "enrichment_worker" {
  account_id   = "enrichment-worker"
  display_name = "Enrichment Worker Service Account"
}

# IAM: pubsub.publisher (publish enriched events)
resource "google_pubsub_topic_iam_member" "enrichment_worker_publisher" {
  topic  = google_pubsub_topic.news_enriched.name
  role   = "roles/pubsub.publisher"
  member = "serviceAccount:${google_service_account.enrichment_worker.email}"
}

# IAM: secretmanager.secretAccessor (read secrets)
resource "google_secret_manager_secret_iam_member" "enrichment_worker_secrets" {
  for_each = toset([
    google_secret_manager_secret.postgres_url.secret_id,
    google_secret_manager_secret.aws_access_key.secret_id,
    google_secret_manager_secret.aws_secret_key.secret_id,
  ])
  
  secret_id = each.value
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${google_service_account.enrichment_worker.email}"
}

# IAM: cloudsql.client (connect to Cloud SQL)
resource "google_project_iam_member" "enrichment_worker_sql" {
  project = var.project_id
  role    = "roles/cloudsql.client"
  member  = "serviceAccount:${google_service_account.enrichment_worker.email}"
}

# Pub/Sub push subscription
resource "google_pubsub_subscription" "enrichment_worker_sub" {
  name  = "dgb.news.scraped--enrichment"
  topic = google_pubsub_topic.news_scraped.name
  
  ack_deadline_seconds = 600
  
  push_config {
    push_endpoint = "${google_cloud_run_service.enrichment_worker.status[0].url}/process"
    
    oidc_token {
      service_account_email = google_service_account.enrichment_worker.email
    }
  }
  
  retry_policy {
    minimum_backoff = "10s"
    maximum_backoff = "600s"
  }
  
  dead_letter_policy {
    dead_letter_topic     = google_pubsub_topic.news_scraped_dlq.id
    max_delivery_attempts = 10
  }
}
```

## **F. Terminologias e Abreviações**

### Arquitetura e Infraestrutura

| Termo | Significado |
|-------|-------------|
| **API** | Application Programming Interface - Interface de Programação de Aplicações |
| **CDN** | Content Delivery Network - Rede de Distribuição de Conteúdo |
| **CI/CD** | Continuous Integration/Continuous Delivery - Integração Contínua/Entrega Contínua |
| **Cloud Run** | Serviço serverless do Google Cloud para executar containers |
| **Cloud SQL** | Serviço de banco de dados gerenciado do Google Cloud |
| **DAG** | Directed Acyclic Graph - Grafo Acíclico Direcionado (usado no Airflow) |
| **DLQ** | Dead-Letter Queue - Fila de mensagens que falharam após múltiplas tentativas |
| **Event-Driven** | Arquitetura orientada a eventos |
| **FastAPI** | Framework web moderno para Python |
| **GCP** | Google Cloud Platform |
| **GCS** | Google Cloud Storage - Armazenamento de objetos do Google Cloud |
| **IAM** | Identity and Access Management - Gerenciamento de Identidade e Acesso |
| **Pub/Sub** | Google Cloud Pub/Sub - Serviço de mensageria assíncrona |
| **SA** | Service Account - Conta de Serviço |
| **SDK** | Software Development Kit - Kit de Desenvolvimento de Software |
| **Serverless** | Arquitetura sem gerenciamento de servidores |
| **VPC** | Virtual Private Cloud - Nuvem Privada Virtual |

### Banco de Dados e Armazenamento

| Termo | Significado |
|-------|-------------|
| **CRUD** | Create, Read, Update, Delete - Operações básicas de banco de dados |
| **JSONB** | JSON Binary - Formato binário otimizado para armazenar JSON no PostgreSQL |
| **ORM** | Object-Relational Mapping - Mapeamento Objeto-Relacional |
| **pgvector** | Extensão PostgreSQL para armazenar e buscar vetores (embeddings) |
| **PostgreSQL** | Sistema de gerenciamento de banco de dados relacional open-source |
| **SQL** | Structured Query Language - Linguagem de Consulta Estruturada |
| **Schema** | Estrutura que define a organização dos dados em um banco |

### Machine Learning e IA

| Termo | Significado |
|-------|-------------|
| **AWS Bedrock** | Serviço AWS para acesso a modelos de IA via API |
| **Batch Processing** | Processamento em lote (múltiplos itens de uma vez) |
| **Claude** | Família de modelos de linguagem da Anthropic |
| **Embedding** | Representação vetorial de texto (768 dimensões) |
| **Haiku** | Modelo Claude mais rápido e econômico (vs Sonnet/Opus) |
| **LLM** | Large Language Model - Modelo de Linguagem de Grande Escala |
| **NLP** | Natural Language Processing - Processamento de Linguagem Natural |
| **Prompt** | Instrução/contexto enviado ao modelo de IA |
| **Temperature** | Parâmetro que controla aleatoriedade do LLM (0-1) |
| **Token** | Unidade básica de texto processada por LLMs (~4 caracteres) |
| **Sentiment Analysis** | Análise de sentimento (positivo/negativo/neutro) |
| **Named Entity Recognition (NER)** | Extração de entidades nomeadas (pessoas, organizações, locais) |

### Data Pipeline e ETL

| Termo | Significado |
|-------|-------------|
| **Airflow** | Plataforma de orquestração de workflows (Apache Airflow) |
| **Backlog** | Conjunto de trabalho pendente de processamento |
| **Bronze Layer** | Camada de dados brutos (Medallion Architecture) |
| **ETL** | Extract, Transform, Load - Extração, Transformação e Carga |
| **Gold Layer** | Camada de dados analíticos (Medallion Architecture) |
| **Idempotência** | Propriedade de operação que pode ser executada múltiplas vezes sem efeito colateral |
| **Medallion Architecture** | Padrão de arquitetura de dados em 3 camadas (Bronze/Silver/Gold) |
| **Reconciliation** | Processo de sincronização para corrigir inconsistências |
| **Silver Layer** | Camada de dados limpos e normalizados (Medallion Architecture) |
| **Worker** | Serviço que processa mensagens de forma assíncrona |

### Métricas e Observabilidade

| Termo | Significação |
|-------|-------------|
| **Ack/Nack** | Acknowledge/Negative Acknowledge - Confirmação positiva/negativa de recebimento |
| **Ack Deadline** | Tempo máximo para processar mensagem antes de retry |
| **Backoff** | Estratégia de aumentar delay entre tentativas (exponential backoff) |
| **Latência** | Tempo de resposta de uma operação |
| **P50/P95/P99** | Percentil 50/95/99 - Valor abaixo do qual X% das medições estão |
| **Retry** | Tentativa de reprocessar operação que falhou |
| **Throttling** | Limitação de taxa de requisições (rate limiting) |
| **Trace ID** | Identificador único para rastrear operação através de múltiplos serviços |

### Classificação e Taxonomia

| Termo | Significado |
|-------|-------------|
| **Acurácia** | Taxa de classificações corretas |
| **Categoria** | Tema ou classe na taxonomia |
| **Código Temático** | Identificador único do tema (ex: "01.02.03") |
| **Hierarquia** | Estrutura de níveis pai-filho na taxonomia |
| **Label** | Rótulo descritivo de uma categoria |
| **Nível** | Profundidade na hierarquia (L1/L2/L3) |
| **Taxonomia** | Sistema hierárquico de classificação |
| **Tema** | Assunto ou tópico principal |

### Formatos e Protocolos

| Termo | Significado |
|-------|-------------|
| **Base64** | Codificação de dados binários em texto ASCII |
| **HTTP** | Hypertext Transfer Protocol - Protocolo de Transferência de Hipertexto |
| **JSON** | JavaScript Object Notation - Formato de dados estruturados |
| **REST** | Representational State Transfer - Estilo arquitetural para APIs |
| **UTF-8** | Codificação de caracteres Unicode |
| **YAML** | Yet Another Markup Language - Linguagem de serialização de dados |

### Métricas de Negócio

| Termo | Significado |
|-------|-------------|
| **Enriquecimento** | Adição de metadados (temas, resumo, sentimento) às notícias |
| **Gov.br** | Domínio oficial do governo brasileiro |
| **MGI** | Ministério da Gestão e da Inovação em Serviços Públicos |
| **Portal** | Site web (destaques.gov.br) |
| **Scraping** | Coleta automatizada de dados de websites |
| **Unique ID** | Identificador único da notícia (formato: agency-YYYY-MM-DD-slug) |

### Siglas de Órgãos e Instituições

| Sigla | Nome Completo |
|-------|---------------|
| **CPQD** | Centro de Pesquisa e Desenvolvimento em Telecomunicações |
| **EBC** | Empresa Brasil de Comunicação |
| **Finep** | Financiadora de Estudos e Projetos |
| **INSPIRE** | Projeto de inovação em serviços públicos (MGI/Finep) |
| **LGPD** | Lei Geral de Proteção de Dados |
| **MEC** | Ministério da Educação |
| **MGI** | Ministério da Gestão e da Inovação em Serviços Públicos |

### Termos Técnicos Específicos

| Termo | Significado |
|-------|-------------|
| **Boto3** | SDK Python oficial da AWS |
| **Cold Start** | Delay inicial ao iniciar instância serverless |
| **Composer** | Google Cloud Composer - Airflow gerenciado |
| **Conflict** | Conflito de chave única no banco (INSERT já existe) |
| **docxcompose** | Biblioteca Python para merge de arquivos DOCX |
| **Graceful Degradation** | Continuar funcionando parcialmente mesmo com falhas |
| **HuggingFace** | Plataforma para compartilhamento de modelos e datasets de ML |
| **Pandoc** | Conversor universal de formatos de documento |
| **Parquet** | Formato colunar eficiente para armazenamento de dados |
| **Poetry** | Gerenciador de dependências Python |
| **psycopg2** | Driver PostgreSQL para Python |
| **Pygments** | Biblioteca Python para syntax highlighting |
| **SQLAlchemy** | ORM (Object-Relational Mapper) para Python |
| **Terraform** | Ferramenta de Infrastructure as Code (IaC) |
| **ThreadPoolExecutor** | Executor de tarefas paralelas em Python |
| **Typesense** | Motor de busca open-source (full-text + semântica) |
| **Workload Identity** | Método seguro para autenticação entre GCP e GitHub Actions |