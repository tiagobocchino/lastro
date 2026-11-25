---
chave: LST-43
jira: https://adelecrm.atlassian.net/browse/LST-43
secao: MKT
status: a-fazer
especialista: engenheiro-frontend
---

# Seção "teste com a sua planilha" no site, servido pelo Render

**Plano:** `docs/planos/painel-gratis-no-site.md`, fatia 6. **Depende de:** LST-39, LST-40, LST-42.

## Critérios de aceite

- [ ] O site passa a ser servido pelo Render até existir domínio (LST-23)
- [ ] Seção nova com: envio ou planilha de exemplo, aceite dos termos e aviso de não subir dado pessoal; perguntas, painel na tela, download do HTML e recibo de apagamento; chamada para conversar (WhatsApp ou formulário do LST-24), com o Power BI como gancho
- [ ] Contato depois do painel e opcional
- [ ] Copy pela skill `marca-e-copy`
- [ ] QA em 375 px e 1440 px e Lighthouse acima de 90

## Verificação

`uv run pytest -q` + os critérios acima.
