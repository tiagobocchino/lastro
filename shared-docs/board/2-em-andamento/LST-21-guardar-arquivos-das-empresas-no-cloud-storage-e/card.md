---
chave: LST-21
jira: https://adelecrm.atlassian.net/browse/LST-21
secao: OPS
status: em-andamento
especialista: engenheiro-de-dados
---

# Guardar arquivos das empresas no Cloud Storage e isolar o sandbox

**Por quê:** O disco do Cloud Run é temporário e o sandbox precisa de uma segunda trava além da lista de funções (LST-17).

## Critérios de aceite

- [ ] Arquivos em gs://<bucket>/tenants/<tenant>/
- [ ] Consultas de agente com enable_external_access=false
- [ ] Teste: um tenant não lê arquivo de outro mesmo burlando a trava
- [ ] Modo local (disco) continua funcionando

## Verificação

Comandos da seção OPS em `docs/agents/secoes.yaml` + os critérios acima.
