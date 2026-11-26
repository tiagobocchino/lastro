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
- [ ] Portal e dashboards: correções críticas e altas da auditoria, mantendo a marca (`BRAND.md`)
- [ ] QA com Playwright em 375 px e 1440 px, sem rolagem horizontal; Lighthouse acima de 90 no site

## Andamento (26/11)

- Estudo de referência do site da Atenta Labs (só leitura do repositório deles): `docs/ux/referencia-atenta-labs.md`. Estudo do OpenSEO: `docs/ux/openseo.md`.
- Site refeito (`site/index.html`) no método Atenta com a marca do Lastro:
  - faixas escuras e claras, seções `[ 01 ]…[ 10 ]`, título em dois tons, um CTA por tela e FAQ em `<details>`;
  - texto do redator, JSON-LD (Organization, WebSite, SoftwareApplication, FAQPage) e Open Graph com `img/og-lastro.jpg`;
  - ícones PNG e fontes servidas pelo próprio site (`site/fontes/`, OFL);
  - `/robots.txt` e `/sitemap.xml` na raiz (`lastro/api.py`).
- Demo: rolagem em 375 px (C1), planilha sem linhas recusada (A2), horário de Brasília no painel e no recibo, iframe sem corte (A7), convite sem "especialista" e sem "atualiza sozinho", nome do arquivo escolhido, alvos de 44 px e movimento reduzido.
- QA: sem rolagem de 320 a 1440 px, demo de ponta a ponta com a planilha de exemplo, sem erro de console (capturas em `docs/ux/capturas/site-novo/`); 349 testes passando.
- Falta: portal e dashboards (critério 4) e Lighthouse no ar depois do deploy.
- A confirmar com o Tiago: "desde 2019" e lixum.labs como Organization no JSON-LD.
