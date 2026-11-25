---
chave: LST-20
jira: https://adelecrm.atlassian.net/browse/LST-20
secao: OPS
status: pronto
especialista: engenheiro-backend
---

# Empacotar a API em container com health check

**Por quê:** O Cloud Run roda containers; o mesmo container serve local e produção.

## Critérios de aceite

- [ ] Dockerfile com uv, usuário sem root, porta por $PORT
- [ ] GET /saude responde 200 com versão e estado do banco
- [ ] Modelo de embeddings fora da imagem
- [ ] docker build/run locais passam; imagem abaixo de 500 MB

## Verificação

Comandos da seção OPS em `docs/agents/secoes.yaml` + os critérios acima.
