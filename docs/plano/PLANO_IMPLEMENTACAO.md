# Guia: Usando LLMs para Gerar Documentação Técnica

> **Contexto**: Este documento descreve como utilizamos o Claude Code para gerar toda a documentação técnica do projeto DestaquesGovbr. Serve como referência de boas práticas de engenharia de prompt para tarefas de documentação.

---

## Por que este guia?

A documentação técnica deste repositório foi **inteiramente gerada por LLM** (Claude Code) a partir dos repositórios existentes do projeto. Este é um caso real de uso de IA generativa para acelerar a criação de documentação técnica de qualidade.

O objetivo deste guia é compartilhar:

- O mindset utilizado para estruturar os prompts
- A abordagem bottom-up de reutilização de código existente
- Os prompts reais utilizados
- As boas práticas aprendidas

---

## A Abordagem Bottom-Up

### O que é?

Em vez de criar documentação "do zero", utilizamos uma abordagem **bottom-up**:

```
Repositórios Existentes → Análise por LLM → Documentação Gerada
```

O LLM analisa o código, workflows, configurações e README existentes para **sintetizar** uma camada de documentação sobre eles.

### Por que funciona?

1. **Código é verdade**: A documentação é derivada diretamente do código real
2. **Consistência**: O LLM mantém padrão ao analisar múltiplos repositórios
3. **Velocidade**: Documentação completa em horas, não semanas
4. **Atualização facilitada**: Basta re-executar com código atualizado

### Pré-requisitos

- Repositórios clonados localmente (para acesso direto pelo Claude Code)
- Estrutura mínima de código organizado
- Documentação fragmentada existente (READMEs, comentários)

---

## O Mindset de Engenharia de Prompt

### 1. Defina o Objetivo com Clareza

Antes de escrever o prompt, responda:

- **Para quem** é a documentação? (público-alvo)
- **Qual problema** ela resolve? (onboarding, referência, troubleshooting)
- **Que formato** é esperado? (markdown, diagramas, guias passo-a-passo)

### 2. Forneça Contexto dos Repositórios

O Claude Code precisa saber **onde olhar**. Liste:

- Caminhos locais dos repositórios
- Função de cada repositório
- Arquivos-chave a serem analisados
- Integrações entre os módulos

### 3. Seja Específico sobre Entregas

Em vez de "documente o projeto", especifique:

- Quais módulos documentar
- Que tipo de diagramas criar
- Estrutura de pastas esperada
- Nível de detalhe técnico

### 4. Itere com Perguntas de Clarificação

O LLM pode (e deve) fazer perguntas. Isso resulta em:

- Documentação mais precisa
- Menos retrabalho
- Decisões registradas

---

## Caso Real: Documentação do DestaquesGovbr

### Prompt Inicial (Plan Mode)

O primeiro prompt foi executado no modo de planejamento do Claude Code:

```markdown
# Roteiro para criação de documentação do DestaquesGovbr com foco de
# apresentação mais arquitetural/técnica dos módulos existentes

- mostrar os módulos e integrações lógicas entre as partes
- explicar os workflows (github actions) do scraper (que integra com cogfy
  e huggingface), do deploy do portal no gcp, da atualização dos dados no
  typesense produção
- explicar a arquitetura da infraestrutura em produção no gcp baseada em
  terraform e subindo cloud run e demais componentes
- Identifique outras características técnicas relevantes do sistema

- Usar diagramas para explicar cada uma destas partes
- inclua links para os repositórios do github
- inclua links para a documentação técnica existente (se houver)

Crie um plano de criação da documentação em fases evolutivas e incrementais
para possibilitar uma documentação melhor estruturada durante a execução
das fases da escrita

O objetivo principal, neste momento, é facilitar o onboard de novos
desenvolvedores e colaboradores técnicos no projeto DestaquesGovbr.
Quero acelerar o processo de ownership e capacidade de começarem a
contribuir logo. Proponha na documentação uma sessão de onboarding
com um roteiro.

Para saber mais conceitualmente sobre o projeto DestaqueGovbr olhe este
documento @/Users/nitai/Dropbox/dev-mgi/destaquesgov-projeto/planos-de-trabalho/Plano_Trabalho_DestaquesGov_v3.odt

Demais repositórios que devem ser cobertos pela documentação:

- /Users/nitai/Dropbox/dev-mgi/govbrnews-scraper
  → Este é o repositório mais backend. Ele contém o Scraper
- /Users/nitai/Dropbox/dev-mgi/destaquesgovbr-portal
  → Este é o portal, a aplicação principal. Aqui existe um workflow de
    atualização do portal no gcp para todo push na branch main
- /Users/nitai/Dropbox/dev-mgi/destaquesgovbr-typesense
  → Aqui está o typensense rodando em docker para desenvolvimento local
- /Users/nitai/Dropbox/dev-mgi/destaquesgovbr-infra
  → Aqui está a infraestrutura como código em terraform para subir no gcp
- /Users/nitai/Dropbox/dev-mgi/destaquesgovbr-agencies
  → Este repositório não contém código, ainda. Ele contém 2 arquivos de
    dados estruturantes dos órgãos. Um arquivo possui os dados de cada
    órgão incluindo a URL das notícias utilizada no scraper, e o outro
    possui a hierarquia dos órgãos, utilizado no portal para navegação
    e filtros. Atualmente esses arquivos são copiados manualmente para
    o repositório do scraper e do portal.
- /Users/nitai/Dropbox/dev-mgi/spaces-govbrnews
  → Aqui está o app de visualização dos dados no huggingface spaces.
    Esta é uma aplicação simples em streamlit que consome o dataset
    hospedado no huggingface datasets.

- O scraper (foi também o primeiro módulo da plataforma). Ele possui um
  workflow que faz a raspagem, a inferência e atualiza o dataset no
  huggingface. Por sinal o dataset no huggingface é a base de dados de
  referência. Podemos dizer que é o nosso BD e com backup. Mais sobre
  esse dataset: https://huggingface.co/datasets/nitaibezerra/govbrnews

- A parte da inferência é feita através de uma plataforma SaS chamada
  Cogfy que utiliza LLM. Nós enviamos os dados para o cogfy e pegamos
  de volta com as colunas de inferência preenchidas. As configurações
  implementadas no cogfy não estão em código e por isso não conseguimos
  dar mais detalhes nesta documentação. Mas é uma meta em breve incluir
  alguns screenshots e detalhes das configurações para as inferências.

- As inferências feitas no cogfy agrega a cada notícia um resumo e a
  classificação temática de acordo com os 3 níveis da árvore temática.

- Uma outra parte estruturante do projeto é a árvore temática. Pretendo
  criar um repositório exclusivo para a gestão da árvore temática. Mas
  por enquanto a árvore temática está hardcoded no scraper e no portal.
  A árvore temática é um componente chave do sistema, pois é a base para
  a classificação das notícias e para os filtros de navegação no portal.
  A árvore temática está aqui:
  - @/Users/nitai/Dropbox/dev-mgi/govbrnews-scraper/src/enrichment/themes_tree.yaml
  - @/Users/nitai/Dropbox/dev-mgi/destaquesgovbr-portal/src/lib/themes.yaml

Pretendo criar um novo repositório para armazenar esta documentação geral
do DestaquesGovBr.

Analise tudo e proponha um plano
```

### Pontos-Chave do Prompt Inicial

| Elemento | Exemplo | Por quê funciona |
|----------|---------|------------------|
| **Objetivo claro** | "facilitar o onboard de novos desenvolvedores" | Define o propósito da documentação |
| **Público-alvo** | "desenvolvedores e colaboradores técnicos" | Define o nível de detalhe |
| **Repositórios listados** | Caminhos locais com descrição | Permite análise direta do código |
| **Contexto adicional** | Link para documento conceitual | Fornece visão de negócio |
| **Entregas específicas** | "diagramas", "workflows", "fases evolutivas" | Define formato esperado |
| **Meta futura** | "repositório exclusivo para árvore temática" | Contextualiza decisões atuais |

### Perguntas de Clarificação do LLM

Antes de começar a gerar, o Claude Code fez perguntas importantes:

```markdown
Perguntas de clarificação:

1. **URLs dos repositórios**: Os repositórios estão em uma organização
   GitHub (ex: github.com/destaquesgovbr/...) ou são repositórios pessoais?
   Preciso das URLs corretas para incluir os links na documentação.

2. **Nome do repositório de documentação**: Você mencionou criar um novo
   repositório para a documentação. Qual será o nome? Sugestão: destaquesgovbr-docs

3. **Público primário**: Para o roteiro de onboarding, qual o perfil mais
   comum dos novos colaboradores?
   - Desenvolvedores Python (backend/data)
   - Desenvolvedores TypeScript/React (frontend)
   - Ambos / Full-stack

4. **Screenshots do Cogfy**: Você mencionou que é uma meta incluir screenshots
   das configurações do Cogfy. Deseja que eu inclua uma seção placeholder para
   isso na documentação, ou prefere adicionar depois quando tiver os screenshots?

5. **Idioma da documentação**: A documentação deve ser em português (alinhado
   com o projeto ser do governo brasileiro) ou inglês (para potencial
   internacionalização)?

6. **Integração com docs existentes**: Notei que destaquesgovbr-infra já tem
   documentação em docs/. Prefere:
   - Migrar essa documentação para o novo repositório centralizado
   - Manter a documentação de infra lá e apenas referenciar
   - Duplicar/expandir no repositório central
```

### Respostas às Clarificações

```markdown
1. Todos os repositórios estão na organização
   https://github.com/orgs/destaquesgovbr/repositories

2. Apenas "docs". Futuramente pretendo inclusive renomear os repositórios
   removendo os prefixos "destaquesgovbr"

3. Estão entrando duas pessoas python backend e uma frontend.
   Então pode fazer sentido ter as 2

4. Sim, crie um placeholder

5. Em português

6. Mantemos as documentações atuais e fazemos referências. Podemos duplicar
   alguns conteúdos e dar mais detalhes através dos links. Esta documentação
   central pretende explicar as partes, suas integrações e funcionamento,
   e apoiar onboard
```

### Resultado: Plano em 5 Fases

O Claude Code gerou um plano estruturado:

| Fase | Descrição | Prioridade |
|------|-----------|------------|
| 1 | Arquitetura e Visão Geral | Alta |
| 2 | Módulos | Alta |
| 3 | Workflows | Alta |
| 4 | Infraestrutura | Média |
| 5 | Onboarding | Alta |

### Execução Iterativa

Após aprovação do plano, a execução foi feita em etapas:

1. **Fases 1 e 5 primeiro** (fundação + onboarding)
2. **Confirmação** para seguir com demais fases
3. **Publicação no GitHub** via `gh` CLI

---

## Template: Prompt para Documentação Técnica

Use este template como ponto de partida:

```markdown
# Objetivo
[Descreva o objetivo principal da documentação]

# Público-alvo
[Quem vai ler? Qual o nível técnico?]

# Repositórios a documentar
- /caminho/local/repo1 → [Descrição e função]
- /caminho/local/repo2 → [Descrição e função]

# Arquivos-chave para análise
- @/caminho/para/arquivo-importante.yaml
- @/caminho/para/workflow.yml

# Entregas esperadas
- [ ] Diagramas de arquitetura
- [ ] Explicação de workflows
- [ ] Guias de setup
- [ ] Troubleshooting

# Formato e idioma
- Formato: Markdown com Mermaid para diagramas
- Idioma: [Português/Inglês]
- Estrutura de pastas: [Descreva ou deixe o LLM propor]

# Contexto adicional
[Links para documentos conceituais, planos de trabalho, etc.]

# Restrições
[O que NÃO deve ser documentado, informações sensíveis, etc.]
```

---

## Boas Práticas Aprendidas

### DO (Faça)

- **Liste caminhos locais** dos repositórios para análise direta
- **Forneça contexto de negócio** além do código
- **Especifique o público-alvo** e seu nível técnico
- **Use o modo Plan** para tarefas complexas
- **Permita perguntas** de clarificação antes da execução
- **Itere em fases** para documentação incremental
- **Referencie documentação existente** em vez de duplicar

### DON'T (Evite)

- Prompts vagos como "documente o projeto"
- Esperar que o LLM adivinhe a estrutura organizacional
- Ignorar as perguntas de clarificação do LLM
- Tentar gerar tudo em um único prompt
- Esquecer de mencionar integrações entre módulos
- Omitir decisões futuras que afetam a documentação atual

---

## Métricas do Caso Real

| Métrica | Valor |
|---------|-------|
| Repositórios analisados | 6 |
| Documentos gerados | 22 |
| Diagramas criados | 15+ |
| Tempo total | ~4 horas |
| Iterações de prompt | 3 |

---

## Conclusão

A engenharia de prompt para documentação técnica não é sobre "pedir para o LLM escrever docs". É sobre:

1. **Estruturar o conhecimento** que você já tem sobre o projeto
2. **Fornecer acesso** ao código-fonte real
3. **Definir claramente** o que você precisa
4. **Iterar** com o LLM até chegar no resultado

O resultado é documentação **derivada da verdade** (o código), não de suposições.

---

## Recursos

- [Claude Code Documentation](https://docs.anthropic.com/claude/docs/claude-code)
- [Mermaid Diagram Syntax](https://mermaid.js.org/syntax/)
- [Documentação do DestaquesGovbr](../) (resultado deste processo)

---

> **Nota**: Este documento foi gerado como parte do processo de documentação do DestaquesGovbr e serve como meta-documentação do próprio processo.
