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

Tipo `oauth2_refresh`. OAuth2: autorização em `https://login.contaazul.com/#/oauth/authorize`, token em `https://api-v2.contaazul.com/oauth/token`, validade de 3600 s; refresh_token rotativo (guardar o novo a cada renovação). Tokens só no cofre (LST-9).

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

- OAuth2 com refresh_token: o cliente autoriza uma vez; o token de acesso vale 1 hora e o refresh_token muda a cada renovação (guardar sempre o novo).
- Renovação recusada volta 400 invalid_grant com error_subtype: access_revoked exige nova autorização.
