---
name: conferencia-card-x-tabela
description: Quando o número do cartão não bate com a soma da tabela, decompor o universo em motivos (conta nos dois, só no cartão, só na tabela, fora dos dois)
type: metodo
tags: [conferência, cartão, card, tabela, divergência, não bate, power bi, looker, contagem, blank, filtro de página]
---

# Quando usar

A área de negócio pergunta "por que o cartão mostra 174 e a tabela 120?" ou "por que o total não fecha com a soma das barras?".

# Como fazer

1. Monte o universo com a **mesma extração e as mesmas regras do painel**. Não acrescente coluna que não exista na origem.
2. Marque cada registro com duas flags: `conta_no_cartao` e `aparece_na_tabela`.
3. Agrupe por motivo e mostre a contagem e o valor de cada grupo. Os motivos que mais aparecem:
   - **conta no cartão e some da tabela:** a medida da tabela fica vazia (BLANK) para o registro. Exemplo: orçamento sem itens. O cartão conta linhas; a tabela só mostra linhas com valor;
   - **fora dos dois:** filtro de página ou de relatório. Exemplo: status CANCELADO excluído da página;
   - **só na tabela:** o cartão exige um campo que o registro não tem. Exemplo: nome do projeto vazio;
   - **some do gráfico por categoria:** a categoria está vazia. A linha entra no total e não aparece em nenhuma barra.
4. Entregue três coisas:
   - a tabela de conferência (CSV/Excel);
   - a consulta SQL para a pessoa rodar sozinha (DBeaver);
   - o resumo por mês do ano inteiro, não só do mês da reclamação.

# O que o Lastro já faz

O Auditor avisa "fora do gráfico por <dimensão>" e "nulos na medida", com a quantidade de linhas e o valor. Esses avisos respondem à pergunta antes que ela chegue.
