---
name: fonte-iapp
description: 'Contrato da API IApp (CRM/orçamentos industriais): autenticação, paginação,
  limites e armadilhas'
type: fonte
tags:
- iapp
- api
- conector
- saas
---

# Contrato

Origem: medido contra a API real (GIMI).

URL base: `https://api.iniciativaaplicativos.com.br/api`.

# Autenticação

Tipo `api_key_header`.

# Paginação

Tipo `pagina`, teto de 50 por página. A API não informa total.

# Limites

por_minuto: 60

# Carga incremental

Não tem: carga completa a cada execução.

# Entidades

- `contratos` em `/contracts`
- `clientes` em `/clients`
- `tarefas` em `/tasks`
- `funcionarios` em `/employees`
- `usuarios` em `/users`
- `vendedores` em `/sellers`
- `grupos` em `/groups`

# Armadilhas

- success:false com HTTP 200 (ESTABELECIMENTO_NOT_FOUND) vira carga vazia silenciosa se não for checado.
- Credencial por empresa: uma carga por empresa, partição company=.
- O parâmetro chamado offset é o TAMANHO da página; page começa em 1 (page=0 rejeitado desde 08/10/2026).
