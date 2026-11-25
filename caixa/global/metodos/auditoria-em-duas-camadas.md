---
name: auditoria-em-duas-camadas
description: Método de depuração em que um especialista técnico e um especialista de negócio auditam o trabalho analítico um do outro, com notebook no Colab
type: metodo
tags: [auditoria, validação, colab, notebook, duplicidade, integridade, revisor]
---

# Camada 1: técnica

O auditor técnico confere o pipeline: contagem de linhas entre camadas, duplicidade na chave, integridade entre fato e dimensões, soma da medida entre silver e fato, nulos, negativos, datas vazias e futuras, e recalcula o total da resposta de forma independente.

# Camada 2: negócio

Outro especialista, de outra área, abre o notebook no Google Colab, refaz as contas com pandas e compara indicador por indicador com o painel. Divergência vira apontamento com print e número (ex.: "61 no gráfico, 69 no indicador macro").

# Regras

- Nenhuma entrega sai sem as duas camadas.
- Reprovação vira nota de aprendizado na Caixa de Ferramenta.
- O notebook é autossuficiente: lê os Parquet do gold, não depende da plataforma.

# Origem

Validação BI da EngenhaDev (maio de 2026) e notebooks de auditoria de duplicidade, integridade, schema, datas e valores.
