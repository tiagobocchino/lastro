# docs/memory

Armadilhas e fatos operacionais. Uma linha por nota.

- [card-no-jira-e-no-board](card-no-jira-e-no-board.md) — Card criado no Jira só existe quando está no board local e no GitHub; conferir com scripts/conferir_board.py.
- [yaml-dois-pontos-na-descricao](yaml-dois-pontos-na-descricao.md) — descrição de nota com dois-pontos quebra o YAML: use aspas.
- [docker-build-atras-de-proxy](docker-build-atras-de-proxy.md) — build atrás de proxy com CA própria; como medir o tamanho real da imagem
- [oauth-refresh-rotativo-e-relogio-zero](oauth-refresh-rotativo-e-relogio-zero.md) — refresh_token rotativo exige gravar no cofre na hora; `agora or time.time()` falha com relógio em 0.0; RD CRM v1 × v2.
- [portal-de-api-com-javascript](portal-de-api-com-javascript.md) — doc "baixada" pode ser só a casca HTML; especificação real via Playwright; Newman --env-var sobrepõe variável de coleção; folga no limitador.
- [supabase-chave-secreta-no-apikey](supabase-chave-secreta-no-apikey.md) — sb_secret_ só no cabeçalho apikey; conferir o espelho com scripts/conferir_espelho.py.
- [postgres-on-conflict-where-silencioso](postgres-on-conflict-where-silencioso.md) — upsert com WHERE de tenant não falha no Postgres: use RETURNING; teste isolamento nos dois bancos; pg_cron ausente no Postgres local.
- [vault-conferir-formato-sem-ler](vault-conferir-formato-sem-ler.md) — conferir segredo do Vault pelo formato, sem ler o valor; exemplo das instruções costuma ir parar no Vault; responder em português.
