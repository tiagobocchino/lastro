---
chave: LST-35
jira: https://adelecrm.atlassian.net/browse/LST-35
secao: NUC
status: a-fazer
especialista: engenheiro-backend
---

# Agente interpreta bases e dashboards para usar nas conversas e nos insights

**Por quê:** o operador conversa com o agente sobre o que está nas bases e nos painéis; o agente precisa ler esse conteúdo e devolver insights com prova (consulta e número conferível), sem alterar a fonte.

## Critérios de aceite

- [ ] O agente lê a gold, os relatórios e as definições dos painéis (Python e PBIP) da empresa
- [ ] Cada insight vem com a consulta que o sustenta e passa pela auditoria de duas camadas
- [ ] Só leitura: nenhuma escrita na fonte ou no BI do cliente
- [ ] Teste: insight sem prova é recusado; dado de outra empresa nunca entra no contexto

## Verificação

`uv run pytest -q` + uma conversa de ponta a ponta no portal.

## Origem

Visão do Tiago em 25/11: o Lastro conecta bases e APIs aos BIs self-service; nosso próprio sistema e os exemplos do site usam dashboards em Python (gratuito), e Looker Studio no pior caso.
