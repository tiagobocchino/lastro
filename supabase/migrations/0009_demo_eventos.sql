-- Lastro · 0009: funil anônimo da demonstração do site (card LST-44).
-- Sem IP, sem nome de coluna, sem valor: só etapa, tempo, faixa de tamanho, nº de colunas, formato e motivo.
-- Etapa, formato, faixa e motivo só aceitam valores de lista fechada (a rota de clique é pública).
create schema if not exists interno;
create table if not exists interno.demo_eventos (
  id bigserial primary key,
  em timestamptz not null default now(),
  etapa text not null check (etapa in ('subiu', 'recusou', 'painel', 'painel_falhou', 'desistiu', 'clicou_contato')),
  duracao_ms integer,
  faixa_tamanho text check (faixa_tamanho in ('até 100 KB', '100 KB a 1 MB', '1 a 5 MB')),
  n_colunas integer check (n_colunas between 0 and 10000),
  visual text check (visual in ('ranking', 'tabela', 'evolucao', 'numero')),
  motivo text check (motivo in ('formato', 'tamanho', 'linhas', 'leitura', 'limite_ip', 'fila', 'prazo'))
);
create index if not exists demo_eventos_em on interno.demo_eventos (em desc);
revoke all on interno.demo_eventos from public, anon, authenticated;

create or replace view painel.demo_funil_dia as
select (em at time zone 'America/Sao_Paulo')::date as dia,
       count(*) filter (where etapa = 'subiu')::integer as subiram,
       count(*) filter (where etapa = 'painel')::integer as paineis,
       count(*) filter (where etapa = 'clicou_contato')::integer as clicaram,
       count(*) filter (where etapa = 'recusou')::integer as recusas,
       count(*) filter (where etapa = 'desistiu')::integer as desistencias,
       round(avg(duracao_ms) filter (where etapa = 'painel'))::integer as ms_medio_painel
  from interno.demo_eventos group by 1;
grant select on painel.demo_funil_dia to painel_leitor;
