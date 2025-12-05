# Plano de Criação da Documentação Técnica - DestaquesGovbr

> **Status**: ✅ Concluído
> **Última atualização**: 2025-12-04
> **Responsável**: Equipe DestaquesGovbr

---

## Contexto do Projeto

O **DestaquesGovbr** é uma plataforma integrada de notícias e informações do Governo Federal Brasileiro que:
- Centraliza ~100+ portais governamentais em plataforma única
- Usa AI/LLM para classificação temática e sumarização
- Disponibiliza dados abertos no HuggingFace (~295k+ notícias)
- Portal web moderno com busca semântica

### Repositórios Cobertos

**Organização GitHub**: https://github.com/destaquesgovbr

| Repositório | URL | Visibilidade | Tecnologia |
|-------------|-----|--------------|------------|
| `govbrnews-scraper` | https://github.com/destaquesgovbr/govbrnews-scraper | Public | Python/Poetry |
| `destaquesgovbr-portal` | https://github.com/destaquesgovbr/destaquesgovbr-portal | Public | Next.js 15/TypeScript |
| `destaquesgovbr-infra` | https://github.com/destaquesgovbr/destaquesgovbr-infra | Private | Terraform/GCP |
| `destaquesgovbr-typesense` | https://github.com/destaquesgovbr/destaquesgovbr-typesense | Public | Docker/Python |
| `destaquesgovbr-agencies` | https://github.com/destaquesgovbr/destaquesgovbr-agencies | Public | YAML |

**Nota**: O repositório `spaces-govbrnews` está em conta pessoal no HuggingFace.

---

## Objetivo da Documentação

**Objetivo principal**: Facilitar o onboarding de novos desenvolvedores e colaboradores técnicos, acelerando o processo de ownership e contribuição.

**Público-alvo**:
- Desenvolvedores Python/Backend (2 pessoas entrando)
- Desenvolvedores TypeScript/Frontend (1 pessoa entrando)
- Colaboradores técnicos externos
- Gestores que precisam entender a arquitetura

**Idioma**: Português

---

## Andamento das Fases

### Legenda
- ⬜ Não iniciado
- 🔄 Em andamento
- ✅ Concluído

| Fase | Descrição | Status | Progresso |
|------|-----------|--------|-----------|
| 1 | Arquitetura e Visão Geral | ✅ | 3/3 |
| 2 | Módulos | ✅ | 7/7 |
| 3 | Workflows | ✅ | 4/4 |
| 4 | Infraestrutura | ✅ | 3/3 |
| 5 | Onboarding | ✅ | 5/5 |

---

## Fases de Criação da Documentação

### FASE 1: Visão Geral e Arquitetura (Prioridade Alta)

| Entregável | Arquivo | Status |
|------------|---------|--------|
| Visão geral com diagrama de arquitetura | `arquitetura/visao-geral.md` | ✅ |
| Fluxo de dados do pipeline | `arquitetura/fluxo-de-dados.md` | ✅ |
| Componentes estruturantes | `arquitetura/componentes-estruturantes.md` | ✅ |

---

### FASE 2: Documentação dos Módulos (Prioridade Alta)

| Entregável | Arquivo | Status |
|------------|---------|--------|
| Scraper | `modulos/scraper.md` | ✅ |
| Portal | `modulos/portal.md` | ✅ |
| Agencies | `modulos/agencies.md` | ✅ |
| Árvore Temática | `modulos/arvore-tematica.md` | ✅ |
| Typesense Local | `modulos/typesense-local.md` | ✅ |
| Integração Cogfy | `modulos/cogfy-integracao.md` | ✅ |
| Streamlit App | `modulos/spaces-streamlit.md` | ✅ |

---

### FASE 3: Workflows e CI/CD (Prioridade Alta)

| Entregável | Arquivo | Status |
|------------|---------|--------|
| Pipeline do Scraper | `workflows/scraper-pipeline.md` | ✅ |
| Deploy do Portal | `workflows/portal-deploy.md` | ✅ |
| Dados do Typesense | `workflows/typesense-data.md` | ✅ |
| Builds Docker | `workflows/docker-builds.md` | ✅ |

---

### FASE 4: Infraestrutura GCP (Prioridade Média)

| Entregável | Arquivo | Status |
|------------|---------|--------|
| Arquitetura GCP | `infraestrutura/arquitetura-gcp.md` | ✅ |
| Guia Terraform | `infraestrutura/terraform-guide.md` | ✅ |
| Secrets e IAM | `infraestrutura/secrets-iam.md` | ✅ |

---

### FASE 5: Onboarding e Guias Práticos (Prioridade Alta)

| Entregável | Arquivo | Status |
|------------|---------|--------|
| Roteiro de Onboarding | `onboarding/roteiro-onboarding.md` | ✅ |
| Setup Backend (Python) | `onboarding/setup-backend.md` | ✅ |
| Setup Frontend (TypeScript) | `onboarding/setup-frontend.md` | ✅ |
| Primeiro PR | `onboarding/primeiro-pr.md` | ✅ |
| Troubleshooting | `onboarding/troubleshooting.md` | ✅ |

---

## Cronograma

| Fase | Descrição | Prioridade | Estimativa |
|------|-----------|------------|------------|
| 1 | Arquitetura e Visão Geral | Alta | 2-3 dias |
| 2 | Módulos | Alta | 4-5 dias |
| 3 | Workflows | Alta | 2-3 dias |
| 4 | Infraestrutura | Média | 2-3 dias |
| 5 | Onboarding | Alta | 2-3 dias |

**Total estimado**: 12-17 dias de trabalho focado

---

## Links e Recursos

### Documentação Existente (referenciada)
| Local | Conteúdo |
|-------|----------|
| `destaquesgovbr-infra/docs/` | Arquitetura, setup Terraform, Typesense |
| `destaquesgovbr-infra/README.md` | Quick start da infra |
| `destaquesgovbr-portal/CLAUDE.md` | Instruções para desenvolvimento |
| `govbrnews-scraper/README.md` | Documentação do scraper |

### Recursos Externos
- **Dataset HuggingFace**: https://huggingface.co/datasets/nitaibezerra/govbrnews
- **Dataset Reduzido**: https://huggingface.co/datasets/nitaibezerra/govbrnews-reduced

---

## Arquivos-Chave para Referência

### Scraper (`govbrnews-scraper`)
| Arquivo | Função |
|---------|--------|
| `src/main.py` | CLI principal |
| `src/dataset_manager.py` | Gerenciador HuggingFace |
| `src/cogfy_manager.py` | Integração Cogfy |
| `src/scraper/webscraper.py` | Scraper principal |
| `src/enrichment/themes_tree.yaml` | Árvore temática |
| `.github/workflows/main-workflow.yaml` | Pipeline diário |

### Portal (`destaquesgovbr-portal`)
| Arquivo | Função |
|---------|--------|
| `src/app/page.tsx` | Homepage |
| `src/lib/typesense-client.ts` | Cliente Typesense |
| `src/lib/themes.yaml` | Árvore temática |
| `src/lib/agencies.yaml` | Catálogo de órgãos |
| `src/lib/prioritization.yaml` | Config de priorização |
| `.github/workflows/deploy-production.yml` | Deploy GCP |

### Infra (`destaquesgovbr-infra`)
| Arquivo | Função |
|---------|--------|
| `terraform/main.tf` | Networking |
| `terraform/typesense.tf` | Compute Engine |
| `terraform/portal.tf` | Cloud Run |
| `terraform/workload-identity.tf` | GitHub OIDC |
| `.github/workflows/typesense-daily-load.yml` | Carga diária |

---

## Decisões de Design

- **Repositório**: `docs` (https://github.com/destaquesgovbr/docs)
- **Idioma**: Português
- **Público**: Devs Python (2) + Devs TypeScript (1)
- **Cogfy**: Placeholder para screenshots futuros
- **Docs existentes**: Manter e referenciar, não duplicar
- **Diagramas**: Mermaid para versionamento no Git
