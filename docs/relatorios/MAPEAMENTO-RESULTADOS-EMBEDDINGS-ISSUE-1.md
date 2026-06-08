# Mapeamento de Resultados - Issue #1 (Embeddings)

**Data:** 08/06/2026  
**Repositório Analisado:** `C:\Users\joserm\Documents\Projetos\Inspire\Meta-7\Git\data-science`  
**Issue:** [#1 - Comparativo de Modelos de Embedding PT-BR](https://github.com/destaquesgovbr/data-science/issues/1)

---

## 🎯 Objetivo da Análise

Localizar e documentar os **resultados finais do experimento** de comparação de modelos de embedding PT-BR estabelecido no Issue #1, executado na branch `embeddings-study`.

---

## ⚠️ Esclarecimento Importante

O diretório solicitado (`source/news-enrichment`) **NÃO contém resultados do Issue #1 (Embeddings)**. 

**news-enrichment** é sobre:
- Enriquecimento de notícias com LLMs (Claude, GPT, Ollama)
- Classificação automática de notícias
- Geração de resumos e tags
- Extração de entidades

**Issue #1 (Embeddings)** é sobre:
- Modelos de embedding (sentence transformers)
- Busca semântica por similaridade de vetores
- Métricas NDCG@10, MAP, MRR
- Localizado em `source/embeddings/` (branch embeddings-study)

---

## 📁 Localização Correta dos Resultados

**Branch:** `embeddings-study`  
**Diretório:** `source/embeddings/`

### Estrutura de Arquivos Encontrada:

```
source/embeddings/
├── README.md                            # Documentação principal
├── notebooks/
│   ├── embedding_comparison.ipynb       # Análise principal (29KB)
│   └── metrics_analysis.ipynb           # Análise detalhada (1MB)
├── results/
│   ├── metrics/
│   │   ├── metrics_summary.csv          # ✅ RANKING FINAL
│   │   └── evaluation_results.json      # ✅ MÉTRICAS COMPLETAS
│   ├── embeddings/
│   │   ├── *.npy                        # Vetores gerados
│   │   └── *_stats.json                 # Estatísticas dos modelos
│   ├── visualizations/
│   │   ├── radar_comparison.png         # Comparação multidimensional
│   │   ├── ranking_by_metric.png        # Ranking visual
│   │   └── ndcg_distribution.png        # Distribuição NDCG
│   └── consistency/
│       └── consistency_results.json     # Validação de consistência
├── docs/
│   ├── METODOLOGIA_METRICAS.md (32KB)  # Validação do corpus
│   ├── METODOLOGIA_NDCG.md (18KB)      # Explicação NDCG
│   ├── METODOLOGIA_QUERIES.md (13KB)   # Justificativa queries
│   ├── ANALISE_CORPUS.md (6KB)         # Estatísticas corpus
│   ├── VALIDACAO_RANKING_BENCHMARKS.md # Validação externa
│   ├── QUERIES_EXPANDIDAS.md           # Queries testadas
│   ├── PAPERS_READING_LIST.md          # Referências científicas
│   └── ISSUE_02_FINE_TUNING_PLAN.md    # Próximos passos
├── scripts/
│   ├── load_models.py
│   ├── generate_embeddings.py
│   ├── evaluate_metrics.py
│   └── benchmark_speed.py
└── data/
    ├── queries/
    ├── documents/
    └── annotations/
```

---

## 📊 Resultados Principais Encontrados

### 1. Ranking Final (metrics_summary.csv)

| Posição | Modelo | Tipo | NDCG@10 | Status |
|---------|--------|------|---------|--------|
| **1º** | **bge-m3** | Multi | **0.9673** | ⭐ VENCEDOR |
| 2º | multilingual-e5-small | Multi | 0.8858 | - |
| 3º | multilingual-e5-base | Multi | 0.8670 | - |
| 4º | multilingual-e5-large | Multi | 0.8545 | - |
| 5º | labse | Multi | 0.7371 | - |
| 6º | serafim-900m-pt | PT-BR | 0.6502 | Melhor PT |
| 7º | paraphrase-mpnet | Multi | 0.5859 | - |
| 8º | paraphrase-miniml | Multi | 0.5049 | - |
| 9º | bertimbau | PT-BR | 0.4181 | Pior |

**Fonte:** `source/embeddings/results/metrics/metrics_summary.csv`

### 2. Métricas Completas (evaluation_results.json)

**BGE-M3 (Vencedor):**
- **NDCG@10:** 0.9673 (96.73%)
- **MAP:** 0.9006 (90.06%)
- **MRR:** 0.9961 (99.61%)
- **Recall@10:** 0.9992 (99.92%)

**Fonte:** `source/embeddings/results/metrics/evaluation_results.json`

### 3. Dataset Executado

- **Corpus:** 250 documentos (25 por categoria, 10 categorias)
- **Queries:** 259 queries (85 base + ~3 variantes)
- **Anotações:** 2.591 pares query-documento (escala 0-3)
- **Taxa de recuperação:** 99.6% com BGE-M3 (249/250 docs)

**Fonte:** README.md + METODOLOGIA_METRICAS.md

### 4. Hipótese do Issue #1

**Hipótese Original:**
> "Modelos específicos para português (BERTimbau, Serafim) podem superar modelos multilinguais (BGE-M3, E5) em tarefas de retrieval em notícias governamentais brasileiras."

**Resultado:** ❌ **HIPÓTESE REFUTADA**

**Evidências:**
- BGE-M3 (multilingual) superou TODOS os modelos PT-específicos
- Gap: +48.8% vs Serafim (melhor PT), +131.4% vs BERTimbau
- Top 5 modelos: 100% multilinguais

---

## 📄 Documentos Finais Planejados vs Criados

### Planejados (no README.md):

1. ❌ `docs/RESEARCH_EMBEDDING_MODELS.md` - **NÃO CRIADO**
2. ❌ `docs/presentation_embedding_models.pdf` - **NÃO CRIADO**

### Criados no Repositório `docs`:

1. ✅ **Relatório-Ciencia-de-Dados-Embeddings-26-05-Versao-02.md**
   - Localização: `relatorios/`
   - Tamanho: 1.907 linhas
   - Status: Publicado (commit 4a19aec)
   - Conteúdo: **TODOS OS RESULTADOS DO ISSUE #1**

2. ✅ **RESUMO-EXECUTIVO-RESULTADOS-EMBEDDINGS.md**
   - Resumo de 1 página
   - Localização: `relatorios/`

3. ✅ **SECOES-ATUALIZADAS-V02.md**
   - Seções críticas isoladas
   - Localização: `relatorios/`

4. ✅ **CHECKLIST-23-ITENS-COMPLETO.md**
   - Verificação dos 23 requisitos
   - Localização: `relatorios/`

---

## 🎯 Conclusão

### Os resultados finais do Issue #1 estão em 3 locais:

1. **Dados Brutos (data-science repo):**
   - `source/embeddings/results/metrics/metrics_summary.csv`
   - `source/embeddings/results/metrics/evaluation_results.json`
   - `source/embeddings/results/visualizations/*.png`

2. **Análises (data-science repo):**
   - `source/embeddings/notebooks/embedding_comparison.ipynb`
   - `source/embeddings/notebooks/metrics_analysis.ipynb`

3. **Relatório Final (docs repo):**
   - **`relatorios/Relatório-Ciencia-de-Dados-Embeddings-26-05-Versao-02.md`**
   - Este é o documento técnico completo que consolida TODOS os resultados

---

## 📌 Recomendação

**O Relatório V02 JÁ DOCUMENTA COMPLETAMENTE os resultados do Issue #1.**

Ele contém:
- ✅ Todos os 23 itens solicitados de engenharia de requisitos
- ✅ Dados reais do experimento (250 docs, 259 queries, 9 modelos)
- ✅ Ranking final com BGE-M3 vencedor (NDCG@10: 0.9673)
- ✅ Hipótese refutada com evidências
- ✅ Análise comparativa e trade-offs
- ✅ Metodologia completa
- ✅ Referências às visualizações
- ✅ Apêndice com conceitos de embeddings

**O relatório V02 substitui o documento `RESEARCH_EMBEDDING_MODELS.md` que não foi criado.**

---

## 📂 Arquivos de Referência

### No repositório data-science (branch embeddings-study):

```bash
# Acessar resultados brutos
cd C:\Users\joserm\Documents\Projetos\Inspire\Meta-7\Git\data-science
git checkout embeddings-study
cat source/embeddings/results/metrics/metrics_summary.csv

# Ver análises
jupyter notebook source/embeddings/notebooks/embedding_comparison.ipynb

# Documentação metodológica
cat source/embeddings/docs/METODOLOGIA_METRICAS.md
```

### No repositório docs (branch main):

```bash
# Relatório final completo
cd C:\Users\joserm\Documents\Projetos\Inspire\Meta-7\Git\docs\docs
cat relatorios/Relatório-Ciencia-de-Dados-Embeddings-26-05-Versao-02.md

# Resumo executivo
cat relatorios/RESUMO-EXECUTIVO-RESULTADOS-EMBEDDINGS.md
```

---

## 🔗 Links Úteis

- **Issue #1:** https://github.com/destaquesgovbr/data-science/issues/1
- **Commit V02:** https://github.com/destaquesgovbr/docs/commit/4a19aec
- **Branch embeddings-study:** https://github.com/destaquesgovbr/data-science/tree/embeddings-study

---

**Elaborado por:** Claude Sonnet 4.5 (Anthropic)  
**Data:** 08/06/2026  
**Baseado em:** Análise completa do repositório data-science
