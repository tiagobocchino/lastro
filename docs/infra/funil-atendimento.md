# Funil de atendimento · LST-24

Lead do site → formulário → planilha com status → aviso para a equipe → e-mail para o lead com o link de agendamento → conversa no Meet. Tudo em conta Google gratuita.

## Peças

| Peça | Onde está | Quem cria |
| --- | --- | --- |
| Planilha "Lastro · Leads" | pasta Lastro do Drive (criada em 25/11) | feito |
| Script do funil | `infra/atendimento/funil.gs`, teste em `funil.test.js` | feito |
| Formulário "Lastro · testar com os meus dados" | criado pelo script (`configurar`) | Tiago roda uma vez |
| Página de agendamento (30 min, Meet) | Google Agenda | Tiago, no navegador |
| Link no site | botão do cartão de contato em `site/index.html` | depois do formulário existir |

## Passos do Tiago (uma vez, ~10 min)

1. Google Agenda no computador → **Criar** → **Página de agendamento**. Duração 30 min, conferência pelo Google Meet, horários em que você atende. Salve e copie o link em **Compartilhar**.
2. Abra a planilha "Lastro · Leads" → **Extensões** → **Apps Script**. Apague o conteúdo e cole `infra/atendimento/funil.gs`. Em `LINK_AGENDA`, cole o link do passo 1.
3. Escolha a função `configurar` → **Executar** → autorize com a sua conta (o Google avisa que o app não é verificado: **Avançado** → **Acessar**). O log mostra o link do formulário.
4. Mande o link do formulário na conversa: eu coloco no site e faço o teste de ponta a ponta.

## Teste de ponta a ponta (depois dos passos)

Responder o formulário com o lead fictício de `funil.test.js` (use um e-mail seu) e conferir:

- linha nova na aba de respostas com `status = novo`;
- e-mail "Lead novo no Lastro: Construtora Exemplo" em lixumlabs@gmail.com;
- e-mail "Recebemos a sua pergunta" no endereço do lead, com o link da Agenda;
- marcar um horário cria o evento com Meet.

## Limites da conta gratuita

- `MailApp` envia até 100 e-mails por dia em conta pessoal: cada lead usa 2. Acima de ~50 leads/dia, migrar para o Workspace.
- O status é atualizado à mão na planilha: `novo` → `conversa marcada` → `piloto` ou `descartado`.
