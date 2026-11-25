---
chave: LST-7
jira: https://adelecrm.atlassian.net/browse/LST-7
secao: NUC
status: em-andamento
especialista: engenheiro-de-dados
---

# Agendar cargas incrementais por conector (plano Operação)

**Por quê:** O empresário quer o número de hoje sem pedir de novo.

## Critérios de aceite

- [ ] Agenda por fonte com marca d'água da última data
- [ ] Execução respeita a cota diária do contrato (ex.: Sienge Free 100/dia)
- [ ] Falha vira aviso no portal, sem carga parcial na gold

## Verificação

Comandos da seção NUC em `docs/agents/secoes.yaml` + os critérios acima.
