---
name: google-bigquery-looker
description: "Trilha Google: fonte do cliente em Bronze/Silver/Gold no BigQuery (sandbox ou camada gratuita), consumo no Looker Studio ou Power BI e auditoria no Colab"
type: playbook
tags: [google, bigquery, sandbox, looker studio, power bi, colab, sheets, drive, medalhão, star schema]
---

# Quando usar

A empresa já vive no Google: Planilhas, Drive, Gmail. Ela quer um painel sem licença (Looker Studio) ou o Power BI lendo de um warehouse, e não tem time de infraestrutura.

# Camadas

Um dataset por camada no mesmo projeto: `lastro_bronze`, `lastro_silver` e `lastro_gold`.
- **Bronze:** a fonte como chegou, carregada com `bq load --autodetect` a partir do CSV que o Lastro gerou, ou por tabela externa sobre a planilha.
- **Silver:** tipos corrigidos (`SAFE_CAST`), textos aparados, filtro do grill aplicado e deduplicação pela chave (`ROW_NUMBER` em subconsulta).
- **Gold:** dimensões e fato do star schema.

O Lastro gera o script pronto (`trilhas/pipeline_bigquery.sql` da demanda), traduzido do pipeline testado no sandbox e conferido por ida e volta. Para rodar: `bq query --use_legacy_sql=false < pipeline_bigquery.sql`.

# Custo gratuito (conferido em 25/11/2026 nas páginas oficiais do Google Cloud)

- **Sandbox do BigQuery** (sem cartão): 10 GiB de armazenamento no total da vida do projeto (apagar dados não devolve a cota), 1 TiB de consulta por mês. Toda tabela, view e partição expira em 60 dias. Serve para piloto, não para produção.
- **Camada gratuita com cobrança ativa:** 10 GiB de armazenamento por mês e 1 TiB de consulta por mês. Ao sair do sandbox, revise a expiração padrão dos datasets, ou as tabelas continuam vencendo em 60 dias.
- **Looker Studio:** sem licença. O custo é a consulta no BigQuery: use extração ou cache para o painel não reconsultar a cada abertura.
- **Orçamento:** o orçamento só de alerta não corta gasto. Ver `docs/infra/conta-google-cloud.md`.

# Auditoria

As duas camadas do Lastro valem iguais:
- **Camada 1:** linhas por etapa, chave sem repetição, soma da medida igual entre silver e fato. Rode as mesmas checagens do relatório como consultas no BigQuery.
- **Camada 2:** o notebook do Colab da demanda lê o gold. No Colab, a autenticação no BigQuery é a da conta Google do revisor; dê a ele só o papel de leitor de dados no `lastro_gold`.

# Armadilhas

- `QUALIFY` no BigQuery exige `WHERE`, `GROUP BY` ou `HAVING`. O gerador evita isso usando subconsulta.
- Nulos na ordenação: o BigQuery põe nulos primeiro em ordem crescente e o DuckDB põe por último. O gerador escreve `NULLS LAST` onde a ordem importa (números das dimensões).
- O sandbox não aceita alguns recursos (DML com streaming, entre outros) e responde `billingNotEnabled`: o sinal de que chegou a hora de ativar a cobrança.

# Origem

Páginas oficiais em `docs/infra/fontes/` (sandbox do BigQuery, recursos gratuitos do Google Cloud). Gerador em `lastro/trilhas.py`, card LST-15. A primeira execução numa conta real será registrada aqui.
