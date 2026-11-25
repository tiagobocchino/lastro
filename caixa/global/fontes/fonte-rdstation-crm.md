---
name: fonte-rdstation-crm
description: 'Contrato da API RD Station CRM: autenticação, paginação, limites e armadilhas'
type: fonte
tags:
- rdstation_crm
- api
- conector
- saas
---

# Contrato

Origem: documentação oficial (developers.rdstation.com) · limites confirmados; paginação a validar no piloto.

URL base: `https://crm.rdstation.com/api/v1`.

# Autenticação

Tipo `oauth2_refresh`.

# Paginação

Tipo `pagina`, teto de 200 por página. Total informado pela API: o motor confere truncamento.

# Limites

por_minuto: 120

# Carga incremental

Não tem: carga completa a cada execução.

# Entidades

- `negocios` em `/deals`
- `contatos` em `/contacts`

# Armadilhas

Nenhuma registrada ainda.
