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

# O que o agente faz (interpretação)

- Tira só o espaço das pontas (`trim`).
- O Explorador conta as grafias diferentes, os marcadores de vazio e os acentos quebrados.
- O grill **pergunta** se as grafias são o mesmo valor e se os marcadores significam "sem informação".
- O Auditor avisa enquanto não houver resposta.

# O que o cliente responde (regra de negócio, nunca deduzida)

- Se "ANA" e "Ana" são o mesmo valor. Podem ser pessoas diferentes.
- Se `N/A`, `X` ou `-` significam vazio ou são uma categoria de verdade.
- Sem resposta, nada é unificado nem apagado. Com resposta, a regra fica gravada para a fonte e vale nas próximas demandas.

# Exportar no Windows

Grave em UTF-8 com BOM (CSV) ou em Excel.
