-- Lastro · 0002: o backend (FastAPI no Cloud Run) é o único cliente do banco (ADR 0008).
-- Ele mantém o login próprio (ADR 0004) e abre cada transação como `authenticated`, com as
-- claims do usuário em request.jwt.claims. Assim a RLS vale também para o backend:
--   {"email": "...", "role": "authenticated", "app_metadata": {"tenant_id": "...", "papel": "..."}}

-- Funções com search_path fixo (aviso de segurança do Supabase) e e-mail do usuário.
create or replace function public.meu_tenant() returns text
language sql stable set search_path = '' as $$ select (auth.jwt() -> 'app_metadata' ->> 'tenant_id') $$;
create or replace function public.meu_papel() returns text
language sql stable set search_path = '' as $$ select (auth.jwt() -> 'app_metadata' ->> 'papel') $$;
create or replace function public.meu_email() returns text
language sql stable set search_path = '' as $$ select lower(auth.jwt() ->> 'email') $$;

-- Login próprio: só o dono do banco (conexão do backend, antes de saber o tenant) lê senha.
create table if not exists usuarios (
  email text primary key,
  tenant_id text not null references tenants (id),
  nome text not null,
  papel text not null check (papel in ('admin', 'demandante', 'revisor', 'leitor')),
  senha_hash text not null
);
alter table usuarios enable row level security;
revoke all on usuarios from anon, authenticated;

-- Autor da demanda é o e-mail do login próprio, não um usuário do Supabase Auth.
drop policy if exists demandas_abre on demandas;
alter table demandas drop constraint if exists demandas_autor_fkey;
alter table demandas alter column autor type text using autor::text;
create policy demandas_abre on demandas for insert
  with check (tenant_id = meu_tenant() and meu_papel() in ('admin', 'demandante') and autor = meu_email());

drop policy if exists demandas_atualiza on demandas;
create policy demandas_atualiza on demandas for update
  using (tenant_id = meu_tenant() and meu_papel() in ('admin', 'demandante', 'revisor'))
  with check (tenant_id = meu_tenant());

-- O backend grava o rastro em nome do usuário; nunca para outro tenant. Ninguém apaga rastro.
drop policy if exists eventos_grava on eventos;
create policy eventos_grava on eventos for insert with check (tenant_id = meu_tenant());

create index if not exists fontes_tenant on fontes (tenant_id);
create index if not exists demandas_tenant on demandas (tenant_id, id desc);
create index if not exists eventos_demanda on eventos (tenant_id, demanda_id);

-- A chave anon do Supabase é pública: ela não alcança nenhuma tabela do Lastro.
revoke all on tenants, perfis, fontes, demandas, eventos, usuarios from anon;
revoke all on all sequences in schema public from anon;
-- authenticated: só o que as políticas permitem; sem apagar e sem mexer em tenants.
revoke all on tenants, perfis, fontes, demandas, eventos from authenticated;
grant select on tenants, perfis to authenticated;
grant select, insert on fontes, eventos to authenticated;
grant select, insert, update on demandas to authenticated;
grant usage on all sequences in schema public to authenticated;
