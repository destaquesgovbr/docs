# MLflow no DGB — Slides

Apresentação interna (*tech talk*, PT-BR) da **plataforma de MLflow compartilhada** do
DestaquesGovBr: o que é, a arquitetura dos dois caminhos (metadados via IAP, artefatos direto
no GCS) e como começar a usar hoje. São **20 slides**, 16:9.

!!! tip "Navegação"
    Use as **setas ←/→**, **espaço** ou **clique** na metade esquerda/direita para navegar.
    `R` reseta. Para exportar em PDF, abra em tela cheia e use `Ctrl/Cmd+P` (1 página por slide).

<div style="position:relative;width:100%;aspect-ratio:16/9;margin:1.5rem 0;
            border-radius:8px;overflow:hidden;border:1px solid var(--md-default-fg-color--lightest);">
  <iframe src="deck.html" title="Slides: MLflow no DGB" loading="lazy"
          allow="fullscreen"
          style="position:absolute;inset:0;width:100%;height:100%;border:0;"></iframe>
</div>

[:material-fullscreen: Abrir os slides em tela cheia →](deck.html){target=_blank}

---

## Sobre este deck

Para o tutorial completo de uso (instalação do cliente, primeiro experimento, Model Registry e
GenAI), veja **[Módulo: MLflow DGB](../../modulos/mlflow.md)**.

| | |
|---|---|
| **Servidor** | `https://destaquesgovbr-mlflow-klvx64dufq-rj.a.run.app` |
| **Instalação do cliente** | `pip install "git+https://github.com/destaquesgovbr/ml-platform.git@v0.1.0#subdirectory=client"` |
| **Pacote / versões** | `dgb-mlflow` v0.1.0 · MLflow 3.13.0 · Python 3.11+ |
| **Repositório** | [destaquesgovbr/ml-platform](https://github.com/destaquesgovbr/ml-platform) |

A fonte editável dos slides (HTML estático + `deck-stage.js`) é mantida pelo Claude Design; para
atualizar o conteúdo, regenere o bundle `deck.html` e substitua o arquivo desta pasta.
