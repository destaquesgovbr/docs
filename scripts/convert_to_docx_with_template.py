#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Converte Markdown para DOCX aplicando formatações do template
Salva no diretório output/
"""

from docx import Document
from docx.shared import Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
import re
import os

def add_page_number(paragraph):
    """Adiciona numeração 'Página X de Y'"""
    paragraph.alignment = WD_ALIGN_PARAGRAPH.RIGHT

    run1 = paragraph.add_run('Página ')

    # Campo PAGE
    fldChar1 = OxmlElement('w:fldChar')
    fldChar1.set(qn('w:fldCharType'), 'begin')
    run2 = paragraph.add_run()
    run2._r.append(fldChar1)

    instrText = OxmlElement('w:instrText')
    instrText.set(qn('xml:space'), 'preserve')
    instrText.text = 'PAGE'
    run3 = paragraph.add_run()
    run3._r.append(instrText)

    fldChar2 = OxmlElement('w:fldChar')
    fldChar2.set(qn('w:fldCharType'), 'end')
    run4 = paragraph.add_run()
    run4._r.append(fldChar2)

    run5 = paragraph.add_run(' de ')

    # Campo NUMPAGES
    fldChar3 = OxmlElement('w:fldChar')
    fldChar3.set(qn('w:fldCharType'), 'begin')
    run6 = paragraph.add_run()
    run6._r.append(fldChar3)

    instrText2 = OxmlElement('w:instrText')
    instrText2.set(qn('xml:space'), 'preserve')
    instrText2.text = 'NUMPAGES'
    run7 = paragraph.add_run()
    run7._r.append(instrText2)

    fldChar4 = OxmlElement('w:fldChar')
    fldChar4.set(qn('w:fldCharType'), 'end')
    run8 = paragraph.add_run()
    run8._r.append(fldChar4)

def add_table(doc, table_lines):
    """Adiciona tabela Markdown"""
    if len(table_lines) < 2:
        return

    # Remove linhas separadoras
    table_lines = [l for l in table_lines if not re.match(r'^\|[\s\-:]+\|$', l)]
    if len(table_lines) < 1:
        return

    # Conta colunas
    first = table_lines[0].strip('|')
    cols = len([c for c in first.split('|') if c.strip()])
    rows = len(table_lines)

    table = doc.add_table(rows=rows, cols=cols)
    table.style = 'Light Grid Accent 1'

    for r_idx, line in enumerate(table_lines):
        cells = [c.strip() for c in line.strip('|').split('|')]
        for c_idx, text in enumerate(cells):
            if c_idx < len(table.rows[r_idx].cells):
                cell = table.rows[r_idx].cells[c_idx]
                cell.text = text
                if r_idx == 0:  # Header
                    for p in cell.paragraphs:
                        for run in p.runs:
                            run.font.bold = True

def main():
    # Caminhos
    template_path = 'docs/relatorios/templates/Template Relatório-Técnico-DestaquesGovbr Tema 7.docx'
    input_path = 'docs/relatorios/Relatório-Técnico-DestaquesGovbr-Requisitos-Ingestão-25-12-31-Versao-01.md'
    output_path = 'docs/relatorios/output/Relatório-Técnico-DestaquesGovbr-Requisitos-Ingestão-25-12-31-Versao-02.docx'

    print("Iniciando conversao...")
    print(f"Entrada: {input_path}")
    print(f"Template: {template_path}")
    print(f"Saida: {output_path}")

    # Carrega template
    template = Document(template_path)
    doc = Document()

    # Copia margens
    t_sec = template.sections[0]
    sec = doc.sections[0]
    sec.top_margin = t_sec.top_margin
    sec.bottom_margin = t_sec.bottom_margin
    sec.left_margin = t_sec.left_margin
    sec.right_margin = t_sec.right_margin

    # Cabeçalho
    header = sec.header
    for p in header.paragraphs:
        p.clear()

    header.add_paragraph()

    p_title = header.add_paragraph()
    p_title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = p_title.add_run('Relatório Técnico DestaquesGovbr [Requisitos de Ingestão]')
    run.font.name = 'Arial'
    run.font.size = Pt(16)

    p_num = header.add_paragraph()
    add_page_number(p_num)

    # Rodapé
    footer = sec.footer
    for p in footer.paragraphs:
        p.clear()

    p_footer = footer.add_paragraph()
    p_footer.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    run_f = p_footer.add_run('CPQD – Todos os direitos reservados.')
    run_f.font.name = 'Open Sans'
    run_f.font.size = Pt(8)

    print("Formatacoes do template aplicadas")

    # Lê MD
    with open(input_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Remove comentários HTML
    content = re.sub(r'<!--.*?-->', '', content, flags=re.DOTALL)

    lines = content.split('\n')
    i = 0
    table_buf = []
    in_table = False
    in_code = False
    code_buf = []
    code_type = ''

    while i < len(lines):
        line = lines[i]

        # Código
        if line.strip().startswith('```'):
            if not in_code:
                in_code = True
                code_type = line.strip()[3:]
                code_buf = []
            else:
                in_code = False
                if code_buf:
                    if code_type.lower() == 'mermaid':
                        p = doc.add_paragraph()
                        run = p.add_run('[Diagrama Mermaid]')
                        run.font.italic = True
                        run.font.color.rgb = RGBColor(128, 128, 128)
                    else:
                        p = doc.add_paragraph()
                        run = p.add_run('\n'.join(code_buf))
                        run.font.name = 'Courier New'
                        run.font.size = Pt(9)
                code_buf = []
            i += 1
            continue

        if in_code:
            code_buf.append(line)
            i += 1
            continue

        # Tabelas
        if line.strip().startswith('|') and '|' in line[1:]:
            if not in_table:
                in_table = True
                table_buf = []
            table_buf.append(line)
            i += 1
            continue
        elif in_table:
            in_table = False
            add_table(doc, table_buf)
            table_buf = []
            continue

        # Títulos
        if line.startswith('#'):
            m = re.match(r'^(#+)\s+(.+)$', line)
            if m:
                level = len(m.group(1))
                text = m.group(2).strip()
                text = re.sub(r'\*\*(.*?)\*\*', r'\1', text)
                doc.add_heading(text, level=min(level, 5))

        # Linha horizontal
        elif line.strip() == '---':
            p = doc.add_paragraph()
            run = p.add_run('─' * 80)
            run.font.color.rgb = RGBColor(192, 192, 192)

        # Texto
        elif line.strip():
            text = line.strip()

            # Listas
            if re.match(r'^[\*\-]\s+', text):
                text = re.sub(r'^[\*\-]\s+', '', text)
                text = re.sub(r'\*\*(.*?)\*\*', r'\1', text)
                doc.add_paragraph(text, style='List Bullet')
            elif re.match(r'^\d+\.\s+', text):
                text = re.sub(r'^\d+\.\s+', '', text)
                text = re.sub(r'\*\*(.*?)\*\*', r'\1', text)
                doc.add_paragraph(text, style='List Number')
            else:
                text = re.sub(r'\*\*(.*?)\*\*', r'\1', text)
                text = re.sub(r'\*(.*?)\*', r'\1', text)
                text = re.sub(r'`([^`]+)`', r'\1', text)
                doc.add_paragraph(text)

        i += 1

    # Salva buffer pendente
    if in_table and table_buf:
        add_table(doc, table_buf)

    # Salva
    os.makedirs('docs/relatorios/output', exist_ok=True)
    doc.save(output_path)

    print(f"\nArquivo criado: {output_path}")
    print("\nConfiguracoes:")
    print("  - Margens: 1.27 cm")
    print("  - Cabecalho: Titulo + Pagina X de Y")
    print("  - Rodape: CPQD - Todos os direitos reservados")
    print("\nConcluido!")

if __name__ == '__main__':
    main()