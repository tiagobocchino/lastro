---
chave: LST-19
jira: https://adelecrm.atlassian.net/browse/LST-19
secao: OPS
status: bloqueado
especialista: engenheiro-backend
---

# Criar conta Google Cloud, projeto lastro-prod e orçamento com alerta

**Por quê:** O Google exige conta de faturamento até para a camada gratuita; sem alerta, um erro vira cobrança.

## Critérios de aceite

- [ ] Projeto lastro-prod ligado à conta de faturamento
- [ ] Orçamento com alertas em R$ 1 e R$ 10
- [ ] APIs habilitadas: Cloud Run, Cloud Storage, Secret Manager, Cloud Scheduler, Artifact Registry
- [ ] Passo a passo pela skill wizard (cartão e termos são do Tiago)

## Verificação

Comandos da seção OPS em `docs/agents/secoes.yaml` + os critérios acima.

## Preparado (25/11)

- Guia para o Tiago: `docs/infra/conta-google-cloud.md`. Fatos conferidos nas páginas oficiais em `docs/infra/fontes/`:
  - o teste gratuito fecha em 90 dias e apaga tudo depois de mais 30;
  - o orçamento comum só avisa;
  - existe teto de gasto para o Cloud Run;
  - o Cloud Storage só é gratuito nas regiões dos EUA.
- Script para o Cloud Shell: `scripts/gcp/criar_projeto_lastro.sh`. Ele cria o projeto, liga ao faturamento, habilita as 8 APIs e cria o orçamento de R$ 10 com alertas em R$ 1, R$ 10 e previsão. Pode rodar de novo sem refazer o que já existe.
- O roteiro foi testado com um `gcloud` falso, conferindo a ordem e os comandos. A execução real fica com o Tiago (cartão e termos).
- Falta: Tiago fazer os passos 1 a 6 e mandar o ID do projeto.

## Bloqueio (25/11)

A ativação do faturamento falhou com `OR_BACR2_59`. O Tiago escolheu o plano B (ADR 0009). O card volta a andar se o Google liberar o faturamento.
