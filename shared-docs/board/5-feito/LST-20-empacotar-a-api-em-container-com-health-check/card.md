---
chave: LST-20
jira: https://adelecrm.atlassian.net/browse/LST-20
secao: OPS
status: feito
especialista: engenheiro-backend
---

# Empacotar a API em container com health check

**Por quê:** O Cloud Run roda containers; o mesmo container serve local e produção.

## Critérios de aceite

- [x] Dockerfile com uv, usuário sem root, porta por $PORT
- [x] GET /saude responde 200 com versão e estado do banco
- [x] Modelo de embeddings fora da imagem
- [x] docker build/run locais passam; imagem abaixo de 500 MB

## Verificação

Comandos da seção OPS em `docs/agents/secoes.yaml` + os critérios acima.

## Evidência (25/11)

- `Dockerfile` em dois estágios (uv só na construção), usuário `lastro` uid 10001, porta por `$PORT` (padrão 8080), HEALTHCHECK em `/saude`.
- `GET /saude` → `{"estado":"ok","versao":"0.1.0","banco":"ok"}`; sem login e sem dado interno (`tests/test_infra.py`).
- Imagem: 369 MB descompactada (`du -sxh /`), 119 MB compactada; modelo de embeddings fora da imagem.
- `docker run`: portal 200, login demo ok, health `healthy`. Em produção: sem contas demo (login recusado) e sem `LASTRO_SEGREDO` o container não sobe.
- `uv run pytest -q`: 121 passed.
- Lição: `docs/memory/docker-build-atras-de-proxy.md`.
