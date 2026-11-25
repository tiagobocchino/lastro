---
chave: LST-28
jira: https://adelecrm.atlassian.net/browse/LST-28
secao: NUC
status: a-fazer
tipo: bug
especialista: auditor
---

# Gravar o parecer do revisor na aprovação

**Por quê:** no teste em tela de 25/11, o revisor escreveu o parecer e aprovou, mas a tela mostrou "(sem parecer)". O parecer é a evidência da camada 2.

## Critérios de aceite

- [ ] Reproduzir (ou descartar como falha do roteiro de teste) com evidência
- [ ] Parecer digitado aparece na demanda aprovada e no rastro dos agentes
- [ ] Teste automatizado da API cobrindo o parecer

## Verificação

`uv run pytest -q` + passeio Playwright do portal.
