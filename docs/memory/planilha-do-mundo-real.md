---
type: armadilha
description: "Planilha real quebra o Explorador (aspas no nome da coluna), esconde o valor em texto 'R$ 526530' e faz o painel somar número de processo"
---

# Planilha do mundo real: nome com aspas, moeda em texto, número que identifica

**Regra:** toda planilha que entra no sandbox passa por `_renomear_colunas` e `_converter_moeda` (`lastro/conectores.py`). O Explorador marca como `identificador` o inteiro quase único com nome de número (`Nº`, `N º E`, `Cód`, `ID`). O painel (`paineis.catalogo`) compara nomes com `construtores.ident`, nunca com `_slug`.

**Why:** a primeira planilha real do Tiago (`processos_gbl.xlsx`, 25/11/2026) teve três falhas em sequência:
- `N º "E"` quebrou o SQL com "zero-length delimited identifier";
- o valor estava em `Previsão` como texto `R$ 526530`;
- o painel somou o número do processo. O `_slug` transforma "º" em "o" (`n_o_e`), e o gold chama a coluna de `n_e`.

**How to apply:** caso novo de planilha que não lê vira teste em `tests/test_nomes_de_coluna.py`, com um DataFrame mínimo que reproduz o cabeçalho e o formato. Não use o arquivo do cliente no teste. Antes de dizer que o painel está certo, confira o total com pandas.
