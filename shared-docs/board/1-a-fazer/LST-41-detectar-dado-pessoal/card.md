---
chave: LST-41
jira: https://adelecrm.atlassian.net/browse/LST-41
secao: NUC
status: a-fazer
especialista: engenheiro-de-dados
---

# Detectar dado pessoal (CPF, CNPJ, e-mail, telefone) no Explorador

**Plano:** `docs/planos/painel-gratis-no-site.md`, fatia 4.

## Critérios de aceite

- [ ] O Explorador marca colunas com cara de CPF, CNPJ, e-mail ou telefone, pelo formato dos valores e não só pelo nome
- [ ] No modo visitante essas colunas ficam fora do painel e o visitante é avisado
- [ ] No produto, o aviso aparece no perfil da fonte e nada muda no resto
- [ ] Testes com valores reais e falsos positivos comuns, como código de produto numérico

## Verificação

`uv run pytest -q` + os critérios acima.
