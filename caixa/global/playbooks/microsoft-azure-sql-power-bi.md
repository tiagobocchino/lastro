---
name: microsoft-azure-sql-power-bi
description: "Trilha Microsoft: Excel/SharePoint em Bronze/Silver/Gold no Azure SQL Database (camada gratuita) ou Warehouse do Fabric, com Power BI e auditoria no Colab"
type: playbook
tags: [microsoft, azure, azure sql, fabric, power bi, excel, sharepoint, t-sql, medalhão, star schema]
---

# Quando usar

A empresa usa Excel, SharePoint e Power BI, e quer um banco central sem montar data lake.

# Camadas

Três schemas no mesmo banco: `bronze`, `silver` e `gold`.
- **Bronze:** a fonte importada como `bronze.fonte_<nome>`, pelo assistente de importação ou `BULK INSERT`.
- **Silver:** `TRY_CAST`, `TRIM`, filtro do grill e deduplicação pela chave (`ROW_NUMBER` em subconsulta, porque o T-SQL não tem `QUALIFY`).
- **Gold:** dimensões e fato.

O Lastro gera `trilhas/pipeline_azure_sql.sql`, com `DROP TABLE IF EXISTS` + `SELECT * INTO` (vale no Azure SQL e no Warehouse do Fabric), traduzido do pipeline do sandbox e conferido por ida e volta. O Power BI conecta pelo conector do Azure SQL.

# Custo gratuito (conferido em 25/11/2026 em learn.microsoft.com)

- **Camada gratuita do Azure SQL Database:** por banco e por mês, 100 mil vCore-segundos, 32 GB de dados e 32 GB de backup, enquanto a assinatura existir. Até 10 bancos gratuitos por assinatura.
- Sem SLA. Dá para criar só banco novo; não é possível converter um existente.
- **Ao atingir o limite do mês**, há duas escolhas:
  - **Auto-pause:** o banco fica fora do ar até o mês virar e nada é cobrado.
  - **Cobrar excedente:** o banco continua no ar e paga. **Não dá para voltar atrás.**

  Recomendação do Lastro: Auto-pause.
- O banco pausa sozinho após 15 minutos sem uso. Conexão aberta do SSMS ou do VS Code impede a pausa e gasta vCore. Feche as ferramentas ao terminar.
- Crie um alerta gratuito na métrica "Free amount remaining" abaixo de 10 mil vCore-segundos (10% do mês).
- A região do primeiro banco gratuito vale para todos os bancos gratuitos da assinatura.

# Auditoria

- **Camada 1:** as mesmas checagens do relatório, em T-SQL.
- **Camada 2:** o notebook do Colab conecta no gold com um login só de leitura (`db_datareader` no schema `gold`).
- **Power BI:** use refresh agendado fora do horário comercial para não acordar o banco à toa e consumir vCore.

# Armadilhas

- O T-SQL não aceita `JOIN ... USING` nem subconsulta sem apelido. O Engenheiro gera SQL portável (`ON` e apelidos) por causa disso.
- `VARCHAR(MAX)` é o equivalente do texto sem tamanho do DuckDB.
- Refresh do Power BI e ferramentas abertas são o que mais gasta a cota mensal.

# Origem

Página oficial em `docs/infra/fontes/` (camada gratuita do Azure SQL Database). Gerador em `lastro/trilhas.py`, card LST-15. A primeira execução numa assinatura real será registrada aqui.
