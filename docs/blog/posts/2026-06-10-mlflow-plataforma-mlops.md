---
date: 2026-06-10
authors:
  - nitai
categories:
  - MLOps
  - Data Science
  - Infraestrutura
title: "MLflow no DGB: uma plataforma de experimentos atrás do IAP — e o JWT que a lib assina sozinha"
hide:
  - toc
---

# MLflow no DGB: uma plataforma de experimentos atrás do IAP — e o JWT que a lib assina sozinha

Até esta semana, cada experimento de ciência de dados do DGB vivia e morria na máquina de quem o rodou: métricas num notebook, o modelo num `.pkl` perdido numa pasta, e nenhum rastro compartilhado de "o que foi treinado, com quais dados, e quão bom ficou". A plataforma ganhou agora um **servidor MLflow compartilhado** — tracking de experimentos, Model Registry e ferramentas de GenAI — rodando em Cloud Run atrás do IAP, com uma biblioteca cliente que faz a autenticação sumir: `import dgb_mlflow; dgb_mlflow.configure()` e o resto é o `mlflow` de sempre. Este post conta o que foi construído, e o gotcha de autenticação que virou a peça central do desenho.

<!-- more -->

!!! tip "Os slides desta entrega"
    Há uma apresentação de 20 slides cobrindo arquitetura, uso e bastidores —
    embutida abaixo e também publicada em
    **<https://destaquesgovbr.github.io/docs/apresentacoes/mlflow-no-dgb/>**.

<div style="position:relative;width:100%;aspect-ratio:16/9;margin:1.5rem 0;
            border-radius:8px;overflow:hidden;border:1px solid var(--md-default-fg-color--lightest);">
  <iframe src="https://destaquesgovbr.github.io/docs/apresentacoes/mlflow-no-dgb/deck.html"
          title="Slides: MLflow no DGB" loading="lazy" allow="fullscreen"
          style="position:absolute;inset:0;width:100%;height:100%;border:0;"></iframe>
</div>

<p><a href="https://destaquesgovbr.github.io/docs/apresentacoes/mlflow-no-dgb/" target="_blank" rel="noopener">⛶ Abrir os slides em tela cheia →</a></p>

---

## O problema: experimentos sem rastro

O time de DS trabalha em duas frentes — as **VMs de desenvolvimento** (uma por pessoa, na infra GCP) e os **computadores pessoais**. Sem um lugar comum, o estado real de um modelo era folclore: ninguém conseguia comparar duas execuções, recarregar a versão que tinha ido melhor, ou auditar com que dados um classificador foi treinado. Para a pesquisa de NLP do DGB (classificação temática, embeddings, GenAI sobre as notícias), isso é dívida que cresce a cada experimento.

A meta foi dar à plataforma **um backend único** para experimentos, métricas, artefatos e modelos versionados — self-service, com governança de acesso e custo controlado, e que começasse com **uma linha de instalação**.

## A arquitetura: dois caminhos

O ponto central do desenho é que o cliente fala com **dois destinos diferentes**, e isso é de propósito:

```
  código Python + dgb-mlflow
        │
        │ (1) METADADOS                          (2) ARTEFATOS
        │ Authorization: Bearer JWT              leitura/escrita DIRETA
        │ aud = <URL>/*                          (ADC, sem proxy do servidor)
        ▼                                              │
   ┌─────────┐    run.invoker   ┌──────────────┐       │
   │   IAP   │ ───────────────► │  Cloud Run    │       │
   └─────────┘                  │  MLflow 3.13  │       │
                                └──────┬───────┘       │
                                       │ metadados      ▼
                              ┌────────▼────────┐  ┌──────────────────────────┐
                              │ Cloud SQL Postgres│  │ GCS                       │
                              │ DB mlflow (privado)│  │ inspire-7-finep-          │
                              └─────────────────┘  │ mlflow-artifacts          │
                                                    └──────────────────────────┘
```

- **Metadados** (experimentos, runs, registry, métricas) passam pelo IAP até o servidor MLflow no Cloud Run, que persiste no **Cloud SQL Postgres**.
- **Artefatos** (os modelos, que podem ser grandes) **não** passam pelo servidor: o cliente lê e grava **direto no GCS** via ADC. O servidor nunca vira gargalo de upload de modelo.

O servidor não tem autenticação nativa do MLflow — **o IAP é a porta**. Quem está na lista de acesso entra; o resto recebe `403` antes mesmo de chegar ao container.

## O gotcha que virou peça central: o JWT auto-assinado

Aqui está a parte que custou a investigação e definiu a biblioteca cliente. IAP direto no Cloud Run é GA (sem load balancer, sem custo extra) — mas o cliente OAuth que o IAP gera é **gerenciado pelo Google**, e ele **recusa ID tokens OIDC programáticos**: toda tentativa de autenticar via `id_token` devolvia `401 Invalid JWT audience`.

A saída não foi um client OAuth próprio, e sim um **JWT auto-assinado**: a service account assina o próprio token (via `iam.signJwt`), com a audience igual à **URL do servidor seguida de `/*`** — não um "IAP client id". Esse token, injetado no header `Authorization` a cada request via o mecanismo de `request_header_provider` do MLflow, passa pelo IAP (resposta `200` confirmada).

O ponto é que **o cientista de dados não vê nada disso**. A biblioteca **`dgb-mlflow`** esconde a complexidade inteira:

```python
import dgb_mlflow, mlflow

dgb_mlflow.configure()                 # resolve URL + assina o JWT do IAP; nada mais
mlflow.set_experiment("meu-experimento")
with mlflow.start_run():
    mlflow.log_param("lr", 0.01)
    mlflow.log_metric("acc", 0.97)
    mlflow.log_artifact("modelo.pkl")  # vai direto ao GCS
```

Instala-se em uma linha, fixada na release:

```bash
pip install "git+https://github.com/destaquesgovbr/ml-platform.git@v0.1.0#subdirectory=client"
```

Na dev VM, a credencial vem automática da service account da VM; no PC, basta um `gcloud auth application-default login`. O código é idêntico nos dois — muda só de onde sai a credencial.

## As pegadinhas de borda (que viraram features)

Construir atrás do IAP rendeu uma sequência de bordas que só apareceram com tráfego real:

- **Conta `@gmail` é barrada no login de browser do IAP.** Vários da equipe usam conta externa à org, e o IAP bloqueia o login interativo delas na UI. A plataforma ganhou um **proxy local** (`scripts/iap_ui_proxy.py`) que injeta o JWT assinado e serve a UI em `http://localhost:5000` — acesso ao painel sem depender do login do navegador.
- **MLflow 3.x bloqueia o header `Host`.** A versão 3.x recusa hosts `*.run.app` com `Invalid Host header` (proteção contra DNS rebinding). Como o IAP já é a fronteira de segurança, a correção foi liberar o host explicitamente (`MLFLOW_SERVER_ALLOWED_HOSTS`) ([infra#195](https://github.com/destaquesgovbr/infra/pull/195)).
- **Postgres público virou privado.** O backend de metadados foi migrado para **IP privado via Direct VPC egress** ([infra#193](https://github.com/destaquesgovbr/infra/pull/193)), num piloto que abriu o caminho para tirar o IP público do resto da instância — rastreado em [infra#194](https://github.com/destaquesgovbr/infra/issues/194).
- **Scale-to-zero.** O Cloud Run roda com `min-instances=0`: sem tráfego, custa zero; o primeiro request paga um cold start. IAP é grátis.

## O que acompanha o servidor

A entrega não foi só o servidor; foi uma plataforma utilizável de ponta a ponta:

- **Biblioteca `dgb-mlflow`** — pacote Python instalável via git, construída com **TDD** (32 testes, mocks de `google.auth`, sem rede real), publicada na release **v0.1.0**.
- **Projetos de exemplo que rodam de verdade** (testados E2E contra o servidor): um **tradicional** (classificação de notícias gov.br com sklearn — tracking + Model Registry, com um caminho BERT opcional) e um de **GenAI** (tracing com `@mlflow.trace`, avaliação com `mlflow.models.evaluate` e prompt registry, provider plugável).
- **Documentação** — 6 tutoriais PT-BR (getting-started PC e VM, como funciona o IAP, Model Registry, GenAI, troubleshooting) no repo, mais o [tutorial no site de docs](https://destaquesgovbr.github.io/docs/modulos/mlflow/).
- **CI/CD** — 57 testes automatizados como gate, build/deploy da imagem por Workload Identity Federation, e build do pacote com release versionada. Tudo verde.
- **Infra como código** — todo o servidor (Cloud Run + IAP + DB + bucket + IAM) foi entregue por PRs no Terraform ([infra#190](https://github.com/destaquesgovbr/infra/pull/190), [#191](https://github.com/destaquesgovbr/infra/pull/191), [#192](https://github.com/destaquesgovbr/infra/pull/192), [#193](https://github.com/destaquesgovbr/infra/pull/193), [#195](https://github.com/destaquesgovbr/infra/pull/195)).

Um detalhe de governança que vale o registro: o acesso começou como uma **lista de e-mails** no Terraform, mas passou a aceitar também um **Google Group** ([infra#196](https://github.com/destaquesgovbr/infra/pull/196)). Onboarding de um novo membro deixou de exigir um PR de infra — basta entrar no grupo.

## Antes e depois

| | Antes | Depois |
|---|---|---|
| Onde vivem os experimentos | máquina de cada um, sem rastro | backend compartilhado (Cloud SQL) |
| Modelos | `.pkl` solto numa pasta | Model Registry versionado |
| Comparar runs | impossível entre pessoas | UI única de tracking |
| Autenticação | — | IAP + JWT auto-assinado (transparente) |
| Artefatos grandes | — | direto no GCS, sem proxy |
| Começar a usar | — | uma linha de `pip install` |
| Custo ocioso | — | zero (`min-instances=0`) |

## Números

| Métrica | Valor |
|--------|-------|
| Servidor | MLflow **3.13.0** · Cloud Run · `southamerica-east1` |
| Pacote cliente | `dgb-mlflow` **v0.1.0** · Python 3.11+ |
| Testes (gate CI) | **57** automatizados · 32 no cliente (TDD) |
| Projetos de exemplo | 2 — tradicional (sklearn/BERT) e GenAI |
| Tutoriais | 6 PT-BR no repo + 1 no site de docs |
| PRs de infra | #190 · #191 · #192 · #193 · #195 · #196 |
| Backend de metadados | Cloud SQL Postgres (IP privado) |
| Artefatos | `gs://inspire-7-finep-mlflow-artifacts` |

## Lições

1. **IAP no Cloud Run recusa OIDC programático — assine o seu próprio JWT.** O cliente OAuth gerenciado pelo Google não aceita `id_token`; um JWT auto-assinado (`iam.signJwt`) com `aud = <URL>/*` passa. Foi o que destravou o acesso de máquina, e a descoberta valeu por toda a investigação.
2. **A complexidade de auth pertence à biblioteca, não ao usuário.** Encapsular o JWT, o ADC e a montagem da URL atrás de `configure()` é o que faz a plataforma ser adotada: o cientista de dados escreve `mlflow` puro e nunca toca no IAP.
3. **Separe metadados de artefatos.** Deixar o cliente gravar modelos direto no GCS (sem proxy do servidor) tira o servidor do caminho crítico de upload — essencial quando os modelos são grandes.
4. **A borda só aparece com a conta real.** O bloqueio de `@gmail` no login e o `Host` recusado pelo MLflow 3.x não estavam em nenhum tutorial; apareceram ao exercitar o caminho de verdade, e cada um virou uma feature (proxy, allowed-hosts).
5. **Privatize por etapas.** Migrar só o Postgres do MLflow para IP privado foi um piloto de baixo risco que validou o Direct VPC egress antes de propor o mesmo para a instância inteira.

A plataforma de experimentos agora existe e é uma linha de install. O próximo passo do arco é levar mais da pesquisa de NLP do DGB ([Epic docs#37](https://github.com/destaquesgovbr/docs/issues/37)) para cima dela — e tirar o IP público do Postgres de vez ([infra#194](https://github.com/destaquesgovbr/infra/issues/194)). O código, os exemplos e os tutoriais estão em **[destaquesgovbr/ml-platform](https://github.com/destaquesgovbr/ml-platform)**.
