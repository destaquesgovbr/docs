# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Documentation site for **DestaquesGovbr**, a government news aggregation platform that centralizes ~160+ Brazilian gov.br portals with AI-powered semantic search. This repo contains only the MkDocs documentation — the actual platform code lives in separate repos (data-platform, portal, scraper, agencies, themes, infra).

## Build & Development Commands

```bash
# Install dependencies
poetry install

# Local dev server (hot-reload)
poetry run mkdocs serve

# Build static site
poetry run mkdocs build
```

No tests or linter configured in this repo. CI runs `poetry run mkdocs build` on push/PR to main and deploys to GitHub Pages on merge.

## Architecture

- **Build tool**: MkDocs with Material theme, managed via Poetry (Python 3.11+)
- **Config**: `mkdocs.yml` — defines nav structure, theme, plugins, markdown extensions
- **Content**: all docs live under `docs/` as Markdown files
- **Output**: built to `site/` (gitignored)
- **Deploy**: GitHub Actions → GitHub Pages (automatic on main)

### Content Sections

| Section | Path | Purpose |
|---------|------|---------|
| Arquitetura | `docs/arquitetura/` | System design & data flow |
| Módulos | `docs/modulos/` | Per-module reference (scraper, portal, data-platform, etc.) |
| Workflows | `docs/workflows/` | CI/CD pipelines & DAGs |
| Infraestrutura | `docs/infraestrutura/` | GCP/Terraform setup |
| Onboarding | `docs/onboarding/` | Developer tracks (backend, frontend, data science) |
| Blog | `docs/blog/` | Dev storytelling posts |

### MkDocs Plugins & Extensions

- **Blog plugin**: posts go in `docs/blog/posts/`, use `<!-- more -->` for excerpt separator
- **Mermaid diagrams**: use ` ```mermaid ` fenced blocks
- **Admonition**: `!!! note`, `!!! warning`, etc.
- **Tabbed content**: `pymdownx.tabbed` with alternate style
- **Search**: configured for Portuguese (`lang: pt`)

## Conventions

- **Language**: all content is in Brazilian Portuguese (pt-BR)
- **Commit messages**: Conventional Commits (`feat:`, `fix:`, `docs:`, `chore:`, etc.)
- **Navigation**: any new page must be added to the `nav:` section in `mkdocs.yml`
- **Blog posts**: filename format `YYYY-MM-DD-slug.md` with YAML frontmatter (date, authors, categories, tags)
- **Diagrams**: prefer Mermaid over static images for architecture/flow diagrams
