---
chave: LST-10
jira: https://adelecrm.atlassian.net/browse/LST-10
secao: INT
status: feito
especialista: pesquisador-de-apis
---

# Mapear Bling, Ploomes e TOTVS

**Por quê:** Docs baixadas em parte; são sistemas comuns entre clientes pequenos e médios.

## Critérios de aceite

- [x] Contrato no catálogo com confianca honesta (Bling e Ploomes; TOTVS foi para o LST-29)
- [x] Simulador e teste por sistema
- [x] Coleção Postman rodando no Newman

## Verificação

Comandos da seção INT em `docs/agents/secoes.yaml` + os critérios acima.

## Evidência (25/11)

**O que havia antes:** os arquivos "baixados" eram só a casca HTML dos portais (o do Ploomes era uma página 404). As especificações reais foram baixadas de novo e conferidas como JSON (`docs/fontes-saas/_bruto/bling-openapi.json`, 169 rotas; `ploomes-openapi.json`, 79 rotas; guias do Bling em `md/`).

**Bling:**
- API v3 com OAuth2 pelo mesmo `GerenteToken` do LST-9: token de 6 horas, `refresh_token` de 30 dias, app identificado por Basic, `state` obrigatório.
- Paginação por `pagina` e `limite` (100); registros em `data`, sem total.
- Limite de 3 por segundo e 120 mil por dia, que vira a cota padrão das cargas.
- Filtro incremental `dataAlteracaoInicial` só em pedidos, contatos e produtos. O motor passou a aceitar incremental por entidade (`incremental_da`).

**Ploomes:**
- `User-Key` no cabeçalho; OData `$skip`/`$top` com teto de 300; 120 por minuto.
- O envelope `value` e a ausência de campo de data de alteração ficaram registrados como "a confirmar no piloto", e por isso a carga é completa.

**TOTVS:** foi para o LST-29. O guia oficial respondeu 503, a TDN bloqueia acesso automatizado, e a API varia por produto e por cliente.

**Simulador e testes:**
- Os dois sistemas entram nos testes parametrizados do catálogo e ganharam testes próprios: o incremental do Bling só nas rotas certas, e o `$skip` 0/300/600 do Ploomes.
- Correção encontrada pelo teste: o limitador ganhou 1% de folga (3 por segundo tomava 429).
- `uv run pytest -q` com Postgres = 188 passed.

**Newman:**
- Coleções do Bling e do Ploomes com 10 de 10 verificações contra /sandbox. Os 15 sistemas do catálogo passam.
- A coleção agora espera o intervalo do contrato antes de cada requisição (`setTimeout`), para funcionar no Postman sem tomar 429.

**Site:** Bling e Ploomes na lista "Funciona com o que eu já uso?"; prévia atualizada.

**Lição:** `docs/memory/portal-de-api-com-javascript.md`.
