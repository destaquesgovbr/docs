# Análise de Texto do Dataset GovBrNews

> Parte 3 do guia de exploração do dataset - Estatísticas de texto, nuvem de palavras, frequência de termos e exercícios práticos.

---

**Nível**: Intermediário
**Tempo estimado**: 60-90 minutos
**Pré-requisitos**: Conclusão das [Parte 1](./index.md) e [Parte 2](./analise-tematica.md)

---

## Parte 3: Análise de Texto (Intermediário)

### Estatísticas de Texto

#### Calculando Métricas de Texto

```python
import numpy as np

# Calcular métricas
df['title_length'] = df['title'].str.len()
df['content_length'] = df['content'].str.len()
df['word_count'] = df['content'].str.split().str.len()
df['summary_length'] = df['summary'].str.len()

# Estatísticas descritivas
text_stats = df[['title_length', 'content_length', 'word_count', 'summary_length']].describe()
print("=== Estatísticas de Texto ===")
print(text_stats)
```

**Output esperado:**

```
=== Estatísticas de Texto ===
       title_length  content_length   word_count  summary_length
count   298547.00       298547.00    298547.00       298547.00
mean        67.23         3542.87       587.45          245.32
std         24.15         2891.43       478.21          112.67
min          5.00           50.00        10.00           20.00
25%         49.00         1523.00       252.00          165.00
50%         64.00         2876.00       476.00          238.00
75%         82.00         4721.00       782.00          315.00
max        250.00        89542.00     14892.00         1500.00
```

#### Distribuição do Tamanho do Conteúdo

```python
fig, axes = plt.subplots(1, 3, figsize=(16, 5))

# Histograma do tamanho do conteúdo
axes[0].hist(df['content_length'], bins=50, color='steelblue', edgecolor='white')
axes[0].set_title('Distribuição do Tamanho do Conteúdo')
axes[0].set_xlabel('Caracteres')
axes[0].set_ylabel('Frequência')
axes[0].axvline(df['content_length'].mean(), color='red', linestyle='--', label='Média')
axes[0].legend()

# Histograma da contagem de palavras
axes[1].hist(df['word_count'], bins=50, color='coral', edgecolor='white')
axes[1].set_title('Distribuição da Contagem de Palavras')
axes[1].set_xlabel('Palavras')
axes[1].set_ylabel('Frequência')
axes[1].axvline(df['word_count'].mean(), color='red', linestyle='--', label='Média')
axes[1].legend()

# Boxplot por tema
top_themes = df['theme_1_level_1'].value_counts().head(5).index.tolist()
df_top = df[df['theme_1_level_1'].isin(top_themes)]
df_top.boxplot(column='word_count', by='theme_1_level_1', ax=axes[2])
axes[2].set_title('Contagem de Palavras por Tema')
axes[2].set_xlabel('Tema')
axes[2].set_ylabel('Palavras')
plt.suptitle('')  # Remove título automático

plt.tight_layout()
plt.savefig('estatisticas_texto.png', dpi=150, bbox_inches='tight')
plt.show()
```

### Nuvem de Palavras por Tema

#### Gerando Wordcloud

```python
from wordcloud import WordCloud
import matplotlib.pyplot as plt

# Função para gerar wordcloud
def gerar_wordcloud(texto, titulo, arquivo):
    """Gera e salva uma nuvem de palavras."""
    # Stopwords em português
    stopwords_pt = {
        'de', 'a', 'o', 'que', 'e', 'do', 'da', 'em', 'um', 'para', 'com',
        'não', 'uma', 'os', 'no', 'se', 'na', 'por', 'mais', 'as', 'dos',
        'como', 'mas', 'ao', 'ele', 'das', 'tem', 'seu', 'sua', 'ou', 'ser',
        'quando', 'muito', 'há', 'nos', 'já', 'está', 'eu', 'também', 'só',
        'pelo', 'pela', 'até', 'isso', 'ela', 'entre', 'era', 'depois',
        'sem', 'mesmo', 'aos', 'ter', 'seus', 'quem', 'nas', 'me', 'esse',
        'eles', 'estão', 'você', 'tinha', 'foram', 'essa', 'num', 'nem',
        'suas', 'meu', 'as', 'minha', 'numa', 'pelos', 'elas', 'havia',
        'seja', 'qual', 'será', 'nós', 'tenho', 'lhe', 'deles', 'essas',
        'esses', 'pelas', 'este', 'fosse', 'dele', 'tu', 'te', 'vocês',
        'vós', 'lhes', 'meus', 'minhas', 'teu', 'tua', 'teus', 'tuas',
        'nosso', 'nossa', 'nossos', 'nossas', 'dela', 'delas', 'esta',
        'estes', 'estas', 'aquele', 'aquela', 'aqueles', 'aquelas', 'isto',
        'aquilo', 'estou', 'está', 'estamos', 'estão', 'estive', 'esteve',
        'estivemos', 'estiveram', 'estava', 'estávamos', 'estavam'
    }

    wordcloud = WordCloud(
        width=800,
        height=400,
        background_color='white',
        stopwords=stopwords_pt,
        max_words=100,
        colormap='viridis'
    ).generate(texto)

    plt.figure(figsize=(12, 6))
    plt.imshow(wordcloud, interpolation='bilinear')
    plt.axis('off')
    plt.title(titulo, fontsize=16)
    plt.tight_layout()
    plt.savefig(arquivo, dpi=150, bbox_inches='tight')
    plt.show()

# Gerar wordcloud para cada tema principal
top_themes = df['theme_1_level_1'].value_counts().head(4).index.tolist()

for theme in top_themes:
    texto = ' '.join(df[df['theme_1_level_1'] == theme]['content'].dropna().tolist())
    gerar_wordcloud(
        texto,
        f'Nuvem de Palavras: {theme}',
        f'wordcloud_{theme.lower().replace(" ", "_")}.png'
    )
```

### Análise de Frequência de Termos

#### Top Termos por Tema

```python
from collections import Counter
import re

def extrair_termos(textos, n_top=20):
    """Extrai os termos mais frequentes de uma lista de textos."""
    # Stopwords expandidas
    stopwords_pt = {
        'de', 'a', 'o', 'que', 'e', 'do', 'da', 'em', 'um', 'para', 'com',
        'não', 'uma', 'os', 'no', 'se', 'na', 'por', 'mais', 'as', 'dos',
        'como', 'mas', 'ao', 'ele', 'das', 'tem', 'seu', 'sua', 'ou', 'ser',
        'quando', 'muito', 'há', 'nos', 'já', 'está', 'eu', 'também', 'só',
        'pelo', 'pela', 'até', 'isso', 'ela', 'entre', 'era', 'depois'
    }

    # Juntar todos os textos
    texto_completo = ' '.join(textos.dropna())

    # Tokenizar e limpar
    palavras = re.findall(r'\b[a-zA-Zà-ú]{3,}\b', texto_completo.lower())

    # Filtrar stopwords
    palavras_filtradas = [p for p in palavras if p not in stopwords_pt]

    # Contar frequências
    return Counter(palavras_filtradas).most_common(n_top)

# Analisar top termos por tema
top_themes = df['theme_1_level_1'].value_counts().head(5).index.tolist()

print("=== Top 10 Termos por Tema ===\n")
for theme in top_themes:
    textos = df[df['theme_1_level_1'] == theme]['content']
    termos = extrair_termos(textos, n_top=10)
    print(f"--- {theme} ---")
    for termo, freq in termos:
        print(f"  {termo}: {freq:,}")
    print()
```

#### Visualização de Frequência de Termos

```python
fig, axes = plt.subplots(2, 3, figsize=(16, 10))
axes = axes.flatten()

for i, theme in enumerate(top_themes[:6]):
    textos = df[df['theme_1_level_1'] == theme]['content']
    termos = extrair_termos(textos, n_top=10)

    palavras = [t[0] for t in termos]
    frequencias = [t[1] for t in termos]

    axes[i].barh(palavras[::-1], frequencias[::-1], color='steelblue')
    axes[i].set_title(f'{theme}', fontsize=11)
    axes[i].set_xlabel('Frequência')

plt.suptitle('Top 10 Termos por Tema', fontsize=14, y=1.02)
plt.tight_layout()
plt.savefig('frequencia_termos.png', dpi=150, bbox_inches='tight')
plt.show()
```

---

## Exercícios Práticos

### Exercício 1: Relatório de Distribuição por Órgão

**Objetivo**: Gerar um relatório completo de distribuição de notícias por órgão governamental.

```python
def gerar_relatorio_orgaos(df, output_file='relatorio_orgaos.csv'):
    """
    Gera relatório de distribuição de notícias por órgão.

    Args:
        df: DataFrame com os dados
        output_file: Arquivo de saída

    Returns:
        DataFrame com o relatório
    """
    # Agregar métricas por órgão
    relatorio = df.groupby('agency').agg({
        'unique_id': 'count',
        'content_length': 'mean',
        'word_count': 'mean',
        'published_at': ['min', 'max']
    }).round(2)

    # Renomear colunas
    relatorio.columns = [
        'total_noticias',
        'media_caracteres',
        'media_palavras',
        'primeira_publicacao',
        'ultima_publicacao'
    ]

    # Ordenar por volume
    relatorio = relatorio.sort_values('total_noticias', ascending=False)

    # Adicionar percentual
    relatorio['percentual'] = (
        relatorio['total_noticias'] / relatorio['total_noticias'].sum() * 100
    ).round(2)

    # Salvar
    relatorio.to_csv(output_file)
    print(f"Relatório salvo em: {output_file}")

    return relatorio

# Executar
relatorio = gerar_relatorio_orgaos(df)
print(relatorio.head(10))
```

**Output esperado:**

```
                              total_noticias  media_caracteres  media_palavras  ...
agency
Ministério da Saúde                    45230           3892.45          647.23  ...
Ministério da Economia                 38102           3124.67          519.44  ...
Ministério da Educação                 29845           4231.89          703.98  ...
...
```

---

### Exercício 2: Visualização de Tendência de Temas

**Objetivo**: Criar visualização interativa mostrando evolução dos temas ao longo do tempo.

```python
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

def visualizar_tendencia_temas(df, top_n=5):
    """
    Cria visualização interativa de tendência de temas.

    Args:
        df: DataFrame com os dados
        top_n: Número de temas a exibir
    """
    # Preparar dados
    df['year_month'] = df['published_at'].dt.to_period('M').astype(str)

    # Top temas
    top_themes = df['theme_1_level_1'].value_counts().head(top_n).index.tolist()

    # Agregar por mes e tema
    monthly = df[df['theme_1_level_1'].isin(top_themes)].groupby(
        ['year_month', 'theme_1_level_1']
    ).size().reset_index(name='count')

    # Criar figura com subplots
    fig = make_subplots(
        rows=2, cols=1,
        subplot_titles=('Evolução Mensal', 'Distribuição Acumulada'),
        row_heights=[0.7, 0.3]
    )

    # Gráfico de linhas
    for theme in top_themes:
        data_theme = monthly[monthly['theme_1_level_1'] == theme]
        fig.add_trace(
            go.Scatter(
                x=data_theme['year_month'],
                y=data_theme['count'],
                name=theme,
                mode='lines+markers'
            ),
            row=1, col=1
        )

    # Gráfico de barras empilhadas
    fig.add_trace(
        go.Bar(
            x=top_themes,
            y=[df[df['theme_1_level_1'] == t].shape[0] for t in top_themes],
            marker_color='steelblue',
            showlegend=False
        ),
        row=2, col=1
    )

    fig.update_layout(
        title='Tendência de Temas ao Longo do Tempo',
        height=800,
        width=1200,
        hovermode='x unified'
    )

    fig.write_html('tendencia_temas_interativo.html')
    fig.show()

    return fig

# Executar
fig = visualizar_tendencia_temas(df, top_n=5)
```

---

### Exercício 3: Top 10 Órgãos Mais Ativos

**Objetivo**: Identificar e analisar os 10 órgãos com maior volume de publicações.

```python
def analisar_top_orgaos(df, top_n=10):
    """
    Analisa os órgãos mais ativos em termos de publicações.

    Args:
        df: DataFrame com os dados
        top_n: Número de órgãos a analisar

    Returns:
        Tuple com DataFrame de análise e figura
    """
    # Top órgãos
    top_agencies = df['agency'].value_counts().head(top_n)

    # Análise detalhada
    analise = []
    for agency in top_agencies.index:
        df_agency = df[df['agency'] == agency]
        analise.append({
            'orgao': agency,
            'total_noticias': len(df_agency),
            'tema_principal': df_agency['theme_1_level_1'].mode().iloc[0],
            'media_palavras': df_agency['word_count'].mean(),
            'periodo_inicio': df_agency['published_at'].min(),
            'periodo_fim': df_agency['published_at'].max(),
            'noticias_por_mes': len(df_agency) / (
                (df_agency['published_at'].max() - df_agency['published_at'].min()).days / 30
            )
        })

    df_analise = pd.DataFrame(analise)

    # Visualização
    fig, axes = plt.subplots(1, 2, figsize=(14, 6))

    # Gráfico de barras
    axes[0].barh(df_analise['orgao'], df_analise['total_noticias'], color='steelblue')
    axes[0].set_title('Top 10 Órgãos por Volume')
    axes[0].set_xlabel('Total de Notícias')
    axes[0].invert_yaxis()

    # Gráfico de produtividade
    axes[1].barh(df_analise['orgao'], df_analise['noticias_por_mes'], color='coral')
    axes[1].set_title('Produtividade (Notícias/Mês)')
    axes[1].set_xlabel('Notícias por Mês')
    axes[1].invert_yaxis()

    plt.tight_layout()
    plt.savefig('top_orgaos_analise.png', dpi=150, bbox_inches='tight')
    plt.show()

    return df_analise, fig

# Executar
df_analise, fig = analisar_top_orgaos(df)
print(df_analise.to_string(index=False))
```

---

### Exercício 4: Correlação Tamanho x Tema

**Objetivo**: Analisar se existe correlação entre o tamanho do texto e o tema da notícia.

```python
import scipy.stats as stats

def analisar_correlacao_tamanho_tema(df):
    """
    Analisa correlação entre tamanho do texto e tema.

    Args:
        df: DataFrame com os dados

    Returns:
        DataFrame com estatísticas por tema
    """
    # Estatísticas por tema
    stats_por_tema = df.groupby('theme_1_level_1').agg({
        'content_length': ['mean', 'std', 'median'],
        'word_count': ['mean', 'std', 'median'],
        'unique_id': 'count'
    }).round(2)

    stats_por_tema.columns = [
        'media_caracteres', 'std_caracteres', 'mediana_caracteres',
        'media_palavras', 'std_palavras', 'mediana_palavras',
        'total_noticias'
    ]

    stats_por_tema = stats_por_tema.sort_values('media_palavras', ascending=False)

    # Visualização
    fig, axes = plt.subplots(1, 2, figsize=(14, 8))

    # Boxplot de palavras por tema
    top_themes = df['theme_1_level_1'].value_counts().head(10).index.tolist()
    df_top = df[df['theme_1_level_1'].isin(top_themes)]

    # Ordenar por mediana
    ordem = df_top.groupby('theme_1_level_1')['word_count'].median().sort_values(ascending=False).index

    import seaborn as sns
    sns.boxplot(
        data=df_top,
        y='theme_1_level_1',
        x='word_count',
        order=ordem,
        ax=axes[0],
        palette='Blues_r'
    )
    axes[0].set_title('Distribuição de Palavras por Tema')
    axes[0].set_xlabel('Contagem de Palavras')
    axes[0].set_ylabel('Tema')
    axes[0].set_xlim(0, 2000)  # Limitar para melhor visualização

    # Scatter plot: média vs variabilidade
    axes[1].scatter(
        stats_por_tema['media_palavras'],
        stats_por_tema['std_palavras'],
        s=stats_por_tema['total_noticias'] / 100,
        alpha=0.6,
        c='steelblue'
    )
    axes[1].set_title('Média vs Variabilidade por Tema')
    axes[1].set_xlabel('Média de Palavras')
    axes[1].set_ylabel('Desvio Padrão')

    # Adicionar labels
    for idx, row in stats_por_tema.head(5).iterrows():
        axes[1].annotate(
            idx[:20],
            (row['media_palavras'], row['std_palavras']),
            fontsize=8
        )

    plt.tight_layout()
    plt.savefig('correlacao_tamanho_tema.png', dpi=150, bbox_inches='tight')
    plt.show()

    # Teste estatístico ANOVA
    grupos = [grupo['word_count'].values for nome, grupo in df_top.groupby('theme_1_level_1')]
    f_stat, p_value = stats.f_oneway(*grupos)

    print(f"\n=== Teste ANOVA ===")
    print(f"F-statistic: {f_stat:.2f}")
    print(f"P-value: {p_value:.2e}")

    if p_value < 0.05:
        print("Conclusão: Há diferença estatisticamente significativa no tamanho dos textos entre temas.")
    else:
        print("Conclusão: Não há diferença estatisticamente significativa.")

    return stats_por_tema

# Executar
stats_tema = analisar_correlacao_tamanho_tema(df)
print("\n=== Estatísticas por Tema ===")
print(stats_tema.head(10))
```

---

## Script Completo para Análise

Para facilitar a execução de todas as análises, aqui está um script completo:

```python
#!/usr/bin/env python3
"""
analise_govbrnews.py

Script completo para análise exploratória do dataset GovBrNews.

Uso:
    python analise_govbrnews.py

Autor: Equipe DestaquesGovBr
"""

from datasets import load_dataset
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from wordcloud import WordCloud
from collections import Counter
import re
import warnings

warnings.filterwarnings('ignore')


def carregar_dados():
    """Carrega o dataset do HuggingFace."""
    print("Carregando dataset...")
    dataset = load_dataset("nitaibezerra/govbrnews")
    df = dataset['train'].to_pandas()

    # Adicionar colunas derivadas
    df['content_length'] = df['content'].str.len()
    df['word_count'] = df['content'].str.split().str.len()
    df['year'] = df['published_at'].dt.year
    df['month'] = df['published_at'].dt.month
    df['year_month'] = df['published_at'].dt.to_period('M')

    print(f"Dataset carregado: {len(df):,} documentos")
    return df


def gerar_estatisticas_basicas(df):
    """Gera estatísticas básicas do dataset."""
    print("\n" + "="*50)
    print("ESTATÍSTICAS BÁSICAS")
    print("="*50)

    print(f"\nTotal de documentos: {len(df):,}")
    print(f"Total de órgãos: {df['agency'].nunique()}")
    print(f"Total de temas (nível 1): {df['theme_1_level_1'].nunique()}")
    print(f"Período: {df['published_at'].min()} a {df['published_at'].max()}")

    print("\n--- Top 10 Órgãos ---")
    print(df['agency'].value_counts().head(10))

    print("\n--- Distribuição por Tema (Nível 1) ---")
    print(df['theme_1_level_1'].value_counts())


def gerar_visualizacoes(df, output_dir='.'):
    """Gera todas as visualizações."""
    print("\n" + "="*50)
    print("GERANDO VISUALIZAÇÕES")
    print("="*50)

    # 1. Distribuição por órgão
    fig, ax = plt.subplots(figsize=(12, 8))
    df['agency'].value_counts().head(20).plot(kind='barh', ax=ax, color='steelblue')
    ax.set_title('Top 20 Órgãos por Volume de Publicações')
    ax.set_xlabel('Quantidade')
    ax.invert_yaxis()
    plt.tight_layout()
    plt.savefig(f'{output_dir}/distribuicao_orgaos.png', dpi=150)
    plt.close()
    print("Salvo: distribuicao_orgaos.png")

    # 2. Distribuição por tema
    fig, ax = plt.subplots(figsize=(10, 8))
    df['theme_1_level_1'].value_counts().plot(kind='barh', ax=ax, color='coral')
    ax.set_title('Distribuição por Tema (Nível 1)')
    ax.set_xlabel('Quantidade')
    ax.invert_yaxis()
    plt.tight_layout()
    plt.savefig(f'{output_dir}/distribuicao_temas.png', dpi=150)
    plt.close()
    print("Salvo: distribuicao_temas.png")

    # 3. Tendência temporal
    monthly = df.groupby('year_month').size()
    fig, ax = plt.subplots(figsize=(14, 6))
    monthly.plot(ax=ax, color='steelblue', linewidth=2)
    ax.fill_between(range(len(monthly)), monthly.values, alpha=0.3)
    ax.set_title('Volume de Publicações ao Longo do Tempo')
    ax.set_xlabel('Período')
    ax.set_ylabel('Quantidade')
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig(f'{output_dir}/tendencia_temporal.png', dpi=150)
    plt.close()
    print("Salvo: tendencia_temporal.png")

    # 4. Estatísticas de texto
    fig, axes = plt.subplots(1, 2, figsize=(12, 5))

    axes[0].hist(df['word_count'].clip(upper=2000), bins=50, color='steelblue', edgecolor='white')
    axes[0].set_title('Distribuição de Palavras por Notícia')
    axes[0].set_xlabel('Palavras')
    axes[0].axvline(df['word_count'].mean(), color='red', linestyle='--', label='Média')
    axes[0].legend()

    top_themes = df['theme_1_level_1'].value_counts().head(5).index.tolist()
    df_top = df[df['theme_1_level_1'].isin(top_themes)]
    df_top.boxplot(column='word_count', by='theme_1_level_1', ax=axes[1])
    axes[1].set_title('Palavras por Tema')
    axes[1].set_xlabel('Tema')
    axes[1].set_ylabel('Palavras')
    plt.suptitle('')

    plt.tight_layout()
    plt.savefig(f'{output_dir}/estatisticas_texto.png', dpi=150)
    plt.close()
    print("Salvo: estatisticas_texto.png")


def main():
    """Função principal."""
    # Carregar dados
    df = carregar_dados()

    # Estatísticas básicas
    gerar_estatisticas_basicas(df)

    # Visualizações
    gerar_visualizacoes(df)

    print("\n" + "="*50)
    print("ANÁLISE CONCLUÍDA")
    print("="*50)


if __name__ == "__main__":
    main()
```

---

## Troubleshooting

### Problemas Comuns

#### Erro ao Carregar o Dataset

**Problema**: `ConnectionError` ou timeout ao baixar o dataset.

**Solução**:

```python
# Tente com streaming para datasets grandes
from datasets import load_dataset

dataset = load_dataset("nitaibezerra/govbrnews", streaming=True)

# Ou baixe em partes
dataset = load_dataset(
    "nitaibezerra/govbrnews",
    download_mode="force_redownload"
)
```

#### Memoria Insuficiente

**Problema**: `MemoryError` ao carregar todo o dataset.

**Solução**:

```python
# Carregar apenas uma amostra
dataset = load_dataset("nitaibezerra/govbrnews", split="train[:10000]")

# Ou usar chunks
for chunk in pd.read_csv('dados.csv', chunksize=10000):
    processar(chunk)
```

#### Erro de Encoding

**Problema**: Caracteres especiais aparecem incorretamente.

**Solução**:

```python
# Garantir encoding UTF-8
df = pd.read_csv('dados.csv', encoding='utf-8')

# Ou tentar latin-1
df = pd.read_csv('dados.csv', encoding='latin-1')
```

#### Datas Invalidas

**Problema**: Erro ao converter coluna de data.

**Solução**:

```python
# Converter com tratamento de erros
df['published_at'] = pd.to_datetime(
    df['published_at'],
    errors='coerce',  # Invalidos viram NaT
    format='mixed'
)

# Remover registros com data invalida
df = df.dropna(subset=['published_at'])
```

#### WordCloud Nao Funciona

**Problema**: Erro ao gerar nuvem de palavras.

**Solução**:

```bash
# Reinstalar wordcloud com dependencias
pip uninstall wordcloud
pip install wordcloud --no-cache-dir

# Se usar conda
conda install -c conda-forge wordcloud
```

### Dicas de Performance

1. **Use `.loc` ao invés de encadeamento**:
   ```python
   # Bom
   df.loc[df['year'] == 2023, 'content']

   # Evite
   df[df['year'] == 2023]['content']
   ```

2. **Evite loops - use vetorização**:
   ```python
   # Bom
   df['word_count'] = df['content'].str.split().str.len()

   # Evite
   for i, row in df.iterrows():
       df.loc[i, 'word_count'] = len(row['content'].split())
   ```

3. **Use categorias para colunas com poucos valores únicos**:
   ```python
   df['agency'] = df['agency'].astype('category')
   df['theme_1_level_1'] = df['theme_1_level_1'].astype('category')
   ```

---

## Navegação

| Parte | Conteúdo | Nível |
|-------|----------|-------|
| [**Parte 1: Básico**](./index.md) | Estrutura, Carregamento e Análise Exploratória Básica | Iniciante |
| [**Parte 2: Análise Temática**](./analise-tematica.md) | Distribuição por Tema, Análise Temporal, Órgãos | Intermediário |
| **Parte 3** (esta página) | Estatísticas de Texto, Nuvem de Palavras, Exercícios | Intermediário |

---

## Próximos Passos

Agora que você conhece o dataset, continue com a trilha Data Science:

- [NLP Aplicado ao Pipeline](../nlp-pipeline/index.md): Pré-processamento de texto, embeddings e busca semântica
- [ML para Classificação](../ml-classificacao/index.md): Treine modelos de classificação de texto
- [Qualidade de Dados](../qualidade-dados/index.md): Validação e métricas de qualidade

Ou volte para:

- [Setup Data Science](../../setup-datascience.md): Configuração do ambiente
- [Roteiro de Onboarding](../../roteiro-onboarding.md): Visão geral das trilhas

---

> Anterior: [Análise Temática](./analise-tematica.md)

> Próximo: [NLP Aplicado ao Pipeline](../nlp-pipeline/index.md)
