---
name: convert-md-to-odt
description: Converte relatórios Markdown para ODT com diagramas Mermaid renderizados
---

# Skill: /convert-md-to-odt

Converte relatórios técnicos Markdown (.md) para ODT (.odt) com renderização de diagramas Mermaid em imagens PNG.

## Instruções de Execução

Quando este skill for invocado:

1. **Se receber `--all`**: Execute `python scripts/convert_md_to_odt.py --all` para converter todos os relatórios

2. **Se receber nome de arquivo**: Execute `python scripts/convert_md_to_odt.py docs/docs/relatorios/{arquivo.md}`

3. **Se NÃO receber argumentos**:
   - Use Glob para listar arquivos .md em `docs/relatorios/*.md`
   - Mostre a lista formatada ao usuário com índices numerados
   - Use AskUserQuestion para perguntar qual arquivo converter (incluir opção "Todos")
   - Execute o script com o arquivo escolhido ou com --all

## Comportamento

- **Com arquivo**: `/convert-md-to-odt Relatório-26-03-24.md` → converte o arquivo especificado
- **Com --all**: `/convert-md-to-odt --all` → converte todos os .md em docs/docs/relatorios/
- **Sem argumentos**: `/convert-md-to-odt` → lista arquivos disponíveis e pergunta ao usuário qual converter

## Uso

```bash
# Converter arquivo específico
/convert-md-to-odt Relatório-Técnico-DestaquesGovbr-Requisitos-Ingestão-26-03-24.md

# Converter todos os relatórios
/convert-md-to-odt --all

# Sem argumentos: listar e escolher
/convert-md-to-odt
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

## Outputs

Os arquivos gerados ficam em:

- `docs/docs/relatorios/output/*.odt` - Arquivos ODT prontos para LibreOffice
- `docs/docs/relatorios/output/imgs/*.png` - Diagramas Mermaid renderizados (cache)

## Como Funciona

1. **Extrai diagramas Mermaid** dos blocos ` ```mermaid...``` `
2. **Renderiza para PNG** usando mermaid-cli (mmdc)
3. **Substitui no Markdown** os blocos por `![Diagrama](./imgs/diagram.png)`
4. **Converte MD → ODT** usando Pandoc via pypandoc
5. **Embarca imagens** no ODT final

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

### Erro de renderização Mermaid

- Verifique sintaxe do diagrama no [Mermaid Live Editor](https://mermaid.live)
- Diagramas muito complexos podem ter timeout (30s)
- Se persistir, o script cria um placeholder e continua

### Limpar cache de diagramas

```bash
# Se houver problemas com imagens antigas
rm -rf docs/docs/relatorios/output/imgs/
```

## Limitações Conhecidas

1. **Diagramas complexos**: Gantt ou flowcharts muito grandes podem ter timeout (30s)
2. **Tabelas largas**: Podem ficar apertadas em páginas A4 (Pandoc faz wrap automático)
3. **Links relativos**: Links para outros .md podem quebrar no ODT (Pandoc converte para referências quando possível)

## Links

- [Script completo](../../scripts/convert_md_to_odt.py)
- [README com detalhes](../../scripts/README-convert.md)
- [Pandoc Documentation](https://pandoc.org/MANUAL.html)
- [Mermaid Documentation](https://mermaid.js.org/)
