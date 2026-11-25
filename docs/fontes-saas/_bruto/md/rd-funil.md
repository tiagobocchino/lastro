---
updatedAt: 2025-09-18T21:29:41.000Z
agentTools:
  projectIndex: https://developers.rdstation.com/llms.txt
---

# Consultar Estatísticas do Funil de Vendas

O objetivo desta API é fornecer os dados funil de vendas com as quantidades de visitantes, leads, oportunidades e vendas cumulativo referente ao período consultado, a fim de trazer mais clareza com relação a performance do seu funil de vendas.

> 🚧 API disponível somente para plano Advanced.

> 📘 Obs: A API de Estatísticas de Funil de Vendas retorna dados a partir de Junho de 2022.

# OpenAPI definition

```json
{
  "openapi": "3.0.1",
  "info": {
    "title": "Funnels - RD Station Marketing API",
    "version": "v2"
  },
  "servers": [
    {
      "url": "api.rd.services"
    }
  ],
  "components": {
    "securitySchemes": {
      "rdsmapi_auth": {
        "type": "http",
        "scheme": "bearer"
      }
    }
  },
  "paths": {
    "/platform/analytics/funnel": {
      "get": {
        "summary": "Consultar Estatísticas do Funil de Vendas",
        "tags": [
          "Análise"
        ],
        "description": "O objetivo desta API é fornecer os dados funil de vendas com as quantidades de visitantes, leads, oportunidades e vendas cumulativo referente ao período consultado, a fim de trazer mais clareza com relação a performance do seu funil de vendas.",
        "security": [
          {
            "rdsmapi_auth": []
          }
        ],
        "parameters": [
          {
            "name": "start_date",
            "in": "query",
            "description": "Data de início a ser consultada. (yyyy-mm-dd)",
            "example": "2023-01-10",
            "schema": {
              "type": "string"
            }
          },
          {
            "name": "end_date",
            "in": "query",
            "description": "Data de término a ser consultada. (yyyy-mm-dd)",
            "example": "2023-01-15",
            "schema": {
              "type": "string"
            }
          },
          {
            "name": "grouped_by",
            "in": "query",
            "required": false,
            "description": "Filtro para agrupamento do período de análise, opções são: daily, weekly e monthly. Requisições sem esse campo preenchido retornam dados diários.",
            "schema": {
              "type": "string",
              "enum": [
                "daily",
                "weekly",
                "monthly"
              ]
            },
            "example": "daily"
          }
        ],
        "responses": {
          "200": {
            "description": "Success",
            "content": {
              "application/json": {
                "schema": {
                  "type": "object",
                  "properties": {
                    "account_id": {
                      "type": "integer",
                      "description": "O id associado a cada conta do RD Station",
                      "example": 1
                    },
                    "query_date": {
                      "type": "object",
                      "description": "O período de tempo usado para buscar os dados",
                      "properties": {
                        "start_date": {
                          "type": "string",
                          "format": "date"
                        },
                        "end_date": {
                          "type": "string",
                          "format": "date"
                        }
                      }
                    },
                    "grouped_by": {
                      "type": "string",
                      "description": "Filtro para agrupamento do período de análise, opções são: daily,weekly e monthly. Requisições sem esse campo preenchido retornam dados diários",
                      "example": "daily"
                    },
                    "funnel": {
                      "type": "array",
                      "items": {
                        "type": "object",
                        "properties": {
                          "reference_day": {
                            "type": "string",
                            "description": "Dia de referência do funil",
                            "example": "2023-01-15"
                          },
                          "visitors_count": {
                            "type": "integer",
                            "description": "Total de visitantes (usuários - GA)",
                            "example": 1000
                          },
                          "contacts_count": {
                            "type": "integer",
                            "description": "Total de contatos",
                            "example": 100
                          },
                          "qualified_contacts_count": {
                            "type": "integer",
                            "description": "Total contatos qualificados",
                            "example": 85
                          },
                          "opportunities_count": {
                            "type": "integer",
                            "description": "Total de oportunidades",
                            "example": 50
                          },
                          "sales_count": {
                            "type": "integer",
                            "description": "Total de vendas",
                            "example": 10
                          }
                        },
                        "required": [
                          "reference_day",
                          "visitors_count",
                          "contacts_count",
                          "qualified_contacts_count",
                          "opportunities_count",
                          "sales_count"
                        ]
                      }
                    }
                  }
                }
              }
            }
          },
          "400": {
            "description": "Bad Request",
            "content": {
              "application/json": {
                "example": {
                  "errors": [
                    {
                      "start_date": {
                        "invalid_date_format": "2023-15-10"
                      },
                      "end_date": {
                        "invalid_date_format": "2023-15-50"
                      },
                      "grouped_by": {
                        "invalid_group_type": "wrong_group"
                      }
                    }
                  ]
                },
                "schema": {
                  "type": "object",
                  "properties": {
                    "errors": {
                      "type": "array",
                      "items": {
                        "type": "object",
                        "properties": {
                          "start_date": {
                            "type": "object",
                            "properties": {
                              "invalid_date_format": {
                                "type": "string"
                              }
                            }
                          },
                          "end_date": {
                            "type": "object",
                            "properties": {
                              "invalid_date_format": {
                                "type": "string"
                              }
                            }
                          },
                          "grouped_by": {
                            "type": "object",
                            "properties": {
                              "invalid_group_type": {
                                "type": "string"
                              }
                            }
                          }
                        }
                      }
                    }
                  }
                }
              }
            }
          },
          "401": {
            "description": "Unauthorized or Forbidden",
            "content": {
              "application/json": {
                "example": {
                  "errors": {
                    "error_type": "UNAUTHORIZED",
                    "error_message": "Invalid token"
                  }
                },
                "schema": {
                  "type": "object",
                  "properties": {
                    "errors": {
                      "type": "object",
                      "properties": {
                        "error_type": {
                          "type": "string"
                        },
                        "error_message": {
                          "type": "string"
                        }
                      }
                    }
                  }
                }
              }
            }
          }
        }
      }
    }
  },
  "x-readme": {
    "explorer-enabled": true,
    "proxy-enabled": true
  }
}
```