-- Lastro · 0008: acesso de BI por empresa (card LST-33).
-- Cada empresa que liga o BI ganha um schema e um papel com o mesmo nome opaco (bi_<aleatório>):
-- o nome não diz de qual empresa é, porque qualquer papel consegue listar schemas e papéis do banco.
-- O papel só tem SELECT no próprio schema, roda em modo só leitura e não alcança public, interno nem o Vault.
-- Os papéis e schemas em si são criados pelo backend (lastro/bi.py); aqui fica só o registro.
create schema if not exists interno;
create table if not exists interno.bi_acessos (
  tenant_id text primary key references public.tenants(id) on delete cascade,
  nome text not null unique check (nome ~ '^bi_[a-f0-9]{10}$'),
  ativo boolean not null default true,
  criado_em timestamptz not null default now(),
  senha_trocada_em timestamptz not null default now(),
  publicado_em timestamptz,
  tabelas jsonb not null default '[]'::jsonb
);
revoke all on interno.bi_acessos from public, anon, authenticated;
