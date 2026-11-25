---
chave: LST-28
jira: https://adelecrm.atlassian.net/browse/LST-28
secao: NUC
status: feito
tipo: bug
especialista: auditor
---

# Gravar o parecer do revisor na aprovação

**Por quê:** no teste em tela de 25/11, o revisor escreveu o parecer e aprovou, mas a tela mostrou "(sem parecer)". O parecer é a evidência da camada 2.

## Critérios de aceite

- [x] Reproduzir (ou descartar como falha do roteiro de teste) com evidência
- [x] Parecer digitado aparece na demanda aprovada e no rastro dos agentes
- [x] Teste automatizado da API cobrindo o parecer

## Verificação

`uv run pytest -q` + passeio Playwright do portal.

## Evidência (25/11)

- Causa: o roteiro Playwright preencheu o parecer antes da segunda renderização da demanda; o backend grava certo.
- Teste novo `test_parecer_do_revisor_fica_gravado` passa.
- Passeio refeito com espera: "rui@demo.lastro aprovou: Números conferem com o notebook; regra de status correta."
