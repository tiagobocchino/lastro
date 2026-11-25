---
name: fonte-hubspot
description: 'Contrato da API HubSpot (CRM): autenticação, paginação, limites e armadilhas'
type: fonte
tags:
- hubspot
- api
- conector
- saas
---

# Contrato

Origem: documentação oficial (developers.hubspot.com).

URL base: `https://api.hubapi.com/crm/v3/objects`.

# Autenticação

Tipo `bearer_estatico`.

# Paginação

Tipo `cursor`, teto de 100 por página. A API não informa total.

# Limites

por_segundo: 10

# Carga incremental

Não tem: carga completa a cada execução.

# Entidades

- `negocios` em `/deals`
- `contatos` em `/contacts`
- `empresas` em `/companies`

# Armadilhas

- Incremental por data exige a Search API (POST de leitura) e tem limite próprio, mais baixo.
