---
name: fonte-omie
description: 'Contrato da API Omie (ERP): autenticação, paginação, limites e armadilhas'
type: fonte
tags:
- omie
- api
- conector
- saas
---

# Contrato

Origem: medido contra a API real em 24/08/2026 (GIMI).

URL base: `https://app.omie.com.br/api/v1`.

# Autenticação

Tipo `credencial_no_corpo`.

# Paginação

Tipo `pagina_total`, teto de 100 por página. Total informado pela API: o motor confere truncamento.

# Limites

por_minuto: 60, pausa_s: 0.3

# Carga incremental

Não tem: carga completa a cada execução.

# Entidades

- `clientes` em `/geral/clientes/`
- `vendedores` em `/geral/vendedores/`

# Armadilhas

- Erro vem com HTTP 200 e faultstring no corpo.
- O nome do array muda por endpoint (clientes_cadastro × cadastro).
- Teto de 100 por página mesmo pedindo mais.
- Campos aninhados (enderecoEntrega, info) viram colunas com prefixo na silver.
