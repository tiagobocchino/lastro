---
name: fonte-pipedrive
description: 'Contrato da API Pipedrive (CRM): autenticação, paginação, limites e
  armadilhas'
type: fonte
tags:
- pipedrive
- api
- conector
- saas
---

# Contrato

Origem: documentação oficial (OpenAPI v2).

URL base: `https://api.pipedrive.com/api/v2`.

# Autenticação

Tipo `api_key_header`.

# Paginação

Tipo `cursor`, teto de 500 por página. A API não informa total.

# Limites

por_minuto: 120

# Carga incremental

Parâmetro `updated_since`.

# Entidades

- `negocios` em `/deals`
- `pessoas` em `/persons`
- `organizacoes` em `/organizations`

# Armadilhas

Nenhuma registrada ainda.
