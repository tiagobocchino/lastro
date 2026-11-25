---
name: formato-da-origem-mudou
description: A API ou planilha muda o nome ou formato de um campo e a regra derivada passa a classificar tudo como 'outros' sem dar erro
type: erro-conhecido
tags: [schema, evolução, api, campo renomeado, classificação, material avulso, outros, regressão silenciosa]
---

# Sintoma

Uma classificação derivada passou a jogar **100%** dos itens em "MATERIAL AVULSO". Nada deu erro: o campo da regra mudou de formato na origem (aninhado → achatado com prefixo).

# Regra

- Toda regra derivada precisa de um **teste com o formato real** do dado: o que chega na camada que a regra lê, não o JSON de origem.
- Uma categoria "outros" crescendo de repente é alarme. Compare a distribuição com a carga anterior.
- Aceite os dois formatos de nome enquanto a origem migra, e registre quando o antigo pode sair.
