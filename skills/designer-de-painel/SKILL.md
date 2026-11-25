---
name: designer-de-painel
description: Monta e edita o painel de uma demanda aprovada a partir do gold, e entrega em HTML e como projeto do Power BI.
---

# Papel

Propõe o painel inicial a partir do modelo da demanda: o número principal (KPI), a quebra que o demandante pediu (barras), a evolução no tempo (linha) e o detalhe (tabela). Depois, aplica as mudanças que o demandante pede em português ou pelo formulário. Código em `lastro/paineis.py`.

# Regras

- Só trabalha sobre demanda **aprovada**: o painel nasce do gold que passou pelas duas camadas.
- Tudo sai de uma especificação JSON por versão (`demandas/<id>/painel/v<n>.json`). Nunca sobrescreve uma versão.
- Toda mudança é validada contra o gold antes de gravar: coluna que não existe, eixo que não existe, medida em uso ou tipo de visual desconhecido são recusados, e nada muda.
- Ids de medidas e visuais são estáveis e nunca são reaproveitados. É isso que mantém o painel do cliente no Power BI de pé quando algo é acrescentado.
- Toda criação, mudança, recusa e download vai para o rastro da demanda (`criou_painel`, `alterou_painel`, `recusou_mudanca_painel`, `baixou_powerbi`).
- Determinístico, sem LLM. Pedido que não reconhece é recusado com exemplos, sem adivinhar.

# Saídas

- **HTML estático:** sem script e sem custo, com os números calculados pelo DuckDB sobre o gold.
- **Projeto do Power BI (PBIP):**
  - modelo em TMDL, com tabelas, relações fato–dimensões e medidas DAX;
  - relatório em PBIR, uma página com um visual por item.
  - As consultas leem o schema de BI da empresa (LST-33). Servidor, banco e schema ficam em parâmetros do Power Query.
  - Os arquivos JSON são validados nos testes contra os schemas oficiais da Microsoft (`tests/dados/powerbi_schemas`).

# Pedidos que entende

- "nova medida média de valor orçado" (soma, média, contagem, distintos, mínimo, máximo)
- "adicione um gráfico de barras de valor vendido por estado" (barras, linha, tabela, KPI; eixo = dimensão, mês ou ano)
- "remova o v3"
