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

- [x] Verificação de /saude a cada 5 min, feita pelo próprio Supabase (pg_cron + pg_net), com alerta por e-mail via Resend
- [x] Alerta de taxa de erro 5xx: a API registra requisições e erros por hora; acima de 5% (com 20+ requisições na hora) vira e-mail
- [x] Keepalive do Supabase: a verificação a cada 5 min passa pelo banco (`/saude` faz ping), então o projeto nunca fica 7 dias parado
- [x] Alerta de limite gratuito: banco acima de 80% de 500 MB ou Storage acima de 80% de 1 GB
- [x] Painel de operação em Python (HTML estático, gratuito): requisições e erros por dia, disponibilidade, demandas por dia, uso do limite gratuito, alertas
- [x] Os mesmos números num schema `painel` com usuário só de leitura, para qualquer BI (Power BI, Looker Studio) se conectar
- [x] Chave do Resend e e-mail de destino só no Vault; nada em arquivo versionado

## Decisões (Tiago, 25/11)

- Alertas por Resend (conta gratuita, 3.000 e-mails/mês).
- Dashboards do nosso sistema em Python; Looker Studio no pior caso. A visão de BI para os clientes virou LST-33, LST-34 e LST-35.

## Verificação

`uv run pytest -q` (com Postgres) + painel gerado contra o Supabase real + alerta de teste chegando no e-mail.

## Evidência (25/11)

**Commits:** `3271fc3` e `b4b5d25` na `main`.

**Migrações aplicadas no Supabase `lastro-teste`:**
- **0006:** tabelas em `interno`, funções de verificação e alerta, schema `painel` e papel `painel_leitor` sem login.
- **0007:** job `lastro-monitor` a cada 5 minutos. O `lastro-acordar` saiu, porque a verificação já mantém o Render acordado.
- `cron.job` em produção: `lastro-cargas` (minuto 17) e `lastro-monitor` (`*/5`).

**Primeira verificação real:** `/saude` respondeu 200 com `"banco":"ok"` e ficou registrada em `interno.verificacoes`. A advisora de segurança do Supabase não acusou nada novo.

**Testes:** suíte completa com 219 passed, com Postgres.
- `tests/test_monitoramento.py`: contagem de 4xx e 5xx, `/saude` e `/web` fora da conta, falha ao gravar a métrica sem derrubar a resposta, painel desenhado e texto escapado.
- `tests/test_postgres.py`:
  - duas falhas seguidas abrem `fora_do_ar`, e a volta fecha o alerta e manda o e-mail pelo Resend (com o pg_net simulado);
  - um pedido sem resposta vira falha;
  - 5xx acima de 5% e banco cheio abrem alerta;
  - `painel_leitor` só lê as views: nada de `interno`, `usuarios`, Vault ou `monitorar()`, e não tem login.

**QA do painel** (dados de 30 dias semeados no Postgres local): em 375 px e 1440 px, nos temas claro e escuro, sem rolagem horizontal. Prints em `evidencias/`.

**Achado:** os textos do eixo dentro do SVG escalavam com a largura, grandes no desktop e minúsculos no celular. Passaram para HTML.

## Falta (Tiago)

1. Ligar o Resend: são 5 minutos, passo a passo em `docs/infra/monitoramento.md`. A chave vai direto no Vault, pelo SQL Editor.
2. Rodar `select interno.enviar_alerta('[Lastro] teste', 'ok')` e confirmar que o e-mail chegou. Com isso o card fecha.
