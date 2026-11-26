-- LST-48 · BI sem atrito C: a planilha Google do cliente que recebe as tabelas prontas do BI.
-- O token do Google fica no cofre (Vault); aqui só o id da planilha e quando foi enviada.
alter table interno.bi_acessos
  add column if not exists planilha_id text check (planilha_id is null or planilha_id ~ '^[A-Za-z0-9_-]{20,100}$'),
  add column if not exists planilha_enviada_em timestamptz;
