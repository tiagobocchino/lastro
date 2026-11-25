---
chave: LST-33
jira: https://adelecrm.atlassian.net/browse/LST-33
secao: INT
status: a-fazer
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
