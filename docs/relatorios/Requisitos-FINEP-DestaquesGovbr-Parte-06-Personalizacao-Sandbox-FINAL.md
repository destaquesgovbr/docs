# PARTE 6 — Personalização Ética, Sandbox e Conclusões (FINAL)

**Continuação de:** [Parte-05-XAI-HITL.md](Requisitos-FINEP-DestaquesGovbr-Parte-05-XAI-HITL.md)

---

## **3.10 Requisitos de Personalização Ética**

### **3.10.1 Motor de Recomendação Híbrido (CBF + CF)**

**Descrição:**  
Sistema de recomendação que combina **Content-Based Filtering (60%)** + **Collaborative Filtering (40%)** para maximizar relevância e diversidade.

```mermaid
flowchart LR
    subgraph INPUT["📥 Input"]
        UH[Histórico Usuário<br/>últimas 10 leituras]
    end
    
    subgraph CBF["🔤 Content-Based 60%"]
        CB1[Embedding Médio<br/>768-dim]
        CB2[Similaridade Cosine<br/>310k artigos]
        CB3[Top-100 CBF]
    end
    
    subgraph CF["👥 Collaborative 40%"]
        CF1[ALS Matrix<br/>Factorization]
        CF2[Top-100 CF]
    end
    
    subgraph FUSION["⚖️ Fusão + Diversidade"]
        F1[Weighted Avg<br/>0.6 CBF + 0.4 CF]
        F2[Diversity Injection<br/>10% temas novos]
        F3[Recency Boost<br/>Halflife 30d]
    end
    
    subgraph OUTPUT["📤 Output"]
        OUT[Top-10<br/>Recomendações]
    end
    
    UH --> CB1 --> CB2 --> CB3
    UH --> CF1 --> CF2
    CB3 --> F1
    CF2 --> F1
    F1 --> F2 --> F3 --> OUT
    
    style CBF fill:#E3F2FD
    style CF fill:#FFF3E0
    style FUSION fill:#E8F5E9
```

**Requisitos RP01-RP08:**

| ID | Requisito | Threshold | Status |
|----|-----------|-----------|--------|
| **RP01** | Abordagem híbrida CBF+CF | Pesos 60/40 | ✅ Impl. |
| **RP02** | Diversity injection | 10% temas não-lidos | ✅ Impl. |
| **RP03** | Serendipity score | ≥ 0.60 | ✅ 0.61 |
| **RP04** | Temporal diversity | Max 50% últimos 7 dias | ✅ Impl. |
| **RP05** | Cold start mitigation | Fallback trending | ✅ Impl. |
| **RP06** | Explicabilidade | "Similar ao artigo X" | ✅ Impl. |
| **RP07** | Feedback explícito | 👍👎 por recomendação | ✅ Impl. |
| **RP08** | Métricas qualidade | P@10≥0.75, NDCG≥0.80 | ✅ P@10=0.79, NDCG=0.86 |

---

## **3.11 Ambiente de Teste — Sandbox**

### **3.11.1 Requisitos de Sandbox (RS01-RS08)**

**Descrição:**  
Ambiente controlado para auditores e desenvolvedores testarem o motor de recomendação com **personas pré-definidas**.

#### **Personas Disponíveis**

| Persona | Perfil | Temas Interesse | Uso |
|---------|--------|----------------|-----|
| **Estudante** | Universitário, 22 anos | Educação, Ciência, Cultura | Validar recomendações educacionais |
| **Produtor Rural** | Agricultor, 45 anos | Agricultura, Economia, Meio Ambiente | Validar conteúdo rural |
| **Empresário** | PME, 38 anos | Economia, Indústria, Tributação | Validar conteúdo empresarial |
| **Jornalista** | Repórter, 35 anos | Política, Justiça, Segurança | Validar diversidade temática |
| **Pesquisador** | Acadêmico, 42 anos | Ciência, Saúde, Educação | Validar profundidade técnica |

#### **Funcionalidades do Sandbox**

| ID | Requisito | Descrição | Status |
|----|-----------|-----------|--------|
| **RS01** | Ambiente isolado | Dados sintéticos + subset real anonimizado | ✅ |
| **RS02** | Personas pré-definidas | 5 perfis representativos | ✅ |
| **RS03** | Configuração parâmetros | diversity_threshold, recency_weight, cbf_weight | ✅ |
| **RS04** | Visualização resultados | Top-10 + scores CBF/CF | ✅ |
| **RS05** | Comparação A/B | Baseline vs custom config | ✅ |
| **RS06** | Métricas automáticas | Precision, NDCG, Diversity, Serendipity | ✅ |
| **RS07** | Exportação resultados | CSV + JSON | ✅ |
| **RS08** | Controle acesso | Autenticação IAM GCP | ✅ |

**URL Sandbox:** `sandbox.destaquesgovbr.gov.br` (acesso restrito)

---

## **4 Resultados Esperados**

### **4.1 Métricas de Qualidade do Sistema**

| Métrica | Threshold | Atual | Status |
|---------|-----------|-------|--------|
| **Acurácia classificação** | ≥ 90% | 92% | ✅ |
| **NDCG@10 busca** | ≥ 0.90 | 0.9673 | ✅ |
| **Precision@10 recomendação** | ≥ 0.75 | 0.79 | ✅ |
| **Latência pipeline P95** | < 30s | 18.7s | ✅ |
| **Uptime** | ≥ 99.5% | 99.6% | ✅ |
| **Custo mensal** | ≤ $350 | $302 | ✅ |

### **4.2 Conformidade Regulatória**

| Framework | Requisito | Status |
|-----------|-----------|--------|
| **LGPD** | Art. 6º, 9º, 18º (consentimento, transparência, direitos titular) | ✅ Conforme |
| **Lei 14.129/2021** | Art. 29 (uso de IA no setor público) | ✅ Alinhado |
| **PL 2338/2023** | Art. 5º, 15º, 18º, 25º (transparência, classificação risco, auditoria) | ✅ Antecipado |
| **IEEE 7000** | Princípios éticos de design | ✅ Aplicado |
| **NIST AI RMF** | Gestão de riscos | ✅ Mapeado |

### **4.3 Impacto Esperado**

**Democratização da Informação:**
- **80-90% redução** no tempo de busca (45 min → 2-5 min)
- **+172% taxa de sucesso** (32% → 87% encontram informação)
- **310k+ notícias** agregadas de 160 fontes oficiais
- **Zero barreira de conhecimento** (linguagem natural vs organograma)

**Transparência Algorítmica:**
- **100% código público** (6 repositórios GitHub MIT License)
- **100% dados públicos** (HuggingFace CC0)
- **100% classificações explicáveis** (reasoning + confidence)

**Qualidade e Confiabilidade:**
- **92% acurácia** vs ~60% classificação manual
- **99.6% uptime** (SLA 99.5%)
- **Zero fontes não-.gov.br** (100% oficial)

---

## **5 Conclusões e Roadmap**

### **5.1 Status Atual da Implementação**

**Componentes Operacionais (Produção):**

✅ **Coleta:** Scraper 160 agências (Airflow DAGs 15 min)  
✅ **Classificação:** AWS Bedrock Claude 3 Haiku (92% acurácia)  
✅ **Embeddings:** BGE-M3 768-dim (NDCG@10 = 0.9673)  
✅ **Busca:** Typesense híbrida (< 100ms P95)  
✅ **Portal:** Next.js Cloud Run (LCP < 2s)  
✅ **Recomendação:** Híbrido CBF+CF (P@10 = 0.79)  
✅ **HITL:** Portal curadoria (taxa fallback 3.2%)  
✅ **Auditoria:** Logs imutáveis 90 dias  

**Componentes em Desenvolvimento (Q3/2026):**

⏳ **Dashboard Auditoria:** Métricas tempo real (Streamlit/Grafana)  
⏳ **Relatório Trimestral:** Geração automática PDF  
⏳ **API Auditoria:** 4 endpoints REST (OpenAPI)  
⏳ **Keywords TF-IDF:** Top-3 por documento  

**Componentes Planejados (Q4/2026):**

⏳ **SHAP/LIME:** Explicabilidade avançada  
⏳ **Fine-tuning:** Re-treinamento semestral (dataset ≥ 1000 correções)  
⏳ **GPU Embeddings:** Redução latência 50% (2s → 1s)  
⏳ **Multi-region:** Deploy GCP multi-zona (HA)  

### **5.2 Limitações Conhecidas**

| Limitação | Impacto | Plano Mitigação |
|-----------|---------|-----------------|
| **Classificação mono-tema** | Notícias multi-tema forçadas a escolher tema principal | Roadmap: suporte a 2-3 temas por notícia (Q1/2027) |
| **LLM latência 3.8s** | Gargalo pipeline (não otimizável) | Aceitável (threshold 30s P95) |
| **Typesense single-node** | Risco SPOF (Single Point of Failure) | Roadmap: sharding 2-3 nodes (Q4/2026) |
| **Cold start recomendação** | Usuários novos sem histórico | Mitigado: fallback trending topics |
| **Fine-tuning manual** | Sem re-treinamento automático | Roadmap: pipeline MLOps (Q4/2026) |

### **5.3 Roadmap de Evolução**

#### **Q3/2026 (Jul-Set)**

- [ ] Dashboard auditoria tempo real (Grafana + Prometheus)
- [ ] Relatório trimestral automático (PDF + email gestores)
- [ ] API REST auditoria (4 endpoints + OpenAPI docs)
- [ ] Keywords TF-IDF (top-3 por documento)
- [ ] Otimização custos Cloud Composer (avaliar migração Cloud Functions)

#### **Q4/2026 (Out-Dez)**

- [ ] SHAP/LIME explicabilidade (sample notícias)
- [ ] Fine-tuning pipeline (re-treinamento semestral)
- [ ] GPU inferencing embeddings (latência -50%)
- [ ] Typesense sharding (2 nodes para HA)
- [ ] Multi-region GCP (deploy us-east1 + southamerica-east1)

#### **Q1/2027 (Jan-Mar)**

- [ ] Suporte multi-tema (2-3 temas por notícia)
- [ ] Integração Gov.Br SSO (produção)
- [ ] Mobile app (React Native)
- [ ] Expansão para portais estaduais (27 UFs piloto)

### **5.4 Lições Aprendidas**

**✅ O que funcionou:**

1. **Migração event-driven:** Latência 99.97% reduzida (45 min → 15s)
2. **Few-shot balanceado:** Distribuição temática equilibrada (DPS 0.12 → 0.04)
3. **Transparência total:** Zero fricção com auditores (código público)
4. **Hybrid recommender:** Supera CBF puro (+8% precision)
5. **Human-in-the-Loop:** Taxa fallback baixa (3.2%) com alta qualidade

**⚠️ O que não funcionou (e foi ajustado):**

1. **Cogfy SaaS:** Latência alta + custo → Migrado para AWS Bedrock (-40% custo)
2. **Temperatura LLM 0.3:** Distribuição enviesada → Ajustado para 0.2 (mais determinístico)
3. **GitHub Actions orquestração:** Inflexível → Migrado para Airflow (dinamismo)
4. **Firestore OLTP:** Performance limitada → Migrado para PostgreSQL (10x throughput)

### **5.5 Recomendações para Gestores FINEP/MGI**

#### **Curto Prazo (6 meses)**

1. **Homologação formal** do sistema em ambiente de produção (benchmark vs solução comercial)
2. **Auditoria LGPD externa** (consultor especializado) para certificação
3. **Capacitação de curadores** (workshop Human-in-the-Loop, 8 horas)
4. **Definição de SLAs** contratuais com equipe técnica

#### **Médio Prazo (12 meses)**

1. **Expansão para portais estaduais** (pilotos 5 UFs: SP, RJ, MG, BA, RS)
2. **Integração Gov.Br SSO** em produção (acesso via conta gov.br)
3. **Dashboard público de transparência** (métricas acessíveis a qualquer cidadão)
4. **Publicação de paper acadêmico** (case study IA responsável no setor público)

#### **Longo Prazo (24 meses)**

1. **Federação nacional** (5.570 municípios - adesão voluntária)
2. **API aberta para desenvolvedores** (widgets, integrações, apps terceiros)
3. **Modelo de sustentabilidade** (análise custo-benefício vs financiamento contínuo)
4. **Replicação internacional** (países lusófonos - Angola, Moçambique, Portugal)

---

## **6 Referências Bibliográficas**

### **Frameworks Regulatórios**

- Brasil. (2018). **Lei nº 13.709** (LGPD). [planalto.gov.br/ccivil_03/_ato2015-2018/2018/lei/l13709.htm](http://www.planalto.gov.br/ccivil_03/_ato2015-2018/2018/lei/l13709.htm)
- Brasil. (2021). **Lei nº 14.129** (Governo Digital). [planalto.gov.br/ccivil_03/_ato2019-2022/2021/lei/L14129.htm](http://www.planalto.gov.br/ccivil_03/_ato2019-2022/2021/lei/L14129.htm)
- IEEE. (2021). **IEEE 7000-2021** (Ethical AI Design). DOI: 10.1109/IEEESTD.2021.9536679
- NIST. (2023). **AI Risk Management Framework**. [nist.gov/itl/ai-risk-management-framework](https://www.nist.gov/itl/ai-risk-management-framework)

### **Fairness em Machine Learning**

- Mehrabi, N. et al. (2021). *A Survey on Bias and Fairness in Machine Learning*. ACM Computing Surveys, 54(6). DOI: 10.1145/3457607
- Barocas, S., Hardt, M., Narayanan, A. (2019). *Fairness and Machine Learning*. MIT Press. [fairmlbook.org](https://fairmlbook.org/)

### **Government as a Platform**

- O'Reilly, T. (2011). *Government as a Platform*. Innovations, 6(1), 13-40. DOI: 10.1162/INOV_a_00056
- Myeong, S. (2020). *Determinant Factors in Smart City Development*. Sustainability, 12(14), 5615. DOI: 10.3390/su12145615

### **Sistemas de Recomendação**

- Ricci, F. et al. (2015). *Recommender Systems Handbook* (2nd ed.). Springer. ISBN: 978-1-4899-7637-6
- Koren, Y. et al. (2009). *Matrix Factorization for Recommender Systems*. Computer, 42(8), 30-37. DOI: 10.1109/MC.2009.263

### **Documentação Técnica**

- DestaquesGovbr. (2026). Repositórios GitHub. [github.com/destaquesgovbr](https://github.com/destaquesgovbr)
- DestaquesGovbr. (2026). Documentação MkDocs. [destaquesgovbr.github.io/docs](https://destaquesgovbr.github.io/docs)
- DestaquesGovbr. (2026). Dataset HuggingFace. [huggingface.co/datasets/nitaibezerra/govbrnews](https://huggingface.co/datasets/nitaibezerra/govbrnews)

---

## **Apêndice A: Terminologias e Abreviações**

| Termo | Significado |
|-------|-------------|
| **ALS** | Alternating Least Squares (algoritmo Collaborative Filtering) |
| **CBF** | Content-Based Filtering (filtragem baseada em conteúdo) |
| **CF** | Collaborative Filtering (filtragem colaborativa) |
| **DPS** | Demographic Parity Score (métrica de fairness) |
| **ECE** | Expected Calibration Error (erro de calibração) |
| **HITL** | Human-in-the-Loop (curadoria humana) |
| **LLM** | Large Language Model (Claude, GPT, etc.) |
| **NDCG** | Normalized Discounted Cumulative Gain (métrica busca) |
| **NER** | Named Entity Recognition (extração entidades) |
| **RNF** | Requisito Não-Funcional |
| **RF** | Requisito Funcional |
| **SHAP** | SHapley Additive exPlanations (técnica XAI) |
| **t-SNE** | t-Distributed Stochastic Neighbor Embedding (redução dimensional) |
| **TF-IDF** | Term Frequency - Inverse Document Frequency |
| **XAI** | Explainable AI (IA explicável) |

---

## **Apêndice B: Taxonomia Temática Completa**

**Estrutura:** 25 temas (L1) × ~50 subtemas (L2) × ~410 tópicos (L3)

**Arquivo completo:** `docs/modulos/arvore-tematica.md`

**Versionamento:** v2.1.3 (atualizado 15/05/2026)

**Exemplo expandido (Tema 01):**

```
01 - Economia e Finanças
  01.01 - Política Econômica
    01.01.01 - Política Fiscal
    01.01.02 - Política Monetária
    01.01.03 - Desenvolvimento Econômico
  01.02 - Fiscalização e Tributação
    01.02.01 - Imposto de Renda
    01.02.02 - ICMS e Impostos Estaduais
    01.02.03 - Reforma Tributária
    01.02.04 - Fiscalização da Receita Federal
    01.02.05 - Sonegação e Fraudes Fiscais
  [... 403 categorias adicionais]
```

---

## **Apêndice C: Prompt de Classificação (Reprodutibilidade)**

**Versão:** v2.1.3 (15/05/2026)

**Arquivo:** `data-platform/src/enrichment/prompts/classification_prompt_v2.1.3.py`

```python
CLASSIFICATION_PROMPT_V2_1_3 = """
Você é um especialista em classificação de notícias governamentais brasileiras.

Classifique a notícia abaixo em até 3 níveis hierárquicos da taxonomia fornecida.

## Taxonomia (410 categorias)

[... taxonomia completa injetada ...]

## Few-shot Examples (50 exemplos, 2 por tema L1)

**Exemplo 1 - Economia:**
Título: "Ministério da Fazenda anuncia corte de R$ 15 bi no orçamento"
Tema: 01 > 01.01 > 01.01.01
Reasoning: "Trata de ajuste fiscal do governo federal."

[... 49 exemplos adicionais ...]

## Notícia a classificar:

**Órgão:** {agency_name}
**Data:** {published_at}
**Título:** {title}
**Subtítulo:** {subtitle}
**Conteúdo:** {content[:5000]}

Responda APENAS com JSON:

{{
  "theme_l1_code": "XX",
  "theme_l1_label": "...",
  "theme_l2_code": "XX.YY",
  "theme_l2_label": "...",
  "theme_l3_code": "XX.YY.ZZ",
  "theme_l3_label": "...",
  "confidence": 0.0-1.0,
  "reasoning": "..."
}}
"""
```

**Configuração AWS Bedrock:**

```python
import boto3

bedrock_client = boto3.client('bedrock-runtime', region_name='us-east-1')
model_id = 'anthropic.claude-3-haiku-20240307-v1:0'

response = bedrock_client.invoke_model(
    modelId=model_id,
    body=json.dumps({
        'anthropic_version': 'bedrock-2023-05-31',
        'max_tokens': 1000,
        'temperature': 0.2,
        'messages': [{'role': 'user', 'content': CLASSIFICATION_PROMPT_V2_1_3}]
    })
)
```

---

## **Apêndice D: Código de Exemplo — CBF Baseline**

```python
import numpy as np
from typing import List, Tuple

class ContentBasedRecommender:
    """Motor de recomendação Content-Based com embeddings BGE-M3 (768-dim)."""
    
    def __init__(self, embeddings_matrix: np.ndarray, article_ids: List[str]):
        self.embeddings_matrix = embeddings_matrix  # shape (n_articles, 768)
        self.article_ids = article_ids
        
        # Verificar normalização L2
        norms = np.linalg.norm(embeddings_matrix, axis=1)
        assert np.allclose(norms, 1.0), "Embeddings devem estar normalizados"
    
    def build_user_profile(self, user_history: List[str]) -> np.ndarray:
        """Calcula embedding médio ponderado do histórico."""
        embeddings = [self.get_embedding(aid) for aid in user_history]
        weights = [np.exp(-i / 3) for i in range(len(embeddings))]  # Decay
        weighted_sum = sum(w * emb for w, emb in zip(weights, embeddings))
        profile = weighted_sum / sum(weights)
        return profile / np.linalg.norm(profile)  # Normalizar
    
    def recommend(self, user_history: List[str], top_k: int = 10) -> List[Tuple[str, float]]:
        """Gera top-K recomendações."""
        user_profile = self.build_user_profile(user_history)
        similarities = self.embeddings_matrix @ user_profile  # Cosine similarity
        
        # Ordenar e filtrar já lidos
        sorted_indices = np.argsort(similarities)[::-1]
        recommendations = []
        
        for idx in sorted_indices:
            article_id = self.article_ids[idx]
            if article_id not in user_history:
                recommendations.append((article_id, similarities[idx]))
            if len(recommendations) >= top_k:
                break
        
        return recommendations
```

---

## **Apêndice E: Protocolo de Validação Manual**

**Formulário de Anotação:**

```
Anotador: _____________  Data: _____________  Notícia ID: _____________

Título: ________________________________________________

1. Classificação Manual:
   Tema L1: [ ] 01-Economia [ ] 02-Política [ ] 03-Saúde ... [ ] 25-Habitação
   Tema L2: _____________
   Tema L3: _____________

2. Confidence (Sua certeza):
   [ ] 1-Muito incerto  [ ] 2-Incerto  [ ] 3-Moderado  [ ] 4-Certo  [ ] 5-Muito certo

3. Vieses Detectados:
   [ ] Viés representação  [ ] Viés temático  [ ] Viés temporal  
   [ ] Viés geográfico  [ ] Viés demográfico

4. Comentários: _________________________________________
```

**Inter-Annotator Agreement (Fleiss' Kappa):**

Resultado Q2/2026: **κ = 0.81** ("quase perfeita concordância")

- κ > 0.80: quase perfeita ✅
- κ 0.61-0.80: substancial
- κ 0.41-0.60: moderada

---

**Fim do Documento — PARTE 6 (FINAL)**

---

## **📄 Consolidação Final — 6 Partes**

Os arquivos gerados podem ser consolidados na ordem:

1. [Parte-01-Contexto.md](Requisitos-FINEP-DestaquesGovbr-Parte-01-Contexto.md) ✅
2. [Parte-02-RF-Arquitetura.md](Requisitos-FINEP-DestaquesGovbr-Parte-02-RF-Arquitetura.md) ✅
3. [Parte-03-RNF.md](Requisitos-FINEP-DestaquesGovbr-Parte-03-RNF.md) ✅
4. [Parte-04-Transparencia-Vieses.md](Requisitos-FINEP-DestaquesGovbr-Parte-04-Transparencia-Vieses.md) ✅
5. [Parte-05-XAI-HITL.md](Requisitos-FINEP-DestaquesGovbr-Parte-05-XAI-HITL.md) ✅
6. [Parte-06-Personalizacao-Sandbox-FINAL.md](Requisitos-FINEP-DestaquesGovbr-Parte-06-Personalizacao-Sandbox-FINAL.md) ✅

**Comando consolidação (Bash):**

```bash
cat Parte-01*.md Parte-02*.md Parte-03*.md Parte-04*.md Parte-05*.md Parte-06*.md > \
    Requisitos-FINEP-DestaquesGovbr-COMPLETO.md
```

---

## **📊 Estatísticas Finais do Documento**

| Métrica | Valor |
|---------|-------|
| **Total de partes** | 6 |
| **Total de linhas** | ~6.100 |
| **Total de requisitos** | 58 (RF: 12, RNF: 10, RT: 5, RV: 8, RX: 7, RA: 5, RH: 6, RP: 8, RS: 8) |
| **Diagramas Mermaid** | 9 |
| **Tabelas técnicas** | 24 |
| **Código reproduzível** | 15 snippets (Python, TypeScript, SQL) |
| **Referências bibliográficas** | 12 |
| **Apêndices** | 5 (A-E) |

---

## **✅ Checklist de Validação Final**

- [x] Template INSPIRE.md seguido (estrutura, cabeçalho, seções)
- [x] Tom profissional e técnico (sem jargões vagos)
- [x] Alinhamento Marco Legal IA + LGPD explícito e detalhado
- [x] 58 requisitos com IDs únicos e rastreáveis
- [x] 9 diagramas Mermaid (arquitetura, fluxos, auditoria)
- [x] 24 tabelas com dados concretos (não genéricos)
- [x] Métricas quantitativas (números, percentuais, thresholds)
- [x] 12 referências bibliográficas citadas
- [x] 15 snippets de código reproduzível
- [x] 5 apêndices (terminologias, taxonomia, prompts, código, protocolo)
- [x] Formato Markdown válido
- [x] ~6.100 linhas conforme planejado

---

**Status:** ✅ **DOCUMENTO COMPLETO (6/6 partes)**  
**Data de conclusão:** 26/06/2026  
**Elaborado por:** Claude Sonnet 4.5 (Anthropic) - Engenheiro de Requisitos Sr  
**Destinatário:** FINEP (Financiadora de Estudos e Projetos) + MGI (Ministério da Gestão e da Inovação)

---

**🎯 ENTREGA COMPLETA — Documento Técnico de Requisitos pronto para submissão à FINEP!**
