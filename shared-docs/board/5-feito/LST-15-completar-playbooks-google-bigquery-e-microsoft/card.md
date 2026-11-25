---
chave: LST-15
jira: https://adelecrm.atlassian.net/browse/LST-15
secao: CON
status: feito
especialista: engenheiro-de-dados
---

# Completar playbooks Google (BigQuery) e Microsoft (Azure)

**Por quê:** As trilhas aparecem como 'em construção' no site.

## Critérios de aceite

- [x] Playbook com camadas, custo gratuito e auditoria para cada trilha
- [x] Gerador de pipeline por trilha a partir do modelo do Arquiteto
- [x] Site atualiza o selo quando o card fechar (não se aplica: o site reescrito no LST-14 não mostra trilhas)

## Verificação

Comandos da seção CON em `docs/agents/secoes.yaml` + os critérios acima.

## Evidência (25/11)

**Playbooks:**
- `caixa/global/playbooks/google-bigquery-looker.md` e `microsoft-azure-sql-power-bi.md`, cada um com camadas, custo gratuito, auditoria e armadilhas. As duas trilhas passaram de "a completar" para "playbook pronto".
- Limites conferidos hoje nas páginas oficiais, salvas em `docs/infra/fontes/`:
  - **Sandbox do BigQuery:** 10 GiB no total da vida do projeto, 1 TiB de consulta por mês e tabelas que expiram em 60 dias.
  - **Camada gratuita do BigQuery:** 10 GiB e 1 TiB por mês.
  - **Azure SQL gratuito:** 100 mil vCore-segundos, 32 GB e até 10 bancos; pausa após 15 minutos; a opção "cobrar excedente" não volta atrás.
- A busca da Caixa acha cada playbook.

**Gerador por trilha** (`lastro/trilhas.py`, com sqlglot):
- O Engenheiro grava `trilhas/pipeline_bigquery.sql`, `pipeline_azure_sql.sql` e `pipeline_athena.sql` em cada demanda.
- O portal ganhou os botões "Google BigQuery", "Azure SQL / Fabric" e "AWS Athena". Testado pela API: 200 e nome de arquivo correto.
- SQL do Engenheiro ficou portável: sem `USING` e com apelido nas subconsultas.
- Cada dialeto evita o que a nuvem recusa:
  - `QUALIFY` virou subconsulta;
  - T-SQL usa `DROP TABLE IF EXISTS` + `SELECT INTO`;
  - Athena usa CTAS em Parquet com local no S3.

**Prova:**
- `tests/test_trilhas.py`: o SQL de cada nuvem volta para o DuckDB, roda nos mesmos dados e dá exatamente o mesmo resultado em silver, dimensões e fato (`EXCEPT ALL` nos dois sentidos). O total é 14.030.477,92 nas três.
- O parser de cada dialeto aceita o script inteiro.
- Isso valida a tradução, não a execução numa nuvem real; a primeira execução vai para o playbook.

**Busca:** ajuste para não confundir "faturamento" (receita) com a cobrança da nuvem; o termo virou "cobrança".

**Suíte:** 194 passed com Postgres.
