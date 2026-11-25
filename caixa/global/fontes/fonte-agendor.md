---
name: fonte-agendor
description: 'Contrato da API Agendor (CRM): autenticação, paginação, limites e armadilhas'
type: fonte
tags:
- agendor
- api
- conector
- saas
---

# Contrato

Origem: documentação oficial (swagger v3).

URL base: `https://api.agendor.com.br/v3`.

# Autenticação

Tipo `api_key_header`.

# Paginação

Tipo `pagina`, teto de 100 por página. A API não informa total.

# Limites

por_minuto: 60

# Carga incremental

Parâmetro `updatedAtGt`.

# Entidades

- `negocios` em `/deals`
- `pessoas` em `/people`
- `organizacoes` em `/organizations`

# Armadilhas

Nenhuma registrada ainda.
