# ADR 0008: O backend fala com o Postgres como `authenticated`, com as claims do usuário

**Status:** aceito · 25/11/2026 · card LST-6 · complementa a ADR 0004

## Contexto

A ADR 0004 previa o Supabase Auth com RLS. O produto, porém, tem login próprio (token assinado com `LASTRO_SEGREDO`), e o portal não fala com o banco: quem fala é só o backend. Se o backend usasse a conexão de dono (ou a service role), a RLS seria ignorada, e o isolamento entre empresas dependeria apenas do `WHERE tenant_id` no código.

## Decisão

- **Uma transação por operação.** Cada chamada do `RepoPostgres` abre a própria transação e executa `SET LOCAL ROLE authenticated` e `set_config('request.jwt.claims', ...)` com o e-mail, o tenant e o papel do usuário da requisição. Isso reproduz o que o PostgREST do Supabase faz com um JWT. As políticas da `0002_backend_proprio.sql` decidem o que cada linha mostra.
- **Conexão de dono só em dois casos:** o login, quando o tenant ainda não é conhecido, e o cadastro de tenant ou usuário.
- **Chave anon pública sem acesso.** O anon perde o acesso a todas as tabelas do Lastro. O `authenticated` não apaga nada, não lê senhas e não mexe em tenants.
- **Mesma interface nos dois bancos.** `abrir_banco(cfg)` devolve SQLite (local) ou Postgres (quando `LASTRO_BANCO_URL` existe), ambos com a mesma interface. Os mesmos testes rodam contra os dois.
- **Pooler em modo transação:** a conexão usa `prepare_threshold=None`, porque esse modo não aceita prepared statements.

## Consequências

- O filtro por tenant no SQL vira a segunda trava, não a única. O teste de mutação (desligar a RLS de `demandas`) derruba 3 testes.
- O `autor` da demanda passa a ser o e-mail do login próprio. Migrar para o Supabase Auth no futuro exige uma nova migração.
- `perfis` (ligada a `auth.users`) fica sem uso até essa migração.
