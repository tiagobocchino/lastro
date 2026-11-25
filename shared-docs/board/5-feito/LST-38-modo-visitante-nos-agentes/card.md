---
chave: LST-38
jira: https://adelecrm.atlassian.net/browse/LST-38
secao: NUC
status: feito
especialista: engenheiro-backend
---

# Modo visitante nos agentes: ADR 0010, RepoMemoria e nenhuma gravação fora da sessão

**Plano:** `docs/planos/painel-gratis-no-site.md`, fatia 1.

## Critérios de aceite

- [x] ADR 0010: demonstração no site com conferência automática (camada 1) e sem revisão humana, marcada como "demonstração". Não vale para o produto
- [x] `RepoMemoria`: mesma interface do Repo, só em memória (demanda, fontes e eventos da sessão)
- [x] Modo visitante na Plataforma: sem espelho no Storage; o Explorador não grava nota na Caixa; o grill não lê nem memoriza decisões; LLM desligado
- [x] Teste: uma análise completa em modo visitante não muda a Caixa global, não grava no banco, não chama o Storage nem faz chamada HTTP de saída

## Verificação

`uv run pytest -q` + os critérios acima.

## Evidência (25/11)

**O que entrou:**
- `Plataforma.visitante(cfg, pasta_sessao)` aponta tudo o que a análise grava para a pasta da sessão: fontes, sandbox, notas do Explorador, decisões do grill, política, gold e relatório. Assim o Explorador e o grill continuam funcionando, mas o que gravam morre com a sessão. Nessa pasta:
  - `RepoMemoria` (`lastro/memoria.py`) no lugar do banco, com `apagar()` para o recibo;
  - sem espelho;
  - LLM e embedder desligados.
- Resultado marcado `modo = "demonstracao"`, e `revisar` é recusado nesse modo.
- ADR 0010 registra a exceção das duas camadas, só para a demonstração.

**Achado:** o cache de vetores da busca semântica (`LASTRO_HOME/vetores.db`) guardaria o texto das notas do visitante, com valores de amostra da planilha, fora da sessão. Por isso o embedder fica desligado no modo visitante, e o teste cobre isso.

**Teste:** `tests/test_visitante.py` roda uma análise completa com LLM e embedder **ligados** na configuração e prova:
- nenhuma chamada HTTP de saída;
- nenhum uso do Storage;
- Caixa global sem nenhuma mudança;
- `LASTRO_HOME` sem nenhuma mudança;
- nenhum sandbox temporário sobrando;
- tudo gravado dentro da sessão;
- KPI do painel igual ao total auditado.

Suíte completa: **244 passed**.
