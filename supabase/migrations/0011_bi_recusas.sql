-- LST-47: por que uma leitura do BI por HTTPS foi recusada, sem guardar a chave (diagnóstico do suporte).
create table if not exists interno.bi_recusas (
  id bigserial primary key,
  quando timestamptz not null default now(),
  motivo text not null check (motivo in ('sem_cabecalho', 'prefixo', 'desconhecida')),
  agente text
);
revoke all on interno.bi_recusas from public, anon, authenticated;
