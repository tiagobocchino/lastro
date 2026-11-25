---
chave: LST-27
jira: https://adelecrm.atlassian.net/browse/LST-27
secao: NUC
status: a-fazer
tipo: bug
especialista: analista-de-dados
---

# Sugerir o filtro que a pergunta pede no grill (ex.: "contratos fechados")

**Por quê:** no teste em tela de 25/11, a pergunta "Quanto cada vendedor vendeu ... nos contratos fechados?" saiu com filtro "nenhum" ao aceitar as sugestões, e o total (14.030.477,92) somou todos os status.

## Critérios de aceite

- [ ] Quando a pergunta cita um valor que existe numa coluna categórica da fonte, o grill sugere esse filtro
- [ ] Sem valor citado, a sugestão continua "nenhum"
- [ ] Teste automatizado cobrindo os dois casos
- [ ] Passeio em tela: aceitando as sugestões, o total bate com a soma só dos fechados

## Verificação

`uv run pytest -q` + passeio Playwright do portal.
