---
name: tabela-unica-de-conferencia
description: O negócio pede uma tabela só, com todas as regras do BI aplicadas, para conferir por conta própria
type: metodo
tags: [conferência, tabela única, flat, sql, dbeaver, regras de negócio, auditoria do negócio, excel]
---

# Pedido típico

"Me dê uma query para uma única tabela, com todas as colunas do BI e todas as regras: datas do funil, etapa, status, número de controle, representante e vendedor. Com um filtro só, o ano."

# Regra

- **Uma linha por registro** da fato, com as dimensões já ligadas e as colunas derivadas pelas mesmas regras do painel.
- Os nomes de coluna são os que o negócio usa, e cada coluna derivada traz a regra num comentário.
- Há um filtro só, no topo, como parâmetro (por exemplo o ano).
- Entregue em SQL para rodar no cliente de banco e também em CSV/Excel.
- É a mesma tabela que o Data Studio e o Power BI consomem mais fácil: o negócio confere aquilo que o painel mostra.
