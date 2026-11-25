# AGENTS.md · Lastro

Plataforma de agentes de análise de dados (Python, FastAPI, DuckDB, SQLite/Supabase). Mesmo método de trabalho do LixumLp e do AdeleCRM-2.0.

## Regras que não se negociam

1. **Fonte primária só em leitura.** Na credencial (conector abre em modo leitura) e no código (`lastro/somente_leitura.py`). Escrita só no sandbox e no staging da demanda.
2. **Nada sai sem duas camadas.** Auditor técnico + revisor de negócio humano.
3. **Grill antes de construir.** Vale para o produto (o Orquestrador) e para quem desenvolve o produto (`/grill-with-docs`).
4. **Contexto por busca.** Agente recebe o índice da Caixa e busca; não carrega o acervo no prompt.
5. **Grátis por padrão.** Recurso pago entra com a conta do cliente.
6. **Tenant em tudo.** Toda tabela tem `tenant_id`; todo acesso passa por `Repo(con, tenant)` local ou RLS no Supabase.

## Fluxo de trabalho

`/grill-with-docs` → `/to-spec` → `/to-tickets` → `/implement` por ticket (com `/tdd` e `/code-review`) → revisão → merge.

- Cards e tickets em `shared-docs/board/<coluna>/LST-n-slug/`.
- Termo de domínio resolvido vai para `CONTEXT.md`; decisão difícil de reverter vai para `docs/adr/`; armadilha que custou tempo vai para `docs/memory/`.
- Recomende sempre o próximo passo do fluxo.

## Como mexer em cada parte

- **Agente novo**: crie `skills/<nome>/SKILL.md` (frontmatter `name`, `description`; seções curtas) e a classe em `lastro/agents/`, herdando `Agente`. Liberdades novas entram em `lastro/politica.py` e no `politica.yaml` do tenant, desligadas por padrão.
- **Conhecimento novo para os agentes**: nota em `caixa/global/<tipo>/` com frontmatter (`name`, `description`, `type`, `tags`). Uma nota, um assunto. Descrição com dois-pontos vai entre aspas.
- **Trilha de nuvem**: playbook em `caixa/global/trilhas/` e, quando houver código, um gerador por trilha a partir do modelo do Arquiteto.

## Verificação

```bash
uv run pytest -q
uv run lastro demo
```

QA do portal: subir `uv run lastro serve`, fazer o fluxo login → demanda → grill → rodar → revisar com Playwright em 375px e 1440px, sem rolagem horizontal.

## Segredos

Nunca em arquivo versionado. `.env` local copiado de `.env.example`; em produção, variáveis do servidor e Supabase Vault.
