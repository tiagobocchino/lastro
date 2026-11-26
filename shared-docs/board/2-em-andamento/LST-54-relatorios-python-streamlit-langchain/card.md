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
- [x] Plano B: HTML interativo (Plotly). Não foi preciso: o Streamlit Community Cloud roda de graça
- [x] LLM gratuita (decisão do Tiago, 26/11): Gemini Flash do AI Studio, com Groq de plano B; a LLM só recebe a pergunta e os nomes das colunas, nunca linhas
- [x] Pendências do Tiago: chave gratuita do AI Studio criada e deploy feito no Community Cloud (26/11)

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

## No ar (26/11)

- O Tiago fez o deploy. A aba Indicadores mostrou 211.290.267,16 em vendas, que bate com o BI.
- Bugs achados no uso e corrigidos:
  - `ResourceInUseException`: a conexão em cache era compartilhada entre as sessões; agora há um cursor por sessão (70e2798);
  - RH sem coluna de valor gerava colunas repetidas na conferência, e uma aba com erro derrubava a outra; agora as abas são isoladas (041b243);
  - o Google desligou o `gemini-2.0-flash`; agora o app usa o `gemini-flash-latest` e cai para palavras-chave se o modelo falhar (033aab6).
- Layout no padrão do painel de entrega: filtros, 4 cartões com o mesmo período do ano anterior, evolução, ranking top 10 e conferência (7ce52ff). Manual em `docs/infra/streamlit.md`.
- Empresas da gimi-teste com nomes fictícios (alfa, beta, gama e delta), trocados direto no banco do BI; ver `docs/memory/gimi-teste-nomes-no-banco.md`.
- **Para fechar:** o Tiago confirma o "Pergunte" com o Gemini respondendo no app publicado.
