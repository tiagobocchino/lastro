# ADR 0004: Tenant em toda tabela; Repo local e RLS no Supabase

**Status:** aceito · 2026-11-25

## Decisão

Local: SQLite com `Repo(con, tenant)`, que filtra por tenant em todas as consultas. Produção: Supabase Auth + Postgres com RLS (`supabase/migrations/0001_inicial.sql`), o `tenant_id` lido do JWT. Papéis: admin, demandante, revisor, leitor.
