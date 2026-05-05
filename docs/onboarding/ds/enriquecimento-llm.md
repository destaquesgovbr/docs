# Onboarding: Enriquecimento de Notícias com AWS Bedrock

Guia prático para desenvolvedores que vão trabalhar com o sistema de enriquecimento de notícias usando Large Language Models (LLMs) via AWS Bedrock.

---

## 📋 Pré-requisitos

Antes de começar, você deve ter:

- [x] Python 3.11+ instalado
- [x] Poetry instalado (`pip install poetry`)
- [x] Acesso ao repositório [`data-science`](https://github.com/inspire-cria/data-science)
- [x] Credenciais AWS com acesso ao Bedrock
- [x] Acesso ao PostgreSQL (Cloud SQL)
- [x] VPN/acesso à rede interna (se necessário)

---

## 🚀 Setup Inicial (30 minutos)

### 1. Clone e configure o repositório

```bash
# Clone
git clone https://github.com/inspire-cria/data-science.git
cd data-science

# Instale dependências
poetry install

# Ative o ambiente virtual
poetry shell
```

### 2. Configure variáveis de ambiente

Crie o arquivo `.env` na raiz do repositório:

```bash
# .env

# AWS Bedrock
AWS_ACCESS_KEY_ID=AKIA...
AWS_SECRET_ACCESS_KEY=...
AWS_DEFAULT_REGION=us-east-1

# PostgreSQL (Silver Layer)
POSTGRES_HOST=10.x.x.x  # IP privado Cloud SQL
POSTGRES_PORT=5432
POSTGRES_DB=destaquesgovbr
POSTGRES_USER=seu_usuario
POSTGRES_PASSWORD=...

# Opcional: para testes locais com Ollama
OLLAMA_API_BASE=http://localhost:11434
```

**⚠️ IMPORTANTE**: Nunca commite o arquivo `.env` no Git! Ele já está no `.gitignore`.

### 3. Teste a conexão AWS Bedrock

```bash
# Verificar identidade AWS
aws sts get-caller-identity

# Listar modelos disponíveis
aws bedrock list-foundation-models --region us-east-1 | grep claude
```

**Esperado**: Você deve ver Claude 3 Haiku, Sonnet e Opus disponíveis.

### 4. Teste o classificador

```bash
cd source/news-enrichment

# Exemplo simples
python examples/classificacao_simples.py
```

**Esperado**: Uma notícia deve ser classificada em ~5-10 segundos sem erros.

---

## 🎯 Conceitos Fundamentais

### Taxonomia Hierárquica (543 categorias)

O sistema usa uma taxonomia de **3 níveis**:

```
01 - Economia                              # Nível 1 (10 temas principais)
  ├─ 01.01 - Política Econômica           # Nível 2 (~50 subtemas)
  │   ├─ 01.01.01 - Política Fiscal       # Nível 3 (~410 categorias específicas)
  │   ├─ 01.01.02 - Política Monetária
  │   └─ 01.01.03 - Política Cambial
  └─ 01.02 - Setor Produtivo
      ├─ 01.02.01 - Agropecuária
      └─ 01.02.02 - Indústria
```

**Arquivo**: [`arvore.yaml`](https://github.com/inspire-cria/themes/blob/main/themes_tree.yaml)

**Como funciona**:
1. LLM recebe a taxonomia completa no prompt
2. LLM classifica a notícia nos 3 níveis
3. Sistema valida e armazena no PostgreSQL

### Providers LLM Suportados

| Provider | Modelo | Uso | Custo/1k docs |
|----------|--------|-----|---------------|
| **AWS Bedrock** (prod) | Claude 3 Haiku | Produção | $0.74 |
| **AWS Bedrock** | Claude 3 Sonnet | Alta qualidade | $3.00 |
| **AWS Bedrock** | Claude 3 Opus | Máxima qualidade | $15.00 |
| **Ollama** (dev) | Llama 3.1 70B | Testes locais | Grátis |
| **Ollama** (dev) | Qwen 2.5 72B | Testes locais | Grátis |

**Recomendação**: Use **Claude 3 Haiku** para produção (melhor custo-benefício).

---

## 🛠️ Componentes Principais

### 1. `llm_client.py` - Cliente Base

```python
from news_enrichment import BedrockLLMClient

# Inicializar cliente
client = BedrockLLMClient(
    model_id="anthropic.claude-3-haiku-20240307-v1:0",
    region="us-east-1",
    batch_size=8,          # Processa 8 notícias por vez
    max_workers=4,         # 4 threads paralelas
    sleep_between_batches=0.2  # 200ms entre batches (evitar throttling)
)

# Classificar uma notícia
news = {
    "title": "Governo anuncia reforma tributária",
    "content": "O governo federal apresentou hoje..."
}

result = client.classify_single(news)
```

**Saída**:
```python
{
    "theme_level_1": "01 - Economia",
    "theme_level_2": "01.01 - Política Econômica",
    "theme_level_3": "01.01.01 - Política Fiscal",
    "most_specific_theme": "01.01.01",
    "summary": "Governo apresenta proposta de reforma tributária...",
    "confidence": 0.95
}
```

### 2. `llm_client_optimized.py` - Cliente Otimizado

```python
from news_enrichment.llm_client_optimized import LLMClientOptimized

# Cliente com otimizações para alto volume
client = LLMClientOptimized(
    model_id="anthropic.claude-3-haiku-20240307-v1:0",
    region="us-east-1",
    batch_size=6,          # ← Menor que o base (mais estável)
    max_workers=4,
    sleep_between_batches=0.3  # ← Maior que o base (evita throttling)
)

# Processar batch
news_list = [news1, news2, news3, ...]
results = client.enrich_news_batch(news_list)
```

**Quando usar**:
- Volumes > 1000 notícias/dia
- Precisa de processamento contínuo sem interrupções
- Quer minimizar throttling AWS

### 3. `taxonomy.py` - Carregamento de Taxonomia

```python
from news_enrichment.taxonomy import load_taxonomy_from_postgres

# Carregar taxonomia (cached)
taxonomy = load_taxonomy_from_postgres(
    conn_string="postgresql://user:pass@host:5432/db"
)

print(f"Total de temas: {len(taxonomy['themes'])}")  # 543
print(f"Nível 1: {len([t for t in taxonomy['themes'] if t['level'] == 1])}")  # 10
print(f"Nível 2: {len([t for t in taxonomy['themes'] if t['level'] == 2])}")  # ~50
print(f"Nível 3: {len([t for t in taxonomy['themes'] if t['level'] == 3])}")  # ~410
```

**⚡ Performance**: Taxonomia é carregada 1x na inicialização usando `@lru_cache`.

### 4. `enrichment_job.py` - Job de Enriquecimento

```python
from news_enrichment.enrichment_job import fetch_unenriched_news, update_enriched_news
import psycopg2

# Conectar ao PostgreSQL
conn = psycopg2.connect(
    host="10.x.x.x",
    port=5432,
    dbname="destaquesgovbr",
    user="enrichment_worker",
    password="..."
)

# Buscar notícias não enriquecidas
unenriched = fetch_unenriched_news(conn, limit=100)
print(f"Encontradas {len(unenriched)} notícias para enriquecer")

# Enriquecer
results = client.enrich_news_batch(unenriched)

# Atualizar PostgreSQL
update_enriched_news(conn, results)
conn.commit()
```

**Idempotência**: A função `fetch_unenriched_news()` verifica se `most_specific_theme_id IS NULL OR summary IS NULL`.

---

## 📊 Exercícios Práticos

### Exercício 1: Classificar uma notícia (5 min)

```python
from news_enrichment import BedrockLLMClient

client = BedrockLLMClient()

news = {
    "title": "Ministério da Saúde lança campanha de vacinação contra gripe",
    "content": "O Ministério da Saúde anunciou hoje o início da campanha nacional de vacinação contra gripe para 2026. A meta é imunizar 90% do público-alvo, incluindo idosos, crianças e profissionais de saúde."
}

result = client.classify_single(news)

# Verifique:
# - theme_level_1 deve ser "03 - Saúde"
# - theme_level_3 deve ser algo como "03.03.01 - Prevenção e Controle de Doenças"
print(result)
```

### Exercício 2: Processar batch (10 min)

Crie um arquivo `test_batch.py`:

```python
from news_enrichment import BedrockLLMClient
import json

# Carregar amostra (você deve ter um arquivo sample.json com 10 notícias)
with open('sample.json') as f:
    news_list = json.load(f)

client = BedrockLLMClient(batch_size=5, max_workers=2)

results = client.enrich_news_batch(news_list)

# Análise
for i, result in enumerate(results, 1):
    print(f"\nNotícia {i}:")
    print(f"  Tema L1: {result['theme_level_1']}")
    print(f"  Tema L3: {result['theme_level_3']}")
    print(f"  Resumo: {result['summary'][:100]}...")
```

**Esperado**: 10 notícias processadas em ~30-60 segundos.

### Exercício 3: Comparar Haiku vs Sonnet (15 min)

```python
from news_enrichment import BedrockLLMClient
import time

news = {
    "title": "Reforma da Previdência aprovada no Senado",
    "content": "O Senado Federal aprovou hoje a proposta de reforma da Previdência Social..."
}

# Testar Haiku
client_haiku = BedrockLLMClient(
    model_id="anthropic.claude-3-haiku-20240307-v1:0"
)
start = time.time()
result_haiku = client_haiku.classify_single(news)
time_haiku = time.time() - start

# Testar Sonnet
client_sonnet = BedrockLLMClient(
    model_id="anthropic.claude-3-sonnet-20240229-v1:0"
)
start = time.time()
result_sonnet = client_sonnet.classify_single(news)
time_sonnet = time.time() - start

# Comparar
print(f"Haiku: {time_haiku:.2f}s - Tema: {result_haiku['theme_level_3']}")
print(f"Sonnet: {time_sonnet:.2f}s - Tema: {result_sonnet['theme_level_3']}")
print(f"\nDiferença de custo: {(time_sonnet/time_haiku - 1) * 100:.0f}% mais caro")
```

### Exercício 4: Usar Ollama Local (20 min)

**Pré-requisito**: Instalar Ollama ([ollama.ai](https://ollama.ai))

```bash
# Instalar Ollama
curl -fsSL https://ollama.ai/install.sh | sh

# Baixar modelo
ollama pull llama3.1:70b  # ~40GB, pode demorar

# Iniciar servidor
ollama serve
```

```python
from news_enrichment.local_llm_client import LocalLLMClient

client = LocalLLMClient(
    provider="ollama",
    model="llama3.1:70b",
    api_base="http://localhost:11434"
)

news = {
    "title": "Governo anuncia aumento do salário mínimo",
    "content": "O governo federal anunciou reajuste do salário mínimo..."
}

result = client.classify_single(news)
print(result)
```

**Observação**: Ollama é **MUITO MAIS LENTO** que Bedrock (~30s vs 5s), mas é grátis e roda localmente.

---

## 🎓 Conceitos Avançados

### Batch Sizing e Paralelização

**Trade-off**: Batch size maior = mais rápido, mas maior risco de throttling.

```python
# Configuração conservadora (recomendada para início)
client = BedrockLLMClient(
    batch_size=8,
    max_workers=4,
    sleep_between_batches=0.2
)
# → ~200-300 docs/min

# Configuração agressiva (apenas se não houver throttling)
client = BedrockLLMClient(
    batch_size=16,
    max_workers=8,
    sleep_between_batches=0.1
)
# → ~400-600 docs/min (mas pode dar ThrottlingException)
```

### Retry Policy

O cliente implementa retry automático:

```python
# Em llm_client.py (linhas 71-100)
for attempt in range(1, self.max_retries + 1):
    try:
        response = self.bedrock.invoke_model(...)
        return response
    except ThrottlingException:
        if attempt < self.max_retries:
            sleep_time = 2 ** attempt  # 1s, 2s, 4s
            time.sleep(sleep_time)
            continue
        raise
    except ValidationException:
        # Não retenta (erro de input)
        raise
```

### Cost Estimation

```python
def estimate_cost(num_docs: int, model: str = "haiku") -> float:
    """
    Estima custo de processamento.
    
    Preços AWS Bedrock (maio 2026):
    - Haiku: $0.00074/doc
    - Sonnet: $0.003/doc
    - Opus: $0.015/doc
    """
    costs = {
        "haiku": 0.00074,
        "sonnet": 0.003,
        "opus": 0.015
    }
    return num_docs * costs.get(model, 0.00074)

# Exemplo
print(f"Processar 100k docs com Haiku: ${estimate_cost(100_000, 'haiku'):.2f}")
# → $74.00

print(f"Processar 100k docs com Sonnet: ${estimate_cost(100_000, 'sonnet'):.2f}")
# → $300.00
```

---

## 🐛 Troubleshooting

### Erro: "AccessDeniedException"

**Causa**: Credenciais AWS sem permissão para Bedrock.

**Solução**:
```bash
# Verificar identidade
aws sts get-caller-identity

# Verificar se tem acesso ao Bedrock
aws bedrock list-foundation-models --region us-east-1
```

Se der erro, peça ao admin AWS para adicionar a política `AmazonBedrockFullAccess` ao seu usuário.

### Erro: "ThrottlingException"

**Causa**: Muitas requisições simultâneas ao Bedrock.

**Solução**:
```python
# Reduzir paralelização
client = BedrockLLMClient(
    batch_size=4,        # ← Reduzir de 8 para 4
    max_workers=2,       # ← Reduzir de 4 para 2
    sleep_between_batches=0.5  # ← Aumentar de 0.2 para 0.5
)
```

### Erro: "ValidationException: The provided model identifier is invalid"

**Causa**: Modelo não disponível na região.

**Solução**:
```bash
# Verificar modelos disponíveis
aws bedrock list-foundation-models --region us-east-1 | jq '.modelSummaries[] | select(.modelId | contains("claude"))'

# Usar ID correto
model_id="anthropic.claude-3-haiku-20240307-v1:0"  # ← versão correta
```

### Problema: Latência alta (>20s por notícia)

**Causas possíveis**:
- Conteúdo muito longo (>10k caracteres)
- Throttling AWS
- Rede lenta

**Diagnóstico**:
```python
import time

start = time.time()
result = client.classify_single(news)
elapsed = time.time() - start

print(f"Tempo: {elapsed:.2f}s")
print(f"Tamanho conteúdo: {len(news['content'])} chars")

if elapsed > 20:
    print("⚠️ Latência alta detectada!")
    if len(news['content']) > 10000:
        print("  → Conteúdo muito longo. Considere truncar.")
```

### Problema: Taxonomia não carregada

**Sintoma**: Erro `KeyError: 'themes'` ou classificação incorreta.

**Solução**:
```python
from news_enrichment.taxonomy import load_taxonomy_from_postgres

# Verificar se carregou
taxonomy = load_taxonomy_from_postgres(conn_string)
assert len(taxonomy['themes']) == 543, "Taxonomia incompleta!"

print(f"✅ Taxonomia carregada: {len(taxonomy['themes'])} temas")
```

---

## 📚 Documentação Relacionada

### Interna
- [News Enrichment Worker](../../modulos/news-enrichment-worker.md) - Arquitetura do worker
- [Pub/Sub Workers](../../arquitetura/pubsub-workers.md) - Arquitetura event-driven
- [Credenciais AWS Bedrock](../../seguranca/credenciais-aws-bedrock.md) - Gerenciamento de credenciais
- [Workers Pub/Sub](./workers-pubsub.md) - Template para criar novos workers

### Externa
- [AWS Bedrock Documentation](https://docs.aws.amazon.com/bedrock/)
- [Claude 3 Model Card](https://www.anthropic.com/claude-3)
- [Ollama Documentation](https://ollama.ai/docs)

---

## ✅ Checklist de Onboarding

Antes de começar a trabalhar em produção, certifique-se de ter completado:

- [ ] Setup inicial (clone, poetry install, .env configurado)
- [ ] Teste de conexão AWS Bedrock (`aws sts get-caller-identity`)
- [ ] Teste de classificação simples (Exercício 1)
- [ ] Teste de batch processing (Exercício 2)
- [ ] Comparação Haiku vs Sonnet (Exercício 3)
- [ ] Leitura da documentação do News Enrichment Worker
- [ ] Entendimento da taxonomia hierárquica (543 categorias)
- [ ] Acesso ao PostgreSQL Cloud SQL
- [ ] Code review de pelo menos 1 PR existente

---

## 🤝 Próximos Passos

1. **Tarefa Prática**: Pegar uma issue `good-first-issue` no GitHub
2. **Pair Programming**: Sessão com outro dev do time
3. **Deploy**: Acompanhar deploy do worker em staging
4. **Monitoramento**: Revisar dashboards Cloud Monitoring

---

**Dúvidas?** Consulte o time no Slack `#data-science` ou abra uma issue no GitHub.

**Última atualização**: 05/05/2026  
**Responsável**: Equipe Data Science - DestaquesGovbr