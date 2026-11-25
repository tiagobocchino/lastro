# ADR 0002: Somente leitura garantida na credencial, trava de SQL como segunda linha

**Status:** aceito · 2026-11-25

## Decisão

Cada conector abre a fonte primária em modo leitura (SQLite `mode=ro`, arquivos lidos como views, banco com usuário só de SELECT, IAM e OAuth com escopo de leitura). Toda consulta de agente passa ainda por `somente_leitura.verificar` (uma instrução, só SELECT/WITH/DESCRIBE, sem palavras de escrita). Escrita só acontece no sandbox DuckDB e no staging da demanda.

## Por quê

Prompt não é controle de acesso. Um agente que erre ou seja induzido a erro continua sem conseguir alterar a fonte.
