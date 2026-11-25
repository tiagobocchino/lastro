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

Origem: documentação oficial da API v2 (developers.rdstation.com/reference/crm-v2-*) · tamanho máximo de página a validar no piloto.

URL base: `https://api.rd.services/crm/v2`.

# Autenticação

Tipo `oauth2_refresh`. OAuth2: autorização em `https://accounts.rdstation.com/oauth/authorize`, token em `https://api.rd.services/oauth2/token`, validade de 7200 s; refresh_token rotativo (guardar o novo a cada renovação). Tokens só no cofre (LST-9).

# Paginação

Tipo `pagina`, teto de 25 por página. A API não informa total.

# Limites

por_minuto: 120

# Carga incremental

Não tem: carga completa a cada execução.

# Entidades

- `negocios` em `/deals`
- `contatos` em `/contacts`

# Armadilhas

- A API v1 (crm.rdstation.com/api/v1) usa um token fixo por usuário e só mostra o que a visibilidade dele permite; o Lastro usa a v2, com OAuth2.
- Token de acesso vale 2 horas; o refresh_token muda a cada renovação e expira se ficar 14 dias sem uso: carga parada por duas semanas exige nova autorização.
- Paginação por page[number] e page[size] (padrão 25); o fim é a página com menos registros que o tamanho.
