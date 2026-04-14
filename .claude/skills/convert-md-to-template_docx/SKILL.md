---
name: convert-md-to-template_docx
description: Converte relatórios Markdown para DOCX com template oficial, diagramas Mermaid renderizados e syntax highlighting
---

# Skill: /convert-md-to-template_docx

Converte relatórios técnicos Markdown (.md) para DOCX (.docx) usando o template oficial do INSPIRE Meta 7, com renderização de diagramas Mermaid para PNG e syntax highlighting de código. Preserva toda formatação, cabeçalho, rodapé e estrutura do template.

## Instruções de Execução

Quando este skill for invocado:

1. **Se receber `--all`**: Execute `python scripts/convert_to_docx_with_template.py --all` para converter todos os relatórios

2. **Se receber nome de arquivo**: Execute `python scripts/convert_to_docx_with_template.py docs/relatorios/{arquivo.md}`

3. **Se NÃO receber argumentos**:
   - Use Glob para listar arquivos .md em `docs/relatorios/*.md`
   - Mostre a lista formatada ao usuário com índices numerados
   - Use AskUserQuestion para perguntar qual arquivo converter (incluir opção "Todos")
   - Execute o script com o arquivo escolhido ou com --all

## Comportamento

- **Com arquivo**: `/convert-md-to-template_docx {arquivo.md}` → converte o arquivo especificado
- **Com --all**: `/convert-md-to-template_docx --all` → converte todos os .md em docs/relatorios/
- **Sem argumentos**: `/convert-md-to-template_docx` → lista arquivos disponíveis e pergunta ao usuário qual converter

## Uso

```bash
# Converter arquivo específico
/convert-md-to-template_docx Relatório-Técnico-DestaquesGovbr-Requisitos-Ingestão-26-03-24.md

# Converter todos os relatórios
/convert-md-to-template_docx --all

# Sem argumentos: listar e escolher
/convert-md-to-template_docx
```

## Template Utilizado

O script usa o template oficial:
- **Caminho**: `docs/relatorios/templates/Template Relatório-Técnico-DestaquesGovbr Tema 7.docx`
- **Conteúdo preservado**:
  - Capa com logo INSPIRE Meta 7
  - Informações do convênio (MGI/Finep)
  - Histórico de versões
  - Nível de sigilo
  - Cabeçalho e rodapé formatados
  - Margens configuradas (1.27cm)

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

- `docs/relatorios/output/*.docx` - Arquivos DOCX prontos para MS Word com template aplicado
- `docs/relatorios/output/imgs/*.png` - Diagramas Mermaid renderizados (cache compartilhado)

## Características do DOCX Gerado

### Estrutura
- **Template preservado**: Capa, cabeçalho, rodapé e formatações originais
- **Conteúdo MD**: Inserido após o parágrafo "Sumário"

### Fontes
- **Texto normal**: Arial 11pt
- **Código fonte**: Courier New 11pt

### Código
- **Syntax highlighting**: Pygments (cores automáticas por linguagem)
- **Fundo cinza claro** em blocos de código
- **Código inline**: Courier New

### Diagramas
- **Mermaid → PNG**: Renderizados automaticamente
- **Largura ajustada**: 6in (caber na página A4)
- **Cache**: PNG reutilizado se diagrama não mudar
- **Erro**: Placeholder textual se falhar renderização

### Tabelas
- **Apenas bordas horizontais** (sem bordas laterais)
- **Cabeçalho**: Borda preta grossa + negrito
- **Linhas**: Bordas cinza finas
- **Largura**: 100% da página

### Outros
- **Links internos**: Funcionais (âncoras entre seções)
- **TOC (Sumário)**: Título convertido para "Sumário"
- **Emojis**: Removidos automaticamente (exceto ✅ ❌ em tabelas)

## Diferença vs /convert-md-to-docx

| Característica | convert-md-to-docx | convert-md-to-template_docx |
|----------------|--------------------|-----------------------------|
| Template | Não usa | ✅ Template oficial INSPIRE |
| Cabeçalho/Rodapé | Genérico | ✅ CPQD + Relatório Técnico |
| Capa | Não tem | ✅ Capa oficial com logo |
| Diagramas Mermaid | ✅ Renderiza PNG | ✅ Renderiza PNG |
| Syntax highlighting | ✅ Sim (pygments) | ✅ Sim (pygments) |
| Tabelas | ✅ Bordas horizontais | ✅ Bordas horizontais |
| TOC (Sumário) | Automático (3 níveis) | Do template |
| Customização | Estilos customizados | Template + estilos Pandoc |

**Conclusão**: Agora ambas as skills têm as mesmas funcionalidades de renderização, mas `/convert-md-to-template_docx` adiciona o template oficial do INSPIRE.

## Como Funciona

1. **Processa diagramas Mermaid**:
   - Extrai blocos ` ```mermaid ` do MD
   - Renderiza cada diagrama para PNG usando mermaid-cli (mmdc)
   - Substitui blocos por `![Diagrama](./imgs/diagram.png)` no MD
   - Cache: reutiliza PNG se diagrama não mudar (hash MD5)

2. **Converte MD → DOCX via Pandoc**:
   - Usa pypandoc com `--highlight-style=pygments`
   - Syntax highlighting automático por linguagem
   - Gera DOCX temporário com todo conteúdo formatado

3. **Mescla template + conteúdo**:
   - Carrega template INSPIRE (preserva capa/cabeçalho/rodapé)
   - Carrega DOCX temporário gerado pelo Pandoc
   - Copia todos os elementos do body do DOCX para o template
   - Template fica no início, conteúdo do MD logo após

4. **Salva resultado final**:
   - DOCX com template + conteúdo + diagramas PNG embedded
   - Remove arquivo temporário

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
- Mensagem: `[AVISO] Erro no diagrama X: ...`

### Limpar cache de diagramas

```bash
# Se houver problemas com imagens antigas (cache compartilhado)
rm -rf docs/relatorios/output/imgs/
```

## Limitações Conhecidas

1. **Diagramas Mermaid complexos**: Gantt ou flowcharts muito grandes podem ter timeout (30s)
2. **Tabelas largas**: Podem ficar apertadas em páginas A4 (Pandoc faz wrap automático)
3. **TOC**: Título convertido para "Sumário", mas links internos podem não funcionar perfeitamente
4. **Estilos do template**: Alguns estilos do Pandoc podem não combinar 100% com o template
5. **Posição do conteúdo**: Sempre adicionado após o template (não há opção de inserir em posição específica)

## Quando Usar Esta Skill vs Outras

**Use `/convert-md-to-template_docx`** quando:
- ✅ Precisa do template oficial INSPIRE com capa/cabeçalho/rodapé
- ✅ Quer relatórios com identidade visual padronizada CPQD
- ✅ Vai entregar para MGI/Finep com logo e formatação oficial
- ✅ Precisa de diagramas Mermaid renderizados + syntax highlighting + template

**Use `/convert-md-to-docx`** quando:
- ✅ Não precisa do template oficial
- ✅ Quer customizar completamente os estilos
- ✅ Precisa de TOC automático (3 níveis)
- ✅ Quer controle total sobre margens e formatação

**Use `/convert-md-to-odt`** quando:
- ✅ Usa LibreOffice ao invés de MS Word
- ✅ Precisa de formato OpenDocument
- ✅ Trabalha em ambiente Linux sem MS Office

## Links

- [Script completo](../../../scripts/convert_to_docx_with_template.py)
- [Template DOCX](../../../docs/relatorios/templates/Template%20Relatório-Técnico-DestaquesGovbr%20Tema%207.docx)
- [Script convert_md_to_docx (sem template)](../../../scripts/convert_md_to_docx.py)
- [python-docx Documentation](https://python-docx.readthedocs.io/)