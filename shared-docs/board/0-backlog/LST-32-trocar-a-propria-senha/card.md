---
chave: LST-32
jira: https://adelecrm.atlassian.net/browse/LST-32
secao: NUC
status: backlog
especialista: engenheiro-backend
---

# Permitir que o usuário troque a própria senha no portal

**Por quê:** o primeiro admin de produção foi criado com uma senha provisória gerada pelo Claude, e não existe tela para trocá-la. Cliente novo vai precisar disso no piloto.

## Critérios de aceite

- [ ] Tela "minha conta" com senha atual + nova senha (mínimo 12 caracteres)
- [ ] Rota que exige a senha atual e grava só o hash (scrypt)
- [ ] Admin consegue gerar senha provisória para um usuário da própria empresa, que precisa ser trocada no primeiro login
- [ ] Teste: senha atual errada é recusada; outro tenant não troca senha de ninguém

## Verificação

`uv run pytest -q` + QA em tela.
