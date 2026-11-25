---
type: fato-operacional
description: docker build atrás de proxy com certificado próprio (sessão na nuvem, rede corporativa)
---

# docker build atrás de proxy

Regra: quando o build falha com `CERTIFICATE_VERIFY_FAILED` ou `Connection refused` em 127.0.0.1, passe o certificado como segredo e use a rede do host:

`docker build --network host --secret id=ca,src=<ca.crt> --build-arg HTTPS_PROXY="$HTTPS_PROXY" -t lastro .`

**Why:** o proxy escuta em 127.0.0.1 (invisível na rede padrão do build) e reassina o TLS com uma CA própria. Custou três builds no LST-20.

**How to apply:** o Dockerfile já lê o segredo `ca` se existir; nada dele fica na imagem. Fora de proxy, `docker build -t lastro .` basta. O `docker image inspect` com containerd soma camada compactada e descompactada: meça com `du -sxh /` dentro do container (369 MB) ou `docker save | gzip | wc -c` (119 MB).
