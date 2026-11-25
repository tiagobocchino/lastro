---
chave: LST-46
jira: https://adelecrm.atlassian.net/browse/LST-46
secao: INT
status: feito
especialista: engenheiro-de-dados
---

# BI sem atrito A · tabela pronta por demanda no BI

**Plano:** `docs/planos/bi-sem-atrito.md`, frente 1.

## Critérios de aceite

- [x] Cada demanda aprovada publica `painel_<n>_<assunto>` no BI: fato ligada às dimensões, data como `date`, ano, mês e ano_mes, medidas e `registros = 1`
- [x] Categoria vazia continua vazia (ADR 0011: rótulo para o vazio é regra do cliente)
- [x] Total da tabela igual ao da fato; teste automatizado
- [x] gimi-teste: vendido 211.290.267,16, orçado 532.781.125,76 e 239 funcionários pela soma de `registros`
- [x] `docs/infra/bi.md` atualizado

## Verificação

`uv run pytest -q` e conferência dos totais no BI de produção.

## Evidência (25/11)

- `bi._rel_painel`: a fato ligada às dimensões por `LEFT JOIN`, com `data` (DATE), `ano`, `mes`, `ano_mes`, as medidas e `registros = 1`. Nenhuma coluna `_id` técnica.
- Vazio continua vazio. Testes:
  - `tests/test_bi_tabela_pronta.py`: total igual ao da fato, linha sem vendedor continua vazia, contagem sem medida pela soma de `registros`;
  - `tests/test_postgres.py`: total e contagem no Postgres iguais aos da fato.
- **Produção (gimi-teste, schema do BI, conferido por SQL):**
  - `painel_7`: vendido 211.290.267,16;
  - `painel_8`: orçado 532.781.125,76 e funil Aprovado 3790 / Perdido 2380 / Orçado 2109 / Em negociação 1243;
  - `painel_9`: itens 211.290.267,16;
  - `painel_10`: 239 funcionários pela soma de `registros`, por setor Administrativo 33 / Comercial 58 / Engenharia 44 / Instalação 58 / Produção 46.

  Tudo igual ao gabarito.
- **Achado no caminho:** publicar sem os arquivos no servidor apagaria o BI inteiro. Agora o que não pode ser recriado fica mantido, com aviso no portal (commit 473d48f, nota `docs/memory/disco-efemero-no-render.md`).
- **Efeito colateral meu:** supus o disco zerado e rodei tudo de novo. A gimi-teste ficou com fontes 11 a 13 e demandas 11 a 14 duplicadas (84 tabelas no BI). A limpeza aguarda o Tiago.
