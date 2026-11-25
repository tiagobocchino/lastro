---
name: fonte-kommo
description: 'Contrato da API Kommo (CRM): autenticação, paginação, limites e armadilhas'
type: fonte
tags:
- kommo
- api
- conector
- saas
---

# Contrato

Origem: documentação oficial (developers.kommo.com).

URL base: `https://{subdominio}.kommo.com/api/v4`.

# Autenticação

Tipo `bearer_estatico`.

# Paginação

Tipo `pagina`, teto de 250 por página. A API não informa total.

# Limites

por_segundo: 7

# Carga incremental

Parâmetro `filter[updated_at][from]`.

# Entidades

- `negocios` em `/leads`
- `contatos` em `/contacts`

# Armadilhas

- Página vazia volta HTTP 204 sem corpo: é o fim da lista, não erro.
