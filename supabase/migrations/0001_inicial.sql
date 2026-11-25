-- Lastro · esquema de produção no Supabase (Postgres + Auth), com RLS por tenant.
-- O tenant e o papel vêm de app_metadata do JWT: {"tenant_id": "...", "papel": "..."}.

create table if not exists tenants (
  id text primary key,
  nome text not null,
  plano text not null default 'consulta' check (plano in ('consulta', 'pipeline', 'operacao')),
  criado_em timestamptz not null default now()
);

create table if not exists perfis (
  user_id uuid primary key references auth.users (id) on delete cascade,
  tenant_id text not null references tenants (id),
  nome text not null,
  papel text not null check (papel in ('admin', 'demandante', 'revisor', 'leitor'))
);

create table if not exists fontes (
  id bigint generated always as identity primary key,
  tenant_id text not null references tenants (id),
  nome text not null,
  tipo text not null,
  caminho text not null,            -- caminho no Storage ou referência ao conector
  segredo_id uuid,                  -- credencial somente leitura no Supabase Vault
  criado_em timestamptz not null default now()
);

create table if not exists demandas (
  id bigint generated always as identity primary key,
  tenant_id text not null references tenants (id),
  autor uuid not null references auth.users (id),
  pergunta text not null,
  fontes bigint[] not null,
  status text not null check (status in ('nova', 'grill', 'pronta', 'em_revisao', 'aprovada', 'reprovada')),
  grill jsonb not null default '[]',
  respostas jsonb not null default '{}',
  resultado jsonb not null default '{}',
  criado_em timestamptz not null default now()
);

create table if not exists eventos (
  id bigint generated always as identity primary key,
  tenant_id text not null references tenants (id),
  demanda_id bigint references demandas (id),
  ator text not null,
  acao text not null,
  detalhe jsonb not null,
  em timestamptz not null default now()
);

create or replace function public.meu_tenant() returns text
language sql stable as $$ select (auth.jwt() -> 'app_metadata' ->> 'tenant_id') $$;

create or replace function public.meu_papel() returns text
language sql stable as $$ select (auth.jwt() -> 'app_metadata' ->> 'papel') $$;

alter table tenants enable row level security;
alter table perfis enable row level security;
alter table fontes enable row level security;
alter table demandas enable row level security;
alter table eventos enable row level security;

create policy tenant_le on tenants for select using (id = meu_tenant());
create policy perfis_le on perfis for select using (tenant_id = meu_tenant());
create policy fontes_le on fontes for select using (tenant_id = meu_tenant());
create policy fontes_admin on fontes for insert with check (tenant_id = meu_tenant() and meu_papel() = 'admin');
create policy demandas_le on demandas for select using (tenant_id = meu_tenant());
create policy demandas_abre on demandas for insert
  with check (tenant_id = meu_tenant() and meu_papel() in ('admin', 'demandante') and autor = auth.uid());
create policy demandas_atualiza on demandas for update
  using (tenant_id = meu_tenant() and meu_papel() in ('admin', 'demandante', 'revisor'));
create policy eventos_le on eventos for select using (tenant_id = meu_tenant());
-- eventos são gravados só pelo backend (service role); usuário não insere nem apaga rastro.
