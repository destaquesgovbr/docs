---
date: 2026-02-26
authors:
  - nitai
categories:
  - Arquitetura
  - Airflow
  - Refatoração
title: "6 dias, 36 PRs, 3 repos novos: desmembrando o monolito data-platform"
hide:
  - toc
---

# 6 dias, 36 PRs, 3 repos novos: desmembrando o monolito data-platform

Em 6 dias, refatoramos a plataforma de dados do DGB de um monolito para uma arquitetura de repos por domínio, ao mesmo tempo em que concluímos o servidor ActivityPub e ganhamos capacidade de federação. Foram **36 PRs mergeados** em **9 repos** e **3 repos novos** criados. De quebra, fechamos 4 issues que já estavam mapeadas no backlog e avançamos parcialmente outras 5.

<!-- more -->

## As duas linhas de trabalho

Essas evoluções aconteceram em dois trilhos paralelos que convergem na mesma visão: cada componente da plataforma vive no seu repo, deploya suas próprias DAGs no Airflow, e é independente para evoluir.

### Trilho 1: Scraper para Airflow (e além)

### Trilho 2: Servidor ActivityPub + Federação

---

## Trilho 1 -- Do monolito ao ecossistema de repos

### Dia 1 (23/fev, domingo): Scraper no Airflow

Tudo começou com a issue [`data-platform#57`](https://github.com/destaquesgovbr/data-platform/issues/57) -- "Migrar Scraper para Airflow com DAG por Órgão". O scraping de ~158 agências gov.br rodava via GitHub Actions, sequencial, 1x/dia. O plano ([`_plan/MIGRAR-SCRAPER-AIRFLOW.md`](https://github.com/destaquesgovbr/data-platform/blob/main/_plan/MIGRAR-SCRAPER-AIRFLOW.md)) desenhava DAGs dinâmicas, uma por agência, com schedule de 15 minutos.

**PRs**:
- [`data-platform#76`](https://github.com/destaquesgovbr/data-platform/pull/76) -- feat(dags): migrar scraper para Airflow com DAG por órgão
- [`data-platform#77`](https://github.com/destaquesgovbr/data-platform/pull/77) -- fix: corrigir formato requirements.txt e deploy source via plugins/
- [`data-platform#78`](https://github.com/destaquesgovbr/data-platform/pull/78) -- fix: corrigir ordem dos args do gsutil rsync
- [`data-platform#79`](https://github.com/destaquesgovbr/data-platform/pull/79) -- fix: adicionar loguru e scipy ao requirements.txt

A sequência de fixes conta a história real: deploy no Composer e um, dois, três ajustes até funcionar. Composer é implacável -- cada `requirements.txt` leva 10-20 min para instalar. Cada fix, mais 10-20 min de espera.

### Ainda Dia 1: A revelação -- Cloud Run API

Enquanto esperava o Composer, veio a percepção: instalar o scraper inteiro como dependência do Composer é frágil. O plano [`_plan/SCRAPER-CLOUD-RUN-API.md`](https://github.com/destaquesgovbr/data-platform/blob/main/_plan/SCRAPER-CLOUD-RUN-API.md) redesenhou a arquitetura:

```
Airflow DAG (leve)              Cloud Run (scraper-api)
+------------------+   HTTP POST   +----------------------+
| scrape_mec       |-------------->| POST /scrape/agencies |
| (httpx + IAM)    |   Bearer IAM  | ScrapeManager.run()   |
+------------------+               | -> PostgreSQL          |
                                   +----------------------+
```

DAGs viram simples chamadas HTTP. Workers do Airflow ficam leves. Scraper roda em container isolado com scale-to-zero.

**PRs**:
- [`data-platform#80`](https://github.com/destaquesgovbr/data-platform/pull/80) -- feat: scraper API no Cloud Run + DAGs leves via HTTP
- [`infra#78`](https://github.com/destaquesgovbr/infra/pull/78) -- feat: add Terraform para Scraper API Cloud Run

### Dia 2 (24/fev, segunda): Nasce o repo `scraper`

Com a API funcionando, o próximo passo natural era extrair tudo para um repo próprio. O plano [`_plan/EXTRAIR-SCRAPER-REPO.md`](https://github.com/destaquesgovbr/data-platform/blob/main/_plan/EXTRAIR-SCRAPER-REPO.md) mapeou a cirurgia completa.

**Novo repo**: [`destaquesgovbr/scraper`](https://github.com/destaquesgovbr/scraper) -- criado em 24/fev

Para fazer o deploy de DAGs de múltiplos repos no mesmo Composer, cada repo precisa usar um subdiretório próprio no bucket GCS. Isso exigiu mudanças coordenadas:

**PRs de infraestrutura do deploy**:
- [`infra#82`](https://github.com/destaquesgovbr/infra/pull/82) -- Add WI binding para repo scraper
- [`data-platform#81`](https://github.com/destaquesgovbr/data-platform/pull/81) -- Deploy DAGs para subdiretório `data-platform/`
- [`data-platform#82`](https://github.com/destaquesgovbr/data-platform/pull/82) -- Remove scraper code (extracted to standalone repo)
- [`scraper#1`](https://github.com/destaquesgovbr/scraper/pull/1) -- docs: CLAUDE.md completo do scraper
- [`infra#80`](https://github.com/destaquesgovbr/infra/pull/80) -- feat: increase concurrency scraper-api
- [`infra#83`](https://github.com/destaquesgovbr/infra/pull/83) -- Remove unused pandas do Composer
- [`data-platform#83`](https://github.com/destaquesgovbr/data-platform/pull/83) -- Remove unused requirements.txt step

### Dia 3 (25/fev, terça): Reusable workflows + data-publishing

O padrão "cada repo deploya suas DAGs" precisava de DRY. Em vez de copiar o workflow de deploy em cada repo, criamos um **reusable workflow** centralizado.

**PR fundacional**:
- [`reusable-workflows#3`](https://github.com/destaquesgovbr/reusable-workflows/pull/3) -- feat: add reusable workflow for Composer DAG deployment

Todos os repos migram para chamar esse workflow com 2-3 parâmetros. E então rolamos a adoção:

- [`data-platform#85`](https://github.com/destaquesgovbr/data-platform/pull/85) -- refactor: use reusable workflow
- [`scraper#2`](https://github.com/destaquesgovbr/scraper/pull/2) + [`scraper#3`](https://github.com/destaquesgovbr/scraper/pull/3) -- refactor: use reusable workflow + fix permissions

Último desmembramento do dia: o plano [`_plan/PLAN-data-publishing-migration.md`](https://github.com/destaquesgovbr/data-platform/blob/main/_plan/PLAN-data-publishing-migration.md) extraiu a DAG de sync PostgreSQL -> HuggingFace para um repo próprio. Isso resolveu de forma elegante a issue [`data-platform#28`](https://github.com/destaquesgovbr/data-platform/issues/28) -- "Executar sync HuggingFace em ambiente isolado (evitar PyPI no Composer)" -- que pedia KubernetesPodOperator, mas ganhou uma solução melhor: repo dedicado com plugins no Composer.

**Novo repo**: [`destaquesgovbr/data-publishing`](https://github.com/destaquesgovbr/data-publishing) -- criado em 25/fev

**PRs de finalização**:
- [`infra#85`](https://github.com/destaquesgovbr/infra/pull/85) -- Authorize data-publishing repo in WIF
- [`data-platform#86`](https://github.com/destaquesgovbr/data-platform/pull/86) -- chore: remove test_postgres_connection DAG
- [`data-platform#87`](https://github.com/destaquesgovbr/data-platform/pull/87) -- Remove HuggingFace sync DAG (migrated to data-publishing)
- [`docs#31`](https://github.com/destaquesgovbr/docs/pull/31) -- docs: update site após extração do scraper

### Ainda Dia 3: Codificando o padrão -- skill `/criar-dag`

Com 3 repos já seguindo o mesmo padrão de DAGs (scraper, data-publishing, activitypub-server), ficou claro que tínhamos uma convenção madura. Em vez de deixar esse conhecimento implícito, codificamos tudo numa **skill do Claude Code**:

- [`data-platform#88`](https://github.com/destaquesgovbr/data-platform/pull/88) -- feat: add /criar-dag skill for Airflow DAG creation

A skill `/criar-dag` é um guia de ~470 linhas que inclui: referência completa da arquitetura Airflow do projeto (connections, schema PostgreSQL, pipeline de dados), templates para módulos plugin + DAG + workflow de deploy + testes, e passo-a-passo de setup na infra (WIF, connections, Secret Manager). Agora, quando precisarmos de uma nova DAG em qualquer repo, basta invocar `/criar-dag` no Claude Code e o padrão se replica sozinho.

Isso fecha um ciclo interessante: começamos a semana criando DAGs manualmente, terminamos codificando o padrão para que DAGs futuras nasçam prontas.

---

## Trilho 2 -- ActivityPub: de servidor a pipeline federado

### Contexto

O repo [`activitypub-server`](https://github.com/destaquesgovbr/activitypub-server) (criado em 13/fev) implementa o protocolo ActivityPub para que as notícias do DGB possam ser seguidas via Mastodon e qualquer servidor do Fediverso. O servidor já existia, mas faltava a integração com o pipeline de dados.

### Dia 2 (24-25/fev): Federation DAG + Deploy

A pergunta era: como o servidor ActivityPub sabe que existem notícias novas para publicar? A resposta: uma DAG no Airflow que consulta o PostgreSQL, enfileira artigos novos com payload completo, e dispara a publicação.

**PRs (em sequência rápida)**:
- [`infra#79`](https://github.com/destaquesgovbr/infra/pull/79) -- fix: remove reserved PORT env var dos Cloud Run services
- [`infra#81`](https://github.com/destaquesgovbr/infra/pull/81) -- Fix federation DATABASE_URL parsing and connectivity
- [`infra#84`](https://github.com/destaquesgovbr/infra/pull/84) -- Add Airflow secrets for federation database
- [`activitypub-server#1`](https://github.com/destaquesgovbr/activitypub-server/pull/1) -- **Phase 6: news_payload in queue + federation DAG**

A Phase 6 é o PR central: adiciona coluna `news_payload JSONB` na fila de publicação, a DAG `federation_publish` que roda a cada 10 min, e conecta tudo.

### Dia 3 (25/fev): Ajustes de produção

Com a DAG rodando, vieram os ajustes finos de quem monitora produção:
- [`activitypub-server#2`](https://github.com/destaquesgovbr/activitypub-server/pull/2) -- fix(dag): batch loop + configurable watermark
- [`activitypub-server#3`](https://github.com/destaquesgovbr/activitypub-server/pull/3) -- fix(dag): max_active_runs=1
- [`activitypub-server#5`](https://github.com/destaquesgovbr/activitypub-server/pull/5) -- perf(dag): batch INSERT + reduce log verbosity
- [`activitypub-server#6`](https://github.com/destaquesgovbr/activitypub-server/pull/6) -- refactor: use reusable workflow for DAG deployment
- [`activitypub-server#7`](https://github.com/destaquesgovbr/activitypub-server/pull/7) -- feat: local Airflow dev environment com Astro CLI
- [`activitypub-server#8`](https://github.com/destaquesgovbr/activitypub-server/pull/8) -- Remove publish queue limit

A sequência batch loop -> max_active_runs -> batch INSERT mostra o ciclo clássico: deploy, observar, otimizar.

Note que o `activitypub-server#7` (Astro CLI) avança a issue [`data-platform#42`](https://github.com/destaquesgovbr/data-platform/issues/42) -- "Criar Ambiente Airflow Local com Astro CLI". O padrão está pronto para ser replicado nos demais repos.

---

## Trilho paralelo: Organização do projeto

Em paralelo, o repo [`project`](https://github.com/destaquesgovbr/project) ganhou sua primeira PR:
- [`project#1`](https://github.com/destaquesgovbr/project/pull/1) -- Add /enviar-telegram skill

O repo `project` centraliza skills do Claude Code para gestão do backlog: daily standup, sprint status, refinement, mover issues, enviar relatórios para Telegram. É a "sala de controle" do projeto.

Também no portal:
- [`portal#80`](https://github.com/destaquesgovbr/portal/pull/80) -- docs: documentação de API e arquitetura dos feeds RSS/Atom/JSON

---

## O antes e depois

### Antes (20/fev)

```
data-platform/     (monolito)
  scrapers/        -- scraping gov.br
  api.py           -- FastAPI do scraper
  dags/            -- TODAS as DAGs
    scrape_*.py
    sync_hf.py
  managers/        -- storage, dataset
  cogfy/           -- enriquecimento
  typesense/       -- busca
```

### Depois (26/fev)

```
scraper/               -- Scraping gov.br (API + DAGs)
data-publishing/       -- Sync PG -> HuggingFace (DAG + plugins)
activitypub-server/    -- Federação ActivityPub (server + DAG)
data-platform/         -- Enriquecimento, Typesense, Cogfy (core pipeline)
reusable-workflows/    -- CI/CD compartilhado (novo workflow DAG deploy)
infra/                 -- Terraform, IAM, WIF (3 novos bindings)
```

Cada repo:
- Tem seu próprio CLAUDE.md
- Deploya suas próprias DAGs num subdiretório do Composer
- Usa o reusable workflow para deploy
- Tem autonomia de release

---

## Issues resolvidas pelo caminho

Uma surpresa positiva: ao revisar o backlog, descobrimos que várias issues já mapeadas foram resolvidas (total ou parcialmente) como efeito colateral das refatorações.

### Fechadas (implementação completa)

| Issue | Título | Como foi resolvida |
|-------|--------|-------------------|
| [`data-platform#57`](https://github.com/destaquesgovbr/data-platform/issues/57) | Migrar Scraper para Airflow com DAG por Órgão | Implementação direta -- PRs #76-#82 + extração para repo `scraper` |
| [`data-platform#28`](https://github.com/destaquesgovbr/data-platform/issues/28) | Executar sync HF em ambiente isolado | Resolvida por caminho diferente: extração para `data-publishing` com plugins |
| [`data-platform#22`](https://github.com/destaquesgovbr/data-platform/issues/22) | Criar DAG para exportar dataset HuggingFace | Já existia, refatorada e migrada para `data-publishing` |
| [`docs#30`](https://github.com/destaquesgovbr/docs/issues/30) | Criar Repositório data-science | Repo criado em 13/fev com 14 issues de pesquisa |

### Avançadas (progresso parcial)

| Issue | Título | Progresso | O que falta |
|-------|--------|-----------|-------------|
| [`data-platform#42`](https://github.com/destaquesgovbr/data-platform/issues/42) | Astro CLI para dev local | ~70% | Replicar padrão do activitypub-server nos outros repos |
| [`data-platform#45`](https://github.com/destaquesgovbr/data-platform/issues/45) | Remover código morto HF | ~50% | Revisar StorageAdapter e limpar dual-write residual |
| [`data-platform#73`](https://github.com/destaquesgovbr/data-platform/issues/73) | Monitoramento de falhas do scraper | ~30% | Alertas automáticos (Airflow já dá visibilidade por DAG) |
| [`docs#15`](https://github.com/destaquesgovbr/docs/issues/15) | Documentar DAG sync HF | ~40% | Atualizar docs site com nova arquitetura |
| [`data-platform#64`](https://github.com/destaquesgovbr/data-platform/issues/64) | Campo `active` para agências | Habilitada | Airflow permite pausar DAGs, campo YAML seria bônus |

---

## Números

| Métrica | Valor |
|---------|-------|
| PRs mergeados | 36 |
| Repos tocados | 9 (data-platform, infra, scraper, activitypub-server, data-publishing, reusable-workflows, portal, docs, project) |
| Repos novos | 3 (scraper, data-publishing, data-science) |
| Issues fechadas | 4 |
| Issues avançadas | 5 |
| Planos escritos | 4 (migrar-airflow, cloud-run-api, extrair-scraper, data-publishing) |
| Skills criadas | 2 (/enviar-telegram, /criar-dag) |
| Dias | 6 |

---

## Lições

1. **Planejar antes de codar** -- Cada refatoração teve um `_plan/*.md` com arquitetura alvo, sequência de migração, e critérios de verificação. Isso evitou retrabalho e deu visibilidade.

2. **Migrar sem downtime** -- A sequência sempre foi: criar novo -> validar -> pausar antigo -> remover. Nunca quebramos o pipeline em produção.

3. **Reusable workflows são multiplicadores** -- Um workflow parametrizado no `reusable-workflows` economiza meia hora de config em cada repo novo.

4. **Composer é lento, Cloud Run é ágil** -- Mover execução pesada para Cloud Run e manter DAGs leves (só HTTP) foi a decisão de arquitetura mais impactante da semana.

5. **O ciclo deploy-observar-otimizar é inevitável** -- Os PRs #2 a #8 do activitypub-server mostram que nenhum plano sobrevive ao primeiro contato com produção. E tá tudo bem.

6. **Codificar padrões, não só usar** -- Quando um padrão se repete 3 vezes, vale transformar em skill ou template. A `/criar-dag` nasceu assim: depois de criar DAGs em 3 repos, codificamos o padrão para que o próximo dev (ou o Claude Code) replique automaticamente.

7. **Refatorar revela issues resolvidas** -- Das 4 issues que fechamos, nenhuma foi atacada diretamente. Todas foram resolvidas como efeito colateral de decisões arquiteturais. Isso reforça que boa arquitetura resolve problemas que você nem estava olhando.
