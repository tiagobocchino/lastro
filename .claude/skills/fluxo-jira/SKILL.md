---
name: fluxo-jira
description: "Regras do fluxo de cards do projeto no Jira (Atlassian): estados, modelo de card, rótulos por seção e espelho local. Use antes de criar, mover ou comentar qualquer card, e quando PO, QA ou gerente de seção forem acionados."
---

# Onde está o fluxo

- Jira: site `adelecrm.atlassian.net` (cloudId `4e6687a8-3f5c-45fc-afeb-f40ff38b3244`), projeto `LST` (Scrum, criado pelo Tiago). Ferramentas: MCP `Atlassian_MCP` (`createJiraIssue`, `searchJiraIssuesUsingJql`, `transitionJiraIssue`, `addOrEditJiraIssueComment`, `editJiraIssue`).
- Seções em `docs/agents/secoes.yaml`. Cada seção é um épico com rótulo `secao-<CHAVE>` (NUC, INT, MKT, CON).
- Sem acesso ao Jira (projeto ainda não criado, sessão sem o conector): use o espelho `shared-docs/board/<coluna>/LST-n-slug/card.md`, com o mesmo modelo. Ao voltar o acesso, o gerente sobe os cards e anota a chave do Jira no `card.md`.

# Estados (nenhum card pula estado)

| Estado | Quem move para cá | Condição |
| --- | --- | --- |
| Backlog | PO | Card escrito no modelo |
| Pronto | PO | Critérios de aceite verificáveis, grill respondido, seção e especialista indicados |
| Em execução | Gerente | Especialista alocado; no máximo 2 cards em execução por seção |
| Em QA | Gerente | Especialista entregou com evidência (comando rodado, saída) |
| Feito | QA | Cada critério conferido com evidência própria do QA |

QA reprovou: volta para Em execução com comentário "reprovado: <critério> · <evidência>". Bloqueio: rótulo `bloqueado` + comentário com o que falta e de quem.

# Modelo de card

```
Título: <verbo no infinitivo> <resultado>   (ex.: Medir o contrato real da API do Sienge)
Seção: NUC | INT | MKT | CON
Por quê: uma frase do valor para o usuário
Critérios de aceite:
- [ ] verificável por comando, tela ou número
Especialista: <nome em .claude/agents/>
Verificação: comandos da seção (secoes.yaml) + os do card
```

# Regras

- Um card cabe numa sessão. Maior que isso, o PO quebra.
- Comentário de trabalho sempre com evidência: comando, saída resumida, caminho do arquivo, print.
- Ninguém escreve token, senha ou chave em card, comentário ou anexo.
