---
chave: LST-22
jira: https://adelecrm.atlassian.net/browse/LST-22
secao: OPS
status: bloqueado
especialista: engenheiro-backend
---

# Publicar a API no Render com cargas pelo GitHub Actions (plano B)

**Por quê:** sem cartão no Google (`OR_BACR2_59`), a v1 vai ao ar no Render gratuito (ADR 0009).

## Critérios de aceite

- [ ] Serviço web gratuito no Render a partir do Dockerfile (LST-20); `/saude` = 200
- [ ] Variáveis só no painel do Render: LASTRO_AMBIENTE=producao, LASTRO_SEGREDO, LASTRO_BANCO_URL, LASTRO_TAREFA_SEGREDO, LASTRO_URL_PUBLICA e as do Storage (LST-30)
- [ ] GitHub Actions agendado no minuto 17 de cada hora chamando POST /tarefas/cargas; o mesmo job mantém o Supabase acordado
- [ ] Migrações 0001 a 0003 no projeto Supabase de produção

## Verificação

`curl https://<servico>.onrender.com/saude` = 200 + uma execução do job registrada no rastro.

Passos manuais do Tiago: criar a conta no Render, ligar o repositório e colar as variáveis.

## Preparado (25/11)

- `render.yaml` (Blueprint): serviço Docker gratuito em virginia, com health check `/saude`. `LASTRO_SEGREDO` e `LASTRO_TAREFA_SEGREDO` são gerados pelo Render; banco, Storage e URL pública são pedidos no painel (`sync: false`). Nenhum valor no repositório.
- `.github/workflows/cargas.yml`: agendado no minuto 17 de cada hora e também manual. Aprovado pelo actionlint. Testado contra a API local (resposta `{"executadas":0,…}`). Sem os segredos, só registra um aviso e não falha.
- Passo a passo: `docs/infra/render-passo-a-passo.md`. O banco da v1 é o `lastro-teste`, que já tem as migrações 0001 a 0003 e o bucket.

## Bloqueio

Passos do Tiago: conta no Render, Blueprint com os 4 valores, os 2 segredos no GitHub e mandar o endereço do serviço.
