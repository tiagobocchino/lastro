---
name: power-bi-refresh-lento
description: Refresh do Power BI lento ou caindo por data/hora automática, colunas calculadas com FILTER(ALL) e calendário sem limite
type: erro-conhecido
tags: [power bi, refresh, lento, performance, auto date time, LocalDateTable, coluna calculada, FILTER ALL, calendário, dax]
---

# Sintoma

O refresh demora dezenas de minutos ou estoura o tempo. O modelo tem muitas tabelas `LocalDateTable_*`.

# Causas comuns

- **Data/hora automática** ligada: uma tabela de datas escondida para cada coluna de data. Desligar mexe nos visuais que usam a hierarquia automática (houve um caso com 53). Mapeie antes.
- **Colunas calculadas com `FILTER(ALL(...))`**, que varrem a tabela inteira para cada linha. Leve a regra para a origem (SQL ou Power Query) ou transforme em medida.
- **Calendário sem limite**, gerado de MIN a MAX de todas as datas, incluindo datas de mentira. Use um intervalo fixo.
- **Merge de fonte de nuvem com fonte local**, que obriga gateway e quebra o refresh no Serviço.

# Correção

Uma mudança de cada vez, seguindo o método mudar-sem-mudar-o-numero.
