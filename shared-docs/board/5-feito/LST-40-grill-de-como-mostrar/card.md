---
chave: LST-40
jira: https://adelecrm.atlassian.net/browse/LST-40
secao: NUC
status: feito
especialista: engenheiro-backend
---

# Grill de "como mostrar" no modo visitante vira a especificação do painel

**Plano:** `docs/planos/painel-gratis-no-site.md`, fatia 3. **Depende de:** LST-38.

## Critérios de aceite

- [x] Até 4 perguntas curtas, cada uma com sugestão pronta: o que medir; quebrado por quê; qual período; como mostrar (número, ranking, evolução ou tabela)
- [x] As respostas viram a especificação do painel do LST-34 (`paineis.py`), sem passar por outro formato
- [x] Teste: cada combinação de respostas gera uma especificação válida contra o gold

## Verificação

`uv run pytest -q` + os critérios acima.

## Evidência (25/11)

**As perguntas do visitante** (`demo.perguntas_visitante`) são no máximo 4, cada uma com sugestão e opções. Só aparecem as que fazem sentido para a planilha:
1. "Qual valor você quer acompanhar?": colunas numéricas.
2. "Quebrado por qual categoria?": as mesmas dimensões que o Arquiteto vai modelar. A regra agora fica num lugar só, `dimensoes_candidatas`.
3. "No tempo, agrupar por mês ou por ano?": só se houver data.
4. "Como você quer ver?": ranking (barras), tabela, evolução no tempo, só o número.

A chave, a data e o recorte ficam com a sugestão do Orquestrador, sem ocupar o visitante.

**`paineis.para_visitante`**: as respostas viram direto a especificação do LST-34. O número principal (KPI) aparece sempre, mais o visual escolhido.

**Resposta fora das opções** volta com 400 antes de rodar, e a sessão continua aberta para o visitante corrigir.

**Testes** (`tests/test_demo.py`, mais 9):
- no máximo 4 perguntas, todas com a sugestão entre as opções;
- cada formato gera o visual certo (ranking por estado, tabela por segmento, evolução por ano e por mês, só o número);
- resposta inválida não perde a sessão;
- planilha só com números oferece apenas "só o número";
- **todas as 40 combinações** (5 categorias × 2 períodos × 4 formatos) geram especificação válida contra o gold. O KPI bate com o total conferido pela auditoria, já sem os contratos repetidos.

Suíte completa: **261 passed**.
