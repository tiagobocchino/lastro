---
chave: LST-44
jira: https://adelecrm.atlassian.net/browse/LST-44
secao: OPS
status: a-fazer
especialista: engenheiro-backend
---

# Funil anônimo da demonstração e ligação com o atendimento (WhatsApp e LST-24)

**Plano:** `docs/planos/painel-gratis-no-site.md`, fatia 7. **Depende de:** LST-39.

## Critérios de aceite

- [ ] `interno.demo_eventos` com etapa, duração, faixa de tamanho, número de colunas e visual escolhido, sem IP e sem nada da planilha
- [ ] Funil no painel de operação (`lastro painel`): subiu → painel → clicou para conversar
- [ ] O clique para conversar leva o tipo de painel na mensagem do WhatsApp, nunca os dados
- [ ] Teste: nenhum evento contém valor da planilha

## Verificação

`uv run pytest -q` + os critérios acima.
