---
chave: LST-5
jira: https://adelecrm.atlassian.net/browse/LST-5
secao: NUC
status: feito
especialista: engenheiro-de-dados
---

# Adicionar embeddings locais à Caixa de Ferramenta

**Por quê:** Sem vetores, 'faturamento' não acha 'valor_vendido' e o grill pergunta o óbvio.

## Critérios de aceite

- [x] Embedder local gratuito (fastembed ou Ollama) plugado em Caixa sem rede paga
- [x] Busca 'faturamento' traz a decisão sobre valor_vendido entre as 3 primeiras
- [x] Suite continua verde

## Verificação

Comandos da seção NUC em `docs/agents/secoes.yaml` + os critérios acima.

## Entrega do engenheiro-de-dados

- `lastro/vetores.py`: EmbedderLocal (fastembed, paraphrase-multilingual-MiniLM-L12-v2, ONNX local, cache SQLite por hash), ligado por `LASTRO_EMBEDDER=fastembed`.
- Achado: a decisão de medida não era gravada (vale só para a demanda). Agora toda resposta do grill vai para a Caixa: as da fonte em `decisoes/`, as da demanda em `decisoes/historico/` (o grill continua perguntando medida e recorte).
- Notas de decisão ganham a seção "Em palavras" (valor_vendido → valor vendido) para o modelo semântico.
- Medição: "faturamento" → decisão de medida em 1º com fastembed; sem embedder, nenhum resultado.
- `uv run pytest -q` → 100 passed (4 novos em `tests/test_vetores.py`).

## QA (qa-secao NUC)

Aprovado em clone limpo (cee12bb) com download do modelo do zero: 4 testes do card sem skip, 100 passed. Sugestão ao PO: registrar no CONTEXT.md que decisões da demanda vão para o histórico.
