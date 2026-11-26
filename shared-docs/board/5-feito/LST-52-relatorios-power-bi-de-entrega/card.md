---
chave: LST-52
jira: https://adelecrm.atlassian.net/browse/LST-52
secao: INT
status: feito
especialista: engenheiro-de-dados
---

# Relatórios Power BI de entrega (gimi-teste)

**Plano:** `docs/planos/relatorios-gimi-teste.md`. **Depende de:** LST-51.

## Critérios de aceite

- [x] PBIP multipágina por relatório (vendas, funil, produtos, RH): KPIs, funil, evolução, rankings, geografia por região e UF (sem mapa: visuais de mapa antigos estão sendo descontinuados; colunas marcadas como geográficas para um Azure Maps manual), segmentações, tema
- [x] Leitura por HTTPS com a chave (LST-47)
- [x] Tiago abre no Desktop e os totais de controle batem

## Evidência (26/11)

- **Código:**
  - `lastro/relatorio_powerbi.py`, no padrão dos relatórios do Looker do Tiago: filtros no topo, cartões com comparação ao ano anterior, "Visão geral" → "<indicador> por <dimensão>" → Geografia → Detalhe;
  - `GET /api/demandas/{id}/relatorio/powerbi` e botão no painel.
- **Testes:**
  - `tests/test_relatorio_powerbi.py`: schemas oficiais, páginas pela pergunta, coluna de um valor só não vira página, nenhuma medida com nome de coluna;
  - teste no Postgres;
  - a suíte inteira está verde (339).
- **Produção:** relatórios das demandas 15 a 18 da gimi-teste gerados pela API. **O Tiago abriu os 4 no Desktop e todos os totais passaram.**
- **Achados no caminho:**
  - páginas de coluna com um valor só (status de venda aprovada): agora o gerador conta os valores distintos no BI;
  - "Registros" × "registros" impediu a abertura (nota `docs/memory/powerbi-medida-com-nome-de-coluna.md`).
