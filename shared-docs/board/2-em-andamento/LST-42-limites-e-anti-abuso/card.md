---
chave: LST-42
jira: https://adelecrm.atlassian.net/browse/LST-42
secao: OPS
status: em-andamento
especialista: engenheiro-backend
---

# Limites e anti-abuso da demonstração (tamanho, tempo, fila e limite por IP)

**Plano:** `docs/planos/painel-gratis-no-site.md`, fatia 5. **Depende de:** LST-39.

## Critérios de aceite

- [ ] Um arquivo, CSV ou Excel, de até 5 MB e 50 mil linhas; recusa com mensagem clara
- [ ] Análise com no máximo 60 segundos
- [ ] Fila de 1 por vez (Render gratuito, 512 MB); quem chega vê "você é o próximo"
- [ ] Limite por IP: 5 análises por hora e 20 por dia, guardado só em memória
- [ ] Turnstile fica fora por ora: só entra se houver abuso (decisão do grill do LST-37)

## Verificação

`uv run pytest -q` + os critérios acima.
