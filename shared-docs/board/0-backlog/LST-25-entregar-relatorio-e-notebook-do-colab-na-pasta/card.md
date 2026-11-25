---
chave: LST-25
jira: https://adelecrm.atlassian.net/browse/LST-25
secao: OPS
status: backlog
especialista: engenheiro-backend
---

# Entregar relatório e notebook do Colab na pasta do cliente no Drive

**Por quê:** O revisor trabalha no Drive e no Colab dele; baixar e reenviar arquivo atrasa a camada 2.

## Critérios de aceite

- [ ] Uma pasta por empresa, compartilhada com o revisor
- [ ] Lastro grava relatório e notebook com escopo drive.file
- [ ] Notebook abre direto no Colab pelo link do e-mail
- [ ] Teste no sandbox com pasta fictícia

## Verificação

Comandos da seção OPS em `docs/agents/secoes.yaml` + os critérios acima.

## Situação

Bloqueado por LST-22.
