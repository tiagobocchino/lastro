-- Lastro · 0005: senha provisória que precisa ser trocada no primeiro login (card LST-32).
alter table usuarios add column if not exists trocar_senha boolean not null default false;
