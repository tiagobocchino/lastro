---
name: fonte-cvcrm
description: 'Contrato da API CV CRM · CVDW (CRM imobiliário): autenticação, paginação,
  limites e armadilhas'
type: fonte
tags:
- cvcrm
- api
- conector
- saas
---

# Contrato

Origem: documentação oficial (desenvolvedor.cvcrm.com.br).

URL base: `https://{dominio}.cvcrm.com.br/api/v1/cvdw`.

# Autenticação

Tipo `login_bearer`. Login em `https://{dominio}.cvcrm.com.br/api/v3/auth/token`.

# Paginação

Tipo `pagina_total`, teto de 500 por página. Total informado pela API: o motor confere truncamento.

# Limites

por_minuto: 20

# Carga incremental

Parâmetro `a_partir_data_referencia`.

# Entidades

- `leads` em `/leads`
- `reservas` em `/reservas`
- `unidades` em `/unidades`
- `corretores` em `/corretores`

# Armadilhas

- Padrão de 30 registros por página: sem registros_por_pagina a carga leva 16x mais chamadas.
- 20 req/min: espaçar 3 s entre chamadas.
- Token v3 expira em 6 h: renovar no meio de cargas longas.
