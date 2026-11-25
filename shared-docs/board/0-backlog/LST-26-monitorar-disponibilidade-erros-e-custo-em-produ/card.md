---
chave: LST-26
jira: https://adelecrm.atlassian.net/browse/LST-26
secao: OPS
status: backlog
especialista: engenheiro-backend
---

# Monitorar disponibilidade, erros e custo em produção

**Por quê:** Com escala a zero e planos gratuitos, queda ou cobrança precisam avisar antes do cliente.

## Critérios de aceite

- [ ] Verificação de /saude a cada 5 min com alerta por e-mail
- [ ] Alerta de taxa de erro 5xx
- [ ] Keepalive diário do Supabase pelo Cloud Scheduler
- [ ] Painel no Looker Studio: demandas por dia, custo do mês

## Verificação

Comandos da seção OPS em `docs/agents/secoes.yaml` + os critérios acima.

## Situação

Bloqueado por LST-22.
