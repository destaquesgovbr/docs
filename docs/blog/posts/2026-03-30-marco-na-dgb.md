---
date: 2026-03-30
authors:
  - nitai
categories:
  - Segurança
  - Clipping
  - Portal
  - Infraestrutura
title: "Março na DGB — da busca semântica ao pentest, passando pelo clipping"
hide:
  - toc
---

# Março na DGB — da busca semântica ao pentest, passando pelo clipping

Em 24 dias, a plataforma DGB recebeu cerca de 100 PRs em 11 repositórios, tocando desde a experiência de busca do portal até a correção de vulnerabilidades identificadas em pentest. O mês trouxe três grandes movimentos: um sistema de clipping completo, o hardening de segurança pós-pentest, e a ativação da busca semântica.

<!-- more -->

## Clipping: de zero a broadcast em 10 dias

O clipping — curadoria automática de notícias com resumo gerado por LLM — passou de conceito a produto funcional entre 15 e 24 de março. A evolução aconteceu em três camadas: o worker backend, o portal frontend, e a infraestrutura de entrega.

### O worker

O serviço `clipping` nasceu com 7 features de uma vez ([clipping#2](https://github.com/destaquesgovbr/clipping/pull/2)): prompt editorial estruturado com output JSON, renderização HTML com layout gov.br, armazenamento de releases no Firestore, e 4 canais de entrega — email, Telegram, web push e webhook.

Logo nos primeiros dias, uma sequência de correções afinaram o serviço: o modelo LLM migrou para Claude Sonnet 4 via Bedrock com inference profile cross-region ([clipping#3](https://github.com/destaquesgovbr/clipping/pull/3), [clipping#4](https://github.com/destaquesgovbr/clipping/pull/4)), o email remetente foi atualizado para um sender verificado ([clipping#5](https://github.com/destaquesgovbr/clipping/pull/5)), e o timezone foi corrigido para BRT ([clipping#11](https://github.com/destaquesgovbr/clipping/pull/11)).

O cron scheduling veio logo depois ([clipping#17](https://github.com/destaquesgovbr/clipping/pull/17)) — cada clipping define sua própria expressão cron e o `since_hours` é calculado dinamicamente. A DAG do Airflow passou a rodar a cada 10 minutos, disparando apenas os clippings cujo horário bateu.

O webhook como canal de entrega foi adicionado em seguida ([clipping#16](https://github.com/destaquesgovbr/clipping/pull/16)), permitindo integração com qualquer sistema externo via POST com payload JSON estruturado.

### O marketplace no portal

No frontend, o Clipping Marketplace surgiu como feature completa num único PR de 4600+ linhas ([portal#125](https://github.com/destaquesgovbr/portal/pull/125)): publicação, listagem paginada, follow, clone e like — com 64 testes no backend. Logo depois, o namespace foi renomeado de "marketplace" para "clippings" e ganhou RSS feed e JSON download ([portal#134](https://github.com/destaquesgovbr/portal/pull/134)).

O sistema de follow foi reescrito de seguidor-cria-clone para broadcast ([portal#142](https://github.com/destaquesgovbr/portal/pull/142)): o autor despacha uma vez e o fan-out entrega a todos os seguidores. No backend, o worker passou a resolver a subcollection `marketplace/{id}/followers` e entregar via os canais configurados por cada seguidor ([clipping#18](https://github.com/destaquesgovbr/clipping/pull/18)).

Capas de imagem e melhorias de UX na prateleira de clippings fecharam o ciclo ([portal#144](https://github.com/destaquesgovbr/portal/pull/144)), apoiadas por uma nova infraestrutura de image-worker com Cloud Run, GCS e Pub/Sub ([infra#160](https://github.com/destaquesgovbr/infra/pull/160)).

### Convites virais e pré-lançamento

Em paralelo, o portal ganhou um sistema de convites virais para controlar o acesso na fase de pré-lançamento ([portal#112](https://github.com/destaquesgovbr/portal/pull/112)): login gated por código de convite, 5 convites por usuário, lista de espera pública, painel admin, e email de boas-vindas via SendGrid. A integração com Keycloak SSO e login inteligente por domínio vieram no mesmo pacote.

---

## Segurança: resposta ao pentest CPQD

O pentest realizado pelo CPQD em 17 de março identificou vulnerabilidades que foram corrigidas ao longo das duas semanas seguintes, envolvendo 4 repositórios e múltiplos contributors.

### V04 — Endpoints internos expostos

O endpoint `/process` da embeddings-api estava acessível publicamente sem autenticação (CVSS 5.3). A correção envolveu remoção da IAM binding `allUsers` e adição de autenticação via identity tokens ([infra#161](https://github.com/destaquesgovbr/infra/pull/161)). O push-notifications também precisou proteger seus endpoints internos `/process` e `/push/clipping` ([push-notifications#12](https://github.com/destaquesgovbr/push-notifications/pull/12), [infra#164](https://github.com/destaquesgovbr/infra/pull/164)).

### V05 — Documentação técnica exposta

A documentação Swagger/ReDoc estava pública em três serviços: embeddings-api, telegram-bot e clipping. A solução foi implementar um toggle `DOCS_ENABLED` controlado por variável de ambiente, desabilitado em produção:

- embeddings-api: app factory com configuração condicional ([embeddings#10](https://github.com/destaquesgovbr/embeddings/pull/10), [infra#162](https://github.com/destaquesgovbr/infra/pull/162))
- telegram-bot: mesma abordagem ([telegram-bot#3](https://github.com/destaquesgovbr/telegram-bot/pull/3), [infra#163](https://github.com/destaquesgovbr/infra/pull/163))

### V07 — Funcionalidades administrativas e security headers

No portal, foram adicionados 6 security headers HTTP — HSTS, X-Frame-Options, CSP com política dinâmica, entre outros ([portal#140](https://github.com/destaquesgovbr/portal/pull/140)). O controle de acesso admin ganhou uma nova camada: roles armazenados no Firestore como fonte adicional de autorização, com cascata Keycloak → Firestore → ADMIN_EMAILS ([portal#146](https://github.com/destaquesgovbr/portal/pull/146)).

---

## Busca semântica ativada

A busca do portal evoluiu de keyword-only (BM25 via Typesense) para hybrid search, combinando busca textual com embeddings vetoriais de 768 dimensões ([portal#110](https://github.com/destaquesgovbr/portal/pull/110)). O alpha de 0.3 dá 70% de peso ao BM25 e 30% ao vetor semântico.

A implementação usa `multiSearch` POST para enviar o vetor sem exceder limites de URL, com fallback gracioso: se a API de embeddings não está disponível, a busca continua funcionando em modo textual. Um toggle de "busca inteligente" na interface permite ao usuário alternar entre os modos ([portal#117](https://github.com/destaquesgovbr/portal/pull/117)).

Para suportar o backfill de 98 mil artigos, a Embeddings API foi temporariamente escalada com `cpu_idle=false` (always allocated) ([infra#145](https://github.com/destaquesgovbr/infra/pull/145), [infra#146](https://github.com/destaquesgovbr/infra/pull/146)). As variáveis de ambiente para conectar o portal à API de embeddings em produção foram ativadas via Terraform ([infra#152](https://github.com/destaquesgovbr/infra/pull/152)).

---

## Scraper: qualidade de dados e cobertura

O scraper passou por um ciclo de estabilização. Foram investigadas 12 agências com parser HTML desatualizado, resultando em fallbacks para novos padrões de sites gov.br ([scraper#22](https://github.com/destaquesgovbr/scraper/pull/22)) — incluindo formatos `article.entry` e `div.item` que antes não eram capturados.

Seis agências que usam Volto/SPA (CMS baseado em React) foram desabilitadas por incompatibilidade com scraping estático ([scraper#25](https://github.com/destaquesgovbr/scraper/pull/25)). Uma validação de sincronização foi implementada para evitar divergência entre as cópias de `site_urls.yaml` usadas pela API e pelas DAGs ([scraper#26](https://github.com/destaquesgovbr/scraper/pull/26)).

---

## Data platform: migrations e modernização

O data-platform ganhou um sistema genérico de database migrations ([data-platform#116](https://github.com/destaquesgovbr/data-platform/pull/116)) — runner Python único com auditoria, dry-run e rollback, substituindo a abordagem anterior de scripts ad-hoc. O sistema foi exercitado imediatamente na migração de `unique_id` para slug legível, que envolveu resolução automática de colisões e recriação da view `news_with_themes` ([data-platform#111](https://github.com/destaquesgovbr/data-platform/pull/111)).

---

## Infraestrutura: Terraform como fonte de verdade

Um tema recorrente do mês foi a migração de env vars do CI/CD para o Terraform. O portal, que antes dependia do CI para injetar variáveis via `--set-env-vars` (substituindo **todas** as env vars a cada deploy), passou a ter o Terraform como fonte de verdade ([infra#151](https://github.com/destaquesgovbr/infra/pull/151)). Isso eliminou uma classe inteira de bugs onde deploys esqueciam variáveis.

O módulo reutilizável de Streamlit ganhou suporte a `secret_env_vars` via Secret Manager ([reusable-terraform#5](https://github.com/destaquesgovbr/reusable-terraform/pull/5)), e a plataforma Streamlit agora tem workflow automatizado de desregistro de apps ([infra#142](https://github.com/destaquesgovbr/infra/pull/142)).

O dashboard infra-health — uma aplicação Streamlit para monitoramento de Cloud Run, Cloud SQL, Composer, Pub/Sub e Registry — recebeu 16 PRs de otimização, saindo de minutos para ~7 segundos no carregamento de DAGs via paralelização de requests.

---

## Números

| Métrica | Valor |
|---------|-------|
| PRs mergeados | ~100 |
| Repositórios tocados | 11 |
| Contributors | 4 |
| Dias | 24 |
| Vulnerabilidades corrigidas (pentest) | V04, V05, V07 |
| Canais de entrega do clipping | 4 (email, Telegram, push, webhook) |
| Artigos com embedding vetorial | 98.000 |
| Agências scraper investigadas | 20+ |

---

## O que vem pela frente

O pentest ainda tem itens abertos em andamento: proteção dos endpoints internos do push-notifications ([push-notifications#12](https://github.com/destaquesgovbr/push-notifications/pull/12), [infra#164](https://github.com/destaquesgovbr/infra/pull/164)) e o endpoint de verificação de integridade do scraper ([scraper#18](https://github.com/destaquesgovbr/scraper/pull/18)) aguardam review. O portal se prepara para o lançamento público com o sistema de convites controlando o acesso gradual.
