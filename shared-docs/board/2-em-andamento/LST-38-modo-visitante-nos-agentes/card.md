---
chave: LST-38
jira: https://adelecrm.atlassian.net/browse/LST-38
secao: NUC
status: em-andamento
especialista: engenheiro-backend
---

# Modo visitante nos agentes: ADR 0010, RepoMemoria e nenhuma gravação fora da sessão

**Plano:** `docs/planos/painel-gratis-no-site.md`, fatia 1.

## Critérios de aceite

- [ ] ADR 0010: demonstração no site com conferência automática (camada 1) e sem revisão humana, marcada como "demonstração". Não vale para o produto
- [ ] `RepoMemoria`: mesma interface do Repo, só em memória (demanda, fontes e eventos da sessão)
- [ ] Modo visitante na Plataforma: sem espelho no Storage; o Explorador não grava nota na Caixa; o grill não lê nem memoriza decisões; LLM desligado
- [ ] Teste: uma análise completa em modo visitante não muda a Caixa global, não grava no banco, não chama o Storage nem faz chamada HTTP de saída

## Verificação

`uv run pytest -q` + os critérios acima.
