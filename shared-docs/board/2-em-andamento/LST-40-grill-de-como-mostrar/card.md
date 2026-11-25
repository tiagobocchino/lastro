---
chave: LST-40
jira: https://adelecrm.atlassian.net/browse/LST-40
secao: NUC
status: em-andamento
especialista: engenheiro-backend
---

# Grill de "como mostrar" no modo visitante vira a especificação do painel

**Plano:** `docs/planos/painel-gratis-no-site.md`, fatia 3. **Depende de:** LST-38.

## Critérios de aceite

- [ ] Até 4 perguntas curtas, cada uma com sugestão pronta: o que medir; quebrado por quê; qual período; como mostrar (número, ranking, evolução ou tabela)
- [ ] As respostas viram a especificação do painel do LST-34 (`paineis.py`), sem passar por outro formato
- [ ] Teste: cada combinação de respostas gera uma especificação válida contra o gold

## Verificação

`uv run pytest -q` + os critérios acima.
