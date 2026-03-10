# DestaquesGovbr - Documentação Técnica

> Documentação central da plataforma DestaquesGovbr para onboarding de desenvolvedores e colaboradores técnicos.

## O que é o DestaquesGovbr?

O **DestaquesGovbr** é uma plataforma integrada de notícias e informações do Governo Federal Brasileiro que:

- **Centraliza** ~160+ portais governamentais em uma plataforma única
- **Classifica** automaticamente notícias usando AI/LLM em 25 temas e 3 níveis hierárquicos
- **Armazena** dados em PostgreSQL (fonte de verdade) e distribui via HuggingFace (~300k+ notícias)
- **Oferece** portal web moderno com busca semântica

## Quick Start

### Para Desenvolvedores Backend (Python)
→ Veja [onboarding/setup-backend.md](onboarding/setup-backend.md)

### Para Desenvolvedores Frontend (TypeScript)
→ Veja [onboarding/setup-frontend.md](onboarding/setup-frontend.md)

### Roteiro Completo de Onboarding
→ Veja [onboarding/roteiro-onboarding.md](onboarding/roteiro-onboarding.md)

---

## Dev VM: Seu Ambiente no GCP

Cada desenvolvedor pode ter uma **VM dedicada no GCP** para desenvolvimento de código:

```mermaid
flowchart LR
    Dev[Seu Computador] -->|SSH via IAP| VM[Dev VM]
    VSCode[VSCode Remote] -->|SSH| VM
    VM -->|Git| GH[GitHub]
```

**Benefícios:**

- 💻 **Ambiente padronizado** - mesma configuração para toda equipe
- 💾 **Disco persistente** de 50GB em `/mnt/data` para seus projetos
- 🛡️ **Seguro** - sem IP público, acesso apenas via IAP
- 💰 **Econômico** - auto-shutdown às 19h

**Para criar sua Dev VM:**

1. Clone o repo [infra](https://github.com/destaquesgovbr/infra)
2. Adicione sua configuração em `terraform/terraform.tfvars`
3. Abra um PR e aguarde o merge

→ Guia completo: [infraestrutura/devvm.md](infraestrutura/devvm.md)

## Arquitetura

```mermaid
flowchart LR
    A[160+ Sites gov.br] -->|Raspagem| B[Scraper]
    B -->|Armazenamento| C[(PostgreSQL)]
    C -->|Enriquecimento| D[Cogfy/LLM]
    D --> C
    C -->|Embeddings| E[Embeddings API]
    E --> C
    C -->|Indexação| F[(Typesense)]
    F -->|Busca| G[Portal Next.js]
    C -->|Sync diário| H[(HuggingFace)]
```

→ Veja detalhes em [arquitetura/visao-geral.md](arquitetura/visao-geral.md)

## Repositórios

| Repositório | Descrição | Tecnologia |
|-------------|-----------|------------|
| [data-platform](https://github.com/destaquesgovbr/data-platform) | Pipeline de dados (scraper, sync, enrichment) | Python/Poetry |
| [portal](https://github.com/destaquesgovbr/portal) | Portal web principal | Next.js 15 |
| [infra](https://github.com/destaquesgovbr/infra) | Infraestrutura como código | Terraform/GCP |
| [agencies](https://github.com/destaquesgovbr/agencies) | Dados dos órgãos | YAML |
| [themes](https://github.com/destaquesgovbr/themes) | Taxonomia temática | YAML |

## Estrutura da Documentação

```
docs/
├── arquitetura/           # Visão geral, fluxo de dados, componentes
├── modulos/               # Detalhes de cada módulo/repositório
├── workflows/             # GitHub Actions, CI/CD, pipelines
├── infraestrutura/        # GCP, Terraform, secrets
├── onboarding/            # Guias para novos desenvolvedores
├── plano/                 # Plano de implementação da documentação
└── assets/diagrams/       # Diagramas em Mermaid
```

## Recursos Externos

- **Portal (Preview)**: [portal](https://portal-klvx64dufq-rj.a.run.app/) *(URL provisória)*
- **Dataset Principal**: [nitaibezerra/govbrnews](https://huggingface.co/datasets/nitaibezerra/govbrnews)
- **Dataset Reduzido**: [nitaibezerra/govbrnews-reduced](https://huggingface.co/datasets/nitaibezerra/govbrnews-reduced)
- **Organização GitHub**: [github.com/destaquesgovbr](https://github.com/destaquesgovbr)

## Como Esta Documentação Foi Criada

Esta documentação foi **inteiramente gerada por LLM** (Claude Code) usando uma abordagem bottom-up: o código dos repositórios existentes foi analisado para criar uma camada de documentação sobre eles.

### Guia de Engenharia de Prompt

Documentamos o processo completo de criação como um guia de boas práticas:

→ Veja [plano/PLANO_IMPLEMENTACAO.md](plano/PLANO_IMPLEMENTACAO.md)

O guia inclui:

- **Mindset** para estruturar prompts de documentação
- **Prompts reais** utilizados neste projeto
- **Template reutilizável** para outros projetos
- **Boas práticas** aprendidas no processo

## Como Contribuir

→ Veja [CONTRIBUTING.md](CONTRIBUTING.md)

---

**Mantido pela equipe DestaquesGovbr** | Ministério da Gestão e da Inovação em Serviços Públicos
