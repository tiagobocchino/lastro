-- Lastro · 0006: monitoramento de produção (card LST-26, plano B/C da ADR 0009).
-- O Supabase verifica a API a cada 5 minutos, avalia erros e limites gratuitos e manda e-mail pelo Resend.
-- A agenda fica na 0007. Chave do Resend e e-mail de destino vêm do Vault
-- (lastro_resend_chave, lastro_alerta_email); nada em texto aqui.

create schema if not exists interno;
revoke all on schema interno from public, anon, authenticated;

-- Requisições da API por hora: a própria API grava (conexão do dono, uma linha por hora).
create table if not exists interno.metricas_api (
  hora timestamptz primary key,
  requisicoes integer not null default 0,
  erros_4xx integer not null default 0,
  erros_5xx integer not null default 0,
  latencia_ms bigint not null default 0
);

-- Cada verificação de /saude feita pelo Supabase (pg_net é assíncrono: a resposta é colhida na rodada seguinte).
create table if not exists interno.verificacoes (
  id bigserial primary key,
  pedido bigint,
  em timestamptz not null default now(),
  status_http integer,
  ok boolean,
  resolvida boolean not null default false
);
create index if not exists verificacoes_em on interno.verificacoes (em desc);

-- Um alerta fica aberto até a condição passar; abrir e fechar mandam um e-mail cada.
create table if not exists interno.alertas (
  id bigserial primary key,
  tipo text not null,
  detalhe text not null,
  aberto_em timestamptz not null default now(),
  fechado_em timestamptz
);
create unique index if not exists alertas_um_aberto_por_tipo on interno.alertas (tipo) where fechado_em is null;

create table if not exists interno.emails (
  id bigserial primary key,
  em timestamptz not null default now(),
  assunto text not null,
  pedido bigint,
  enviado boolean not null
);

-- Limites ajustáveis sem nova migração (update interno.limites set valor = ... where nome = ...).
create table if not exists interno.limites (nome text primary key, valor numeric not null, descricao text not null);
insert into interno.limites (nome, valor, descricao) values
  ('banco_mb', 500, 'banco do plano gratuito do Supabase'),
  ('storage_mb', 1024, 'Storage do plano gratuito do Supabase'),
  ('uso_alerta', 0.8, 'fração do limite que dispara o alerta'),
  ('taxa_5xx', 0.05, 'fração de respostas 5xx na última hora que dispara o alerta'),
  ('minimo_requisicoes', 20, 'abaixo disso na hora, a taxa de 5xx não é avaliada'),
  ('falhas_seguidas', 2, 'verificações de /saude seguidas com falha para dizer que a API caiu')
on conflict (nome) do nothing;

create or replace function interno.limite(n text) returns numeric
language sql stable security definer set search_path = '' as $$ select valor from interno.limites where nome = n $$;

create or replace function interno.segredo(nome text) returns text
language sql stable security definer set search_path = '' as $$
  select decrypted_secret from vault.decrypted_secrets where name = nome
$$;

-- Uso do Storage: storage.objects só existe no Supabase; fora dele, zero.
create or replace function interno.storage_mb() returns numeric
language plpgsql stable security definer set search_path = '' as $$
declare mb numeric := 0;
begin
  if to_regclass('storage.objects') is not null then
    execute 'select coalesce(sum((metadata->>''size'')::bigint), 0) / 1048576.0 from storage.objects' into mb;
  end if;
  return round(mb, 2);
end $$;

create or replace function interno.enviar_alerta(assunto text, texto text) returns bigint
language plpgsql security definer set search_path = '' as $$
declare
  chave text := interno.segredo('lastro_resend_chave');
  para text := interno.segredo('lastro_alerta_email');
  pedido bigint;
begin
  if chave is null or para is null then  -- sem Resend configurado: o alerta fica só na tabela e no painel
    insert into interno.emails (assunto, enviado) values (assunto, false);
    return null;
  end if;
  pedido := net.http_post(
    url := 'https://api.resend.com/emails',
    body := jsonb_build_object('from', 'Lastro <onboarding@resend.dev>', 'to', jsonb_build_array(para),
                               'subject', assunto, 'text', texto),
    headers := jsonb_build_object('Authorization', 'Bearer ' || chave, 'Content-Type', 'application/json'),
    timeout_milliseconds := 30000
  );
  insert into interno.emails (assunto, pedido, enviado) values (assunto, pedido, true);
  return pedido;
end $$;

-- Colhe as respostas pendentes e dispara a verificação desta rodada.
create or replace function interno.verificar_saude() returns bigint
language plpgsql security definer set search_path = '' as $$
declare url text := interno.segredo('lastro_url_api');
begin
  update interno.verificacoes v
     set status_http = r.status_code,
         ok = coalesce(r.status_code = 200 and r.content like '%"banco":"ok"%', false),
         resolvida = true
    from net._http_response r
   where r.id = v.pedido and not v.resolvida;
  -- pedido sem resposta depois de 3 minutos conta como falha (timeout que o pg_net não registrou)
  update interno.verificacoes set ok = false, resolvida = true where not resolvida and em < now() - interval '3 minutes';
  delete from interno.verificacoes where em < now() - interval '90 days';
  if url is null then
    raise notice 'lastro_url_api ausente no Vault';
    return null;
  end if;
  insert into interno.verificacoes (pedido)
  values (net.http_get(url := url || '/saude', timeout_milliseconds := 90000));
  return currval('interno.verificacoes_id_seq');
end $$;

create or replace function interno._abrir_ou_fechar(tipo_ text, ativo boolean, detalhe_ text) returns integer
language plpgsql security definer set search_path = '' as $$
declare aberto bigint;
begin
  select id into aberto from interno.alertas where tipo = tipo_ and fechado_em is null;
  if ativo and aberto is null then
    insert into interno.alertas (tipo, detalhe) values (tipo_, detalhe_);
    perform interno.enviar_alerta('[Lastro] alerta: ' || detalhe_, detalhe_ || E'\n\nPainel: uv run lastro painel');
    return 1;
  elsif not ativo and aberto is not null then
    update interno.alertas set fechado_em = now() where id = aberto;
    perform interno.enviar_alerta('[Lastro] normalizado: ' || tipo_, 'A condição "' || tipo_ || '" voltou ao normal.');
    return 1;
  end if;
  return 0;
end $$;

-- Avalia as quatro condições e devolve quantos alertas abriram ou fecharam nesta rodada.
create or replace function interno.avaliar_alertas() returns integer
language plpgsql security definer set search_path = '' as $$
declare
  n integer := 0;
  seguidas integer := interno.limite('falhas_seguidas')::integer;
  falhas integer;
  req integer;
  e5 integer;
  banco numeric := round(pg_database_size(current_database()) / 1048576.0, 2);
  stor numeric := interno.storage_mb();
begin
  select count(*) filter (where not ok) into falhas
    from (select ok from interno.verificacoes where resolvida order by em desc limit seguidas) u;
  n := n + interno._abrir_ou_fechar('fora_do_ar', falhas >= seguidas,
    format('a API não respondeu ok em %s verificações seguidas de /saude', seguidas));

  select coalesce(sum(requisicoes), 0), coalesce(sum(erros_5xx), 0) into req, e5
    from interno.metricas_api where hora >= now() - interval '1 hour';
  n := n + interno._abrir_ou_fechar('erros_5xx',
    req >= interno.limite('minimo_requisicoes') and e5 > interno.limite('taxa_5xx') * req,
    format('%s de %s requisições com erro 5xx na última hora', e5, req));

  n := n + interno._abrir_ou_fechar('banco_cheio', banco > interno.limite('uso_alerta') * interno.limite('banco_mb'),
    format('banco com %s MB de %s MB do plano gratuito', banco, interno.limite('banco_mb')));
  n := n + interno._abrir_ou_fechar('storage_cheio', stor > interno.limite('uso_alerta') * interno.limite('storage_mb'),
    format('Storage com %s MB de %s MB do plano gratuito', stor, interno.limite('storage_mb')));
  return n;
end $$;

create or replace function interno.monitorar() returns integer
language plpgsql security definer set search_path = '' as $$
begin
  perform interno.verificar_saude();
  return interno.avaliar_alertas();
end $$;

revoke all on all functions in schema interno from public, anon, authenticated;
revoke all on all tables in schema interno from public, anon, authenticated;

-- ---- painel: os números da operação para o Python (lastro painel) e para qualquer BI -------------
-- Schema fora da API pública; o BI entra com o usuário painel_leitor (só SELECT nestas views).
create schema if not exists painel;
revoke all on schema painel from public, anon, authenticated;

create or replace view painel.requisicoes_dia as
select (hora at time zone 'America/Sao_Paulo')::date as dia,
       sum(requisicoes)::integer as requisicoes, sum(erros_4xx)::integer as erros_4xx, sum(erros_5xx)::integer as erros_5xx,
       round(sum(erros_5xx)::numeric / nullif(sum(requisicoes), 0), 4) as taxa_5xx,
       round(sum(latencia_ms)::numeric / nullif(sum(requisicoes), 0), 1) as latencia_media_ms
  from interno.metricas_api group by 1;

create or replace view painel.disponibilidade_dia as
select (em at time zone 'America/Sao_Paulo')::date as dia,
       count(*)::integer as verificacoes, count(*) filter (where ok)::integer as ok,
       round(100.0 * count(*) filter (where ok) / count(*), 2) as disponibilidade_pct
  from interno.verificacoes where resolvida group by 1;

create or replace view painel.demandas_dia as
select (criado_em at time zone 'America/Sao_Paulo')::date as dia, tenant_id as empresa, status, count(*)::integer as demandas
  from public.demandas group by 1, 2, 3;

create or replace view painel.cargas as
select tenant_id as empresa, saas, entidade, ativa, ultimo_status, ultimo_aviso,
       to_timestamp(ultima_execucao) as ultima_execucao, to_timestamp(marca_dagua) as ultima_carga_boa
  from public.cargas;

create or replace view painel.uso_gratuito as
select 'banco'::text as recurso, round(pg_database_size(current_database()) / 1048576.0, 2) as usado_mb,
       interno.limite('banco_mb') as limite_mb
union all
select 'storage', interno.storage_mb(), interno.limite('storage_mb');

create or replace view painel.alertas as
select tipo, detalhe, aberto_em, fechado_em, fechado_em is null as aberto from interno.alertas;

-- Papel do BI: sem login até o Tiago dar uma senha (docs/infra/monitoramento.md).
do $$ begin
  if not exists (select 1 from pg_roles where rolname = 'painel_leitor') then create role painel_leitor nologin; end if;
end $$;
grant usage on schema painel to painel_leitor;
grant select on all tables in schema painel to painel_leitor;
-- Funções chamadas por uma view são checadas com o papel de quem consulta: o BI precisa poder chamá-las.
grant usage on schema interno to painel_leitor;
grant execute on function interno.limite(text), interno.storage_mb() to painel_leitor;
