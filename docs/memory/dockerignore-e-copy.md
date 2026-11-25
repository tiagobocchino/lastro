---
type: armadilha
description: "COPY no Dockerfile de pasta que está no .dockerignore quebra o deploy do Render com 'failed to compute cache key: not found'"
---

# COPY de pasta ignorada quebra o build no Render

**Regra:** ao acrescentar `COPY <pasta>` no `Dockerfile`, confira se ela não está no `.dockerignore`. O teste `test_dockerfile_so_copia_o_que_esta_no_contexto` (`tests/test_infra.py`) acusa isso antes do push.

**Why:** no LST-43, `COPY site ./site` falhou no Render ("failed to compute cache key ... not found"). O `site/` estava no `.dockerignore` desde quando o site ia para o Firebase (ADR 0006). O deploy falhou e a versão anterior continuou no ar. Aqui não deu para buildar a imagem completa: o Docker Hub devolve 429 para este ambiente ao baixar o `python:3.13-slim`.

**How to apply:**
- Mudou o `Dockerfile` ou o `.dockerignore`? Rode `uv run --extra dev pytest -q tests/test_infra.py`.
- Se o Docker Hub deixar, rode também `docker build --secret id=ca,src=/root/.ccr/ca-bundle.crt .` (ver `docker-build-atras-de-proxy.md`).
