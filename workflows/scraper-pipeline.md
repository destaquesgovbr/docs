# Workflow: Pipeline do Scraper

> Pipeline diário de coleta e enriquecimento de notícias.

**Arquivo**: `govbrnews-scraper/.github/workflows/main-workflow.yaml`

## Visão Geral

O pipeline é executado diariamente às **4AM UTC** (1AM Brasília) e consiste em 5 jobs sequenciais:

```mermaid
flowchart LR
    A[scraper] --> B[ebc-scraper]
    B --> C[upload-to-cogfy]
    C --> D[wait-cogfy]
    D --> E[enrich-themes]
```

---

## Trigger

```yaml
on:
  schedule:
    - cron: '0 4 * * *'  # 4AM UTC diário
  workflow_dispatch:      # Manual
    inputs:
      min-date:
        description: 'Data inicial (YYYY-MM-DD)'
        required: false
      max-date:
        description: 'Data final (YYYY-MM-DD)'
        required: false
```

### Execução automática

- **Horário**: 4AM UTC (1AM Brasília)
- **Frequência**: Diária
- **Dias cobertos**: Últimos 3 dias (para capturar atualizações)

### Execução manual

Via GitHub Actions UI ou CLI:

```bash
# Últimos 3 dias (padrão)
gh workflow run main-workflow.yaml

# Período específico
gh workflow run main-workflow.yaml \
  -f min-date=2024-12-01 \
  -f max-date=2024-12-03
```

---

## Jobs Detalhados

### Job 1: `scraper`

Raspa notícias dos sites gov.br.

```yaml
scraper:
  runs-on: ubuntu-latest
  container:
    image: ghcr.io/destaquesgovbr/govbrnews-scraper:latest
  steps:
    - name: Scrape gov.br sites
      run: |
        python src/main.py scrape \
          --start-date ${{ inputs.min-date || steps.dates.outputs.min }} \
          --end-date ${{ inputs.max-date || steps.dates.outputs.max }}
      env:
        HF_TOKEN: ${{ secrets.HF_TOKEN }}
```

**Duração**: ~30-60 minutos (dependendo do período)

### Job 2: `ebc-scraper`

Raspa notícias dos sites EBC (Agência Brasil, etc).

```yaml
ebc-scraper:
  needs: scraper
  runs-on: ubuntu-latest
  container:
    image: ghcr.io/destaquesgovbr/govbrnews-scraper:latest
  steps:
    - name: Scrape EBC sites
      run: |
        python src/main.py scrape-ebc \
          --start-date ${{ inputs.min-date || steps.dates.outputs.min }} \
          --end-date ${{ inputs.max-date || steps.dates.outputs.max }} \
          --allow-update
      env:
        HF_TOKEN: ${{ secrets.HF_TOKEN }}
```

**Duração**: ~10-20 minutos

### Job 3: `upload-to-cogfy`

Envia notícias para classificação no Cogfy.

```yaml
upload-to-cogfy:
  needs: ebc-scraper
  runs-on: ubuntu-latest
  container:
    image: ghcr.io/destaquesgovbr/govbrnews-scraper:latest
  steps:
    - name: Upload to Cogfy
      run: |
        python src/upload_to_cogfy_manager.py \
          --start-date ${{ inputs.min-date || steps.dates.outputs.min }} \
          --end-date ${{ inputs.max-date || steps.dates.outputs.max }}
      env:
        HF_TOKEN: ${{ secrets.HF_TOKEN }}
        COGFY_API_KEY: ${{ secrets.COGFY_API_KEY }}
        COGFY_COLLECTION_ID: ${{ secrets.COGFY_COLLECTION_ID }}
```

**Duração**: ~5-10 minutos

### Job 4: `wait-cogfy`

Aguarda processamento no Cogfy.

```yaml
wait-cogfy:
  needs: upload-to-cogfy
  runs-on: ubuntu-latest
  steps:
    - name: Wait for Cogfy processing
      run: sleep 1200  # 20 minutos
```

**Duração**: 20 minutos (fixo)

### Job 5: `enrich-themes`

Busca resultados do Cogfy e atualiza dataset.

```yaml
enrich-themes:
  needs: wait-cogfy
  runs-on: ubuntu-latest
  container:
    image: ghcr.io/destaquesgovbr/govbrnews-scraper:latest
  steps:
    - name: Enrich with themes
      run: |
        python src/enrichment_manager.py \
          --start-date ${{ inputs.min-date || steps.dates.outputs.min }} \
          --end-date ${{ inputs.max-date || steps.dates.outputs.max }}
      env:
        HF_TOKEN: ${{ secrets.HF_TOKEN }}
        COGFY_API_KEY: ${{ secrets.COGFY_API_KEY }}
        COGFY_COLLECTION_ID: ${{ secrets.COGFY_COLLECTION_ID }}
```

**Duração**: ~10-20 minutos

---

## Diagrama de Sequência

```mermaid
sequenceDiagram
    participant GH as GitHub Actions
    participant SC as Scraper Container
    participant GOV as Sites gov.br
    participant EBC as Sites EBC
    participant HF as HuggingFace
    participant CF as Cogfy

    Note over GH: 4AM UTC - Trigger

    GH->>SC: Job: scraper
    SC->>GOV: Fetch ~100+ sites
    GOV-->>SC: HTML pages
    SC->>SC: Parse → Markdown
    SC->>HF: Insert articles

    GH->>SC: Job: ebc-scraper
    SC->>EBC: Fetch EBC sites
    EBC-->>SC: HTML pages
    SC->>HF: Insert/Update articles

    GH->>SC: Job: upload-to-cogfy
    SC->>HF: Load articles
    SC->>CF: POST records (batch)

    Note over GH: Wait 20 min

    GH->>SC: Job: enrich-themes
    SC->>CF: GET processed records
    CF-->>SC: Themes + Summary
    SC->>HF: Update with enrichment
```

---

## Secrets Necessárias

| Secret | Descrição | Usado em |
|--------|-----------|----------|
| `HF_TOKEN` | Token HuggingFace (write) | Todos os jobs |
| `COGFY_API_KEY` | API Key do Cogfy | upload, enrich |
| `COGFY_COLLECTION_ID` | ID da collection Cogfy | upload, enrich |

### Configurar secrets

```bash
# Via GitHub CLI
gh secret set HF_TOKEN --body "hf_xxxxx"
gh secret set COGFY_API_KEY --body "sk-xxxxx"
gh secret set COGFY_COLLECTION_ID --body "uuid-xxxxx"
```

---

## Monitoramento

### Ver status do workflow

```bash
# Listar execuções recentes
gh run list --workflow=main-workflow.yaml

# Ver detalhes de uma execução
gh run view <run_id>

# Ver logs
gh run view <run_id> --log
```

### Via interface GitHub

1. Acessar repositório no GitHub
2. Aba "Actions"
3. Selecionar "main-workflow"
4. Ver execuções e logs

---

## Tratamento de Erros

### Falha em scraping

- Jobs posteriores **não executam** (dependência)
- Artigos com erro são **skipados** (não bloqueia)
- Logs detalhados disponíveis

### Falha em upload Cogfy

- Retry automático (3 tentativas)
- Enriquecimento não executa
- Dados ficam sem classificação até próxima execução

### Falha em enriquecimento

- Dataset mantém dados sem enriquecimento
- Próxima execução pode recuperar

---

## Execução Manual (Dispatch)

### Para período específico

```bash
gh workflow run main-workflow.yaml \
  -f min-date=2024-01-01 \
  -f max-date=2024-01-31
```

### Para reprocessar

```bash
# Reprocessar últimos 7 dias
gh workflow run main-workflow.yaml \
  -f min-date=$(date -v-7d +%Y-%m-%d) \
  -f max-date=$(date +%Y-%m-%d)
```

---

## Workflow Separado: Dispatch

Existe também `scraper-dispatch.yaml` para execuções manuais isoladas:

```yaml
# scraper-dispatch.yaml
on:
  workflow_dispatch:
    inputs:
      min-date:
        required: true
      max-date:
        required: true
      job:
        type: choice
        options:
          - scrape
          - ebc-scrape
          - upload-cogfy
          - enrich
```

Uso:

```bash
# Apenas scraping
gh workflow run scraper-dispatch.yaml \
  -f min-date=2024-12-01 \
  -f max-date=2024-12-03 \
  -f job=scrape
```

---

## Duração Total

| Job | Duração Típica |
|-----|----------------|
| scraper | 30-60 min |
| ebc-scraper | 10-20 min |
| upload-to-cogfy | 5-10 min |
| wait-cogfy | 20 min (fixo) |
| enrich-themes | 10-20 min |
| **Total** | **~75-130 min** |

---

## Links Relacionados

- [Fluxo de Dados](../arquitetura/fluxo-de-dados.md) - Visão geral do pipeline
- [Módulo Scraper](../modulos/scraper.md) - Detalhes do scraper
- [Integração Cogfy](../modulos/cogfy-integracao.md) - Classificação LLM
- [Docker Builds](./docker-builds.md) - Build da imagem
