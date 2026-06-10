# Apresentações

Slides dos projetos do **DestaquesGovBr**, publicados direto no site da documentação.
Cada deck é uma página própria: dá para navegar embutido aqui ou abrir em tela cheia, e
exportar para PDF (`Ctrl/Cmd+P`).

## Decks disponíveis

| Deck | Tema | Slides |
|------|------|--------|
| [MLflow no DGB](mlflow-no-dgb/index.md) | Plataforma de MLflow compartilhada — o que é, arquitetura e como usar | 20 |

---

## Como publicar um novo deck

O fluxo é self-service e não exige nenhuma configuração nova no MkDocs:

1. **Gere o bundle** `deck.html` (HTML single-file, com fontes/JS embutidos). Os slides do
   DGB costumam vir do Claude Design já nesse formato.
2. **Crie uma pasta** por deck em `docs/apresentacoes/<slug>/` e coloque o `deck.html` dentro.
   Usar uma pasta por deck (com `index.md`) é o que faz o `<iframe src="deck.html">` resolver
   certo com `use_directory_urls` ligado (default do projeto).
3. **Crie o `index.md`** da pasta embutindo o deck (copie o bloco da página do MLflow).
4. **Adicione ao `nav`** do `mkdocs.yml`, sob `Apresentações`.
5. **Registre o deck** na tabela acima.

O MkDocs copia qualquer arquivo não-`.md` dentro de `docs/` para o site automaticamente —
o `deck.html` é servido como asset estático ao lado da página.
