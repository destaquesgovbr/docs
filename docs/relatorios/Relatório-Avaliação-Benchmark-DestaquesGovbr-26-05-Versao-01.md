Data: 29/05/2026

PROMPT: Analise exclusivamente o documento "relatorios\output\UX - Discovery - Bench_v2.pdf", e desse contexto, gere um documento com o nome "docs\relatorios\Relatório-Avaliação-Benchmark-DestaquesGovbr-26-05-Versao-01.md", usando como base o template "docs\relatorios\Template-Relatório Técnico INSPIRE.md", mantendo-se fiel ao conteúdo do arquivo original, assim como de sua divisão de sequencia dos tópicos abordados.

Elaborado por: Claude Sonnet 4.5 (Anthropic)

Revisado por: <!-- NÃO PREENCHA ESTE CAMPO: O humano preencherá manualmente-->

**Sumário** 

<!-- NÃO PREENCHA ESTE CAMPO: O humano incluirá manualmente-->

# **1 Objetivo deste documento**

Este documento apresenta uma avaliação de benchmarking de UX (User Experience) para o projeto **DestaquesGovBr**, analisando 10 plataformas de referência global em difusão de notícias e publicações governamentais, distribuídas em dois grupos:

- **Grupo A — Portais Governamentais**: GOV.UK (Reino Unido), USA.gov (Estados Unidos), Canada.ca (Canadá), Gov.br (Brasil) e Portugal.gov.pt (Portugal)
- **Grupo B — Agregadores de Notícias**: Google News, Feedly, Apple News, Flipboard e SmartNews

O benchmarking avalia cada plataforma em 6 dimensões de UX: (1) Arquitetura da Informação, (2) Busca e Filtragem, (3) Personalização de Feed, (4) Área do Usuário e Clipping, (5) Clareza de Conteúdo e (6) Comunicação e Engajamento. O objetivo é identificar padrões positivos e negativos, gaps de mercado que nenhum portal governamental resolve hoje, e oportunidades de diferenciação e inovação para o DestaquesGovBr.

Este relatório posiciona-se na fase **Descobrir (Discover)** do modelo Double Diamond de design e inovação, servindo como base para a próxima fase (Definir), onde serão criadas personas, jornadas, requisitos, wireframes e protótipos no Figma.

## **1.1 Nível de sigilo dos documentos**

Este documento é classificado como **Nível 2 – RESERVADO**, destinado aos envolvidos no projeto MGI/Finep e equipes técnicas do CPQD.

# **2 Público-alvo**

* Gestores de dados do Ministério da Gestão e da Inovação (MGI).  
* Equipes de desenvolvimento e arquitetura do CPQD.  
* Pesquisadores em Governança de Dados e IA.
* Equipes de design e produto do projeto DestaquesGovBr.

# **3 Desenvolvimento**

## **3.1 Contexto: O Problema que Justifica o Produto**

Para encontrar uma notícia oficial, o cidadão brasileiro precisa conhecer o organograma do Estado. Isso cria barreiras cognitivas severas, sobrecarga informacional e ineficiência crítica. O cenário atual apresenta:

- **160+ sites e portais federais** independentes e fragmentados (Decreto 9.756/2019 / Agência Brasil, jul. 2019)
- **23,4 minutos perdidos** a cada troca de contexto informacional (NewzTiQ Blog, 2025)
- **US$ 14 bilhões**: mercado global de agregadores de notícias (NewzTiQ Blog, 2025)

O DestaquesGovBr propõe centralizar, personalizar e verificar as notícias governamentais num único lugar, usando o conceito de **Government as a Platform (GaaP)**.

### **3.1.1 Fundamentação Teórica: Government as a Platform (GaaP)**

**Tim O'Reilly (2011)** cunhou o conceito no artigo 'Government as a Platform' (MIT Press): assim como Google, Amazon e Wikipedia aprenderam a usar o poder dos próprios usuários para co-criar valor, o governo deveria se tornar uma plataforma aberta — disponibilizando dados e infraestrutura para que cidadãos, empresas e desenvolvedores construam serviços sobre eles.

**Myeong (MDPI, 2020)** avança essa ideia usando o método AHP (Analytic Hierarchy Process), uma técnica de priorização por peso, para identificar quais fatores especialistas consideram mais importantes ao construir um GaaP. Resultado: especialistas priorizam o caráter público da plataforma — o governo deve focar em sua função primária, independente das características técnicas. Um GaaP orientado a dados é necessário para lidar com big data, múltiplos canais e serviços contratuais, onde governo, cidadãos e setor privado atuam como parceiros.

**Referências:**
- O'Reilly (2011): direct.mit.edu/itgg/article/6/1/13/9649
- Myeong (2020): mdpi.com/2071-1050/12/14/5615

## **3.2 Metodologia: Double Diamond e Posicionamento do Benchmarking**

Publicado originalmente em 2005 e revisado em 2015 pelo Design Council do Reino Unido, o **Double Diamond** é uma das metodologias de design e inovação mais adotadas no mundo — usada pelo próprio GOV.UK, pela BBC e por empresas como Lego e Philips. O modelo organiza o processo criativo em quatro fases:

1. **DESCOBRIR (Discover)**: divergir — coletar amplamente insights, pesquisar, observar, explorar → **Você está aqui**
2. **DEFINIR (Define)**: convergir — sintetizar descobertas, formular o problema correto
3. **DESENVOLVER (Develop)**: divergir — gerar ideias, prototipar, testar diferentes soluções
4. **ENTREGAR (Deliver)**: convergir — refinar, validar e lançar a solução

Este benchmarking posiciona-se como peça metodológica rigorosa dentro da fase de **Descoberta**: seu papel é divergir, coletar amplamente o que existe, antes de qualquer decisão de design. Os insights gerados aqui alimentam diretamente a fase seguinte (Definir): personas, jornadas e requisitos do DestaquesGovBr.

**Referência:**
- Design Council UK (2015): designcouncil.org.uk/our-resources/framework-for-innovation/

### **3.2.1 Seleção dos Players: E-Government Survey 2024 (ONU)**

O E-Government Survey é publicado a cada dois anos pela Divisão de Administração Pública da ONU (UNDESA). Mede a maturidade digital de 193 países usando o índice EGDI (E-Government Development Index), composto por três pilares:

- **Online Service Index**: qualidade e abrangência dos serviços digitais ao cidadão
- **Telecommunication Infrastructure Index**: conectividade e infraestrutura
- **Human Capital Index**: capacidade humana para usar e desenvolver serviços digitais

O relatório de 2024 apontou que o GaaP (Government as a Platform) é o modelo dominante nos países líderes, com governos atuando cada vez mais como catalisadores de ecossistemas digitais, não apenas como provedores de serviços.

**Justificativa para os players analisados no Grupo A:**
- GOV.UK (Reino Unido), USA.gov (EUA), Canada.ca (Canadá) e Portugal.gov.pt figuram consistentemente entre os líderes do índice EGDI
- Gov.br (Brasil) foi incluído como referência de contexto local — sendo o caso mais próximo ao DestaquesGovBr em termos de escala, idioma e desafios de fragmentação

**Referência:**
- ONU / UNDESA – E-Government Survey 2024: govinsider.asia/intl-en/article/asia-an-emerging-leader-in-digital-government

### **3.2.2 Framework de Avaliação: 6 Dimensões de UX**

Cada uma das 10 plataformas foi avaliada em 6 dimensões (escala 1–5), baseadas no framework de benchmarking de UX do Nielsen Norman Group:

1. **Arquitetura da Informação**: taxonomia, hierarquia, navegação, breadcrumbs, consistência estrutural
2. **Busca e Filtragem**: busca semântica, filtros progressivos, metadados, faceted search
3. **Personalização de Feed**: following explícito, ML/algoritmos, curadoria híbrida, diversidade de perspectivas
4. **Área do Usuário e Clipping**: autenticação, salvamento, organização (boards/folders), export, sync cross-device
5. **Clareza de Conteúdo**: plain language, metadados visíveis, sumarização, link para fonte primária, acessibilidade
6. **Comunicação e Engajamento**: combate a fake news, transparência afirmativa, canal de denúncia, FAQ educativo, federação

**Referência:**
- Nielsen Norman Group – Documenting a UX-Benchmarking Study

## **3.3 Análise dos Players**

### **3.3.1 Grupo A — Portais Governamentais**

#### **GOV.UK — Reino Unido**

**Avaliação:**
- Arquitetura da Informação: 5/5
- Busca e Filtragem: 4/5
- Personalização: 1/5
- Clipping: 1/5
- Clareza de Conteúdo: 5/5
- Comunicação e Engajamento: 4/5
- **Média: 3,3/5**

**O que faz de melhor:**

**Content Modelling Granular**
Blocos mínimos reutilizáveis — "estilo Lego". Um único dado publicado serve web, app, voz e IA sem retrabalho editorial. Base factual confiável para modelos de IA.

Publicado em abril de 2025 pela equipe de Arquitetura da Informação do Government Digital Service (GDS) do Reino Unido, o artigo descreve a evolução do GOV.UK: da publicação de páginas HTML estáticas para a fragmentação do conteúdo em blocos mínimos enriquecidos com metadados semânticos — o que a própria equipe chama de estrutura 'estilo Lego'.

Dois objetivos críticos dessa reestruturação:
- **Entrega omnicanal**: apps com espaço restrito de tela consultam a API e exibem apenas os dados essenciais para o cidadão naquele momento, sem carregar páginas HTML completas
- **Base de conhecimento para IA (ground truth)**: conteúdo altamente estruturado fornece fundação factual indispensável para modelos de IA, ancorando respostas em evidências rastreáveis e mitigando severamente o risco de alucinações algorítmicas

**Design System completo (WCAG 2.1 AA)**
Componentes testados com usuários reais. Step-by-step navigation para jornadas complexas. Breadcrumbs consistentes em todas as páginas.

**Taxonomia de ~4.000 tópicos**
Accordions e grids para escaneamento. Plain language mandatório via GOV.UK style guide. Busca semântica com aliases para termos familiares.

**Gap / Ausências:**
Personalização zero, sem clipping de notícias e sem canal de denúncia de fake news.

**Insight para o DestaquesGovBr:**
💡 Adotar content modelling desde o início — uma notícia publicada uma vez deve ser exibível no feed, app, notificações e respostas de IA sem retrabalho editorial.

**Referências:**
- Inside GOV.UK Blog, abr. 2025 (content modelling, ~4.000 tópicos): insidegovuk.blog.gov.uk/2025/04/10/how-information-architects-are-helping-to-build-gov-uks-future/
- design-system.service.gov.uk (Design System, WCAG 2.1 AA)

#### **USA.gov — Estados Unidos**

**Avaliação:**
- Arquitetura da Informação: 4/5
- Busca e Filtragem: 4/5
- Personalização: 1/5
- Clipping: 2/5
- Clareza de Conteúdo: 5/5
- Comunicação e Engajamento: 5/5
- **Média: 3,5/5**

**O que faz de melhor:**

**Busca Facetada (Search.gov)**
Filtros laterais progressivos por departamento, tipo de documento, data e tópico. Metadados dos CMS das agências expostos de forma padronizada.

**API-first (api.data.gov)**
Centenas de APIs abertas em tempo real — jornalistas e desenvolvedores consomem dados governamentais sem depender do portal como único canal.

**Atendimento multicanal e Section 508**
Telefone gratuito, chat online, formulário estruturado e processo formal para acessibilidade. Section 508 mandatório em todos os componentes.

**Gap / Ausências:**
Login.gov existe como autenticação unificada para serviços, mas nunca aplicado a curadoria de notícias.

**Insight para o DestaquesGovBr:**
💡 Busca facetada é padrão obrigatório para 160+ fontes. Filtros por órgão, tipo de publicação, data e categoria IPTC são essenciais para qualquer usuário.

**Referências:**
- USAGov Blog, dez. 2023 (busca facetada): usa.gov/blog/2023/12/less-is-more-improving-the-publics-web-search-experience-with-filters
- api.data.gov — U.S. GSA
- ADA.gov – Web Accessibility Guidance (Section 508)

#### **Canada.ca — Canadá**

**Avaliação:**
- Arquitetura da Informação: 5/5
- Busca e Filtragem: 4/5
- Personalização: 2/5
- Clipping: 1/5
- Clareza de Conteúdo: 5/5
- Comunicação e Engajamento: 4/5
- **Média: 3,5/5**

**O que faz de melhor:**

**Arquitetura flat e mobile-first**
Hierarquia rasa, navegação in-page mais eficaz que menus complexos. Templates testados em inglês/francês, mobile/tablet/desktop e tecnologias assistivas.

**Journey Maps e Service Blueprints**
Canada.ca Experience Office mapeia jornadas end-to-end antes de qualquer decisão de design — inclui serviços de múltiplas agências.

**Conteúdo único e autêntico (princípio)**
O governo não publica conteúdo para o qual não é fonte autoritativa. Duplicatas removidas sistematicamente. Ciclo de vida ativo.

**Gap / Ausências:**
Personalização em experimentação com geolocalização, mas não implementada. Sem clipping.

**Insight para o DestaquesGovBr:**
💡 Journey Maps são essenciais antes de prototipar. A jornada de um jornalista e a de um cidadão buscando benefícios são completamente distintas — cada persona exige caminhos específicos.

**Referências:**
- canada.ca/en/government/system/digital-government/design-with-users.html
- Canadian Digital Service, 2024

#### **Gov.br — Brasil**

**Avaliação:**
- Arquitetura da Informação: 4/5
- Busca e Filtragem: 3/5
- Personalização: 1/5
- Clipping: 3/5
- Clareza de Conteúdo: 4/5
- Comunicação e Engajamento: 3/5
- **Média: 3,0/5**

**O que faz de melhor:**

**Conta gov.br — dezenas de milhões de usuários**
SSO unificado com assinatura eletrônica, documentos digitais (CNH, CPF) e histórico de serviços. Infraestrutura de autenticação pronta.

**Design System GovBr v4**
Design tokens, componentes reutilizáveis, padrões de autenticação, biblioteca Figma. Versão 4.0 em desenvolvimento com modernizações.

**Catálogo de 3.000+ serviços + app mobile**
Organização temática (Saúde, Educação, Trabalho). App gov.br centraliza serviços, documentos e assinatura digital no celular.

**Gap / Ausências:**
Busca de notícias muito mais fraca que busca de serviços. Conta gov.br nunca usada para curadoria de notícias. Sem personalização ou canal anti fake news.

**Insight para o DestaquesGovBr:**
💡 A Conta gov.br é a maior oportunidade do projeto — infraestrutura com dezenas de milhões de usuários e custo de aquisição zero. Estender para preferências de notícias e clippings.

**Referências:**
- Decreto 9.756/2019 / Agência Brasil, jul. 2019 (~1.600 sites, R$ 43 mi investimento)
- next-ds.estaleiro.serpro.gov.br (Design System GovBr v4)

#### **Portugal.gov.pt — Portugal**

**Avaliação:**
- Arquitetura da Informação: 3/5
- Busca e Filtragem: 3/5
- Personalização: 1/5
- Clipping: 2/5
- Clareza de Conteúdo: 4/5
- Comunicação e Engajamento: 3/5
- **Média: 2,7/5**

**O que faz de melhor:**

**Chave Móvel Digital (CMD)**
Autenticação via SMS ou app, válida para serviços públicos e privados (banca, saúde, telecomunicações). Simplicidade + segurança — referência da lusofonia.

**Padrão jornalístico na redação**
Textos seguem regras editoriais claras. Notícias, comunicados e documentos claramente separados. Histórico de governos preservado.

**Gap / Ausências:**
Separação entre portal de notícias (portugal.gov.pt) e serviços (gov.pt) gera fricção. Busca básica. Personalização e clipping ausentes apesar da CMD existir.

**Insight para o DestaquesGovBr:**
💡 O DestaquesGovBr deve integrar notícias e serviços numa mesma experiência — o cidadão lê sobre um benefício e acessa o serviço no mesmo fluxo, sem trocar de portal.

**Referências:**
- autenticacao.gov.pt (Chave Móvel Digital)
- eportugal.gov.pt/en/sobre (portal de serviços)

### **3.3.2 Grupo B — Agregadores de Notícias**

#### **Google News**

**Avaliação:**
- Arquitetura da Informação: 5/5
- Busca e Filtragem: 5/5
- Personalização: 5/5
- Clipping: 4/5
- Clareza de Conteúdo: 5/5
- Comunicação e Engajamento: 3/5
- **Média: 4,5/5**

**O que faz de melhor:**

**Personalização em camadas distintas**
"For You" (ML histórico), "Headlines" (regional), "Following" (escolha explícita), "Newsstand" (exploração). Cada tab com propósito único e claro.

**Full Coverage — múltiplas perspectivas**
Exibe diversas fontes sobre o mesmo evento — combate o filter bubble mostrando que um fato pode ser narrado de formas diferentes.

**Preferred Sources + Fact-check labels**
Usuário escolhe outlets favoritos (2025). Fact Check Schema integra verificações de fatos nos resultados de busca e feed.

**Gap / Ausências:**
Clipping básico (sem boards/folders). Sem canal direto de denúncia de fake news ou FAQ educativo sobre verificação de fontes.

**Insight para o DestaquesGovBr:**
💡 Full Coverage aplicado ao governo: ao noticiar um programa de saúde, exibir automaticamente links para a portaria ministerial, dados orçamentários e estatísticas de implementação regional.

**Referências:**
- support.google.com/googlenews (personalização e Full Coverage)
- Straight Arrow News, ago. 2025 (Preferred Sources)
- Google News Initiative, 2024 (fact-check)

#### **Feedly · 12+ milhões de usuários**

**Avaliação:**
- Arquitetura da Informação: 5/5
- Busca e Filtragem: 5/5
- Personalização: 5/5
- Clipping: 5/5
- Clareza de Conteúdo: 5/5
- Comunicação e Engajamento: 4/5
- **Média: 4,8/5**

**O que faz de melhor:**

**Feeds > Folders > Boards (3 camadas)**
Organização multi-nível. Boards são coleções temáticas cross-feed — jornalistas organizam por pauta, pesquisadores por projeto, servidores por tema.

**AI Leo — filtra antes de você ler**
Assistente de IA que prioriza artigos relevantes antes da leitura, analisando milhões de conteúdos/dia. Age upstream — menos ruído, mais sinal.

**Export e 1.000+ integrações via Zapier**
Boards exportados para Notion, Google Sheets, Slack. Transforma o agregador em ferramenta de trabalho — não só de consumo passivo.

**Gap / Ausências:**
Sem foco em conteúdo governamental. Sem denúncia de fake news ou educação sobre verificação de fontes.

**Insight para o DestaquesGovBr:**
💡 Boards são o benchmark de clipping profissional. Jornalistas, servidores e pesquisadores precisam organizar por projeto — com possibilidade de anotar, exportar e compartilhar coleções.

**Referências:**
- Readless.app – Feedly vs Readwise Reader, abr. 2026 (12+ milhões de usuários, AI Leo, Zapier integrações)

#### **Apple News**

**Avaliação:**
- Arquitetura da Informação: 5/5
- Busca e Filtragem: 4/5
- Personalização: 5/5
- Clipping: 5/5
- Clareza de Conteúdo: 5/5
- Comunicação e Engajamento: 2/5
- **Média: 4,3/5**

**O que faz de melhor:**

**Curadoria híbrida: ML + equipe editorial**
Today tab combina top stories curadas por humanos com recomendações de ML — evita filter bubble (100% ML) e falta de escala (100% humano).

**Blocked Channels & Topics — controle total**
Usuário bloqueia fontes ou tópicos permanentemente. Controle granular explícito sobre o que nunca quer ver no feed.

**Saved Stories, History + Audio Stories offline**
Artigos salvos offline via iCloud, sincronizados entre iPhone, iPad e Mac. Audio Stories para consumo em mobilidade e acessibilidade.

**Gap / Ausências:**
Filtros de busca limitados. Canal de comunicação mínimo — sem denúncia de fake news. Exclusivo do ecossistema Apple.

**Insight para o DestaquesGovBr:**
💡 Curadoria híbrida é o modelo ideal para governo. Editores governamentais definem destaques do dia; o algoritmo personaliza o restante do feed para cada cidadão com base em interesses.

**Referências:**
- AppleInsider – Inside Apple News, mar. 2025 (curadoria híbrida, Saved Stories, Audio Stories, iCloud sync)

#### **Flipboard**

**Avaliação:**
- Arquitetura da Informação: 5/5
- Busca e Filtragem: 5/5
- Personalização: 5/5
- Clipping: 5/5
- Clareza de Conteúdo: 5/5
- Comunicação e Engajamento: 3/5
- **Média: 4,7/5**

**O que faz de melhor:**

**Smart Magazines — um canal por interesse**
Cada interesse vira uma revista separada, não um feed único que mistura tudo. Usuário swipa entre até 9 magazines no carousel da home.

**10M+ magazines de curadoria colaborativa**
Usuários criam e publicam magazines. Algoritmo combina sinais de máquinas e de pessoas — conteúdo humano indexado e amplificado por IA.

**Content Search — busca que vira revista**
Busca por topic, person ou hashtag gera uma 'revista instantânea' com todo o conteúdo relacionado no formato visual do Flipboard.

**Gap / Ausências:**
Sem foco governamental. Sem canal de denúncia de fake news ou educação sobre verificação de fontes.

**Insight para o DestaquesGovBr:**
💡 Smart Magazines para o governo: um canal por ministério e por tema IPTC — Saúde, Editais, Educação. O cidadão assina os canais que quer, sem navegar por 160 sites.

**Referências:**
- Flipboard Press, 2017 (Smart Magazines)
- Flipboard Blog, 2014 (30.000+ tópicos, 10M+ magazines)

#### **SmartNews**

**Avaliação:**
- Arquitetura da Informação: 4/5
- Busca e Filtragem: 3/5
- Personalização: 4/5
- Clipping: 3/5
- Clareza de Conteúdo: 5/5
- Comunicação e Engajamento: 4/5
- **Média: 3,8/5**

**O que faz de melhor:**

**Personalized Discovery — anti-câmara-de-eco**
O algoritmo intencionalmente recomenda conteúdo fora da bolha usual do usuário. Perspectivas diversas por design, não por acidente.

**Offline reading por pré-download**
Artigos e imagens baixados antes de o usuário perder conexão. Fundamental para regiões com conectividade intermitente — como grande parte do Brasil.

**~400 publishers verificados nos EUA**
AP, Reuters, Bloomberg, USA Today. Publisher-friendly: primeiro clique vai para o publisher, que fica com 100% da receita de anúncios no SmartView.

**Gap / Ausências:**
Filtros de busca básicos. Boards ausentes. Combate a fake news via curadoria de fontes — opaco para o usuário, sem canal explícito de denúncia.

**Insight para o DestaquesGovBr:**
💡 Offline reading é acessibilidade no Brasil. O princípio anti-filter-bubble deve ser central: DestaquesGovBr deve mostrar perspectivas de múltiplos órgãos sobre o mesmo tema.

**Referências:**
- Nanalyze, ago. 2019 (Personalized Discovery)
- Marketing Dive, 2014 (~400 publishers EUA, SmartView modelo publisher-friendly)

## **3.4 Matriz Comparativa e Análise de Gaps**

### **3.4.1 Matriz Comparativa: 10 Players × 6 Dimensões**

| Player | Arq.Info | Busca | Pers. | Clipping | Clareza | Comunic. | Média |
|--------|----------|-------|-------|----------|---------|----------|-------|
| 🇬🇧 GOV.UK | 5 | 4 | 1 | 1 | 5 | 4 | **3,3** |
| 🇺🇸 USA.gov | 4 | 4 | 1 | 2 | 5 | 5 | **3,5** |
| 🇨🇦 Canada.ca | 5 | 4 | 2 | 1 | 5 | 4 | **3,5** |
| 🇧🇷 Gov.br | 4 | 3 | 1 | 3 | 4 | 3 | **3,0** |
| 🇵🇹 Portugal.gov.pt | 3 | 3 | 1 | 2 | 4 | 3 | **2,7** |
| Google News | 5 | 5 | 5 | 4 | 5 | 3 | **4,5** |
| Feedly | 5 | 5 | 5 | 5 | 5 | 4 | **4,8** |
| Apple News | 5 | 4 | 5 | 5 | 5 | 2 | **4,3** |
| Flipboard | 5 | 5 | 5 | 5 | 5 | 3 | **4,7** |
| SmartNews | 4 | 3 | 4 | 3 | 5 | 4 | **3,8** |

**Médias por grupo:**
- **Portais Governamentais**: 3,0/5,0
- **Agregadores de Notícias**: 4,4/5,0
- **Gap**: 1,4 pontos

### **3.4.2 O Gap Crítico — e a Oportunidade do DestaquesGovBr**

**Gaps uniformes em todos os portais governamentais analisados:**

1. **Sem clipping de notícias**
   - Nenhum portal gov permite salvar, organizar ou exportar notícias
   - Cidadãos dependem de screenshots e ferramentas externas para guardar informação oficial

2. **Sem personalização do feed**
   - Todos recebem o mesmo conteúdo
   - Quem acompanha saúde navega por notícias de transporte
   - Sobrecarga para uns, irrelevância para outros

3. **Sem combate estruturado a fake news**
   - Nenhum portal tem canal robusto de denúncia ou verificação
   - Nenhum educa sobre como identificar fontes governamentais oficiais

**Conclusão:**
Nenhum player combina: agregação centralizada + área logada + clipping + personalização ML + combate a fake news + padrão IPTC. **Esse é o espaço do DestaquesGovBr.**

## **3.5 Padrões Identificados**

### **3.5.1 Padrões Positivos — O que funciona e deve ser adotado**

#### **GOV.UK: Content Modelling Granular**
Conteúdo em blocos mínimos reutilizáveis. Um dado publicado serve web, app, voz e IA sem retrabalho. Base confiável para modelos de IA.

#### **USA.gov: Busca Facetada com Metadados**
Filtros progressivos por departamento, tipo, data e tema. Essencial para bases com 160+ fontes. Usuário refina sem sair da página.

#### **Apple News: Curadoria Híbrida**
Algoritmo + editores humanos. Evita filter bubble (só ML) e limitação de escala (só humano). Editores priorizam; IA personaliza.

#### **Feedly: Boards e Coleções Profissionais**
Organizar por projeto, anotar, exportar e compartilhar coleções. Transforma o portal em ferramenta de trabalho real.

#### **Flipboard: Smart Magazines por Interesse**
Um canal separado por tema, não um feed único confuso. Usuário swipa entre revistas que escolheu seguir. Reduz sobrecarga.

#### **SmartNews: Offline Reading Robusto**
Pré-download de conteúdo. No Brasil, com desigualdade de conectividade, isso é acessibilidade — não conforto ou feature extra.

### **3.5.2 Padrões Negativos — O que evitar e onde estão os gaps**

#### **Fake news flags simples não funcionam** (Todos os players)

Estudos cognitivos mostram que 'bandeiras de falso' são ignoradas por viés de confirmação e criam o efeito de verdade implícita em artigos não marcados.

**Solução:** transparência afirmativa — links para fontes primárias e ClaimReview, não rótulos binários.

**Evidência científica:**
- Dennis et al. / LSE Business Review (2019): Experimento com EEG (eletroencefalograma) mostrou que 80% dos usuários não conseguem distinguir notícias falsas de verdadeiras. O flag de fake news do Facebook não teve NENHUM efeito na crença dos usuários. O viés de confirmação dominou: as pessoas acreditaram nos títulos alinhados às suas crenças e ignoraram completamente os que conflitavam.

- Pennycook et al. / Management Science (2020) — 'The Implied Truth Effect': quando avisos de 'falso' são colocados em apenas alguns artigos, os artigos SEM aviso passam a ser percebidos como MAIS verdadeiros do que eram antes — como se a ausência do rótulo fosse um selo de aprovação implícito. Estudo com N = 5.271 participantes.

**Referências:**
- LSE Business Review, jun. 2019: blogs.lse.ac.uk/businessreview/2019/06/26/fake-news-source-ratings...
- Pennycook et al. (2020): doi.org/10.1287/mnsc.2019.3478

#### **Infraestrutura de autenticação subutilizada** (Gov.br / USA.gov / Portugal.gov.pt)

Conta gov.br, Login.gov e Autenticação.gov têm sistemas robustos com milhões de usuários — mas nenhum usa isso para curadoria de notícias. Infraestrutura pronta, oportunidade desperdiçada.

#### **Busca de notícias fraca vs. busca de serviços** (Gov.br / Portugal.gov.pt)

Portais governamentais investem em busca de serviços e ignoram busca de notícias. Filtrar por data, órgão ou tema é precário ou impossível — mesmo com 160+ fontes publicando diariamente.

#### **Personalização zero — todos recebem o mesmo conteúdo** (Todos os portais governamentais)

Nenhum portal permite seguir órgãos ou temas. Resultado: sobrecarga para quem acompanha muito e irrelevância para quem acompanha pouco. Engajamento estruturalmente baixo.

## **3.6 Temas Transversais**

### **3.6.1 Taxonomia IPTC e Schema.org: a Espinha Dorsal da Plataforma**

#### **IPTC MEDIA TOPICS**

**O que é:**
Vocabulário controlado com 1.100+ termos hierárquicos para classificar notícias. Padrão global — adotado por Reuters, AP e BBC.

**Por que adotar:**
Uma notícia do Min. Infraestrutura sobre meio ambiente usa os mesmos metadados de uma do Min. Meio Ambiente — a busca entende que é o mesmo assunto.

**Regra fundamental:**
Categorizar pelo ASSUNTO, jamais pelo ministério emissor. Reestruturações administrativas não podem quebrar a navegação.

**Referência:**
- iptc.org/standards/media-topics (1.100+ termos, compatível XML/JSON/NewsML-G2)

#### **SCHEMA.ORG + JSON-LD + CLAIMREVIEW**

**NewsArticle + GovernmentOrganization:**
Toda publicação recebe marcação via JSON-LD. Google reconhece o governo como fonte primária e oficial. Rich snippets nos resultados de busca.

**ClaimReview (combate fake news):**
Para cada desmentido publicado, o código inclui ClaimReview. Quando alguém googla o tema, a correção oficial aparece com destaque visual nos resultados — sem depender de denúncias manuais.

**Referências:**
- schema.org/NewsArticle
- Google Fact Check Tools / ClaimReview (newsinitiative.withgoogle.com)

### **3.6.2 IA, Sumarização e Combate à Desinformação**

#### **Sumarização com Governança (Key Takeaways)**

Portarias e decretos ganham resumo gerado por IA no topo da publicação — como já fazem WSJ e Yahoo News. Três salvaguardas obrigatórias:
1. Modelo confinado ao texto da publicação, sem acesso à internet
2. Editor humano revisa e aprova (human-in-the-loop)
3. Interface informa claramente que é um resumo assistido por IA

**Evidência real:**
Reportagem publicada pelo Nieman Journalism Lab (Harvard) em junho de 2025, documentando as experiências reais de três grandes redações com sumarização automática de artigos por IA:

- **Wall Street Journal**: usa key points gerados por IA para expandir o negócio de newswires, inclusive em coreano e japonês
- **Bloomberg**: adota sumarização com guardrails editoriais rigorosos
- **Yahoo News**: lançou 'Key Takeaways' em 2024. A lição principal da diretora: 'human-in-the-loop is critical — as taxas de erro são muito baixas, mas não são zero, e mesmo erros raros podem gerar correções custosas.'

Conclusão compartilhada pelas três redações: 'Resumos não substituem o jornalismo — eles não podem existir sem ele.'

**Referência:**
- Nieman Lab / Harvard, jun. 2025: niemanlab.org/2025/06/lets-get-to-the-point-three-newsrooms-on-generating-ai-summaries-for-news/

#### **Combate à Desinformação: Transparência Afirmativa**

Fake news flags simples são ineficazes — ignoradas por viés de confirmação e criam o "efeito de verdade implícita" em artigos não marcados.

**Solução:**
- Links para portarias/decretos em cada notícia
- ClaimReview em desmentidos
- FAQ educativo sobre como identificar fontes .gov.br
- Contexto e evidência no lugar de rótulos

#### **Personalização com Equidade Algorítmica**

Algoritmos de recomendação podem herdar vieses históricos — se otimizarem só engajamento, priorizarão sensacionalismo e excluirão populações vulneráveis de informações importantes. Fairness-aware algorithms garantem exposição equitativa, com auditoria contínua documentada e pública.

# **4 Resultados**

## **4.1 DestaquesGovBr — Avaliação nas 6 Dimensões**

O mesmo framework usado para avaliar os 10 players aplicado ao DestaquesGovBr. Não é um ranking — é uma régua para saber onde estamos e para onde ir.

| Dimensão | Nota | Detalhe |
|----------|------|---------|
| **1. Arquitetura da Informação** | **4,5/5** | Taxonomia IPTC com 3 níveis hierárquicos. Órgãos catalogados por ministério/autarquia. Schema.org NewsArticle + GovernmentOrganization. Hierarquia rasa, breadcrumbs consistentes. |
| **2. Busca e Filtragem** | **4,0/5** | Busca híbrida: keyword + semântica (embeddings). Filtros progressivos por órgão, tema IPTC e data. Artigos relacionados por similaridade semântica. |
| **3. Personalização de Feed** | **4,0/5** | Following explícito: usuário segue órgãos e temas IPTC de interesse. Feed personalizado com apenas conteúdo dos seguidos. Notificações push configuráveis por órgão e tema. |
| **4. Área do Usuário e Clipping** | **4,5/5** | Clippings automáticos com entrega em múltiplos canais (email, Telegram, webhook, RSS). Marketplace de clippings. Boards de organização multi-feed. Sync cross-device. |
| **5. Clareza de Conteúdo** | **4,5/5** | Plain language. Sumarização automática por IA. Metadados visíveis: órgão, data, tema, entidades. Link para fonte primária sempre presente em cada notícia. |
| **6. Comunicação e Engajamento** | **4,0/5** | ClaimReview (Schema.org): desmentidos indexados com destaque no Google. Links para portarias/decretos em cada notícia. FAQ educativo. Federação ActivityPub. |

**Média geral: 4,2/5**

## **4.2 Highlights — O que o DestaquesGovBr Faz de Melhor Hoje**

### **🚀 Único Portal Gov com Personalização e Clipping**

- Following explícito por órgão e tema IPTC, com autenticação via Google OAuth e Gov.br
- Feed personalizado exibe apenas o que o usuário escolheu acompanhar
- Clippings automáticos em múltiplos canais (email, Telegram, webhook, RSS)
- Marketplace de clippings: qualquer usuário pode seguir, curtir e clonar a curadoria de outros
- Boards para organização multi-feed por projeto ou pauta

**Diferencial:** Preenche o gap crítico: nenhum dos portais governamentais analisados (GOV.UK, USA.gov, Canada.ca, Gov.br, Portugal) tem personalização ou clipping.

### **👑 Líder em Combate à Desinformação**

- Transparência afirmativa em vez de fake news flags — estratégia embasada em estudos cognitivos
- Links para portarias e decretos originais em cada notícia
- ClaimReview (Schema.org): desmentidos indexados com destaque visual nos buscadores
- FAQ educativo: como verificar se uma URL é fonte oficial (.gov.br)
- Federação ActivityPub: distribuição em redes descentralizadas desde Abr 2026

**Diferencial:** Único player — governamental OU agregador — com estratégia estruturada contra fake news. Supera a média dos agregadores comerciais nesta dimensão.

### **🔍 Busca Híbrida com IPTC e Schema.org**

- Busca híbrida: keyword (BM25) combinada com semântica (embeddings) — encontra por significado, não só por palavra exata
- Taxonomia IPTC com 3 níveis hierárquicos — mesmo padrão usado por Reuters, AP e BBC
- Filtros progressivos por órgão, tema e data
- Artigos relacionados via similaridade semântica
- Schema.org NewsArticle: rich snippets no Google identificando o governo como fonte primária

**Diferencial:** Único portal governamental com busca semântica e taxonomia IPTC implementadas.

### **📡 Múltiplos Canais de Distribuição**

- Portal web moderno com arquitetura de componentes (Next.js, App Router)
- Feeds estruturados: RSS/Atom/JSON — globais e por clipping individual
- Federação ActivityPub: qualquer instância Mastodon ou Misskey pode seguir o portal
- Widgets embarcáveis em múltiplos layouts e tamanhos — outros portais gov.br exibem notícias sem scraping
- Push notifications PWA e bot Telegram com comandos interativos

**Diferencial:** Government as a Platform (GaaP) em prática: dados públicos distribuídos para qualquer canal que queira consumi-los.

### **🏗 Arquitetura Event-Driven e Sumarização por IA**

- Pipeline event-driven: processamento assíncrono e escalável por natureza
- Sumarização automática por IA (AWS Bedrock) — resumos de 2-3 frases para cada publicação
- Classificação temática automática com IPTC e extração de entidades (pessoas, locais, organizações)
- Escalabilidade automática com escala-to-zero: custo proporcional ao uso real
- Filas com dead letter queue e retry automático para garantir processamento

**Diferencial:** Infraestrutura desenhada para crescer: mesma arquitetura suporta 156 órgãos ou 1.600.

### **🔐 Autenticação Integrada ao Gov.br**

- Conta gov.br (OIDC): SSO unificado — o mesmo login de dezenas de serviços públicos
- Google OAuth 2.0 como alternativa simplificada
- Custo de aquisição zero: o usuário já tem Conta gov.br
- Primeira aplicação gov.br que estende a Conta para curadoria de notícias — não apenas serviços transacionais
- Base para expansão: histórico de leitura, preferências e clippings vinculados à identidade digital

**Diferencial:** USA.gov tem Login.gov mas nunca o usou para notícias. Portugal tem CMD mas mantém portais separados. DestaquesGovBr integrou desde o MVP.

## **4.3 Oportunidades de Evolução — Gaps e Roadmap**

### **🔴 Prioridade 1: Crítica**

#### **1. Human-in-the-Loop para Sumarização** (Dimensão 5: Clareza de Conteúdo)

**Gap:** Sumarização 100% automática — sem revisão editorial antes da publicação.

**Solução:** Adicionar revisão humana como WSJ e Yahoo News. Interface transparente: 'resumo assistido por IA, revisado por editor'. Reduz risco em portarias críticas.

**Referência:** Nieman Lab / Harvard, jun. 2025

### **🟢 Prioridade 2: Alta**

#### **2. Curadoria Híbrida (ML + Editores Humanos)** (Dimensão 3: Personalização de Feed)

**Gap:** Personalização baseada só em following explícito — sem ML de histórico nem editor priorizando destaques do dia.

**Solução:** Algoritmo recomenda por histórico + editores definem destaques. Evita filter bubble (só ML) e falta de escala (só humano). Inspiração: Apple News.

#### **3. Múltiplas Perspectivas de Órgãos** (Dimensão 2: Busca e Filtragem)

**Gap:** Notícias exibidas isoladamente — sem agrupamento de perspectivas de múltiplos órgãos sobre o mesmo evento.

**Solução:** MEC anuncia programa → exibe automaticamente: portaria original, dados orçamentários (Tesouro) e estatísticas regionais (IBGE). Inspiração: Google News.

#### **4. Integrações Zapier/Make e Export PDF/Planilha** (Dimensão 4: Área do Usuário e Clipping)

**Gap:** Clippings exportáveis apenas como RSS/JSON — sem export para PDF, Excel, Notion ou Slack.

**Solução:** Solicitação recorrente dos usuários. Inspiração: Feedly com 1.000+ integrações via Zapier. Transforma o portal em ferramenta de trabalho profissional.

#### **5. Canal de Denúncia Bidirecional de Fake News** (Dimensão 6: Comunicação e Engajamento)

**Gap:** Sem canal para cidadão reportar notícia suspeita. FAQ educativo é estático e sem interação.

**Solução:** Formulário de denúncia + chatbot educativo interativo. Crowdsourcing de vigilância: cidadãos identificam fake news em escala. Fortalece o diferencial competitivo único.

#### **6. API Pública Documentada para Desenvolvedores** (Dimensão 1: Arquitetura da Informação)

**Gap:** Widgets embarcáveis existem, mas sem API REST pública documentada. Desenvolvedores não criam integrações customizadas.

**Solução:** api.destaquesgov.br com OpenAPI/Swagger: /noticias, /temas IPTC, /orgaos. Princípio fundador do GaaP: dados públicos para quem quiser construir sobre eles.

### **🟡 Prioridade 3: Média**

#### **7. Content Modelling Granular (Inspiração GOV.UK)** (Dimensão 1: Arquitetura da Informação)

**Gap:** Conteúdo como páginas HTML completas — sem fragmentação em blocos mínimos reutilizáveis.

**Solução:** 'Estilo Lego' do GOV.UK: notícia como componentes atômicos (manchete, lead, galeria, portaria vinculada). Base factual para LLMs. Requisito para fase 2.

#### **8. AI Leo-Style Filtering (Priorização Upstream)** (Dimensão 2: Busca e Filtragem)

**Gap:** Usuário escaneia todos os resultados — sem filtragem inteligente antes da leitura.

**Solução:** Assistente de IA que prioriza artigos relevantes antes do usuário ler. Inspiração: Feedly Leo. Reduz sobrecarga informacional para jornalistas e servidores.

#### **9. Offline Reading Robusto (PWA com Pré-Download)** (Dimensão 4: Área do Usuário e Clipping)

**Gap:** PWA instalável, mas sem pré-download. Offline limitado ao cache do navegador.

**Solução:** Pré-download de artigos e imagens dos órgãos seguidos. Acessibilidade real no Brasil com conectividade intermitente. Inspiração: SmartNews.

#### **10. Dark Mode Funcional** (UX / Acessibilidade)

**Gap:** Interface apenas light mode — solicitação recorrente dos usuários.

**Solução:** Toggle manual + detecção automática (prefers-color-scheme). Design tokens do GovBr v4 se disponíveis. Contraste WCAG AA obrigatório. Reduz fadiga visual.

# **5 Conclusões e considerações finais**

Este benchmarking de UX, realizado na fase de Descoberta do modelo Double Diamond, identificou o espaço único que o DestaquesGovBr ocupa no ecossistema de difusão de notícias governamentais:

## **5.1 Principais Conclusões**

1. **Gap crítico nos portais governamentais**: Nenhum dos portais gov analisados (GOV.UK, USA.gov, Canada.ca, Gov.br, Portugal) oferece personalização de feed, clipping de notícias ou combate estruturado a fake news. A média de UX dos portais governamentais é 3,0/5, enquanto os agregadores comerciais atingem 4,4/5 — uma diferença de 1,4 pontos.

2. **DestaquesGovBr preenche esse gap**: Com média de 4,2/5, o produto já supera os portais governamentais de referência internacional e se aproxima dos agregadores comerciais, mantendo o diferencial único de ser focado exclusivamente em conteúdo oficial verificado.

3. **Infraestrutura de autenticação subutilizada**: A Conta gov.br representa a maior oportunidade estratégica — infraestrutura com dezenas de milhões de usuários e custo de aquisição zero. O DestaquesGovBr é a primeira aplicação gov.br que estende a Conta para curadoria de notícias, não apenas serviços transacionais.

4. **Transparência afirmativa funciona melhor que flags**: Estudos cognitivos comprovam que rótulos de "fake news" são ineficazes. A estratégia correta — implementada no DestaquesGovBr — é oferecer links para fontes primárias, ClaimReview em desmentidos e educação proativa.

5. **Content modelling é requisito para fase 2**: O GOV.UK demonstra que fragmentar conteúdo em blocos mínimos ('estilo Lego') é essencial para entregar experiências omnicanal e servir como base confiável (ground truth) para modelos de IA.

## **5.2 Próximos Passos**

Este relatório encerra a fase de **Descoberta** e prepara a entrada na fase de **Definir** do Double Diamond. Os próximos passos são:

1. **Personas e jornadas**: mapear perfis de usuários (jornalistas, servidores públicos, cidadãos, pesquisadores) e suas jornadas específicas no portal
2. **Requisitos funcionais**: traduzir os padrões positivos identificados em requisitos priorizados
3. **Wireframes e protótipos**: criar mockups no Figma incorporando os insights deste benchmarking
4. **Testes com usuários reais**: validar as decisões de design antes da implementação

## **5.3 Considerações Finais**

O DestaquesGovBr está posicionado para ser o primeiro portal governamental do mundo a combinar agregação centralizada, personalização algorítmica, clipping profissional e combate estruturado à desinformação — tudo isso construído sobre padrões internacionais (IPTC, Schema.org) e integrado à infraestrutura de identidade digital já existente.

A oportunidade está mapeada. O próximo passo é o design.

# **6 Referências Bibliográficas**

## **6.1 Fundamentação Teórica**

[1] **Decreto 9.756/2019 — Portal único gov.br**  
Agência Brasil, jul. 2019  
https://agenciabrasil.ebc.com.br/geral/noticia/2019-07/portal-unico-do-governo-ja-esta-disponivel-na-internet

[2] **Government as a Platform — Priority Factors**  
MDPI Sustainability, 2020  
https://mdpi.com/2071-1050/12/14/5615

[3] **Best News Aggregator Apps 2025: Complete Comparison Guide**  
NewzTiQ Blog, 2025  
https://newztiq.ai/blogs/blog?slug=best-news-aggregator-apps-2025

[4] **Five Best News Aggregators: Evidence-Based Efficiency Ranking**  
LifeTips / NewzTiQ, 2025  
https://lifetips.alibaba.com/tech-efficiency/five-best-news-aggregators

## **6.2 Metodologia**

[5] **The Double Diamond Design Process**  
Design Council UK, 2015  
https://designcouncil.org.uk/our-resources/framework-for-innovation/

[6] **Asia an emerging leader in digital government — E-Government Survey 2024**  
GovInsider / ONU, 2024  
https://govinsider.asia/intl-en/article/asia-an-emerging-leader-in-digital-government

## **6.3 Portais Governamentais — Grupo A**

[7] **How information architects are helping to build GOV.UK's future**  
Inside GOV.UK Blog (GDS), abr. 2025  
https://insidegovuk.blog.gov.uk/2025/04/10/how-information-architects-are-helping-to-build-gov-uks-future/

[8] **GOV.UK Design System**  
Government Digital Service, 2018–2026  
https://design-system.service.gov.uk

[9] **Less is more: improving the public's web search experience with filters**  
USAGov Blog, dez. 2023  
https://usa.gov/blog/2023/12/less-is-more-improving-the-publics-web-search-experience-with-filters

[10] **api.data.gov — APIs abertas do governo federal americano**  
U.S. General Services Administration, 2024  
https://api.data.gov

[11] **Guidance on Web Accessibility and the ADA**  
ADA.gov, 2024  
https://ada.gov/resources/web-guidance/

[12] **Design with users — Canada.ca**  
Canadian Digital Service / Government of Canada, 2025  
https://canada.ca/en/government/system/digital-government/design-with-users.html

[13] **Padrão Digital de Governo — Design System GovBr v4**  
Serpro / MGI, 2024  
https://next-ds.estaleiro.serpro.gov.br

[14] **Autenticação.gov — Chave Móvel Digital / ePortugal**  
Governo de Portugal, 2024  
https://autenticacao.gov.pt | https://eportugal.gov.pt/en/sobre

## **6.4 Agregadores de Notícias — Grupo B**

[15] **How Google News stories are selected**  
Google News Help, 2025  
https://support.google.com/googlenews/answer/9005749

[16] **Customize what you find on Google News**  
Google News Help, 2025  
https://support.google.com/googlenews/answer/9010862

[17] **Google allows users to filter news sources — Preferred Sources**  
Straight Arrow News, ago. 2025  
https://straightarrowsnews.com

[18] **Google Fact Check Tools**  
Google News Initiative, 2024  
https://newsinitiative.withgoogle.com/resources/trainings/google-fact-check-tools/

[19] **Feedly vs Readwise Reader 2026 — 12M+ usuários, AI Leo, Zapier**  
Readless.app, abr. 2026  
https://readless.app/blog/feedly-vs-readwise-reader-2026

[20] **Inside Apple News — curadoria híbrida, Audio Stories, iCloud sync**  
AppleInsider, mar. 2025  
https://appleinsider.com/inside/apple-news/tips/

[21] **Flipboard Releases World's First Smart Magazines**  
Flipboard Press, 2017  
https://about.flipboard.com/press/new-flipboard-first-smart_magazines/

[22] **The New Flipboard Gets Personal with Over 30,000 Topics**  
Flipboard Blog, 2014  
https://about.flipboard.com/inside-flipboard/the-new-flipboard-gets-personal-with-over-30000-topics-to-follow/

[23] **SmartNews: An AI News App for Personalized Discovery**  
Nanalyze, ago. 2019  
https://nanalyze.com/2019/08/smartnews-ai-news/

[24] **NBC News, AP seek SmartNews for aggregated content (~400 publishers)**  
Marketing Dive, 2014  
https://marketingdive.com/ex/mobilemarketer/cms/news/media/18904.html

## **6.5 Evidência sobre Fake News e Combate à Desinformação**

[25] **Fake news, source ratings and better user interface design**  
LSE Business Review, jun. 2019  
https://blogs.lse.ac.uk/businessreview/2019/06/26/fake-news-source-ratings-and-better-user-interface-design-help-us-see-deception/

[26] **It matters how platforms label manipulated media — 12 principles**  
Partnership on AI  
https://partnershiponai.org/it-matters-how-platforms-label-manipulated-media-here-are-12-principles-designers-should-follow/

## **6.6 Padrões Técnicos**

[27] **IPTC Media Topics — 1.100+ termos hierárquicos para notícias**  
International Press Telecommunications Council, 2024  
https://iptc.org/standards/media-topics/

[28] **NewsArticle Schema — marcação semântica para notícias**  
Schema.org  
https://schema.org/NewsArticle

[29] **ClaimReview / Google Fact Check Tools**  
Schema.org + Google News Initiative, 2024  
https://newsinitiative.withgoogle.com/resources/trainings/google-fact-check-tools/

## **6.7 IA e Sumarização**

[30] **Three newsrooms on generating AI summaries for news (WSJ, Yahoo News)**  
Nieman Lab, jun. 2025  
https://niemanlab.org/2025/06/lets-get-to-the-point-three-newsrooms-on-generating-ai-summaries-for-news/

## **6.8 Referências Complementares**

[31] **LifeSG app — 100+ serviços por eventos de vida do cidadão**  
GovTech Singapore, 2024  
https://life.gov.sg/app

# **Apêndice**

## **A.1 Terminologias e Abreviações**

### **Conceitos e Metodologias**

**AHP (Analytic Hierarchy Process)**  
Técnica de priorização por peso utilizada no estudo de Myeong (2020) para identificar fatores críticos na construção de plataformas governamentais.

**Double Diamond**  
Metodologia de design e inovação com quatro fases: Descobrir, Definir, Desenvolver e Entregar. Desenvolvida pelo Design Council UK e adotada globalmente.

**GaaP (Government as a Platform)**  
Conceito criado por Tim O'Reilly (2011) que propõe que governos se tornem plataformas abertas, disponibilizando dados e infraestrutura para que cidadãos, empresas e desenvolvedores construam serviços sobre eles.

**Human-in-the-Loop**  
Abordagem onde um ser humano (geralmente um editor) revisa e aprova conteúdo gerado automaticamente por IA antes da publicação.

**Plain Language**  
Prática editorial que prioriza linguagem clara, direta e acessível, evitando jargões técnicos desnecessários.

**Transparência Afirmativa**  
Estratégia de combate à desinformação que fornece links para fontes primárias e contexto factual, em vez de usar rótulos simples de "fake news".

### **Padrões e Tecnologias**

**API (Application Programming Interface)**  
Interface que permite que diferentes sistemas de software se comuniquem e troquem dados de forma padronizada.

**ClaimReview**  
Esquema do Schema.org específico para marcação de fact-checking. Quando implementado, faz correções oficiais aparecerem com destaque visual em buscadores.

**Content Modelling**  
Abordagem que fragmenta conteúdo em blocos mínimos reutilizáveis ("estilo Lego"), permitindo distribuição omnicanal sem retrabalho editorial.

**IPTC (International Press Telecommunications Council)**  
Consórcio internacional que desenvolve padrões para a indústria de notícias. O IPTC Media Topics é um vocabulário controlado com 1.100+ termos hierárquicos para classificar notícias.

**JSON-LD (JavaScript Object Notation for Linked Data)**  
Formato de dados usado para marcação semântica de páginas web, permitindo que buscadores entendam o conteúdo estruturado.

**NewsML-G2 (News Markup Language Generation 2)**  
Padrão IPTC para intercâmbio de conteúdo noticioso estruturado.

**OAuth (Open Authorization)**  
Protocolo padrão aberto de autorização, usado para autenticação segura de usuários sem compartilhar senhas.

**OIDC (OpenID Connect)**  
Camada de identidade sobre OAuth 2.0, usada pela Conta gov.br para autenticação unificada.

**RSS (Really Simple Syndication) / Atom**  
Formatos de feed web que permitem assinatura de atualizações de conteúdo.

**Schema.org**  
Vocabulário colaborativo mantido por Google, Microsoft, Yahoo e Yandex para marcação semântica de páginas web. NewsArticle e GovernmentOrganization são esquemas específicos usados no DestaquesGovBr.

**WCAG (Web Content Accessibility Guidelines)**  
Diretrizes internacionais para acessibilidade de conteúdo web. WCAG 2.1 AA é o padrão mandatório no GOV.UK e recomendado globalmente.

### **Algoritmos e Técnicas**

**BM25 (Best Matching 25)**  
Algoritmo de ranking usado em buscas por palavra-chave (keyword search).

**Embeddings**  
Representações vetoriais de texto que capturam significado semântico, permitindo busca por similaridade conceitual em vez de apenas palavras exatas.

**Fairness-Aware Algorithms**  
Algoritmos que garantem exposição equitativa de conteúdo, evitando vieses que possam excluir populações vulneráveis.

**ML (Machine Learning)**  
Aprendizado de máquina — técnicas que permitem sistemas aprenderem padrões a partir de dados sem programação explícita.

### **Organizações e Índices**

**EGDI (E-Government Development Index)**  
Índice da ONU que mede maturidade digital de 193 países em três pilares: serviços online, infraestrutura de telecomunicações e capital humano.

**GDS (Government Digital Service)**  
Órgão do governo britânico responsável pela transformação digital de serviços públicos, incluindo o GOV.UK.

**ONU / UNDESA (United Nations Department of Economic and Social Affairs)**  
Divisão de Administração Pública da ONU que publica o E-Government Survey bianualmente.

### **Componentes e Experiência**

**Breadcrumbs**  
Trilha de navegação que mostra a localização do usuário na hierarquia do site (ex: Home > Saúde > Campanhas).

**Boards**  
Coleções temáticas de notícias organizadas por projeto, pauta ou tema, permitindo curadoria cross-feed.

**Clipping**  
Processo de salvar, organizar e compartilhar notícias de interesse em coleções personalizadas.

**Faceted Search / Busca Facetada**  
Sistema de busca com múltiplos filtros progressivos (ex: por órgão, tipo, data, tema) que se refinam dinamicamente.

**Feed**  
Fluxo contínuo de conteúdo atualizado, podendo ser personalizado conforme preferências do usuário.

**Following**  
Mecanismo onde usuário escolhe explicitamente quais fontes (órgãos) ou temas deseja acompanhar.

**Full Coverage**  
Funcionalidade do Google News que agrupa múltiplas perspectivas de diferentes fontes sobre o mesmo evento.

**PWA (Progressive Web App)**  
Aplicação web que pode ser instalada como app nativo, oferecendo recursos offline e notificações push.

**Rich Snippets**  
Resultados de busca enriquecidos com informações estruturadas (imagem, data, autor) que aparecem diretamente no Google.

**Smart Magazines**  
Conceito do Flipboard onde cada interesse vira uma "revista" separada com design editorial próprio.

**UX (User Experience)**  
Experiência do usuário — disciplina que estuda e projeta a interação entre pessoas e sistemas digitais.

### **Infraestrutura e Segurança**

**ActivityPub**  
Protocolo aberto de federação que permite interoperabilidade entre redes sociais descentralizadas (Mastodon, Misskey).

**CMD (Chave Móvel Digital)**  
Sistema de autenticação português via SMS ou app, válido para serviços públicos e privados.

**Conta gov.br**  
Sistema de autenticação unificada do governo brasileiro (SSO) com dezenas de milhões de usuários.

**Section 508**  
Lei americana que exige acessibilidade em tecnologias de informação do governo federal dos EUA.

**SSO (Single Sign-On)**  
Sistema de autenticação unificada que permite acesso a múltiplos serviços com um único login.

### **Outros Termos**

**EEG (Eletroencefalograma)**  
Técnica de medição de atividade elétrica cerebral, usada por Dennis et al. (2019) para estudar reações a fake news flags.

**FAQ (Frequently Asked Questions)**  
Perguntas frequentes — seção educativa com respostas a dúvidas comuns.

**Filter Bubble / Bolha de Filtro**  
Fenômeno onde algoritmos mostram apenas conteúdo alinhado às crenças prévias do usuário, isolando-o de perspectivas diversas.

**HTML (HyperText Markup Language)**  
Linguagem de marcação padrão para criação de páginas web.

**MVP (Minimum Viable Product)**  
Produto mínimo viável — versão inicial de um produto com funcionalidades essenciais para validação de mercado.

**Viés de Confirmação**  
Tendência cognitiva de buscar, interpretar e lembrar informações que confirmam crenças preexistentes, ignorando evidências contrárias.

**XML (eXtensible Markup Language)**  
Linguagem de marcação extensível usada para estruturação e transporte de dados.

---

*Espaço reservado para materiais complementares adicionais que o humano revisor julgar necessário incluir.*
