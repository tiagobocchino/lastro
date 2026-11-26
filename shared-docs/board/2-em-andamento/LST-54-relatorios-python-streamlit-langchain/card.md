---
chave: LST-54
jira: https://adelecrm.atlassian.net/browse/LST-54
secao: NUC
status: em-andamento
especialista: engenheiro-backend
---

# Relatórios Python rápidos: Streamlit + agente LangChain

**Plano:** `docs/planos/relatorios-gimi-teste.md`. **Depende de:** LST-51.

## Critérios de aceite

- [x] Streamlit com KPIs gerais até empresa, setor, estado/região e data (`lastro/rapido/app.py`)
- [x] Agente LangChain que monta gráficos a partir de pedidos em português: a LLM devolve um plano JSON, e o Lastro valida, monta o SQL (trava `somente_leitura`, valor como parâmetro) e roda
- [ ] Plano B: HTML interativo (Plotly)
- [ ] LLM gratuita (decisão do Tiago, 26/11): Gemini Flash do AI Studio, com Groq de plano B; a LLM só recebe a pergunta e os nomes das colunas, nunca linhas
- [ ] Pendências do Tiago: criar a chave gratuita do AI Studio e fazer o deploy no Community Cloud

## Evidência (26/11)

- **Código:**
  - `lastro/rapido/nucleo.py`: catálogo só com nomes, plano validado contra lista fechada, SQL montado pelo Lastro, interpretação por LangChain + Gemini ou por palavras-chave;
  - `lastro/rapido/app.py`: abas Indicadores e Pergunte;
  - `lastro/rapido/requirements.txt` para o Streamlit Cloud;
  - extra `rapido` no pyproject.
- **Testes:** `tests/test_rapido.py`, 7 testes:
  - detalhe além da demonstração é recusado;
  - injeção no filtro não vaza;
  - RH sem valor vira contagem;
  - a LLM falsa recebe só a pergunta e o catálogo, nenhum valor;
  - o app abre pelo AppTest com os números certos.
  - A suíte inteira está verde (346).
- **Falta (Tiago):** criar a chave gratuita no AI Studio e fazer o deploy no Streamlit Community Cloud com os secrets.
