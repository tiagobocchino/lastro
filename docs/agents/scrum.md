# Scrum no Lastro

Como o projeto aplica o Scrum Guide no Jira `LST` (board 1). Os papéis do Scrum mapeiam para os agentes de seção.

| Scrum | No Lastro |
| --- | --- |
| Product Owner | Tiago, apoiado pelo `po-secao` de cada seção (ordena o backlog da seção) |
| Scrum Master | `gerente-secao` (remove impedimentos, protege o limite de 2 cards em execução) |
| Developers | especialistas em `.claude/agents/` + `qa-secao` |
| Product Backlog | backlog do board, ordenado (rank) por valor e risco; segurança e dado errado sempre no topo |
| Sprint Backlog | cards da sprint ativa |
| Increment | release (fix version) liberada |

## Cadência

Sprints de 2 semanas, de quarta a quarta.

| Evento | Quando | Quem conduz | Saída |
| --- | --- | --- | --- |
| Sprint Planning | 1º dia da sprint | PO + gerentes | meta da sprint (campo "goal") e cards puxados com estimativa |
| Daily | todo dia útil, 15 min | gerente de cada seção | comentário no épico: feito ontem, hoje, impedimentos |
| Refinamento | meio da sprint | PO da seção | cards do topo do backlog com critérios verificáveis, estimativa e rótulo `pronto` |
| Sprint Review | último dia | PO + Tiago | release liberada ou cards devolvidos ao backlog |
| Retrospectiva | último dia, depois da review | gerentes | uma nota em `docs/memory/` por lição que custou tempo |

## Estimativa

Story points em Fibonacci (1, 2, 3, 5, 8, 13) no campo "Story point estimate". Card acima de 8 é quebrado pelo PO antes de entrar em sprint. Capacidade de partida: 12 pontos por sprint (ajustar pela velocidade das 2 primeiras sprints).

## Definition of Done

Um card só vai para Feito quando o `qa-secao` confirmou, com evidência própria:

1. Todos os critérios de aceite marcados, cada um com comando, saída ou print.
2. `uv run pytest -q` verde; conector alterado também com a coleção Postman passando no Newman.
3. Tela alterada conferida em 375px e 1440px, temas claro e escuro.
4. Nenhum segredo em código, card ou comentário.
5. Documentação tocada atualizada (`CONTEXT.md`, ADR, `docs/memory/`, nota da Caixa).
6. Commit na `main` com o card no assunto (ex.: `LST-11: ...`).

## Releases

| Versão | Datas | Conteúdo |
| --- | --- | --- |
| v0.1 Demo | liberada em 25/11/2026 | LST-12, LST-13, LST-16 |
| v0.2 Piloto | 25/11 a 09/12/2026 · Sprint 1 | LST-5, LST-11, LST-14 |
| v0.3 Multiempresa | 09/12 a 23/12/2026 · Sprint 2 | LST-6, LST-9, LST-8 |
| v0.4 Operação | 04/01 a 29/01/2027 | LST-7, LST-10, LST-15 |

Dependências registradas no Jira: LST-9 bloqueia LST-8; LST-6 bloqueia LST-7; LST-15 relaciona-se com LST-11.
