---
name: fonte-google-sheets
description: 'Contrato da API Google Sheets (planilhas): autenticação, paginação,
  limites e armadilhas'
type: fonte
tags:
- google_sheets
- api
- conector
- saas
---

# Contrato

Origem: referência pública da Sheets API v4 · a validar no piloto (docs não baixadas nesta sessão).

URL base: `https://sheets.googleapis.com/v4/spreadsheets/{planilha_id}`.

# Autenticação

Tipo `oauth2_refresh`.

# Paginação

Tipo `nenhuma`, teto de 0 por página. A API não informa total.

# Limites

por_minuto: 60

# Carga incremental

Não tem: carga completa a cada execução.

# Entidades

- `valores` em `/values/{aba}`

# Armadilhas

- A resposta é uma matriz: a primeira linha é o cabeçalho, as demais viram registros.
- Células vazias no fim da linha são omitidas: a linha vem mais curta que o cabeçalho.
- Sem valueRenderOption=UNFORMATTED_VALUE os números chegam como texto formatado ("R$ 1.234,56").
- Cota de leitura por usuário é baixa (60/min): uma aba por chamada, sem varrer célula a célula.
