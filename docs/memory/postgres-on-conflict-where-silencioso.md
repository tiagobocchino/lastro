---
type: armadilha
description: "ON CONFLICT DO UPDATE ... WHERE não falha quando o WHERE barra a linha: não grava nada e segue em silêncio"
---

# `ON CONFLICT ... WHERE` não falha: confira o `RETURNING`

**Regra:** quando um upsert no Postgres tem `WHERE` para impedir uma troca (ex.: mover um e-mail de uma empresa para outra), termine com `RETURNING` e trate o "nenhuma linha" como recusa. No SQLite o mesmo caminho levantava `PermissionError`; no Postgres o comando passava sem gravar nada.

**Why:** no LST-32, `criar_usuario(outra_empresa, "ana@acme")` "funcionava" no Postgres e o teste de isolamento só pegou porque roda nos dois bancos (`test_contas_nos_dois_bancos`).

**How to apply:** todo upsert com trava de tenant em `lastro/banco_postgres.py` usa `RETURNING` e checa `fetchone() is None`. E teste de isolamento novo vai na fixture `banco` (SQLite e Postgres) de `tests/test_postgres.py`, não só no SQLite.

Também: o Postgres local de teste não tem `pg_cron`. A fixture `url_pg` pula a migração que cria a extensão (0004); o resto das migrações roda igual.
