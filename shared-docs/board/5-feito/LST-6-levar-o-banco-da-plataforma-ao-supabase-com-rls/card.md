---
chave: LST-6
jira: https://adelecrm.atlassian.net/browse/LST-6
secao: NUC
status: feito
especialista: engenheiro-backend
---

# Levar o banco da plataforma ao Supabase com RLS

**Por quê:** Piloto com mais de uma empresa precisa de isolamento no banco, não só no código.

## Critérios de aceite

- [x] Migração supabase/migrations/0001 aplicada num projeto de teste
- [x] Usuário de um tenant não lê linha de outro (teste com dois JWTs)
- [x] Repo local e Supabase atrás da mesma interface

## Verificação

Comandos da seção NUC em `docs/agents/secoes.yaml` + os critérios acima.

## Evidência (25/11)

- **Supabase:** projeto `lastro-teste` (org Adele, região sa-east-1) com `0001_inicial` e `0002_backend_proprio` aplicadas.
- **Dois tokens no Supabase:** cada empresa, como `authenticated` com as próprias claims, enxerga só a si mesma em tenants, fontes, demandas e eventos. Ficaram bloqueados: alterar demanda da outra (0 linhas), gravar fonte na outra, ler senhas e a chave anon ler demandas. Os dados de teste foram apagados depois.
- **Verificador de segurança do Supabase:** um único aviso informativo, sobre `usuarios` ter RLS sem política. É intencional: só a conexão de dono lê senhas.
- **Mesma interface:** `abrir_banco(cfg)` devolve `BancoSqlite` ou `BancoPostgres` (`LASTRO_BANCO_URL`). Em `tests/test_postgres.py`, o contrato do repositório roda nos dois bancos, a RLS é testada direto no SQL com dois tokens, e o ciclo completo de uma demanda (abrir, executar, revisar) roda no Postgres.
- **Teste de mutação:** desligar a RLS de `demandas` derruba 3 testes.
- **Suíte:** `LASTRO_TESTE_PG=… uv run --extra postgres pytest -q` = 144 passed (Postgres 16 local, com `supabase/teste/auth_simulado.sql`).
- **Container contra o Postgres:** `/saude` ok, login, demanda aberta, executada e aprovada pela API, 12 eventos gravados.
- **Decisão:** `docs/adr/0008-backend-como-authenticated-no-postgres.md`.
- **Pendente para o LST-22:** a URL do pooler com senha vai para o Secret Manager como `LASTRO_BANCO_URL`.
