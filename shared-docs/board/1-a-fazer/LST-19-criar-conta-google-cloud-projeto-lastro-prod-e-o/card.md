---
chave: LST-19
jira: https://adelecrm.atlassian.net/browse/LST-19
secao: OPS
status: pronto
especialista: engenheiro-backend
---

# Criar conta Google Cloud, projeto lastro-prod e orçamento com alerta

**Por quê:** O Google exige conta de faturamento até para a camada gratuita; sem alerta, um erro vira cobrança.

## Critérios de aceite

- [ ] Projeto lastro-prod ligado à conta de faturamento
- [ ] Orçamento com alertas em R$ 1 e R$ 10
- [ ] APIs habilitadas: Cloud Run, Cloud Storage, Secret Manager, Cloud Scheduler, Artifact Registry
- [ ] Passo a passo pela skill wizard (cartão e termos são do Tiago)

## Verificação

Comandos da seção OPS em `docs/agents/secoes.yaml` + os critérios acima.
