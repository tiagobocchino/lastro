---
chave: LST-45
jira: https://adelecrm.atlassian.net/browse/LST-45
secao: NUC
status: feito
especialista: engenheiro-de-dados
---

# Lições do dia a dia de BI viram regras dos agentes

**Pedido do Tiago (25/11):** aplicar o dia a dia de trabalhar com IA e BI, visto nas outras conversas, como contexto de resolução de problemas e regras para o agente ficar mais inteligente.

## Critérios de aceite

- [x] As sessões de BI lidas e cada problema real mapeado para uma regra (`docs/conhecimento/licoes-de-bi.md`)
- [x] 10 notas novas na Caixa global (6 métodos e 4 erros conhecidos), achadas pela busca com as perguntas típicas
- [x] Explorador mede a sujeira de texto: grafias diferentes, marcadores de vazio e acentos quebrados
- [x] Engenheiro faz trim e colapsa espaços na silver, com SQL portável para as trilhas
- [x] Auditor avisa o que some do gráfico por dimensão (linhas e valor), as grafias, os marcadores e os nulos na medida (cartão × tabela)
- [x] Grill explica que a data escolhida muda a contagem e mostra quantas estão preenchidas
- [x] Intérprete responde "por que não bate?" com os motivos medidos, também no portal
- [x] Testes em `tests/test_licoes_de_bi.py`; suíte inteira verde

## Verificação

`uv run pytest -q`: 322 testes passando. Lint sem erro novo.
