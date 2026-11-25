---
chave: LST-11
jira: https://adelecrm.atlassian.net/browse/LST-11
secao: INT
status: em-qa
especialista: engenheiro-de-dados
---

# Conector somente leitura para Google Sheets e Drive

**Por quê:** Muita empresa começa a análise numa planilha.

## Critérios de aceite

- [ ] Escopo OAuth drive.readonly / spreadsheets.readonly
- [ ] Planilha vira fonte com perfil do Explorador
- [ ] Teste com planilha fictícia

## Verificação

Comandos da seção INT em `docs/agents/secoes.yaml` + os critérios acima.

## Entrega do engenheiro-de-dados

- Contratos `google_sheets` (escopo `spreadsheets.readonly`) e `google_drive` (escopo `drive.readonly`) em `lastro/saas/catalogo.yaml`, confiança "a validar no piloto".
- Motor: paginação `nenhuma`, resposta em matriz (`matriz_para_registros`, completa células vazias omitidas), variáveis no caminho (`/values/{aba}`), `params_fixos` (`UNFORMATTED_VALUE`).
- Simulador reproduz a omissão de células vazias no fim da linha.
- Evidência: `uv run pytest -q` → 96 passed; Newman `google_sheets` e `google_drive` contra `/sandbox` → 4/4 asserções; `POST /api/saas/google_sheets/testar` com importar → 180 registros, fonte criada.
- Fora do escopo: o fluxo OAuth real (autorizar e renovar token) é o LST-9.
