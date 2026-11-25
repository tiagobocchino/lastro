---
chave: LST-21
jira: https://adelecrm.atlassian.net/browse/LST-21
secao: OPS
status: feito
especialista: engenheiro-de-dados
---

# Guardar arquivos das empresas no Cloud Storage e isolar o sandbox

**Por quê:** O disco do Cloud Run é temporário e o sandbox precisa de uma segunda trava além da lista de funções (LST-17).

## Critérios de aceite

- [x] Arquivos em gs://<bucket>/tenants/<tenant>/
- [x] Consultas de agente com enable_external_access=false
- [x] Teste: um tenant não lê arquivo de outro mesmo burlando a trava
- [x] Modo local (disco) continua funcionando

## Verificação

Comandos da seção OPS em `docs/agents/secoes.yaml` + os critérios acima.

## Evidência (25/11)

- `Sandbox.travar()` em `lastro/conectores.py`: as fontes entram como tabelas; depois `allowed_directories` = pasta da demanda, `enable_external_access=false`, extensões automáticas desligadas e `lock_configuration=true`.
- `tests/test_isolamento.py`: 12 testes. SQL cru (sem a trava de SQL) falha ao ler arquivo de outra empresa (`read_csv`, `FROM 'x.csv'`, `read_text`), ao gravar fora, ao religar o acesso externo, ao mudar diretórios permitidos, ao fazer ATTACH e ao instalar extensão. O pipeline grava só na pasta da demanda; a demanda 1 não alcança a 2 nem a 10.
- `LASTRO_TENANTS` aponta a pasta de tenants para o bucket montado. O DuckDB de trabalho fica em pasta temporária local.
- Container com uma pasta do host no papel do bucket (`-v …:/bucket -e LASTRO_TENANTS=/bucket`, `lastro demo`): 19 arquivos em `tenants/demo/…` (fontes, decisões, gold, relatório, notebook, pipeline), 0 arquivos `.duckdb` no bucket; total 14.030.477,92 com auditoria aprovada.
- Modo local (disco): `uv run pytest -q` passa inteiro (133 testes).
- Decisão: `docs/adr/0007-bucket-montado-e-sandbox-travado.md`. A montagem real do bucket entra como critério do LST-22.
