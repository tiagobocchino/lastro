---
name: planilha-para-star-schema
description: Como transformar uma planilha ou CSV plano num modelo dimensional (fato + dimensões) pronto para BI
type: playbook
tags: [star schema, modelo dimensional, fato, dimensão, planilha, excel, csv, power bi]
---

# Quando usar

Fonte plana (Excel, CSV, Google Sheets) com uma linha por evento (venda, orçamento, ação) e colunas de texto repetidas (vendedor, estado, status).

# Passos

1. Bronze: copie a fonte como está, com a data de carga.
2. Silver: tipagem (datas com TRY_CAST, texto com trim e vazio como nulo), filtro de negócio e remoção de duplicados pela chave, mantendo o registro mais recente.
3. Gold: uma dimensão por coluna de texto de baixa cardinalidade (id substituto + valor), dimensão de data (ano, mês, ano_mes) e uma tabela fato com as chaves das dimensões e as medidas numéricas.
4. Exporte o gold em Parquet; o BI lê o Parquet ou o warehouse.

# Origem

Método usado no ETL das 23 Fichas de Ação do Plano de Oceano (MMA): Excel complexo para 12 tabelas (1 fato principal, 8 dimensões, 3 fatos de relacionamento) e 60+ medidas DAX.

# Armadilhas

- Coluna de texto com cardinalidade quase igual ao número de linhas não é dimensão: é atributo ou chave.
- Somar uma medida antes de deduplicar infla o total; audite silver contra fato.
