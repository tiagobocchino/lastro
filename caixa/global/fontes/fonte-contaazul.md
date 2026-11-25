---
name: fonte-contaazul
description: 'Contrato da API Conta Azul (ERP financeiro): autenticação, paginação,
  limites e armadilhas'
type: fonte
tags:
- contaazul
- api
- conector
- saas
---

# Contrato

Origem: documentação oficial (developers.contaazul.com) · paginação a validar no piloto.

URL base: `https://api-v2.contaazul.com/v1`.

# Autenticação

Tipo `oauth2_refresh`.

# Paginação

Tipo `pagina`, teto de 100 por página. Total informado pela API: o motor confere truncamento.

# Limites

por_minuto: 60

# Carga incremental

Não tem: carga completa a cada execução.

# Entidades

- `vendas` em `/venda/busca`
- `contas_receber` em `/financeiro/eventos-financeiros/contas-a-receber/buscar`

# Armadilhas

- OAuth2 com refresh_token: o cliente autoriza uma vez; o token de acesso precisa ser renovado.
