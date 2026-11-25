# ADR 0001: Caixa de Ferramenta própria em SQLite FTS5 com RRF

**Status:** aceito · 2026-11-25

## Contexto

Os agentes precisam de contexto grande (playbooks, decisões do cliente, perfis de fontes) sem carregar tudo no prompt. Candidatos estudados: progressive disclosure das Agent Skills da Anthropic; qmd (BM25 + vetor + rerank local, MCP, Node); claude-context da Zilliz (código, depende de Milvus/Zilliz Cloud e de chave de embedding); o padrão sqlite-vec + FTS5 + RRF descrito por Alex Garcia e Simon Willison.

## Decisão

Construir a nossa Caixa em Python: SQLite FTS5 (BM25, sem acento) por escopo, fusão por Reciprocal Rank Fusion (k = 60), peso por escopo (demanda > tenant > global) e um `Embedder` opcional para somar busca vetorial ao RRF. Três camadas de leitura: índice, busca, leitura por seção. Notas em Markdown com frontmatter no formato das Agent Skills.

## Consequências

- Zero dependência paga ou de rede; roda dentro do processo.
- Sem embeddings, sinônimos não batem (ex.: "faturamento" × "valor_vendido"). Próximo passo: embeddings locais (fastembed ou Ollama) via `Embedder`.
- qmd continua útil para o time no Claude Code; não entra no produto por ser Node.
