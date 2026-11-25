---
name: fonte-imuv
description: 'Contrato da API IMUV (gestão): autenticação, paginação, limites e armadilhas'
type: fonte
tags:
- imuv
- api
- conector
- saas
---

# Contrato

Origem: medido contra a API real em 17/07/2026 (GIMI).

URL base: `https://{subdominio}.imuv.me/administrator/api`.

# Autenticação

Tipo `login_bearer`. Login em `https://{subdominio}.imuv.me/administrator/api/auth/login`.

# Paginação

Tipo `cabecalho`, teto de 50 por página. Total informado pela API: o motor confere truncamento.

# Limites

por_minuto: 60

# Carga incremental

Não tem: carga completa a cada execução.

# Entidades

- `vendas` em `/sale`
- `tarefas` em `/task`

# Armadilhas

- Nunca inferir o fim por lote menor que o pedido: o teto é 50 (10 em /task).
- Token só no Authorization: Bearer; na query volta 401.
