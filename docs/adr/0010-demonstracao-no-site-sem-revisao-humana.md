# ADR 0010: demonstração no site com conferência automática e sem revisão humana

**Status:** aceito · 2026-11-25 · cards LST-37 (plano) e LST-38

## Contexto

O site vai deixar o visitante subir uma planilha e sair com um painel, sem cadastro (plano em `docs/planos/painel-gratis-no-site.md`). A regra "nada sai sem duas camadas" (AGENTS.md) pede auditor técnico e revisor de negócio humano. No site não há revisor: o visitante é anônimo e o dado é dele.

## Decisão

- Existe um **modo visitante** (`Plataforma.visitante`) que roda os mesmos agentes.
  - A **camada 1** (Auditor) roda normalmente, e o resultado dela aparece no painel.
  - A **camada 2** (revisor humano) não existe, e `revisar` é recusado nesse modo.
- Todo resultado do modo visitante sai marcado `modo = "demonstracao"`, e o site mostra "demonstração: conferência automática, sem revisão humana".
- O modo visitante não guarda nada fora da pasta temporária da sessão:
  - usa `RepoMemoria` em vez de banco;
  - não usa o espelho no Storage;
  - deixa o LLM e o embedder desligados (o cache de vetores ficaria em `LASTRO_HOME`);
  - aponta a Caixa da empresa e as decisões do grill para dentro da sessão.
- **A exceção vale só para a demonstração do site.** Entrega a cliente continua exigindo as duas camadas.

## Consequências

- O visitante vê o valor do Lastro sem atrito. O que vende o produto contratado é justamente o que falta na demonstração: a revisão humana, as fontes ligadas e a atualização diária.
- `tests/test_visitante.py` prova que uma análise completa nesse modo não toca a Caixa global, o banco, o Storage, a rede nem `LASTRO_HOME`.
