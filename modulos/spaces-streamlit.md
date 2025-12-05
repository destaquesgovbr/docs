# Módulo: Streamlit App (spaces-govbrnews)

> Aplicação de análise e visualização de dados no HuggingFace Spaces.

**Localização**: HuggingFace Spaces (conta pessoal nitaibezerra)

## Visão Geral

O Streamlit App é uma aplicação interativa para:
- **Explorar** o dataset de notícias governamentais
- **Visualizar** estatísticas e tendências
- **Analisar** distribuição por órgão e tema
- **Baixar** subconjuntos de dados

```mermaid
flowchart LR
    HF[(HuggingFace Dataset)] -->|Load| ST[Streamlit App]
    ST -->|Visualização| U[Usuário]
    ST -->|Download| U
```

---

## Funcionalidades

### 1. Visão Geral do Dataset

- Total de notícias
- Período coberto
- Quantidade por órgão
- Quantidade por tema

### 2. Filtros Interativos

- Por órgão (multiselect)
- Por tema (nível 1, 2, 3)
- Por período (date range)
- Por palavras-chave

### 3. Visualizações

- **Timeline**: Notícias por dia/semana/mês
- **Distribuição**: Por órgão e tema
- **Word Cloud**: Termos mais frequentes
- **Heatmap**: Cruzamento órgão × tema

### 4. Download de Dados

- CSV filtrado
- Parquet completo
- Subconjuntos customizados

---

## Stack Tecnológico

| Tecnologia | Uso |
|------------|-----|
| Streamlit | Framework de apps |
| Pandas | Manipulação de dados |
| Altair | Visualizações |
| datasets | Load do HuggingFace |
| HuggingFace Spaces | Hospedagem |

---

## Estrutura do App

```python
# app.py (simplificado)
import streamlit as st
import pandas as pd
from datasets import load_dataset

# Configuração da página
st.set_page_config(
    page_title="DestaquesGovbr Analytics",
    layout="wide"
)

# Carregar dados
@st.cache_data
def load_data():
    ds = load_dataset("nitaibezerra/govbrnews")
    return ds["train"].to_pandas()

df = load_data()

# Sidebar com filtros
st.sidebar.header("Filtros")
agencies = st.sidebar.multiselect(
    "Órgãos",
    options=df["agency"].unique()
)
date_range = st.sidebar.date_input(
    "Período",
    value=(df["published_at"].min(), df["published_at"].max())
)

# Aplicar filtros
filtered_df = df.copy()
if agencies:
    filtered_df = filtered_df[filtered_df["agency"].isin(agencies)]

# Métricas principais
col1, col2, col3 = st.columns(3)
col1.metric("Total de Notícias", len(filtered_df))
col2.metric("Órgãos", filtered_df["agency"].nunique())
col3.metric("Temas", filtered_df["theme_1_level_1_label"].nunique())

# Gráficos
st.subheader("Notícias por Órgão")
chart = alt.Chart(filtered_df).mark_bar().encode(
    x="agency",
    y="count()"
)
st.altair_chart(chart, use_container_width=True)
```

---

## Visualizações Disponíveis

### Timeline de Publicações

```python
# Notícias por dia
daily = df.groupby(df["published_at"].dt.date).size()

chart = alt.Chart(daily.reset_index()).mark_line().encode(
    x="published_at:T",
    y="0:Q"
)
```

### Distribuição por Órgão

```python
# Top 20 órgãos
top_agencies = df["agency"].value_counts().head(20)

chart = alt.Chart(top_agencies.reset_index()).mark_bar().encode(
    x=alt.X("agency", sort="-y"),
    y="count"
)
```

### Distribuição por Tema

```python
# Temas nível 1
themes = df["theme_1_level_1_label"].value_counts()

chart = alt.Chart(themes.reset_index()).mark_arc().encode(
    theta="count",
    color="theme_1_level_1_label"
)
```

### Heatmap Órgão × Tema

```python
# Cruzamento
cross = pd.crosstab(df["agency"], df["theme_1_level_1_label"])

chart = alt.Chart(cross.reset_index().melt(id_vars="agency")).mark_rect().encode(
    x="theme_1_level_1_label",
    y="agency",
    color="value"
)
```

---

## Deploy no HuggingFace Spaces

### Estrutura do repositório

```
spaces-govbrnews/
├── app.py              # Aplicação principal
├── requirements.txt    # Dependências
├── README.md           # Documentação do Space
└── .gitattributes      # Config Git LFS
```

### `requirements.txt`

```
streamlit>=1.28.0
pandas>=2.0.0
altair>=5.0.0
datasets>=2.14.0
```

### `README.md` (HuggingFace format)

```yaml
---
title: DestaquesGovbr Analytics
emoji: 📰
colorFrom: blue
colorTo: green
sdk: streamlit
sdk_version: 1.28.0
app_file: app.py
pinned: false
---

# DestaquesGovbr Analytics

Análise interativa de notícias governamentais brasileiras.
```

### Deploy

1. Criar Space no HuggingFace
2. Push do código:

```bash
git remote add space https://huggingface.co/spaces/nitaibezerra/govbrnews-analytics
git push space main
```

3. Space builda automaticamente

---

## Funcionalidades de Download

### CSV Filtrado

```python
@st.cache_data
def convert_to_csv(df):
    return df.to_csv(index=False).encode("utf-8")

csv = convert_to_csv(filtered_df)
st.download_button(
    label="Download CSV",
    data=csv,
    file_name="govbrnews_filtered.csv",
    mime="text/csv"
)
```

### Subconjunto Customizado

```python
# Seleção de colunas
columns = st.multiselect(
    "Colunas para download",
    options=df.columns,
    default=["title", "agency", "published_at", "url"]
)

csv = filtered_df[columns].to_csv(index=False).encode("utf-8")
```

---

## Performance e Cache

### Cache de dados

```python
@st.cache_data(ttl=3600)  # 1 hora
def load_data():
    """Carrega dataset com cache."""
    ds = load_dataset("nitaibezerra/govbrnews")
    return ds["train"].to_pandas()
```

### Cache de computações

```python
@st.cache_data
def compute_statistics(df):
    """Computa estatísticas com cache."""
    return {
        "total": len(df),
        "by_agency": df["agency"].value_counts(),
        "by_theme": df["theme_1_level_1_label"].value_counts(),
    }
```

---

## Limitações

| Limitação | Descrição | Workaround |
|-----------|-----------|------------|
| Memória | Dataset grande (~300k rows) | Sampling ou filtros |
| Latência | Primeiro load demorado | Cache agressivo |
| Recursos | Tier gratuito do HF Spaces | Otimizar queries |

---

## Uso Local

### Desenvolvimento

```bash
# Clone do repo
git clone https://huggingface.co/spaces/nitaibezerra/govbrnews-analytics
cd govbrnews-analytics

# Instalar dependências
pip install -r requirements.txt

# Rodar localmente
streamlit run app.py
```

### Acessar em

```
http://localhost:8501
```

---

## Links Relacionados

- [Dataset HuggingFace](https://huggingface.co/datasets/nitaibezerra/govbrnews)
- [Componentes Estruturantes](../arquitetura/componentes-estruturantes.md)
- [Visão Geral da Arquitetura](../arquitetura/visao-geral.md)
