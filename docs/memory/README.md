# docs/memory

Armadilhas e fatos operacionais. Uma linha por nota.

- [card-no-jira-e-no-board](card-no-jira-e-no-board.md) — Card criado no Jira só existe quando está no board local e no GitHub; conferir com scripts/conferir_board.py.
- [yaml-dois-pontos-na-descricao](yaml-dois-pontos-na-descricao.md) — descrição de nota com dois-pontos quebra o YAML: use aspas.
- [docker-build-atras-de-proxy](docker-build-atras-de-proxy.md) — build atrás de proxy com CA própria; como medir o tamanho real da imagem
- [oauth-refresh-rotativo-e-relogio-zero](oauth-refresh-rotativo-e-relogio-zero.md) — refresh_token rotativo exige gravar no cofre na hora; `agora or time.time()` falha com relógio em 0.0; RD CRM v1 × v2.
