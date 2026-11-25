---
type: regra
description: Todo card criado no Jira é espelhado no board local e sobe no mesmo commit; conferir os dois antes de dizer que terminou
---

Regra: card novo no Jira (épico, tarefa ou bug) só está criado quando também existe em `shared-docs/board/<coluna>/LST-n-slug/card.md` e esse arquivo foi commitado e enviado ao GitHub. Mudança de estado no Jira move a pasta no mesmo passo.

**Why:** em 25/11/2026 os cards LST-17 a LST-26 foram criados só no Jira e nunca subiram para o repositório; o Tiago pediu para isso nunca mais acontecer.

**How to apply:** depois de qualquer criação ou mudança de card, rode a JQL `project = LST AND issuetype != Epic ORDER BY key`, passe as chaves para `python scripts/conferir_board.py <chaves>`, que precisa sair 0, e só então faça commit, push e o relato ao Tiago.
