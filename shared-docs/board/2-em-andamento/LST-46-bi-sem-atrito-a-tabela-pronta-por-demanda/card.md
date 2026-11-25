---
chave: LST-46
jira: https://adelecrm.atlassian.net/browse/LST-46
secao: INT
status: em-andamento
especialista: engenheiro-de-dados
---

# BI sem atrito A · tabela pronta por demanda no BI

**Plano:** `docs/planos/bi-sem-atrito.md`, frente 1.

## Critérios de aceite

- [ ] Cada demanda aprovada publica `painel_<n>_<assunto>` no BI: fato ligada às dimensões, data como `date`, ano, mês e ano_mes, medidas e `registros = 1`
- [ ] Categoria vazia continua vazia (ADR 0011: rótulo para o vazio é regra do cliente)
- [ ] Total da tabela igual ao da fato; teste automatizado
- [ ] gimi-teste: vendido 211.290.267,16, orçado 532.781.125,76 e 239 funcionários pela soma de `registros`
- [ ] `docs/infra/bi.md` atualizado

## Verificação

`uv run pytest -q` e conferência dos totais no BI de produção.
