# SEO e legibilidade do site no padrão Yoast (LST-55)

Página: `site/index.html`, no ar em https://lastro-api-73zx.onrender.com/site/ .
Quem aplica: engenheiro de frontend. Este documento não muda o HTML; traz a auditoria e o texto pronto.

Regras usadas na copy:

1. A página responde as perguntas do empresário nesta ordem: o número está certo? quanto me custa? meus dados estão seguros? funciona com o que já uso? quanto tempo até a primeira resposta?
2. Cada afirmação tem prova no produto. A fonte de cada uma está na seção 6.
3. Frases curtas, sem jargão de IA ("agentes" saiu do texto público), sem promessa de acerto.

Limite desta auditoria: as contagens foram feitas à mão, lendo o HTML. O Flesch e a voz passiva são estimativas. Antes de fechar o card, confira no analisador do Yoast (ou no `yoastseo` em Node) colando o texto final.

---

## 1. Frase-chave

**Principal: `dashboard para empresas`**

Por que essa:

- **Intenção comercial.** Quem busca "dashboard para empresas" quer contratar ou comprar, não aprender. "dashboard power bi" tem mais volume, mas a primeira página é de tutoriais e cursos (intenção de aprender).
- **Palavra do cliente.** O empresário brasileiro fala "dashboard" bem mais do que "painel de dados". "painel" continua no resto do texto, que é a voz da marca.
- **Cabe nos dois destinos do produto.** O painel abre no Power BI ou no Looker Studio. Uma frase só com "Power BI" deixaria o Looker de fora.
- **Volume plausível, não medido.** Não há ferramenta de volume neste ambiente. Confirmar no Planejador de Palavras-chave do Google Ads ou no Google Trends (Brasil, 12 meses) contra "painel de indicadores" e "dashboard power bi". Se "painel de indicadores" vier bem maior, troque a principal por ela: o texto já usa as duas.

**Sinônimos e relacionadas** (cadastrar no campo "sinônimos" do Yoast):

1. `painel de indicadores`
2. `painel de dados`
3. `dashboard Power BI`
4. `relatório gerencial`
5. `BI para PME` (relacionada; aparece só na meta keywords do JSON-LD, não force no texto)

Atenção ao Yoast gratuito: ele casa a forma exata das palavras. "dashboard da sua empresa" (singular) não conta. Nos pontos de SEO, o texto usa "empresas" no plural.

---

## 2. Auditoria do site atual

Legenda: **verde** passa, **laranja** melhorar, **vermelho** problema.

### 2.1 SEO

| Regra Yoast | Nota | Evidência no site atual |
|---|---|---|
| Frase-chave no título SEO (50–60 caracteres, no começo) | vermelho | `<title>Lastro</title>`: 6 caracteres, sem frase-chave. |
| Tamanho do título | vermelho | 6 caracteres; o Google completa com o que achar. |
| Frase-chave na meta description | vermelho | Ausente. |
| Tamanho da meta description (120–156) | laranja | 168 caracteres; corta no "apagados ao final". |
| Frase-chave no H1 | vermelho | H1: "O relatório chegou. Dá para confiar nele?" |
| Frase-chave no primeiro parágrafo | vermelho | O primeiro `<p>` é o rótulo "para quem decide com números"; o `lead` também não tem a frase. |
| Frase-chave em subtítulos H2/H3 (30–75%) | vermelho | 0 de 15 subtítulos (10 H2 + 5 H3). |
| Densidade (0,5–3%) | vermelho | 0 ocorrências em cerca de 800 palavras. |
| Slug | não se aplica | É a página inicial; hoje mora em `/site/`. Quando houver domínio próprio, a home vai para a raiz e a regra deixa de valer. |
| Alt das imagens | laranja | 4 imagens, todas com alt descritivo e bom, mas nenhum com a frase ou um sinônimo. |
| Links internos | vermelho | Só âncoras da própria página (`#teste`, `#certo`…); o Yoast não conta âncora como link interno. |
| Links externos | verde | `wa.me` (WhatsApp) com `rel="noopener"`, sem `nofollow`. |
| Tamanho do texto (≥ 300 palavras) | verde | Cerca de 800 palavras visíveis. |
| Título único | laranja | Página única, mas "Lastro" sozinho colide com qualquer outra página que use a palavra. |

**Nota do grupo: vermelho.**

### 2.2 Legibilidade

| Regra Yoast | Nota | Evidência no site atual |
|---|---|---|
| Frases com mais de 20 palavras (máx. 25%) | verde, no limite | Cerca de 11 de 55 frases (20%). As mais longas: auditor (29 palavras), ambiente simulado (26), "A conferência em duas camadas nasceu…" (25), "Na primeira vez…" (23), "Cada armadilha…" (23). |
| Parágrafos com mais de 150 palavras | verde | O maior tem cerca de 45 palavras. |
| Voz passiva (máx. 10%) | laranja | Cerca de 6 de 55 (11%): "é apagada", "a análise é entregue", "são lidas", "eram comparados", "é combinado", "apagada ao final". |
| Palavras de transição (mín. 30%) | vermelho | Cerca de 7 de 55 (13%): "Antes de", "Depois", "Só então", "Mesmo que", "No fim". |
| Frases seguidas começando igual | laranja | Na lista de sistemas, "pela documentação oficial" aparece 8 vezes em blocos seguidos. O Yoast pode ler os `<small>` como frases e acusar repetição. Sem pontuação, a lista também pode virar uma frase única de cerca de 45 palavras. |
| Distribuição de subtítulos (máx. 300 palavras sem subtítulo) | verde | O maior trecho sem subtítulo é a abertura, com cerca de 90 palavras. |
| Flesch adaptado ao português | laranja | Estimativa de cerca de 50 (Martins et al.: 248,835 − 1,015 × palavras/frase − 84,6 × sílabas/palavra, com cerca de 13 palavras por frase e 2,2 sílabas por palavra). Fica entre "difícil" e "razoável". |

**Nota do grupo: laranja.**

### 2.3 Técnico

| Item | Nota | Evidência no site atual |
|---|---|---|
| `lang="pt-BR"` | verde | `<html lang="pt-BR">`. |
| Favicon | laranja | Só o SVG (`marca/simbolo-cotejo-claro.svg`). Faltam PNG 32×32 e `apple-touch-icon` 180×180; Safari antigo e o Google na busca podem não mostrar. |
| Canonical | vermelho | Ausente. O mesmo conteúdo responde em `/site/` e `/site/index.html`. |
| Open Graph (`og:title`, `og:description`, `og:image` 1200×630, `og:url`, `og:type`, `og:locale`) | vermelho | Nenhum. Link colado no WhatsApp ou no LinkedIn sai sem imagem e sem título. Também não existe imagem 1200×630 no repositório. |
| Twitter card | vermelho | Ausente. |
| JSON-LD (Organization, SoftwareApplication, FAQPage) | vermelho | Nenhum. Também não há seção de perguntas na página. |
| Meta robots | laranja | Ausente. O padrão é indexar, mas falta `max-image-preview:large` para a imagem aparecer grande na busca. |
| `robots.txt` | vermelho | Não existe; `lastro/api.py` não tem rota `/robots.txt` na raiz do domínio. |
| `sitemap.xml` | vermelho | Não existe. |
| `<meta name="viewport">` e `charset` | verde | Presentes. |

**Nota do grupo: vermelho.**

---

## 3. Ordem das seções

As perguntas do empresário vêm nesta ordem. Mover uma `<section>` inteira não mexe em nada que o `demo.js` usa: ele só procura `#palco` e o que está dentro dele.

| # | Pergunta | Seção (id) | Hoje está em |
|---|---|---|---|
| — | abertura | `.abre` | 1ª |
| 1 | O número está certo? | `#certo` | 3ª |
| 2 | Quanto me custa? | `#custo` (id novo) + seção da equipe logo depois | 7ª e 6ª |
| 3 | Meus dados estão seguros? | `#seguranca` (id novo) | 4ª |
| 4 | Funciona com o que já uso? | `#sistemas` | 5ª |
| 5 | Quanto tempo até a primeira resposta? | `#teste` (demonstração) + seção "explicar de novo" | 2ª e 6ª |
| — | como começar | `#piloto` | igual |
| — | quem está por trás | sem id | igual |
| — | perguntas | `#perguntas` (seção nova) | — |
| — | contato | `#contato` | igual |

Os ids novos (`custo`, `seguranca`, `perguntas`) são acréscimos; nenhum id ou classe existente muda de nome.

Se o time preferir manter a demonstração logo depois da abertura, por causa da conversão, o texto funciona igual. Só a ordem das perguntas perde força.

---

## 4. Texto novo, pronto para colar

O que não aparece aqui fica como está. Os ids e as classes são os mesmos de hoje.

### 4.1 `<head>`

Substitui as linhas 5 a 7 atuais (`<title>`, favicon e description). O resto do `<head>` fica igual.

```html
<title>Dashboard para empresas com número conferido | Lastro</title>
<meta name="description" content="Dashboard para empresas a partir do ERP, CRM ou planilha. Cada número passa por auditoria e por um revisor do seu time. Demonstração grátis, sem cadastro.">
<link rel="canonical" href="https://lastro-api-73zx.onrender.com/site/">
<meta name="robots" content="index, follow, max-image-preview:large">

<link rel="icon" type="image/svg+xml" href="marca/simbolo-cotejo-claro.svg">
<link rel="icon" type="image/png" sizes="32x32" href="marca/favicon-32.png">
<link rel="apple-touch-icon" sizes="180x180" href="marca/apple-touch-icon.png">
<meta name="theme-color" content="#EEF1F3">

<meta property="og:type" content="website">
<meta property="og:locale" content="pt_BR">
<meta property="og:site_name" content="Lastro">
<meta property="og:url" content="https://lastro-api-73zx.onrender.com/site/">
<meta property="og:title" content="Dashboard para empresas com cada número conferido">
<meta property="og:description" content="Do ERP, do CRM ou da planilha para o Power BI ou o Looker Studio. Auditoria automática e revisão de alguém do seu time antes de o número chegar a você.">
<meta property="og:image" content="https://lastro-api-73zx.onrender.com/site/img/og-lastro.jpg">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta property="og:image:alt" content="Painel de dados do Lastro com o total vendido por vendedor, conferido pela auditoria. Dados fictícios da demonstração.">

<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="Dashboard para empresas com cada número conferido">
<meta name="twitter:description" content="Auditoria automática e revisão de alguém do seu time antes de o número chegar a você. Demonstração grátis, sem cadastro.">
<meta name="twitter:image" content="https://lastro-api-73zx.onrender.com/site/img/og-lastro.jpg">
```

Contagens:

- Título: 53 caracteres e começa pela frase-chave.
- Meta description: 154 caracteres, com a frase-chave no começo. Confira no preview do Yoast: o limite é 156.
- og:description: 152 caracteres.

Arquivos que precisam ser criados (o frontend gera; nada disso existe hoje):

- `site/img/og-lastro.jpg`, 1200×630. Recorte de `img/resposta.jpg` com o logotipo e a faixa "dados fictícios da demonstração". Sem número que não esteja na demonstração.
- `site/marca/favicon-32.png` e `site/marca/apple-touch-icon.png`, gerados de `marca/simbolo-cotejo-claro.svg`.

### 4.2 JSON-LD

Colar no fim do `<head>`. As respostas do FAQ precisam ser **idênticas** ao texto visível da seção 4.12. Se o texto mudar, o JSON muda junto.

```html
<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@graph": [
    {
      "@type": "Organization",
      "@id": "https://lastro-api-73zx.onrender.com/site/#org",
      "name": "lixum.labs",
      "url": "https://lixumlabs.com.br",
      "email": "lixumlabs@gmail.com",
      "contactPoint": {
        "@type": "ContactPoint",
        "telephone": "+55-61-99952-0802",
        "contactType": "sales",
        "availableLanguage": "pt-BR"
      }
    },
    {
      "@type": "WebSite",
      "@id": "https://lastro-api-73zx.onrender.com/site/#site",
      "url": "https://lastro-api-73zx.onrender.com/site/",
      "name": "Lastro",
      "inLanguage": "pt-BR",
      "publisher": { "@id": "https://lastro-api-73zx.onrender.com/site/#org" }
    },
    {
      "@type": "SoftwareApplication",
      "@id": "https://lastro-api-73zx.onrender.com/site/#lastro",
      "name": "Lastro",
      "url": "https://lastro-api-73zx.onrender.com/site/",
      "applicationCategory": "BusinessApplication",
      "operatingSystem": "Web",
      "inLanguage": "pt-BR",
      "description": "Dashboard para empresas a partir do ERP, do CRM ou da planilha, com auditoria automática e revisão de negócio humana antes da entrega. Abre no Power BI ou no Looker Studio.",
      "keywords": "dashboard para empresas, painel de indicadores, painel de dados, dashboard Power BI, BI para PME",
      "publisher": { "@id": "https://lastro-api-73zx.onrender.com/site/#org" }
    },
    {
      "@type": "FAQPage",
      "@id": "https://lastro-api-73zx.onrender.com/site/#perguntas",
      "mainEntity": [
        { "@type": "Question", "name": "Preciso comprar licença para ter o painel de dados?",
          "acceptedAnswer": { "@type": "Answer", "text": "Não para começar. O painel abre no Power BI que você já tem ou no Looker Studio, que é grátis. Além disso, o Lastro usa ferramentas gratuitas e a sua própria nuvem." } },
        { "@type": "Question", "name": "Quem define as regras de negócio?",
          "acceptedAnswer": { "@type": "Answer", "text": "Você. Antes de calcular, o Lastro pergunta qual valor somar e qual data vale. Também pergunta o que conta como repetido, qual recorte usar e quem revisa. Cada pergunta vem com uma sugestão, mas a escolha é sua." } },
        { "@type": "Question", "name": "O que acontece com a planilha da demonstração?",
          "acceptedAnswer": { "@type": "Answer", "text": "Ela fica numa área temporária, só durante a análise. No fim, apagamos tudo e mostramos o recibo, com arquivos, tabelas e tamanho. Se você sair no meio, a varredura apaga o que sobrou em até 15 minutos." } },
        { "@type": "Question", "name": "Posso subir uma planilha com CPF ou telefone de clientes?",
          "acceptedAnswer": { "@type": "Answer", "text": "Melhor não: a demonstração pede que você não envie dados pessoais. Mesmo assim, se o Lastro achar uma coluna desse tipo, ele avisa e deixa a coluna fora do painel." } },
        { "@type": "Question", "name": "A demonstração tem a revisão humana?",
          "acceptedAnswer": { "@type": "Answer", "text": "Não. Ela mostra só a conferência automática, e o painel vem marcado assim. A revisão de negócio, por alguém do seu time, entra no piloto." } },
        { "@type": "Question", "name": "Qual planilha eu posso usar?",
          "acceptedAnswer": { "@type": "Answer", "text": "CSV ou Excel, até 5 MB e 50 mil linhas. A primeira linha precisa ter o nome das colunas. Se não tiver uma à mão, use a planilha de exemplo, com orçamentos de uma construtora fictícia." } }
      ]
    }
  ]
}
</script>
```

Notas sobre o JSON-LD:

- **Sem `offers` e sem `aggregateRating`.** O Lastro não tem preço público nem avaliações, e nada disso será inventado. Sem esses campos, o Google não mostra o resultado rico de "software". O schema continua válido e ajuda a identificar a entidade.
- **FAQPage.** Desde 2023, o Google só mostra o FAQ expandido para sites de governo e saúde. A marcação vale para outros buscadores e respostas de IA; o ganho no Google é pequeno.
- **Organization = lixum.labs.** O `BRAND.md` diz "um produto lixum.labs (a confirmar no grill)". Se a titularidade mudar, troque o nó Organization.

### 4.3 Navegação (`header.topo nav`)

Mesma ordem das perguntas. Os links usam ids existentes ou os novos da seção 3.

```html
<nav aria-label="Seções">
  <a href="#certo">o número está certo?</a>
  <a href="#custo">quanto custa</a>
  <a href="#sistemas">meus sistemas</a>
  <a href="#teste">testar agora</a>
  <a class="cta" href="#contato">falar com a gente</a>
</nav>
```

"como começar" saiu do menu para caber em 375 px. Se couber, volte com ele antes do CTA.

### 4.4 Abertura (`.abre`)

Troque `<p class="rot">` por `<span class="rot">` (a classe não muda). Assim, o rótulo não conta como "primeiro parágrafo" e o `lead` passa a ser a introdução que o Yoast lê. Se o espaçamento mudar, `display:block` no span resolve.

```html
<span class="rot">para quem decide com números</span>
<h1>Dashboard para empresas, com cada número conferido duas vezes</h1>
<p class="lead">O relatório chegou. Mas dá para confiar nele? O Lastro monta o dashboard para empresas que têm os dados no ERP, no CRM ou em planilha. Antes de chegar a você, cada número passa por duas conferências. Primeiro, uma auditoria automática. Depois, a revisão de alguém que conhece o seu negócio.</p>
<div class="acoes"><a class="cta ouro" href="#teste">testar com os meus dados</a><a class="cta leve" href="#certo">ver como a conferência funciona</a></div>
```

Imagem e legenda:

```html
<img src="img/resposta.jpg" alt="Painel de dados do Lastro com o total vendido por vendedor nos contratos fechados: Eva Martins lidera com R$ 2.567.582,13; total de R$ 14.030.477,92. Dados fictícios." width="1574" height="560">
<figcaption class="nota"><span>Antes de somar, o Lastro achou <b>12 contratos lançados duas vezes</b>. Sem essa limpeza, o total sairia <b>R$ 181.820,60 maior</b>. Dados fictícios da demonstração.</span></figcaption>
```

A legenda fica como está: é a melhor prova da página.

### 4.5 Pergunta 1: `#certo`

```html
<div class="pergunta"><span class="rot">a primeira pergunta de toda segunda-feira</span><h2>“Esse número está certo?”</h2></div>
<div class="resposta">
  <p>Antes de qualquer número sair, um auditor automático refaz a conta do zero. Ele procura registros repetidos e datas no futuro. Também confere se a soma bate em cada etapa.</p>
  <p>Depois, alguém do seu time abre a mesma conta no Google Colab e aprova. Só então a análise chega a você.</p>
  <p class="quieto">Por isso, o Lastro não deduz regra de negócio. Ele pergunta a você antes de calcular.</p>
  <div class="janela"><div class="barra" aria-hidden="true"><i></i><i></i><i></i><span>auditoria técnica</span></div><img src="img/auditoria.jpg" alt="Auditoria técnica do Lastro antes de o painel sair: linhas entre etapas, chaves repetidas, integridade, soma conferida e datas no futuro." width="1574" height="900" loading="lazy"></div>
</div>
```

### 4.6 Pergunta 2: `#custo` (era a seção "o investimento")

Ponha `id="custo"` na `<section>`.

```html
<div class="pergunta"><span class="rot">o investimento</span><h2>“Quanto custa um dashboard para empresas como a minha?”</h2></div>
<div class="resposta">
  <p>Para começar, você não paga licença nova. O Lastro usa ferramentas gratuitas e o que já é seu. Por exemplo, a sua nuvem, as suas planilhas e o seu Power BI.</p>
  <p>Além disso, o dashboard para empresas também pode abrir no Looker Studio, que é grátis.</p>
  <p class="quieto">O piloto tem escopo e valor por escrito, combinados com você antes de qualquer trabalho.</p>
</div>
```

### 4.7 Pergunta 2, continuação: a equipe

```html
<div class="pergunta"><span class="rot">a equipe</span><h2>“Preciso contratar um analista para ter um painel de indicadores?”</h2></div>
<div class="resposta">
  <p>Não para o trabalho pesado. Buscar, limpar, modelar, calcular e conferir fica com o Lastro.</p>
  <p>Mas a decisão continua com gente. Quem aprova cada entrega é alguém do seu negócio, que sabe quando um número não faz sentido.</p>
</div>
```

### 4.8 Pergunta 3: `#seguranca` (era "Vão mexer no meu sistema?")

Ponha `id="seguranca"` na `<section>`.

```html
<div class="pergunta"><span class="rot">a preocupação com a operação</span><h2>“Meus dados estão seguros? Vão mexer no meu sistema?”</h2></div>
<div class="resposta">
  <p>Não mexemos no seu sistema: o Lastro só lê. Essa trava fica na própria credencial de acesso. Então ela não depende de alguém lembrar de tomar cuidado.</p>
  <p>Além disso, se alguma etapa tentar gravar na sua fonte, o Lastro recusa e registra a tentativa. Cada empresa entra com login próprio e enxerga só os próprios dados.</p>
  <p class="quieto">Tudo o que o Lastro consulta, decide e entrega fica registrado com data e autor. Assim, daqui a seis meses, você sabe de onde veio cada número.</p>
</div>
```

### 4.9 Pergunta 4: `#sistemas`

```html
<div class="pergunta"><span class="rot">sem trocar de sistema</span><h2>“Funciona com o que eu já uso?”</h2></div>
<div class="resposta">
  <p>Estes sistemas já estão mapeados. Sabemos como cada um entrega os dados, quanto aguenta de consulta e onde costuma esconder erro.</p>
  <!-- .sistemas: lista igual à atual, sem mudança -->
  <p>Planilhas Excel e CSV entram direto. Já as do Google Planilhas, o Lastro lê na pasta do Drive que você indicar. No fim, o painel abre no seu Power BI ou no Looker Studio.</p>
  <p class="quieto">Antes de tocar no seu sistema, testamos a conexão num ambiente simulado. Ele tem os mesmos limites e os mesmos erros do real.</p>
  <div class="janela"><div class="barra" aria-hidden="true"><i></i><i></i><i></i><span>teste de conexão · Sienge · ambiente simulado</span></div><img src="img/conector.jpg" alt="Laudo do teste de conexão com o Sienge em ambiente simulado: 180 registros, total conferido, 1 requisição." width="1574" height="700" loading="lazy"></div>
</div>
```

Lista `.sistemas`: os rótulos ficam iguais ("testado em operação real", "pela documentação oficial", "a confirmar no piloto"). Para o Yoast não ler a lista como uma frase gigante nem acusar 8 começos iguais, envolva a lista com `data-nosnippet` e, se o analisador ainda reclamar, transforme a lista em `<ul>`/`<li>` com as mesmas classes `.sis`. É escolha de markup do frontend; o texto não muda.

### 4.10 Pergunta 5: `#teste` (demonstração)

Só a coluna `.pergunta` e os textos estáticos de dentro do `#palco` mudam. **Os ids `palco`, `t-envio`, `t-arquivo`, `t-exemplo`, `t-aceite`, `t-analisar` e `t-erro`, as classes `envio`, `aceite`, `linkbtn`, `miuda` e `alerta`, e o texto do botão `analisar planilha` ficam exatamente como estão.** O `demo.js` repõe "analisar planilha" depois de um erro, e o texto precisa bater.

```html
<div class="pergunta">
  <span class="rot">teste com a sua planilha</span>
  <h2>“Quanto tempo até o primeiro painel de dados?”</h2>
  <p>Dá para ver agora. Suba uma planilha, responda até quatro perguntas e receba o painel com a conferência automática. A análise tem limite de 60 segundos. Se passar disso, o Lastro cancela e apaga tudo.</p>
  <p class="nota"><span><b>Nada fica com a gente.</b> A análise roda numa área temporária. No fim, apagamos tudo e mostramos o recibo.</span></p>
  <p class="nota"><span><b>CSV ou Excel</b>, até 5 MB e 50 mil linhas. Sem cadastro.</span></p>
</div>
```

Dentro do `#palco`, só muda o texto do aceite (o resto fica igual):

```html
<label class="aceite"><input type="checkbox" id="t-aceite"> <span>Não vou enviar dados pessoais (CPF, e-mail, telefone). Entendo que é uma demonstração: tem só a conferência automática, sem revisão humana, e o Lastro apaga tudo no fim.</span></label>
```

### 4.11 Pergunta 5, continuação: "explicar de novo"

```html
<div class="pergunta"><span class="rot">o tempo do seu time</span><h2>“Vou ter que explicar tudo de novo toda vez?”</h2></div>
<div class="resposta">
  <p>Só o que muda. Na primeira vez, o Lastro pergunta o que não pode adivinhar. Por exemplo, qual valor somar, qual data vale e o que conta como registro repetido. Cada pergunta já vem com uma sugestão.</p>
  <p>Depois, o que vale para a fonte fica guardado, como a data e a chave. Já a medida e o recorte, o Lastro confirma a cada pergunta nova. Na demonstração, a segunda análise sobre os mesmos dados precisou de 2 respostas, não de 5.</p>
  <div class="janela"><div class="barra" aria-hidden="true"><i></i><i></i><i></i><span>perguntas antes de calcular</span></div><img src="img/grill.jpg" alt="Perguntas do Lastro antes de calcular o painel de indicadores: medida, data, chave de registro, recorte e revisor, cada uma com sugestão." width="1574" height="1100" loading="lazy"></div>
</div>
```

### 4.12 `#piloto`

```html
<div class="pergunta"><span class="rot">o piloto</span><h2>Como começar: um painel de indicadores em quatro passos</h2></div>
<div class="resposta"><p>Uma pergunta real da sua empresa, de ponta a ponta, com as duas conferências.</p></div>
```

```html
<li><h3>A pergunta</h3><p>Primeiro, conversamos sobre o número que mais pesa nas suas decisões hoje.</p></li>
<li><h3>A conexão</h3><p>Em seguida, ligamos uma fonte em modo só leitura. Ou você manda uma planilha.</p></li>
<li><h3>As respostas</h3><p>Então você define as regras que o Lastro não deve adivinhar.</p></li>
<li><h3>O painel conferido</h3><p>Por fim, você recebe a análise, a auditoria técnica e a planilha de conferência para o seu time aprovar.</p></li>
```

### 4.13 Quem está por trás

"data lakes" e "pipelines" saem: são jargão para o empresário.

```html
<div class="pergunta"><span class="rot">quem está por trás</span><h2>Feito por quem já errou o número antes</h2></div>
<div class="resposta">
  <p>Montamos bases de dados e painéis de Power BI desde 2019, para indústria e construção civil. A conferência em duas camadas nasceu num projeto real. Nele, comparamos o painel e a planilha de conferência indicador por indicador, até baterem.</p>
  <p class="quieto">Cada armadilha que custou horas em produção virou uma checagem automática no Lastro. Por exemplo, um sistema que responde “deu certo” e esconde um erro.</p>
</div>
```

"desde 2019" já está no site atual. Mantenha só se o Tiago confirmar a data: não há prova disso dentro do produto.

### 4.14 Seção nova: `#perguntas` (FAQ)

Entra entre "quem está por trás" e `#contato`. Usa as classes que já existem. Sugestão de CSS para o frontend: `.resposta h3 { font-size: 20px; font-weight: 600 }`.

```html
<section id="perguntas">
  <div class="qa">
    <div class="pergunta"><span class="rot">antes de conversar</span><h2>Outras perguntas sobre o dashboard para empresas</h2></div>
    <div class="resposta">
      <h3>Preciso comprar licença para ter o painel de dados?</h3>
      <p>Não para começar. O painel abre no Power BI que você já tem ou no Looker Studio, que é grátis. Além disso, o Lastro usa ferramentas gratuitas e a sua própria nuvem.</p>

      <h3>Quem define as regras de negócio?</h3>
      <p>Você. Antes de calcular, o Lastro pergunta qual valor somar e qual data vale. Também pergunta o que conta como repetido, qual recorte usar e quem revisa. Cada pergunta vem com uma sugestão, mas a escolha é sua.</p>

      <h3>O que acontece com a planilha da demonstração?</h3>
      <p>Ela fica numa área temporária, só durante a análise. No fim, apagamos tudo e mostramos o recibo, com arquivos, tabelas e tamanho. Se você sair no meio, a varredura apaga o que sobrou em até 15 minutos.</p>

      <h3>Posso subir uma planilha com CPF ou telefone de clientes?</h3>
      <p>Melhor não: a demonstração pede que você não envie dados pessoais. Mesmo assim, se o Lastro achar uma coluna desse tipo, ele avisa e deixa a coluna fora do painel.</p>

      <h3>A demonstração tem a revisão humana?</h3>
      <p>Não. Ela mostra só a conferência automática, e o painel vem marcado assim. A revisão de negócio, por alguém do seu time, entra no piloto.</p>

      <h3>Qual planilha eu posso usar?</h3>
      <p>CSV ou Excel, até 5 MB e 50 mil linhas. A primeira linha precisa ter o nome das colunas. Se não tiver uma à mão, use a planilha de exemplo, com orçamentos de uma construtora fictícia.</p>
    </div>
  </div>
</section>
```

### 4.15 `#contato`

O título fica. Só o parágrafo muda.

```html
<h2 style="font-size:clamp(30px,4vw,44px);line-height:1.06;margin:12px 0 16px">Traga a pergunta que tira o seu sono</h2>
<p style="color:var(--quieta);max-width:52ch">Mande a pergunta já no primeiro contato. Assim, a conversa começa pelo número que mais importa.</p>
```

Os CTAs ficam iguais: "falar no WhatsApp", "copiar e-mail" (o script repõe esse texto e ele precisa bater) e a mensagem pronta do `wa.me`.

### 4.16 Rodapé e link interno

O texto atual fica. Para o Yoast contar um link interno, acrescente um link para o portal (o caminho já existe: `/web/`):

```html
<footer><span>lastro · um produto lixum.labs</span><span>Telas e números desta página vêm da demonstração, com dados fictícios.</span><a href="/web/">entrar no portal</a></footer>
```

Só aplique se o portal puder ser mostrado ao público. Se não puder, a regra de links internos fica laranja até existir uma segunda página do site.

---

## 5. Técnico fora do HTML

### 5.1 `robots.txt`

O arquivo precisa estar na raiz do domínio, `https://lastro-api-73zx.onrender.com/robots.txt`, e não em `/site/`. Hoje a raiz é a API. Precisa de uma rota em `lastro/api.py` (`PlainTextResponse`), fora do `NAO_MEDIR` se quiserem medir, ou dentro, se não quiserem:

```
User-agent: *
Allow: /site/
Disallow: /api/
Disallow: /web/
Disallow: /sandbox/

Sitemap: https://lastro-api-73zx.onrender.com/sitemap.xml
```

### 5.2 `sitemap.xml`

Também na raiz, pela mesma via:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <url>
    <loc>https://lastro-api-73zx.onrender.com/site/</loc>
    <lastmod>AAAA-MM-DD</lastmod>
  </url>
</urlset>
```

`lastmod` = data da publicação do texto novo.

### 5.3 Quando vier o domínio próprio

Troque a URL em seis lugares: `canonical`, `og:url`, `og:image`, `twitter:image`, os `@id`/`url` do JSON-LD e o `sitemap.xml`. Depois, faça um 301 de `/site/` para o domínio novo.

---

## 6. Prova de cada afirmação

| Afirmação no texto novo | Prova no produto |
|---|---|
| 12 contratos duplicados; total R$ 181.820,60 maior | Demonstração (legenda atual, `img/resposta.jpg`) |
| Auditor procura repetidos, datas no futuro, soma entre etapas | `img/auditoria.jpg` (checagens listadas no alt) |
| Revisão humana no Google Colab antes da entrega | Camada 2 em `CONTEXT.md`; regra 2 do `AGENTS.md` |
| O Lastro não deduz regra; pergunta antes de calcular, com sugestão | Grill (`CONTEXT.md`), `img/grill.jpg` |
| Sem licença nova; ferramentas gratuitas; Looker Studio grátis | Regra 5 do `AGENTS.md`; `caixa/global/playbooks/google-bigquery-looker.md` |
| Abre no Power BI ou no Looker Studio | Trilhas em `caixa/global/trilhas/`; BI por HTTPS em `lastro/api.py` (LST-47) |
| Só leitura na credencial | `lastro/somente_leitura.py` (docstring: conector abre em modo leitura) |
| Recusa e registra tentativa de escrita | `EscritaBloqueada`; `tentativas_escrita_bloqueadas` no laudo de conector (`lastro/saas/servico.py`) |
| Login próprio; cada empresa só vê os próprios dados | Regra 6 do `AGENTS.md` (tenant em tudo) |
| Registro com data e autor | Texto atual do site, mantido |
| Sistemas testados ou pela documentação | Lista atual; `lastro/saas/catalogo.yaml` |
| Ambiente simulado com os mesmos limites e erros | `lastro/saas/simulador.py`; `img/conector.jpg` |
| Até quatro perguntas na demonstração | `perguntas_visitante` em `lastro/demo.py` ("Até 4 perguntas") |
| Limite de 60 segundos e cancelamento | `PRAZO_S = 60` e erro `Demorou` em `lastro/demo.py` |
| Apaga em até 15 minutos se a pessoa sair no meio | `TTL_S = 15 * 60` em `lastro/demo.py`; `pagehide` em `site/demo.js` |
| Recibo com arquivos, tabelas e tamanho | `reciboHtml` em `site/demo.js` |
| CSV ou Excel, 5 MB, 50 mil linhas | `MAX_BYTES` e `MAX_LINHAS` em `lastro/demo.py` |
| Coluna de dado pessoal fica fora do painel | `pessoais()` e `excluir=` em `lastro/demo.py`; rótulo "dado pessoal, fora do painel" no `demo.js` |
| Demonstração sem revisão humana, marcada no painel | Selo "sem revisão humana" em `site/demo.js` |
| Fonte guarda data e chave; medida e recorte são confirmados de novo | Termo "Decisão" em `CONTEXT.md` |
| 2 respostas, não 5, na segunda análise | Demonstração (texto atual do site) |
| Desde 2019, indústria e construção civil | **Sem prova no produto**; confirmar com o Tiago |

Ficou de fora por falta de prova: prazo do piloto até a primeira entrega, número de clientes, depoimentos, certificações e LGPD como selo.

---

## 7. Inconsistência fora deste arquivo (para o frontend)

No `site/demo.js`, linha 132, o convite depois do painel diz "passa pela revisão de **um especialista**". O site e o `CONTEXT.md` dizem que o revisor é **alguém do seu time** (papel `revisor` do cliente). Sugestão de texto:

> **Isso foi uma planilha, uma vez.** No Lastro contratado, o painel liga direto nos seus sistemas (Sienge, Omie, Bling…), passa pela revisão de alguém do seu time e abre no seu Power BI ou Looker Studio.

Saiu também "atualiza sozinho todo dia": a carga agendada é do plano Operação, não de todo contrato. Se quiser manter, use "no plano Operação, atualiza todo dia".

---

## 8. Nota esperada depois do texto novo

Estimativa sobre o texto da seção 4, com cerca de 950 palavras visíveis.

| Grupo | Hoje | Depois | O que sustenta |
|---|---|---|---|
| SEO | vermelho | verde | Título com 53 caracteres começando pela frase. Meta com 154 caracteres. Frase no H1 e no `lead`. 7 ocorrências exatas (cerca de 0,7%): título, meta, H1, lead, H2 de custo, corpo de custo, H2 do FAQ. 7 de 22 subtítulos com a frase ou um sinônimo (cerca de 32%). Alt com sinônimo em 2 de 4 imagens. Link externo (`wa.me`). Fica laranja: link interno, até aplicar o 4.16. O slug não se aplica. |
| Legibilidade | laranja | verde | Nenhuma frase nova passa de 20 palavras, salvo a do lead, com 19. Transição em cerca de 35% das frases (primeiro, depois, então, além disso, por exemplo, por isso, assim, mas, também, em seguida, por fim, mesmo assim). Passiva em cerca de 2%. Flesch estimado entre 55 e 60, no limite do verde. Fica laranja: a lista `.sistemas`, se o markup não mudar. |
| Técnico | vermelho | verde | Canonical, Open Graph completo com imagem 1200×630, Twitter card, JSON-LD (Organization, WebSite, SoftwareApplication, FAQPage), meta robots, `robots.txt` e `sitemap.xml` na raiz, favicon PNG e `apple-touch-icon`. Depende do frontend criar a imagem OG, os ícones e as duas rotas. |

Próximo passo: o engenheiro de frontend aplica a seção 4 no `site/index.html` e as rotas da seção 5 no `lastro/api.py`. Depois, roda o Yoast (ou o `yoastseo`) e o Lighthouse para confirmar as notas, e faz o QA com Playwright em 375 px e 1440 px, como pede o LST-55.
