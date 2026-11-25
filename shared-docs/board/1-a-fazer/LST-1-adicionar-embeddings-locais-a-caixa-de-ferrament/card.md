---
chave: LST-1
jira: pendente (subir quando o projeto LST existir)
secao: NUC
status: pronto
especialista: engenheiro-de-dados
---

# Adicionar embeddings locais à Caixa de Ferramenta

**Por quê:** Sem vetores, 'faturamento' não acha 'valor_vendido' e o grill pergunta o óbvio.

## Critérios de aceite

- [ ] Embedder local gratuito (fastembed ou Ollama) plugado em Caixa sem rede paga
- [ ] Busca 'faturamento' traz a decisão sobre valor_vendido entre as 3 primeiras
- [ ] Suite continua verde

## Verificação

Comandos da seção NUC em `docs/agents/secoes.yaml` + os critérios acima.
