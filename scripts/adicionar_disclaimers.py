#!/usr/bin/env python3
"""Adiciona disclaimers RF08/RF09 e seção de limitações de forma segura."""

import sys

filepath = sys.argv[1] if len(sys.argv) > 1 else None
if not filepath:
    print("Uso: python adicionar_disclaimers.py <arquivo.md>")
    sys.exit(1)

with open(filepath, 'r', encoding='utf-8') as f:
    lines = f.readlines()

output_lines = []
i = 0

while i < len(lines):
    line = lines[i]
    output_lines.append(line)

    # Adicionar disclaimer após RF08
    if '#### **RF08: Análise de Sentimento (Positivo/Neutro/Negativo)**' in line:
        # Adicionar linha em branco se não existir
        if i + 1 < len(lines) and lines[i + 1].strip():
            output_lines.append('\n')
        output_lines.append('**NOTA:** A análise de sentimento atual é uma implementação elementar via LLM. Não foi baseada em estudos científicos formais nem validada contra datasets padrão. Status: Experimental, sujeito a revisão em Q3/2026.\n')
        output_lines.append('\n')

    # Adicionar disclaimer após RF09
    elif '#### **RF09: Extração de Entidades Nomeadas (NER)**' in line:
        if i + 1 < len(lines) and lines[i + 1].strip():
            output_lines.append('\n')
        output_lines.append('**NOTA:** A extração de entidades (NER) atual é uma implementação elementar via LLM. Não foi comparada com modelos especializados (spaCy, Stanza) nem validada formalmente. A precisão de 85% é baseada em sample pequeno (n=200). Status: Experimental, sujeito a revisão em Q4/2026.\n')
        output_lines.append('\n')

    # Adicionar seção de limitações antes de RF10
    elif '#### **RF10: Geração de Embeddings' in line:
        output_lines.insert(-1, '\n---\n\n')
        output_lines.insert(-1, '### **Limitações Conhecidas (RF08/RF09)**\n\n')
        output_lines.insert(-1, '**Análise de Sentimento (RF08):**\n')
        output_lines.insert(-1, '- Implementação básica sem benchmarking contra datasets padrão\n')
        output_lines.insert(-1, '- Validação baseada em sample limitado (n=100)\n')
        output_lines.insert(-1, '- Não captura nuances de ironia ou sarcasmo\n')
        output_lines.insert(-1, '- Roadmap: Q3/2026 - Benchmark e validação formal\n\n')
        output_lines.insert(-1, '**Extração de Entidades (RF09):**\n')
        output_lines.insert(-1, '- Não comparada com modelos especializados\n')
        output_lines.insert(-1, '- Precisão de 85% baseada em sample pequeno (n=200)\n')
        output_lines.insert(-1, '- Inferência de gênero por nome pode ter falsos positivos\n')
        output_lines.insert(-1, '- Roadmap: Q4/2026 - Comparação com modelos especializados + validação cruzada\n\n')
        output_lines.insert(-1, '**Status:** Ambas funcionalidades marcadas como Experimental até validação científica formal.\n\n')
        output_lines.insert(-1, '---\n\n')

    i += 1

# Salvar arquivo
with open(filepath, 'w', encoding='utf-8') as f:
    f.writelines(output_lines)

print(f"Disclaimers adicionados com sucesso em: {filepath}")
print(f"Total de linhas: {len(output_lines)}")
