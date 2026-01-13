# Módulo: Scraper (Arquivado)

!!! warning "Módulo Migrado"
    Este módulo foi migrado para o repositório **data-platform**.
    O repositório `scraper` foi arquivado.

    **Novo repositório**: [github.com/destaquesgovbr/data-platform](https://github.com/destaquesgovbr/data-platform)

---

## Documentação Atualizada

A funcionalidade de scraping agora faz parte do repositório unificado `data-platform`. Consulte:

- **[Data Platform](data-platform.md)** - Visão geral do repositório unificado
- **[Fluxo de Dados](../arquitetura/fluxo-de-dados.md)** - Pipeline completo de coleta e enriquecimento
- **[PostgreSQL](../arquitetura/postgresql.md)** - Banco de dados central (fonte de verdade)

## Principais Mudanças

| Antes (scraper) | Agora (data-platform) |
|-----------------|----------------------|
| Repositório separado | Repositório unificado |
| HuggingFace como fonte de verdade | PostgreSQL como fonte de verdade |
| `python src/main.py scrape` | `data-platform scrape` |
| DatasetManager (HF) | PostgresManager + StorageAdapter |

## CLI Atual

```bash
# Raspagem de sites gov.br
data-platform scrape --start-date YYYY-MM-DD --end-date YYYY-MM-DD

# Raspagem de sites EBC
data-platform scrape-ebc --start-date YYYY-MM-DD --end-date YYYY-MM-DD

# Upload para Cogfy (enriquecimento)
data-platform upload-cogfy --start-date YYYY-MM-DD --end-date YYYY-MM-DD

# Buscar enriquecimento do Cogfy
data-platform enrich --start-date YYYY-MM-DD --end-date YYYY-MM-DD
```

## Arquivos Principais (Novo Local)

| Componente | Localização |
|------------|-------------|
| WebScraper | `src/data_platform/scrapers/webscraper.py` |
| EBCWebScraper | `src/data_platform/scrapers/ebc_webscraper.py` |
| ScrapeManager | `src/data_platform/scrapers/scrape_manager.py` |
| PostgresManager | `src/data_platform/managers/postgres_manager.py` |
| StorageAdapter | `src/data_platform/managers/storage_adapter.py` |
| site_urls.yaml | `src/data_platform/scrapers/site_urls.yaml` |
| agencies.yaml | `src/data_platform/scrapers/agencies.yaml` |
