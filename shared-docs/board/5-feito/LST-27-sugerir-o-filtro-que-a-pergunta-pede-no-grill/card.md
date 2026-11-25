---
chave: LST-27
jira: https://adelecrm.atlassian.net/browse/LST-27
secao: NUC
status: feito
tipo: bug
especialista: analista-de-dados
---

# Sugerir o filtro que a pergunta pede no grill (ex.: "contratos fechados")

**Por quê:** no teste em tela de 25/11, a pergunta "Quanto cada vendedor vendeu ... nos contratos fechados?" saiu com filtro "nenhum" ao aceitar as sugestões, e o total (14.030.477,92) somou todos os status.

## Critérios de aceite

- [x] Quando a pergunta cita um valor que existe numa coluna categórica da fonte, o grill sugere esse filtro
- [x] Sem valor citado, a sugestão continua "nenhum"
- [x] Teste automatizado cobrindo os dois casos
- [x] Passeio em tela: aceitando as sugestões, o total bate com a soma só dos fechados

## Verificação

`uv run pytest -q` + passeio Playwright do portal.

## Evidência (25/11)

- `filtro_citado` em `lastro/agents/orquestrador.py`; o Explorador guarda os valores de colunas com até 30 categorias.
- `uv run pytest -q`: 118 passed (4 casos de sugestão + total só dos fechados).
- Passeio em tela: grill sugeriu `status = 'Fechado'` aceitando as sugestões.
