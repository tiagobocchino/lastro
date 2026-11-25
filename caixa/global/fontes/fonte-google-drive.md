---
name: fonte-google-drive
description: 'Contrato da API Google Drive (lista de planilhas): autenticação, paginação,
  limites e armadilhas'
type: fonte
tags:
- google_drive
- api
- conector
- saas
---

# Contrato

Origem: referência pública da Drive API v3 · a validar no piloto (docs não baixadas nesta sessão).

URL base: `https://www.googleapis.com/drive/v3`.

# Autenticação

Tipo `oauth2_refresh`.

# Paginação

Tipo `cursor`, teto de 100 por página. A API não informa total.

# Limites

por_minuto: 600

# Carga incremental

Não tem: carga completa a cada execução.

# Entidades

- `planilhas` em `/files`

# Armadilhas

- Sem o parâmetro fields a resposta vem enxuta e sem modifiedTime.
- Arquivos na lixeira aparecem se o filtro trashed=false for esquecido.
