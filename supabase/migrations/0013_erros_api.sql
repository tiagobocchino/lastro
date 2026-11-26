-- Erros que os usuários encontraram (4xx e 5xx), para acompanhar os testes sem depender dos logs do Render (26/11).
-- Só o tipo do erro: método, rota, status e a mensagem devolvida. Nunca e-mail, token ou conteúdo de planilha.
create table if not exists interno.erros_api (
  id bigserial primary key,
  em timestamptz not null default now(),
  metodo text not null,
  rota text not null,
  status integer not null,
  mensagem text
);
create index if not exists erros_api_em on interno.erros_api (em desc);
revoke all on interno.erros_api from public, anon, authenticated;
