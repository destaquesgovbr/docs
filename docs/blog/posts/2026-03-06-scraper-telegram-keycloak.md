---
date: 2026-03-06
authors:
  - nitai
categories:
  - Scraper
  - Push Notifications
  - Infraestrutura
  - Autenticação
title: "Três frentes em paralelo: scraper, Telegram e Keycloak"
hide:
  - toc
---

# Três frentes em paralelo: scraper, Telegram e Keycloak

Entre 4 e 6 de março, o projeto avançou em paralelo em três direções distintas: o scraper ganhou uma otimização de performance que evita re-processar artigos já conhecidos, o serviço de push notifications cresceu de WebPush para um ecossistema Telegram completo, e a infraestrutura de autenticação ganhou um SSO centralizado com Keycloak.

<!-- more -->

## Contexto

O último post parou em 4 de março, com o portal v1 no ar e o bot Telegram fazendo scraping ao vivo. Mas naquele mesmo dia, antes de dormir, já tinha três frentes abertas em paralelo. Cada PR que mergeiava abria espaço para o próximo.

---

## Frente 1: Scraper — performance e qualidade de dados

### Dia 1 (04/03): Known URL fence

O scraper tinha um problema silencioso: a cada execução, ele refazia o fetch de artigos que já estavam no banco. Sem nenhum mecanismo de deduplicação no nível do loop de scraping, cada DAG processava tudo do zero.

A solução foi o [known URL fence (scraper#12)](https://github.com/destaquesgovbr/scraper/pull/12): antes de iniciar o scraping de uma agência, o sistema consulta o PostgreSQL e carrega as URLs recentes. Durante o loop, artigos com URL já conhecida são pulados sem fazer fetch da página. E se 3 artigos consecutivos forem conhecidos, o sistema encerra a busca antecipadamente — o "fence".

```
Listagem da agência
│
├── Artigo 1 → URL nova → scrape
├── Artigo 2 → URL nova → scrape
├── Artigo 3 → URL conhecida → skip
├── Artigo 4 → URL conhecida → skip
├── Artigo 5 → URL conhecida → skip ← 3 consecutivos → FENCE
└── (para aqui, não processa o resto)
```

Backward-compatible: sem `known_urls`, o comportamento é idêntico ao atual. O PR saiu com 11 testes unitários escritos em TDD (testes primeiro), adicionados à suite de 98 testes.

### Dia 1-2 (04-05/03): Qualidade dos dados

Com o scraper otimizado, vieram dois fixes de qualidade:

- [scraper#14](https://github.com/destaquesgovbr/scraper/pull/14): URLs de agências com falha persistente (403, 404) foram corrigidas ou desativadas, resolvendo issues de data quality que já estavam abertas.
- [scraper#17](https://github.com/destaquesgovbr/scraper/pull/17) (por [@mauriciomendonca](https://github.com/mauriciomendonca)): o algoritmo de limpeza de conteúdo estava removendo texto legítimo. A heurística foi ajustada para ser menos agressiva, preservando mais do conteúdo original dos artigos.

---

## Frente 2: Push Notifications → ecossistema Telegram

Esta foi a frente mais intensa. O serviço `push-notifications` saiu de WebPush simples para um sistema com DMs Telegram, canais por órgão e filtros expandidos.

### Dia 1 (04/03): Filtros expandidos e Telegram rico

Dois PRs grandes mergeiram em sequência:

**[push-notifications#1](https://github.com/destaquesgovbr/push-notifications/pull/1) — filtros v2:** as subscriptions passaram a suportar filtros por themes L2/L3, tags e keywords (além de agency e theme_l1 que já existiam). Adicionado cooldown de 15min entre notificações para o mesmo subscriber — sem isso, um burst de artigos de uma agência spammaria todos os inscritos. O campo `user_id` foi adicionado para vincular subscriptions a usuários autenticados no portal.

**[push-notifications#2](https://github.com/destaquesgovbr/push-notifications/pull/2) — Telegram com formato rico:** criado `telegram_sender.py` com envio de foto via `sendPhoto` e fallback para texto quando a imagem falha. Formato da notificação: agência, categoria, título, resumo, data e link. Usuários se inscrevem direto no bot Telegram, que gerencia assinaturas via webhook. Se o bot for bloqueado pelo usuário, a assinatura é removida automaticamente.

A infra para rodar o bot no Cloud Run chegou logo depois com [infra#116](https://github.com/destaquesgovbr/infra/pull/116) e um fix de token com [infra#117](https://github.com/destaquesgovbr/infra/pull/117).

### Dia 2 (06/03): Summary no WebPush e canais por órgão

Com o bot funcionando para DMs, a pergunta natural foi: e os canais de órgão? Em vez de cada pessoa se inscrever individualmente, canais Telegram dos próprios órgãos recebem automaticamente os artigos publicados.

**[push-notifications#4](https://github.com/destaquesgovbr/push-notifications/pull/4):** adicionado `summary` ao payload WebPush — o lead editorial do artigo agora aparece na notificação do navegador, não só o título.

**[push-notifications#5](https://github.com/destaquesgovbr/push-notifications/pull/5) — canais por órgão:** novo módulo `telegram_channel_sender.py`. Quando um artigo é publicado, além das DMs individuais, o sistema faz posting automático no canal Telegram do órgão (se registrado). Admins registram canais via comandos `/canal` e `/canais` no bot. Auto-desativação após 5 falhas consecutivas. Saiu com 29 novos testes, totalizando 114 na suite.

As env vars correspondentes chegaram com [infra#119](https://github.com/destaquesgovbr/infra/pull/119).

---

## Frente 3: Keycloak SSO

### Dia 2 (06/03): Do zero ao SSO em produção

O portal usava Google OAuth diretamente via NextAuth. A ideia era centralizar a autenticação num SSO que, futuramente, suportaria Gov.br como identity provider — sem precisar mexer no código do portal toda vez que o IdP mudar.

A escolha foi Keycloak, deployado no Cloud Run:

**[infra#120](https://github.com/destaquesgovbr/infra/pull/120):** toda a infra Keycloak em Terraform — database no Cloud SQL existente, service account dedicada, Artifact Registry para imagens Docker, Cloud Run com 2 vCPU, 1Gi e `min=1` (always-on), 4 secrets no Secret Manager, IAM granular. Seguiu exatamente o padrão de `federation.tf` que já existia no repo.

**[infra#121](https://github.com/destaquesgovbr/infra/pull/121):** fix imediato — as health probes estavam apontando para a porta padrão, mas o Keycloak expõe management na porta 9000.

**[portal#98](https://github.com/destaquesgovbr/portal/pull/98):** a migração no portal foi zero código. O `auth.ts` já suportava OIDC genérico via `AUTH_GOVBR_ISSUER`. Bastou trocar a variável de ambiente apontando para o Keycloak DGB e substituir os secrets do Google pelos do Keycloak.

```
Antes:  Usuário → Portal → NextAuth → Google
Depois: Usuário → Portal → NextAuth → Keycloak → Google (upstream IdP)
```

A camada extra do Keycloak parece overhead, mas abre espaço para adicionar Gov.br, autenticação de parceiros e políticas de acesso sem tocar no código do portal.

---

## Números

| Frente | PRs | Repos | Testes |
|--------|-----|-------|--------|
| Scraper | 4 | scraper | 98 → 109 |
| Push Notifications | 6 | push-notifications, infra | 77 → 114 |
| Keycloak SSO | 3 | infra, portal | — |
| **Total** | **13** | **4** | **+46** |

---

## Lições

1. **Trabalho paralelo funciona quando as frentes são independentes.** Scraper, push notifications e Keycloak não tinham dependências entre si — cada frente avançou no próprio ritmo sem bloquear as outras.

2. **TDD ajuda mais em otimizações do que em features novas.** O known URL fence foi escrito com testes primeiro porque a lógica de skip+fence tinha muitos edge cases (backward compat, sem known_urls, fence count). Os testes capturaram 2 bugs antes do PR.

3. **Infraestrutura como código paga dividendos.** Subir o Keycloak no Cloud Run foi possível porque o padrão `federation.tf` já estava estabelecido. Copiar a estrutura e ajustar os valores levou menos tempo do que configurar via console.

4. **Auto-desativação é essencial para sistemas de notificação.** Bots bloqueados e canais inacessíveis acumulam silenciosamente. A remoção automática de assinaturas falhas (e o contador de falhas nos canais) evita que o sistema tente em loop entregar para destinos mortos.
