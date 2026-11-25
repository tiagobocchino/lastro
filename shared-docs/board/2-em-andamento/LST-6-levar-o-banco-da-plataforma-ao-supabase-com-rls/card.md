---
chave: LST-6
jira: https://adelecrm.atlassian.net/browse/LST-6
secao: NUC
status: em-andamento
especialista: engenheiro-backend
---

# Levar o banco da plataforma ao Supabase com RLS

**Por quê:** Piloto com mais de uma empresa precisa de isolamento no banco, não só no código.

## Critérios de aceite

- [ ] Migração supabase/migrations/0001 aplicada num projeto de teste
- [ ] Usuário de um tenant não lê linha de outro (teste com dois JWTs)
- [ ] Repo local e Supabase atrás da mesma interface

## Verificação

Comandos da seção NUC em `docs/agents/secoes.yaml` + os critérios acima.
