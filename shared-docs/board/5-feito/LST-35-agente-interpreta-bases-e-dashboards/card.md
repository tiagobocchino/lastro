---
chave: LST-35
jira: https://adelecrm.atlassian.net/browse/LST-35
secao: NUC
status: feito
especialista: engenheiro-backend
---

# Agente interpreta bases e dashboards para usar nas conversas e nos insights

**Por quê:** o operador conversa com o agente sobre o que está nas bases e nos painéis; o agente precisa ler esse conteúdo e devolver insights com prova (consulta e número conferível), sem alterar a fonte.

## Critérios de aceite

- [x] O agente lê a gold, os relatórios e as definições dos painéis (Python e PBIP) da empresa
- [x] Cada insight vem com a consulta que o sustenta e passa pela auditoria de duas camadas
- [x] Só leitura: nenhuma escrita na fonte ou no BI do cliente
- [x] Teste: insight sem prova é recusado; dado de outra empresa nunca entra no contexto

## Verificação

`uv run pytest -q` + uma conversa de ponta a ponta no portal.

## Origem

Visão do Tiago em 25/11: o Lastro conecta bases e APIs aos BIs self-service; nosso próprio sistema e os exemplos do site usam dashboards em Python (gratuito), e Looker Studio no pior caso.

## Evidência (25/11)

**Intérprete** (`lastro/agents/interprete.py`, skill `skills/interprete`), determinístico (ADR 0003).

- **O que lê:** só a pasta da demanda aprovada:
  - o gold, num DuckDB em memória e travado (sem acesso externo, sem extensão, `lock_configuration`);
  - a especificação do painel, que é a mesma do HTML e do PBIP (LST-34). A medida e o eixo dos insights vêm dela;
  - o total do relatório aprovado.
  - Um link no gold que aponte para fora da pasta é recusado.
- **Tipos de insight:** total ("bate com o total do relatório aprovado"), quem lidera, quem fica por último, concentração nos 3 maiores e evolução do último mês (a variação é calculada na própria consulta). Pergunta aberta vira resumo, e cada resposta traz sugestões.
- **Camada 1:** `auditar` refaz a consulta numa conexão separada, compara o resultado e recusa insight sem consulta, com resultado divergente, com número no texto que não está no resultado ou com SQL de escrita. Os recusados vão para o rastro (`recusou_insight`).
- **Camada 2:** cada turno nasce "aguardando revisor". Revisor ou admin aprova ou reprova; o demandante recebe 403.
- **API:** `GET/POST /api/demandas/{id}/conversa` (só em demanda aprovada) e `POST …/conversa/{n}/revisao`. A conversa fica em `demandas/<id>/conversa.json`, dentro da pasta da empresa. Rastro: `interpretou`, `recusou_insight`, `revisou_insights`.
- **Portal:** bloco "Conversar com os dados" com histórico, sugestões, "ver a consulta e o resultado" e o estado das camadas, além dos botões do revisor.

**Testes:** `tests/test_interprete.py`, 9 testes.
- Quem lidera com prova: Eva Martins, 2.567.582,13.
- Total igual ao relatório.
- Categoria citada (estado), concentração e tendência.
- Resumo com sugestões.
- Leitura da definição do painel (medida renomeada aparece no insight).
- **Insight sem prova recusado:** sem SQL, número adulterado, resultado adulterado e `DROP`.
- Gold intacto (hash) e conexão travada.
- Link para o gold de outra empresa recusado.
- API ponta a ponta com revisor, e outra empresa recebe 404 em tudo.

Suíte completa: **307 passed**.

**Conversa de ponta a ponta no portal** (Playwright, 1440 e 375 px, sem erro de JavaScript), conferida com prints em `evidencias/`:
- a Ana pergunta "Quem lidera em valor vendido por estado? Está concentrado?";
- a resposta é "PR lidera … 2.577.907,68 (18,4% do total)" e "Os 3 maiores em estado concentram 51,9%";
- o Rui aprova os insights.

**Não usa o BI do cliente:** lê o gold de dentro do Lastro. A conexão externa (LST-33 e LST-36) é independente.
