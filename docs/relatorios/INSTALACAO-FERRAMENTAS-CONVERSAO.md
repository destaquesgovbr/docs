# Instalação de Ferramentas para Conversão MD → DOCX/ODT

Este guia explica como instalar as dependências necessárias para converter relatórios Markdown para DOCX ou ODT com diagramas Mermaid renderizados.

## Visão Geral

A conversão requer:
- **Python packages**: pypandoc, python-docx (✅ já instalados)
- **Pandoc**: conversor universal de documentos
- **Mermaid CLI**: renderizador de diagramas Mermaid

---

## 1. Instalar Pandoc

### Opção A: Chocolatey (Recomendado para Windows)

Se você tem Chocolatey instalado:

```bash
choco install pandoc
```

### Opção B: Instalador Manual

1. Acesse https://github.com/jgm/pandoc/releases/latest
2. Baixe o arquivo `pandoc-X.XX-windows-x86_64.msi`
3. Execute o instalador
4. Reinicie o terminal

### Verificar Instalação

```bash
pandoc --version
```

Saída esperada:
```
pandoc 3.x.x
...
```

---

## 2. Instalar Node.js (pré-requisito para Mermaid CLI)

### Verificar se já está instalado

```bash
node --version
npm --version
```

Se os comandos funcionarem, pule para a **Seção 3**.

### Instalar Node.js

#### Opção A: Instalador Oficial

1. Acesse https://nodejs.org/
2. Baixe a versão **LTS** (Long Term Support)
3. Execute o instalador
4. Reinicie o terminal

#### Opção B: Chocolatey

```bash
choco install nodejs-lts
```

### Verificar Instalação

```bash
node --version  # Deve mostrar v20.x.x ou superior
npm --version   # Deve mostrar 10.x.x ou superior
```

---

## 3. Instalar Mermaid CLI

Com Node.js instalado, execute:

```bash
npm install -g @mermaid-js/mermaid-cli
```

### Verificar Instalação

```bash
mmdc --version
```

Saída esperada:
```
11.x.x
```

### Troubleshooting

Se `mmdc` não for encontrado após a instalação:

1. **Verifique o PATH do npm global**:
   ```bash
   npm config get prefix
   ```

2. **Adicione ao PATH** (substitua `<prefix>` pela saída do comando anterior):
   ```
   C:\Users\<seu-usuario>\AppData\Roaming\npm
   ```

3. **Reinicie o terminal** e teste novamente:
   ```bash
   mmdc --version
   ```

---

## 4. Testar Conversão

Após instalar tudo, teste a conversão:

```bash
# Converter arquivo específico
python scripts/convert_md_to_docx.py "docs/relatorios/Relatório-Técnico-DestaquesGovbr-Requisitos-Ingestão-26-03-24.md"

# Ou converter todos
python scripts/convert_md_to_docx.py --all
```

### Outputs Esperados

Se tudo funcionar, você verá:

```
[1/3] Extraindo diagramas Mermaid...
   -> Encontrados 5 diagramas
   -> Renderizando diagram_001.png... OK
   -> Renderizando diagram_002.png... OK
   ...

[2/3] Convertendo MD -> DOCX com Pandoc...
   -> OK

[3/3] Customizando estilos DOCX...
   -> Fontes: Arial 11pt / Courier New 10pt
   -> Tabelas: apenas bordas horizontais
   -> TOC: 3 níveis

[OK] DOCX gerado: docs/relatorios/output/Relatório-Técnico-DestaquesGovbr-Requisitos-Ingestão-26-03-24.docx
```

---

## Resumo dos Comandos

```bash
# 1. Instalar Pandoc
choco install pandoc

# 2. Instalar Node.js (se necessário)
choco install nodejs-lts

# 3. Instalar Mermaid CLI
npm install -g @mermaid-js/mermaid-cli

# 4. Verificar tudo
pandoc --version
node --version
npm --version
mmdc --version

# 5. Converter relatório
python scripts/convert_md_to_docx.py "docs/relatorios/Relatório-Técnico-DestaquesGovbr-Requisitos-Ingestão-26-03-24.md"
```

---

## Links Úteis

- [Pandoc Documentation](https://pandoc.org/MANUAL.html)
- [Mermaid Documentation](https://mermaid.js.org/)
- [Node.js Downloads](https://nodejs.org/)
- [Chocolatey Package Manager](https://chocolatey.org/)

---

## Problemas Comuns

### "pandoc: command not found"
- Reinstale o Pandoc e reinicie o terminal
- Verifique se está no PATH: `where pandoc`

### "mmdc: command not found"
- Verifique se Node.js está instalado: `node --version`
- Verifique PATH do npm: `npm config get prefix`
- Adicione ao PATH do sistema e reinicie o terminal

### Erro ao renderizar diagrama Mermaid
- Verifique sintaxe no [Mermaid Live Editor](https://mermaid.live)
- Diagramas complexos podem ter timeout (30s)
- O script cria placeholder e continua se falhar

### "pypandoc não está instalado"
- Execute: `pip install pypandoc python-docx`
- Ou use Poetry: `poetry add pypandoc python-docx`