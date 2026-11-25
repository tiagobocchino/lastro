---
chave: LST-34
jira: https://adelecrm.atlassian.net/browse/LST-34
secao: NUC
status: a-fazer
especialista: engenheiro-de-dados
---

# Agentes criam e editam dashboards (Python, Power BI e Looker Studio)

**Por quê:** além de responder perguntas, o agente precisa montar o painel: em Python (gratuito, para o nosso sistema e os exemplos do site) e, para quem já tem BI, deixar o painel pronto na ferramenta do cliente.

## Critérios de aceite

- [ ] Dashboard em Python (HTML estático, sem custo) gerado pelo agente a partir da gold de uma demanda aprovada
- [ ] Projeto do Power BI em formato aberto (PBIP/TMDL) gerado pelo agente: modelo, relações e medidas DAX, que abre no Power BI Desktop gratuito
- [ ] Looker Studio: link de criação (Linking API, gratuita) apontando para a fonte do cliente
- [ ] O agente edita um painel existente a pedido (nova medida, novo visual) sem quebrar o que já existe
- [ ] Toda mudança no painel fica no rastro da demanda

## Verificação

`uv run pytest -q` + abrir o PBIP no Power BI Desktop e o HTML no navegador (QA em 375 px e 1440 px).

## Fora do escopo agora

Publicação no serviço pago do Power BI ou do Looker.

## Origem

Visão do Tiago em 25/11: o Lastro conecta bases e APIs aos BIs self-service; nosso próprio sistema e os exemplos do site usam dashboards em Python (gratuito), e Looker Studio no pior caso.
