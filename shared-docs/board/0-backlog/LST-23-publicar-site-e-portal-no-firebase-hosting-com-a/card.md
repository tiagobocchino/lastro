---
chave: LST-23
jira: https://adelecrm.atlassian.net/browse/LST-23
secao: OPS
status: backlog
especialista: engenheiro-frontend
---

# Publicar site e portal no Firebase Hosting com /api para o Cloud Run

**Por quê:** Site e portal num endereço só, com SSL e sem custo (Vercel Hobby não permite uso comercial; ADR 0006).

## Critérios de aceite

- [ ] firebase.json: site na raiz, portal em /app, rewrite /api/** para o Cloud Run
- [ ] Domínio próprio com SSL (DNS pelo Tiago)
- [ ] Deploy pelo mesmo workflow
- [ ] QA em 375 px e 1440 px no endereço público

## Verificação

Comandos da seção OPS em `docs/agents/secoes.yaml` + os critérios acima.

## Situação

Bloqueado por LST-22.
