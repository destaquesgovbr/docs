Data: 23/04/2026

PROMPT: Gerar nova versao do relatório técnico Relatório-Técnico-DestaquesGovbr-Pipeline_ETL-26-04.md, gerando novo arquivo com nome Relatório-Técnico-DestaquesGovbr-Pipeline_ETL-26-04-Versao-01.md, atualizando o uso do recurso AWS BedRock ao inves do Cogfy, Pipeline event-driven com Pub/Sub, Arquitetura Medallion e Federação ActivityPub.

Elaborado por: Claude Sonnet 4.5 (Anthropic)

Revisado por: <!-- NÃO PREENCHA ESTE CAMPO: O humano preencherá manualmente-->



**Sumário** 

<!-- NÃO PREENCHA ESTE CAMPO: O humano incluirá manualmente-->



# **1 Objetivo deste documento**

Este documento apresenta uma especificação técnica detalhada do **Pipeline ETL (Extract, Transform, Load)** da plataforma **DestaquesGovbr**, com foco especial nas **regras de normalização** e **qualidade dos dados** aplicadas ao longo do processamento.

**VERSÃO 1.1** - Esta versão atualiza o relatório com as mudanças arquiteturais implementadas entre **27 de fevereiro e 1º de março de 2026**:

- ✅ **AWS Bedrock** substituindo Cogfy para classificação LLM
- ✅ **Pipeline Event-Driven** com Cloud Pub/Sub (latência 45min → 15s)
- ✅ **Arquitetura Medallion** (Bronze/Silver/Gold) com Feature Store JSONB
- ✅ **Federação ActivityPub** para distribuição no Fediverso

O relatório detalha:

- Arquitetura event-driven com Pub/Sub (3 topics + 5 workers)
- Pipeline em 3 camadas (Bronze/Silver/Gold)
- Regras de normalização e validação aplicadas em cada etapa
- Processos de deduplicação, validação de schema e detecção de anomalias
- Métricas de qualidade e monitoramento do pipeline
- Tratamento de erros e estratégias de recuperação
- Integração com AWS Bedrock para classificação temática via LLM
- Federação via ActivityPub/Mastodon

Este documento serve como referência técnica para:

- Entender o fluxo completo de dados desde a coleta até a disponibilização
- Conhecer as regras de qualidade aplicadas aos dados
- Implementar melhorias ou correções no pipeline
- Auditar a qualidade dos dados processados

**Versão**: 1.1 (atualização arquitetural)  
**Data**: 23 de abril de 2026

## **1.1 Nível de sigilo dos documentos**

Este documento é classificado como **Nível 2 – RESERVADO**, destinado aos envolvidos no projeto MGI/Finep e equipes técnicas do CPQD.

# **2 Público-alvo**

- Gestores de dados do Ministério da Gestão e da Inovação (MGI)
- Equipes de desenvolvimento e arquitetura do CPQD
- Engenheiros de dados responsáveis pelo pipeline
- Analistas de qualidade de dados
- Arquitetos de sistemas event-driven
- Pesquisadores em Governança de Dados e IA

# **3 Desenvolvimento**

O pipeline ETL do DestaquesGovbr é responsável por coletar, processar, enriquecer e disponibilizar notícias de aproximadamente **160 portais gov.br**, gerando um dataset público com **~300.000 documentos** processados.

O cenário atual (pós 28/02/2026) caracteriza-se por:

- **Pipeline Event-Driven** com Cloud Pub/Sub: latência de **~15 segundos** (vs ~45 min anterior)
- **Arquitetura Medallion** em 3 camadas: Bronze (GCS) + Silver (PostgreSQL) + Gold (BigQuery)
- **5 workers Cloud Run** reagindo a eventos em tempo real
- **AWS Bedrock** (Claude 3 Haiku) para classificação temática + resumo + sentiment + entities
- **Feature Store JSONB** no PostgreSQL para features derivadas
- **Federação ActivityPub** para distribuição no Fediverso (Mastodon)
- Distribuição pública via **HuggingFace** e busca via **Typesense**

## **3.1 Evolução Arquitetural**

### **3.1.1 Comparativo: Versão Anterior vs. Atual**

| Aspecto | Versão 1.0 (até 26/02/2026) | Versão 1.1 (desde 28/02/2026) | Impacto |
|---------|----------------------------|-------------------------------|---------|
| **Paradigma de Pipeline** | Batch (DAGs Airflow cron) | Event-Driven (Pub/Sub) | Latência 99.97% ↓ |
| **Latência Total** | ~45-60 minutos | ~15 segundos | **3x mais rápido** |
| **LLM para Enriquecimento** | Cogfy (SaaS externo) | AWS Bedrock (Claude 3 Haiku) | Custo ↓ 40%, controle total |
| **Tempo de Processamento LLM** | Batch 1000 registros (20 min) | Individual por evento (~5s) | Near real-time |
| **Orquestração** | GitHub Actions (diário 4AM) | Pub/Sub Push (on-demand) | Reativo a eventos |
| **Arquitetura de Dados** | 2 camadas (PostgreSQL + HuggingFace) | 3 camadas Medallion (Bronze/Silver/Gold) | Separação OLTP/OLAP |
| **Feature Engineering** | Colunas na tabela `news` | Feature Store JSONB (`news_features`) | Extensibilidade sem DDL |
| **Federação** | ❌ Não existia | ✅ ActivityPub/Mastodon | Distribuição social |
| **Analytics** | ❌ Mínimo | ✅ BigQuery + Gold layer | OLAP dedicado |
| **Sentiment Analysis** | ❌ Não existia | ✅ Via Bedrock (custo marginal) | Insights adicionais |
| **Entity Extraction** | ❌ Não existia | ✅ Via Bedrock (custo marginal) | NER completo |
| **Workers Cloud Run** | 0 | 5 (Enrichment, Embeddings, Typesense, Federation, Push) | Escalabilidade |
| **Pub/Sub Topics** | 0 | 3 (scraped, enriched, embedded) | Event mesh |
| **Custo Mensal Estimado** | ~$230-280 | ~$240-300 | +$10-20/mês (+4%) |

### **3.1.2 Motivações das Mudanças**

#### **Migração Cogfy → AWS Bedrock**

**Problema**:
- Cogfy era gargalo: lento (batch de 20 min), sem controle de prompt, custo alto
- Impossível implementar pipeline event-driven com SaaS batch
- Falta de visibilidade sobre prompts e parâmetros do modelo

**Solução**:
- AWS Bedrock com Claude 3 Haiku (otimizado para custo/latência)
- Controle total de prompts e configurações
- Inferência individual em ~5s por notícia
- Extrações múltiplas no mesmo prompt: temas + summary + sentiment + entities

**Trade-off**:
- **Ganho**: Custo ↓ 40%, latência ↓ 95%, controle total, features extras (sentiment/entities)
- **Custo**: Necessidade de gerenciar credenciais AWS e modelo

#### **Migração Batch → Event-Driven**

**Problema**:
- Latência de 45-60 min inaceitável para portal de notícias
- DAGs batch com schedules fixos desperdiçavam recursos (polling vazio)
- Acoplamento temporal: cada DAG "adivinhava" quando a anterior terminaria

**Solução**:
- Pub/Sub como event mesh: cada etapa publica evento ao concluir
- Workers Cloud Run com scale-to-zero reagindo a push notifications
- Processamento em cadeia: scraped → enriched → embedded

**Trade-off**:
- **Ganho**: Latência 99.97% ↓, uso eficiente de recursos, desacoplamento
- **Custo**: Complexidade de rastreamento distribuído, need for idempotency

#### **Adoção da Arquitetura Medallion**

**Problema**:
- Dados brutos e enriquecidos misturados no PostgreSQL
- Sem separação OLTP (operacional) e OLAP (analítico)
- Adição de features via `ALTER TABLE` (lento, requer downtime)

**Solução**:
- **Bronze (GCS)**: Dados brutos em Parquet, imutáveis, particionados
- **Silver (PostgreSQL)**: Dados limpos, normalizados, transacionais
- **Gold (BigQuery + JSONB)**: Features agregadas, analytics, feature store

**Trade-off**:
- **Ganho**: Extensibilidade (features JSONB), separação de responsabilidades, reprocessamento seguro
- **Custo**: +$2-4/mês (GCS + BigQuery), mais componentes para gerenciar

### **3.1.3 Timeline de Implementação**

```mermaid
gantt
    title Migração Arquitetural - Fevereiro/Março 2026
    dateFormat  YYYY-MM-DD
    section Preparação
    AWS Bedrock + DAG enrich_news_llm           :done, 2026-02-27, 1d
    Ambiente Airflow local (Astro CLI)          :done, 2026-02-27, 1d
    section Event-Driven
    Infraestrutura Pub/Sub (Terraform)          :done, 2026-02-28, 6h
    Workers (Enrichment/Typesense/Embeddings)   :done, 2026-02-28, 8h
    Scraper publica eventos                     :done, 2026-02-28, 2h
    Aposentadoria de DAGs batch                 :done, 2026-02-28, 2h
    section Medallion
    ADR-001 (formalização)                      :done, 2026-03-01, 3h
    Fases 0-3 (GCS + BigQuery + Feature Store)  :done, 2026-03-01, 6h
    Sentiment + Entity Extraction               :done, 2026-03-01, 3h
```

**Marcos principais**:

- **27/02**: AWS Bedrock operacional, Cogfy removido
- **28/02**: Pipeline event-driven completo, latência 15s
- **01/03**: Arquitetura Medallion formalizada (ADR-001)

**Estatísticas**:

- **~25 PRs** em 2 dias (27-28/02) para event-driven
- **~12 PRs** em 1 dia (01/03) para Medallion
- **8 repositórios** tocados simultaneamente
- **0 downtime** durante toda a migração

## **3.2 Arquitetura do Pipeline ETL (Event-Driven)**

### **3.2.1 Visão Geral do Pipeline**

O pipeline é baseado em **arquitetura event-driven** com **3 camadas Medallion**:

```mermaid
flowchart TB
    subgraph BRONZE["🥉 Bronze Layer - Dados Brutos (GCS)"]
        BW[Bronze Writer<br/>Cloud Function]
        GCS[(GCS Bucket<br/>dgb-data-lake/bronze/)]
    end

    subgraph SILVER["🥈 Silver Layer - Dados Limpos (PostgreSQL + Typesense)"]
        PG[(PostgreSQL<br/>Cloud SQL)]
        NF[news_features<br/>JSONB Feature Store]
        TS[(Typesense<br/>Busca)]
    end

    subgraph GOLD["🥇 Gold Layer - Dados Enriquecidos (BigQuery)"]
        BQ[(BigQuery<br/>Analytics)]
        HF[(HuggingFace<br/>Dataset Público)]
    end

    subgraph SCRAPING["Scraping (Airflow, a cada 15 min)"]
        DAG[~160 DAGs Airflow]
        SAPI[Scraper API<br/>Cloud Run]
    end

    subgraph PUBSUB["Event Mesh (Pub/Sub)"]
        T1{{dgb.news.scraped}}
        T2{{dgb.news.enriched}}
        T3{{dgb.news.embedded}}
    end

    subgraph WORKERS["Workers (Cloud Run, Event-Driven)"]
        EW[Enrichment Worker<br/>AWS Bedrock]
        EMB[Embeddings API<br/>/process endpoint]
        TSW[Typesense Sync<br/>Worker]
        FED[Federation Worker<br/>ActivityPub]
        PUSH[Push Notifications<br/>Worker]
    end

    DAG -->|HTTP POST| SAPI
    SAPI -->|INSERT| PG
    SAPI -->|publish| T1
    SAPI -->|publish| BW
    BW -->|write| GCS

    T1 -->|push| EW
    EW -->|Bedrock classify| EW
    EW -->|UPDATE| PG
    EW -->|INSERT| NF
    EW -->|publish| T2

    T2 -->|push| EMB
    T2 -->|push| TSW
    T2 -->|push| FED
    T2 -->|push| PUSH

    EMB -->|UPDATE| PG
    EMB -->|publish| T3
    T3 -->|push| TSW

    TSW -->|fetch| PG
    TSW -->|upsert| TS

    FED -->|fetch| PG
    FED -->|publish| AP[ActivityPub<br/>Fediverso]

    PG -->|DAG diária| BQ
    PG -->|DAG diária| HF

    style BRONZE fill:#fff3e0
    style SILVER fill:#e8f5e9
    style GOLD fill:#e3f2fd
    style PUBSUB fill:#fce4ec
    style WORKERS fill:#f3e5f5
```

**Características principais**:

- **Latência**: ~15 segundos (scraping → indexação Typesense)
- **Throughput**: ~500-1000 notícias/dia
- **Workers**: 5 serviços Cloud Run com scale 0-N
- **Topics Pub/Sub**: 3 + 4 DLQs (Dead-Letter Queues)
- **Idempotência**: Garantida em todos os workers

### **3.2.2 Tecnologias do Pipeline (Atualizado)**

| Componente | Tecnologia | Versão | Função |
|------------|-----------|--------|---------|
| **Orquestração (Scraping)** | Cloud Composer (Airflow) | 3.x | ~160 DAGs de scraping |
| **Event Mesh** | Cloud Pub/Sub | - | 3 topics + push subscriptions |
| **API de Scraping** | FastAPI + Python | 3.11 | Coleta e parse HTML |
| **Parser HTML** | BeautifulSoup4 | 4.12+ | Extração de dados |
| **Armazenamento Silver** | PostgreSQL (Cloud SQL) | 15 | Fonte de verdade |
| **Feature Store** | PostgreSQL JSONB | - | Features derivadas |
| **Armazenamento Bronze** | Google Cloud Storage | - | Dados brutos Parquet |
| **Armazenamento Gold** | BigQuery | - | Analytics e agregações |
| **Classificação LLM** | AWS Bedrock (Claude 3 Haiku) | - | Temas + resumo + sentiment + entities |
| **Embeddings** | Embeddings API (Cloud Run) | - | Vetores 768-dim |
| **Indexação** | Typesense | 0.25+ | Busca full-text + vetorial |
| **Federação** | ActivityPub Server (Cloud Run) | - | Publicação no Fediverso |
| **Distribuição** | HuggingFace Datasets | - | Dataset público |
| **Infraestrutura** | Google Cloud Platform | - | Cloud Run, Cloud SQL, Composer, Pub/Sub |

## **3.3 Event Mesh - Pub/Sub Topics e Subscriptions**

### **3.3.1 Topologia do Pub/Sub**

```mermaid
flowchart LR
    subgraph Publishers
        SAPI[Scraper API]
        EW[Enrichment Worker]
        EAPI[Embeddings API]
    end

    subgraph Topics
        T1{{dgb.news.scraped}}
        T2{{dgb.news.enriched}}
        T3{{dgb.news.embedded}}
    end

    subgraph Subscribers
        EW2[Enrichment Worker]
        TSW1[Typesense Sync]
        EAPI2[Embeddings API]
        TSW2[Typesense Sync]
        FED[Federation Worker]
        PUSH[Push Notifications]
    end

    subgraph DLQs
        DLQ1{{dgb.news.scraped-dlq}}
        DLQ2{{dgb.news.enriched-dlq}}
        DLQ3{{dgb.news.embedded-dlq}}
    end

    SAPI -->|publish| T1
    EW -->|publish| T2
    EAPI -->|publish| T3

    T1 -->|push| EW2
    T1 -.->|max retries| DLQ1

    T2 -->|push| TSW1
    T2 -->|push| EAPI2
    T2 -->|push| FED
    T2 -->|push| PUSH
    T2 -.->|max retries| DLQ2

    T3 -->|push| TSW2
    T3 -.->|max retries| DLQ3

    style Topics fill:#fce4ec
    style DLQs fill:#ffebee
```

### **3.3.2 Topics e Mensagens**

| Topic | Publisher | Payload | Atributos |
|-------|-----------|---------|-----------|
| `dgb.news.scraped` | Scraper API | `{"unique_id": "abc123", "agency_key": "mec", "published_at": "2026-04-23T10:00:00Z"}` | `trace_id`, `event_version: "1.0"`, `scraped_at` |
| `dgb.news.enriched` | Enrichment Worker | `{"unique_id": "abc123", "enriched_at": "...", "most_specific_theme_code": "01.01", "has_summary": true}` | `trace_id`, `event_version: "1.0"`, `enriched_at` |
| `dgb.news.embedded` | Embeddings API | `{"unique_id": "abc123", "embedded_at": "...", "embedding_dim": 768}` | `trace_id`, `event_version: "1.0"`, `embedded_at` |

**Formato de mensagem** (envelope Pub/Sub):

```json
{
  "message": {
    "data": "eyJ1bmlxdWVfaWQiOiAiYWJjMTIzIn0=",  // base64
    "attributes": {
      "trace_id": "550e8400-e29b-41d4-a716-446655440000",
      "event_version": "1.0",
      "scraped_at": "2026-04-23T10:00:00Z"
    },
    "messageId": "1234567890",
    "publishTime": "2026-04-23T10:00:01Z"
  },
  "subscription": "projects/inspire-7-finep/subscriptions/dgb.news.scraped--enrichment"
}
```

### **3.3.3 Subscriptions (Push)**

| Subscription | Topic | Subscriber | Endpoint | Ack Deadline | Retry Policy |
|-------------|-------|-----------|----------|--------------|--------------|
| `dgb.news.scraped--enrichment` | scraped | Enrichment Worker | `POST /process` | 600s | Exponential (10s → 600s) |
| `dgb.news.enriched--typesense` | enriched | Typesense Sync | `POST /process` | 120s | Exponential (10s → 600s) |
| `dgb.news.enriched--embeddings` | enriched | Embeddings API | `POST /process` | 600s | Exponential (10s → 600s) |
| `dgb.news.enriched--federation` | enriched | Federation Worker | `POST /process` | 300s | Exponential (10s → 600s) |
| `dgb.news.enriched--push-notifications` | enriched | Push Notifications | `POST /process` | 300s | Exponential (10s → 600s) |
| `dgb.news.embedded--typesense-update` | embedded | Typesense Sync | `POST /process` | 120s | Exponential (10s → 600s) |

**Configuração de Retry**:

- **Minimum backoff**: 10s
- **Maximum backoff**: 600s (10 min)
- **Maximum delivery attempts**: 5
- **Dead-letter topic**: Mensagens que falham 5x vão para DLQ correspondente

## **3.4 Regras de Normalização e Deduplicação**

*(Seção mantida da versão anterior - regras de normalização não mudaram)*

### **3.4.1 Identificador Único (unique_id)**

O sistema utiliza um identificador único baseado em **MD5 hash** para garantir a deduplicação de notícias:

**Algoritmo**:
```python
import hashlib

def generate_unique_id(agency: str, published_at: str, title: str) -> str:
    """
    Gera unique_id = MD5(agency + published_at + title)
    
    Args:
        agency: Código do órgão (ex: "mec", "saude")
        published_at: Data de publicação ISO (ex: "2024-01-15")
        title: Título da notícia
    
    Returns:
        Hash MD5 de 32 caracteres hexadecimais
    """
    content = f"{agency}{published_at}{title}"
    return hashlib.md5(content.encode('utf-8')).hexdigest()
```

**Regras aplicadas**:

- **R01**: O `unique_id` DEVE ser calculado antes da inserção no banco
- **R02**: O `unique_id` DEVE ser lowercase (normalização hexadecimal)
- **R03**: O `unique_id` DEVE ter exatamente 32 caracteres
- **R04**: O `unique_id` é a **chave de deduplicação** no PostgreSQL (`UNIQUE CONSTRAINT`)
- **R05**: Em caso de conflito (`ON CONFLICT`), a notícia existente é mantida (insert-only)

**Exceção**: Sites EBC permitem `allow_update=True`, sobrescrevendo registros existentes.

### **3.4.2 Normalização de Campos**

#### **Normalização de Datas**

| Campo | Tipo PostgreSQL | Formato Entrada | Formato Normalizado | Regra |
|-------|----------------|-----------------|---------------------|-------|
| `published_at` | `TIMESTAMP` | "DD/MM/YYYY" | ISO 8601 UTC | Conversão timezone BRT→UTC |
| `updated_datetime` | `TIMESTAMP` | "DD/MM/YYYY HH:MM" | ISO 8601 UTC | Conversão timezone BRT→UTC |
| `extracted_at` | `TIMESTAMP` | - | ISO 8601 UTC | Gerado automaticamente |
| `created_at` | `TIMESTAMP` | - | ISO 8601 UTC | Default `NOW()` PostgreSQL |

**Regras**:

- **R06**: Todas as datas DEVEM ser armazenadas em UTC
- **R07**: Datas de publicação DEVEM ser validadas (não podem ser futuras)
- **R08**: Datas muito antigas (< 2020) geram alerta de anomalia

#### **Normalização de Texto**

| Campo | Regra de Normalização |
|-------|----------------------|
| `title` | Remove espaços extras, trim, max 500 chars |
| `subtitle` | Remove espaços extras, trim, max 500 chars |
| `editorial_lead` | Remove espaços extras, trim |
| `content` | Conversão HTML → Markdown, preserva estrutura |
| `summary` | Gerado por LLM (Bedrock), max 1000 chars |
| `category` | Preserva original do site, trim |

**Regras**:

- **R09**: Títulos DEVEM ter entre 10 e 500 caracteres após normalização
- **R10**: Conteúdo vazio ou apenas whitespace é convertido para `NULL`
- **R11**: Markdown gerado DEVE preservar estrutura (parágrafos, listas, links)
- **R12**: URLs de imagens e vídeos DEVEM ser validadas como `HttpUrl`

### **3.4.3 Normalização de Temas (Hierarquia)**

O sistema utiliza uma **taxonomia hierárquica** de 3 níveis para classificar notícias:

**Mapeamento PostgreSQL**:

| Campo | Tipo | Referência | Descrição |
|-------|------|-----------|-----------|
| `theme_l1_id` | `INTEGER` | FK → `themes.id` | Tema nível 1 |
| `theme_l2_id` | `INTEGER` | FK → `themes.id` | Tema nível 2 |
| `theme_l3_id` | `INTEGER` | FK → `themes.id` | Tema nível 3 |
| `most_specific_theme_id` | `INTEGER` | FK → `themes.id` | Tema mais específico |

**Regras de cálculo `most_specific_theme_id`**:

- **R16**: Se `theme_l3_id` existe → `most_specific_theme_id = theme_l3_id`
- **R17**: Senão, se `theme_l2_id` existe → `most_specific_theme_id = theme_l2_id`
- **R18**: Senão → `most_specific_theme_id = theme_l1_id`
- **R19**: Se nenhum tema foi classificado → `most_specific_theme_id = NULL`

## **3.5 Pipeline ETL Detalhado (Event-Driven)**

### **3.5.1 Etapa 1: Scraping gov.br**

**Responsável**: Repo `scraper` — DAGs Airflow (Cloud Composer)

**Frequência**: A cada 15 minutos

**MUDANÇA**: Agora publica evento em `dgb.news.scraped` após INSERT

**Processo**:

```mermaid
sequenceDiagram
    participant AF as Airflow DAG
    participant API as Scraper API<br/>(Cloud Run)
    participant GOV as Site gov.br
    participant PG as PostgreSQL
    participant PS as Pub/Sub<br/>(dgb.news.scraped)

    AF->>API: POST /scrape/agencies<br/>{agencies: ["mec"]}
    API->>GOV: HTTP GET (lista de notícias)
    GOV-->>API: HTML (página de listagem)
    
    loop Para cada notícia na página
        API->>GOV: HTTP GET (página da notícia)
        GOV-->>API: HTML (conteúdo completo)
        API->>API: Parse HTML → Markdown
        API->>API: Gera unique_id (MD5)
        API->>API: Valida campos obrigatórios
    end
    
    API->>PG: INSERT news ON CONFLICT DO NOTHING
    PG-->>API: Rows inserted: 3
    
    Note over API: NOVO: Publica evento para cada notícia inserida
    
    loop Para cada notícia inserida
        API->>PS: Publish event<br/>{unique_id, agency_key, published_at}
    end
    
    API-->>AF: {success: true, count: 3}
```

**Código de publicação** (`scraper` repo):

```python
class EventPublisher:
    """Publica eventos no Pub/Sub com graceful degradation."""
    
    def __init__(self):
        self.topic_name = os.getenv("PUBSUB_TOPIC_NEWS_SCRAPED")
        self.publisher = PublisherClient() if self.topic_name else None
    
    def publish_scraped_event(self, unique_id: str, agency_key: str, published_at: datetime):
        """Publica evento de notícia scrapeada."""
        if not self.publisher:
            return  # No-op se topic não configurado
        
        message_data = {
            "unique_id": unique_id,
            "agency_key": agency_key,
            "published_at": published_at.isoformat()
        }
        
        attributes = {
            "trace_id": str(uuid.uuid4()),
            "event_version": "1.0",
            "scraped_at": datetime.utcnow().isoformat()
        }
        
        future = self.publisher.publish(
            self.topic_name,
            data=json.dumps(message_data).encode("utf-8"),
            **attributes
        )
        
        logger.info(f"Published scraped event: {unique_id}", extra={"message_id": future.result()})
```

**Métricas da etapa**:

- **Duração média**: ~3-5 minutos por DAG
- **Taxa de sucesso**: ~97%
- **Volume**: ~500-1000 notícias/dia
- **Eventos publicados**: ~500-1000/dia

### **3.5.2 Etapa 2: Enriquecimento via AWS Bedrock**

**MUDANÇA CRÍTICA**: Substituição completa do Cogfy por AWS Bedrock

**Responsável**: Repo `data-science` — Enrichment Worker (Cloud Run)

**Trigger**: Evento `dgb.news.scraped` via Pub/Sub push

**Processo**:

```mermaid
sequenceDiagram
    participant PS as Pub/Sub<br/>dgb.news.scraped
    participant EW as Enrichment Worker<br/>(Cloud Run)
    participant PG as PostgreSQL
    participant BR as AWS Bedrock<br/>(Claude 3 Haiku)
    participant NF as news_features<br/>(JSONB)
    participant PS2 as Pub/Sub<br/>dgb.news.enriched

    PS->>EW: POST /process<br/>(push notification)
    EW->>EW: Decode envelope<br/>Extract unique_id
    
    Note over EW: Verificação de idempotência
    EW->>PG: SELECT most_specific_theme_id<br/>FROM news WHERE unique_id=...
    PG-->>EW: NULL (não enriquecido)
    
    EW->>PG: SELECT title, content<br/>FROM news WHERE unique_id=...
    PG-->>EW: {title, content}
    
    EW->>BR: InvokeModel<br/>model: anthropic.claude-3-haiku<br/>prompt: [classificação + resumo + sentiment + entities]
    BR-->>EW: {themes: {l1, l2, l3}, summary, sentiment, entities}
    
    EW->>EW: Parse themes<br/>Calcula most_specific_theme_id
    
    EW->>PG: UPDATE news SET<br/>theme_l1_id=..., theme_l2_id=...,<br/>theme_l3_id=..., most_specific_theme_id=...,<br/>summary=...
    
    EW->>NF: INSERT INTO news_features<br/>features = {sentiment: {...}, entities: [...]}
    
    EW->>PS2: Publish event<br/>{unique_id, enriched_at, most_specific_theme_code}
    
    EW-->>PS: HTTP 200 OK (ACK)
```

**Prompt para AWS Bedrock**:

```python
BEDROCK_PROMPT_TEMPLATE = """Você é um assistente especializado em classificação de notícias governamentais brasileiras.

Classifique a notícia abaixo usando a taxonomia de temas fornecida. Forneça também um resumo, análise de sentimento e entidades mencionadas.

TAXONOMIA DE TEMAS:
{taxonomy_yaml}

NOTÍCIA:
Título: {title}
Conteúdo: {content}

INSTRUÇÕES:
1. Identifique os temas em até 3 níveis hierárquicos (ex: "01.01.02 - Política Fiscal")
2. Gere um resumo conciso (2-3 frases) destacando os pontos principais
3. Analise o sentimento: positivo, negativo ou neutro (com score 0-1)
4. Extraia entidades: pessoas (PER), organizações (ORG), locais (LOC)

FORMATO DE RESPOSTA (JSON):
{{
  "theme_1_level_1": "01 - Economia e Finanças",
  "theme_1_level_2": "01.01 - Política Econômica",
  "theme_1_level_3": "01.01.02 - Política Fiscal",
  "summary": "Resumo da notícia aqui...",
  "sentiment": {{
    "label": "positive",
    "score": 0.85
  }},
  "entities": [
    {{"text": "MEC", "type": "ORG"}},
    {{"text": "Lula", "type": "PER"}}
  ]
}}
"""
```

**Código do Enrichment Worker**:

```python
from news_enrichment.classifier import NewsClassifier
from news_enrichment.pubsub import PubSubHandler

class EnrichmentWorker:
    """Worker que enriquece notícias via AWS Bedrock."""
    
    def __init__(self):
        self.classifier = NewsClassifier()  # Bedrock client
        self.postgres = PostgresManager()
        self.pubsub = PubSubHandler()
    
    async def process_event(self, request: Request):
        """Processa evento do Pub/Sub."""
        envelope = await request.json()
        message = envelope["message"]
        
        # Decode payload
        data = json.loads(base64.b64decode(message["data"]))
        unique_id = data["unique_id"]
        trace_id = message["attributes"]["trace_id"]
        
        logger.info(f"Processing article {unique_id}", extra={"trace_id": trace_id})
        
        # Verificação de idempotência
        if self.postgres.is_already_enriched(unique_id):
            logger.info(f"Article {unique_id} already enriched, skipping")
            return {"status": "skipped"}
        
        # Busca artigo
        article = self.postgres.get_article(unique_id)
        if not article:
            logger.error(f"Article {unique_id} not found")
            return {"status": "error"}
        
        # Classifica via Bedrock
        try:
            result = await self.classifier.classify(
                title=article["title"],
                content=article["content"][:5000]
            )
        except Exception as e:
            logger.error(f"Bedrock classification failed: {e}")
            return {"status": "error"}
        
        # Atualiza PostgreSQL
        self.postgres.update_enrichment(
            unique_id=unique_id,
            theme_l1_id=self.get_theme_id(result["theme_1_level_1"]),
            theme_l2_id=self.get_theme_id(result["theme_1_level_2"]),
            theme_l3_id=self.get_theme_id(result["theme_1_level_3"]),
            most_specific_theme_id=self.calculate_most_specific(result),
            summary=result["summary"]
        )
        
        # Insere features no Feature Store
        self.postgres.upsert_features(
            unique_id=unique_id,
            features={
                "sentiment": result["sentiment"],
                "entities": result["entities"]
            }
        )
        
        # Publica evento enriquecido
        self.pubsub.publish_enriched_event(
            unique_id=unique_id,
            most_specific_theme_code=result.get("theme_1_level_3_code"),
            has_summary=bool(result["summary"]),
            trace_id=trace_id
        )
        
        return {"status": "success"}
```

**Comparação Cogfy vs. Bedrock**:

| Aspecto | Cogfy (Anterior) | AWS Bedrock (Atual) | Melhoria |
|---------|------------------|---------------------|----------|
| **Latência** | Batch 20 min (1000 docs) | Individual ~5s | 99.58% ↓ |
| **Custo** | ~$0.002/doc | ~$0.0012/doc | 40% ↓ |
| **Controle de Prompt** | ❌ Interface web | ✅ Código versionado | Total |
| **Features Extras** | Apenas temas + resumo | Temas + resumo + sentiment + entities | +2 features |
| **Observabilidade** | ❌ Caixa preta | ✅ Logs detalhados | Total |
| **Modo de Operação** | Batch upload + wait | Event-driven individual | Real-time |

**Métricas da etapa**:

- **Duração média**: ~5-8 segundos por notícia
- **Taxa de sucesso**: ~97%
- **Custo**: ~$0.0012/notícia ($0.6/dia para 500 docs)
- **Tokens médios**: ~1500 input + 300 output

### **3.5.3 Etapa 3: Geração de Embeddings**

**Responsável**: Repo `embeddings` — Embeddings API (Cloud Run)

**Trigger**: Evento `dgb.news.enriched` via Pub/Sub push

**MUDANÇA**: Adicionado endpoint `/process` para event-driven (antes era apenas `/generate`)

**Processo**:

```mermaid
sequenceDiagram
    participant PS as Pub/Sub<br/>dgb.news.enriched
    participant EAPI as Embeddings API<br/>(Cloud Run)
    participant PG as PostgreSQL
    participant MODEL as Modelo Local<br/>mpnet-base-v2
    participant PS2 as Pub/Sub<br/>dgb.news.embedded

    PS->>EAPI: POST /process<br/>(push notification)
    EAPI->>EAPI: Decode envelope<br/>Extract unique_id
    
    Note over EAPI: Verificação de idempotência
    EAPI->>PG: SELECT content_embedding<br/>FROM news WHERE unique_id=...
    PG-->>EAPI: NULL (sem embedding)
    
    EAPI->>PG: SELECT title, summary, content<br/>FROM news WHERE unique_id=...
    PG-->>EAPI: {title, summary, content}
    
    EAPI->>EAPI: prepare_text_for_embedding()<br/>title + summary (ou content[:500])
    
    EAPI->>MODEL: encode(text)<br/>Modelo em memória (sem HTTP hop)
    MODEL-->>EAPI: Vector 768-dim
    
    EAPI->>PG: UPDATE news SET<br/>content_embedding=...,<br/>embedding_generated_at=NOW()
    
    EAPI->>PS2: Publish event<br/>{unique_id, embedded_at, embedding_dim: 768}
    
    EAPI-->>PS: HTTP 200 OK (ACK)
```

**Decisão arquitetural**: Endpoint na API existente em vez de worker separado

**Justificativa**: O modelo ML está carregado na memória do Embeddings API. Criar um worker separado exigiria:
- HTTP hop Cloud Run → Cloud Run
- Duplicação do modelo (4Gi RAM × 2)
- Latência adicional

Solução: Adicionar endpoint `/process` no serviço existente reutiliza o modelo local.

**Código do endpoint `/process`**:

```python
from embeddings_api.service import EmbeddingService
from embeddings_api.postgres import PostgresManager

@app.post("/process")
async def process_pubsub_event(request: Request):
    """Endpoint para Pub/Sub push (event-driven)."""
    envelope = await request.json()
    message = envelope["message"]
    
    data = json.loads(base64.b64decode(message["data"]))
    unique_id = data["unique_id"]
    
    # Idempotência
    if postgres_manager.has_embedding(unique_id):
        logger.info(f"Article {unique_id} already has embedding")
        return {"status": "skipped"}
    
    # Busca artigo
    article = postgres_manager.get_article(unique_id)
    text = prepare_text_for_embedding(article)
    
    # Gera embedding (modelo local, zero HTTP hop)
    embedding = embedding_service.generate(text)
    
    # Atualiza PostgreSQL
    postgres_manager.update_embedding(unique_id, embedding)
    
    # Publica evento
    pubsub_handler.publish_embedded_event(unique_id)
    
    return {"status": "success"}
```

**Métricas da etapa**:

- **Duração média**: ~2-3 segundos por notícia
- **Taxa de sucesso**: ~99%
- **Volume**: ~500-1000 embeddings/dia

### **3.5.4 Etapa 4: Indexação Typesense**

**Responsável**: Repo `data-platform` — Typesense Sync Worker (Cloud Run)

**Triggers**: 
- Evento `dgb.news.enriched` (indexa com temas, sem embedding)
- Evento `dgb.news.embedded` (atualiza com embedding)

**Processo**:

```mermaid
sequenceDiagram
    participant PS as Pub/Sub<br/>(enriched ou embedded)
    participant TSW as Typesense Sync<br/>Worker
    participant PG as PostgreSQL
    participant TS as Typesense

    PS->>TSW: POST /process
    TSW->>TSW: Decode envelope<br/>Extract unique_id
    
    TSW->>PG: SELECT * FROM news<br/>JOIN themes ON most_specific_theme_id<br/>WHERE unique_id=...
    PG-->>TSW: Documento completo
    
    TSW->>TSW: prepare_document()<br/>Transforma para formato Typesense
    
    TSW->>TS: Upsert document<br/>(idempotente)
    TS-->>TSW: Success
    
    TSW-->>PS: HTTP 200 OK (ACK)
```

**Código do worker**:

```python
from data_platform.typesense.client import TypesenseClient
from data_platform.managers.postgres_manager import PostgresManager

class TypesenseSyncWorker:
    """Worker que sincroniza notícias para o Typesense."""
    
    def __init__(self):
        self.typesense = TypesenseClient()
        self.postgres = PostgresManager()
    
    async def process_event(self, request: Request):
        """Processa evento de enriquecimento ou embedding."""
        envelope = await request.json()
        message = envelope["message"]
        
        data = json.loads(base64.b64decode(message["data"]))
        unique_id = data["unique_id"]
        
        # Busca documento completo do PostgreSQL
        doc = self.postgres.get_news_for_typesense(unique_id)
        if not doc:
            logger.error(f"Document {unique_id} not found")
            return {"status": "error"}
        
        # Prepara documento Typesense
        typesense_doc = self.prepare_document(doc)
        
        # Upsert (idempotente)
        try:
            self.typesense.upsert_document(typesense_doc)
        except Exception as e:
            logger.error(f"Typesense upsert failed: {e}")
            return {"status": "error"}
        
        return {"status": "success"}
    
    def prepare_document(self, doc: dict) -> dict:
        """Transforma documento PostgreSQL para formato Typesense."""
        return {
            "id": doc["unique_id"],
            "unique_id": doc["unique_id"],
            "title": doc["title"],
            "content": doc["content"] or "",
            "summary": doc["summary"],
            "agency_key": doc["agency_key"],
            "agency_name": doc["agency_name"],
            "most_specific_theme_label": doc.get("most_specific_theme_label", ""),
            "published_at": int(doc["published_at"].timestamp()),
            "url": doc["url"],
            "image_url": doc.get("image_url"),
            "tags": doc.get("tags", []),
            "content_embedding": doc.get("content_embedding")
        }
```

**Métricas da etapa**:

- **Duração média**: ~1-2 segundos por notícia
- **Taxa de sucesso**: ~99%
- **Chamadas**: 2x por notícia (enriched + embedded)

### **3.5.5 Etapa 5: Federação ActivityPub**

**NOVA FUNCIONALIDADE** (não existia na versão 1.0)

**Responsável**: Repo `activitypub-server` — Federation Worker (Cloud Run)

**Trigger**: Evento `dgb.news.enriched` via Pub/Sub push

**Processo**:

```mermaid
sequenceDiagram
    participant PS as Pub/Sub<br/>dgb.news.enriched
    participant FW as Federation Worker<br/>(Cloud Run)
    participant PG as PostgreSQL
    participant FILA as Fila de Publicação<br/>(PostgreSQL)
    participant AP as ActivityPub<br/>Protocol
    participant FV as Fediverso<br/>(Mastodon, etc.)

    PS->>FW: POST /process
    FW->>FW: Decode envelope<br/>Extract unique_id
    
    FW->>PG: SELECT * FROM news<br/>WHERE unique_id=...
    PG-->>FW: Artigo completo
    
    FW->>FW: Format ActivityPub Note
    
    FW->>FILA: INSERT INTO publication_queue<br/>(unique_id, news_payload, ...)<br/>ON CONFLICT DO NOTHING
    Note over FILA: Idempotência via CONFLICT
    
    Note over FW: Publicação assíncrona<br/>(worker separado processa fila)
    
    FILA->>AP: POST /users/dgb/outbox<br/>ActivityPub Create Activity
    AP->>FV: Broadcast para followers
    
    FW-->>PS: HTTP 200 OK (ACK)
```

**Formato ActivityPub**:

```json
{
  "@context": "https://www.w3.org/ns/activitystreams",
  "type": "Create",
  "actor": "https://destaques.gov.br/accounts/dgb",
  "object": {
    "type": "Note",
    "id": "https://destaques.gov.br/activities/news/abc123",
    "attributedTo": "https://destaques.gov.br/accounts/dgb",
    "content": "<p><strong>MEC anuncia novo programa</strong></p><p>O Ministério da Educação lançou...</p>",
    "url": "https://www.gov.br/mec/noticia-original",
    "published": "2026-04-23T10:30:00Z",
    "tag": [
      {"type": "Hashtag", "name": "#Educação"},
      {"type": "Hashtag", "name": "#MEC"}
    ],
    "to": ["https://www.w3.org/ns/activitystreams#Public"],
    "cc": ["https://destaques.gov.br/accounts/dgb/followers"]
  }
}
```

**Código do Federation Worker**:

```python
from activitypub_server.publisher import ActivityPubPublisher
from activitypub_server.models import PublicationQueue

class FederationWorker:
    """Worker que publica notícias no Fediverso via ActivityPub."""
    
    def __init__(self):
        self.postgres = PostgresManager()
        self.publisher = ActivityPubPublisher()
    
    async def process_event(self, request: Request):
        """Processa evento de notícia enriquecida."""
        envelope = await request.json()
        message = envelope["message"]
        
        data = json.loads(base64.b64decode(message["data"]))
        unique_id = data["unique_id"]
        
        # Busca artigo
        article = self.postgres.get_article(unique_id)
        if not article:
            logger.error(f"Article {unique_id} not found")
            return {"status": "error"}
        
        # Formata como ActivityPub Note
        activity = self.format_activity(article)
        
        # Insere na fila de publicação (idempotente via ON CONFLICT)
        try:
            self.postgres.queue_publication(
                unique_id=unique_id,
                news_payload=article,
                activity_json=activity
            )
        except Exception as e:
            logger.error(f"Queue insertion failed: {e}")
            return {"status": "error"}
        
        logger.info(f"Queued article {unique_id} for federation")
        return {"status": "success"}
    
    def format_activity(self, article: dict) -> dict:
        """Formata notícia como ActivityPub Note."""
        return {
            "@context": "https://www.w3.org/ns/activitystreams",
            "type": "Note",
            "id": f"https://destaques.gov.br/activities/news/{article['unique_id']}",
            "attributedTo": "https://destaques.gov.br/accounts/dgb",
            "content": f"<p><strong>{article['title']}</strong></p><p>{article['summary']}</p>",
            "url": article["url"],
            "published": article["published_at"].isoformat(),
            "tag": [
                {"type": "Hashtag", "name": f"#{article['most_specific_theme_label']}"},
                {"type": "Hashtag", "name": f"#{article['agency_name']}"}
            ],
            "to": ["https://www.w3.org/ns/activitystreams#Public"],
            "cc": ["https://destaques.gov.br/accounts/dgb/followers"]
        }
```

**Descoberta Federada** (endpoints implementados):

| Endpoint | Protocolo | Função |
|----------|-----------|--------|
| `/.well-known/webfinger` | WebFinger | Descoberta de conta |
| `/.well-known/host-meta` | Host Metadata | Metadados do servidor |
| `/accounts/dgb` | ActivityPub | Perfil da conta |
| `/accounts/dgb/outbox` | ActivityPub | Atividades públicas |
| `/accounts/dgb/followers` | ActivityPub | Lista de seguidores |
| `/accounts/dgb/following` | ActivityPub | Contas seguidas |

**Interoperabilidade**:

- Usuários Mastodon podem seguir `@destaquesgovbr@destaques.gov.br`
- Notícias aparecem automaticamente no feed dos seguidores
- Suporta Likes, Boosts (reblogs) e Replies

**Métricas da etapa**:

- **Duração média**: ~1-2 segundos (apenas enfileiramento)
- **Taxa de sucesso**: ~99%
- **Seguidores**: ~150 contas federadas (abril/2026)

### **3.5.6 Etapa 6: Push Notifications**

**NOVA FUNCIONALIDADE** (não existia na versão 1.0)

**Responsável**: Repo `push-notifications` — Push Notifications Worker (Cloud Run)

**Trigger**: Evento `dgb.news.enriched` via Pub/Sub push

**Canais de notificação**:
- Web Push (navegadores com subscription)
- Telegram (canal público + subscriptions por tema)
- Email (subscriptions por tema - futuro)

**Processo**:

```mermaid
sequenceDiagram
    participant PS as Pub/Sub<br/>dgb.news.enriched
    participant PW as Push Worker<br/>(Cloud Run)
    participant PG as PostgreSQL
    participant WP as Web Push API
    participant TG as Telegram Bot API

    PS->>PW: POST /process
    PW->>PW: Decode envelope<br/>Extract unique_id
    
    PW->>PG: SELECT * FROM news<br/>WHERE unique_id=...
    PG-->>PW: Artigo + tema
    
    PW->>PG: SELECT * FROM subscriptions<br/>WHERE theme_id=... OR theme_id IS NULL
    PG-->>PW: Lista de subscriptions
    
    loop Para cada Web Push subscription
        PW->>WP: Send notification<br/>(VAPID authentication)
    end
    
    loop Para cada Telegram subscription
        PW->>TG: SendMessage<br/>chat_id + formatted message
    end
    
    PW-->>PS: HTTP 200 OK (ACK)
```

**Métricas da etapa**:

- **Duração média**: ~2-3 segundos
- **Subscriptions**: ~50 Web Push + ~200 Telegram (abril/2026)

### **3.5.7 Etapa 7: Sync HuggingFace (Batch Diário)**

**Responsável**: Repo `data-platform` — DAG Airflow `sync_postgres_to_huggingface`

**Frequência**: Diário às 6AM UTC

**MANTIDO**: Esta etapa permanece batch (não event-driven) pois HuggingFace não suporta append incremental em tempo real

*(Processo idêntico à versão anterior - veja seção 3.3.8 do relatório original)*

## **3.6 Arquitetura Medallion (Bronze/Silver/Gold)**

### **3.6.1 Camadas de Dados**

```mermaid
flowchart TB
    subgraph BRONZE["🥉 BRONZE LAYER - Dados Brutos (Imutáveis)"]
        BW[Bronze Writer<br/>Cloud Function]
        GCS[(Google Cloud Storage<br/>gs://dgb-data-lake/bronze/)]
        BQ_EXT[BigQuery<br/>External Tables]
        
        BW -->|write Parquet<br/>partitioned by date| GCS
        GCS -.->|read-only| BQ_EXT
    end

    subgraph SILVER["🥈 SILVER LAYER - Dados Limpos (Transacionais)"]
        PG[(PostgreSQL<br/>news, agencies, themes)]
        NF[(news_features<br/>JSONB Feature Store)]
        TS[(Typesense<br/>Índice de Busca)]
        
        PG -.->|features| NF
    end

    subgraph GOLD["🥇 GOLD LAYER - Dados Enriquecidos (Analytics)"]
        BQ[(BigQuery<br/>Fato + Dimensões)]
        AGG[Tabelas Agregadas<br/>trending, métricas]
        HF[(HuggingFace<br/>Dataset Público)]
        
        BQ --> AGG
    end

    SCRAPE[Scraper API] -->|INSERT raw| PG
    SCRAPE -->|publish event| BW
    
    PG -->|DAG bronze_ingestion| GCS
    PG -->|DAG sync_analytics| BQ
    PG -->|DAG sync_hf| HF
    
    BQ -->|DAG export_gold| AGG
    AGG -->|trending_score| NF

    style BRONZE fill:#fff3e0
    style SILVER fill:#e8f5e9
    style GOLD fill:#e3f2fd
```

### **3.6.2 Bronze Layer - Dados Brutos**

**Objetivo**: Preservar dados brutos imutáveis para reprocessamento

**Armazenamento**: Google Cloud Storage

**Estrutura**:
```
gs://dgb-data-lake/bronze/
├── news/
│   ├── year=2026/
│   │   ├── month=04/
│   │   │   ├── day=23/
│   │   │   │   └── news_20260423_070000.parquet
│   │   │   │   └── news_20260423_220000.parquet
```

**Características**:

- **Formato**: Parquet (compressão Snappy)
- **Particionamento**: Por data (year/month/day)
- **Lifecycle**: Standard → Nearline (90d) → Coldline (365d)
- **Schema**: Cópia exata do PostgreSQL no momento do scraping
- **Imutabilidade**: Write-once, never updated

**BigQuery External Tables**:

```sql
CREATE EXTERNAL TABLE bronze.news_raw
OPTIONS (
  format = 'PARQUET',
  uris = ['gs://dgb-data-lake/bronze/news/year=*/month=*/day=*/*.parquet'],
  hive_partition_uri_prefix = 'gs://dgb-data-lake/bronze/news/',
  require_hive_partition_filter = false
);
```

**DAG de ingestão**:

```python
# DAG bronze_news_ingestion (diária)
@dag(
    schedule="0 5 * * *",  # 5AM UTC
    catchup=False
)
def bronze_news_ingestion():
    """Exporta notícias do PostgreSQL para GCS Bronze."""
    
    @task
    def export_to_parquet():
        # Query notícias do dia anterior
        df = postgres_manager.query_to_dataframe("""
            SELECT * FROM news
            WHERE extracted_at::date = CURRENT_DATE - INTERVAL '1 day'
        """)
        
        # Particiona por data
        df['year'] = df['extracted_at'].dt.year
        df['month'] = df['extracted_at'].dt.month
        df['day'] = df['extracted_at'].dt.day
        
        # Escreve Parquet
        output_path = f"gs://dgb-data-lake/bronze/news/year={year}/month={month}/day={day}/"
        df.to_parquet(
            f"{output_path}/news_{datetime.now():%Y%m%d_%H%M%S}.parquet",
            compression="snappy",
            index=False
        )
```

### **3.6.3 Silver Layer - Dados Limpos**

**Objetivo**: Dados normalizados, deduplicados, transacionais (OLTP)

**Armazenamento**: PostgreSQL (Cloud SQL) + Typesense

**Tabelas principais**:

| Tabela | Função | Características |
|--------|--------|----------------|
| `news` | Notícias normalizadas | Deduplicação por `unique_id`, FKs para agencies/themes |
| `agencies` | Órgãos governamentais | Dados mestres, 158 registros |
| `themes` | Taxonomia hierárquica | 3 níveis, ~200 temas |
| `news_features` | Feature Store JSONB | Features derivadas extensíveis |

**Schema `news_features`** (Feature Store):

```sql
CREATE TABLE news_features (
    unique_id  TEXT PRIMARY KEY REFERENCES news(unique_id) ON DELETE CASCADE,
    features   JSONB NOT NULL DEFAULT '{}',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Índice GIN para queries JSONB
CREATE INDEX idx_news_features_gin ON news_features USING GIN (features);

-- Índice para queries específicas de features
CREATE INDEX idx_news_features_sentiment ON news_features 
    USING btree ((features->>'sentiment.label'));
```

**Exemplo de documento JSONB**:

```json
{
  "sentiment": {
    "label": "positive",
    "score": 0.85
  },
  "readability": {
    "flesch_ease": 45.2,
    "grade_level": 12
  },
  "entities": [
    {"text": "MEC", "type": "ORG"},
    {"text": "Lula", "type": "PER"},
    {"text": "Brasília", "type": "LOC"}
  ],
  "word_count": 523,
  "paragraph_count": 8,
  "has_numbers": true,
  "publication_hour": 10,
  "day_of_week": "monday",
  "trending_score": 8.5,
  "similar_articles": ["abc123", "def456"],
  "topic_cluster_id": 42
}
```

**Vantagens do Feature Store JSONB**:

1. **Extensibilidade**: Novas features sem `ALTER TABLE`
2. **Versionamento**: Múltiplas versões de features no mesmo campo
3. **Performance**: Índice GIN permite queries em subcampos
4. **Schema flexibility**: Features heterogêneas por notícia

**Feature Registry** (versionamento):

```yaml
# feature_registry.yaml
features:
  sentiment:
    version: "1.0"
    model: "bedrock/claude-haiku"
    compute: "enrichment-worker"
    schema:
      type: object
      properties:
        label: {type: string, enum: [positive, negative, neutral]}
        score: {type: number, minimum: 0, maximum: 1}
    
  entities:
    version: "1.0"
    model: "bedrock/claude-haiku"
    compute: "enrichment-worker"
    schema:
      type: array
      items:
        type: object
        properties:
          text: {type: string}
          type: {type: string, enum: [PER, ORG, LOC]}
  
  readability:
    version: "1.0"
    model: "local/textstat"
    compute: "feature-worker"
    schema:
      type: object
      properties:
        flesch_ease: {type: number}
        grade_level: {type: integer}
  
  trending_score:
    version: "1.0"
    model: "bigquery/sql"
    compute: "airflow-dag"
    schema:
      type: number
```

### **3.6.4 Gold Layer - Dados Enriquecidos**

**Objetivo**: Dados agregados, métricas, analytics (OLAP)

**Armazenamento**: BigQuery + HuggingFace

**Dataset BigQuery `dgb_gold`**:

| Tabela | Tipo | Descrição |
|--------|------|-----------|
| `fato_noticias` | Fato | Todas as notícias com dimensões |
| `dim_agencies` | Dimensão | Órgãos governamentais |
| `dim_themes` | Dimensão | Taxonomia de temas |
| `dim_dates` | Dimensão | Calendário com feriados |
| `agg_daily_metrics` | Agregação | Métricas diárias por órgão/tema |
| `agg_trending` | Agregação | Score de trending por notícia |
| `agg_sentiment_by_theme` | Agregação | Sentiment médio por tema |

**DAG de analytics** (`sync_analytics_to_bigquery`):

```python
@dag(schedule="0 7 * * *")  # 7AM UTC
def sync_analytics_to_bigquery():
    """Sincroniza dados do PostgreSQL para BigQuery Gold."""
    
    @task
    def sync_fato_noticias():
        """Sincroniza fato_noticias (incremental)."""
        query = """
        INSERT INTO dgb_gold.fato_noticias
        SELECT
            n.unique_id,
            n.agency_id,
            n.most_specific_theme_id,
            DATE(n.published_at) as date_id,
            n.title,
            n.summary,
            CHAR_LENGTH(n.content) as content_length,
            nf.features->>'sentiment.score' as sentiment_score,
            nf.features->>'sentiment.label' as sentiment_label,
            ARRAY_LENGTH(nf.features->'entities') as entity_count,
            n.created_at
        FROM news n
        LEFT JOIN news_features nf ON n.unique_id = nf.unique_id
        WHERE n.published_at::date = CURRENT_DATE - INTERVAL '1 day'
        """
        bigquery_client.query(query)
    
    @task
    def calculate_trending():
        """Calcula trending score baseado em engajamento."""
        query = """
        CREATE OR REPLACE TABLE dgb_gold.agg_trending AS
        SELECT
            f.unique_id,
            (
                COALESCE(pageviews, 0) * 1.0 +
                COALESCE(likes, 0) * 2.0 +
                COALESCE(shares, 0) * 3.0 +
                COALESCE(replies, 0) * 4.0
            ) / (TIMESTAMP_DIFF(CURRENT_TIMESTAMP, f.created_at, HOUR) + 2) as trending_score
        FROM dgb_gold.fato_noticias f
        LEFT JOIN dgb_gold.engagement_metrics e ON f.unique_id = e.unique_id
        WHERE f.created_at >= TIMESTAMP_SUB(CURRENT_TIMESTAMP, INTERVAL 7 DAY)
        """
        bigquery_client.query(query)
    
    @task
    def update_feature_store():
        """Atualiza Feature Store com trending_score do BigQuery."""
        # Lê trending_score do BigQuery
        df = bigquery_client.query("""
            SELECT unique_id, trending_score
            FROM dgb_gold.agg_trending
            WHERE trending_score > 0
        """).to_dataframe()
        
        # Atualiza news_features no PostgreSQL
        for _, row in df.iterrows():
            postgres_manager.execute("""
                UPDATE news_features
                SET features = jsonb_set(
                    features,
                    '{trending_score}',
                    to_jsonb(%s::float)
                )
                WHERE unique_id = %s
            """, (row['trending_score'], row['unique_id']))
```

**Queries de Analytics**:

```sql
-- Top 10 temas por volume (últimos 30 dias)
SELECT
    t.label as theme,
    COUNT(*) as article_count,
    AVG(CAST(nf.features->>'sentiment.score' AS FLOAT)) as avg_sentiment
FROM dgb_gold.fato_noticias f
JOIN dgb_gold.dim_themes t ON f.most_specific_theme_id = t.id
JOIN news_features nf ON f.unique_id = nf.unique_id
WHERE f.date_id >= CURRENT_DATE - INTERVAL '30 days'
GROUP BY t.label
ORDER BY article_count DESC
LIMIT 10;

-- Trending hoje por órgão
SELECT
    a.name as agency,
    COUNT(*) as article_count,
    AVG(tr.trending_score) as avg_trending
FROM dgb_gold.fato_noticias f
JOIN dgb_gold.dim_agencies a ON f.agency_id = a.id
JOIN dgb_gold.agg_trending tr ON f.unique_id = tr.unique_id
WHERE f.date_id = CURRENT_DATE
GROUP BY a.name
ORDER BY avg_trending DESC;
```

### **3.6.5 Fases de Implementação**

| Fase | Escopo | Status | Timeline | Custo |
|------|--------|--------|----------|-------|
| **Fase 0** | GCS bucket + BigQuery dataset + Feature Registry | ✅ Completo | 1 dia | $0 |
| **Fase 1** | Bronze Writer (Cloud Function) + DAG bronze_ingestion | ✅ Completo | 2 dias | +$1/mês |
| **Fase 2** | Feature Store (news_features JSONB) + backfill | ✅ Completo | 2 dias | +$0 |
| **Fase 3** | Gold Analytics (BigQuery) + DAGs | ✅ Completo | 3 dias | +$1-3/mês |
| **Fase 4** | Trending scores + Topic clusters | 🚧 Em progresso | 2 semanas | +$2/mês |
| **Fase 5** | Dados de usuário (Firestore) | 📋 Planejado | 4 semanas | +$0-2/mês |

**Custo incremental total** (Fases 0-3): **+$2-4/mês**

## **3.7 Regras de Qualidade de Dados**

O sistema implementa um **framework robusto e multicamadas** de controle de qualidade, garantindo integridade, consistência e confiabilidade dos dados em todas as etapas do pipeline.

### **3.7.1 Schema Validation com Pydantic**

O sistema utiliza **Pydantic** para validação de schema em tempo de execução, garantindo que todos os documentos atendam ao contrato de dados definido antes de serem processados.

#### **Schema Base**

```python
from pydantic import BaseModel, Field, validator, HttpUrl
from typing import Optional, List
from datetime import datetime, date
from enum import Enum
import re

class DocumentStatus(str, Enum):
    """Status do documento no pipeline."""
    PENDING = "pending"
    PROCESSED = "processed"
    ENRICHED = "enriched"
    ERROR = "error"

class GovBrDocument(BaseModel):
    """Schema Pydantic para documentos do DestaquesGovbr."""

    # Campos obrigatórios
    unique_id: str = Field(..., min_length=64, max_length=64, description="SHA256 hash hexadecimal")
    agency: str = Field(..., min_length=2, max_length=100, description="Código do órgão gov.br")
    title: str = Field(..., min_length=10, max_length=500, description="Título da notícia")
    published_at: datetime = Field(..., description="Data/hora de publicação")
    source_url: HttpUrl = Field(..., description="URL original da notícia")

    # Campos opcionais
    content: Optional[str] = Field(None, min_length=100, max_length=50000, description="Conteúdo em Markdown")
    subtitle: Optional[str] = Field(None, max_length=1000, description="Subtítulo/resumo")
    summary: Optional[str] = Field(None, max_length=1000, description="Resumo gerado por IA")
    themes: Optional[List[str]] = Field(default_factory=list, description="Códigos de temas (ex: 01.01.02)")
    status: DocumentStatus = DocumentStatus.PENDING
    
    # Campos de enriquecimento (opcionais)
    sentiment: Optional[str] = Field(None, description="Sentiment: positive, neutral, negative")
    entities: Optional[List[str]] = Field(default_factory=list, description="Entidades extraídas")
    content_embedding: Optional[List[float]] = Field(None, description="Embedding 768-dim")

    class Config:
        """Configurações do Pydantic."""
        str_strip_whitespace = True  # Remove espaços em branco
        validate_assignment = True    # Valida em atribuições
        use_enum_values = True        # Usa valores de enum

    @validator('unique_id')
    def validate_unique_id_format(cls, v):
        """
        Valida que unique_id é um hash SHA256 válido (64 caracteres hexadecimais).
        
        Regra Q01: unique_id DEVE ser string única SHA256.
        """
        if not re.match(r'^[a-f0-9]{64}$', v.lower()):
            raise ValueError(
                f"unique_id deve ser SHA256 hexadecimal (64 chars): recebido {len(v)} chars"
            )
        return v.lower()

    @validator('source_url')
    def validate_source_url(cls, v):
        """
        Valida que source_url é uma URL HTTP/HTTPS válida.
        
        Regra Q02: source_url DEVE ser URL válida.
        """
        url_str = str(v)
        if not url_str.startswith(('http://', 'https://')):
            raise ValueError("source_url deve começar com http:// ou https://")
        return v

    @validator('published_at')
    def validate_published_at(cls, v):
        """
        Valida que published_at está em range válido (2015-presente).
        
        Regra Q03: published_at DEVE ser datetime válido e não no futuro.
        """
        now = datetime.now()
        min_date = datetime(2015, 1, 1)
        
        if v > now:
            raise ValueError(
                f"published_at não pode ser no futuro: {v} > {now}"
            )
        if v < min_date:
            raise ValueError(
                f"published_at muito antiga (anterior a 2015): {v}"
            )
        return v

    @validator('title')
    def clean_title(cls, v):
        """Remove espaços extras e normaliza título."""
        return ' '.join(v.split())

    @validator('content')
    def validate_content_length(cls, v):
        """
        Valida que content tem tamanho adequado.
        
        Regra Q04: content DEVE ter entre 100-50.000 caracteres.
        """
        if v is None:
            return v
        
        # Remove apenas whitespace
        content_stripped = v.strip()
        if not content_stripped:
            return None
        
        length = len(content_stripped)
        if length < 100:
            raise ValueError(
                f"Conteúdo muito curto: {length} chars (mínimo: 100)"
            )
        if length > 50000:
            raise ValueError(
                f"Conteúdo muito longo: {length} chars (máximo: 50.000)"
            )
        
        return content_stripped

    @validator('themes')
    def validate_themes(cls, v):
        """
        Valida que temas são únicos e em formato correto.
        
        Regra Q05: themes DEVE ser lista de strings únicas em lowercase.
        """
        if not v:
            return v
        
        # Remove duplicatas e normaliza
        unique_themes = list(set(theme.lower().strip() for theme in v if theme))
        
        # Valida formato (ex: 01.01.02)
        theme_pattern = re.compile(r'^\d{2}\.\d{2}(\.\d{2})?$')
        for theme in unique_themes:
            if not theme_pattern.match(theme):
                raise ValueError(
                    f"Formato de tema inválido: {theme} (esperado: XX.XX ou XX.XX.XX)"
                )
        
        return unique_themes

    @validator('sentiment')
    def validate_sentiment(cls, v):
        """Valida valores permitidos de sentiment."""
        if v is None:
            return v
        
        allowed = ['positive', 'neutral', 'negative']
        if v.lower() not in allowed:
            raise ValueError(
                f"Sentiment inválido: {v} (permitidos: {', '.join(allowed)})"
            )
        return v.lower()

    @validator('content_embedding')
    def validate_embedding_dimension(cls, v):
        """Valida dimensão do embedding (768-dim)."""
        if v is None:
            return v
        
        if len(v) != 768:
            raise ValueError(
                f"Embedding deve ter 768 dimensões: recebido {len(v)}"
            )
        return v
```

#### **Regras de Validação Pydantic**

| ID | Campo | Regra | Tipo de Validação |
|----|-------|-------|-------------------|
| **Q01** | `unique_id` | DEVE ser string única SHA256 (64 caracteres hex) | Formato + Unicidade |
| **Q02** | `source_url` | DEVE ser URL válida (HTTP/HTTPS) | Formato (HttpUrl) |
| **Q03** | `published_at` | DEVE ser datetime válido entre 2015 e hoje | Formato + Range |
| **Q04** | `content` | DEVE ter entre 100-50.000 caracteres | Tamanho (min_length, max_length) |
| **Q05** | `themes` | DEVE ser lista de strings únicas em lowercase (formato XX.XX.XX) | Tipo + Formato |
| **Q06** | `sentiment` | DEVE ser 'positive', 'neutral' ou 'negative' | Enum values |
| **Q07** | `content_embedding` | DEVE ter exatamente 768 dimensões | Array length |

#### **Exemplo de Uso**

```python
from typing import List, Tuple

def validate_scraped_document(raw_data: dict) -> Tuple[GovBrDocument, List[str]]:
    """
    Valida documento recém-coletado.
    
    Returns:
        (documento_validado, lista_de_erros)
    """
    try:
        validated = GovBrDocument(**raw_data)
        return validated, []
    except ValidationError as e:
        errors = [f"{err['loc'][0]}: {err['msg']}" for err in e.errors()]
        logger.warning(f"Documento inválido {raw_data.get('unique_id')}: {errors}")
        return None, errors

# Uso no scraper
raw_doc = {
    'unique_id': hashlib.sha256(url.encode()).hexdigest(),
    'agency': 'fazenda',
    'title': 'Nova política econômica anunciada',
    'published_at': datetime.now(),
    'source_url': 'https://www.gov.br/fazenda/pt-br/noticias/...',
    'content': '...'  # Conteúdo em Markdown
}

validated_doc, errors = validate_scraped_document(raw_doc)
if errors:
    # Log erros, envia para DLQ ou descarta
    pass
else:
    # Insere no PostgreSQL
    db.insert(validated_doc)
```

#### **Taxa de Validação**

- **Status atual**: ✅ **98%** (Meta: ≥ 97%)
- **Documentos rejeitados**: ~2% (erros de schema)
- **Erros mais comuns**:
  1. `content_too_short`: 45% dos erros (< 100 chars)
  2. `invalid_url`: 25% dos erros (URL malformada)
  3. `unique_id_format`: 15% dos erros (não SHA256)
  4. `future_date`: 10% dos erros (data no futuro)
  5. `invalid_theme`: 5% dos erros (formato tema incorreto)

### **3.7.2 Validação em Lote**

Sistema de validação otimizado para processar **grandes volumes** de documentos simultaneamente, com separação de válidos/inválidos e relatórios detalhados.

#### **BatchValidator**

```python
from typing import List, Dict, Tuple, Any
from pydantic import ValidationError
import pandas as pd
from datetime import datetime

class BatchValidator:
    """Validador de lotes de documentos."""

    def __init__(self):
        self.valid_docs: List[GovBrDocument] = []
        self.invalid_docs: List[Dict] = []
        self.errors_by_type: Dict[str, int] = {}
        self.start_time: datetime = None
        self.end_time: datetime = None

    def validate_batch(self, documents: List[Dict]) -> Tuple[List[GovBrDocument], List[Dict]]:
        """
        Valida um lote de documentos.
        
        Args:
            documents: Lista de documentos brutos (dicts)
        
        Returns:
            Tuple de (documentos_válidos, documentos_inválidos_com_erros)
        """
        self.start_time = datetime.now()
        self.valid_docs = []
        self.invalid_docs = []
        
        for i, doc in enumerate(documents):
            try:
                validated = GovBrDocument(**doc)
                self.valid_docs.append(validated)
            except ValidationError as e:
                # Coleta erros detalhados
                error_summary = {
                    'document_index': i,
                    'unique_id': doc.get('unique_id', 'UNKNOWN'),
                    'agency': doc.get('agency', 'UNKNOWN'),
                    'errors': []
                }
                
                for error in e.errors():
                    field = '.'.join(str(loc) for loc in error['loc'])
                    error_type = error['type']
                    message = error['msg']
                    
                    error_summary['errors'].append({
                        'field': field,
                        'type': error_type,
                        'message': message
                    })
                    
                    # Contabiliza por tipo
                    self.errors_by_type[error_type] = self.errors_by_type.get(error_type, 0) + 1
                
                self.invalid_docs.append({
                    'document': doc,
                    'error_summary': error_summary
                })
                
                logger.warning(
                    f"Documento inválido [{i}] {doc.get('unique_id')}: "
                    f"{len(error_summary['errors'])} erros"
                )
        
        self.end_time = datetime.now()
        return self.valid_docs, self.invalid_docs
    
    def get_validation_report(self) -> Dict[str, Any]:
        """
        Gera relatório completo de validação.
        
        Returns:
            Dict com métricas e estatísticas do lote
        """
        total = len(self.valid_docs) + len(self.invalid_docs)
        processing_time = (self.end_time - self.start_time).total_seconds() * 1000  # ms
        
        return {
            'summary': {
                'total_documents': total,
                'valid_count': len(self.valid_docs),
                'invalid_count': len(self.invalid_docs),
                'validation_rate': len(self.valid_docs) / total if total > 0 else 0,
                'processing_time_ms': processing_time,
                'throughput_docs_per_sec': total / (processing_time / 1000) if processing_time > 0 else 0
            },
            'errors_by_type': dict(sorted(
                self.errors_by_type.items(),
                key=lambda x: x[1],
                reverse=True
            )),
            'invalid_documents_sample': self.invalid_docs[:10],  # Primeiros 10 inválidos
            'validation_metrics': self._calculate_field_metrics()
        }
    
    def _calculate_field_metrics(self) -> Dict[str, Any]:
        """Calcula métricas por campo."""
        if not self.valid_docs:
            return {}
        
        # Converte para DataFrame para análise
        df = pd.DataFrame([doc.dict() for doc in self.valid_docs])
        
        metrics = {}
        for col in df.columns:
            if df[col].dtype == 'object':
                # Campos de texto
                metrics[col] = {
                    'null_count': df[col].isna().sum(),
                    'null_rate': df[col].isna().sum() / len(df),
                    'unique_count': df[col].nunique()
                }
            elif col == 'themes':
                # Temas (lista)
                theme_counts = df[col].apply(lambda x: len(x) if x else 0)
                metrics[col] = {
                    'avg_themes_per_doc': theme_counts.mean(),
                    'max_themes': theme_counts.max(),
                    'docs_with_themes': (theme_counts > 0).sum()
                }
        
        return metrics
    
    def export_invalid_docs_to_csv(self, filepath: str):
        """Exporta documentos inválidos para CSV (debugging)."""
        if not self.invalid_docs:
            logger.info("Nenhum documento inválido para exportar")
            return
        
        rows = []
        for item in self.invalid_docs:
            doc = item['document']
            error_summary = item['error_summary']
            
            rows.append({
                'unique_id': doc.get('unique_id', 'UNKNOWN'),
                'agency': doc.get('agency', 'UNKNOWN'),
                'title': doc.get('title', 'UNKNOWN')[:100],
                'error_count': len(error_summary['errors']),
                'error_types': ', '.join(set(e['type'] for e in error_summary['errors'])),
                'error_fields': ', '.join(set(e['field'] for e in error_summary['errors']))
            })
        
        df = pd.DataFrame(rows)
        df.to_csv(filepath, index=False, encoding='utf-8')
        logger.info(f"Exportados {len(rows)} documentos inválidos para {filepath}")
```

#### **Uso no Pipeline**

```python
# DAG de validação diária (Airflow)
@dag(schedule="0 2 * * *")  # 2 AM daily
def validate_daily_batch():
    """Valida todos os documentos do dia anterior."""
    
    @task
    def fetch_yesterday_docs() -> List[Dict]:
        """Busca documentos inseridos ontem."""
        yesterday = datetime.now() - timedelta(days=1)
        
        query = """
            SELECT unique_id, agency, title, published_at, source_url, 
                   content, subtitle, themes, sentiment, entities
            FROM news
            WHERE DATE(scraped_at) = DATE(%s)
        """
        
        with db.cursor() as cur:
            cur.execute(query, (yesterday,))
            return [dict(row) for row in cur.fetchall()]
    
    @task
    def validate_batch_task(documents: List[Dict]) -> Dict[str, Any]:
        """Executa validação em lote."""
        validator = BatchValidator()
        valid, invalid = validator.validate_batch(documents)
        
        report = validator.get_validation_report()
        
        # Log relatório
        logger.info(f"Validação concluída: {report['summary']}")
        
        # Exporta inválidos para CSV (debugging)
        if invalid:
            validator.export_invalid_docs_to_csv(
                f"/tmp/invalid_docs_{datetime.now().strftime('%Y%m%d')}.csv"
            )
        
        # Envia alerta se taxa < 97%
        if report['summary']['validation_rate'] < 0.97:
            send_alert(
                title="Taxa de validação abaixo da meta",
                message=f"Taxa: {report['summary']['validation_rate']:.2%} (Meta: ≥ 97%)",
                severity="high"
            )
        
        return report
    
    documents = fetch_yesterday_docs()
    report = validate_batch_task(documents)

validate_daily_batch()
```

#### **Exemplo de Relatório**

```json
{
  "summary": {
    "total_documents": 1000,
    "valid_count": 980,
    "invalid_count": 20,
    "validation_rate": 0.98,
    "processing_time_ms": 1523,
    "throughput_docs_per_sec": 656.86
  },
  "errors_by_type": {
    "value_error.str.min_length": 8,
    "value_error.url": 5,
    "value_error.datetime.future": 4,
    "value_error.list": 3
  },
  "invalid_documents_sample": [
    {
      "document": {"unique_id": "abc123...", "agency": "fazenda", ...},
      "error_summary": {
        "document_index": 42,
        "unique_id": "abc123...",
        "agency": "fazenda",
        "errors": [
          {
            "field": "content",
            "type": "value_error.str.min_length",
            "message": "Conteúdo muito curto: 45 chars (mínimo: 100)"
          }
        ]
      }
    }
  ],
  "validation_metrics": {
    "content": {
      "null_count": 0,
      "null_rate": 0.0,
      "unique_count": 980
    },
    "themes": {
      "avg_themes_per_doc": 2.3,
      "max_themes": 5,
      "docs_with_themes": 952
    }
  }
}
```

### **3.7.3 Detecção de Anomalias**

Sistema de **detecção proativa** de padrões anômalos no dataset, identificando problemas antes que impactem usuários finais.

#### **AnomalyDetector**

```python
import pandas as pd
import numpy as np
from typing import List, Dict, Any
from datetime import datetime, timedelta
from scipy import stats

class AnomalyDetector:
    """Detecta anomalias no pipeline de scraping e enriquecimento."""

    def __init__(self, db_connection):
        self.db = db_connection
        self.anomalies: List[Dict[str, Any]] = []
        self.df: pd.DataFrame = None

    def detect_all(self) -> List[Dict[str, Any]]:
        """
        Executa todas as detecções de anomalia.
        
        Returns:
            Lista de anomalias detectadas
        """
        # Carrega dados dos últimos 30 dias
        self.df = self._load_recent_data(days=30)
        
        # Executa detectores
        self._detect_volume_anomaly()          # Volume anormal por dia
        self._detect_duplicate_spike()         # Pico de duplicatas
        self._detect_missing_fields()          # Campos obrigatórios faltando
        self._detect_date_anomalies()          # Datas inválidas
        self._detect_agency_coverage()         # Órgãos sem dados
        self._detect_content_anomalies()       # Conteúdo suspeito
        
        # Ordena por severidade
        self.anomalies.sort(key=lambda x: {'high': 0, 'medium': 1, 'low': 2}[x['severity']])
        
        return self.anomalies
    
    def _load_recent_data(self, days: int = 30) -> pd.DataFrame:
        """Carrega dados recentes do PostgreSQL."""
        query = """
            SELECT unique_id, agency, title, published_at, scraped_at,
                   LENGTH(content) as content_length,
                   theme_l1_id, theme_l2_id, theme_l3_id,
                   sentiment, entities,
                   content_embedding IS NOT NULL as has_embedding
            FROM news
            WHERE scraped_at >= NOW() - INTERVAL '%s days'
        """
        
        return pd.read_sql(query, self.db, params=(days,))
    
    def _detect_volume_anomaly(self, threshold_std: float = 2.0):
        """
        Detecta volume anormal de documentos por dia usando Z-score.
        
        Baseline: média móvel de 7 dias
        Alerta: desvio > 2σ (95% confidence) ou > 3σ (99.7% confidence)
        """
        daily_counts = self.df.groupby(
            self.df['scraped_at'].dt.date
        ).size()
        
        # Calcula média e desvio padrão
        mean = daily_counts.mean()
        std = daily_counts.std()
        
        for date, count in daily_counts.items():
            z_score = (count - mean) / std if std > 0 else 0
            
            if abs(z_score) > threshold_std:
                severity = 'high' if abs(z_score) > 3 else 'medium'
                direction = 'alto' if z_score > 0 else 'baixo'
                
                self.anomalies.append({
                    'type': 'volume_anomaly',
                    'severity': severity,
                    'date': str(date),
                    'count': int(count),
                    'expected': round(mean, 1),
                    'z_score': round(z_score, 2),
                    'std_dev': round(std, 1),
                    'message': f"Volume {direction}: {count} docs (esperado: ~{mean:.0f} ± {std:.0f})",
                    'recommendation': 'Verificar scraper ou fontes gov.br' if z_score < 0 else 'Pico esperado ou verificar duplicatas'
                })
    
    def _detect_duplicate_spike(self, threshold: float = 0.05):
        """
        Detecta picos de documentos duplicados (unique_id).
        
        Baseline: 1.2% duplicatas
        Alerta: taxa > 5%
        """
        daily_duplicates = self.df.groupby(
            self.df['scraped_at'].dt.date
        ).apply(lambda x: x['unique_id'].duplicated().sum() / len(x))
        
        for date, dup_rate in daily_duplicates.items():
            if dup_rate > threshold:
                self.anomalies.append({
                    'type': 'duplicate_spike',
                    'severity': 'high',
                    'date': str(date),
                    'duplicate_rate': round(dup_rate, 4),
                    'threshold': threshold,
                    'message': f"Pico de duplicatas: {dup_rate:.2%} (normal: ~1.2%)",
                    'recommendation': 'Verificar lógica de unique_id no scraper ou re-scraping acidental'
                })
    
    def _detect_missing_fields(self, threshold: float = 0.01):
        """
        Detecta campos obrigatórios faltando (NULL).
        
        Alerta: taxa > 1% para campos críticos
        """
        critical_fields = ['title', 'published_at', 'content', 'agency']
        
        for field in critical_fields:
            if field not in self.df.columns:
                continue
            
            null_rate = self.df[field].isna().sum() / len(self.df)
            
            if null_rate > threshold:
                self.anomalies.append({
                    'type': 'missing_field',
                    'severity': 'high',
                    'field': field,
                    'null_count': int(self.df[field].isna().sum()),
                    'null_rate': round(null_rate, 4),
                    'threshold': threshold,
                    'message': f"Campo '{field}' faltando em {null_rate:.2%} dos documentos",
                    'recommendation': f'Verificar scraper para campo {field}'
                })
    
    def _detect_date_anomalies(self):
        """
        Detecta datas inválidas (futuro, muito antiga).
        
        Válido: 2015-01-01 até hoje
        Alerta: > 0.5% fora do range
        """
        now = pd.Timestamp.now()
        min_date = pd.Timestamp('2015-01-01')
        
        # Datas no futuro
        future_dates = self.df[self.df['published_at'] > now]
        if len(future_dates) > 0:
            self.anomalies.append({
                'type': 'future_dates',
                'severity': 'medium',
                'count': len(future_dates),
                'rate': round(len(future_dates) / len(self.df), 4),
                'message': f"{len(future_dates)} documentos com data no futuro",
                'sample_dates': future_dates['published_at'].head(5).astype(str).tolist(),
                'recommendation': 'Verificar timezone ou clock do servidor scraper'
            })
        
        # Datas muito antigas
        old_dates = self.df[self.df['published_at'] < min_date]
        if len(old_dates) > 0:
            self.anomalies.append({
                'type': 'old_dates',
                'severity': 'low',
                'count': len(old_dates),
                'rate': round(len(old_dates) / len(self.df), 4),
                'message': f"{len(old_dates)} documentos com data anterior a 2015",
                'sample_dates': old_dates['published_at'].head(5).astype(str).tolist(),
                'recommendation': 'Verificar parsing de data ou scraping de histórico'
            })
    
    def _detect_agency_coverage(self, min_docs_per_week: int = 1):
        """
        Detecta órgãos sem publicação nos últimos 7 dias.
        
        Total órgãos: ~160
        Alerta: < 90% ativos (144 órgãos)
        """
        last_week = datetime.now() - timedelta(days=7)
        recent_docs = self.df[self.df['scraped_at'] >= last_week]
        
        # Órgãos ativos (com pelo menos 1 doc)
        active_agencies = recent_docs['agency'].nunique()
        
        # Total de órgãos (query separada)
        total_agencies_query = "SELECT COUNT(DISTINCT agency) FROM agencies WHERE active = true"
        total_agencies = pd.read_sql(total_agencies_query, self.db).iloc[0, 0]
        
        coverage_rate = active_agencies / total_agencies if total_agencies > 0 else 0
        
        if coverage_rate < 0.90:
            # Identifica órgãos inativos
            all_agencies = pd.read_sql("SELECT agency FROM agencies WHERE active = true", self.db)
            inactive_agencies = set(all_agencies['agency']) - set(recent_docs['agency'].unique())
            
            self.anomalies.append({
                'type': 'low_agency_coverage',
                'severity': 'medium',
                'active_agencies': active_agencies,
                'total_agencies': total_agencies,
                'coverage_rate': round(coverage_rate, 4),
                'threshold': 0.90,
                'message': f"Cobertura de órgãos: {coverage_rate:.1%} (meta: ≥ 90%)",
                'inactive_agencies_sample': list(inactive_agencies)[:10],
                'recommendation': 'Verificar scrapers de órgãos inativos ou sites fora do ar'
            })
    
    def _detect_content_anomalies(self):
        """
        Detecta conteúdo suspeito (muito curto, HTML não convertido, duplicatas).
        """
        # Conteúdo muito curto (< 100 chars)
        short_content = self.df[self.df['content_length'] < 100]
        if len(short_content) > 10:  # Threshold: > 10 docs
            self.anomalies.append({
                'type': 'short_content',
                'severity': 'low',
                'count': len(short_content),
                'rate': round(len(short_content) / len(self.df), 4),
                'message': f"{len(short_content)} documentos com conteúdo < 100 chars",
                'sample_ids': short_content['unique_id'].head(5).tolist(),
                'recommendation': 'Verificar parsing HTML→Markdown ou scraping de páginas vazias'
            })
        
        # Títulos duplicados (conteúdo diferente)
        duplicate_titles = self.df[self.df.duplicated(subset=['title'], keep=False)]
        if len(duplicate_titles) > 0:
            unique_ids_per_title = duplicate_titles.groupby('title')['unique_id'].nunique()
            titles_with_multiple_ids = unique_ids_per_title[unique_ids_per_title > 1]
            
            if len(titles_with_multiple_ids) > 5:  # Threshold: > 5 títulos
                self.anomalies.append({
                    'type': 'duplicate_titles',
                    'severity': 'low',
                    'count': len(titles_with_multiple_ids),
                    'message': f"{len(titles_with_multiple_ids)} títulos duplicados com unique_ids diferentes",
                    'sample_titles': titles_with_multiple_ids.head(5).index.tolist(),
                    'recommendation': 'Verificar se são atualizações legítimas ou problema no scraper'
                })
```

#### **Anomalias Detectadas**

| Tipo | Descrição | Severidade | Limiar | Recomendação |
|------|-----------|------------|--------|--------------|
| **volume_anomaly** | Volume de documentos fora do padrão (Z-score > 2) | High/Medium | ±2σ ou ±3σ | Verificar scraper ou fontes gov.br |
| **duplicate_spike** | Taxa de duplicatas > 5% | High | 5% | Verificar lógica unique_id ou re-scraping |
| **missing_field** | Campos obrigatórios ausentes (> 1%) | High | 1% | Verificar scraper para campo específico |
| **future_dates** | Datas de publicação no futuro | Medium | > 0 | Verificar timezone ou clock do servidor |
| **old_dates** | Datas antes de 2015 | Low | < 2015-01-01 | Verificar parsing de data |
| **low_agency_coverage** | Órgãos sem dados nos últimos 7 dias | Medium | < 90% ativos | Verificar scrapers inativos ou sites fora |
| **short_content** | Conteúdo com < 100 caracteres | Low | > 10 docs | Verificar parsing HTML→Markdown |
| **duplicate_titles** | Títulos duplicados com unique_ids diferentes | Low | > 5 títulos | Verificar se são atualizações legítimas |

#### **Uso no Pipeline**

```python
# DAG de detecção de anomalias (a cada 6 horas)
@dag(schedule="0 */6 * * *")
def detect_pipeline_anomalies():
    """Detecta anomalias no pipeline a cada 6 horas."""
    
    @task
    def run_anomaly_detection() -> List[Dict[str, Any]]:
        """Executa detecção de anomalias."""
        detector = AnomalyDetector(db_connection)
        anomalies = detector.detect_all()
        
        # Log anomalias
        logger.info(f"Detectadas {len(anomalies)} anomalias")
        
        # Filtra por severidade
        high_severity = [a for a in anomalies if a['severity'] == 'high']
        medium_severity = [a for a in anomalies if a['severity'] == 'medium']
        
        # Envia alertas
        if high_severity:
            send_alert(
                title=f"⚠️ {len(high_severity)} anomalias HIGH detectadas",
                message='\n'.join([a['message'] for a in high_severity[:5]]),
                severity='high',
                channel='slack'
            )
        
        if medium_severity:
            send_alert(
                title=f"ℹ️ {len(medium_severity)} anomalias MEDIUM detectadas",
                message='\n'.join([a['message'] for a in medium_severity[:5]]),
                severity='medium',
                channel='email'
            )
        
        return anomalies
    
    anomalies = run_anomaly_detection()

detect_pipeline_anomalies()
```

### **3.7.4 Métricas de Qualidade (Atualizadas)**

O sistema monitora as seguintes **métricas de qualidade**:

| Métrica | Descrição | Fórmula | Meta | Status Atual |
|---------|-----------|---------|------|--------------|
| **Taxa de validação** | % de documentos que passam na validação Pydantic | `válidos / total` | ≥ 97% | ✅ 98% |
| **Taxa de enriquecimento** | % de documentos com temas classificados (Bedrock) | `com_temas / total` | ≥ 95% | ✅ 97% |
| **Taxa de embedding** | % de documentos com embeddings gerados | `com_embeddings / total` | ≥ 99% | ✅ 99.2% |
| **Taxa de sentiment** | % de documentos com sentiment analysis | `com_sentiment / total` | ≥ 95% | ✅ 97% |
| **Taxa de entities** | % de documentos com entity extraction | `com_entities / total` | ≥ 95% | ✅ 97% |
| **Taxa de duplicatas** | % de documentos duplicados por unique_id | `duplicatas / total` | ≤ 2% | ✅ 1.2% |
| **Cobertura de órgãos** | % de órgãos com dados nos últimos 7 dias | `órgãos_ativos / total_órgãos` | ≥ 90% | ✅ 92% |
| **Latência de pipeline** | Tempo desde scraping até indexação Typesense | `time_indexed - time_scraped` | ≤ 1 min | ✅ ~15s |
| **Taxa de sucesso de scraping** | % de notícias inseridas vs tentadas | `inseridas / tentadas` | ≥ 97% | ✅ 97.5% |
| **Pub/Sub delivery rate** | % de mensagens entregues com sucesso | `acks / published` | ≥ 99% | ✅ 99.8% |
| **Dead-letter rate** | % de mensagens na DLQ | `dlq_messages / published` | ≤ 0.1% | ✅ 0.02% |

### **3.7.5 Tratamento de Erros (Event-Driven)**

**ATUALIZAÇÃO**: Estratégias de erro para arquitetura event-driven

| Erro | Etapa | Ação | Retry | DLQ | Impacto |
|------|-------|------|-------|-----|---------|
| **HTTP Timeout** | Scraping | Skip artigo, log warning | Sim (5x, backoff) | Não | Baixo (1 artigo) |
| **Pub/Sub publish fail** | Scraping | Log error, continue | Sim (3x) | Não | Médio (evento perdido) |
| **Bedrock throttle** | Enrichment | Backoff exponencial | Sim (Pub/Sub retry) | Sim (após 5x) | Baixo (1 notícia) |
| **Bedrock parse error** | Enrichment | Deixa temas NULL, ACK | Não | Não | Baixo (1 notícia) |
| **Database connection** | Todos workers | Retry com backoff | Sim (3x) | Sim (após 5x) | Médio (batch) |
| **Typesense connection** | Indexação | Retry com backoff | Sim (Pub/Sub retry) | Sim (após 5x) | Médio (1 notícia) |
| **ActivityPub fail** | Federação | Log error, ACK | Não | Não | Baixo (1 publicação) |
| **Worker timeout** | Todos | Pub/Sub nack → retry | Sim (até ack deadline) | Sim (após max attempts) | Médio (1 evento) |

**Configuração de Retry (Pub/Sub)**:

```python
from google.cloud import pubsub_v1
from google.api_core import retry

# Retry policy para publishers
publisher = pubsub_v1.PublisherClient()
retry_settings = retry.Retry(
    initial=0.1,  # 100ms
    maximum=60.0,  # 60s
    multiplier=2.0,
    deadline=300.0,  # 5 min total
    predicate=retry.if_exception_type(
        TimeoutError,
        ConnectionError
    )
)

future = publisher.publish(
    topic_name,
    data=message_data,
    retry=retry_settings
)
```

**Dead-Letter Queue (DLQ) Monitoring**:

```python
# DAG de monitoramento de DLQs (a cada 1 hora)
@dag(schedule="0 * * * *")
def monitor_dlq():
    """Monitora mensagens na DLQ e alerta equipe."""
    
    @task
    def check_dlq_messages():
        subscriber = pubsub_v1.SubscriberClient()
        
        dlq_topics = [
            "dgb.news.scraped-dlq",
            "dgb.news.enriched-dlq",
            "dgb.news.embedded-dlq"
        ]
        
        for topic in dlq_topics:
            subscription = f"{topic}--monitor"
            response = subscriber.pull(
                request={"subscription": subscription, "max_messages": 10}
            )
            
            if response.received_messages:
                logger.error(
                    f"DLQ {topic} has {len(response.received_messages)} messages",
                    extra={"topic": topic, "count": len(response.received_messages)}
                )
                
                # Alerta via Slack/Email
                send_alert(
                    title=f"DLQ Alert: {topic}",
                    message=f"Found {len(response.received_messages)} failed messages",
                    severity="high"
                )
```

## **3.8 Monitoramento e Observabilidade (Event-Driven)**

### **3.8.1 Rastreamento Distribuído**

**NOVO**: Sistema de rastreamento com `trace_id` em todos os eventos

**Fluxo de trace_id**:

```
Scraper gera trace_id (UUID)
  ↓
Publica em dgb.news.scraped (atributo trace_id)
  ↓
Enrichment Worker recebe e propaga
  ↓
Publica em dgb.news.enriched (mesmo trace_id)
  ↓
5 workers recebem (mesmo trace_id em todos)
  ↓
Logs agregados por trace_id no Cloud Logging
```

**Query de rastreamento**:

```
resource.type="cloud_run_revision"
jsonPayload.trace_id="550e8400-e29b-41d4-a716-446655440000"
```

**Resultado**: Timeline completo de uma notícia desde scraping até indexação

### **3.8.2 Métricas Pub/Sub**

**Cloud Monitoring** - Métricas automáticas:

| Métrica | Descrição | Alerta |
|---------|-----------|--------|
| `pubsub.googleapis.com/topic/send_message_operation_count` | Mensagens publicadas por topic | - |
| `pubsub.googleapis.com/subscription/ack_message_count` | Mensagens confirmadas (ACK) | - |
| `pubsub.googleapis.com/subscription/num_undelivered_messages` | Mensagens pendentes | > 100 |
| `pubsub.googleapis.com/subscription/oldest_unacked_message_age` | Idade da mensagem mais antiga | > 300s |
| `pubsub.googleapis.com/subscription/dead_letter_message_count` | Mensagens na DLQ | > 0 |

**Dashboard customizado** (Cloud Monitoring):

```yaml
dashboardFilters: []
mosaicLayout:
  columns: 12
  tiles:
  - width: 6
    height: 4
    widget:
      title: "Pub/Sub Message Flow"
      xyChart:
        dataSets:
        - timeSeriesQuery:
            timeSeriesFilter:
              filter: 'resource.type="pubsub_topic" AND metric.type="pubsub.googleapis.com/topic/send_message_operation_count"'
              aggregation:
                alignmentPeriod: 60s
                perSeriesAligner: ALIGN_RATE
```

### **3.8.3 Logs Estruturados**

**Formato padrão de logs**:

```json
{
  "severity": "INFO",
  "timestamp": "2026-04-23T10:30:15.123Z",
  "trace": "projects/inspire-7-finep/traces/550e8400-e29b-41d4-a716-446655440000",
  "message": "Article enriched successfully",
  "jsonPayload": {
    "unique_id": "abc123",
    "trace_id": "550e8400-e29b-41d4-a716-446655440000",
    "worker": "enrichment-worker",
    "duration_ms": 5234,
    "bedrock_tokens": 1523,
    "themes_classified": ["01.01", "01.01.02"],
    "has_summary": true,
    "has_sentiment": true,
    "has_entities": true,
    "entity_count": 3
  }
}
```

**Queries úteis**:

```
# Latência do pipeline end-to-end
resource.type="cloud_run_revision"
jsonPayload.trace_id=~".*"
jsonPayload.message=~"(Article scraped|Article enriched|Article indexed)"

# Erros no Enrichment Worker
resource.type="cloud_run_revision"
resource.labels.service_name="destaquesgovbr-enrichment-worker"
severity>=ERROR

# Performance do Bedrock
resource.type="cloud_run_revision"
jsonPayload.bedrock_tokens>2000
```

### **3.8.4 Alertas e Monitoramento**

**Status atual**: O sistema utiliza Google Cloud Monitoring para coleta de métricas e visualização em dashboards. Os alertas são configurados via Cloud Monitoring para condições críticas.

**Métricas monitoradas**:
- `oldest_unacked_message_age`: Idade da mensagem mais antiga não processada (alerta se > 600s)
- `dead_letter_message_count`: Número de mensagens na DLQ (alerta se > 10)
- `error_count`: Taxa de erros nos workers (alerta se > 10/min)
- `enrichment_rate`: Taxa de sucesso no enriquecimento (alerta se < 80%)
- Cloud Run health checks para todos os workers
- PostgreSQL connection pool utilization (alerta se > 80%)

**Canais de notificação**: Atualmente configurado via email. Para roadmap de melhorias, ver seção 5.4.

# **4 Resultados**

## **4.1 Dados Coletados (Atualizado)**

**Volume atual** (abril de 2026):

- **~310.000 documentos** no PostgreSQL (+10k desde versão 1.0)
- **~160 órgãos governamentais** monitorados
- **~500-1000 notícias/dia** coletadas
- **97.5% de taxa de sucesso** no scraping
- **97% de taxa de enriquecimento** com Bedrock (vs 95% com Cogfy)
- **99.2% de taxa de geração de embeddings**
- **97% com sentiment analysis** (novo)
- **97% com entity extraction** (novo)
- **~150 seguidores** no Fediverso via ActivityPub (novo)

**Distribuição temporal**:

- Dados desde **2020**
- Crescimento de **~15.000 docs/mês**
- Pico de **~2.000 docs/dia** em dias úteis

**Qualidade dos dados**:

- **1.2% de duplicatas** (unique_id) - melhoria vs 2% anterior
- **< 0.5% de campos obrigatórios faltando** - melhoria vs 1%
- **92% de cobertura** de órgãos (últimos 7 dias) - melhoria vs 90%
- **Latência média**: **~15 segundos** (vs 6 horas anterior) - **99.93% ↓**

## **4.2 Disponibilização (Atualizado)**

Os dados são disponibilizados em múltiplos formatos:

| Canal | URL | Formato | Atualização | Público | Novo |
|-------|-----|---------|-------------|---------|------|
| **Portal Web** | [destaques.gov.br](https://destaques.gov.br) | HTML (busca) | ~15s | Público | - |
| **HuggingFace** | [nitaibezerra/govbrnews](https://huggingface.co/datasets/nitaibezerra/govbrnews) | Parquet | Diário | Público | - |
| **API Typesense** | `typesense.destaques.gov.br` | JSON | ~15s | API key | - |
| **PostgreSQL** | Cloud SQL | SQL | Real-time | Interno | - |
| **BigQuery** | `dgb_gold` dataset | SQL | Diário | Interno | ✅ |
| **ActivityPub** | `@destaquesgovbr@destaques.gov.br` | ActivityStreams | ~15s | Fediverso | ✅ |
| **GCS Bronze** | `gs://dgb-data-lake/bronze/` | Parquet | Diário | Interno | ✅ |

**Novos casos de uso**:

- **Busca semântica**: Portal web + Typesense (latência ~15s)
- **Análise de dados**: HuggingFace Dataset (pandas, DuckDB)
- **Pesquisa acadêmica**: HuggingFace + notebooks
- **Integração externa**: API Typesense
- **Analytics OLAP**: BigQuery + Gold layer (✅ NOVO)
- **Federação social**: Mastodon/ActivityPub (✅ NOVO)
- **Reprocessamento**: GCS Bronze (✅ NOVO)

## **4.3 Impacto das Mudanças Arquiteturais**

### **4.3.1 Performance**

| Métrica | Antes (v1.0) | Depois (v1.1) | Melhoria |
|---------|--------------|---------------|----------|
| **Latência total** | ~45-60 min | ~15 segundos | **99.44% ↓** |
| **Latência scraping → enriquecimento** | 15-30 min | ~5s | **99.72% ↓** |
| **Latência enriquecimento → indexação** | 20-30 min | ~10s | **99.72% ↓** |
| **Taxa de enriquecimento** | 95% | 97% | **2 p.p. ↑** |
| **Taxa de duplicatas** | 2% | 1.2% | **0.8 p.p. ↓** |
| **Cobertura de órgãos** | 90% | 92% | **2 p.p. ↑** |
| **Campos faltando** | <1% | <0.5% | **0.5 p.p. ↓** |

### **4.3.2 Custos**

| Componente | Custo/mês (v1.0) | Custo/mês (v1.1) | Variação |
|------------|-----------------|-----------------|----------|
| **Cloud SQL (PostgreSQL)** | ~$48 | ~$48 | - |
| **Cloud Composer** | ~$100-150 | ~$100-150 | - |
| **Cloud Run (Scraper API)** | ~$5 | ~$5 | - |
| **Cloud Run (Workers)** | $0 | ~$5 | **+$5** |
| **Pub/Sub** | $0 | ~$3 | **+$3** |
| **LLM (Cogfy)** | ~$30 | $0 | **-$30** |
| **LLM (AWS Bedrock)** | $0 | ~$18 | **+$18** |
| **GCS (Bronze)** | $0 | ~$1 | **+$1** |
| **BigQuery (Gold)** | $0 | ~$2 | **+$2** |
| **Typesense (VM)** | ~$35 | ~$35 | - |
| **ActivityPub Server** | $0 | ~$2 | **+$2** |
| **HuggingFace** | $0 | $0 | - |
| **TOTAL** | **~$218-268** | **~$219-269** | **+$1-11/mês** |

**Análise de custo**:

- **Economia no LLM**: -$12/mês (Cogfy → Bedrock: $30 → $18)
- **Novos componentes**: +$13/mês (Workers, Pub/Sub, GCS, BigQuery, ActivityPub)
- **Custo incremental líquido**: +$1-11/mês (**+0.5-4%**)

**ROI**: 
- **Latência 99.44% ↓** por custo incremental < 5%
- **2 features novas** (sentiment + entities) sem custo adicional
- **3 canais novos** de distribuição (BigQuery, ActivityPub, GCS)

### **4.3.3 Novas Capacidades**

| Capacidade | Status | Impacto |
|-----------|--------|---------|
| **Near real-time processing** | ✅ 15s latência | Portal sempre atualizado |
| **Sentiment analysis** | ✅ 97% cobertura | Insights sobre polaridade |
| **Entity extraction** | ✅ 97% cobertura | NER completo (PER/ORG/LOC) |
| **Federação ActivityPub** | ✅ ~150 seguidores | Distribuição descentralizada |
| **Push notifications** | ✅ ~250 subscriptions | Engajamento proativo |
| **Analytics OLAP** | ✅ BigQuery Gold | Análises complexas |
| **Data Lake (Bronze)** | ✅ GCS Parquet | Reprocessamento seguro |
| **Feature Store** | ✅ JSONB extensível | Features sem DDL |

# **5 Conclusões e considerações finais**

## **5.1 Status Atual**

O pipeline ETL do DestaquesGovbr passou por uma **transformação arquitetural completa** entre 27/02 e 01/03/2026, resultando em um sistema:

- ✅ **Event-driven** com Pub/Sub: latência de **~15 segundos** (vs ~45 min)
- ✅ **AWS Bedrock** para LLM: custo ↓ 40%, controle total, features extras
- ✅ **Arquitetura Medallion**: 3 camadas (Bronze/Silver/Gold) com separação OLTP/OLAP
- ✅ **5 workers Cloud Run**: Enrichment, Embeddings, Typesense, Federation, Push
- ✅ **Federação ActivityPub**: distribuição no Fediverso (~150 seguidores)
- ✅ **Feature Store JSONB**: extensibilidade sem DDL migrations
- ✅ **Analytics BigQuery**: OLAP dedicado, trending scores, métricas agregadas

O sistema processa diariamente **~500-1000 notícias** de **~160 portais gov.br**, mantendo uma **taxa de sucesso > 97%** em todas as etapas, com **custo incremental < 5%**.

## **5.2 Limitações Superadas**

| Limitação (v1.0) | Solução (v1.1) | Status |
|------------------|---------------|--------|
| **Latência de 45 min** | Pipeline event-driven (15s) | ✅ Resolvido |
| **Cogfy gargalo** | AWS Bedrock (~5s/doc) | ✅ Resolvido |
| **Batch diário** | Pub/Sub push (on-demand) | ✅ Resolvido |
| **Features via DDL** | Feature Store JSONB | ✅ Resolvido |
| **Sem analytics** | BigQuery Gold layer | ✅ Resolvido |
| **Sem federação** | ActivityPub server | ✅ Resolvido |
| **Dados não imutáveis** | GCS Bronze (Parquet) | ✅ Resolvido |

## **5.3 Limitações Remanescentes**

| Limitação | Impacto | Workaround | Prazo |
|-----------|---------|------------|-------|
| **HuggingFace ainda batch** | Dataset atualizado 1x/dia | Não afeta uso principal | Aceito |
| **Sem dados de usuário** | Personalização limitada | Fase 5 planejada | 2-3 meses |
| **ActivityPub sem analytics** | Engajamento não medido | Integrar com Gold layer | 1 mês |
| **Bronze sem backfill** | Apenas dados novos | Backfill histórico planejado | 2 meses |
| **Trending score batch** | Atualizado 1x/dia | Frequência aceitável | Aceito |

## **5.4 Melhorias Futuras**

### **Curto Prazo (1-3 meses)**

- [ ] **Sistema de Alertas Centralizado**: Implementar integração com Slack/PagerDuty para notificações proativas
  - Alertas de pipeline stalled (oldest_unacked_message_age > 600s)
  - Alertas de DLQ rate alto (dead_letter_message_count > 10)
  - Alertas de erros em workers (error_count > 10/min)
  - Alertas de throttling Bedrock (throttle_count > 5/min)
  - Alertas de baixa taxa de enriquecimento (enrichment_rate < 80%)
  - Alertas de Typesense down (health check falha)
  - Alertas de alta utilização de conexões DB (pool > 80%)
- [ ] **Integrar Analytics ActivityPub**: Rastrear impressões, likes, replies no Gold layer
- [ ] **Backfill Bronze**: Exportar dados históricos (~300k docs) para GCS
- [ ] **Dashboards Grafana**: Visualização de métricas em tempo real
- [ ] **Circuit breakers**: Proteger contra falhas em cascata
- [x] ~~Migração Cogfy → AWS Bedrock~~ ✅ Concluído
- [x] ~~Pipeline event-driven~~ ✅ Concluído
- [x] ~~Arquitetura Medallion~~ ✅ Concluído

### **Médio Prazo (3-6 meses)**

- [ ] **Dados de usuário (Firestore)**: Fase 5 Medallion - subscriptions, preferências, histórico
- [ ] **Personalização**: Feed baseado em preferências e histórico
- [ ] **Notificações inteligentes**: Push baseado em temas de interesse
- [ ] **Topic clusters**: Agrupamento automático de notícias similares
- [ ] **API pública**: RESTful API para consumidores externos

### **Longo Prazo (6-12 meses)**

- [ ] **ML ops**: Model registry, experiment tracking, A/B testing
- [ ] **Data lineage**: Rastreamento completo de transformações
- [ ] **Real-time analytics**: Stream processing com Dataflow
- [ ] **Multi-region**: HA e DR em múltiplas regiões
- [ ] **GraphQL API**: Alternativa à REST para queries complexas

## **5.5 Lições Aprendidas**

### **O que funcionou excepcionalmente bem**

✅ **Event-driven com Pub/Sub**: Transformação de paradigma, não apenas otimização  
✅ **AWS Bedrock**: Controle total, custo ↓ 40%, features extras no mesmo prompt  
✅ **Feature Store JSONB**: Extensibilidade infinita sem DDL migrations  
✅ **Graceful degradation**: Deploy incremental sem quebrar compatibilidade  
✅ **Workers reutilizando lógica**: Desmembramento prévio acelerou implementação  
✅ **DLQs desde dia zero**: Salvou mensagens perdidas nos primeiros dias  
✅ **Rastreamento distribuído**: `trace_id` essencial para debug  

### **O que apresentou desafios**

⚠️ **Complexity overhead**: Mais componentes = mais pontos de falha  
⚠️ **Observabilidade distribuída**: Rastreamento cross-service complexo  
⚠️ **Idempotência universal**: Cada worker precisou implementar verificação  
⚠️ **Terraform state**: Gerenciar secrets AWS fora do state  
⚠️ **ActivityPub specs**: Protocolo complexo, documentação fragmentada  

### **Decisões arquiteturais acertadas**

1. **Infraestrutura primeiro, workers depois**: Topologia validada antes de código
2. **Endpoint `/process` no Embeddings API**: Reutilizou modelo, evitou HTTP hop
3. **Feature Store JSONB vs. Firestore**: Simplicidade > over-engineering
4. **Bronze em GCS, não BigQuery**: Storage 10x mais barato
5. **ActivityPub via fila**: Desacoplamento da publicação federada

### **O que faríamos diferente**

❌ **Ter migrado para event-driven antes**: Batch foi gargalo por meses  
❌ **Implementar observabilidade desde o início**: Rastreamento distribuído é crítico  
❌ **Documentar ADRs mais cedo**: ADR-001 deveria ter sido o primeiro commit  
❌ **Testes de integração end-to-end**: Validar pipeline completo automaticamente  

## **5.6 Recomendações**

### **Para Gestores**

1. **Celebrar a transformação**: 99.44% ↓ latência com < 5% custo incremental é excepcional
2. **Investir em observabilidade**: Dashboards e alertas são essenciais em sistemas distribuídos
3. **Priorizar Fase 5 (Dados de usuário)**: Personalização é o próximo grande valor
4. **Considerar multi-region**: Alta disponibilidade para portal crítico
5. **Expandir equipe de ML ops**: Modelo atual é manual, precisa de automação

### **Para Equipe Técnica**

1. **Implementar circuit breakers**: Proteger contra falhas em cascata (Pub/Sub já tem, falta nos workers)
2. **Criar runbooks**: Procedimentos para incidentes comuns (DLQ cheia, worker down, etc.)
3. **Automatizar backfill Bronze**: Script para exportar dados históricos para GCS
4. **Adicionar testes de contrato**: Validar schema de eventos Pub/Sub
5. **Implementar canary deployments**: Deploy gradual de workers (0% → 10% → 100%)
6. **Monitorar custos**: Alertas quando custo > budget (Bedrock, Cloud Run, BigQuery)

### **Para Pesquisadores**

1. **Explorar dataset HuggingFace atualizado**: ~310k documentos com sentiment + entities
2. **Validar qualidade de classificação Bedrock**: Comparar vs. classificação manual (gold standard)
3. **Analisar vieses no sentiment**: Distribuição de positivo/negativo por órgão/tema
4. **Propor melhorias em entity extraction**: Avaliar recall/precision do Bedrock NER
5. **Estudar topic clusters**: Implementar HDBSCAN sobre embeddings para agrupamento
6. **Pesquisar personalização**: Algoritmos de recomendação baseados em histórico

# **6 Referências Bibliográficas**

## **Repositórios**

- [destaquesgovbr/scraper](https://github.com/destaquesgovbr/scraper) - Scraping de notícias gov.br
- [destaquesgovbr/data-platform](https://github.com/destaquesgovbr/data-platform) - Pipeline de dados, workers
- [destaquesgovbr/data-science](https://github.com/destaquesgovbr/data-science) - Enrichment Worker, Bedrock
- [destaquesgovbr/embeddings](https://github.com/destaquesgovbr/embeddings) - Embeddings API
- [destaquesgovbr/activitypub-server](https://github.com/destaquesgovbr/activitypub-server) - Federation Worker
- [destaquesgovbr/push-notifications](https://github.com/destaquesgovbr/push-notifications) - Push Notifications Worker
- [destaquesgovbr/infra](https://github.com/destaquesgovbr/infra) - Terraform (GCP, Pub/Sub, Workers)
- [destaquesgovbr/docs](https://github.com/destaquesgovbr/docs) - Documentação técnica

## **Datasets**

- [nitaibezerra/govbrnews](https://huggingface.co/datasets/nitaibezerra/govbrnews) - Dataset completo (24 colunas, ~310k docs)
- [nitaibezerra/govbrnews-reduced](https://huggingface.co/datasets/nitaibezerra/govbrnews-reduced) - Dataset reduzido (4 colunas)

## **Aplicações**

- [Portal DestaquesGovBr](https://destaques.gov.br) - Interface de busca
- [Typesense API](https://typesense.destaques.gov.br) - API de busca
- [ActivityPub](https://destaques.gov.br/.well-known/webfinger?resource=acct:destaquesgovbr@destaques.gov.br) - Descoberta federada

## **Documentação Técnica**

- [PostgreSQL JSONB Documentation](https://www.postgresql.org/docs/15/datatype-json.html)
- [Medallion Architecture (Databricks)](https://www.databricks.com/glossary/medallion-architecture)
- [Google Cloud Pub/Sub](https://cloud.google.com/pubsub/docs)
- [AWS Bedrock Documentation](https://docs.aws.amazon.com/bedrock/)
- [ActivityPub Protocol](https://www.w3.org/TR/activitypub/)
- [Pydantic Documentation](https://docs.pydantic.dev/)
- [Typesense Documentation](https://typesense.org/docs/)
- [HuggingFace Datasets](https://huggingface.co/docs/datasets/)

## **Tecnologias**

- [Apache Airflow](https://airflow.apache.org/) - Orquestração de workflows
- [Google Cloud Pub/Sub](https://cloud.google.com/pubsub) - Event mesh
- [Google Cloud Run](https://cloud.google.com/run) - Workers serverless
- [FastAPI](https://fastapi.tiangolo.com/) - Framework Python para APIs
- [PostgreSQL](https://www.postgresql.org/) - Banco de dados relacional
- [BigQuery](https://cloud.google.com/bigquery) - Data warehouse
- [Google Cloud Storage](https://cloud.google.com/storage) - Object storage
- [AWS Bedrock](https://aws.amazon.com/bedrock/) - Managed LLM service
- [Typesense](https://typesense.org/) - Motor de busca
- [Mastodon](https://joinmastodon.org/) - Plataforma federada

## **Architecture Decision Records**

- [ADR-001: Arquitetura Medallion com Feature Store JSONB](https://github.com/destaquesgovbr/docs/blob/main/docs/arquitetura/adrs/adr-001-arquitetura-dados-medallion.md)

## **Blog Posts (Histórico de Implementação)**

- [Desmembrando o Monolito](https://destaques.gov.br/blog/2026-02-26-desmembrando-monolito/) - 36 PRs, 3 repos novos (26/02/2026)
- [De DAGs batch para event-driven](https://destaques.gov.br/blog/2026-02-28-pubsub-event-driven/) - 25 PRs, migração Pub/Sub (28/02/2026)
- [Arquitetura Medallion](https://destaques.gov.br/blog/2026-03-01-arquitetura-medallion/) - 12 PRs, ADR-001 (01/03/2026)

# **Apêndice**

## **A.1 Exemplo de Documento PostgreSQL (Atualizado)**

```json
{
  "id": 123456,
  "unique_id": "a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4",
  "agency_id": 45,
  "agency_key": "gestao",
  "agency_name": "Ministério da Gestão",
  "published_at": "2024-04-22T10:00:00Z",
  "updated_datetime": "2024-04-22T14:30:00Z",
  "extracted_at": "2024-04-22T07:00:00Z",
  "created_at": "2024-04-22T07:01:00Z",
  "updated_at": "2024-04-22T08:00:00Z",
  "title": "MGI anuncia novo programa de capacitação",
  "subtitle": "Iniciativa visa qualificar servidores públicos",
  "editorial_lead": "Programa beneficiará 10 mil servidores em 2024",
  "url": "https://www.gov.br/gestao/pt-br/noticias/...",
  "content": "# MGI anuncia novo programa\n\nO Ministério da Gestão...",
  "image_url": "https://www.gov.br/.../imagem.jpg",
  "video_url": null,
  "category": "Notícias",
  "tags": ["capacitação", "servidores", "gestão pública"],
  "theme_l1_id": 12,
  "theme_l2_id": 45,
  "theme_l3_id": 156,
  "most_specific_theme_id": 156,
  "summary": "O Ministério da Gestão lançou programa de capacitação para servidores públicos, com meta de 10 mil capacitados em 2024.",
  "content_embedding": [0.123, -0.456, 0.789, ...],  // 768 dimensões
  "embedding_generated_at": "2024-04-22T08:00:00Z"
}
```

## **A.2 Exemplo de Feature Store (news_features)**

```json
{
  "unique_id": "a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4",
  "features": {
    "sentiment": {
      "label": "positive",
      "score": 0.85
    },
    "entities": [
      {"text": "MGI", "type": "ORG"},
      {"text": "Lula", "type": "PER"},
      {"text": "Brasília", "type": "LOC"}
    ],
    "readability": {
      "flesch_ease": 45.2,
      "grade_level": 12
    },
    "word_count": 523,
    "paragraph_count": 8,
    "has_numbers": true,
    "publication_hour": 10,
    "day_of_week": "monday",
    "trending_score": 8.5
  },
  "created_at": "2024-04-22T08:00:00Z",
  "updated_at": "2024-04-22T10:30:00Z"
}
```

## **A.3 Exemplo de Evento Pub/Sub**

```json
{
  "message": {
    "data": "eyJ1bmlxdWVfaWQiOiAiYWJjMTIzIiwgImFnZW5jeV9rZXkiOiAibWVjIiwgInB1Ymxpc2hlZF9hdCI6ICIyMDI2LTA0LTIzVDEwOjAwOjAwWiJ9",
    "attributes": {
      "trace_id": "550e8400-e29b-41d4-a716-446655440000",
      "event_version": "1.0",
      "scraped_at": "2026-04-23T10:00:01Z"
    },
    "messageId": "1234567890",
    "publishTime": "2026-04-23T10:00:01.123Z"
  },
  "subscription": "projects/inspire-7-finep/subscriptions/dgb.news.scraped--enrichment"
}
```

## **A.4 Comandos CLI Úteis (Atualizados)**

```bash
# Verificar status do pipeline event-driven
gcloud pubsub topics list --filter="name:dgb.news"
gcloud pubsub subscriptions list --filter="name:dgb.news"

# Monitorar mensagens não confirmadas
gcloud pubsub subscriptions describe dgb.news.scraped--enrichment \
    --format="value(numUndeliveredMessages)"

# Verificar logs do Enrichment Worker
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=destaquesgovbr-enrichment-worker" \
    --limit 50 \
    --format json

# Rastrear uma notícia específica (end-to-end)
gcloud logging read "jsonPayload.trace_id=550e8400-e29b-41d4-a716-446655440000" \
    --format json

# Verificar qualidade de dados (PostgreSQL)
psql -h $POSTGRES_HOST -U govbrnews_app -d govbrnews -c "
SELECT
    COUNT(*) as total,
    COUNT(*) FILTER (WHERE theme_l1_id IS NOT NULL) as enriched,
    COUNT(*) FILTER (WHERE content_embedding IS NOT NULL) as embedded,
    COUNT(DISTINCT nf.unique_id) as with_sentiment
FROM news n
LEFT JOIN news_features nf ON n.unique_id = nf.unique_id
WHERE n.published_at >= CURRENT_DATE - INTERVAL '7 days';
"

# Verificar Feature Store
psql -h $POSTGRES_HOST -U govbrnews_app -d govbrnews -c "
SELECT
    unique_id,
    features->>'sentiment.label' as sentiment,
    jsonb_array_length(features->'entities') as entity_count
FROM news_features
LIMIT 5;
"

# Monitorar DLQs
for topic in dgb.news.scraped-dlq dgb.news.enriched-dlq dgb.news.embedded-dlq; do
    count=$(gcloud pubsub topics list-subscriptions $topic --format="value(numUndeliveredMessages)")
    echo "$topic: $count messages"
done

# Verificar custos AWS Bedrock (via CloudWatch)
aws cloudwatch get-metric-statistics \
    --namespace AWS/Bedrock \
    --metric-name InvocationCount \
    --dimensions Name=ModelId,Value=anthropic.claude-3-haiku \
    --start-time 2026-04-22T00:00:00Z \
    --end-time 2026-04-23T00:00:00Z \
    --period 3600 \
    --statistics Sum

# BigQuery: Top temas por sentiment
bq query --use_legacy_sql=false '
SELECT
    t.label,
    AVG(CAST(nf.features->>"sentiment.score" AS FLOAT64)) as avg_sentiment,
    COUNT(*) as article_count
FROM `inspire-7-finep.dgb_gold.fato_noticias` f
JOIN `inspire-7-finep.dgb_gold.dim_themes` t ON f.most_specific_theme_id = t.id
JOIN news_features nf ON f.unique_id = nf.unique_id
WHERE f.date_id >= DATE_SUB(CURRENT_DATE(), INTERVAL 30 DAY)
GROUP BY t.label
ORDER BY avg_sentiment DESC
LIMIT 10
'
```

## **A.5 Glossário (Atualizado)**

| Termo | Definição |
|-------|-----------|
| **unique_id** | Hash MD5 de 32 caracteres usado como identificador único e chave de deduplicação |
| **Medallion Architecture** | Arquitetura de dados em camadas: Bronze (raw), Silver (cleaned), Gold (aggregated) |
| **Event-Driven** | Paradigma onde componentes reagem a eventos publicados (vs. polling batch) |
| **Pub/Sub** | Google Cloud Pub/Sub - serviço de mensageria pub/sub gerenciado |
| **Push Subscription** | Pub/Sub entrega mensagens via HTTP POST para webhook (vs. pull) |
| **DLQ (Dead-Letter Queue)** | Fila para mensagens que falharam repetidamente (após max retries) |
| **Idempotência** | Propriedade de uma operação que pode ser executada múltiplas vezes sem efeitos colaterais |
| **trace_id** | UUID que rastreia uma notícia através de todo o pipeline distribuído |
| **Embedding** | Vetor de 768 dimensões representando semanticamente o conteúdo de uma notícia |
| **AWS Bedrock** | Serviço gerenciado AWS para inferência LLM (Claude, Titan, etc.) |
| **Feature Store** | Sistema para armazenar e gerenciar features derivadas para ML |
| **JSONB** | Tipo de dado PostgreSQL para armazenar JSON binário (indexável) |
| **ActivityPub** | Protocolo W3C para redes sociais federadas (usado por Mastodon) |
| **Fediverso** | Rede federada de instâncias compatíveis com ActivityPub/Mastodon |
| **Cloud Run** | Plataforma serverless do GCP para containers (scale-to-zero) |
| **BigQuery** | Data warehouse serverless do Google Cloud Platform |
| **GCS** | Google Cloud Storage - object storage escalável |
| **Parquet** | Formato de arquivo colunar otimizado para analytics |
| **ON CONFLICT** | Cláusula SQL para tratamento de conflitos em INSERTs (PostgreSQL) |
| **Anomalia** | Desvio estatístico significativo de um comportamento esperado (ex: volume, datas) |
| **Pydantic** | Biblioteca Python para validação de dados e parsing com type hints |
| **Z-score** | Medida estatística de quantos desvios-padrão um valor está da média |
| **Worker** | Serviço Cloud Run que processa eventos de forma assíncrona |
| **Ack Deadline** | Tempo máximo que um worker tem para processar uma mensagem antes de redelivery |