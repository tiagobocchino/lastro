-- Só para teste local (Postgres puro): imita o que o Supabase já traz pronto.
-- Papéis anon/authenticated e as funções auth.jwt() e auth.uid() lendo request.jwt.claims,
-- como o PostgREST do Supabase faz. Nunca aplicar num projeto Supabase.
do $$ begin
  if not exists (select 1 from pg_roles where rolname = 'anon') then create role anon nologin; end if;
  if not exists (select 1 from pg_roles where rolname = 'authenticated') then create role authenticated nologin; end if;
  if not exists (select 1 from pg_roles where rolname = 'service_role') then create role service_role nologin bypassrls; end if;
end $$;
create schema if not exists auth;
create table if not exists auth.users (id uuid primary key default gen_random_uuid());
create or replace function auth.jwt() returns jsonb language sql stable as
  $$ select coalesce(nullif(current_setting('request.jwt.claims', true), ''), '{}')::jsonb $$;
create or replace function auth.uid() returns uuid language sql stable as
  $$ select nullif(auth.jwt() ->> 'sub', '')::uuid $$;
grant usage on schema auth, public to anon, authenticated, service_role;
grant execute on all functions in schema auth to anon, authenticated, service_role;
-- O Supabase dá privilégios padrão a anon e authenticated em public; a 0002 revoga o do anon.
alter default privileges in schema public grant all on tables to anon, authenticated, service_role;
alter default privileges in schema public grant all on sequences to anon, authenticated, service_role;

-- Vault simulado (o Supabase traz o real, que cifra o segredo). Mesma assinatura das funções usadas pelo cofre.
create schema if not exists vault;
create table if not exists vault.secrets (id uuid primary key default gen_random_uuid(), name text unique, description text, secret text not null);
create or replace function vault.create_secret(new_secret text, new_name text default null, new_description text default '', new_key_id uuid default null)
returns uuid language sql as $$ insert into vault.secrets (name, description, secret) values (new_name, new_description, new_secret) returning id $$;
create or replace function vault.update_secret(secret_id uuid, new_secret text default null, new_name text default null, new_description text default null, new_key_id uuid default null)
returns void language sql as $$ update vault.secrets set secret = coalesce(new_secret, secret) where id = secret_id $$;
create or replace view vault.decrypted_secrets as select id, name, description, secret as decrypted_secret from vault.secrets;
revoke all on schema vault from anon, authenticated;

-- pg_net simulado: guarda os pedidos e deixa o teste escrever a resposta em net._http_response.
create schema if not exists net;
create table if not exists net.pedidos (id bigserial primary key, metodo text, url text, corpo jsonb, cabecalhos jsonb);
create table if not exists net._http_response (id bigint primary key, status_code integer, content text, timed_out boolean, error_msg text, created timestamptz default now());
create or replace function net.http_get(url text, params jsonb default '{}', headers jsonb default '{}', timeout_milliseconds integer default 5000)
returns bigint language sql as $$ insert into net.pedidos (metodo, url, cabecalhos) values ('GET', url, headers) returning id $$;
create or replace function net.http_post(url text, body jsonb default '{}', params jsonb default '{}', headers jsonb default '{}', timeout_milliseconds integer default 5000)
returns bigint language sql as $$ insert into net.pedidos (metodo, url, corpo, cabecalhos) values ('POST', url, body, headers) returning id $$;
