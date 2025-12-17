# Troubleshooting

> Problemas comuns e suas soluções para desenvolvedores do DestaquesGovbr.

## Índice

- [Scraper (Python)](#scraper-python)
- [Portal (TypeScript)](#portal-typescript)
- [Typesense](#typesense)
- [Docker](#docker)
- [GitHub Actions](#github-actions)
- [HuggingFace](#huggingface)
- [GCP](#gcp)

---

## Scraper (Python)

### Erro: `ModuleNotFoundError`

```
ModuleNotFoundError: No module named 'src'
```

**Causa**: Ambiente virtual não ativado ou dependências não instaladas.

**Solução**:

```bash
# Ativar ambiente virtual
poetry shell

# Reinstalar dependências
poetry install --sync
```

---

### Erro: `HfHubHTTPError` ou `401 Unauthorized`

```
HfHubHTTPError: 401 Client Error: Unauthorized
```

**Causa**: Token HuggingFace inválido ou expirado.

**Solução**:

```bash
# Verificar se HF_TOKEN está configurado
echo $HF_TOKEN

# Fazer login manual
huggingface-cli login

# Ou configurar no .env
HF_TOKEN=hf_xxxxxxxxxxxxx
```

---

### Erro: `ConnectionError` ao raspar sites

```
requests.exceptions.ConnectionError: Connection refused
```

**Causa**: Site gov.br indisponível ou bloqueio temporário.

**Solução**:

1. Aguardar alguns minutos e tentar novamente
2. Verificar se o site está acessível no navegador
3. O scraper tem retry automático (5 tentativas)

---

### Erro: `KeyError` no parsing HTML

```
KeyError: 'title'
```

**Causa**: Estrutura HTML do site mudou.

**Solução**:

1. Verificar estrutura atual do site no navegador
2. Atualizar seletores em `webscraper.py`
3. Reportar issue se for mudança permanente

---

### Scraping muito lento

**Causa**: Muitos sites ou conexão lenta.

**Solução**:

```bash
# Raspar apenas alguns órgãos para teste
# Editar site_urls.yaml temporariamente

# Ou usar período menor
python src/main.py scrape --start-date $(date +%Y-%m-%d) --end-date $(date +%Y-%m-%d)
```

---

## Portal (TypeScript)

### Erro: `ECONNREFUSED` ao conectar Typesense

```
Error: connect ECONNREFUSED 127.0.0.1:8108
```

**Causa**: Typesense não está rodando.

**Solução**:

```bash
# Verificar se container está rodando
docker ps | grep typesense

# Se não estiver, subir
cd typesense
docker compose up -d

# Verificar saúde
curl http://localhost:8108/health
```

---

### Erro: `Type error` no build

```
Type error: Property 'x' does not exist on type 'y'
```

**Solução**:

```bash
# Verificar erros de tipo
pnpm type-check

# Corrigir tipos ou adicionar definições
```

---

### Página em branco / sem notícias

**Causa**: Typesense sem dados ou configuração incorreta.

**Solução**:

1. Verificar console do navegador para erros
2. Verificar se Typesense tem dados:

```bash
curl "http://localhost:8108/collections/news/documents/search?q=*" \
  -H "X-TYPESENSE-API-KEY: xyz"
```

3. Carregar dados se necessário:

```bash
cd typesense/python
python scripts/load_data.py --mode incremental --days 7
```

---

### Erro de CORS

```
Access-Control-Allow-Origin error
```

**Causa**: Requisições cross-origin bloqueadas.

**Solução**: Verificar se está usando `localhost` consistentemente (não misturar com `127.0.0.1`).

---

### Componente shadcn não renderiza

**Causa**: Componente não instalado ou importação incorreta.

**Solução**:

```bash
# Reinstalar componente
npx shadcn@latest add <nome-componente>

# Verificar importação
import { Button } from "@/components/ui/button"  # Correto
import { Button } from "shadcn"                  # Incorreto
```

---

## Typesense

### Erro: `Collection not found`

```
Could not find a collection named 'news'
```

**Causa**: Collection não criada ou nome diferente.

**Solução**:

```bash
# Listar collections existentes
curl http://localhost:8108/collections -H "X-TYPESENSE-API-KEY: xyz"

# Criar collection (script de carga faz isso automaticamente)
cd typesense/python
python scripts/load_data.py --mode full
```

---

### Busca não retorna resultados esperados

**Causa**: Dados desatualizados ou query incorreta.

**Solução**:

```bash
# Verificar quantidade de documentos
curl "http://localhost:8108/collections/news" -H "X-TYPESENSE-API-KEY: xyz"

# Testar busca manual
curl "http://localhost:8108/collections/news/documents/search?q=economia&query_by=title,content" \
  -H "X-TYPESENSE-API-KEY: xyz"
```

---

### Typesense usando muita memória

**Causa**: Dataset grande em memória.

**Solução**:

```bash
# Reiniciar com limite de memória
docker compose down
docker compose up -d

# Ou carregar menos dados
python scripts/load_data.py --mode incremental --days 3
```

---

## Docker

### Erro: `Cannot connect to Docker daemon`

```
Cannot connect to the Docker daemon at unix:///var/run/docker.sock
```

**Causa**: Docker Desktop não está rodando.

**Solução**: Iniciar Docker Desktop ou o daemon do Docker.

---

### Erro: `Port already in use`

```
Error: bind: address already in use
```

**Causa**: Outra aplicação usando a porta.

**Solução**:

```bash
# Descobrir o que está usando a porta
lsof -i :8108

# Matar o processo
kill -9 <PID>

# Ou usar outra porta no docker-compose
```

---

### Container não inicia

**Solução**:

```bash
# Ver logs do container
docker logs <container_id>

# Remover e recriar
docker compose down
docker compose up -d --force-recreate
```

---

## GitHub Actions

### Workflow falhou

**Solução**:

1. Acessar a aba "Actions" no repositório
2. Clicar no workflow que falhou
3. Expandir o step com erro
4. Analisar logs

---

### Secret não encontrado

```
Error: Input required and not supplied: HF_TOKEN
```

**Causa**: Secret não configurado no repositório.

**Solução**: Solicitar ao admin para adicionar a secret em Settings > Secrets.

---

### Workflow não dispara

**Causa**: Trigger incorreto ou branch errada.

**Solução**:

1. Verificar triggers no arquivo `.github/workflows/*.yaml`
2. Verificar se está na branch correta
3. Disparar manualmente se necessário

---

## HuggingFace

### Erro de autenticação

```
huggingface_hub.utils._errors.HfHubHTTPError: 401 Client Error
```

**Solução**:

```bash
# Fazer login
huggingface-cli login

# Verificar token
huggingface-cli whoami
```

---

### Push muito lento

**Causa**: Dataset grande ou conexão lenta.

**Solução**: O sistema tem retry automático. Aguardar conclusão.

---

### Dataset corrompido

**Causa**: Push interrompido.

**Solução**:

1. Verificar se há commits parciais no HuggingFace
2. Reverter para versão anterior se necessário
3. Refazer o push

---

## GCP

### Erro de permissão

```
Error 403: Permission denied
```

**Causa**: Conta de serviço sem permissões.

**Solução**: Solicitar ao admin para verificar IAM.

---

### Cloud Run não atualiza

**Causa**: Cache ou deploy não completou.

**Solução**:

```bash
# Verificar status do deploy
gcloud run services describe portal --region=us-east1

# Forçar novo deploy
# (via GitHub Actions ou manualmente)
```

---

## Comandos Úteis para Debug

### Verificar ambiente Python

```bash
python --version
poetry --version
poetry env info
poetry show
```

### Verificar ambiente Node

```bash
node --version
pnpm --version
pnpm list
```

### Verificar Docker

```bash
docker --version
docker ps
docker images
docker logs <container_id>
```

### Verificar Typesense

```bash
# Saúde
curl http://localhost:8108/health

# Collections
curl http://localhost:8108/collections -H "X-TYPESENSE-API-KEY: xyz"

# Contagem de docs
curl http://localhost:8108/collections/news -H "X-TYPESENSE-API-KEY: xyz"
```

### Verificar GitHub

```bash
git status
git log --oneline -5
git remote -v
```

---

## Ainda com Problemas?

1. **Pesquise**: O erro já foi reportado nas issues?
2. **Logs**: Colete logs relevantes
3. **Reproduza**: Documente passos para reproduzir
4. **Pergunte**: Use o canal do projeto
5. **Reporte**: Abra uma issue se for bug novo

### Informações úteis ao reportar

```
- Sistema operacional:
- Versão do Python/Node:
- Versão do Docker:
- Comando executado:
- Mensagem de erro completa:
- Passos para reproduzir:
```

---

→ Voltar para [Roteiro de Onboarding](./roteiro-onboarding.md)
