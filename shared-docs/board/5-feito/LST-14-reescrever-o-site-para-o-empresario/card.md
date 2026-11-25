---
chave: LST-14
jira: https://adelecrm.atlassian.net/browse/LST-14
secao: MKT
status: feito
especialista: redator-de-copy
---

# Reescrever o site para o empresário

**Por quê:** O site atual explica o sistema; o empresário quer resposta para as preocupações dele.

## Critérios de aceite

- [x] Perguntas do empresário respondidas na ordem dele
- [x] Toda afirmação tem prova no produto
- [x] Sem rolagem horizontal em 375px; temas claro e escuro

## Verificação

Comandos da seção MKT em `docs/agents/secoes.yaml` + os critérios acima.

## Entrega (aguardando QA)

- `site/index.html` + `site/img/` (telas reais da demo, dados fictícios)
- Prévia privada: https://claude.ai/artifact/Nz5EVywrMvaxR39K1riCme
- 375px sem rolagem horizontal (Playwright)

## QA (25/11)

- Google Planilhas e Google Drive incluídos entre os sistemas mapeados (LST-11).
- Corrigido: a página não declarava `charset` e os acentos quebravam fora da prévia (Firebase, arquivo local).
- Playwright: 375px e 1440px, claro e escuro: sem rolagem horizontal, 0 imagens quebradas, 0 erros.
- Números da página conferidos com DuckDB direto no CSV: 14.030.477,92 só fechados e deduplicados; duplicados somariam 181.820,60.
- Prévia atualizada: https://claude.ai/artifact/Nz5EVywrMvaxR39K1riCme
