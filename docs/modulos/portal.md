# Módulo: Portal (portal)

> Portal web para busca e navegação de notícias governamentais.

**Repositório**: [github.com/destaquesgovbr/portal](https://github.com/destaquesgovbr/portal)

**URL Produção**: [destaquesgovbr-portal-klvx64dufq-rj.a.run.app](https://destaquesgovbr-portal-klvx64dufq-rj.a.run.app/) _(URL provisória - Cloud Run/GCP)_

## Visão Geral

O portal é a interface principal do DestaquesGovbr, oferecendo:

- **Busca full-text** com Typesense
- **Filtros** por órgão, tema e data
- **Navegação** por temas e órgãos
- **Páginas individuais** de notícias
- **Feeds RSS/Atom/JSON** com filtros dinâmicos

```mermaid
flowchart LR
    U[Usuário] --> P[Portal Next.js]
    P --> T[(Typesense)]
    T --> HF[(HuggingFace)]
    P --> CF[Configurações YAML]
    P --> F[Feeds API<br/>RSS/Atom/JSON]
    F --> T
```

---

## Stack Tecnológico

| Tecnologia   | Versão | Uso                          |
| ------------ | ------ | ---------------------------- |
| Next.js      | 15     | Framework React (App Router) |
| TypeScript   | 5      | Tipagem estática             |
| Typesense    | -      | Busca full-text              |
| shadcn/ui    | -      | Componentes UI               |
| Tailwind CSS | 3      | Estilização                  |
| React Query  | 5      | Data fetching                |
| Biome        | -      | Lint + Format                |

---

## Estrutura do Repositório

```
portal/
├── src/
│   ├── app/                         # App Router (Next.js 15)
│   │   ├── page.tsx                 # Homepage
│   │   ├── layout.tsx               # Layout principal
│   │   ├── globals.css              # Estilos globais
│   │   ├── temas/
│   │   │   └── [themeLabel]/        # Páginas por tema
│   │   │       └── page.tsx
│   │   ├── orgaos/
│   │   │   └── [agencyKey]/         # Páginas por órgão
│   │   │       └── page.tsx
│   │   ├── noticias/
│   │   │   └── [id]/                # Página de notícia
│   │   │       └── page.tsx
│   │   ├── feeds/
│   │   │   └── page.tsx             # Página de descoberta de feeds
│   │   ├── feed.xml/route.ts        # RSS 2.0 API route
│   │   ├── feed.atom/route.ts       # Atom 1.0 API route
│   │   ├── feed.json/route.ts       # JSON Feed 1.1 API route
│   │   └── api/                     # API Routes
│   ├── components/
│   │   ├── ui/                      # Componentes shadcn/ui
│   │   ├── search/                  # Busca e filtros
│   │   ├── news/                    # Cards e listas de notícias
│   │   ├── layout/                  # Header, Footer, Nav
│   │   ├── filters/                 # Filtros de busca
│   │   └── common/
│   │       └── FeedLink.tsx         # Link RSS contextual
│   ├── lib/
│   │   ├── typesense-client.ts      # Cliente Typesense
│   │   ├── feed.ts                  # Lógica core de feeds (parsing, validação, serialização)
│   │   ├── feed-handler.ts          # Handler HTTP compartilhado (ETag, cache)
│   │   ├── markdown-to-html.ts      # Conversor markdown → HTML para feeds
│   │   ├── themes.yaml              # Árvore temática
│   │   ├── agencies.yaml            # Catálogo de órgãos
│   │   ├── prioritization.yaml      # Config de priorização
│   │   └── utils.ts                 # Utilitários
│   ├── hooks/                       # React hooks customizados
│   └── types/                       # Definições TypeScript
├── public/                          # Assets estáticos
├── docs/
│   ├── FEEDS_API.md                 # Documentação completa da API de feeds
│   └── FEEDS_ARCHITECTURE.md        # Arquitetura técnica dos feeds
├── .github/workflows/
│   └── deploy-production.yml        # Deploy Cloud Run
├── package.json
├── tailwind.config.ts
├── next.config.ts
├── tsconfig.json
└── Dockerfile
```

---

## Páginas Principais

### Homepage (`/`)

- Lista de notícias mais recentes
- Busca com autocomplete
- Filtros rápidos por tema
- Notícias priorizadas (destaques)

### Página de Tema (`/temas/[themeLabel]`)

- Notícias filtradas por tema
- Breadcrumb de navegação
- Subtemas disponíveis

### Página de Órgão (`/orgaos/[agencyKey]`)

- Notícias do órgão específico
- Informações do órgão
- Órgãos relacionados (hierarquia)

### Página de Notícia (`/noticias/[id]`)

- Conteúdo completo
- Metadados (data, órgão, tema)
- Notícias relacionadas

### Página de Feeds (`/feeds`)

- **Construtor interativo**: Multi-select de órgãos e temas, gera URLs dos 3 formatos (RSS/Atom/JSON) em tempo real
- **Feeds por Ministério**: Grid com links diretos RSS/Atom para cada ministério
- **Feeds por Tema**: Grid com links diretos RSS/Atom para cada tema de nível 1
- **Instruções**: Guia passo a passo para usar os feeds em leitores RSS

### Feeds API

- **`/feed.xml`**: RSS 2.0
- **`/feed.atom`**: Atom 1.0
- **`/feed.json`**: JSON Feed 1.1

**Parâmetros suportados**:
- `agencias` - Filtrar por órgãos (ex: `agencias=mre,saude`)
- `temas` - Filtrar por temas (ex: `temas=01,03`)
- `tag` - Filtrar por tag exata
- `q` - Busca textual em título e conteúdo
- `limit` - Quantidade de itens (default: 20, máx: 50)

→ Documentação completa em [portal/docs/FEEDS_API.md](https://github.com/destaquesgovbr/portal/blob/main/docs/FEEDS_API.md)

---

## Componentes Principais

### SearchBar

```tsx
// Barra de busca com autocomplete
<SearchBar
  placeholder="Buscar notícias..."
  onSearch={(query) => handleSearch(query)}
  suggestions={suggestions}
/>
```

### NewsCard

```tsx
// Card de notícia
<NewsCard
  title={news.title}
  summary={news.summary}
  agency={news.agency}
  publishedAt={news.published_at}
  theme={news.theme_1_level_1_label}
  imageUrl={news.image}
  href={`/noticias/${news.unique_id}`}
/>
```

### FilterPanel

```tsx
// Painel de filtros
<FilterPanel
  agencies={agencies}
  themes={themes}
  selectedAgencies={selected.agencies}
  selectedThemes={selected.themes}
  dateRange={dateRange}
  onFilterChange={handleFilterChange}
/>
```

---

## Cliente Typesense

### Configuração (`typesense-client.ts`)

```typescript
import Typesense from "typesense";

const client = new Typesense.Client({
  nodes: [
    {
      host: process.env.TYPESENSE_HOST,
      port: Number(process.env.TYPESENSE_PORT),
      protocol: process.env.TYPESENSE_PROTOCOL,
    },
  ],
  apiKey: process.env.TYPESENSE_API_KEY,
  connectionTimeoutSeconds: 2,
});
```

### Função de Busca

```typescript
interface SearchParams {
  query: string;
  filters?: {
    agency?: string[];
    theme_1_level_1_code?: string[];
    dateFrom?: number;
    dateTo?: number;
  };
  page?: number;
  perPage?: number;
  sortBy?: string;
}

async function searchNews(params: SearchParams): Promise<SearchResult> {
  const { query, filters, page = 1, perPage = 20 } = params;

  // Construir filter_by
  const filterClauses: string[] = [];
  if (filters?.agency?.length) {
    filterClauses.push(`agency:[${filters.agency.join(",")}]`);
  }
  if (filters?.theme_1_level_1_code?.length) {
    filterClauses.push(
      `theme_1_level_1_code:[${filters.theme_1_level_1_code.join(",")}]`
    );
  }
  if (filters?.dateFrom) {
    filterClauses.push(`published_at:>=${filters.dateFrom}`);
  }

  const result = await client
    .collections("news")
    .documents()
    .search({
      q: query || "*",
      query_by: "title,content,summary",
      filter_by: filterClauses.join(" && ") || undefined,
      sort_by: "published_at:desc",
      page,
      per_page: perPage,
      highlight_fields: "title,summary",
    });

  return result;
}
```

---

## Schema do Documento Typesense

```typescript
interface NewsDocument {
  id: string; // unique_id
  unique_id: string;
  agency: string; // ex: "gestao"
  title: string;
  url: string;
  image?: string;
  content: string; // Markdown
  published_at: number; // Unix timestamp
  category?: string;
  tags?: string[];

  // Campos enriquecidos
  theme_1_level_1_code?: string; // ex: "01"
  theme_1_level_1_label?: string; // ex: "Economia e Finanças"
  theme_1_level_2_code?: string;
  theme_1_level_2_label?: string;
  theme_1_level_3_code?: string;
  theme_1_level_3_label?: string;
  most_specific_theme_code?: string;
  most_specific_theme_label?: string;
  summary?: string; // Resumo AI
}
```

---

## Arquivos de Configuração

### `themes.yaml` - Árvore Temática

```yaml
themes:
  - label: Economia e Finanças
    code: "01"
    children:
      - label: Política Econômica
        code: "01.01"
        children:
          - label: Política Fiscal
            code: "01.01.01"
          - label: Autonomia Econômica
            code: "01.01.02"
```

### `agencies.yaml` - Catálogo de Órgãos

```yaml
sources:
  gestao:
    name: Ministério da Gestão e da Inovação em Serviços Públicos
    parent: presidencia
    type: Ministério

  inpe:
    name: Instituto Nacional de Pesquisas Espaciais
    parent: mcti
    type: Instituto
```

### `prioritization.yaml` - Priorização

```yaml
# Órgãos com notícias priorizadas no topo
priority_agencies:
  - presidencia
  - gestao
  - fazenda
  - saude

# Temas em destaque
priority_themes:
  - "01" # Economia
  - "03" # Saúde
  - "20" # Políticas Públicas
```

---

## Server Components vs Client Components

### Server Components (padrão)

```tsx
// app/temas/[themeLabel]/page.tsx
export default async function ThemePage({ params }: Props) {
  // Busca no servidor
  const news = await searchNews({
    query: "*",
    filters: { theme_1_level_1_label: [params.themeLabel] },
  });

  return <NewsList news={news.hits} />;
}
```

### Client Components

```tsx
"use client";

// components/search/SearchBar.tsx
export function SearchBar() {
  const [query, setQuery] = useState("");

  // Interatividade no cliente
  return <input value={query} onChange={(e) => setQuery(e.target.value)} />;
}
```

---

## Variáveis de Ambiente

```bash
# .env.local (desenvolvimento)
TYPESENSE_HOST=localhost
TYPESENSE_PORT=8108
TYPESENSE_PROTOCOL=http
TYPESENSE_API_KEY=xyz
TYPESENSE_COLLECTION_NAME=news

# Produção (via Secret Manager)
TYPESENSE_HOST=<ip-interno>
TYPESENSE_PORT=8108
TYPESENSE_PROTOCOL=http
TYPESENSE_API_KEY=<api-key-producao>
```

---

## Comandos de Desenvolvimento

```bash
# Instalar dependências
pnpm install

# Desenvolvimento
pnpm dev

# Build de produção
pnpm build

# Rodar build local
pnpm start

# Lint
pnpm lint

# Formatar
pnpm format

# Type check
pnpm type-check
# ou
pnpm exec tsc --noEmit
```

---

## Componentes shadcn/ui

### Adicionar componente

```bash
npx shadcn@latest add button
npx shadcn@latest add card
npx shadcn@latest add input
npx shadcn@latest add select
```

### Usar componente

```tsx
import { Button } from "@/components/ui/button";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Input } from "@/components/ui/input";

export function Example() {
  return (
    <Card>
      <CardHeader>
        <CardTitle>Buscar</CardTitle>
      </CardHeader>
      <CardContent>
        <Input placeholder="Digite sua busca..." />
        <Button>Buscar</Button>
      </CardContent>
    </Card>
  );
}
```

---

## Deploy

### Automático (GitHub Actions)

Push para `main` → Deploy automático via `deploy-production.yml`

### Manual

```bash
# Build Docker
docker build -t portal .

# Push para Artifact Registry
docker tag portal gcr.io/PROJECT_ID/portal
docker push gcr.io/PROJECT_ID/portal

# Deploy Cloud Run
gcloud run deploy portal \
  --image gcr.io/PROJECT_ID/portal \
  --region us-east1
```

---

## Feeds RSS/Atom/JSON

### Características

- ✅ **3 formatos padrão**: RSS 2.0, Atom 1.0, JSON Feed 1.1
- ✅ **Filtros dinâmicos**: Por órgão, tema, tag e busca textual
- ✅ **Construtor interativo**: Página `/feeds` com multi-select de órgãos/temas
- ✅ **Links contextuais**: Feeds automáticos em páginas de busca, tema e órgão
- ✅ **Autodiscovery**: Tags `<link rel="alternate">` no `<head>`
- ✅ **Caching otimizado**: `Cache-Control` com 10min + ETag para 304 Not Modified
- ✅ **Markdown → HTML**: Conversão server-side com mesmo pipeline do portal

### Endpoints

```
GET /feed.xml?agencias=mre,saude&temas=01&q=reforma&limit=30
GET /feed.atom?agencias=gestao&temas=03
GET /feed.json?temas=01,20&limit=50
```

### Implementação

**Arquitetura**:
```
Route Handler (/feed.xml/route.ts)
    ↓
handleFeedRequest() (feed-handler.ts)
    ↓
parseFeedParams() → validateFeedParams() → buildFeed()
    ↓
queryArticlesForFeed() → Typesense
    ↓
markdownToHtml() → serializeFeed(format)
    ↓
computeETag() → Response (200 ou 304)
```

**Validação**:
- `agencias`: Verifica existência em `agencies.yaml`
- `temas`: Verifica existência em `themes.yaml`
- `q`: Máximo 200 caracteres
- `limit`: Entre 1-50

**Caching**:
- `Cache-Control: public, s-maxage=600, stale-while-revalidate=60`
- `ETag`: MD5 do body
- `If-None-Match` → 304 Not Modified

**Título dinâmico**:
```
/feed.xml → "Destaques GOV.BR"
/feed.xml?agencias=mre → "Destaques GOV.BR — Ministério das Relações Exteriores"
/feed.xml?temas=03 → "Destaques GOV.BR — Saúde"
/feed.xml?q=reforma → "Destaques GOV.BR — Busca: reforma"
```

### Testes

**Cobertura**: 43 testes unitários (32 em `feed.test.ts` + 11 em `markdown-to-html.test.ts`)

**Áreas testadas**:
- Parsing e validação de parâmetros
- Query Typesense com filtros combinados
- Serialização nos 3 formatos
- Conversão markdown → HTML
- ETag computation e 304 responses
- Tratamento de erros (400, 500)

### Documentação Adicional

→ **API completa**: [portal/docs/FEEDS_API.md](https://github.com/destaquesgovbr/portal/blob/main/docs/FEEDS_API.md) (198 linhas)  
→ **Arquitetura técnica**: [portal/docs/FEEDS_ARCHITECTURE.md](https://github.com/destaquesgovbr/portal/blob/main/docs/FEEDS_ARCHITECTURE.md)

---

## Links Relacionados

- [Visão Geral da Arquitetura](../arquitetura/visao-geral.md)
- [Setup Frontend](../onboarding/setup-frontend.md) - Guia de desenvolvimento
- [Typesense Local](./typesense-local.md) - Ambiente de desenvolvimento
- [Deploy do Portal](../workflows/portal-deploy.md) - GitHub Actions
