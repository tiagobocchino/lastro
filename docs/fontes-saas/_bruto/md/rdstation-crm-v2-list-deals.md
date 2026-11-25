---
updatedAt: 2026-04-22T17:02:29.000Z
agentTools:
  projectIndex: https://developers.rdstation.com/llms.txt
---

# Listar negociações

Este end-point recupera uma lista paginada de todas as negociações na conta, permitindo a filtragem por diversos critérios, como funil, etapa ou proprietário. É útil para sincronizar dados de negociações com sistemas externos ou para construir painéis de visualização personalizados.

## Filtro

Propriedades disponíveis para filtro usando [RDQL](crm-v2-rdql-filtering).

| Propriedade | Tipo | Descrição |
| :--- | :--- | :--- |
| `id` | `String` | Filtra por um ou mais IDs de negociação. |
| `name` | `String` | Filtra por nome da negociação, suportando busca exata ou por correspondência (usando operador match `~`). |
| `rating` | `Integer` | Filtra por um valor de classificação numérica da negociação. |
| `status` | `String` | Filtra por status da negociação. |
| `closed_at` | `DateTime` | Filtra por data e hora de fechamento da negociação. |
| `created_at` | `DateTime` | Filtra por data e hora de criação da negociação. |
| `updated_at` | `DateTime` | Filtra por data e hora da última atualização da negociação. |
| `expected_close_date` | `Date` | Filtra pela data de fechamento prevista da negociação. |
| `organization_id` | `String` | Filtra por um ID de empresa. |
| `contact_id` | `String` | Filtra por um ou mais IDs de contato. |
| `stage_id` | `String` | Filtra por um ID de etapa do funil de vendas. |
| `lost_reason_id` | `String` | Filtra por um ID de motivo de perda da negociação. |
| `campaign_id` | `String` | Filtra por um ID de campanha. |
| `owner_id` | `String` | Filtra por um ID de proprietário (usuário) da negociação. |
| `pipeline_id` | `String` | Filtra negociações por um ID de funil de vendas. |
| `product_ids` | `String` | Filtra negociações que contêm um ou mais IDs de produtos. |
| `has:product` | `Boolean` | Filtra negociações que têm produtos associados. |
| `@<custom_field_slug>` | `String` | Filtra por um campo personalizado. Exemplo: `filial:norte`, `erp_id:123`. |

## Ordenação

Propriedades disponíveis para [ordenação](crm-v2-introduction#ordenação).

* `name`
* `rating`
* `created_at`
* `updated_at`
* `closed_at`

# OpenAPI definition

```json
{
  "openapi": "3.1.1",
  "info": {
    "title": "RD Station CRM API v2",
    "version": "2.0",
    "description": "Esta documentação detalha os end-points e webhooks disponíveis na API v2 do RD Station CRM.\n\n# Autenticação\n\nA API v2 do RD Station CRM utiliza o padrão OAuth 2.0 para autenticação e autorização. Para acessar os recursos da API, você precisará obter um token de acesso. O fluxo de autorização é o `authorizationCode`.",
    "license": {
      "name": "Termos de Uso do Software RD Station CRM",
      "url": "https://legal.rdstation.com/pt/rdstation-crm-services-agreement/"
    },
    "termsOfService": "https://legal.rdstation.com/pt/rdstation-crm-services-agreement/",
    "contact": {
      "name": "Suporte RD Station",
      "url": "https://developers.rdstation.com/docs/suporte"
    }
  },
  "externalDocs": {
    "description": "Documentação completa",
    "url": "https://developers.rdstation.com/crm-v2"
  },
  "servers": [
    {
      "url": "https://api.rd.services/crm/v2",
      "description": "Production"
    }
  ],
  "security": [
    {
      "OAuth2": []
    }
  ],
  "tags": [
    {
      "name": "crm-v2-campaigns",
      "description": "Campanhas"
    },
    {
      "name": "crm-v2-contacts",
      "description": "Contatos"
    },
    {
      "name": "crm-v2-deals",
      "description": "Negociações"
    },
    {
      "name": "crm-v2-dialer-calls",
      "description": "Ligações do discador webphone"
    },
    {
      "name": "crm-v2-leads",
      "description": "Leads"
    },
    {
      "name": "crm-v2-lost-reasons",
      "description": "Motivos de perda"
    },
    {
      "name": "crm-v2-meetings",
      "description": "Reuniões"
    },
    {
      "name": "crm-v2-organizations",
      "description": "Empresas"
    },
    {
      "name": "crm-v2-products",
      "description": "Produtos"
    },
    {
      "name": "crm-v2-proposals",
      "description": "Propostas comerciais na negociação (listagem, criação e detalhe)"
    },
    {
      "name": "crm-v2-sources",
      "description": "Fontes"
    },
    {
      "name": "crm-v2-tasks",
      "description": "Tarefas"
    },
    {
      "name": "crm-v2-webhook-events",
      "description": "Eventos de webhook"
    }
  ],
  "paths": {
    "/deals": {
      "get": {
        "summary": "Listar negociações",
        "operationId": "crm-v2-list-deals",
        "tags": [
          "crm-v2-deals"
        ],
        "description": "Este end-point recupera uma lista paginada de todas as negociações na conta, permitindo a filtragem por diversos critérios, como funil, etapa ou proprietário. É útil para sincronizar dados de negociações com sistemas externos ou para construir painéis de visualização personalizados.\n\n## Filtro\n\nPropriedades disponíveis para filtro usando [RDQL](crm-v2-rdql-filtering).\n\n| Propriedade | Tipo | Descrição |\n| :--- | :--- | :--- |\n| `id` | `String` | Filtra por um ou mais IDs de negociação. |\n| `name` | `String` | Filtra por nome da negociação, suportando busca exata ou por correspondência (usando operador match `~`). |\n| `rating` | `Integer` | Filtra por um valor de classificação numérica da negociação. |\n| `status` | `String` | Filtra por status da negociação. |\n| `closed_at` | `DateTime` | Filtra por data e hora de fechamento da negociação. |\n| `created_at` | `DateTime` | Filtra por data e hora de criação da negociação. |\n| `updated_at` | `DateTime` | Filtra por data e hora da última atualização da negociação. |\n| `expected_close_date` | `Date` | Filtra pela data de fechamento prevista da negociação. |\n| `organization_id` | `String` | Filtra por um ID de empresa. |\n| `contact_id` | `String` | Filtra por um ou mais IDs de contato. |\n| `stage_id` | `String` | Filtra por um ID de etapa do funil de vendas. |\n| `lost_reason_id` | `String` | Filtra por um ID de motivo de perda da negociação. |\n| `campaign_id` | `String` | Filtra por um ID de campanha. |\n| `owner_id` | `String` | Filtra por um ID de proprietário (usuário) da negociação. |\n| `pipeline_id` | `String` | Filtra negociações por um ID de funil de vendas. |\n| `product_ids` | `String` | Filtra negociações que contêm um ou mais IDs de produtos. |\n| `has:product` | `Boolean` | Filtra negociações que têm produtos associados. |\n| `@<custom_field_slug>` | `String` | Filtra por um campo personalizado. Exemplo: `filial:norte`, `erp_id:123`. |\n\n## Ordenação\n\nPropriedades disponíveis para [ordenação](crm-v2-introduction#ordenação).\n\n* `name`\n* `rating`\n* `created_at`\n* `updated_at`\n* `closed_at`",
        "parameters": [
          {
            "$ref": "#/components/parameters/RDQLFilter"
          },
          {
            "$ref": "#/components/parameters/Sort"
          },
          {
            "$ref": "#/components/parameters/PaginationNumber"
          }
        ],
        "responses": {
          "200": {
            "description": "OK",
            "content": {
              "application/json": {
                "schema": {
                  "allOf": [
                    {
                      "$ref": "#/components/schemas/PayloadDataList"
                    },
                    {
                      "$ref": "#/components/schemas/PayloadLinks"
                    },
                    {
                      "type": "object",
                      "properties": {
                        "data": {
                          "type": "array",
                          "items": {
                            "$ref": "#/components/schemas/Deal"
                          }
                        },
                        "links": {
                          "$ref": "#/components/schemas/PaginationLinks"
                        }
                      }
                    }
                  ]
                }
              }
            }
          },
          "400": {
            "$ref": "#/components/responses/BadRequest"
          },
          "401": {
            "$ref": "#/components/responses/Unauthorized"
          },
          "403": {
            "$ref": "#/components/responses/Forbidden"
          },
          "429": {
            "$ref": "#/components/responses/TooManyRequests"
          },
          "500": {
            "$ref": "#/components/responses/InternalServerError"
          }
        }
      }
    }
  },
  "webhooks": {
    "crm_campaign_created": {
      "post": {
        "summary": "Campanha criada",
        "operationId": "crm-v2-webhook-event-crm-campaign-created",
        "tags": [
          "crm-v2-webhook-events",
          "crm-v2-campaigns"
        ],
        "description": "Esse evento de webhook é disparado quando uma campanha é criada.",
        "security": [],
        "requestBody": {
          "description": "O conteúdo enviado ao seu end-point quando o evento é disparado.",
          "content": {
            "application/json": {
              "schema": {
                "allOf": [
                  {
                    "$ref": "#/components/schemas/WebhookEvent"
                  },
                  {
                    "type": "object",
                    "properties": {
                      "event_name": {
                        "const": "crm_campaign_created"
                      }
                    }
                  },
                  {
                    "type": "object",
                    "properties": {
                      "document": {
                        "$ref": "#/components/schemas/Campaign"
                      }
                    }
                  }
                ]
              }
            }
          }
        },
        "responses": {
          "2XX": {
            "$ref": "#/components/responses/WebhookEventAccepted"
          },
          "default": {
            "$ref": "#/components/responses/WebhookEventRejected"
          }
        }
      }
    },
    "crm_campaign_deleted": {
      "post": {
        "summary": "Campanha deletada",
        "operationId": "crm-v2-webhook-event-crm-campaign-deleted",
        "tags": [
          "crm-v2-webhook-events",
          "crm-v2-campaigns"
        ],
        "description": "Esse evento de webhook é disparado quando uma campanha é deletada.",
        "security": [],
        "requestBody": {
          "description": "O conteúdo enviado ao seu end-point quando o evento é disparado.",
          "content": {
            "application/json": {
              "schema": {
                "allOf": [
                  {
                    "$ref": "#/components/schemas/WebhookEvent"
                  },
                  {
                    "type": "object",
                    "properties": {
                      "event_name": {
                        "const": "crm_campaign_deleted"
                      }
                    }
                  },
                  {
                    "type": "object",
                    "properties": {
                      "document": {
                        "type": "object",
                        "properties": {
                          "id": {
                            "description": "Identificador único.",
                            "type": "string",
                            "pattern": "^[0-9a-f]{24}$"
                          },
                          "name": {
                            "description": "Nome da campanha.",
                            "type": "string"
                          }
                        }
                      }
                    }
                  }
                ]
              }
            }
          }
        },
        "responses": {
          "2XX": {
            "$ref": "#/components/responses/WebhookEventAccepted"
          },
          "default": {
            "$ref": "#/components/responses/WebhookEventRejected"
          }
        }
      }
    },
    "crm_campaign_updated": {
      "post": {
        "summary": "Campanha atualizada",
        "operationId": "crm-v2-webhook-event-crm-campaign-updated",
        "tags": [
          "crm-v2-webhook-events",
          "crm-v2-campaigns"
        ],
        "description": "Esse evento de webhook é disparado quando uma campanha é atualizada.",
        "security": [],
        "requestBody": {
          "description": "O conteúdo enviado ao seu end-point quando o evento é disparado.",
          "content": {
            "application/json": {
              "schema": {
                "allOf": [
                  {
                    "$ref": "#/components/schemas/WebhookEvent"
                  },
                  {
                    "type": "object",
                    "properties": {
                      "event_name": {
                        "const": "crm_campaign_updated"
                      }
                    }
                  },
                  {
                    "type": "object",
                    "properties": {
                      "document": {
                        "$ref": "#/components/schemas/Campaign"
                      }
                    }
                  }
                ]
              }
            }
          }
        },
        "responses": {
          "2XX": {
            "$ref": "#/components/responses/WebhookEventAccepted"
          },
          "default": {
            "$ref": "#/components/responses/WebhookEventRejected"
          }
        }
      }
    },
    "crm_contact_created": {
      "post": {
        "summary": "Contato criado",
        "operationId": "crm-v2-webhook-event-crm-contact-created",
        "tags": [
          "crm-v2-webhook-events",
          "crm-v2-contacts"
        ],
        "description": "Esse evento de webhook é disparado quando um contato é criado.",
        "security": [],
        "requestBody": {
          "description": "O conteúdo enviado ao seu end-point quando o evento é disparado.",
          "content": {
            "application/json": {
              "schema": {
                "allOf": [
                  {
                    "$ref": "#/components/schemas/WebhookEvent"
                  },
                  {
                    "type": "object",
                    "properties": {
                      "event_name": {
                        "const": "crm_contact_created"
                      }
                    }
                  },
                  {
                    "type": "object",
                    "properties": {
                      "document": {
                        "$ref": "#/components/schemas/Contact"
                      }
                    }
                  }
                ]
              }
            }
          }
        },
        "responses": {
          "2XX": {
            "$ref": "#/components/responses/WebhookEventAccepted"
          },
          "default": {
            "$ref": "#/components/responses/WebhookEventRejected"
          }
        }
      }
    },
    "crm_contact_deleted": {
      "post": {
        "summary": "Contato deletado",
        "operationId": "crm-v2-webhook-event-crm-contact-deleted",
        "tags": [
          "crm-v2-webhook-events",
          "crm-v2-contacts"
        ],
        "description": "Esse evento de webhook é disparado quando um contato é deletado.",
        "security": [],
        "requestBody": {
          "description": "O conteúdo enviado ao seu end-point quando o evento é disparado.",
          "content": {
            "application/json": {
              "schema": {
                "allOf": [
                  {
                    "$ref": "#/components/schemas/WebhookEvent"
                  },
                  {
                    "type": "object",
                    "properties": {
                      "event_name": {
                        "const": "crm_contact_deleted"
                      }
                    }
                  },
                  {
                    "type": "object",
                    "properties": {
                      "document": {
                        "type": "object",
                        "properties": {
                          "id": {
                            "description": "Identificador único.",
                            "type": "string",
                            "pattern": "^[0-9a-f]{24}$"
                          },
                          "name": {
                            "description": "Nome do contato.",
                            "type": "string"
                          }
                        }
                      }
                    }
                  }
                ]
              }
            }
          }
        },
        "responses": {
          "2XX": {
            "$ref": "#/components/responses/WebhookEventAccepted"
          },
          "default": {
            "$ref": "#/components/responses/WebhookEventRejected"
          }
        }
      }
    },
    "crm_contact_updated": {
      "post": {
        "summary": "Contato atualizado",
        "operationId": "crm-v2-webhook-event-crm-contact-updated",
        "tags": [
          "crm-v2-webhook-events",
          "crm-v2-contacts"
        ],
        "description": "Esse evento de webhook é disparado quando um contato é atualizado.",
        "security": [],
        "requestBody": {
          "description": "O conteúdo enviado ao seu end-point quando o evento é disparado.",
          "content": {
            "application/json": {
              "schema": {
                "allOf": [
                  {
                    "$ref": "#/components/schemas/WebhookEvent"
                  },
                  {
                    "type": "object",
                    "properties": {
                      "event_name": {
                        "const": "crm_contact_updated"
                      }
                    }
                  },
                  {
                    "type": "object",
                    "properties": {
                      "document": {
                        "$ref": "#/components/schemas/Contact"
                      }
                    }
                  }
                ]
              }
            }
          }
        },
        "responses": {
          "2XX": {
            "$ref": "#/components/responses/WebhookEventAccepted"
          },
          "default": {
            "$ref": "#/components/responses/WebhookEventRejected"
          }
        }
      }
    },
    "crm_deal_created": {
      "post": {
        "summary": "Negociação criada",
        "operationId": "crm-v2-webhook-event-crm-deal-created",
        "tags": [
          "crm-v2-webhook-events",
          "crm-v2-deals"
        ],
        "description": "Esse evento de webhook é disparado quando uma negociação é criada.",
        "security": [],
        "requestBody": {
          "description": "O conteúdo enviado ao seu end-point quando o evento é disparado.",
          "content": {
            "application/json": {
              "schema": {
                "allOf": [
                  {
                    "$ref": "#/components/schemas/WebhookEvent"
                  },
                  {
                    "type": "object",
                    "properties": {
                      "event_name": {
                        "const": "crm_deal_created"
                      }
                    }
                  },
                  {
                    "type": "object",
                    "properties": {
                      "document": {
                        "$ref": "#/components/schemas/DealV1"
                      }
                    }
                  }
                ]
              }
            }
          }
        },
        "responses": {
          "2XX": {
            "$ref": "#/components/responses/WebhookEventAccepted"
          },
          "default": {
            "$ref": "#/components/responses/WebhookEventRejected"
          }
        }
      }
    },
    "crm_deal_deleted": {
      "post": {
        "summary": "Negociação deletada",
        "operationId": "crm-v2-webhook-event-crm-deal-deleted",
        "tags": [
          "crm-v2-webhook-events",
          "crm-v2-deals"
        ],
        "description": "Esse evento de webhook é disparado quando uma negociação é deletada.",
        "security": [],
        "requestBody": {
          "description": "O conteúdo enviado ao seu end-point quando o evento é disparado.",
          "content": {
            "application/json": {
              "schema": {
                "allOf": [
                  {
                    "$ref": "#/components/schemas/WebhookEvent"
                  },
                  {
                    "type": "object",
                    "properties": {
                      "event_name": {
                        "const": "crm_deal_deleted"
                      }
                    }
                  },
                  {
                    "type": "object",
                    "properties": {
                      "document": {
                        "type": "object",
                        "properties": {
                          "id": {
                            "description": "Identificador único.",
                            "type": "string",
                            "pattern": "^[0-9a-f]{24}$"
                          },
                          "name": {
                            "description": "Nome da negociação.",
                            "type": "string"
                          }
                        }
                      }
                    }
                  }
                ]
              }
            }
          }
        },
        "responses": {
          "2XX": {
            "$ref": "#/components/responses/WebhookEventAccepted"
          },
          "default": {
            "$ref": "#/components/responses/WebhookEventRejected"
          }
        }
      }
    },
    "crm_deal_updated": {
      "post": {
        "summary": "Negociação atualizada",
        "operationId": "crm-v2-webhook-event-crm-deal-updated",
        "tags": [
          "crm-v2-webhook-events",
          "crm-v2-deals"
        ],
        "description": "Esse evento de webhook é disparado quando uma negociação é atualizada.",
        "security": [],
        "requestBody": {
          "description": "O conteúdo enviado ao seu end-point quando o evento é disparado.",
          "content": {
            "application/json": {
              "schema": {
                "allOf": [
                  {
                    "$ref": "#/components/schemas/WebhookEvent"
                  },
                  {
                    "type": "object",
                    "properties": {
                      "event_name": {
                        "const": "crm_deal_updated"
                      }
                    }
                  },
                  {
                    "type": "object",
                    "properties": {
                      "document": {
                        "$ref": "#/components/schemas/DealV1"
                      }
                    }
                  }
                ]
              }
            }
          }
        },
        "responses": {
          "2XX": {
            "$ref": "#/components/responses/WebhookEventAccepted"
          },
          "default": {
            "$ref": "#/components/responses/WebhookEventRejected"
          }
        }
      }
    },
    "crm_dialer_call_status_changed": {
      "post": {
        "summary": "Status da ligação do Webphone alterado",
        "operationId": "crm-v2-webhook-event-crm-dialer-call-status-changed",
        "tags": [
          "crm-v2-webhook-events",
          "crm-v2-dialer-calls"
        ],
        "description": "Esse evento de webhook é disparado a cada mudança do status de uma ligação Webphone\npara um status final (`answered`, `no_answer`, `busy`, `congested` ou `failed`).\nPermanecer em `initial`, reenvio sem mudança de status e criação da ligação não disparam\neste evento. A transcrição costuma estar em `processing`, com `content` vazio.",
        "security": [],
        "requestBody": {
          "description": "O conteúdo enviado ao seu end-point quando o evento é disparado.",
          "content": {
            "application/json": {
              "schema": {
                "allOf": [
                  {
                    "$ref": "#/components/schemas/WebhookEvent"
                  },
                  {
                    "type": "object",
                    "properties": {
                      "event_name": {
                        "const": "crm_dialer_call_status_changed"
                      }
                    }
                  },
                  {
                    "type": "object",
                    "properties": {
                      "document": {
                        "$ref": "#/components/schemas/DialerCallWebhookDocument"
                      }
                    }
                  }
                ]
              }
            }
          }
        },
        "responses": {
          "2XX": {
            "$ref": "#/components/responses/WebhookEventAccepted"
          },
          "default": {
            "$ref": "#/components/responses/WebhookEventRejected"
          }
        }
      }
    },
    "crm_dialer_call_transcription_completed": {
      "post": {
        "summary": "Transcrição da ligação do Webphone concluída",
        "operationId": "crm-v2-webhook-event-crm-dialer-call-transcription-completed",
        "tags": [
          "crm-v2-webhook-events",
          "crm-v2-dialer-calls"
        ],
        "description": "Esse evento de webhook é disparado uma vez quando a transcrição de uma ligação Webphone\npassa para `completed`. O corpo é o mesmo objeto da ligação do evento\n`crm_dialer_call_status_changed`, com `transcription.summary` e as falas em `transcription.content`.\nQuando o Webphone não consegue transcrever, a transcrição também chega como `completed`,\ncom `summary` começando com `Transcrição falhou:` e `content` vazio.\nTranscrição que continua em `processing` não dispara este evento.",
        "security": [],
        "requestBody": {
          "description": "O conteúdo enviado ao seu end-point quando o evento é disparado.",
          "content": {
            "application/json": {
              "schema": {
                "allOf": [
                  {
                    "$ref": "#/components/schemas/WebhookEvent"
                  },
                  {
                    "type": "object",
                    "properties": {
                      "event_name": {
                        "const": "crm_dialer_call_transcription_completed"
                      }
                    }
                  },
                  {
                    "type": "object",
                    "properties": {
                      "document": {
                        "$ref": "#/components/schemas/DialerCallWebhookDocument"
                      }
                    }
                  }
                ]
              }
            }
          }
        },
        "responses": {
          "2XX": {
            "$ref": "#/components/responses/WebhookEventAccepted"
          },
          "default": {
            "$ref": "#/components/responses/WebhookEventRejected"
          }
        }
      }
    },
    "crm_lead_created": {
      "post": {
        "summary": "Lead criado",
        "operationId": "crm-v2-webhook-event-crm-lead-created",
        "tags": [
          "crm-v2-webhook-events",
          "crm-v2-leads"
        ],
        "description": "Esse evento de webhook é disparado quando um lead é criado.",
        "security": [],
        "requestBody": {
          "description": "O conteúdo enviado ao seu end-point quando o evento é disparado.",
          "content": {
            "application/json": {
              "schema": {
                "allOf": [
                  {
                    "$ref": "#/components/schemas/WebhookEvent"
                  },
                  {
                    "type": "object",
                    "properties": {
                      "event_name": {
                        "const": "crm_lead_created"
                      }
                    }
                  },
                  {
                    "type": "object",
                    "properties": {
                      "document": {
                        "$ref": "#/components/schemas/LeadWebhookDocument"
                      }
                    }
                  }
                ]
              }
            }
          }
        },
        "responses": {
          "2XX": {
            "$ref": "#/components/responses/WebhookEventAccepted"
          },
          "default": {
            "$ref": "#/components/responses/WebhookEventRejected"
          }
        }
      }
    },
    "crm_lead_deleted": {
      "post": {
        "summary": "Lead deletado",
        "operationId": "crm-v2-webhook-event-crm-lead-deleted",
        "tags": [
          "crm-v2-webhook-events",
          "crm-v2-leads"
        ],
        "description": "Esse evento de webhook é disparado quando um lead é deletado.",
        "security": [],
        "requestBody": {
          "description": "O conteúdo enviado ao seu end-point quando o evento é disparado.",
          "content": {
            "application/json": {
              "schema": {
                "allOf": [
                  {
                    "$ref": "#/components/schemas/WebhookEvent"
                  },
                  {
                    "type": "object",
                    "properties": {
                      "event_name": {
                        "const": "crm_lead_deleted"
                      }
                    }
                  },
                  {
                    "type": "object",
                    "properties": {
                      "document": {
                        "$ref": "#/components/schemas/LeadDeletedWebhookDocument"
                      }
                    }
                  }
                ]
              }
            }
          }
        },
        "responses": {
          "2XX": {
            "$ref": "#/components/responses/WebhookEventAccepted"
          },
          "default": {
            "$ref": "#/components/responses/WebhookEventRejected"
          }
        }
      }
    },
    "crm_lead_owner_changed": {
      "post": {
        "summary": "Responsável do lead alterado",
        "operationId": "crm-v2-webhook-event-crm-lead-owner-changed",
        "tags": [
          "crm-v2-webhook-events",
          "crm-v2-leads"
        ],
        "description": "Esse evento de webhook é disparado quando o responsável de um lead é alterado.\nA mesma alteração também dispara `crm_lead_updated`.",
        "security": [],
        "requestBody": {
          "description": "O conteúdo enviado ao seu end-point quando o evento é disparado.",
          "content": {
            "application/json": {
              "schema": {
                "allOf": [
                  {
                    "$ref": "#/components/schemas/WebhookEvent"
                  },
                  {
                    "type": "object",
                    "properties": {
                      "event_name": {
                        "const": "crm_lead_owner_changed"
                      }
                    }
                  },
                  {
                    "type": "object",
                    "properties": {
                      "document": {
                        "$ref": "#/components/schemas/LeadWebhookDocument"
                      }
                    }
                  }
                ]
              }
            }
          }
        },
        "responses": {
          "2XX": {
            "$ref": "#/components/responses/WebhookEventAccepted"
          },
          "default": {
            "$ref": "#/components/responses/WebhookEventRejected"
          }
        }
      }
    },
    "crm_lead_rating_changed": {
      "post": {
        "summary": "Qualificação do lead alterada",
        "operationId": "crm-v2-webhook-event-crm-lead-rating-changed",
        "tags": [
          "crm-v2-webhook-events",
          "crm-v2-leads"
        ],
        "description": "Esse evento de webhook é disparado quando a qualificação de um lead é alterada.\nA mesma alteração também dispara `crm_lead_updated`.",
        "security": [],
        "requestBody": {
          "description": "O conteúdo enviado ao seu end-point quando o evento é disparado.",
          "content": {
            "application/json": {
              "schema": {
                "allOf": [
                  {
                    "$ref": "#/components/schemas/WebhookEvent"
                  },
                  {
                    "type": "object",
                    "properties": {
                      "event_name": {
                        "const": "crm_lead_rating_changed"
                      }
                    }
                  },
                  {
                    "type": "object",
                    "properties": {
                      "document": {
                        "$ref": "#/components/schemas/LeadWebhookDocument"
                      }
                    }
                  }
                ]
              }
            }
          }
        },
        "responses": {
          "2XX": {
            "$ref": "#/components/responses/WebhookEventAccepted"
          },
          "default": {
            "$ref": "#/components/responses/WebhookEventRejected"
          }
        }
      }
    },
    "crm_lead_stage_changed": {
      "post": {
        "summary": "Etapa do lead alterada",
        "operationId": "crm-v2-webhook-event-crm-lead-stage-changed",
        "tags": [
          "crm-v2-webhook-events",
          "crm-v2-leads"
        ],
        "description": "Esse evento de webhook é disparado quando a etapa de um lead é alterada.\nA mesma alteração também dispara `crm_lead_updated`.",
        "security": [],
        "requestBody": {
          "description": "O conteúdo enviado ao seu end-point quando o evento é disparado.",
          "content": {
            "application/json": {
              "schema": {
                "allOf": [
                  {
                    "$ref": "#/components/schemas/WebhookEvent"
                  },
                  {
                    "type": "object",
                    "properties": {
                      "event_name": {
                        "const": "crm_lead_stage_changed"
                      }
                    }
                  },
                  {
                    "type": "object",
                    "properties": {
                      "document": {
                        "$ref": "#/components/schemas/LeadWebhookDocument"
                      }
                    }
                  }
                ]
              }
            }
          }
        },
        "responses": {
          "2XX": {
            "$ref": "#/components/responses/WebhookEventAccepted"
          },
          "default": {
            "$ref": "#/components/responses/WebhookEventRejected"
          }
        }
      }
    },
    "crm_lead_status_changed": {
      "post": {
        "summary": "Status do lead alterado",
        "operationId": "crm-v2-webhook-event-crm-lead-status-changed",
        "tags": [
          "crm-v2-webhook-events",
          "crm-v2-leads"
        ],
        "description": "Esse evento de webhook é disparado quando o status de um lead é alterado.\nA mesma alteração também dispara `crm_lead_updated`.",
        "security": [],
        "requestBody": {
          "description": "O conteúdo enviado ao seu end-point quando o evento é disparado.",
          "content": {
            "application/json": {
              "schema": {
                "allOf": [
                  {
                    "$ref": "#/components/schemas/WebhookEvent"
                  },
                  {
                    "type": "object",
                    "properties": {
                      "event_name": {
                        "const": "crm_lead_status_changed"
                      }
                    }
                  },
                  {
                    "type": "object",
                    "properties": {
                      "document": {
                        "$ref": "#/components/schemas/LeadWebhookDocument"
                      }
                    }
                  }
                ]
              }
            }
          }
        },
        "responses": {
          "2XX": {
            "$ref": "#/components/responses/WebhookEventAccepted"
          },
          "default": {
            "$ref": "#/components/responses/WebhookEventRejected"
          }
        }
      }
    },
    "crm_lead_updated": {
      "post": {
        "summary": "Lead atualizado",
        "operationId": "crm-v2-webhook-event-crm-lead-updated",
        "tags": [
          "crm-v2-webhook-events",
          "crm-v2-leads"
        ],
        "description": "Esse evento de webhook é disparado quando um lead é atualizado.\nMudança de etapa, status, qualificação ou responsável também dispara o evento específico correspondente.",
        "security": [],
        "requestBody": {
          "description": "O conteúdo enviado ao seu end-point quando o evento é disparado.",
          "content": {
            "application/json": {
              "schema": {
                "allOf": [
                  {
                    "$ref": "#/components/schemas/WebhookEvent"
                  },
                  {
                    "type": "object",
                    "properties": {
                      "event_name": {
                        "const": "crm_lead_updated"
                      }
                    }
                  },
                  {
                    "type": "object",
                    "properties": {
                      "document": {
                        "$ref": "#/components/schemas/LeadWebhookDocument"
                      }
                    }
                  }
                ]
              }
            }
          }
        },
        "responses": {
          "2XX": {
            "$ref": "#/components/responses/WebhookEventAccepted"
          },
          "default": {
            "$ref": "#/components/responses/WebhookEventRejected"
          }
        }
      }
    },
    "crm_lost_reason_created": {
      "post": {
        "summary": "Motivo de perda criado",
        "operationId": "crm-v2-webhook-event-crm-lost-reason-created",
        "tags": [
          "crm-v2-webhook-events",
          "crm-v2-lost-reasons"
        ],
        "description": "Esse evento de webhook é disparado quando um motivo de perda é criado.",
        "security": [],
        "requestBody": {
          "description": "O conteúdo enviado ao seu end-point quando o evento é disparado.",
          "content": {
            "application/json": {
              "schema": {
                "allOf": [
                  {
                    "$ref": "#/components/schemas/WebhookEvent"
                  },
                  {
                    "type": "object",
                    "properties": {
                      "event_name": {
                        "const": "crm_lost_reason_created"
                      }
                    }
                  },
                  {
                    "type": "object",
                    "properties": {
                      "document": {
                        "$ref": "#/components/schemas/LostReason"
                      }
                    }
                  }
                ]
              }
            }
          }
        },
        "responses": {
          "2XX": {
            "$ref": "#/components/responses/WebhookEventAccepted"
          },
          "default": {
            "$ref": "#/components/responses/WebhookEventRejected"
          }
        }
      }
    },
    "crm_lost_reason_deleted": {
      "post": {
        "summary": "Motivo de perda deletado",
        "operationId": "crm-v2-webhook-event-crm-lost-reason-deleted",
        "tags": [
          "crm-v2-webhook-events",
          "crm-v2-lost-reasons"
        ],
        "description": "Esse evento de webhook é disparado quando um motivo de perda é deletado.",
        "security": [],
        "requestBody": {
          "description": "O conteúdo enviado ao seu end-point quando o evento é disparado.",
          "content": {
            "application/json": {
              "schema": {
                "allOf": [
                  {
                    "$ref": "#/components/schemas/WebhookEvent"
                  },
                  {
                    "type": "object",
                    "properties": {
                      "event_name": {
                        "const": "crm_lost_reason_deleted"
                      }
                    }
                  },
                  {
                    "type": "object",
                    "properties": {
                      "document": {
                        "type": "object",
                        "properties": {
                          "id": {
                            "description": "Identificador único.",
                            "type": "string",
                            "pattern": "^[0-9a-f]{24}$"
                          },
                          "name": {
                            "description": "Nome do motivo de perda.",
                            "type": "string"
                          }
                        }
                      }
                    }
                  }
                ]
              }
            }
          }
        },
        "responses": {
          "2XX": {
            "$ref": "#/components/responses/WebhookEventAccepted"
          },
          "default": {
            "$ref": "#/components/responses/WebhookEventRejected"
          }
        }
      }
    },
    "crm_lost_reason_updated": {
      "post": {
        "summary": "Motivo de perda atualizado",
        "operationId": "crm-v2-webhook-event-crm-lost-reason-updated",
        "tags": [
          "crm-v2-webhook-events",
          "crm-v2-lost-reasons"
        ],
        "description": "Esse evento de webhook é disparado quando um motivo de perda é atualizado.",
        "security": [],
        "requestBody": {
          "description": "O conteúdo enviado ao seu end-point quando o evento é disparado.",
          "content": {
            "application/json": {
              "schema": {
                "allOf": [
                  {
                    "$ref": "#/components/schemas/WebhookEvent"
                  },
                  {
                    "type": "object",
                    "properties": {
                      "event_name": {
                        "const": "crm_lost_reason_updated"
                      }
                    }
                  },
                  {
                    "type": "object",
                    "properties": {
                      "document": {
                        "$ref": "#/components/schemas/LostReason"
                      }
                    }
                  }
                ]
              }
            }
          }
        },
        "responses": {
          "2XX": {
            "$ref": "#/components/responses/WebhookEventAccepted"
          },
          "default": {
            "$ref": "#/components/responses/WebhookEventRejected"
          }
        }
      }
    },
    "crm_meeting_created": {
      "post": {
        "summary": "Reunião criada",
        "operationId": "crm-v2-webhook-event-crm-meeting-created",
        "tags": [
          "crm-v2-webhook-events",
          "crm-v2-meetings"
        ],
        "description": "Esse evento de webhook é disparado quando uma reunião é criada.",
        "security": [],
        "requestBody": {
          "description": "O conteúdo enviado ao seu end-point quando o evento é disparado.",
          "content": {
            "application/json": {
              "schema": {
                "allOf": [
                  {
                    "$ref": "#/components/schemas/WebhookEvent"
                  },
                  {
                    "type": "object",
                    "properties": {
                      "event_name": {
                        "const": "crm_meeting_created"
                      }
                    }
                  },
                  {
                    "type": "object",
                    "properties": {
                      "document": {
                        "$ref": "#/components/schemas/MeetingWebhookDocument"
                      }
                    }
                  }
                ]
              }
            }
          }
        },
        "responses": {
          "2XX": {
            "$ref": "#/components/responses/WebhookEventAccepted"
          },
          "default": {
            "$ref": "#/components/responses/WebhookEventRejected"
          }
        }
      }
    },
    "crm_meeting_participants_changed": {
      "post": {
        "summary": "Participantes da reunião alterados",
        "operationId": "crm-v2-webhook-event-crm-meeting-participants-changed",
        "tags": [
          "crm-v2-webhook-events",
          "crm-v2-meetings"
        ],
        "description": "Esse evento de webhook é disparado quando os participantes (responsável ou contatos) de uma reunião são alterados.",
        "security": [],
        "requestBody": {
          "description": "O conteúdo enviado ao seu end-point quando o evento é disparado.",
          "content": {
            "application/json": {
              "schema": {
                "allOf": [
                  {
                    "$ref": "#/components/schemas/WebhookEvent"
                  },
                  {
                    "type": "object",
                    "properties": {
                      "event_name": {
                        "const": "crm_meeting_participants_changed"
                      }
                    }
                  },
                  {
                    "type": "object",
                    "properties": {
                      "document": {
                        "$ref": "#/components/schemas/MeetingWebhookDocument"
                      }
                    }
                  }
                ]
              }
            }
          }
        },
        "responses": {
          "2XX": {
            "$ref": "#/components/responses/WebhookEventAccepted"
          },
          "default": {
            "$ref": "#/components/responses/WebhookEventRejected"
          }
        }
      }
    },
    "crm_meeting_status_changed": {
      "post": {
        "summary": "Status da reunião alterado",
        "operationId": "crm-v2-webhook-event-crm-meeting-status-changed",
        "tags": [
          "crm-v2-webhook-events",
          "crm-v2-meetings"
        ],
        "description": "Esse evento de webhook é disparado quando o status de uma reunião é alterado.",
        "security": [],
        "requestBody": {
          "description": "O conteúdo enviado ao seu end-point quando o evento é disparado.",
          "content": {
            "application/json": {
              "schema": {
                "allOf": [
                  {
                    "$ref": "#/components/schemas/WebhookEvent"
                  },
                  {
                    "type": "object",
                    "properties": {
                      "event_name": {
                        "const": "crm_meeting_status_changed"
                      }
                    }
                  },
                  {
                    "type": "object",
                    "properties": {
                      "document": {
                        "$ref": "#/components/schemas/MeetingWebhookDocument"
                      }
                    }
                  }
                ]
              }
            }
          }
        },
        "responses": {
          "2XX": {
            "$ref": "#/components/responses/WebhookEventAccepted"
          },
          "default": {
            "$ref": "#/components/responses/WebhookEventRejected"
          }
        }
      }
    },
    "crm_meeting_updated": {
      "post": {
        "summary": "Reunião atualizada",
        "operationId": "crm-v2-webhook-event-crm-meeting-updated",
        "tags": [
          "crm-v2-webhook-events",
          "crm-v2-meetings"
        ],
        "description": "Esse evento de webhook é disparado quando uma reunião é atualizada.",
        "security": [],
        "requestBody": {
          "description": "O conteúdo enviado ao seu end-point quando o evento é disparado.",
          "content": {
            "application/json": {
              "schema": {
                "allOf": [
                  {
                    "$ref": "#/components/schemas/WebhookEvent"
                  },
                  {
                    "type": "object",
                    "properties": {
                      "event_name": {
                        "const": "crm_meeting_updated"
                      }
                    }
                  },
                  {
                    "type": "object",
                    "properties": {
                      "document": {
                        "$ref": "#/components/schemas/MeetingWebhookDocument"
                      }
                    }
                  }
                ]
              }
            }
          }
        },
        "responses": {
          "2XX": {
            "$ref": "#/components/responses/WebhookEventAccepted"
          },
          "default": {
            "$ref": "#/components/responses/WebhookEventRejected"
          }
        }
      }
    },
    "crm_organization_created": {
      "post": {
        "summary": "Empresa criada",
        "operationId": "crm-v2-webhook-event-crm-organization-created",
        "tags": [
          "crm-v2-webhook-events",
          "crm-v2-organizations"
        ],
        "description": "Esse evento de webhook é disparado quando uma empresa é criada.",
        "security": [],
        "requestBody": {
          "description": "O conteúdo enviado ao seu end-point quando o evento é disparado.",
          "content": {
            "application/json": {
              "schema": {
                "allOf": [
                  {
                    "$ref": "#/components/schemas/WebhookEvent"
                  },
                  {
                    "type": "object",
                    "properties": {
                      "event_name": {
                        "const": "crm_organization_created"
                      }
                    }
                  },
                  {
                    "type": "object",
                    "properties": {
                      "document": {
                        "$ref": "#/components/schemas/Organization"
                      }
                    }
                  }
                ]
              }
            }
          }
        },
        "responses": {
          "2XX": {
            "$ref": "#/components/responses/WebhookEventAccepted"
          },
          "default": {
            "$ref": "#/components/responses/WebhookEventRejected"
          }
        }
      }
    },
    "crm_organization_deleted": {
      "post": {
        "summary": "Empresa deletada",
        "operationId": "crm-v2-webhook-event-crm-organization-deleted",
        "tags": [
          "crm-v2-webhook-events",
          "crm-v2-organizations"
        ],
        "description": "Esse evento de webhook é disparado quando uma empresa é deletada.",
        "security": [],
        "requestBody": {
          "description": "O conteúdo enviado ao seu end-point quando o evento é disparado.",
          "content": {
            "application/json": {
              "schema": {
                "allOf": [
                  {
                    "$ref": "#/components/schemas/WebhookEvent"
                  },
                  {
                    "type": "object",
                    "properties": {
                      "event_name": {
                        "const": "crm_organization_deleted"
                      }
                    }
                  },
                  {
                    "type": "object",
                    "properties": {
                      "document": {
                        "type": "object",
                        "properties": {
                          "id": {
                            "description": "Identificador único.",
                            "type": "string",
                            "pattern": "^[0-9a-f]{24}$"
                          },
                          "name": {
                            "description": "Nome da empresa.",
                            "type": "string"
                          }
                        }
                      }
                    }
                  }
                ]
              }
            }
          }
        },
        "responses": {
          "2XX": {
            "$ref": "#/components/responses/WebhookEventAccepted"
          },
          "default": {
            "$ref": "#/components/responses/WebhookEventRejected"
          }
        }
      }
    },
    "crm_organization_updated": {
      "post": {
        "summary": "Empresa atualizada",
        "operationId": "crm-v2-webhook-event-crm-organization-updated",
        "tags": [
          "crm-v2-webhook-events",
          "crm-v2-organizations"
        ],
        "description": "Esse evento de webhook é disparado quando uma empresa é atualizada.",
        "security": [],
        "requestBody": {
          "description": "O conteúdo enviado ao seu end-point quando o evento é disparado.",
          "content": {
            "application/json": {
              "schema": {
                "allOf": [
                  {
                    "$ref": "#/components/schemas/WebhookEvent"
                  },
                  {
                    "type": "object",
                    "properties": {
                      "event_name": {
                        "const": "crm_organization_updated"
                      }
                    }
                  },
                  {
                    "type": "object",
                    "properties": {
                      "document": {
                        "$ref": "#/components/schemas/Organization"
                      }
                    }
                  }
                ]
              }
            }
          }
        },
        "responses": {
          "2XX": {
            "$ref": "#/components/responses/WebhookEventAccepted"
          },
          "default": {
            "$ref": "#/components/responses/WebhookEventRejected"
          }
        }
      }
    },
    "crm_product_created": {
      "post": {
        "summary": "Produto criado",
        "operationId": "crm-v2-webhook-event-crm-product-created",
        "tags": [
          "crm-v2-webhook-events",
          "crm-v2-products"
        ],
        "description": "Esse evento de webhook é disparado quando um produto é criado.",
        "security": [],
        "requestBody": {
          "description": "O conteúdo enviado ao seu end-point quando o evento é disparado.",
          "content": {
            "application/json": {
              "schema": {
                "allOf": [
                  {
                    "$ref": "#/components/schemas/WebhookEvent"
                  },
                  {
                    "type": "object",
                    "properties": {
                      "event_name": {
                        "const": "crm_product_created"
                      }
                    }
                  },
                  {
                    "type": "object",
                    "properties": {
                      "document": {
                        "$ref": "#/components/schemas/Product"
                      }
                    }
                  }
                ]
              }
            }
          }
        },
        "responses": {
          "2XX": {
            "$ref": "#/components/responses/WebhookEventAccepted"
          },
          "default": {
            "$ref": "#/components/responses/WebhookEventRejected"
          }
        }
      }
    },
    "crm_product_deleted": {
      "post": {
        "summary": "Produto deletado",
        "operationId": "crm-v2-webhook-event-crm-product-deleted",
        "tags": [
          "crm-v2-webhook-events",
          "crm-v2-products"
        ],
        "description": "Esse evento de webhook é disparado quando um produto é deletado.",
        "security": [],
        "requestBody": {
          "description": "O conteúdo enviado ao seu end-point quando o evento é disparado.",
          "content": {
            "application/json": {
              "schema": {
                "allOf": [
                  {
                    "$ref": "#/components/schemas/WebhookEvent"
                  },
                  {
                    "type": "object",
                    "properties": {
                      "event_name": {
                        "const": "crm_product_deleted"
                      }
                    }
                  },
                  {
                    "type": "object",
                    "properties": {
                      "document": {
                        "type": "object",
                        "properties": {
                          "id": {
                            "description": "Identificador único.",
                            "type": "string",
                            "pattern": "^[0-9a-f]{24}$"
                          },
                          "name": {
                            "description": "Nome do produto.",
                            "type": "string"
                          }
                        }
                      }
                    }
                  }
                ]
              }
            }
          }
        },
        "responses": {
          "2XX": {
            "$ref": "#/components/responses/WebhookEventAccepted"
          },
          "default": {
            "$ref": "#/components/responses/WebhookEventRejected"
          }
        }
      }
    },
    "crm_product_updated": {
      "post": {
        "summary": "Produto atualizado",
        "operationId": "crm-v2-webhook-event-crm-product-updated",
        "tags": [
          "crm-v2-webhook-events",
          "crm-v2-products"
        ],
        "description": "Esse evento de webhook é disparado quando um produto é atualizado.",
        "security": [],
        "requestBody": {
          "description": "O conteúdo enviado ao seu end-point quando o evento é disparado.",
          "content": {
            "application/json": {
              "schema": {
                "allOf": [
                  {
                    "$ref": "#/components/schemas/WebhookEvent"
                  },
                  {
                    "type": "object",
                    "properties": {
                      "event_name": {
                        "const": "crm_product_updated"
                      }
                    }
                  },
                  {
                    "type": "object",
                    "properties": {
                      "document": {
                        "$ref": "#/components/schemas/Product"
                      }
                    }
                  }
                ]
              }
            }
          }
        },
        "responses": {
          "2XX": {
            "$ref": "#/components/responses/WebhookEventAccepted"
          },
          "default": {
            "$ref": "#/components/responses/WebhookEventRejected"
          }
        }
      }
    },
    "crm_proposal_created": {
      "post": {
        "summary": "Proposta criada",
        "operationId": "crm-v2-webhook-event-crm-proposal-created",
        "tags": [
          "crm-v2-webhook-events",
          "crm-v2-proposals"
        ],
        "description": "Esse evento de webhook é disparado quando uma proposta comercial é criada na negociação.",
        "security": [],
        "requestBody": {
          "description": "O conteúdo enviado ao seu end-point quando o evento é disparado.",
          "content": {
            "application/json": {
              "schema": {
                "allOf": [
                  {
                    "$ref": "#/components/schemas/WebhookEvent"
                  },
                  {
                    "type": "object",
                    "properties": {
                      "event_name": {
                        "const": "crm_proposal_created"
                      }
                    }
                  },
                  {
                    "type": "object",
                    "properties": {
                      "document": {
                        "$ref": "#/components/schemas/Proposal"
                      }
                    }
                  }
                ]
              }
            }
          }
        },
        "responses": {
          "2XX": {
            "$ref": "#/components/responses/WebhookEventAccepted"
          },
          "default": {
            "$ref": "#/components/responses/WebhookEventRejected"
          }
        }
      }
    },
    "crm_source_created": {
      "post": {
        "summary": "Fonte criada",
        "operationId": "crm-v2-webhook-event-crm-source-created",
        "tags": [
          "crm-v2-webhook-events",
          "crm-v2-sources"
        ],
        "description": "Esse evento de webhook é disparado quando uma fonte é criada.",
        "security": [],
        "requestBody": {
          "description": "O conteúdo enviado ao seu end-point quando o evento é disparado.",
          "content": {
            "application/json": {
              "schema": {
                "allOf": [
                  {
                    "$ref": "#/components/schemas/WebhookEvent"
                  },
                  {
                    "type": "object",
                    "properties": {
                      "event_name": {
                        "const": "crm_source_created"
                      }
                    }
                  },
                  {
                    "type": "object",
                    "properties": {
                      "document": {
                        "$ref": "#/components/schemas/Source"
                      }
                    }
                  }
                ]
              }
            }
          }
        },
        "responses": {
          "2XX": {
            "$ref": "#/components/responses/WebhookEventAccepted"
          },
          "default": {
            "$ref": "#/components/responses/WebhookEventRejected"
          }
        }
      }
    },
    "crm_source_deleted": {
      "post": {
        "summary": "Fonte deletada",
        "operationId": "crm-v2-webhook-event-crm-source-deleted",
        "tags": [
          "crm-v2-webhook-events",
          "crm-v2-sources"
        ],
        "description": "Esse evento de webhook é disparado quando uma fonte é deletada.",
        "security": [],
        "requestBody": {
          "description": "O conteúdo enviado ao seu end-point quando o evento é disparado.",
          "content": {
            "application/json": {
              "schema": {
                "allOf": [
                  {
                    "$ref": "#/components/schemas/WebhookEvent"
                  },
                  {
                    "type": "object",
                    "properties": {
                      "event_name": {
                        "const": "crm_source_deleted"
                      }
                    }
                  },
                  {
                    "type": "object",
                    "properties": {
                      "document": {
                        "type": "object",
                        "properties": {
                          "id": {
                            "description": "Identificador único.",
                            "type": "string",
                            "pattern": "^[0-9a-f]{24}$"
                          },
                          "name": {
                            "description": "Nome da fonte.",
                            "type": "string"
                          }
                        }
                      }
                    }
                  }
                ]
              }
            }
          }
        },
        "responses": {
          "2XX": {
            "$ref": "#/components/responses/WebhookEventAccepted"
          },
          "default": {
            "$ref": "#/components/responses/WebhookEventRejected"
          }
        }
      }
    },
    "crm_source_updated": {
      "post": {
        "summary": "Fonte atualizada",
        "operationId": "crm-v2-webhook-event-crm-source-updated",
        "tags": [
          "crm-v2-webhook-events",
          "crm-v2-sources"
        ],
        "description": "Esse evento de webhook é disparado quando uma fonte é atualizada.",
        "security": [],
        "requestBody": {
          "description": "O conteúdo enviado ao seu end-point quando o evento é disparado.",
          "content": {
            "application/json": {
              "schema": {
                "allOf": [
                  {
                    "$ref": "#/components/schemas/WebhookEvent"
                  },
                  {
                    "type": "object",
                    "properties": {
                      "event_name": {
                        "const": "crm_source_updated"
                      }
                    }
                  },
                  {
                    "type": "object",
                    "properties": {
                      "document": {
                        "$ref": "#/components/schemas/Source"
                      }
                    }
                  }
                ]
              }
            }
          }
        },
        "responses": {
          "2XX": {
            "$ref": "#/components/responses/WebhookEventAccepted"
          },
          "default": {
            "$ref": "#/components/responses/WebhookEventRejected"
          }
        }
      }
    },
    "crm_task_created": {
      "post": {
        "summary": "Tarefa criada",
        "operationId": "crm-v2-webhook-event-crm-task-created",
        "tags": [
          "crm-v2-webhook-events",
          "crm-v2-tasks"
        ],
        "description": "Esse evento de webhook é disparado quando uma tarefa é criada.",
        "security": [],
        "requestBody": {
          "description": "O conteúdo enviado ao seu end-point quando o evento é disparado.",
          "content": {
            "application/json": {
              "schema": {
                "allOf": [
                  {
                    "$ref": "#/components/schemas/WebhookEvent"
                  },
                  {
                    "type": "object",
                    "properties": {
                      "event_name": {
                        "const": "crm_task_created"
                      }
                    }
                  },
                  {
                    "type": "object",
                    "properties": {
                      "document": {
                        "$ref": "#/components/schemas/Task"
                      }
                    }
                  }
                ]
              }
            }
          }
        },
        "responses": {
          "2XX": {
            "$ref": "#/components/responses/WebhookEventAccepted"
          },
          "default": {
            "$ref": "#/components/responses/WebhookEventRejected"
          }
        }
      }
    },
    "crm_task_deleted": {
      "post": {
        "summary": "Tarefa deletada",
        "operationId": "crm-v2-webhook-event-crm-task-deleted",
        "tags": [
          "crm-v2-webhook-events",
          "crm-v2-tasks"
        ],
        "description": "Esse evento de webhook é disparado quando uma tarefa é deletada.",
        "security": [],
        "requestBody": {
          "description": "O conteúdo enviado ao seu end-point quando o evento é disparado.",
          "content": {
            "application/json": {
              "schema": {
                "allOf": [
                  {
                    "$ref": "#/components/schemas/WebhookEvent"
                  },
                  {
                    "type": "object",
                    "properties": {
                      "event_name": {
                        "const": "crm_task_deleted"
                      }
                    }
                  },
                  {
                    "type": "object",
                    "properties": {
                      "document": {
                        "type": "object",
                        "properties": {
                          "id": {
                            "description": "Identificador único.",
                            "type": "string",
                            "pattern": "^[0-9a-f]{24}$"
                          },
                          "name": {
                            "description": "Assunto da tarefa.",
                            "type": "string"
                          }
                        }
                      }
                    }
                  }
                ]
              }
            }
          }
        },
        "responses": {
          "2XX": {
            "$ref": "#/components/responses/WebhookEventAccepted"
          },
          "default": {
            "$ref": "#/components/responses/WebhookEventRejected"
          }
        }
      }
    },
    "crm_task_updated": {
      "post": {
        "summary": "Tarefa atualizada",
        "operationId": "crm-v2-webhook-event-crm-task-updated",
        "tags": [
          "crm-v2-webhook-events",
          "crm-v2-tasks"
        ],
        "description": "Esse evento de webhook é disparado quando uma tarefa é atualizada.",
        "security": [],
        "requestBody": {
          "description": "O conteúdo enviado ao seu end-point quando o evento é disparado.",
          "content": {
            "application/json": {
              "schema": {
                "allOf": [
                  {
                    "$ref": "#/components/schemas/WebhookEvent"
                  },
                  {
                    "type": "object",
                    "properties": {
                      "event_name": {
                        "const": "crm_task_updated"
                      }
                    }
                  },
                  {
                    "type": "object",
                    "properties": {
                      "document": {
                        "$ref": "#/components/schemas/Task"
                      }
                    }
                  }
                ]
              }
            }
          }
        },
        "responses": {
          "2XX": {
            "$ref": "#/components/responses/WebhookEventAccepted"
          },
          "default": {
            "$ref": "#/components/responses/WebhookEventRejected"
          }
        }
      }
    }
  },
  "components": {
    "securitySchemes": {
      "OAuth2": {
        "type": "oauth2",
        "description": "Para mais informações, veja: [Autenticação](crm-v2-authentication).",
        "flows": {
          "authorizationCode": {
            "authorizationUrl": "/oauth/authorize",
            "tokenUrl": "/oauth/token",
            "scopes": {}
          }
        }
      }
    },
    "parameters": {
      "PaginationNumber": {
        "name": "page",
        "in": "query",
        "description": "Paginação. ([Saiba mais](crm-v2-introduction#paginação))",
        "schema": {
          "type": "object",
          "properties": {
            "number": {
              "description": "Número da página.",
              "type": "integer",
              "default": 1
            },
            "size": {
              "description": "Tamanho da página.",
              "type": "integer",
              "default": 25
            }
          }
        },
        "style": "deepObject",
        "explode": true
      },
      "RDQLFilter": {
        "name": "filter",
        "in": "query",
        "description": "Filtro no formato RDQL. ([Saiba mais](crm-v2-rdql-filtering))",
        "schema": {
          "type": "string"
        },
        "example": "field:value other_field:>10"
      },
      "Sort": {
        "name": "sort",
        "in": "query",
        "description": "Ordenação. ([Saiba mais](crm-v2-introduction#ordenação))",
        "schema": {
          "type": "object",
          "additionalProperties": {
            "description": "Nome da propriedade a ser ordenada e direção da ordenação.",
            "type": "string",
            "enum": [
              "asc",
              "desc"
            ],
            "x-enumDescriptions": {
              "asc": "Ordenação ascendente.",
              "desc": "Ordenação descendente."
            }
          }
        },
        "style": "deepObject",
        "explode": true
      }
    },
    "responses": {
      "BadRequest": {
        "description": "A requisição está malformada e não consegue ser processada. Ordenação ou paginação inválida responde com `type: INVALID_PARAMETER` e o parâmetro em `source.parameter`. Na ordenação: `sort` (campo que não aceita ordenação ou mais campos que o permitido) ou `sort[campo]` (direção diferente de `asc` ou `desc`). Na paginação: `page[size]` (tamanho menor que 1 ou acima do máximo), `page[number]` (página menor que 1) ou `page` (`page[number]` × `page[size]` acima de 10.000 registros).",
        "content": {
          "application/json": {
            "schema": {
              "$ref": "#/components/schemas/Error"
            }
          }
        }
      },
      "Forbidden": {
        "description": "O token não tem permissão para acessar o recurso solicitado.",
        "content": {
          "application/json": {
            "schema": {
              "$ref": "#/components/schemas/Error"
            }
          }
        }
      },
      "InternalServerError": {
        "description": "Erro interno ou inesperado no servidor.",
        "content": {
          "application/json": {
            "schema": {
              "$ref": "#/components/schemas/Error"
            }
          }
        }
      },
      "TooManyRequests": {
        "description": "O limite de requisições foi excedido."
      },
      "Unauthorized": {
        "description": "O token da API está ausente ou inválido.",
        "content": {
          "application/json": {
            "schema": {
              "$ref": "#/components/schemas/Error"
            }
          }
        }
      },
      "WebhookEventAccepted": {
        "description": "O evento é considerado aceito retornando qualquer código de resposta 2XX."
      },
      "WebhookEventRejected": {
        "description": "O evento é considerado rejeitado para qualquer outro código de resposta. A emissão do evento será repetida posteriormente."
      }
    },
    "schemas": {
      "Address": {
        "type": "object",
        "properties": {
          "line": {
            "description": "Endereço.",
            "type": "string"
          },
          "latitude": {
            "description": "Latitude do endereço.",
            "type": "string"
          },
          "longitude": {
            "description": "Longitude do endereço.",
            "type": "string"
          }
        }
      },
      "Campaign": {
        "type": "object",
        "properties": {
          "id": {
            "description": "Identificador único.",
            "type": "string",
            "pattern": "^[0-9a-f]{24}$",
            "readOnly": true
          },
          "name": {
            "description": "Nome da campanha.",
            "type": "string"
          },
          "description": {
            "description": "Descrição da campanha.",
            "type": "string"
          },
          "created_at": {
            "description": "Data de criação da campanha.",
            "type": "string",
            "format": "date-time",
            "readOnly": true
          },
          "updated_at": {
            "description": "Data de atualização da campanha.",
            "type": "string",
            "format": "date-time",
            "readOnly": true
          }
        }
      },
      "Contact": {
        "type": "object",
        "properties": {
          "id": {
            "description": "Identificador único.",
            "type": "string",
            "pattern": "^[0-9a-f]{24}$",
            "readOnly": true
          },
          "name": {
            "description": "Nome do contato.",
            "type": "string"
          },
          "job_title": {
            "description": "Cargo do contato.",
            "type": "string"
          },
          "emails": {
            "description": "Emails do contato.",
            "type": "array",
            "items": {
              "$ref": "#/components/schemas/Email"
            }
          },
          "phones": {
            "description": "Telefones do contato.",
            "type": "array",
            "items": {
              "$ref": "#/components/schemas/Phone"
            }
          },
          "whatsapp_username": {
            "description": "Username do WhatsApp do contato.",
            "type": "string"
          },
          "birthday": {
            "description": "Data de aniversário do contato. Formato: `YYYY-MM-DD`. Caso só tenha o mês e o dia, use `0000-MM-DD`.",
            "type": "string",
            "format": "date"
          },
          "social_profiles": {
            "description": "Perfis sociais do contato.",
            "type": "array",
            "items": {
              "$ref": "#/components/schemas/SocialProfile"
            }
          },
          "organization_id": {
            "description": "ID da organização.",
            "type": "string",
            "pattern": "^[0-9a-f]{24}$"
          },
          "legal_bases": {
            "description": "Bases legais para o contato. ([Saiba mais](crm-v2-introduction#bases-legais))",
            "type": "array",
            "items": {
              "$ref": "#/components/schemas/LegalBase"
            }
          },
          "custom_fields": {
            "description": "Campos personalizados do contato.",
            "$ref": "#/components/schemas/CustomFields"
          },
          "created_at": {
            "description": "Data de criação do contato.",
            "type": "string",
            "format": "date-time",
            "readOnly": true
          },
          "updated_at": {
            "description": "Data de atualização do contato.",
            "type": "string",
            "format": "date-time",
            "readOnly": true
          }
        }
      },
      "CustomFields": {
        "type": "object",
        "additionalProperties": {
          "description": "Define o valor de um campo personalizado sendo a chave o `slug` do campo personalizado e o valor deve ser do tipo correspondente ao tipo definido no campo personalizado.",
          "type": "string"
        }
      },
      "Deal": {
        "type": "object",
        "properties": {
          "id": {
            "description": "Identificador único.",
            "type": "string",
            "pattern": "^[0-9a-f]{24}$",
            "readOnly": true
          },
          "name": {
            "description": "Nome da negociação.",
            "type": "string"
          },
          "recurrence_price": {
            "description": "Valor recorrente da negociação.",
            "type": "number",
            "format": "float"
          },
          "one_time_price": {
            "description": "Valor único da negociação.",
            "type": "number",
            "format": "float"
          },
          "total_price": {
            "description": "Valor total da negociação.",
            "type": "number",
            "format": "float",
            "readOnly": true
          },
          "expected_close_date": {
            "description": "Data de previsão de fechamento da negociação.",
            "type": "string",
            "format": "date"
          },
          "rating": {
            "description": "Qualificação da negociação.",
            "type": "integer"
          },
          "status": {
            "description": "Status da negociação.",
            "type": "string",
            "enum": [
              "won",
              "lost",
              "ongoing",
              "paused"
            ]
          },
          "closed_at": {
            "description": "Data de fechamento da negociação.",
            "type": "string",
            "format": "date-time",
            "readOnly": true
          },
          "pipeline_id": {
            "description": "ID do funil de vendas da negociação.",
            "type": "string",
            "pattern": "^[0-9a-f]{24}$",
            "readOnly": true
          },
          "stage_id": {
            "description": "ID da etapa do funil de vendas da negociação.",
            "type": "string",
            "pattern": "^[0-9a-f]{24}$"
          },
          "owner_id": {
            "description": "ID do usuário responsável pela negociação.",
            "type": "string",
            "pattern": "^[0-9a-f]{24}$"
          },
          "source_id": {
            "description": "ID da fonte da negociação.",
            "type": "string",
            "pattern": "^[0-9a-f]{24}$"
          },
          "campaign_id": {
            "description": "ID da campanha da negociação.",
            "type": "string",
            "pattern": "^[0-9a-f]{24}$"
          },
          "lost_reason_id": {
            "description": "ID do motivo de perda da negociação.",
            "type": "string",
            "pattern": "^[0-9a-f]{24}$"
          },
          "organization_id": {
            "description": "ID da empresa associada à negociação.",
            "type": "string",
            "pattern": "^[0-9a-f]{24}$"
          },
          "contact_ids": {
            "description": "IDs dos contatos associados à negociação.",
            "type": "array",
            "items": {
              "type": "string",
              "pattern": "^[0-9a-f]{24}$"
            }
          },
          "custom_fields": {
            "description": "Campos personalizados da negociação.",
            "$ref": "#/components/schemas/CustomFields"
          },
          "distribution_settings": {
            "description": "Configurações de distribuição da negociação.",
            "$ref": "#/components/schemas/DistributionSetting"
          },
          "created_at": {
            "description": "Data de criação da negociação.",
            "type": "string",
            "format": "date-time",
            "readOnly": true
          },
          "updated_at": {
            "description": "Data de atualização da negociação.",
            "type": "string",
            "format": "date-time",
            "readOnly": true
          }
        }
      },
      "DealV1": {
        "type": "object",
        "properties": {
          "id": {
            "description": "Identificador único.",
            "type": "string",
            "pattern": "^[0-9a-f]{24}$"
          },
          "name": {
            "description": "Nome da negociação.",
            "type": "string"
          },
          "amount_monthly": {
            "description": "Valor recorrente da negociação.",
            "type": "number",
            "format": "float"
          },
          "amount_unique": {
            "description": "Valor único da negociação.",
            "type": "number",
            "format": "float"
          },
          "amount_total": {
            "description": "Valor total da negociação.",
            "type": "number",
            "format": "float"
          },
          "prediction_date": {
            "description": "Data de previsão de fechamento da negociação.",
            "type": "string",
            "format": "date"
          },
          "rating": {
            "description": "Qualificação da negociação.",
            "type": "integer"
          },
          "status": {
            "description": "Status da negociação.",
            "type": "string",
            "enum": [
              "won",
              "lost",
              "ongoing",
              "paused"
            ]
          },
          "closed_at": {
            "description": "Data de fechamento da negociação.",
            "type": "string",
            "format": "date-time"
          },
          "deal_pipeline": {
            "description": "Funil de vendas da negociação.",
            "type": "object",
            "properties": {
              "id": {
                "description": "Identificador único.",
                "type": "string",
                "pattern": "^[0-9a-f]{24}$"
              },
              "name": {
                "description": "Nome do funil de vendas.",
                "type": "string"
              }
            }
          },
          "deal_stage": {
            "description": "Etapa do funil de vendas da negociação.",
            "type": "object",
            "properties": {
              "id": {
                "description": "Identificador único.",
                "type": "string",
                "pattern": "^[0-9a-f]{24}$"
              },
              "name": {
                "description": "Nome da etapa do funil de vendas.",
                "type": "string"
              },
              "nickname": {
                "description": "Sigla da etapa do funil de vendas.",
                "type": "string"
              },
              "order": {
                "description": "Ordem da etapa do funil de vendas.",
                "type": "integer"
              },
              "created_at": {
                "description": "Data de criação da etapa do funil de vendas.",
                "type": "string",
                "format": "date-time"
              },
              "updated_at": {
                "description": "Data de atualização da etapa do funil de vendas.",
                "type": "string",
                "format": "date-time"
              }
            }
          },
          "user": {
            "description": "Usuário responsável pela negociação.",
            "type": "object",
            "properties": {
              "id": {
                "description": "Identificador único.",
                "type": "string",
                "pattern": "^[0-9a-f]{24}$"
              },
              "name": {
                "description": "Nome do usuário.",
                "type": "string"
              },
              "email": {
                "description": "Email do usuário.",
                "type": "string"
              },
              "avatar_url": {
                "description": "URL do avatar do usuário.",
                "type": "string"
              }
            }
          },
          "deal_source": {
            "description": "Fonte da negociação.",
            "type": "object",
            "properties": {
              "id": {
                "description": "Identificador único.",
                "type": "string",
                "pattern": "^[0-9a-f]{24}$"
              },
              "name": {
                "description": "Nome da fonte.",
                "type": "string"
              }
            }
          },
          "campaign": {
            "description": "Campanha da negociação.",
            "type": "object",
            "properties": {
              "id": {
                "description": "Identificador único.",
                "type": "string",
                "pattern": "^[0-9a-f]{24}$"
              },
              "name": {
                "description": "Nome da campanha.",
                "type": "string"
              }
            }
          },
          "deal_lost_reason": {
            "description": "Motivo de perda da negociação.",
            "type": "object",
            "properties": {
              "id": {
                "description": "Identificador único.",
                "type": "string",
                "pattern": "^[0-9a-f]{24}$"
              },
              "name": {
                "description": "Nome do motivo de perda.",
                "type": "string"
              }
            }
          },
          "deal_products": {
            "description": "Produtos da negociação.",
            "type": "array",
            "items": {
              "type": "object",
              "properties": {
                "product_id": {
                  "description": "Identificador único.",
                  "type": "string",
                  "pattern": "^[0-9a-f]{24}$"
                },
                "name": {
                  "description": "Nome do produto.",
                  "type": "string"
                },
                "description": {
                  "description": "Descrição do produto.",
                  "type": "string"
                },
                "price": {
                  "description": "Preço do produto.",
                  "type": "number",
                  "format": "float"
                },
                "quantity": {
                  "description": "Quantidade do produto.",
                  "type": "number",
                  "format": "float"
                },
                "discount": {
                  "description": "Desconto do produto.",
                  "type": "number",
                  "format": "float"
                },
                "discount_type": {
                  "description": "Tipo de desconto.",
                  "type": "string"
                },
                "total": {
                  "description": "Preço total do produto.",
                  "type": "number",
                  "format": "float"
                }
              }
            }
          },
          "deal_custom_fields": {
            "description": "Campos personalizados da negociação.",
            "type": "array",
            "items": {
              "type": "object",
              "properties": {
                "value": {
                  "description": "Valor do campo personalizado.",
                  "type": "string"
                },
                "custom_field": {
                  "description": "Campo personalizado.",
                  "type": "object",
                  "properties": {
                    "id": {
                      "description": "Identificador único.",
                      "type": "string",
                      "pattern": "^[0-9a-f]{24}$"
                    },
                    "label": {
                      "description": "Nome do campo personalizado.",
                      "type": "string"
                    },
                    "required": {
                      "description": "Se o campo é obrigatório.",
                      "type": "boolean"
                    },
                    "unique": {
                      "description": "Se o campo é único.",
                      "type": "boolean"
                    },
                    "opts": {
                      "description": "Opções do campo personalizado.",
                      "type": "array",
                      "items": {
                        "description": "Opção do campo personalizado.",
                        "type": "string"
                      }
                    },
                    "type": {
                      "description": "Tipo do campo personalizado.",
                      "type": "string"
                    }
                  }
                }
              }
            }
          },
          "created_at": {
            "description": "Data de criação da negociação.",
            "type": "string",
            "format": "date-time"
          },
          "updated_at": {
            "description": "Data de atualização da negociação.",
            "type": "string",
            "format": "date-time"
          }
        }
      },
      "DistributionSetting": {
        "type": "object",
        "writeOnly": true,
        "properties": {
          "stage_id": {
            "description": "ID da etapa do funil de vendas da negociação.",
            "type": "string",
            "pattern": "^[0-9a-f]{24}$"
          },
          "rule": {
            "description": "Configurações para seleção do usuário para receber a negociação.",
            "type": "object",
            "properties": {
              "type": {
                "description": "Tipo de distribuição.",
                "type": "string",
                "enum": [
                  "user",
                  "team",
                  "all",
                  "all_users",
                  "all_admins",
                  "owner"
                ]
              },
              "id": {
                "description": "Identificador do time ou usuário para distribuição da negociação.",
                "type": "string",
                "pattern": "^[0-9a-f]{24}$"
              },
              "email": {
                "description": "Email do usuário para distribuir a negociação.",
                "type": "string"
              }
            }
          }
        }
      },
      "Email": {
        "type": "object",
        "properties": {
          "email": {
            "description": "Endereço de email.",
            "type": "string"
          }
        }
      },
      "Error": {
        "type": "object",
        "properties": {
          "errors": {
            "type": "array",
            "items": {
              "type": "object",
              "required": [
                "detail"
              ],
              "properties": {
                "type": {
                  "description": "Tipo do erro. `NOT_FOUND` (404), `VALIDATION` (422), `INVALID_PARAMETER` (400 ou 422 de filtro), `AUTHORIZATION` (401 do serviço de webhooks), `FORBIDDEN` (403) e `INTERNAL_ERROR` (500).",
                  "type": "string",
                  "enum": [
                    "NOT_FOUND",
                    "VALIDATION",
                    "INVALID_PARAMETER",
                    "AUTHORIZATION",
                    "FORBIDDEN",
                    "INTERNAL_ERROR"
                  ]
                },
                "title": {
                  "description": "Título curto do tipo do erro (ex.: `Invalid Parameter`).",
                  "type": "string"
                },
                "detail": {
                  "description": "Explicação do erro. No 500 é sempre `Internal server error`, sem detalhes técnicos.",
                  "type": "string"
                },
                "source": {
                  "description": "Origem do erro na requisição. Ausente quando não se aplica.",
                  "type": "object",
                  "properties": {
                    "parameter": {
                      "description": "Parâmetro de consulta que causou o erro (ex.: `filter`, `page`).",
                      "type": "string"
                    },
                    "pointer": {
                      "description": "Campo do corpo da requisição que causou o erro, em JSON Pointer (RFC 6901) (ex.: `/data/name`). Presente nos erros 422 de validação de um campo do contrato.",
                      "type": "string"
                    }
                  }
                }
              }
            }
          }
        }
      },
      "Lead": {
        "type": "object",
        "properties": {
          "id": {
            "description": "Identificador único.",
            "type": "string",
            "pattern": "^[0-9a-f]{24}$",
            "readOnly": true
          },
          "name": {
            "description": "Nome do lead. Obrigatório na criação. Mínimo de 2 e máximo de 255 caracteres.",
            "type": "string",
            "minLength": 2,
            "maxLength": 255
          },
          "status": {
            "description": "Status do lead. Na criação, somente `ongoing` (padrão). Valores: `ongoing`, `converted`, `discarded`.",
            "type": "string",
            "enum": [
              "ongoing",
              "converted",
              "discarded"
            ]
          },
          "rating": {
            "description": "Qualificação do lead, de 1 a 5. Padrão `1`.",
            "type": "integer",
            "minimum": 1,
            "maximum": 5
          },
          "stage_id": {
            "description": "ID da etapa do lead. Na criação, se omitido, o lead é associado à primeira etapa do funil.",
            "type": "string",
            "pattern": "^[0-9a-f]{24}$"
          },
          "source_id": {
            "description": "ID da fonte do lead.",
            "type": "string",
            "pattern": "^[0-9a-f]{24}$"
          },
          "campaign_id": {
            "description": "ID da campanha associada ao lead.",
            "type": "string",
            "pattern": "^[0-9a-f]{24}$"
          },
          "organization_id": {
            "description": "ID da empresa associada ao lead.",
            "type": "string",
            "pattern": "^[0-9a-f]{24}$"
          },
          "contact_ids": {
            "description": "IDs dos contatos vinculados ao lead. Todos devem existir na conta.",
            "type": "array",
            "items": {
              "type": "string",
              "pattern": "^[0-9a-f]{24}$"
            }
          },
          "owner_id": {
            "description": "ID do usuário responsável pelo lead. Obrigatório na criação.",
            "type": "string",
            "pattern": "^[0-9a-f]{24}$"
          },
          "created_at": {
            "description": "Data de criação do lead.",
            "type": "string",
            "format": "date-time",
            "readOnly": true
          },
          "updated_at": {
            "description": "Data de atualização do lead.",
            "type": "string",
            "format": "date-time",
            "readOnly": true
          }
        }
      },
      "LeadDeletedWebhookDocument": {
        "description": "Documento do webhook de lead deletado.",
        "type": "object",
        "required": [
          "data"
        ],
        "properties": {
          "data": {
            "type": "object",
            "properties": {
              "id": {
                "description": "Identificador único.",
                "type": "string",
                "pattern": "^[0-9a-f]{24}$"
              },
              "name": {
                "description": "Nome do lead.",
                "type": "string"
              }
            }
          }
        }
      },
      "LeadWebhookDocument": {
        "description": "Documento do webhook de lead.",
        "type": "object",
        "required": [
          "data"
        ],
        "properties": {
          "data": {
            "$ref": "#/components/schemas/Lead"
          }
        }
      },
      "LegalBase": {
        "type": "object",
        "properties": {
          "category": {
            "description": "A categoria relativa à base legal.",
            "type": "string",
            "enum": [
              "communications"
            ]
          },
          "type": {
            "description": "Qual base legal autoriza o tratamento dos dados pessoais.",
            "type": "string",
            "enum": [
              "consent",
              "legitimate_interest",
              "pre_existent_contract",
              "judicial_process",
              "vital_interest",
              "public_interest"
            ]
          },
          "status": {
            "description": "Status da base legal.",
            "type": "string",
            "enum": [
              "granted",
              "declined"
            ],
            "x-enumDescriptions": {
              "granted": "Consentimento concedido pelo contato.",
              "declined": "Consentimento recusado pelo contato."
            }
          }
        }
      },
      "LostReason": {
        "type": "object",
        "properties": {
          "id": {
            "description": "Identificador único.",
            "type": "string",
            "pattern": "^[0-9a-f]{24}$",
            "readOnly": true
          },
          "name": {
            "description": "Nome do motivo de perda.",
            "type": "string"
          },
          "created_at": {
            "description": "Data de criação do motivo de perda.",
            "type": "string",
            "format": "date-time",
            "readOnly": true
          },
          "updated_at": {
            "description": "Data de atualização do motivo de perda.",
            "type": "string",
            "format": "date-time",
            "readOnly": true
          }
        }
      },
      "DialerCall": {
        "type": "object",
        "properties": {
          "id": {
            "description": "Identificador único da ligação.",
            "type": "string",
            "pattern": "^[0-9a-f]{24}$",
            "readOnly": true
          },
          "status": {
            "description": "Status da ligação. Valores: `initial`, `answered`, `no_answer`, `busy`, `congested`, `failed`.",
            "type": "string",
            "readOnly": true,
            "enum": [
              "initial",
              "answered",
              "no_answer",
              "busy",
              "congested",
              "failed"
            ]
          },
          "user_id": {
            "description": "ID de quem ligou.",
            "type": "string",
            "pattern": "^[0-9a-f]{24}$",
            "readOnly": true
          },
          "deal_id": {
            "description": "ID da negociação. Preenchido quando o pai é um deal.",
            "type": [
              "string",
              "null"
            ],
            "pattern": "^[0-9a-f]{24}$",
            "readOnly": true
          },
          "lead_id": {
            "description": "ID do lead. Preenchido quando o pai é um lead.",
            "type": [
              "string",
              "null"
            ],
            "pattern": "^[0-9a-f]{24}$",
            "readOnly": true
          },
          "deal_stage_id": {
            "description": "Etapa do deal na ligação.",
            "type": [
              "string",
              "null"
            ],
            "pattern": "^[0-9a-f]{24}$",
            "readOnly": true
          },
          "lead_stage_id": {
            "description": "Etapa do lead na ligação.",
            "type": [
              "string",
              "null"
            ],
            "pattern": "^[0-9a-f]{24}$",
            "readOnly": true
          },
          "contact_id": {
            "description": "ID do contato.",
            "type": [
              "string",
              "null"
            ],
            "pattern": "^[0-9a-f]{24}$",
            "readOnly": true
          },
          "phone_number_to": {
            "description": "Número discado.",
            "type": [
              "string",
              "null"
            ],
            "readOnly": true
          },
          "started_at": {
            "description": "Início da ligação.",
            "type": [
              "string",
              "null"
            ],
            "format": "date-time",
            "readOnly": true
          },
          "answered_at": {
            "description": "Momento em que a ligação foi atendida.",
            "type": [
              "string",
              "null"
            ],
            "format": "date-time",
            "readOnly": true
          },
          "ended_at": {
            "description": "Fim da ligação.",
            "type": [
              "string",
              "null"
            ],
            "format": "date-time",
            "readOnly": true
          },
          "duration": {
            "description": "Duração em segundos.",
            "type": [
              "integer",
              "null"
            ],
            "readOnly": true
          },
          "recording_url": {
            "description": "URL da gravação.",
            "type": [
              "string",
              "null"
            ],
            "readOnly": true
          },
          "external_id": {
            "description": "ID da ligação no Webphone.",
            "type": "string",
            "readOnly": true
          },
          "created_at": {
            "description": "Data de criação.",
            "type": "string",
            "format": "date-time",
            "readOnly": true
          },
          "updated_at": {
            "description": "Data de atualização.",
            "type": "string",
            "format": "date-time",
            "readOnly": true
          },
          "transcription": {
            "$ref": "#/components/schemas/DialerCallTranscription"
          }
        }
      },
      "DialerCallTranscription": {
        "type": "object",
        "properties": {
          "status": {
            "description": "Status da transcrição. Valores: `processing`, `completed`.",
            "type": [
              "string",
              "null"
            ],
            "enum": [
              "processing",
              "completed"
            ]
          },
          "summary": {
            "description": "Resumo da transcrição, ou a mensagem de falha quando o Webphone não consegue transcrever.",
            "type": [
              "string",
              "null"
            ]
          },
          "content": {
            "description": "Falas da transcrição.",
            "type": "array",
            "items": {
              "$ref": "#/components/schemas/DialerCallTranscriptionContent"
            }
          }
        }
      },
      "DialerCallTranscriptionContent": {
        "type": "object",
        "properties": {
          "time": {
            "description": "Instante da fala.",
            "type": "string"
          },
          "speaker": {
            "description": "Quem falou (valor repassado pelo Webphone).",
            "type": "string"
          },
          "text": {
            "description": "Texto da fala.",
            "type": "string"
          }
        }
      },
      "DialerCallWebhookDocument": {
        "description": "Documento do webhook de ligação do Webphone.",
        "type": "object",
        "required": [
          "data"
        ],
        "properties": {
          "data": {
            "$ref": "#/components/schemas/DialerCall"
          }
        }
      },
      "Meeting": {
        "type": "object",
        "properties": {
          "id": {
            "description": "Identificador único da reunião.",
            "type": "string",
            "pattern": "^[0-9a-f]{24}$",
            "readOnly": true
          },
          "subject": {
            "description": "Assunto da reunião. Tamanho máximo de 150 caracteres.",
            "type": "string",
            "maxLength": 150
          },
          "notes": {
            "description": "Observações da reunião. Tamanho máximo de 1000 caracteres.",
            "type": "string",
            "maxLength": 1000
          },
          "starts_at": {
            "description": "Data e hora de início da reunião.",
            "type": "string",
            "format": "date-time"
          },
          "ends_at": {
            "description": "Data e hora de término da reunião (calculado a partir de `starts_at` e `duration_minutes`).",
            "type": "string",
            "format": "date-time",
            "readOnly": true
          },
          "duration_minutes": {
            "description": "Duração da reunião em minutos.",
            "type": "integer",
            "minimum": 1
          },
          "status": {
            "description": "Status da reunião. Valores: `scheduled`, `completed`, `no_show`.",
            "type": "string",
            "enum": [
              "scheduled",
              "completed",
              "no_show"
            ]
          },
          "responsible_id": {
            "description": "ID do usuário responsável pela reunião.",
            "type": "string",
            "pattern": "^[0-9a-f]{24}$"
          },
          "organizer_id": {
            "description": "ID do usuário organizador da reunião.",
            "type": "string",
            "pattern": "^[0-9a-f]{24}$"
          },
          "contact_ids": {
            "description": "IDs dos contatos participantes da reunião (máximo de 20).",
            "type": "array",
            "maxItems": 20,
            "items": {
              "type": "string",
              "pattern": "^[0-9a-f]{24}$"
            }
          },
          "created_at": {
            "description": "Data de criação da reunião.",
            "type": "string",
            "format": "date-time",
            "readOnly": true
          },
          "updated_at": {
            "description": "Data de atualização da reunião.",
            "type": "string",
            "format": "date-time",
            "readOnly": true
          }
        }
      },
      "MeetingWebhookDocument": {
        "description": "Documento do webhook de reunião.",
        "type": "object",
        "required": [
          "data"
        ],
        "properties": {
          "data": {
            "$ref": "#/components/schemas/Meeting"
          }
        }
      },
      "Proposal": {
        "description": "Proposta comercial vinculada à negociação (recurso serializado pela API v2).",
        "type": "object",
        "properties": {
          "id": {
            "description": "Identificador único da proposta.",
            "type": "string",
            "pattern": "^[0-9a-f]{24}$",
            "readOnly": true
          },
          "status": {
            "description": "Status da proposta. Valores: `active`, `inactive`.",
            "type": "string",
            "enum": [
              "active",
              "inactive"
            ]
          },
          "approval_status": {
            "description": "Status de aprovação. Valores: `pending`, `approved`.",
            "type": "string",
            "readOnly": true,
            "enum": [
              "pending",
              "approved"
            ]
          },
          "approved_at": {
            "description": "Data em que a proposta foi aprovada.",
            "type": "string",
            "format": "date-time",
            "readOnly": true
          },
          "token": {
            "description": "Token público de acesso à proposta (compartilhamento).",
            "type": "string",
            "readOnly": true
          },
          "total": {
            "description": "Valor total da proposta (alinhado ao total da negociação no momento da criação).",
            "type": "number",
            "format": "float",
            "readOnly": true
          },
          "sections": {
            "description": "Seções persistidas da proposta.",
            "type": "array",
            "items": {
              "$ref": "#/components/schemas/ProposalSection"
            }
          },
          "deal_id": {
            "description": "ID da negociação associada.",
            "type": "string",
            "pattern": "^[0-9a-f]{24}$",
            "readOnly": true
          },
          "proposal_template_id": {
            "description": "ID do modelo de proposta utilizado na criação.",
            "type": "string",
            "pattern": "^[0-9a-f]{24}$"
          },
          "created_by_id": {
            "description": "ID do usuário que criou a proposta.",
            "type": "string",
            "pattern": "^[0-9a-f]{24}$",
            "readOnly": true
          },
          "created_at": {
            "description": "Data de criação da proposta.",
            "type": "string",
            "format": "date-time",
            "readOnly": true
          },
          "updated_at": {
            "description": "Data de atualização da proposta.",
            "type": "string",
            "format": "date-time",
            "readOnly": true
          }
        }
      },
      "ProposalSection": {
        "description": "Seção de conteúdo da proposta (contrato API v2).",
        "type": "object",
        "properties": {
          "id": {
            "description": "Identificador da seção, quando persistido.",
            "type": "string",
            "pattern": "^[0-9a-f]{24}$",
            "readOnly": true
          },
          "slug": {
            "description": "Slug da seção no modelo.",
            "type": "string"
          },
          "type": {
            "description": "Tipo da seção.",
            "type": "string",
            "enum": [
              "html",
              "products_list"
            ]
          },
          "value": {
            "description": "Conteúdo da seção (ex. HTML para tipo `html`; sanitizado no servidor quando aplicável).",
            "type": "string"
          },
          "order": {
            "description": "Ordem de exibição da seção.",
            "type": "integer"
          },
          "lock": {
            "description": "Indica se a seção está bloqueada para edição.",
            "type": "boolean"
          },
          "properties": {
            "description": "Propriedades da seção (objeto). O formato depende do `type` da seção.",
            "$ref": "#/components/schemas/ProposalSectionProperties"
          }
        }
      },
      "ProposalSectionLayoutProperties": {
        "description": "Configuração de layout vertical da seção.",
        "type": "object",
        "properties": {
          "padding_top": {
            "description": "Espaçamento superior da seção, em pixels.",
            "type": "integer",
            "minimum": 0
          },
          "padding_bottom": {
            "description": "Espaçamento inferior da seção, em pixels.",
            "type": "integer",
            "minimum": 0
          }
        }
      },
      "ProposalSectionProductsListColumn": {
        "description": "Coluna exibida em seções do tipo `products_list`.",
        "type": "object",
        "required": [
          "entity",
          "field_type",
          "identifier"
        ],
        "properties": {
          "entity": {
            "description": "Entidade de origem do campo (`product` ou `deal_product`).",
            "type": "string"
          },
          "field_type": {
            "description": "Tipo do campo (`default` ou `custom`).",
            "type": "string"
          },
          "identifier": {
            "description": "Identificador do campo na entidade.",
            "type": "string"
          }
        }
      },
      "ProposalSectionProperties": {
        "description": "Propriedades da seção. Para `html`, use `layout` com espaçamento vertical.\nPara `products_list`, use `columns` (lista de colunas) e, opcionalmente, `layout`.",
        "type": "object",
        "properties": {
          "layout": {
            "$ref": "#/components/schemas/ProposalSectionLayoutProperties"
          },
          "columns": {
            "description": "Colunas da tabela de produtos (apenas para seções `products_list`).",
            "type": "array",
            "items": {
              "$ref": "#/components/schemas/ProposalSectionProductsListColumn"
            }
          }
        },
        "additionalProperties": true
      },
      "Organization": {
        "type": "object",
        "properties": {
          "id": {
            "description": "Identificador único.",
            "type": "string",
            "pattern": "^[0-9a-f]{24}$",
            "readOnly": true
          },
          "name": {
            "description": "Nome da empresa.",
            "type": "string"
          },
          "description": {
            "description": "Descrição da empresa.",
            "type": "string"
          },
          "url": {
            "description": "Site da empresa.",
            "type": "string"
          },
          "address": {
            "description": "Endereço da empresa.",
            "$ref": "#/components/schemas/Address"
          },
          "segment_ids": {
            "description": "IDs dos segmentos da empresa.",
            "type": "array",
            "items": {
              "type": "string",
              "pattern": "^[0-9a-f]{24}$"
            }
          },
          "follower_ids": {
            "description": "IDs dos usuários seguidores da empresa.",
            "type": "array",
            "items": {
              "type": "string",
              "pattern": "^[0-9a-f]{24}$"
            }
          },
          "owner_id": {
            "description": "ID do usuário responsável pela empresa.",
            "type": "string",
            "pattern": "^[0-9a-f]{24}$"
          },
          "custom_fields": {
            "description": "Campos personalizados da empresa.",
            "$ref": "#/components/schemas/CustomFields"
          },
          "created_at": {
            "description": "Data de criação da empresa.",
            "type": "string",
            "format": "date-time",
            "readOnly": true
          },
          "updated_at": {
            "description": "Data de atualização da empresa.",
            "type": "string",
            "format": "date-time",
            "readOnly": true
          }
        }
      },
      "PaginationLinks": {
        "description": "Links de navegação da paginação.",
        "type": "object",
        "properties": {
          "first": {
            "description": "Link para a primeira página.",
            "type": "string",
            "format": "uri"
          },
          "prev": {
            "description": "Link para a página anterior.",
            "type": "string",
            "format": "uri"
          },
          "self": {
            "description": "Link para a página atual.",
            "type": "string",
            "format": "uri"
          },
          "next": {
            "description": "Link para a próxima página.",
            "type": "string",
            "format": "uri"
          },
          "last": {
            "description": "Link para a última página.",
            "type": "string",
            "format": "uri"
          }
        }
      },
      "PayloadDataList": {
        "type": "object",
        "properties": {
          "data": {
            "description": "Lista de recursos relacionados.",
            "type": "array",
            "items": {
              "description": "Dados do recurso relacionado.",
              "type": "object"
            }
          }
        }
      },
      "PayloadLinks": {
        "type": "object",
        "properties": {
          "links": {
            "description": "Links relacionados.",
            "type": "object"
          }
        }
      },
      "Phone": {
        "type": "object",
        "properties": {
          "phone": {
            "description": "Telefone.",
            "type": "string"
          },
          "type": {
            "description": "Tipo do telefone.",
            "type": "string",
            "enum": [
              "work",
              "fax",
              "home",
              "mobile"
            ]
          }
        }
      },
      "Product": {
        "type": "object",
        "properties": {
          "id": {
            "description": "Identificador único.",
            "type": "string",
            "pattern": "^[0-9a-f]{24}$",
            "readOnly": true
          },
          "name": {
            "description": "Nome do produto.",
            "type": "string"
          },
          "description": {
            "description": "Descrição do produto.",
            "type": "string"
          },
          "price": {
            "description": "Preço do produto.",
            "type": "number",
            "format": "float"
          },
          "visible": {
            "description": "Visibilidade do produto.",
            "type": "boolean"
          },
          "custom_fields": {
            "description": "Campos personalizados do produto.",
            "$ref": "#/components/schemas/CustomFields"
          },
          "created_at": {
            "description": "Data de criação do produto.",
            "type": "string",
            "format": "date-time",
            "readOnly": true
          },
          "updated_at": {
            "description": "Data de atualização do produto.",
            "type": "string",
            "format": "date-time",
            "readOnly": true
          }
        }
      },
      "SocialProfile": {
        "type": "object",
        "properties": {
          "type": {
            "description": "Tipo de perfil social.",
            "type": "string",
            "enum": [
              "facebook",
              "linkedin",
              "skype"
            ]
          },
          "username": {
            "description": "Nome de usuário.",
            "type": "string"
          }
        }
      },
      "Source": {
        "type": "object",
        "properties": {
          "id": {
            "description": "Identificador único.",
            "type": "string",
            "pattern": "^[0-9a-f]{24}$",
            "readOnly": true
          },
          "name": {
            "description": "Nome da fonte.",
            "type": "string"
          },
          "description": {
            "description": "Descrição da fonte.",
            "type": "string"
          },
          "created_at": {
            "description": "Data de criação da fonte.",
            "type": "string",
            "format": "date-time",
            "readOnly": true
          },
          "updated_at": {
            "description": "Data de atualização da fonte.",
            "type": "string",
            "format": "date-time",
            "readOnly": true
          }
        }
      },
      "Task": {
        "type": "object",
        "properties": {
          "id": {
            "description": "Identificador único.",
            "type": "string",
            "pattern": "^[0-9a-f]{24}$",
            "readOnly": true
          },
          "name": {
            "description": "Assunto da tarefa.",
            "type": "string"
          },
          "description": {
            "description": "Notas ou descrição adicional da tarefa.",
            "type": "string"
          },
          "type": {
            "description": "Tipo da tarefa.",
            "type": "string",
            "enum": [
              "call",
              "email",
              "meeting",
              "task",
              "lunch",
              "visit",
              "whatsapp"
            ]
          },
          "status": {
            "description": "Status da tarefa.",
            "type": "string",
            "enum": [
              "open",
              "completed",
              "canceled"
            ]
          },
          "due_date": {
            "description": "Data limite para conclusão da tarefa.",
            "type": "string",
            "format": "date-time"
          },
          "created_by_id": {
            "description": "ID do usuário que criou a tarefa.",
            "type": "string",
            "pattern": "^[0-9a-f]{24}$"
          },
          "completed_at": {
            "description": "Data em que a tarefa foi concluída.",
            "type": "string",
            "format": "date-time",
            "readOnly": true
          },
          "completed_by_id": {
            "description": "ID do usuário que concluiu a tarefa.",
            "type": "string",
            "pattern": "^[0-9a-f]{24}$"
          },
          "deal_id": {
            "description": "ID da negociação associada.",
            "type": "string",
            "pattern": "^[0-9a-f]{24}$"
          },
          "owner_ids": {
            "description": "IDs dos usuários responsáveis pela tarefa.",
            "type": "array",
            "items": {
              "type": "string",
              "pattern": "^[0-9a-f]{24}$"
            }
          },
          "created_at": {
            "description": "Data de criação da tarefa.",
            "type": "string",
            "format": "date-time",
            "readOnly": true
          },
          "updated_at": {
            "description": "Data de atualização da tarefa.",
            "type": "string",
            "format": "date-time",
            "readOnly": true
          }
        }
      },
      "WebhookEvent": {
        "type": "object",
        "properties": {
          "event_name": {
            "description": "Tipo de evento do webhook.",
            "type": "string",
            "example": "crm_deal_created"
          },
          "event_timestamp": {
            "description": "A data em que ocorreu o evento que acionou o webhook.",
            "type": "string",
            "format": "date-time",
            "example": "2025-01-01T00:00:00.000Z"
          },
          "transaction_uuid": {
            "description": "Identificador único do evento.",
            "type": "string",
            "format": "uuid",
            "example": "00000000-0052-4400-B753-746174696F6E"
          },
          "document": {
            "description": "Documento relacionado ao evento do webhook.",
            "type": "object"
          }
        }
      }
    }
  }
}
```