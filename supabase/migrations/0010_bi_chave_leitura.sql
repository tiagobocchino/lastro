-- LST-47 · BI sem atrito B: chave de leitura do BI por empresa, para o Power BI ler o gold por HTTPS
-- (sem certificado do Supabase e sem gateway). Só o hash fica no banco; a chave aparece uma vez no portal.
alter table interno.bi_acessos
  add column if not exists chave_hash text unique check (chave_hash is null or chave_hash ~ '^[a-f0-9]{64}$'),
  add column if not exists chave_criada_em timestamptz,
  add column if not exists chave_usada_em timestamptz;
