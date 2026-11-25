---
chave: LST-24
jira: https://adelecrm.atlassian.net/browse/LST-24
secao: OPS
status: bloqueado
especialista: engenheiro-frontend
---

# Montar o funil de atendimento: Forms, Planilha, Apps Script, Gmail e Agenda

**Por quê:** Todo lead do site precisa chegar à equipe na hora e virar conversa marcada, sem ferramenta paga.

## Critérios de aceite

- [ ] Formulário curto ligado ao CTA do site
- [x] Planilha de leads com status
- [x] Apps Script avisa lixumlabs@gmail.com a cada lead (código + teste; falta autorizar)
- [ ] Página de agendamento da Agenda; reunião no Meet
- [ ] Teste com lead fictício de ponta a ponta

## Verificação

Comandos da seção OPS em `docs/agents/secoes.yaml` + os critérios acima.

## Andamento (25/11)

- Feito: `infra/atendimento/funil.gs` cria o formulário, liga à planilha, instala o gatilho, marca `status = novo`, avisa a equipe e responde o lead com o link da Agenda.
- Feito: `node infra/atendimento/funil.test.js` com lead fictício: 11 checagens ok.
- Feito: planilha "Lastro · Leads" na pasta Lastro do Drive.
- Guia: `docs/infra/funil-atendimento.md`.

## Bloqueio

Passos do Tiago (conta Google): criar a página de agendamento, colar o script e rodar `configurar`, mandar o link do formulário. Depois: link no site e teste de ponta a ponta.
