---
chave: LST-39
jira: https://adelecrm.atlassian.net/browse/LST-39
secao: NUC
status: em-andamento
especialista: engenheiro-backend
---

# API de demonstração /api/demo: sessão temporária, perfil, grill rápido, painel e apagamento com recibo

**Plano:** `docs/planos/painel-gratis-no-site.md`, fatia 2. **Depende de:** LST-38.

## Critérios de aceite

- [ ] Rotas públicas sem login: enviar arquivo (ou usar o exemplo) → perfil → perguntas → painel → apagar
- [ ] Sessão em `tmp/demo-<id aleatório>`, com no máximo 15 minutos de vida; varredura a cada 5 minutos apaga as abandonadas
- [ ] Entrega do painel (HTML) na resposta e, em seguida, apagamento com recibo: arquivos, tabelas, bytes e hora
- [ ] Logs só com etapa, tempo, tamanho e número de colunas, nunca valores ou nomes de coluna
- [ ] Testes provam que, depois da sessão, nada sobra no disco, no banco, no Storage nem no log

## Verificação

`uv run pytest -q` + os critérios acima.
