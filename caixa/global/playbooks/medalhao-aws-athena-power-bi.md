---
name: medalhao-aws-athena-power-bi
description: Data lake serverless na AWS com camadas Bronze/Silver/Gold em S3, catálogo Glue, consulta Athena e Power BI
type: playbook
tags: [aws, s3, glue, athena, lambda, step functions, eventbridge, power bi, data lake, medalhão]
---

# Arquitetura

EventBridge (agenda diária) aciona Step Functions, que roda Lambdas por camada: Bronze (JSON bruto da API), Silver (Parquet estruturado), Gold (Parquet deduplicado, pronto para Athena). Glue Crawlers catalogam; views no Athena expõem o schema esperado pelo Power BI (ODBC).

# Fonte única de configuração

Um YAML lista fontes, entidades e empresas; Terraform e o input da Step Function são derivados dele. Adicionar uma entidade = editar o YAML, fazer deploy das Lambdas e aplicar o Terraform.

# Caminhos

Hive-style: `{env}/{dominio}/{camada}/{entidade}/company={empresa}/extraction_date={data}/`. Metadados em árvore separada `_metadata/`.

# Custos (referência de 2026)

O dinheiro está em armazenamento S3 e egress do refresh do Power BI, não no scan do Athena. Ative lifecycle na Silver e nos resultados do Athena, use partition projection no lugar de crawlers diários e crie budgets com alarme.

# Origem

Pipeline IAPP/IMUV/OMIE da EngenhaDev (ADRs 0001 a 0006).
