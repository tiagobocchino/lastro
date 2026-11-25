# Financeiro

A API de Financeiro tem como objetivo oferecer um conjunto de recursos para gerenciar de forma programática os principais aspectos financeiros de uma empresa, desde a criação de eventos de contas a receber ou pagar, passando pela gestão de contas financeiras, centros de custo, categorias, até a consulta de saldos. Com esta API, sistemas podem integrar de forma fluida com o módulo financeiro da Conta Azul, garantindo que lançamentos, saldos, classificações e relatórios estejam sempre sincronizados.
Se desejar aprofundar o entendimento das regras de negócio aplicadas pelo ERP, recomendamos, de forma opcional a consulta à nossa Central de Ajuda:
**Contas a pagar e receber:**
[https://ajuda.contaazul.com/hc/pt-br/sections/20564397198989-Lan%C3%A7amentos-financeiros-contas-a-receber-e-a-pagar](https://ajuda.contaazul.com/hc/pt-br/sections/20564397198989-Lan%C3%A7amentos-financeiros-contas-a-receber-e-a-pagar)
**Cadastro e gestão de contas financeiras:**
[https://ajuda.contaazul.com/hc/pt-br/sections/20546846147981-Cadastro-e-gest%C3%A3o-de-contas-financeiras](https://ajuda.contaazul.com/hc/pt-br/sections/20546846147981-Cadastro-e-gest%C3%A3o-de-contas-financeiras)
**Categorias financeiras e centro de custos:**
[https://ajuda.contaazul.com/hc/pt-br/sections/28553633338765-Categorias-financeiras-e-centros-de-custo](https://ajuda.contaazul.com/hc/pt-br/sections/28553633338765-Categorias-financeiras-e-centros-de-custo)
## Criar contas a pagar e a receber agora leva uma única chamada
> **Breaking change a partir de 18/10/2026.** A criação de contas a pagar e a receber deixa de retornar o protocolo: a resposta do `POST` já traz a conta criada, com o `id`. As rotas atuais continuam existindo, com o novo retorno, e há novas rotas com o mesmo comportamento.

**Novos endpoints (use estes):** criam a conta e devolvem o resultado na mesma chamada.
- `POST /v1/financeiro/contas-a-pagar`
- `POST /v1/financeiro/contas-a-receber`

**Endpoints atuais, que continuam existindo e passam a devolver a conta criada em vez do protocolo:**
- `POST /v1/financeiro/eventos-financeiros/contas-a-pagar`
- `POST /v1/financeiro/eventos-financeiros/contas-a-receber`

**Descontinuado em 18/10/2026:** `GET /v1/protocolo/{id}`. A API de Protocolos deixa de existir.
|  | Até 17/10/2026 | A partir de 18/10/2026 |
|  --- | --- | --- |
| Chamadas para criar e confirmar | 3: `POST`, `GET /v1/protocolo/{id}` e `GET .../eventos-financeiros/{id_evento}/parcelas` | 1: `POST` |
| Resposta do `POST` | `202` com `protocolo` e status `PENDING` | `201` com a conta criada, o `id` e as parcelas |
| Erros de validação | Só na consulta do protocolo (`ERROR`) | Na própria resposta do `POST`, com HTTP `400` |

**A sua integração é afetada se** cria contas a pagar ou a receber pela API **e** usa o protocolo retornado na criação ou consulta `GET /v1/protocolo/{id}`. Se for o seu caso, faça o ajuste até 18/10/2026, quando a API de Protocolos deixa de existir:
1. Leia o
`id`
 direto da resposta do
`POST`
, sem guardar nem consultar o protocolo.
2. Trate os erros na própria resposta do
`POST`
, que passam a voltar com status HTTP 4xx e a mensagem do erro.
3. Remova as rotinas de espera ou nova tentativa que aguardavam o protocolo sair de
`PENDING`
.
4. Precisa das parcelas? Elas já vêm em
`condicao_pagamento.parcelas`
, e com o
`id`
 da conta a consulta de parcelas continua funcionando como hoje.

Dúvidas ou ajuda com o prazo: [api@contaazul.com](mailto:api@contaazul.com).

Version: v1

## Servers

Servidor de produção
```
https://api-v2.contaazul.com
```

## Security

### BearerAuth

Token de autorização Bearer JWT

Type: http
Scheme: bearer
Bearer Format: JWT

## Download OpenAPI description

 - [Financeiro](https://developers.contaazul.com/_bundle/docs/financial-apis-openapi.yaml)

## v1

 - [GET /v1/centro-de-custo](https://developers.contaazul.com/docs/financial-apis-openapi/v1/searchcostcenters.md): Permite consultar os centros de custo cadastrados. Suporta filtros como página, tamanho de página, busca por texto, status (ativo/inativo/todos) e ordenação. Utilizado para consultar lançamentos finan
 - [POST /v1/centro-de-custo](https://developers.contaazul.com/docs/financial-apis-openapi/v1/createcostcenter.md): Permite criar um novo centro de custo, definindo campos como código, nome, parâmetros que ajudam a organizar os custos da empresa de forma estruturada.
 - [GET /v1/financeiro/eventos-financeiros/{id_evento}/parcelas](https://developers.contaazul.com/docs/financial-apis-openapi/v1/getinstallmentsbyeventid.md): Permite listar as parcelas vinculadas a um evento financeiro específico (id_evento). Útil para acompanhar cada parcela de um lançamento de contas a pagar ou receber, com seus valores, vencimentos e st
 - [GET /v1/categorias](https://developers.contaazul.com/docs/financial-apis-openapi/v1/searchcategories.md): Permite listar as categorias utilizadas para classificação de receitas ou despesas. Auxilia no controle, agrupamento e geração de relatórios financeiros baseados em categorias.
 - [GET /v1/categorias/configuracao-padrao](https://developers.contaazul.com/docs/financial-apis-openapi/v1/getdefaultcategoryconfig.md): Retorna o de-para entre as operações financeiras e as categorias configuradas para o tenant, incluindo opcionalmente a sugestão padrão de categoria para cada operação.
 - [GET /v1/financeiro/categorias-dre](https://developers.contaazul.com/docs/financial-apis-openapi/v1/searchdrecategories.md): Permite listar as categorias de DRE (Demonstração do Resultado do Exercício) usadas para a estrutura contábil-financeira da empresa, facilitando o fechamento financeiro e contábil.
 - [GET /v1/conta-financeira](https://developers.contaazul.com/docs/financial-apis-openapi/v1/searchfinancialaccounts.md): Permite consultar as contas financeiras existentes no sistema (contas bancárias, cartões, poupança, etc.). Suporta filtros como tipo de conta, nome, se estão ativas, entre outros.
 - [GET /v1/conta-financeira/{id_conta_financeira}/saldo-atual](https://developers.contaazul.com/docs/financial-apis-openapi/v1/searchbalancebyfinancialaccountid.md): Permite obter o saldo atual de uma conta financeira específica identificada por id_conta_financeira. Útil para monitoramento em tempo real de saldos das contas da empresa.
 - [GET /v1/financeiro/transferencias](https://developers.contaazul.com/docs/financial-apis-openapi/v1/searchaccountingexporttransfers.md): Permite consultar as transferências realizadas entre contas financeiras mediante filtros como período de datas e contas financeiras específicas. Para viabilizar a conciliação financeira automática e s
 - [POST /v1/financeiro/contas-a-receber](https://developers.contaazul.com/docs/financial-apis-openapi/v1/createreceivable.md): Permite criar um novo evento financeiro de contas a receber, passando dados como data de competência, valor, descrição, cliente, conta financeira, rateio e condições de pagamento. Facilita o registro
 - [POST /v1/financeiro/eventos-financeiros/contas-a-receber](https://developers.contaazul.com/docs/financial-apis-openapi/v1/createreceivablefinancialevent.md): > **Retorno com protocolo descontinuado em 18/10/2026.** A partir dessa data esta rota deixa de retornar `202` com protocolo e passa a responder igual ao `POST /v1/financeiro/contas-a-receber`: `201`
 - [GET /v1/financeiro/eventos-financeiros/contas-a-receber/buscar](https://developers.contaazul.com/docs/financial-apis-openapi/v1/searchinstallmentstoreceivebyfilter.md): Permite consultar as parcelas de receitas (contas a receber) mediante filtros como data de vencimento, data de competência, data de pagamento, data de alteração, valor, status, dentre outros. Essa fun
 - [POST /v1/financeiro/contas-a-pagar](https://developers.contaazul.com/docs/financial-apis-openapi/v1/createpayable.md): Permite criar um novo evento financeiro de contas a pagar, informando dados como valor, fornecedor, condições de pagamento, descrição, conta financeira e rateio. Esse endpoint facilita o registro das
 - [POST /v1/financeiro/eventos-financeiros/contas-a-pagar](https://developers.contaazul.com/docs/financial-apis-openapi/v1/createpayablefinancialevent.md): > **Retorno com protocolo descontinuado em 18/10/2026.** A partir dessa data esta rota deixa de retornar `202` com protocolo e passa a responder igual ao `POST /v1/financeiro/contas-a-pagar`: `201` co
 - [GET /v1/financeiro/eventos-financeiros/contas-a-pagar/buscar](https://developers.contaazul.com/docs/financial-apis-openapi/v1/searchinstallmentstopaybyfilter.md): Permite consultar as parcelas de despesas (contas a pagar) conforme filtros como data de vencimento, data competência, data de alteração, valor, status, conta financeira, etc. Essa consulta possibilit
 - [GET /v1/financeiro/eventos-financeiros/parcelas/{id}](https://developers.contaazul.com/docs/financial-apis-openapi/v1/getinstallmentbyid.md): Permite consultar os detalhes de uma parcela específica (de conta a receber ou a pagar) identificada pelo seu id. A resposta traz campos como data de vencimento, valor, status, conta financeira, entre
 - [PATCH /v1/financeiro/eventos-financeiros/parcelas/{id}](https://developers.contaazul.com/docs/financial-apis-openapi/v1/updateinstallment.md): Permite atualizar parcialmente uma parcela existente identificada pelo id, alterando campos como data de vencimento, valor, observações, conta financeira e outros campos permitidos. Essa operação ajud
 - [GET /v1/financeiro/eventos-financeiros/alteracoes](https://developers.contaazul.com/docs/financial-apis-openapi/v1/getalteredfinancialevents.md): Permite consultar os IDs dos eventos financeiros (contas a pagar e a receber) que foram alterados em um período definido por data de ínico e fim. Essa funcionalidade é útil para identificar quais eve
 - [GET /v1/financeiro/eventos-financeiros/saldo-inicial](https://developers.contaazul.com/docs/financial-apis-openapi/v1/getinitialbalancesoffinancialaccounts.md): Permite consultar os saldos iniciais das contas financeiras em um período definido por data de início e fim.
