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

- [x] Camada gold de cada empresa exposta por um endpoint SQL padrão (Postgres), com usuário só de leitura por empresa e RLS: uma empresa nunca vê a outra
- [ ] Guia de conexão testado com o que é gratuito: Power BI Desktop (conector PostgreSQL), Looker Studio (conector PostgreSQL) e Metabase OSS (Docker local)
- [x] Exportação CSV/Parquet por fonte para BI sem conector de banco
- [x] Credencial do BI gerada no portal pelo admin, trocável, nunca exibida duas vezes
- [x] Teste: o usuário de BI não grava nada e não lê outra empresa

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

## Evidência (25/11)

Commit `1851225`. Migração `0008_bi` aplicada no Supabase `lastro-teste`. O usuário de produção tem `CREATEROLE`.

**Testes: 226 passed com Postgres.** O Postgres local passou a exigir senha de todo usuário que não é o `postgres`, para a senha valer de verdade.
- O usuário de BI vê só o próprio schema, com as fontes e o esquema estrela do gold.
- Recusados com erro de permissão: outra empresa, `usuarios`, `demandas`, `interno`, Vault e `monitorar()`.
- Escrita bloqueada duas vezes: pela sessão só leitura e, mesmo com ela desligada, pela falta de privilégio. Criar tabela em `public` também é recusado.
- Trocar a senha mantém usuário e schema, e a senha antiga para de valer. Desligar tira o login. A senha não fica no registro nem volta na tela.
- Publicação atômica: uma fonte quebrada vira aviso e as outras são publicadas (savepoint por tabela).
- No modo local (SQLite), o BI por SQL avisa que precisa do Postgres, e a exportação CSV/Parquet funciona.

**QA no portal** (Postgres local, Playwright em 1440 e 375 px): sem rolagem horizontal, sem erro de JavaScript, e a senha some ao recarregar.

**Metabase OSS v0.52.4 real (Docker)**, conectado com a credencial gerada no portal:
- enxerga só o schema da empresa, com 9 tabelas;
- o total vendido saiu 14.030.477,92, igual ao da auditoria;
- ler a outra empresa, gravar e ler os usuários foram recusados.

Prints em `evidencias/`.

**Achados:**
- Esta versão do DuckDB tirou `fetchmany` e `fetchone` das relações. A leitura passou a ser por cursor, em lotes.
- Um erro no meio de um `COPY` aborta a transação inteira do Postgres. Por isso há um savepoint por tabela.
- Este container não alcança o pooler do Supabase. Por isso, ao ligar o BI, a API entra com a credencial nova pelo mesmo caminho do BI e mostra o resultado na tela.

## Falta (Tiago)

1. No portal de produção: **conta → Conectar ao BI → ligar o BI**. Ler a linha **Testado** ou **Atenção** logo acima da senha.
2. Conectar um BI gratuito (Power BI Desktop ou Looker Studio) com os dados mostrados, seguindo `docs/infra/bi.md`.
