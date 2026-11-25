---
chave: LST-47
jira: https://adelecrm.atlassian.net/browse/LST-47
secao: INT
status: em-andamento
especialista: engenheiro-backend
---

# BI sem atrito B · Power BI por HTTPS, sem certificado e sem gateway

**Plano:** `docs/planos/bi-sem-atrito.md`, frente 2. **Depende de:** LST-46.

## Critérios de aceite

- [x] `GET /bi/v1/<tabela>.parquet` com chave de leitura do BI por empresa, só leitura, revogável e enviada no cabeçalho
- [x] PBIP com `Parquet.Document(Web.Contents(...))` e URL base fixa (o `.pbids` saiu: não carrega o cabeçalho da chave e abriria uma conexão que dá 401)
- [ ] Tiago valida a atualização agendada no Power BI Service sem gateway, com os totais da gimi-teste

## Evidência (25/11)

- Código:
  - migração `0010_bi_chave_leitura` (só o hash da chave);
  - `AcessoBI.gerar_chave / revogar_chave / pela_chave / parquet`;
  - rotas `/bi/v1/`, `/bi/v1/tabelas`, `/bi/v1/<tabela>.parquet`, `POST/DELETE /api/bi/chave`;
  - portal com gerar, trocar e revogar;
  - PBIP padrão em HTTPS (`?via=postgres` mantém o Postgres).
- Testes:
  - `test_bi_por_https_com_chave_de_leitura`: 401 sem chave, isolamento entre empresas, nome malicioso dá 404, trocar, revogar e desligar cortam;
  - `test_bi_parquet_mantem_os_tipos_do_postgres_com_vazios`.
  - A suíte inteira está verde (328).
- **Produção (gimi-teste), chave temporária revogada no fim:**
  - sem chave dá 401;
  - `painel_7` 211.290.267,16, `d8_fato` 532.781.125,76, `d9_fato` 211.290.267,16, `painel_10` 239 registros;
  - 2 a 3 s e 100 a 300 KB por tabela;
  - ids continuam BIGINT;
  - PBIP aponta para `https://lastro-api-73zx.onrender.com/`.
- **Achados corrigidos na validação:**
  - `LASTRO_URL_PUBLICA` no Render aponta para um host que não existe (afetava também o retorno do OAuth). O endereço agora vem do próprio pedido.
  - Id com vazio saía DOUBLE e coluna toda vazia saía NULL. O tipo agora vem da coluna no Postgres.
- **Falta:** o Tiago valida no Power BI Service a atualização sem gateway (kit com a chave criada por ele no SQL Editor).
