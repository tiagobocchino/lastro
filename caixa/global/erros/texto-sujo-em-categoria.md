---
name: texto-sujo-em-categoria
description: Mesma categoria com espaço no fim, caixa ou acento diferente vira barras separadas e quebra mapeamentos por igualdade exata
type: erro-conhecido
tags: [texto, categoria, espaço, trim, caixa, acento, encoding, cp1252, latin1, utf-8, mojibake, N/A, marcador de vazio]
---

# Sintoma

- Um mapeamento por igualdade exata deixou estágios de fora: 7 de 247 tinham espaço no fim (`'Recebido '`).
- Acentos aparecem como `Ã§` ou `�`.
- `N/A`, `X` e `-` aparecem como categoria no gráfico.

# Causa

- Texto digitado à mão na origem.
- Arquivo salvo em latin-1/cp1252 e lido como UTF-8, ou ao contrário. No Windows, o terminal também converte.

# Correção

- O Lastro faz `trim` e colapsa espaços na silver.
- O Explorador conta as grafias diferentes, os marcadores de vazio e os acentos quebrados, e o Auditor avisa em cada dimensão.
- Caixa e acento não são corrigidos em silêncio: a regra de padronização é pergunta para o negócio, porque "ANA" e "Ana" podem ser pessoas diferentes.
- Ao exportar para o cliente no Windows, grave em UTF-8 com BOM (CSV) ou em Excel.
