---
chave: LST-48
jira: https://adelecrm.atlassian.net/browse/LST-48
secao: INT
status: feito
especialista: engenheiro-backend
---

# BI sem atrito C · Data Studio pela planilha Google do cliente

**Plano:** `docs/planos/bi-sem-atrito.md`, frente 3. **Depende de:** LST-46.

## Critérios de aceite

- [x] Tabelas `painel_*` gravadas numa planilha do cliente a cada publicação, com OAuth `drive.file`
- [x] Guia de 3 cliques no Data Studio; acima do limite da planilha, o portal sugere o Postgres
- [x] Tiago valida os totais da gimi-teste no Data Studio

## Evidência (26/11)

- **Código:** `lastro/planilha_bi.py`, rotas `/api/bi/planilha/*`, envio na volta da autorização e a cada publicação, bloco no portal, migração 0012.
- **Testes:**
  - `tests/test_planilha_bi.py`, com o Google simulado em `tests/google_falso.py`: RAW sem fórmula, grade no tamanho exato, reenvio na mesma planilha, planilha apagada, token renovado e limite de células;
  - `test_planilha_google_do_bi_pelo_portal`.
  - A suíte inteira está verde (333).
- **Produção:**
  - O Tiago criou o app OAuth no Google Cloud (projeto lastro-515811, escopo `drive.file`, app em modo teste) e configurou `LASTRO_OAUTH_GOOGLE_SHEETS_*` no Render.
  - Ele autorizou com o próprio Gmail pelo link gerado para a gimi-teste. A planilha "Lastro · BI · gimi-teste" foi criada com 4 abas `painel_…`, sem avisos.
  - **O Tiago conferiu no Data Studio: os totais bateram.**
- **Aprendizado:** a tela "Criar branding" do Google Auth Platform quebrou o layout no navegador do Tiago. Os links diretos por etapa ajudaram.
