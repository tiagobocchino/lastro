---
name: egress-refresh-power-bi
description: Conta AWS sobe por egress quando o Power BI faz refresh contra o Athena e os resultados se acumulam no S3
type: erro-conhecido
tags: [aws, custo, egress, athena, power bi, refresh, s3, lifecycle]
---

# Sintoma

Custo novo e diário de transferência de dados logo após ligar o Power BI ao Athena; bucket de resultados do Athena crescendo.

# Correção

Lifecycle de poucos dias no bucket de resultados, refresh incremental ou agregado no lado do Athena, e budget com alarme na conta.
