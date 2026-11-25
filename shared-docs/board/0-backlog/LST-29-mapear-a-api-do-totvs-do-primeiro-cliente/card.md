---
chave: LST-29
jira: https://adelecrm.atlassian.net/browse/LST-29
secao: INT
status: backlog
especialista: pesquisador-de-apis
---

# Mapear a API do TOTVS do primeiro cliente que usar (Protheus, RM ou Datasul)

**Por quê:** saiu do LST-10. "TOTVS" é uma família de produtos, e a API roda no servidor de cada cliente, com versão e rotas próprias. Em 25/11, o guia oficial (api.totvs.com.br) respondeu 503, e a TDN bloqueia acesso automatizado (Cloudflare). Mapear de memória contrariaria a regra de confiança honesta do catálogo.

## Critérios de aceite

- [ ] Produto e versão do TOTVS do cliente identificados no piloto
- [ ] Contrato no catálogo a partir da documentação oficial do produto (guia de API TOTVS ou o Swagger do próprio servidor do cliente), com a confiança registrada
- [ ] Simulador, teste e coleção Postman rodando no Newman, como os demais

## Verificação

`uv run pytest -q tests/test_saas.py` + Newman contra /sandbox.
