# Referência: site da Atenta Labs (padrão de qualidade para o Lastro)

**Card:** LST-55 · **Fonte:** repositório `fhscosme90/atenta-labs` (commit 3f46baf), servido localmente. O site no ar não abre pelo proxy desta sessão.
**Capturas:** `docs/ux/capturas/atenta/`. Os arquivos `home-*` e `sec-*` são da Atenta; os `lastro-hoje-*` são do nosso site atual.

O que copiamos é o **método**: a estrutura, o ritmo das seções, o SEO e a performance. **Marca, textos, fotos e ícones da Atenta não entram.** O Lastro continua com a paleta do `BRAND.md`, sem o verde-limão nem a coruja da Atenta.

## Como o site deles é montado

- **Stack mínima:**
  - Vite multipágina (`rollupOptions.input` com uma entrada por HTML).
  - HTML estático com o CSS crítico inline no `<head>`.
  - Um único `src/main.js` de 70 linhas.
  - Nenhum framework.
- **Fontes servidas pelo próprio site**, em `/fonts/*.woff2`, sem Google Fonts.
  - As duas fontes da dobra entram com `preload`; todas com `font-display: swap`.
  - As fontes usadas só abaixo da dobra carregam em `requestIdleCallback`.
- **Imagens em WebP:**
  - a foto do hero tem duas versões, desktop e mobile, carregadas com `preload` + `media` + `fetchpriority="high"`;
  - as demais têm `loading="lazy"`;
  - a pasta `img/` soma menos de 1 MB.
- **Tema por seção, não por página:** cada `<section>` recebe `dk` (escura) ou `lt` / `lt white` (clara), e os tokens `--bg`, `--text`, `--quiet` e `--line` mudam com essa classe. A página alterna as faixas: hero escuro, seções claras e preços escuros.
- **LGPD de verdade:**
  - O Google Tag Manager só carrega depois de "aceitar" no aviso de cookies (`public/rastreamento.js`, evento `atenta:consent`).
  - Os leads viram eventos no dataLayer (`*_lead` com `cta_local` e `lead_method`).
- **Conversão:**
  - o formulário monta o link `wa.me` com nome e área preenchidos;
  - há um botão flutuante de WhatsApp, que some enquanto o aviso de cookies está aberto.

## SEO (o que o Yoast pediria, já feito à mão)

| Item | Como eles fazem |
|---|---|
| Title | Palavra-chave na frente, marca no fim: "Marketing para advogados: tráfego, SEO e site \| Atenta Labs" |
| Meta description | Cerca de 150 caracteres, com benefício e chamada ("Agende uma conversa.") |
| Canonical, robots | `index, follow, max-image-preview:large`; páginas de exemplo com `Disallow` no robots.txt |
| Open Graph / Twitter | og:image 1200×630 com `?v=` para furar o cache, `og:image:alt`, `summary_large_image` |
| JSON-LD | Home: `ProfessionalService` + `WebSite` + `FAQPage`. Artigo: `BlogPosting` + `BreadcrumbList` |
| Sitemap | `lastmod` por URL, prioridade por tipo e `image:image` para as imagens dos artigos |
| FAQ | `<details>` nativo (6 perguntas), espelhado no `FAQPage` |
| Blog | `/blog/<slug>/index.html` (URL limpa), categorias, busca por `busca.json`, `feed.xml` RSS, link "pular para o conteúdo" |
| Acessibilidade | `:focus-visible` em tudo, `prefers-reduced-motion`, nenhum alt vazio em imagem de conteúdo |

## Linguagem visual

- **Tipografia:** Space Grotesk 700 nos títulos (`clamp(2rem, 4.6vw, 3.25rem)`, `letter-spacing -.02em`), Inter 400 no texto (18px / 1,7) e JetBrains Mono nos rótulos em caixa alta com espaçamento largo.
- **Numeração das seções:** `[ 01 ] POR QUE O CLIENTE NÃO CHEGA.` em mono. O Lastro já usa esse rótulo de olho; falta a numeração.
- **Título em dois tons:** a afirmação vem em `--text` e o complemento em `--quiet` ("O cliente certo está procurando. *Só não está te achando.*").
- **Grade de células com linha de 1px:**
  - `.grid { gap:1px; background: var(--line) }` desenha divisórias finas sem bordas duplicadas;
  - raio de 16px.
- **Respiro:**
  - seções com `padding: 104px 0`;
  - conteúdo com no máximo 1240px e 28px de gutter;
  - texto corrido com no máximo 640px.
- **Um único CTA forte por tela,** em minúsculas ("agendar conversa"), com 52px de altura. A frase de garantia fica logo abaixo ("Conversa sem compromisso…").
- **Ordem das seções:**
  1. dor;
  2. o que fazemos (4 frentes);
  3. exemplos (cartões com moldura de navegador);
  4. diferencial;
  5. três passos;
  6. preços (escuro);
  7. prova / quem somos;
  8. dúvidas;
  9. contato (escuro).

## Lastro hoje × padrão Atenta

| Ponto | Lastro hoje | Ajuste |
|---|---|---|
| 375px | **Rolagem horizontal**: o `form.envio` fica com 392px de largura (`lastro-hoje-375-*.png`) | Corrigir primeiro (`min-width:0` e `max-width:100%` no formulário e no `input[type=file]`) |
| Fontes | Externas | Servir `woff2` do próprio site, com `preload` das duas fontes da dobra |
| Ritmo | Tudo no fundo `--chao` claro | Alternar faixas `dk`/`lt` com a tinta `#111820` como fundo escuro; o ouro `#B58324` faz o papel do verde deles |
| Seções | Sem numeração; o upload aparece cedo demais | `[ 01 ]…[ NN ]`; a ordem dor → o que faz → demonstração → conferência → três passos → preços → dúvidas → contato |
| Hero | A prévia da tabela é forte (manter) | Título em dois tons; um CTA principal e a frase de garantia embaixo |
| Upload de planilha | Input nativo "Choose File" em inglês | Área de soltar o arquivo com rótulo em PT |
| SEO | Ver `docs/ux/seo-site-yoast.md` (auditoria em andamento) | `FAQPage`, `SoftwareApplication`/`ProfessionalService`, sitemap com `lastmod`, OG 1200×630 |
| Conteúdo | Sem blog | Blog estático `/blog/<slug>/` com artigos sobre conferência de números, Power BI e planilhas (é o que traz busca orgânica) |
| Cookies | Sem aviso | Rastreamento só depois do consentimento, como no `rastreamento.js` deles |

## E na plataforma (portal e dashboards)

A "pegada" vale para o portal com as mesmas peças:

- os tokens claro e escuro por região (barra lateral escura, área de trabalho clara);
- o rótulo mono numerado nas etapas da demanda (`[ 01 ] fonte · [ 02 ] grill · [ 03 ] rodar · [ 04 ] revisar`);
- a grade de células de 1px nos cartões de KPI;
- um CTA principal por tela;
- `:focus-visible` e `prefers-reduced-motion`.

Os dashboards (Power BI, Looker e Streamlit) seguem o mesmo tema: fundo `--chao`, cartões com borda de 1px e ouro só no destaque.
