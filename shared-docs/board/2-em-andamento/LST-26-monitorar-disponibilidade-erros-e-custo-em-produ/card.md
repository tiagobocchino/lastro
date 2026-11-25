---
chave: LST-26
jira: https://adelecrm.atlassian.net/browse/LST-26
secao: OPS
status: em-andamento
especialista: engenheiro-backend
---

# Monitorar disponibilidade, erros e custo em produção

**Por quê:** Com escala a zero e planos gratuitos, queda ou cobrança precisam avisar antes do cliente.

## Critérios de aceite (revistos em 25/11 para o plano B/C: Render + Supabase, sem Google Cloud)

- [ ] Verificação de /saude a cada 5 min, feita pelo próprio Supabase (pg_cron + pg_net), com alerta por e-mail via Resend
- [ ] Alerta de taxa de erro 5xx: a API registra requisições e erros por hora; acima de 5% (com 20+ requisições na hora) vira e-mail
- [ ] Keepalive do Supabase: a verificação a cada 5 min passa pelo banco (`/saude` faz ping), então o projeto nunca fica 7 dias parado
- [ ] Alerta de limite gratuito: banco acima de 80% de 500 MB ou Storage acima de 80% de 1 GB
- [ ] Painel de operação em Python (HTML estático, gratuito): requisições e erros por dia, disponibilidade, demandas por dia, uso do limite gratuito, alertas
- [ ] Os mesmos números num schema `painel` com usuário só de leitura, para qualquer BI (Power BI, Looker Studio) se conectar
- [ ] Chave do Resend e e-mail de destino só no Vault; nada em arquivo versionado

## Decisões (Tiago, 25/11)

- Alertas por Resend (conta gratuita, 3.000 e-mails/mês).
- Dashboards do nosso sistema em Python; Looker Studio no pior caso. A visão de BI para os clientes virou LST-33, LST-34 e LST-35.

## Verificação

`uv run pytest -q` (com Postgres) + painel gerado contra o Supabase real + alerta de teste chegando no e-mail.
