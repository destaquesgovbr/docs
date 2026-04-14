---
name: convert-md-to-docx
description: Converte relatórios Markdown para DOCX com diagramas Mermaid renderizados
---

# Skill: /convert-md-to-docx

Converte relatórios técnicos Markdown (.md) para DOCX (.docx) com renderização de diagramas Mermaid em imagens PNG.

## Instruções de Execução

Quando este skill for invocado:

1. **Se receber `--all`**: Execute `python scripts/convert_md_to_docx.py --all` para converter todos os relatórios

2. **Se receber nome de arquivo**: Execute `python scripts/convert_md_to_docx.py docs/docs/relatorios/{arquivo.md}`

3. **Se NÃO receber argumentos**:
   - Use Glob para listar arquivos .md em `docs/relatorios/*.md`
   - Mostre a lista formatada ao usuário com índices numerados
   - Use AskUserQuestion para perguntar qual arquivo converter (incluir opção "Todos")
   - Execute o script com o arquivo escolhido ou com --all

## Comportamento

- **Com arquivo**: `/convert-md-to-docx {arquivo.md}` → converte o arquivo especificado
- **Com --all**: `/convert-md-to-docx --all` → converte todos os .md em docs/docs/relatorios/
- **Sem argumentos**: `/convert-md-to-docx` → lista arquivos disponíveis e pergunta ao usuário qual converter

## Uso

```bash
# Converter arquivo específico
/convert-md-to-docx Relatório-Técnico-DestaquesGovbr-Requisitos-Ingestão-26-03-24.md

# Converter todos os relatórios
/convert-md-to-docx --all

# Sem argumentos: listar e escolher
/convert-md-to-docx
```

## Dependências

### Sistema (obrigatório)

- **pandoc** - Conversor universal de documentos
  ```bash
  # macOS
  brew install pandoc

  # Linux
  apt install pandoc

  # Windows
  choco install pandoc
  ```

- **mermaid-cli** - Renderizador de diagramas Mermaid
  ```bash
  npm install -g @mermaid-js/mermaid-cli
  ```

### Python (obrigatório)

- **pypandoc** - Wrapper Python do Pandoc
  ```bash
  pip install pypandoc
  # ou
  poetry add pypandoc
  ```

- **python-docx** - Manipulação de arquivos DOCX
  ```bash
  pip install python-docx
  # ou
  poetry add python-docx
  ```

## Outputs

Os arquivos gerados ficam em:

- `docs/docs/relatorios/output/*.docx` - Arquivos DOCX prontos para MS Word
- `docs/docs/relatorios/output/imgs/*.png` - Diagramas Mermaid renderizados (cache compartilhado)

## Características do DOCX Gerado

### Fontes
- **Texto normal**: Arial 11pt
- **Código fonte**: Courier New 10pt

### Código
- Syntax highlighting (pygments)
- Fundo cinza claro
- Blocos de código formatados

### Tabelas
- Apenas bordas horizontais (sem bordas laterais)
- Linhas separadas visualmente

### Diagramas
- Renderizados como PNG
- Largura ajustada para 6in (caber na página A4)
- Embarcados no DOCX

### Outros
- **Sumário (TOC)** automático com 3 níveis
- **Sem emojis** (removidos automaticamente)
- **Links internos** funcionais

## Como Funciona

1. **Extrai diagramas Mermaid** dos blocos ` ```mermaid...``` `
2. **Renderiza para PNG** usando mermaid-cli (mmdc)
3. **Substitui no Markdown** os blocos por `![Diagrama](./imgs/diagram.png)`
4. **Converte MD → DOCX** usando Pandoc via pypandoc
5. **Customiza estilos** usando python-docx (fontes Arial/Courier New)
6. **Embarca imagens** no DOCX final

## Troubleshooting

### Erro: "mmdc not found"

```bash
npm install -g @mermaid-js/mermaid-cli

# Verificar instalação
mmdc --version
```

### Erro: "pandoc not found"

```bash
# macOS
brew install pandoc

# Linux
apt install pandoc

# Windows
choco install pandoc

# Verificar instalação
pandoc --version
```

### Erro: "pypandoc não está instalado"

```bash
pip install pypandoc
# ou com Poetry
poetry add pypandoc
```

### Erro: "python-docx não está instalado"

```bash
pip install python-docx
# ou com Poetry
poetry add python-docx
```

### Erro de renderização Mermaid

- Verifique sintaxe do diagrama no [Mermaid Live Editor](https://mermaid.live)
- Diagramas muito complexos podem ter timeout (30s)
- Se persistir, o script cria um placeholder e continua

### Limpar cache de diagramas

```bash
# Se houver problemas com imagens antigas (cache compartilhado com ODT)
rm -rf docs/docs/relatorios/output/imgs/
```

## Diferenças ODT vs DOCX

| Característica | ODT | DOCX |
|----------------|-----|------|
| Software | LibreOffice | MS Word |
| Formato | OpenDocument | Office Open XML |
| Customização | Mais complexa | Mais direta |
| Template | reference.odt | reference.docx (opcional) |
| Pós-processamento | XML manual | python-docx |

## Limitações Conhecidas

1. **Diagramas complexos**: Gantt ou flowcharts muito grandes podem ter timeout (30s)
2. **Tabelas largas**: Podem ficar apertadas em páginas A4 (Pandoc faz wrap automático)
3. **Links relativos**: Links para outros .md podem quebrar no DOCX
4. **Estilos avançados**: Customizações avançadas requerem template DOCX

## Links

- [Script completo](../../scripts/convert_md_to_docx.py)
- [Script ODT (referência)](../../scripts/convert_md_to_odt.py)
- [Pandoc Documentation](https://pandoc.org/MANUAL.html)
- [Mermaid Documentation](https://mermaid.js.org/)
- [python-docx Documentation](https://python-docx.readthedocs.io/)
