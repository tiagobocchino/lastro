---
chave: LST-32
jira: https://adelecrm.atlassian.net/browse/LST-32
secao: NUC
status: em-andamento
especialista: engenheiro-backend
---

# Permitir que o usuário troque a própria senha no portal

**Por quê:** o primeiro admin de produção foi criado com uma senha provisória gerada pelo Claude, e não existe tela para trocá-la. Cliente novo vai precisar disso no piloto.

## Critérios de aceite

- [x] Tela "minha conta" com senha atual + nova senha (mínimo 12 caracteres)
- [x] Rota que exige a senha atual e grava só o hash (scrypt)
- [x] Admin consegue gerar senha provisória para um usuário da própria empresa, que precisa ser trocada no primeiro login
- [x] Teste: senha atual errada é recusada; outro tenant não troca senha de ninguém

## Verificação

`uv run pytest -q` + QA em tela.

## Evidência (25/11)

Commit `d252cbc` na `main`.

**O que entrou:**
- `POST /api/conta/senha`: exige a senha atual, pede no mínimo 12 caracteres e recusa repetir a mesma. Grava só o hash scrypt e devolve um token novo.
- `GET/POST /api/usuarios` (só admin): cadastra alguém da própria empresa com senha provisória, que aparece uma única vez. Cadastrar o mesmo e-mail de novo gera outra senha, e esse é o caminho para quem esqueceu.
- Quem entra com senha provisória recebe 403 em tudo, menos na troca e em `/api/eu`, até escolher a própria senha.
- Se o e-mail já é de outra empresa, a resposta é 409 "este e-mail já está em uso", sem dizer qual empresa. Nem `criar_usuario` move um e-mail entre empresas.
- Aba **conta** no portal: troca de senha, lista da equipe, cadastro com botão de copiar e tela obrigatória no primeiro acesso.
- Migração `0005_trocar_senha` aplicada no Supabase `lastro-teste`.

**Testes:**
- `tests/test_contas.py`: 8 testes.
- `test_contas_nos_dois_bancos`: os mesmos casos no SQLite e no Postgres.
- Suíte completa: 211 passed com Postgres.

**QA em tela** (375 px e 1440 px), sem rolagem horizontal:
- senha atual errada: "senha atual incorreta";
- senha curta: "a nova senha precisa de pelo menos 12 caracteres";
- usuário convidado cai na tela obrigatória, troca a senha e entra no portal;
- admin de outra empresa tentando o mesmo e-mail recebe 409.

Print em `evidencias/obrigatoria-375.png`. O print da equipe ficou fora do git porque mostra uma senha provisória.

**Achado:** no Postgres, um upsert com `WHERE` de tenant não falha, só deixa de gravar. Virou nota em `docs/memory/postgres-on-conflict-where-silencioso.md`.

**Conhecimento durável:** `docs/memory/postgres-on-conflict-where-silencioso.md`.

**Para o Tiago:** sua senha de admin em produção já pode ser trocada pela aba conta.
