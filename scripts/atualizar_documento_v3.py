#!/usr/bin/env python3
"""
Script para aplicar atualizações técnicas no documento v3.
Atualiza: NOVA LITE 2, NER/Sentiment para experimental, remove HuggingFace restantes.
"""

import re
import sys

def atualizar_documento(filepath):
    print(f"Lendo arquivo: {filepath}")
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    # Backup
    backup_path = filepath.replace('.md', '.backup.md')
    with open(backup_path, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"Backup criado: {backup_path}")

    # 1. Atualizar RF07 para NOVA LITE 2
    print("\n1. Atualizando RF07 (Sumarização) para NOVA LITE 2...")

    # Atualizar método de sumarização
    content = re.sub(
        r'(\*\*Método:\*\*) Sumarização abstrativa via LLM \(mesmo prompt de classificação, campo `summary`\)',
        r'\1 Sumarização abstrativa via **Amazon Nova Lite 2** (`amazon.nova-lite-v1:0`) com prompt dedicado',
        content
    )

    # Atualizar título na tabela de requisitos
    content = re.sub(
        r'\| \*\*RF07\*\* \| Geração automática de resumos \|',
        r'| **RF07** | Geração automática de resumos (NOVA LITE 2) |',
        content
    )

    # 2. Adicionar disclaimer RF08 (Sentiment)
    print("2. Adicionando disclaimer RF08 (Análise de Sentimento)...")

    rf08_pattern = r'(#### \*\*RF08: Análise de Sentimento \(Positivo/Neutro/Negativo\)\*\*\s+\*\*Objetivo:\*\*[^\n]+\n)'
    rf08_disclaimer = r'''\1
> **⚠️ NOTA DE IMPLEMENTAÇÃO:** A análise de sentimento atual é uma implementação **elementar** via LLM (campo `sentiment` no output de classificação). Não foi baseada em estudos científicos formais nem validada contra datasets padrão (ex: SemEval, IMDB). **Status: Experimental, sujeito a revisão em Q3/2026.**

'''
    content = re.sub(rf08_pattern, rf08_disclaimer, content, count=1)

    # Atualizar método RF08
    content = re.sub(
        r'(\*\*Método:\*\*) Análise via LLM \(campo `sentiment` no output\)',
        r'\1 Análise via LLM (campo `sentiment` no output) - **Implementação experimental**',
        content
    )

    # 3. Adicionar disclaimer RF09 (NER)
    print("3. Adicionando disclaimer RF09 (NER)...")

    rf09_pattern = r'(#### \*\*RF09: Extração de Entidades Nomeadas \(NER\)\*\*\s+\*\*Objetivo:\*\*[^\n]+\n)'
    rf09_disclaimer = r'''\1
> **⚠️ NOTA DE IMPLEMENTAÇÃO:** A extração de entidades (NER) atual é uma implementação **elementar** via LLM (campo `entities` no output de classificação). Não foi comparada com modelos especializados (spaCy pt_core_news_lg, Stanza PT, etc.) nem validada formalmente. A precisão de 85% é baseada em sample pequeno (n=200) com anotação não-independente. **Status: Experimental, sujeito a revisão em Q4/2026.**

'''
    content = re.sub(rf09_pattern, rf09_disclaimer, content, count=1)

    # Atualizar método RF09
    content = re.sub(
        r'(\*\*Método:\*\*) Named Entity Recognition via LLM \(campo `entities` no output\)',
        r'\1 Named Entity Recognition via LLM (campo `entities` no output) - **Implementação experimental**',
        content
    )

    # 4. Atualizar status na tabela de requisitos
    print("4. Atualizando tabela de requisitos (RF08/RF09 para Experimental)...")

    content = re.sub(
        r'\| \*\*RF08\*\* \| Análise de sentimento \| ([^|]+) \| ([^|]+) \| OK Impl\. \|',
        r'| **RF08** | Análise de sentimento | \1 | \2 | 🟡 Experimental |',
        content
    )

    content = re.sub(
        r'\| \*\*RF09\*\* \| Extração de entidades \(NER\) \| ([^|]+) \| ([^|]+) \| OK Impl\. \|',
        r'| **RF09** | Extração de entidades (NER) | \1 | \2 | 🟡 Experimental |',
        content
    )

    # 5. Atualizar diagrama sequence (separar classificação, sumarização, sentiment/NER)
    print("5. Atualizando diagrama sequence (separar Claude Haiku, NOVA LITE 2)...")

    # Buscar e substituir bloco do diagrama
    old_diagram = r'''Note over EW,LLM: Classificação Temática \+ Sumarização
    EW->>LLM: \{title, content, taxonomia\}
    LLM-->>EW: \{theme_l1/l2/l3, summary, sentiment, entities, confidence, reasoning\}'''

    new_diagram = '''Note over EW,LLM: Classificação Temática (Claude Haiku)
    EW->>+LLM: {title, content, taxonomia}
    LLM-->>-EW: {theme_l1/l2/l3, confidence, reasoning}

    Note over EW,LLM: Sumarização (NOVA LITE 2)
    EW->>+LLM: {title, content}
    LLM-->>-EW: {summary}

    Note over EW,LLM: Sentiment/NER (Experimental)
    EW->>+LLM: {title, content}
    LLM-->>-EW: {sentiment, entities}'''

    content = re.sub(old_diagram, new_diagram, content, flags=re.MULTILINE)

    # 6. Adicionar nota sobre limitações NER/Sentiment em seções de vieses
    print("6. Adicionando notas sobre limitações NER/Sentiment...")

    # Na seção de viés demográfico
    content = re.sub(
        r'(- NER \(Named Entity Recognition\) não apresenta viés significativo de gênero)',
        r'\1\n\n> **⚠️ NOTA:** Análise preliminar baseada em implementação NER elementar. Validação científica formal pendente (Q4/2026).',
        content,
        count=1
    )

    # 7. Adicionar seção de limitações conhecidas (após RF09)
    print("7. Adicionando seção de limitações conhecidas...")

    limitacoes = '''

---

### **Limitações Conhecidas (RF08/RF09)**

**Análise de Sentimento (RF08):**
- Implementação básica sem benchmarking contra datasets padrão (SemEval, IMDB, etc.)
- Validação baseada em sample limitado (n=100) sem anotadores independentes
- Não captura nuances de ironia, sarcasmo ou sentimento misto
- **Roadmap:** Q3/2026 - Benchmark contra datasets padrão + validação formal

**Extração de Entidades (RF09):**
- Não comparada com modelos especializados (spaCy pt_core_news_lg, Stanza PT)
- Precisão de 85% baseada em sample pequeno (n=200)
- Inferência de gênero por nome pode ter falsos positivos
- Não captura identidade de gênero auto-declarada
- **Roadmap:** Q4/2026 - Comparação com modelos especializados (F1-score) + validação cruzada (n≥500)

**Status:** Ambas funcionalidades marcadas como **🟡 Experimental** até validação científica formal.

---
'''

    # Inserir após a seção RF09
    content = re.sub(
        r'(#### \*\*RF10: Geração de Embeddings)',
        limitacoes + r'\1',
        content,
        count=1
    )

    # 8. Remover referências HuggingFace restantes (manter apenas menções históricas)
    print("8. Limpando referências HuggingFace restantes...")

    # Remover linhas com tabela de datasets HuggingFace
    content = re.sub(
        r'\| \*\*govbrnews\*\* \| HuggingFace[^\n]+\n',
        '',
        content
    )
    content = re.sub(
        r'\| \*\*validation_sample\*\* \| HuggingFace[^\n]+\n',
        '',
        content
    )

    # Substituir "Datasets: HuggingFace" por "Datasets: PostgreSQL"
    content = re.sub(
        r'Datasets: HuggingFace \(300k\+ notícias\)',
        'Datasets: PostgreSQL PGVector (310k+ notícias operacionais)',
        content
    )

    # Salvar arquivo atualizado
    output_path = filepath
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(content)

    print(f"\nOK Arquivo atualizado salvo: {output_path}")
    print(f"OK Backup disponível em: {backup_path}")

    # Estatísticas
    print("\nStats Estatísticas de atualizações:")
    print(f"  - NOVA LITE 2: {content.count('NOVA LITE 2')} menções")
    print(f"  - Experimental: {content.count('🟡 Experimental')} marcações")
    print(f"  - Disclaimers: {content.count('⚠️ NOTA')} adicionados")
    print(f"  - PostgreSQL PGVector: {content.count('PostgreSQL PGVector')} menções")
    print(f"  - HuggingFace restantes: {content.count('HuggingFace') + content.count('huggingface')}")

if __name__ == '__main__':
    filepath = 'c:/Users/joserm/Documents/Projetos/Inspire/Meta-7/Git/docs/docs/relatorios/Relatorio-Tecnico-Transparencia-Vieses-Personalizacao-26-06-COMPLETO-v3-MERGED-ATUALIZADO.md'

    if len(sys.argv) > 1:
        filepath = sys.argv[1]

    atualizar_documento(filepath)
    print("\nSUCCESS Atualização concluída com sucesso!")
