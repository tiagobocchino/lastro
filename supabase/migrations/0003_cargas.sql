-- Lastro · 0003: cargas incrementais agendadas por fonte (card LST-7, plano Operação).
-- Credenciais da carga ficam no cofre (Vault), nunca nesta tabela.
create table if not exists cargas (
  id bigint generated always as identity primary key,
  tenant_id text not null references tenants (id),
  fonte_id bigint not null references fontes (id),
  saas text not null,
  entidade text not null,
  variaveis jsonb not null default '{}',
  chave text not null default 'id',
  modo text not null default 'real' check (modo in ('real', 'sandbox')),
  hora int not null default 6 check (hora between 0 and 23),      -- hora local (America/Sao_Paulo)
  cota_diaria int check (cota_diaria is null or cota_diaria > 0), -- requisições/dia do contrato do cliente
  marca_dagua double precision,                                   -- epoch do início da última carga boa
  ultima_execucao double precision,
  ultimo_status text not null default 'nunca' check (ultimo_status in ('nunca', 'ok', 'falhou', 'cota')),
  ultimo_aviso text not null default '',
  dia_cota text not null default '',
  chamadas_no_dia int not null default 0,
  ativa boolean not null default true,
  criado_em timestamptz not null default now()
);
alter table cargas enable row level security;
create policy cargas_le on cargas for select using (tenant_id = meu_tenant());
create policy cargas_admin_cria on cargas for insert with check (tenant_id = meu_tenant() and meu_papel() = 'admin');
-- O executor grava o resultado em nome do sistema (claims de admin do tenant da carga).
create policy cargas_admin_atualiza on cargas for update
  using (tenant_id = meu_tenant() and meu_papel() = 'admin') with check (tenant_id = meu_tenant());
create index if not exists cargas_tenant on cargas (tenant_id);
revoke all on cargas from anon, authenticated;
grant select, insert, update on cargas to authenticated;
grant usage on all sequences in schema public to authenticated;
