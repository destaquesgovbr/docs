#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Verificação de hyperlinks no DOCX gerado
"""

from docx import Document
from docx.oxml.shared import qn

import sys

if len(sys.argv) > 1:
    doc_path = sys.argv[1]
else:
    doc_path = "docs/relatorios/output/Relatório-Técnico-DestaquesGovbr-Pipeline_ETL-26-04-Versao-01.docx"

print(f"\nVerificando hyperlinks em: {doc_path}\n")
print("=" * 70)

doc = Document(doc_path)

# Contar hyperlinks
hyperlink_count = 0
hyperlinks_found = []

for paragraph in doc.paragraphs:
    for element in paragraph._element:
        if element.tag == qn('w:hyperlink'):
            hyperlink_count += 1
            # Tentar extrair URL
            rel_id = element.get(qn('r:id'))
            url = "N/A"
            if rel_id:
                try:
                    rel = doc.part.rels[rel_id]
                    url = rel.target_ref
                except:
                    pass

            # Extrair texto
            text = ""
            for run_elem in element.findall(qn('w:r')):
                for text_elem in run_elem.findall(qn('w:t')):
                    text += text_elem.text

            hyperlinks_found.append({
                'text': text[:50] + ('...' if len(text) > 50 else ''),
                'url': url[:70] + ('...' if len(url) > 70 else '')
            })

print(f"\nTotal de hyperlinks encontrados: {hyperlink_count}\n")

if hyperlink_count > 0:
    print("Primeiros 10 hyperlinks:\n")
    for i, link in enumerate(hyperlinks_found[:10], 1):
        print(f"{i}. Texto: {link['text']}")
        print(f"   URL: {link['url']}\n")

print("=" * 70)
print(f"\n[OK] Esperado: ~31 hyperlinks externos")
print(f"[OK] Encontrado: {hyperlink_count} hyperlinks")

if hyperlink_count >= 30:
    print(f"\nSUCESSO! Hyperlinks foram preservados!\n")
else:
    print(f"\nATENCAO: Menos hyperlinks que esperado\n")