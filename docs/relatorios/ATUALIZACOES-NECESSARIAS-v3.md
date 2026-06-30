# RELATÓRIO DE ATUALIZAÇÕES NECESSÁRIAS - v3

**Data:** 26/06/2026  
**Documento:** Relatorio-Tecnico-Transparencia-Vieses-Personalizacao-26-06-COMPLETO-v3-MERGED.md

---

## MUDANÇAS TÉCNICAS A APLICAR

### 1. ✅ PostgreSQL com PGVector (substituir HuggingFace)

**Situação Atual no Documento:**
- Dataset armazenado no HuggingFace (310k+ notícias)
- 13 referências a "HuggingFace" encontradas

**Nova Realidade:**
- Banco de dados: **PostgreSQL no GCP com extensão PGVector**
- Embeddings armazenados em coluna `content_embedding VECTOR(768)`

**Ocorrências a Atualizar:**

| Linha | Contexto Atual | Atualização Necessária |
|-------|----------------|------------------------|
| **158** | Datasets de treinamento/validação (HuggingFace Datasets) | Manter HuggingFace apenas para datasets públicos históricos (backup/reprodutibilidade), mencionar PostgreSQL como armazenamento operacional |
| **400** | Dataset completo público no HuggingFace (310k+ notícias) | **PostgreSQL (GCP Cloud SQL)** como armazenamento primário; HuggingFace mantido como repositório público (snapshot) |
| **587** | Diagrama: HuggingFace Datasets Públicos | Atualizar para "PostgreSQL PGVector (Produção) + HuggingFace (Público)" |
| **1165** | Armazenamento: PostgreSQL coluna content_embedding (tipo VECTOR(768) via pgvector) | ✅ **JÁ CORRETO** |
| **2053-2055** | Tabela datasets (govbrnews HuggingFace) | Adicionar linha: PostgreSQL Cloud SQL (operacional) + HuggingFace (público/backup) |
| **2085** | Datasets públicos (HuggingFace + GitHub) | Adicionar: PostgreSQL como primário operacional |
| **2159** | Diagrama Transparência: Datasets HuggingFace CC0 | Adicionar: PostgreSQL PGVector (produção) |
| **2445** | URL analytics HuggingFace Spaces | Manter (dashboard público válido) |
| **2486** | Streamlit em HuggingFace Spaces | Manter (interface pública válida) |
| **3653** | Datasets: HuggingFace (300k+ notícias) | Atualizar: PostgreSQL (primário) + HuggingFace (público) |
| **5565** | Staging: HuggingFace Spaces | Manter (válido para testes públicos) |
| **7243** | 100% dados públicos (HuggingFace CC0) | Adicionar: PostgreSQL (operacional) |
| **7387** | Referência: Dataset HuggingFace | Manter + adicionar nota PostgreSQL |

---

### 2. ✅ Modelo NOVA LITE 2 para Sumarização

**Situação Atual no Documento:**
- Sumarização via LLM Claude 3 Haiku (mesmo prompt de classificação)
- 6 referências a "sumarização" encontradas

**Nova Realidade:**
- Modelo: **NOVA LITE 2** (Amazon Nova Lite)
- Prompt específico para sumarização (não mais acoplado ao prompt de classificação)

**Ocorrências a Atualizar:**

| Linha | Contexto Atual | Atualização Necessária |
|-------|----------------|------------------------|
| **840** | Sequence diagram: Classificação Temática + Sumarização | Separar: Claude Haiku (classificação) + NOVA LITE 2 (sumarização) |
| **1040-1070** | RF07: Geração Automática de Resumos (Sumarização) | Atualizar método: **NOVA LITE 2** via AWS Bedrock |
| **1047** | Método: Sumarização abstrativa via LLM (mesmo prompt de classificação, campo summary) | **Novo:** Prompt dedicado NOVA LITE 2 (separado da classificação) |
| **1070** | Qualidade: validação manual de 100 resumos → 85% aprovados | Atualizar com novos dados de validação NOVA LITE 2 (se disponíveis) |
| **1304** | Tabela requisitos: RF07 Geração automática de resumos | Adicionar nota: Modelo NOVA LITE 2 |

**Informações Adicionais Necessárias:**
- [ ] ID exato do modelo AWS Bedrock: `amazon.nova-lite-v1:0` (confirmar)
- [ ] Custo por chamada NOVA LITE 2
- [ ] Latência média P95
- [ ] Métricas de qualidade (ROUGE, BLEU, validação manual)
- [ ] Tamanho do resumo (150-250 caracteres mantido?)

---

### 3. ⚠️ Análise de Sentimento e NER (Implementação Elementar)

**Situação Atual no Documento:**
- RF08: Análise de sentimento via LLM (85% validação)
- RF09: Extração de entidades (NER) via LLM (85% validação)
- Apresentado como funcionalidades maduras

**Nova Realidade:**
- Implementação **elementar** e **não baseada em estudos**
- Ainda em fase experimental

**Ocorrências a Atualizar:**

| Linha | Contexto Atual | Atualização Necessária |
|-------|----------------|------------------------|
| **1081-1113** | RF08: Análise de Sentimento (tom: positivo/neutro/negativo) | Adicionar **disclaimer**: "Implementação elementar, ainda não validada cientificamente. Em fase experimental." |
| **1115-1156** | RF09: Extração de Entidades Nomeadas (NER) | Adicionar **disclaimer**: "Implementação elementar via LLM. Validação formal pendente. Precisão ~85% em sample limitado (n=200)." |
| **1139** | Precisão: validação manual → 85% das entidades são corretas (sample n=200) | Adicionar: "Sample limitado. Estudo formal de precisão pendente." |
| **1305-1306** | Tabela requisitos: RF08 Análise sentimento + RF09 NER | Status: "🟡 Experimental" ao invés de "✅ Impl." |
| **2501** | Diagrama vieses: Viés Demográfico - Desequilíbrio em entidades extraídas | Adicionar nota: "NER experimental, métricas preliminares" |
| **2946-2964** | Seção 3.2.1 Dimensão 5: Viés Demográfico (Entity Bias) | Adicionar disclaimer: "Análise preliminar. NER não validado formalmente." |
| **3439-3454** | Resultado 5: Viés Demográfico (Análise de entidades) | Adicionar: "Resultados preliminares. Implementação NER elementar requer validação científica." |
| **3619-3643** | Estratégia 7: Validação NER para Fairness de Gênero | Adicionar: "Validação preliminar (n=200). Estudo aprofundado pendente." |
| **4434** | Tabela fase 3: Features extras (sentiment + entities) | Marcar como "experimental" |
| **4512-4579** | Seção 3.3.3.3: Multi-Feature Enrichment (sentiment + entities) | Adicionar disclaimer de implementação elementar |

**Recomendações Adicionais:**
1. **Seção nova sugerida:** "3.3.X Limitações Conhecidas"
   - Análise de sentimento: implementação básica sem benchmarking contra datasets padrão
   - NER: sem comparação com modelos especializados (spaCy, Stanza, etc.)
   - Métricas (85%) baseadas em sample pequeno (n=200)
   - Falta validação cruzada com múltiplos anotadores (Fleiss' Kappa)

2. **Roadmap sugerido:**
   - Q3/2026: Benchmark sentiment contra datasets padrão (SemEval, etc.)
   - Q4/2026: Comparação NER com modelos especializados
   - Q1/2027: Validação formal com anotadores independentes (n≥500)

---

## TEXTO PROPOSTO PARA DISCLAIMERS

### Disclaimer Análise de Sentimento (RF08)

```markdown
> **⚠️ NOTA DE IMPLEMENTAÇÃO:** A análise de sentimento atual é uma implementação 
> **elementar** via LLM (campo `sentiment` no output de classificação). Não foi 
> baseada em estudos científicos formais nem validada contra datasets padrão 
> (ex: SemEval, IMDB). A métrica de 85% de aprovação é baseada em sample limitado 
> (n=100) sem validação cruzada. **Status: Experimental, sujeito a revisão.**
```

### Disclaimer Extração de Entidades (RF09)

```markdown
> **⚠️ NOTA DE IMPLEMENTAÇÃO:** A extração de entidades (NER) atual é uma implementação 
> **elementar** via LLM (campo `entities` no output de classificação). Não foi 
> comparada com modelos especializados (spaCy pt_core_news_lg, Stanza PT, etc.) 
> nem validada formalmente. A precisão de 85% é baseada em sample pequeno (n=200) 
> com anotação não-independente. **Status: Experimental, sujeito a revisão.**
> 
> **Roadmap de Melhoria:**
> - Q3/2026: Benchmark contra spaCy/Stanza (F1-score)
> - Q4/2026: Validação cruzada com 3 anotadores independentes (n≥500)
> - Q1/2027: Possível substituição por modelo especializado ou fine-tuning
```

---

## IMPACTO NAS MÉTRICAS DE CONFORMIDADE

### Antes das Atualizações

| Requisito | Status | Observação |
|-----------|--------|------------|
| RF07 (Sumarização) | ✅ Implementado | Claude Haiku |
| RF08 (Sentimento) | ✅ Implementado | 85% validação |
| RF09 (NER) | ✅ Implementado | 85% validação |
| Armazenamento | PostgreSQL + HuggingFace | Confuso (HuggingFace primário?) |

### Após as Atualizações

| Requisito | Status | Observação |
|-----------|--------|------------|
| RF07 (Sumarização) | ✅ Implementado | **NOVA LITE 2** (atualizado) |
| RF08 (Sentimento) | 🟡 Experimental | Disclaimer de implementação elementar |
| RF09 (NER) | 🟡 Experimental | Disclaimer de implementação elementar |
| Armazenamento | ✅ PostgreSQL PGVector (primário) | HuggingFace secundário (público) |

**Legenda:**
- ✅ Implementado e validado
- 🟡 Implementado mas experimental/preliminar
- 🔴 Não implementado

---

## AÇÕES IMEDIATAS RECOMENDADAS

### Prioridade ALTA (Bloqueante para Entrega FINEP)

1. **Atualizar RF07 (Sumarização) para NOVA LITE 2**
   - Incluir: ID modelo, custo, latência, métricas
   - Atualizar diagramas (linha 840)
   - Atualizar tabela requisitos (linha 1304)

2. **Adicionar disclaimers RF08/RF09**
   - Marcar como "Experimental" na tabela de requisitos
   - Adicionar notas de limitação nas seções 1081-1156

3. **Clarificar PostgreSQL como armazenamento primário**
   - Atualizar 13 referências HuggingFace
   - Manter HuggingFace como repositório público (secundário)

### Prioridade MÉDIA (Qualidade do Documento)

4. **Criar seção "3.3.X Limitações Conhecidas"**
   - Documentar limitações NER/Sentiment
   - Roadmap de melhorias Q3-Q1/2027

5. **Atualizar diagramas arquiteturais**
   - Linha 587: Adicionar PostgreSQL PGVector
   - Linha 2159: Separar armazenamento operacional vs público

6. **Atualizar tabela de custos**
   - Incluir custo NOVA LITE 2
   - Verificar se PostgreSQL PGVector tem custo adicional

### Prioridade BAIXA (Refinamento)

7. **Adicionar seção "Comparação HuggingFace vs PostgreSQL"**
   - Justificar migração
   - Benchmarks de performance

8. **Expandir validação NER/Sentiment**
   - Planejar estudos futuros
   - Definir métricas-alvo (F1-score, Cohen's Kappa)

---

## CHECKLIST DE EXECUÇÃO

- [ ] Coletar informações adicionais sobre NOVA LITE 2:
  - [ ] ID exato do modelo AWS Bedrock
  - [ ] Custo por chamada
  - [ ] Latência P50/P95
  - [ ] Métricas de qualidade (ROUGE, validação manual)
  
- [ ] Atualizar 13 referências HuggingFace:
  - [ ] Linhas 158, 400, 587, 2053-2055, 2085, 2159, 2445, 2486, 3653, 5565, 7243, 7387
  
- [ ] Adicionar disclaimers:
  - [ ] RF08 Análise de Sentimento (linha 1081)
  - [ ] RF09 Extração de Entidades (linha 1115)
  
- [ ] Atualizar RF07 Sumarização:
  - [ ] Linha 1040-1070 (descrição)
  - [ ] Linha 840 (diagrama)
  - [ ] Linha 1304 (tabela requisitos)
  
- [ ] Atualizar status na tabela de requisitos:
  - [ ] RF08: ✅ → 🟡 Experimental
  - [ ] RF09: ✅ → 🟡 Experimental
  
- [ ] Criar nova seção:
  - [ ] 3.3.X Limitações Conhecidas (NER + Sentiment)
  
- [ ] Revisar e regenerar DOCX:
  - [ ] `/convert-md-to-template_docx` após atualizações

---

## PRÓXIMOS PASSOS

1. **Confirmar com usuário:**
   - Informações adicionais sobre NOVA LITE 2
   - Se há estudos/validações pendentes para NER/Sentiment
   - Se HuggingFace deve ser mantido como repositório público

2. **Executar atualizações:**
   - Aplicar edits no arquivo .md
   - Regenerar DOCX final

3. **Validar alterações:**
   - Verificar consistência das métricas
   - Garantir que disclaimers não comprometem aprovação FINEP

---

**Elaborado por:** Claude Sonnet 4.5 (Anthropic)  
**Data:** 26/06/2026  
**Documento de referência:** Relatorio-Tecnico-Transparencia-Vieses-Personalizacao-26-06-COMPLETO-v3-MERGED.md
