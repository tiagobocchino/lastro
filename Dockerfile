# syntax=docker/dockerfile:1
# API e agentes do Lastro (Cloud Run ou local). Card LST-20 · plano em docs/infra/plano-nuvem-v1.md
# O modelo de embeddings fica fora da imagem: com LASTRO_EMBEDDER=fastembed, ele vem do Cloud Storage (LST-21).
# Rede corporativa ou proxy com certificado próprio: docker build --secret id=ca,src=<arquivo.crt> .
# O certificado só existe durante o RUN; nada dele fica na imagem.

FROM python:3.13-slim AS construcao
ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy UV_PROJECT_ENVIRONMENT=/app/.venv UV_PYTHON_DOWNLOADS=never
RUN --mount=type=secret,id=ca,required=false \
    if [ -f /run/secrets/ca ]; then export PIP_CERT=/run/secrets/ca; fi; \
    pip install --no-cache-dir uv==0.9.5
WORKDIR /app
# Dependências primeiro: a camada só muda quando o uv.lock muda.
COPY pyproject.toml uv.lock README.md ./
RUN --mount=type=secret,id=ca,required=false \
    if [ -f /run/secrets/ca ]; then export SSL_CERT_FILE=/run/secrets/ca; fi; \
    uv sync --frozen --no-dev --extra postgres --no-install-project --no-cache
COPY lastro ./lastro
RUN --mount=type=secret,id=ca,required=false \
    if [ -f /run/secrets/ca ]; then export SSL_CERT_FILE=/run/secrets/ca; fi; \
    uv sync --frozen --no-dev --extra postgres --no-cache

FROM python:3.13-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PATH="/app/.venv/bin:$PATH" LASTRO_HOME=/dados PORT=8080
WORKDIR /app
RUN useradd --create-home --uid 10001 lastro && mkdir -p /dados && chown lastro /dados
COPY --from=construcao /app/.venv /app/.venv
COPY lastro ./lastro
COPY caixa ./caixa
COPY skills ./skills
COPY exemplos ./exemplos
USER lastro
EXPOSE 8080
HEALTHCHECK --interval=30s --timeout=5s CMD python -c "import os,urllib.request; urllib.request.urlopen(f'http://127.0.0.1:{os.environ[\"PORT\"]}/saude', timeout=4)"
CMD ["lastro", "serve"]
