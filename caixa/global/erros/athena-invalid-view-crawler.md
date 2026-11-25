---
name: athena-invalid-view-crawler
description: Power BI falha com INVALID_VIEW no Athena porque o Glue Crawler recatalogou a tabela com o schema errado
type: erro-conhecido
tags: [athena, glue, crawler, power bi, odbc, invalid_view, schema]
---

# Sintoma

ODBC ErrorType 1107, `INVALID_VIEW ... Column 'id' cannot be resolved`. Não é rede nem SSL.

# Causa

O crawler leu só arquivos de metadados e catalogou a tabela com 4 colunas internas (`_extraction_date`, `_company`, `_source`, `_loaded_at`).

# Correção

Exclua os prefixos de metadados do crawler, recrie a tabela com a DDL certa ou troque crawler por partition projection; rode as views de novo antes do refresh.
