-- Lastro · 0004: o próprio Supabase dispara as cargas agendadas (plano C da ADR 0009, card LST-22).
-- O GitHub Actions recusou o disparo (HTTP 500, nenhuma execução agendada); o workflow fica como reserva.
-- Endereço e segredo da tarefa vêm do Vault (nomes lastro_url_api e lastro_tarefa_segredo); nada em texto aqui.
create extension if not exists pg_cron;
create extension if not exists pg_net with schema extensions;  -- fora do public (aviso do verificador do Supabase)

-- Schema fora da API pública do Supabase (PostgREST só expõe public e graphql_public).
create schema if not exists interno;
revoke all on schema interno from public, anon, authenticated;

create or replace function interno.segredo(nome text) returns text
language sql stable security definer set search_path = '' as $$
  select decrypted_secret from vault.decrypted_secrets where name = nome
$$;

-- Minuto 12: acorda o Render (o plano gratuito dorme após 15 minutos e leva ~1 minuto para voltar).
create or replace function interno.acordar_lastro() returns bigint
language plpgsql security definer set search_path = '' as $$
declare url text := interno.segredo('lastro_url_api');
begin
  if url is null then
    raise notice 'lastro_url_api ausente no Vault';
    return null;
  end if;
  return net.http_get(url := url || '/saude', timeout_milliseconds := 120000);
end $$;

-- Minuto 17: dispara as cargas que estão na hora (POST /tarefas/cargas com o segredo da tarefa).
create or replace function interno.disparar_cargas() returns bigint
language plpgsql security definer set search_path = '' as $$
declare
  url text := interno.segredo('lastro_url_api');
  seg text := interno.segredo('lastro_tarefa_segredo');
begin
  if url is null or seg is null then
    raise notice 'lastro_url_api ou lastro_tarefa_segredo ausente no Vault';
    return null;
  end if;
  return net.http_post(
    url := url || '/tarefas/cargas',
    body := '{}'::jsonb,
    headers := jsonb_build_object('X-Lastro-Tarefa', seg, 'Content-Type', 'application/json'),
    timeout_milliseconds := 120000
  );
end $$;

revoke all on all functions in schema interno from public, anon, authenticated;

-- Reagenda sem duplicar (cron.schedule com o mesmo nome substitui o job).
select cron.schedule('lastro-acordar', '12 * * * *', 'select interno.acordar_lastro()');
select cron.schedule('lastro-cargas', '17 * * * *', 'select interno.disparar_cargas()');
