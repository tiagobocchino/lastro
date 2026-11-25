---
name: fonte-bling
description: 'Contrato da API Bling (ERP): autenticação, paginação, limites e armadilhas'
type: fonte
tags:
- bling
- api
- conector
- saas
---

# Contrato

Origem: especificação OpenAPI oficial da API v3 (developer.bling.com.br, baixada em 25/11/2026) e guias de autenticação e limites · tamanho máximo de página e rotação do refresh_token a validar no piloto.

URL base: `https://api.bling.com.br/Api/v3`.

# Autenticação

Tipo `oauth2_refresh`. OAuth2: autorização em `https://bling.com.br/Api/v3/oauth/authorize`, token em `https://bling.com.br/Api/v3/oauth/token`, validade de 21600 s; refresh_token rotativo (guardar o novo a cada renovação). Tokens só no cofre (LST-9).

# Paginação

Tipo `pagina`, teto de 100 por página. A API não informa total.

# Limites

por_segundo: 3, por_dia: 120000

# Carga incremental

Não tem: carga completa a cada execução.

# Entidades

- `pedidos_venda` em `/pedidos/vendas`
- `contatos` em `/contatos`
- `produtos` em `/produtos`
- `contas_receber` em `/contas/receber`
- `contas_pagar` em `/contas/pagar`

# Armadilhas

- Filtro por data de alteração só existe em algumas rotas (pedidos, contatos, produtos): contas a receber e a pagar voltam inteiras a cada carga.
- Filtro por período maior que um ano responde HTTP 400: uma carga parada há mais de um ano precisa recomeçar do zero.
- Limite de 3 requisições por segundo e 120 mil por dia para a conta inteira, somando todos os aplicativos.
- O código de autorização expira em 30 segundos: a troca por token precisa ser imediata.
- O token opaco foi descontinuado; a autenticação atual é JWT (o uso no cabeçalho Bearer é o mesmo).
- A resposta não informa total: o fim é a página vazia, e o truncamento não pode ser conferido.
