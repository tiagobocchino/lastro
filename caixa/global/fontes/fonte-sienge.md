---
name: fonte-sienge
description: 'Contrato da API Sienge (ERP construção): autenticação, paginação, limites
  e armadilhas'
type: fonte
tags:
- sienge
- api
- conector
- saas
---

# Contrato

Origem: documentação oficial (api.sienge.com.br/docs, 87 specs OpenAPI).

URL base: `https://api.sienge.com.br/{subdominio}/public/api/v1`.

# Autenticação

Tipo `basic`.

# Paginação

Tipo `offset`, teto de 200 por página. Total informado pela API: o motor confere truncamento.

# Limites

por_minuto: 200, por_dia_por_pacote: {'Free': 100, 'Start': 1000, 'Special': 2500, 'Essencial': 5000, 'Enterprise': 10000, 'Business': 30000, 'Ultimate': 75000, 'Infinity': 200000}

# Carga incremental

Parâmetro `modifiedAfter`.

# Entidades

- `contratos_venda` em `/sales-contracts`
- `clientes` em `/customers`
- `empreendimentos` em `/enterprises`
- `centros_custo` em `/cost-centers`

# Armadilhas

- Cota diária do pacote Free é 100 requisições: uma carga completa pode não caber num dia.
- Bulk data tem URL própria (/public/api/bulk-data/v1) e limite de 20/min.
