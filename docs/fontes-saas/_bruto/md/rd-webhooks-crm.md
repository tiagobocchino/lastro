---
updatedAt: 2025-09-18T21:24:16.000Z
agentTools:
  projectIndex: https://developers.rdstation.com/llms.txt
---

# Webhooks CRM payload

> 🚧 Nota: O evento de negociação do CRM está disponível somente para planos Basic e PRO do CRM

## Corpo da requisição

Quando o evento configurado no Webhook é acionado, o RD Station CRM envia uma requisição com o método configurado no `http_method` com o cabeçalho `Content-Type: application/json`.

Abaixo seguem os campos disponíveis no payload da requisição:

### Payload Negociação do CRM - Create/Update/Delete

```json crm_deal_created
{
      {
   "event_name": "crm_deal_created",
   "document":{
      "id":"650878567482d9c0c7002050a475",
      "name":"Teste Negociação",
      "amount_monthly":0.0,
      "amount_unique":0.0,
      "amount_total":0.0,
      "prediction_date":null,
      "created_at":"2023-09-18T15:04:34.515-03:00",
      "updated_at":"2023-09-18T15:04:34.515-03:00",
      "rating":1,
      "status":"ongoing",
      "closed_at":null,
      "user":{
         "id":"622e7fb2f678470c001576f4a4",
         "name":"Hian Almada",
         "email":"hian.almada@rn.com",
         "avatar_url":null
      },
      "deal_stage":{
         "id":"622e4cee412e87000d2f52a6",
         "name":"Sem contato",
         "nickname":"SC",
         "created_at":"2022-03-13T16:58:38.951-03:00",
         "updated_at":"2022-03-13T16:58:38.951-03:00",
         "order":1
      },
      "deal_pipeline":{
         "id":"622e4cee111e87000d2f52a5",
         "name":"Funil Padrão"
      },
      "deal_source":{
         
      },
      "campaign":{
         
      },
      "deal_lost_reason":{
         
      },
      "deal_custom_fields":[
         {
            "value":null,
            "custom_field":{
               "id":"611e89b0f269d0000b3bb2c2",
               "label":"Whatsapp",
               "required":false,
               "unique":false,
               "opts":[
                  
               ],
               "type":"text"
            }
         },
         {
            "value":null,
            "custom_field":{
               "id":"112e89ca673c7300162f15b3",
               "label":"Instagram",
               "required":false,
               "unique":false,
               "opts":[
                  
               ],
               "type":"text"
            }
         },
         {
            "value":null,
            "custom_field":{
               "id":"622e89e9f329d0000f3bb17a",
               "label":"Qual a sua idade?",
               "required":false,
               "unique":false,
               "opts":[
                  
               ],
               "type":"text"
            }
         },
         {
            "value":null,
            "custom_field":{
               "id":"622e8a32f269d0011f3bb17d",
               "label":"De onde você conhece a Issues?",
               "required":false,
               "unique":false,
               "opts":[
                  "Selecione",
                  "Redes Sociais",
                  "Indicação",
                  "Pesquisa no Goole",
                  "Evento",
                  "Pista de skate"
               ],
               "type":"option"
            }
         },
         {
            "value":null,
            "custom_field":{
               "id":"6258480fd71568001128705a",
               "label":"Unidade",
               "required":false,
               "unique":false,
               "opts":[
                  "Florianópolis",
                  "São Paulo"
               ],
               "type":"multiple_choice"
            }
         }
      ],
      "deal_products":[
         
      ]
   },
   "event_timestamp":"2023-09-18T18:04:34.000Z",
   "transaction_uuid":"f111b90-ec81-4353-8d52-ffd3b8df412d"
}
```
```coffeescript crm_deal_updated
{
      {
   "event_name": "crm_deal_updated",
   "document":{
      "id":"650878567482d9c0c7002050a475",
      "name":"Teste Negociação",
      "amount_monthly":0.0,
      "amount_unique":0.0,
      "amount_total":0.0,
      "prediction_date":null,
      "created_at":"2023-09-18T15:04:34.515-03:00",
      "updated_at":"2023-09-18T15:04:34.515-03:00",
      "rating":1,
      "status":"ongoing",
      "closed_at":null,
      "user":{
         "id":"622e7fb2f678470c001576f4a4",
         "name":"Hian Almada",
         "email":"hian.almada@rn.com",
         "avatar_url":null
      },
      "deal_stage":{
         "id":"622e4cee412e87000d2f52a6",
         "name":"Sem contato",
         "nickname":"SC",
         "created_at":"2022-03-13T16:58:38.951-03:00",
         "updated_at":"2022-03-13T16:58:38.951-03:00",
         "order":1
      },
      "deal_pipeline":{
         "id":"622e4cee111e87000d2f52a5",
         "name":"Funil Padrão"
      },
      "deal_source":{
         
      },
      "campaign":{
         
      },
      "deal_lost_reason":{
         
      },
      "deal_custom_fields":[
         {
            "value":null,
            "custom_field":{
               "id":"611e89b0f269d0000b3bb2c2",
               "label":"Whatsapp",
               "required":false,
               "unique":false,
               "opts":[
                  
               ],
               "type":"text"
            }
         },
         {
            "value":null,
            "custom_field":{
               "id":"112e89ca673c7300162f15b3",
               "label":"Instagram",
               "required":false,
               "unique":false,
               "opts":[
                  
               ],
               "type":"text"
            }
         },
         {
            "value":null,
            "custom_field":{
               "id":"622e89e9f329d0000f3bb17a",
               "label":"Qual a sua idade?",
               "required":false,
               "unique":false,
               "opts":[
                  
               ],
               "type":"text"
            }
         },
         {
            "value":null,
            "custom_field":{
               "id":"622e8a32f269d0011f3bb17d",
               "label":"De onde você conhece a Issues?",
               "required":false,
               "unique":false,
               "opts":[
                  "Selecione",
                  "Redes Sociais",
                  "Indicação",
                  "Pesquisa no Goole",
                  "Evento",
                  "Pista de skate"
               ],
               "type":"option"
            }
         },
         {
            "value":null,
            "custom_field":{
               "id":"6258480fd71568001128705a",
               "label":"Unidade",
               "required":false,
               "unique":false,
               "opts":[
                  "Florianópolis",
                  "São Paulo"
               ],
               "type":"multiple_choice"
            }
         }
      ],
      "deal_products":[
         
      ]
   },
   "event_timestamp":"2023-09-18T18:04:34.000Z",
   "transaction_uuid":"f111b90-ec81-4353-8d52-ffd3b8df412d"
}
```
```coffeescript crm_deal_delete
{
   "event_name":"crm_deal_deleted",
   "document":{
      "id":"64df7a11113f80018644923",
      "name":"Teste Negociação"
   },
   "event_timestamp":"2023-11-14T18:43:09.000Z",
   "transaction_uuid":"b2daa3cb-23b1-497f-afb5-a5e4acda9374"
}
```

***

## Legenda dos campos enviados no payload padrão

Confira abaixo cada campo enviado pelo webhook e o que cada um deles representa:

| Campo                | Tipo     | Descrição                                                                                                                                                                 |
| :------------------- | :------- | :------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| event\_name          | String   | O tipo de evento que acionou a solicitação do webhook. Atualmente, apenas **CRM\_DEAL\_CREATED.** ou **CRM\_DEAL\_UPDATED** ou **CRM\_DEAL\_DELETED** são opções válidas. |
| event\_timestamp     | DateTime | A hora em que ocorreu o evento que acionou o webhook.                                                                                                                     |
| transaction\_uuid    | UUID     | Identificador único do evento.                                                                                                                                            |
| document             | Object   | Objeto contendo objetos com as informações da negociação                                                                                                                  |
| user                 | Object   | Usuário relacionado a negociação                                                                                                                                          |
| deal\_stage          | Object   | Estágio da negociação no fluxo                                                                                                                                            |
| deal\_pipeline       | Object   | Funil do CRM em que a negociação se encontra                                                                                                                              |
| deal\_source         | Object   | Fonte da negociação                                                                                                                                                       |
| campaign             | Object   | Informação das campanhas referente à entrada das negociações                                                                                                              |
| deal\_lost\_reason   | Object   | Motivo da perda da negociação                                                                                                                                             |
| deal\_custom\_fields | Object   | Campos personalizados da negociação                                                                                                                                       |
| deal\_products       | Object   | Produtos e serviços presentes na negociação                                                                                                                               |
| amount\_unique       | Object   | Valor único                                                                                                                                                               |
| amount\_monthly      | Object   | Valor recorrente                                                                                                                                                          |
| amount\_annual       | Object   | Valor total (soma do valor único e valor recorrente)                                                                                                                      |

> ❗️ O webhook envia um payload padrão em JSON único e imutável.
>
> **Não é possível personalizar os dados enviados pelo webhook.**