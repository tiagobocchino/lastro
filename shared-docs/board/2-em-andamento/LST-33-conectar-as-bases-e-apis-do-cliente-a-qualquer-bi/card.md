---
chave: LST-33
jira: https://adelecrm.atlassian.net/browse/LST-33
secao: INT
status: em-andamento
especialista: engenheiro-de-dados
---

# Conectar as bases e APIs do cliente a qualquer BI self-service

**Por quê:** o propósito do Lastro é ligar as bases e as APIs do cliente diretamente ao BI que ele já usa (Power BI, Looker Studio, Metabase, Superset…), para o operador alterar, construir do zero e consumir os dados e relatórios, os mesmos que os agentes analisam.

## Critérios de aceite

- [ ] Camada gold de cada empresa exposta por um endpoint SQL padrão (Postgres), com usuário só de leitura por empresa e RLS: uma empresa nunca vê a outra
- [ ] Guia de conexão testado com o que é gratuito: Power BI Desktop (conector PostgreSQL), Looker Studio (conector PostgreSQL) e Metabase OSS (Docker local)
- [ ] Exportação CSV/Parquet por fonte para BI sem conector de banco
- [ ] Credencial do BI gerada no portal pelo admin, trocável, nunca exibida duas vezes
- [ ] Teste: o usuário de BI não grava nada e não lê outra empresa

## Verificação

`uv run pytest -q` + conexão real de um BI gratuito em produção.

## Fora do escopo agora

Contas pagas (Power BI Pro/Fabric, Looker pago, Tableau): sem teste até haver conta.

## Origem

Visão do Tiago em 25/11: o Lastro conecta bases e APIs aos BIs self-service; nosso próprio sistema e os exemplos do site usam dashboards em Python (gratuito), e Looker Studio no pior caso.

## Desenho (25/11)

- **Isolamento por schema e papel, não por RLS.** Cada empresa tem um schema e um papel com o mesmo nome opaco, `bi_<10 hex>`. O papel só tem `SELECT` no próprio schema e roda com `default_transaction_read_only`, `statement_timeout` e limite de conexões. Os BIs listam schemas e tabelas, e o schema por empresa mostra só o que é dela. O nome é opaco porque `pg_namespace` e `pg_roles` são legíveis por qualquer papel.
- **O que vai para o BI:**
  - cada fonte vira `fonte_<nome>`;
  - cada demanda aprovada vira `d<id>_fato`, `d<id>_dim_*` e `d<id>_silver`, um esquema estrela do gold.
  - A troca é atômica, numa transação só.
- **Quando publica:** pelo botão no portal, depois de cada carga boa (LST-7) e de cada aprovação.
- **Acesso ao banco:** pelo Session pooler do Supabase (porta 5432), com usuário `bi_xxx.<ref>`.
