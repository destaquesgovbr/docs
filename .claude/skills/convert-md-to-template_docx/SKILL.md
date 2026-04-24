---
name: convert-md-to-template_docx
description: Converte relatórios Markdown para DOCX com template oficial usando fluxo de 2 etapas (docxcompose) para 100% de preservação de estilos, imagens, fontes e diagramas
---

# Skill: /convert-md-to-template_docx

Converte relatórios técnicos Markdown (.md) para DOCX (.docx) usando o template oficial do INSPIRE Meta 7, com renderização de diagramas Mermaid para PNG e syntax highlighting de código. 

**Utiliza fluxo de 2 etapas com docxcompose** para garantir **100% de preservação** de todos os elementos: estilos, fontes, imagens do header/footer (logos INSPIRE/CPQD), tabelas, diagramas e configurações.

## Instruções de Execução

Este skill utiliza o **fluxo de 2 etapas com docxcompose** para garantir **100% de preservação** de todos os elementos (estilos, fontes, imagens do header/footer, tabelas, diagramas).

Quando este skill for invocado:

1. **Se receber `--all`**: Para cada arquivo .md em `docs/relatorios/`:
   - **Passo 1**: Execute `python scripts/convert_md_to_docx.py docs/relatorios/{arquivo.md}` (conversão limpa, sem template)
   - **Passo 2**: Execute `python scripts/merge_docx_with_docxcompose.py "docs/relatorios/templates/Template Relatório-Técnico-DestaquesGovbr Tema 7.docx" "docs/relatorios/output/{arquivo}.docx" "docs/relatorios/output/{arquivo}-FINAL.docx"`

2. **Se receber nome de arquivo**: Execute o fluxo de 2 etapas:
   - **Passo 1**: Execute `python scripts/convert_md_to_docx.py docs/relatorios/{arquivo.md}` (conversão limpa, sem template)
   - **Passo 2**: Execute `python scripts/merge_docx_with_docxcompose.py "docs/relatorios/templates/Template Relatório-Técnico-DestaquesGovbr Tema 7.docx" "docs/relatorios/output/{arquivo}.docx" "docs/relatorios/output/{arquivo}-FINAL.docx"`
   - Informe ao usuário que o arquivo final está em `{arquivo}-FINAL.docx`

3. **Se NÃO receber argumentos**:
   - Use Glob para listar arquivos .md em `docs/relatorios/*.md`
   - Mostre a lista formatada ao usuário com índices numerados
   - Use AskUserQuestion para perguntar qual arquivo converter (incluir opção "Todos")
   - Execute o fluxo de 2 etapas para o(s) arquivo(s) escolhido(s)

## Comportamento

- **Com arquivo**: `/convert-md-to-template_docx {arquivo.md}` → converte o arquivo especificado (100% preservação via docxcompose)
- **Com --all**: `/convert-md-to-template_docx --all` → converte todos os .md em docs/relatorios/ (100% preservação)
- **Sem argumentos**: `/convert-md-to-template_docx` → lista arquivos disponíveis e pergunta ao usuário qual converter

**Método**: Sempre usa fluxo de 2 etapas (MD → DOCX limpo → Merge com template via docxcompose) para garantir preservação total.

## Uso

```bash
# Converter arquivo específico (100% preservação)
/convert-md-to-template_docx Relatório-Técnico-DestaquesGovbr-Requisitos-Ingestão-26-03-24.md

# Converter todos os relatórios (100% preservação)
/convert-md-to-template_docx --all

# Sem argumentos: listar e escolher
/convert-md-to-template_docx
```

**Nota**: Todos os modos usam o fluxo de 2 etapas com docxcompose para garantir 100% de preservação.

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
- **Hyperlinks**: Preservados (externos e internos)
- **Links internos**: Funcionais (âncoras entre seções)
- **TOC (Sumário)**: Título convertido para "Sumário"
- **Emojis**: Removidos automaticamente (exceto ✅ ❌ em tabelas)

## Diferença vs /convert-md-to-docx

| Característica | convert-md-to-docx | convert-md-to-template_docx |
|----------------|--------------------|-----------------------------|
| Template | Não usa | ✅ Template oficial INSPIRE |
| Cabeçalho/Rodapé | Genérico | ✅ CPQD + Relatório Técnico (100% preservado) |
| Capa | Não tem | ✅ Capa oficial com logo |
| Diagramas Mermaid | ✅ Renderiza PNG | ✅ Renderiza PNG |
| Syntax highlighting | ✅ Sim (pygments) | ✅ Sim (pygments) |
| Tabelas | ✅ Bordas horizontais | ✅ Bordas horizontais |
| TOC (Sumário) | Automático (3 níveis) | Do template |
| Método | Conversão direta | Conversão + Merge (docxcompose) |
| Preservação | ~95% | **100%** (todas imagens, estilos, fontes) |

**Conclusão**: `/convert-md-to-template_docx` usa fluxo de 2 etapas com docxcompose para garantir **100% de preservação** de todos os elementos do template oficial INSPIRE.

## Como Funciona (Fluxo de 2 Etapas com 100% Preservação)

### Passo 1: Conversão MD → DOCX Limpo (sem template)

Usa `convert_md_to_docx.py`:

1. **Processa diagramas Mermaid**:
   - Extrai blocos ` ```mermaid ` do MD
   - Renderiza cada diagrama para PNG usando mermaid-cli (mmdc)
   - Substitui blocos por `![Diagrama](./imgs/diagram.png)` no MD
   - Cache: reutiliza PNG se diagrama não mudar (hash MD5)

2. **Converte MD → DOCX via Pandoc**:
   - Usa pypandoc com `--highlight-style=pygments`
   - Syntax highlighting automático por linguagem
   - Gera DOCX limpo com todo conteúdo formatado (sem template)

3. **Aplica customizações**:
   - Remove bookmarks automáticos do Pandoc
   - **Preserva hyperlinks** (externos e internos)
   - Configura margens, estilos, tabelas, código

### Passo 2: Merge com Template usando docxcompose

Usa `merge_docx_with_docxcompose.py`:

1. **Carrega documentos**:
   - Template INSPIRE (capa, cabeçalho, rodapé, logos)
   - DOCX limpo gerado no Passo 1

2. **Merge com docxcompose**:
   - Biblioteca especializada preserva **100%** de todos os elementos
   - Template fica no início, conteúdo do MD logo após
   - Todas as imagens preservadas (5 do template + 10 diagramas)
   - Todos os estilos, fontes, relationships preservados

3. **Salva resultado final**:
   - DOCX com template + conteúdo + **todas** as imagens/estilos
   - Arquivo final: `{nome}-FINAL.docx`

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
- ✅ Precisa de **100% de preservação** de todos os elementos (imagens, estilos, fontes)
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

---

## 🎯 O que é Preservado (100%)

Este skill usa a biblioteca especializada `docxcompose` no Passo 2 que preserva **ABSOLUTAMENTE TUDO**:

- ✅ **Todos os estilos e fontes** de ambos os documentos
- ✅ **Todas as imagens** (5 logos do template + 10 diagramas Mermaid = 15 imagens)
- ✅ **Relationships** (links internos entre XML e arquivos de imagem)
- ✅ **Formatação de tabelas** com bordas, cores e estilos
- ✅ **Configurações de página** (margens, tamanhos, orientação)
- ✅ **Numeração de listas** e hierarquia
- ✅ **Header e footer** com todos os elementos e imagens
- ✅ **Arquivos de mídia** (renomeia automaticamente para evitar conflitos)
- ✅ **Diagramas e gráficos** embarcados
- ✅ **Campos dinâmicos** (data, numeração de páginas, etc.)

### Exemplo de Resultado

```
Template (5 imagens) + Conteúdo (10 diagramas) = FINAL (15 imagens)
  
  Arquivos no DOCX final:
  - image1.png a image5.png   → logos INSPIRE/CPQD do template
  - image6.png a image15.png  → diagramas Mermaid (renomeados automaticamente)
```

## Links

### Scripts

- [convert_to_docx_with_template.py](../../../scripts/convert_to_docx_with_template.py) - Conversão MD → DOCX com template
- [merge_docx_with_docxcompose.py](../../../scripts/merge_docx_with_docxcompose.py) - Merge de DOCX com preservação total (100%)
- [convert_md_to_docx.py](../../../scripts/convert_md_to_docx.py) - Conversão MD → DOCX sem template

### Templates

- [Template Relatório Técnico INSPIRE](../../../docs/relatorios/templates/Template%20Relatório-Técnico-DestaquesGovbr%20Tema%207.docx)

### Documentação

- [python-docx Documentation](https://python-docx.readthedocs.io/)
- [docxcompose Documentation](https://github.com/4teamwork/docxcompose)
- [Pandoc Documentation](https://pandoc.org/MANUAL.html)
- [Mermaid Documentation](https://mermaid.js.org/)