---
name: fonte-ploomes
description: 'Contrato da API Ploomes (CRM): autenticação, paginação, limites e armadilhas'
type: fonte
tags:
- ploomes
- api
- conector
- saas
---

# Contrato

Origem: especificação oficial (developers.ploomes.com/json/openapi.json, baixada em 25/11/2026) · o envelope OData `value` não aparece na especificação, a confirmar no piloto.

URL base: `https://public-api2.ploomes.com`.

# Autenticação

Tipo `api_key_header`.

# Paginação

Tipo `offset`, teto de 300 por página. A API não informa total.

# Limites

por_minuto: 120

# Carga incremental

Não tem: carga completa a cada execução.

# Entidades

- `negocios` em `/Deals`
- `contatos` em `/Contacts`
- `pedidos` em `/Orders`
- `propostas` em `/Quotes`
- `tarefas` em `/Tasks`

# Armadilhas

- Limite de 120 requisições por minuto somando todos os usuários de integração da conta.
- No máximo 300 itens por requisição em Contacts, Deals, Cities, Tasks, Orders e Quotes.
- Só administradores criam a User-Key (Administração > Integrações > Usuários de Integração): peça um usuário de integração só de leitura.
- A especificação não documenta campo de data de alteração: a carga é completa até o piloto confirmar um filtro OData por data.
