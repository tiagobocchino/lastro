---
chave: LST-54
jira: https://adelecrm.atlassian.net/browse/LST-54
secao: NUC
status: a-fazer
especialista: engenheiro-backend
---

# Relatórios Python rápidos: Streamlit + agente LangChain

**Plano:** `docs/planos/relatorios-gimi-teste.md`. **Depende de:** LST-51.

## Critérios de aceite

- [ ] Streamlit (Community Cloud) com KPIs gerais até setor, estado/região e data
- [ ] Agente LangChain que monta gráficos a partir de pedidos em português, só leitura e com SQL conferido
- [ ] Plano B: HTML interativo (Plotly)
- [ ] LLM gratuita (decisão do Tiago, 26/11): Gemini Flash do AI Studio, com Groq de plano B; a LLM só recebe a pergunta e os nomes das colunas, nunca linhas
- [ ] Pendências do Tiago: criar a chave gratuita do AI Studio e fazer o deploy no Community Cloud
