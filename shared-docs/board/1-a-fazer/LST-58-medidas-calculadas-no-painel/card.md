---
chave: LST-58
jira: https://adelecrm.atlassian.net/browse/LST-58
secao: NUC
status: a-fazer
especialista: engenheiro-de-dados
---

# Medidas calculadas no painel: conversão (vendido ÷ orçado), variação mês a mês e mês até hoje

**Origem:** pedidos reais de um testador na demanda 19 da demo (26/11, entre 13h28 e 13h38). O designer recusou todos, porque o painel só sabe medidas de uma coluna (soma, média, contagem, distintos, mínimo e máximo).

## O que foi pedido

1. **Taxa de conversão:** valor vendido ÷ valor orçado, no total, por vendedor e mês a mês.
2. **Variação mês a mês:** a evolução mensal com o % contra o mês anterior.
3. **Mês até hoje:** o mês atual até a data de hoje contra o mês anterior até o mesmo dia (ex.: 01 a 26/11 contra 01 a 26/10).

Por enquanto, o designer responde com uma mensagem específica e sugere pôr as duas medidas lado a lado (commit 423790f).

## Grill (regra de negócio vem do cliente, ADR 0011)

- **Conversão:**
  - É valor (vendido ÷ orçado) ou quantidade (contratos fechados ÷ orçamentos)?
  - Qual data vale, a do orçamento ou a do fechamento?
  - Um orçamento de um mês fechado no mês seguinte entra em qual mês?
- **Mês até hoje:**
  - "Hoje" é a data do servidor ou o último dia com dado?
  - O que fazer quando o mês anterior é mais curto (31/03 contra 28/02)?
- **Onde vale:** as medidas calculadas entram também no Power BI (DAX) e no Looker, ou só no painel do Lastro?

## Critérios de aceite

- [ ] Medida de razão entre duas medidas do painel, com proteção para divisão por zero.
- [ ] Variação contra o período anterior (mês a mês), no gráfico e na tabela de conferência.
- [ ] Comparação do mês até o mesmo dia, com a regra respondida no grill.
- [ ] O que o painel HTML calcula bate com o projeto do Power BI (mesma regra em DAX).
- [ ] As frases do testador viram testes (`tests/test_paineis.py`).
