---
chave: LST-22
jira: https://adelecrm.atlassian.net/browse/LST-22
secao: OPS
status: backlog
especialista: engenheiro-backend
---

# Publicar a API no Cloud Run pelo GitHub Actions com segredos no Secret Manager

**Por quê:** Deploy reproduzível a cada merge na main, sem chave guardada no GitHub.

## Critérios de aceite

- [ ] Workflow testa, constrói e publica a cada push na main
- [ ] Workload Identity Federation, nenhuma chave JSON
- [ ] Segredos no Secret Manager; LASTRO_AMBIENTE=producao
- [ ] Máx. 2 instâncias, mín. 0; /saude = 200
- [ ] Bucket das empresas montado em /dados/tenants com LASTRO_TENANTS (ADR 0007, comando no plano de nuvem)

## Verificação

Comandos da seção OPS em `docs/agents/secoes.yaml` + os critérios acima.

## Situação

Bloqueado por LST-19, LST-20, LST-21 e LST-6.
