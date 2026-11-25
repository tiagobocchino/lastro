---
chave: LST-47
jira: https://adelecrm.atlassian.net/browse/LST-47
secao: INT
status: a-fazer
especialista: engenheiro-backend
---

# BI sem atrito B · Power BI por HTTPS, sem certificado e sem gateway

**Plano:** `docs/planos/bi-sem-atrito.md`, frente 2. **Depende de:** LST-46.

## Critérios de aceite

- [ ] `GET /bi/v1/<tabela>.parquet` com chave de leitura do BI por empresa, só leitura, revogável e enviada no cabeçalho
- [ ] PBIP com `Parquet.Document(Web.Contents(...))` e URL base fixa; arquivo `.pbids`
- [ ] Tiago valida a atualização agendada no Power BI Service sem gateway, com os totais da gimi-teste
