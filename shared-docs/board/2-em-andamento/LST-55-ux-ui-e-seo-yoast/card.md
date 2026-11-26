---
chave: LST-55
jira: https://adelecrm.atlassian.net/browse/LST-55
secao: MKT
status: em-andamento
especialista: engenheiro-frontend
---

# UX/UI e SEO (padrão Yoast) do site, portal e dashboards

**Pedido do Tiago (26/11):** usar a skill ui-ux-pro-max com o time de UX/UI para deixar o site, a plataforma e os layouts dos dashboards mais bonitos e adequados ao SEO do Yoast, para atrair mais clientes.

## Critérios de aceite

- [x] Auditoria de SEO e legibilidade no padrão Yoast do site, com texto novo (redator-de-copy, `docs/ux/seo-site-yoast.md`)
- [x] Auditoria de UI/UX do site, do portal e dos dashboards pela skill (engenheiro-frontend, `docs/ux/auditoria-ui-ux.md`)
- [x] Site: título e descrição, frase-chave, Open Graph, JSON-LD, canonical, `robots.txt`, `sitemap.xml`, alt e legibilidade
- [x] Portal e dashboards: correções críticas e altas da auditoria, mantendo a marca (`BRAND.md`)
- [x] QA com Playwright em 375 px e 1440 px, sem rolagem horizontal; Lighthouse acima de 90 no site

## Andamento (26/11)

- Estudo de referência do site da Atenta Labs (só leitura do repositório deles): `docs/ux/referencia-atenta-labs.md`. Estudo do OpenSEO: `docs/ux/openseo.md`.
- Site refeito (`site/index.html`) no método Atenta com a marca do Lastro:
  - faixas escuras e claras, seções `[ 01 ]…[ 10 ]`, título em dois tons, um CTA por tela e FAQ em `<details>`;
  - texto do redator, JSON-LD (Organization, WebSite, SoftwareApplication, FAQPage) e Open Graph com `img/og-lastro.jpg`;
  - ícones PNG e fontes servidas pelo próprio site (`site/fontes/`, OFL);
  - `/robots.txt` e `/sitemap.xml` na raiz (`lastro/api.py`).
- Demo: rolagem em 375 px (C1), planilha sem linhas recusada (A2), horário de Brasília no painel e no recibo, iframe sem corte (A7), convite sem "especialista" e sem "atualiza sozinho", nome do arquivo escolhido, alvos de 44 px e movimento reduzido.
- QA: sem rolagem de 320 a 1440 px, demo de ponta a ponta com a planilha de exemplo, sem erro de console (capturas em `docs/ux/capturas/site-novo/`); 349 testes passando.
- Portal e dashboards (26/11):
  - login: senha errada não vira mais "sessão expirou" (C2); contas de teste só fora de produção, por `/api/config` (A5); estado "entrando…";
  - erro e esqueleto de carregamento ao abrir demanda e na lista (A3); no celular, rola até a demanda aberta e o topo cabe numa linha (A4);
  - bordas de campo com 3:1 (`--campo`), alvos de 44 px e fontes do próprio Lastro (M1, M2, M3);
  - painel HTML sem coluna vazia (A1);
  - Streamlit com o tema da marca (`.streamlit/config.toml`), título visível no escuro (C3), textos em PT e números no formato brasileiro, barras no lugar da rosca (A8, M10 em parte);
  - Power BI: paleta com 3:1 sobre branco e cores good/bad/neutral (M9); desvio da Segoe UI registrado no `BRAND.md`.
- Demanda aprovada reordenada (A6):
  - ordem nova: total com selo da auditoria, painel, resposta, conversa;
  - auditoria, "como chegamos aqui" e rastro ficam recolhidos e têm links de atalho no topo;
  - o rastro aparece em "chave: valor", não em JSON;
  - a página caiu de 4.300 px para 2.700 px no desktop e de 6.500 px para 3.800 px no celular.
- Manual do Streamlit Cloud para o Tiago: `docs/infra/streamlit.md`.
- Layout novo dos dashboards, conforme o grill:
  - painel HTML: `lastro/painel_html.py`, com cubo embutido, filtros, 4 cartões, gráfico principal, ranking top 10 + outros e conferência com total; funciona sem JavaScript;
  - Streamlit: `nucleo.resumo` e `nucleo.ranking`, com a mesma estrutura;
  - testes conferem os números contra SQL direto no gold;
  - capturas em `docs/ux/capturas/painel-novo/`.
- Lighthouse no ar (26/11, commit 7ce52ff):
  - site: 99/100/100/100 no celular e 100 nas quatro no desktop;
  - portal: 100/100/100, com SEO 63 por causa do `noindex`, que é proposital: o portal não deve ser indexado.
- Imagens do site em WebP com versão de 800 px (de 45% a 85% menores) e atributos de tamanho certos; cache longo para fontes (1 ano) e imagens (7 dias).
- Confirmado pelo Tiago (26/11): "desde 2019" fica no texto e a lixum.labs é a Organization do JSON-LD.

## Grill do layout dos dashboards (26/11, respondido pelo Tiago)

- Comparação dos cartões: **mesmo período do ano anterior**, de janeiro até o último mês com dado (igual ao Power BI de entrega).
- Ranking: **top 10 + "outros"**, com o % do total de cada linha.
- Painel HTML: **com filtros interativos** (empresa, região, ano) dentro do próprio arquivo.
- Ordem: **painel HTML e Streamlit juntos**, com a mesma estrutura: filtros → 4 cartões → gráfico principal → ranking → tabela de conferência.

## Pronto para fechar (26/11)

- Todos os critérios de aceite estão marcados.
- Lighthouse no ar depois das imagens em WebP: site 100/100/100/100 no celular, com 184 KB no total.
- Ajuste de texto pedido pelo Tiago na seção [05] do site: "mapeado em operação real" (d61646c).
- **Falta:** o "ok" do Tiago para mover o card para Feito.
