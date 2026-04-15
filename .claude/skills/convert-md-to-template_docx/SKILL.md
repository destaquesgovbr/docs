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

3. **Se receber `--merge` ou `--100%`**: Execute o fluxo de 2 etapas para 100% de preservação:
   - Use AskUserQuestion para perguntar qual arquivo converter (se não especificado)
   - **Passo 1**: Execute `python scripts/convert_md_to_docx.py docs/relatorios/{arquivo.md}` (conversão limpa, sem template)
   - **Passo 2**: Execute `python scripts/merge_docx_with_docxcompose.py "docs/relatorios/templates/Template Relatório-Técnico-DestaquesGovbr Tema 7.docx" "docs/relatorios/output/{arquivo}.docx" "docs/relatorios/output/{arquivo}-FINAL.docx"` (merge com 100% preservação)
   - Informe ao usuário que o arquivo final está em `{arquivo}-FINAL.docx`

4. **Se NÃO receber argumentos**:
   - Use Glob para listar arquivos .md em `docs/relatorios/*.md`
   - Mostre a lista formatada ao usuário com índices numerados
   - Use AskUserQuestion para perguntar qual arquivo converter (incluir opção "Todos")
   - Execute o script com o arquivo escolhido ou com --all

## Comportamento

- **Com arquivo**: `/convert-md-to-template_docx {arquivo.md}` → converte o arquivo especificado (~95% preservação)
- **Com --all**: `/convert-md-to-template_docx --all` → converte todos os .md em docs/relatorios/ (~95% preservação)
- **Com --merge ou --100%**: `/convert-md-to-template_docx --merge {arquivo.md}` → conversão em 2 etapas (100% preservação)
- **Sem argumentos**: `/convert-md-to-template_docx` → lista arquivos disponíveis e pergunta ao usuário qual converter

## Uso

```bash
# Converter arquivo específico (~95% preservação)
/convert-md-to-template_docx Relatório-Técnico-DestaquesGovbr-Requisitos-Ingestão-26-03-24.md

# Converter com 100% de preservação (fluxo 2 etapas com docxcompose)
/convert-md-to-template_docx --merge Relatório-Técnico-DestaquesGovbr-Requisitos-Ingestão-26-03-24.md
/convert-md-to-template_docx --100% Relatório-Técnico-DestaquesGovbr-Requisitos-Ingestão-26-03-24.md

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

---

## 🔀 Merge de Documentos DOCX com Preservação Total

Se você já tem arquivos DOCX prontos (com ou sem template) e quer fazer merge preservando **ABSOLUTAMENTE TUDO** (estilos, fontes, imagens do header/footer, tabelas, configurações), use o script `merge_docx_with_docxcompose.py`.

### Quando Usar Merge

- ✅ Você tem dois DOCX prontos e quer combiná-los
- ✅ Precisa preservar 100% dos estilos, imagens e formatação de ambos
- ✅ Quer adicionar template a um DOCX já existente
- ✅ Precisa mesclar relatórios mantendo logos do header/footer

### Como Usar

```bash
# Sintaxe
python scripts/merge_docx_with_docxcompose.py <template.docx> <content.docx> <output.docx>

# Exemplo: Merge de template + relatório
python scripts/merge_docx_with_docxcompose.py \
  "docs/relatorios/templates/Template Relatório-Técnico-DestaquesGovbr Tema 7.docx" \
  "docs/relatorios/output/Relatório-Existente.docx" \
  "docs/relatorios/output/Resultado-Merge.docx"
```

### Dependência Adicional

```bash
# Instalar docxcompose (biblioteca especializada em merge de DOCX)
pip install docxcompose

# ou com Poetry
poetry add docxcompose
```

### O que o Merge Preserva (100%)

A biblioteca `docxcompose` foi **especificamente criada para merge de DOCX** e preserva automaticamente:

- ✅ **Todos os estilos e fontes** de ambos os documentos
- ✅ **Todas as imagens** (incluindo logos do header/footer do template)
- ✅ **Relationships** (links internos entre XML e arquivos de imagem)
- ✅ **Formatação de tabelas** com bordas, cores e estilos
- ✅ **Configurações de página** (margens, tamanhos, orientação)
- ✅ **Numeração de listas** e hierarquia
- ✅ **Header e footer** com todos os elementos e imagens
- ✅ **Arquivos de mídia** (renomeia automaticamente para evitar conflitos)
- ✅ **Diagramas e gráficos** embarcados
- ✅ **Campos dinâmicos** (data, numeração de páginas, etc.)

### Exemplo de Resultado

Ao fazer merge, **TODAS as imagens são preservadas**:

```
Template (5 imagens) + Conteúdo (10 diagramas) = Merge (15 imagens)
  
  Arquivos no DOCX final:
  - image1.png a image5.png   → logos INSPIRE/CPQD do template
  - image6.png a image15.png  → diagramas Mermaid (renomeados automaticamente)
```

### Diferença: Conversão vs Merge

| Aspecto | convert_to_docx_with_template.py | merge_docx_with_docxcompose.py |
|---------|----------------------------------|--------------------------------|
| **Entrada** | Arquivo .md (Markdown) | Dois arquivos .docx prontos |
| **Processo** | MD → DOCX → Merge interno | Merge direto de DOCX |
| **Preservação** | ~95% (pode perder algumas imagens do header) | **100%** (preserva tudo) |
| **Imagens do header** | Parcial (estrutura, mas não todas as imagens) | ✅ Completo (todas as imagens) |
| **Uso recomendado** | Conversão inicial de MD para DOCX | Merge de arquivos DOCX já existentes |
| **Velocidade** | Mais lento (processa MD, Mermaid, Pandoc) | Mais rápido (merge direto) |

### Quando Usar Cada Um

**Use `convert_to_docx_with_template.py`** quando:
- 📝 Está convertendo de **Markdown** para DOCX
- ⚡ Quer fazer tudo em um único passo (conversão + merge)
- 🖼️ Pode aceitar 95% de preservação (suficiente para maioria dos casos)

**Use `merge_docx_with_docxcompose.py`** quando:
- 📄 Já tem **dois DOCX prontos** para mesclar
- 🎯 Precisa de **100% de preservação** (crítico para documentos oficiais)
- 🖼️ **Imagens do header/footer** são essenciais (logos, marcas)
- 🔧 Quer máximo controle sobre o processo de merge

### Fluxo de Trabalho Recomendado

Para **máxima qualidade** (100% de preservação):

```bash
# Passo 1: Converter MD → DOCX sem template
python scripts/convert_md_to_docx.py relatorio.md

# Passo 2: Merge com template usando docxcompose
python scripts/merge_docx_with_docxcompose.py \
  "templates/Template.docx" \
  "output/relatorio.docx" \
  "output/relatorio-final.docx"
```

### Troubleshooting do Merge

#### Erro: "docxcompose não está instalado"

```bash
pip install docxcompose
# Verificar instalação
python -c "import docxcompose; print(docxcompose.__version__)"
```

#### Imagens duplicadas ou conflitos

O `docxcompose` renomeia automaticamente arquivos de mídia para evitar conflitos. Exemplo:
- Template tem `image1.png`
- Conteúdo tem `image1.png` (diferente)
- Resultado: `image1.png` (do template) + `image2.png` (renomeado do conteúdo)

#### Documento muito grande após merge

Isso é **normal** e **esperado** - o documento contém TODAS as imagens de ambos os arquivos. Exemplo:
- Template: 200 KB (5 imagens)
- Conteúdo: 400 KB (10 diagramas)
- Merge: 600 KB+ (15 imagens + estilos duplicados)

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