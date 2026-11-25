---
updatedAt: 2026-08-27T09:08:19.000Z
agentTools:
  projectIndex: https://developers.kommo.com/llms.txt
---

# Get leads

This method allows getting a list of leads in the account

**Limitations**
The method is available in accordance with the user’s rights.

`“with”`**parameters**

| Parameter                      | Description                                                                                                                                                                                                                                            |
| :----------------------------- | :----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| contacts                       | Adds information about the contacts associated with the lead to the response                                                                                                                                                                           |
| only\_deleted                  | If this parameter is passed, the method request will return only the deleted leads that are still restorable in the response. You will receive lead models with the following properties: “id”, modification date and “is\_deleted” = true parameters. |
| loss\_reason                   | Adds detailed information about the lead loss reason to the response                                                                                                                                                                                   |
| is\_price\_modified\_by\_robot | Adds a property represents whether the lead sale value was changed last time by Robot to the response                                                                                                                                                  |
| catalog\_elements              | Adds lists items linked to the lead to the response                                                                                                                                                                                                    |
| source\_id                     | Adds the lead source ID to the response                                                                                                                                                                                                                |
| source                         | Adds information about the source, its ID and name to the response                                                                                                                                                                                     |

### filter\[statuses]

<Callout icon="❗️" theme="error">
  Due to the service limitations, you can filter only one stage in one pipeline. But it is possible to filter several stages within several pipelines outside of the service.
</Callout>

**Data type header when the request is successful**
Content-Type: application/hal+json

**Data type header in case of an error**
Content-Type: application/problem+json

**Response parameters**

| Parameter                                          | Data type   | Description                                                                                                        |
| :------------------------------------------------- | :---------- | :----------------------------------------------------------------------------------------------------------------- |
| id                                                 | int         | Lead ID                                                                                                            |
| name                                               | string      | Lead name                                                                                                          |
| price                                              | int         | Lead sale                                                                                                          |
| responsible\_user\_id                              | int         | Lead responsible user ID                                                                                           |
| group\_id                                          | int         | Group ID of the lead responsible user                                                                              |
| status\_id                                         | int         | ID of the stage the lead is added to, the first stage of the main pipeline by default                              |
| pipeline\_id                                       | int         | ID of the pipeline the lead is added to                                                                            |
| loss\_reason\_id                                   | int         | Lead loss reason ID                                                                                                |
| source\_id                                         | int         | **GET parameter “with” is required.**<br />Lead source ID.                                                         |
| created\_by                                        | int         | Id of the user who created the lead                                                                                |
| updated\_by                                        | int         | Id of the user who updated the lead                                                                                |
| created\_at                                        | int         | The time and date the lead was created in the format of Unix Timestamp                                             |
| updated\_at                                        | int         | The time and date the lead was updated in the format of Unix Timestamp                                             |
| closed\_at                                         | int         | The time and date the lead was closed in the format of Unix Timestamp                                              |
| closest\_task\_at                                  | int         | The time and date of the closest open task in the format of Unix Timestamp                                         |
| custom\_fields\_values                             | array\|null | An array containing information on the values of custom fields specified for this lead                             |
| score                                              | int\|null   | Lead score                                                                                                         |
| account\_id                                        | int         | Account ID where the lead is located in                                                                            |
| labor\_cost                                        | int         | Shows how much time was spent working with the lead. Calculation time in seconds.                                  |
| is\_price\_modified\_by\_robot                     | bool        | **GET parameter “with” is required.**<br />Defines whether the lead sale value was changed by the Robot last time. |
| \_embedded                                         | object      | Embedded entities data                                                                                             |
| \_embedded\[loss\_reason]\[loss\_reason]           | object      | **GET parameter “with” is required.**<br />Lead loss reason                                                        |
| \_embedded\[loss\_reason]\[id]                     | int         | Loss reason ID                                                                                                     |
| \_embedded\[loss\_reason]\[name]                   | string      | Loss reason name                                                                                                   |
| \_embedded\[tags]                                  | array       | Lead tags data array                                                                                               |
| \_embedded\[tags]\[0]                              | object      | Lead tag model                                                                                                     |
| \_embedded\[tags]\[0]\[id]                         | int         | Tag ID                                                                                                             |
| \_embedded\[tags]\[0]\[name]                       | string      | Tag name                                                                                                           |
| \_embedded\[tags]\[0]\[color]                      | string/null | Tag color                                                                                                          |
| \_embedded\[contacts]                              | array       | **GET parameter “with” is required.**<br />Linked contacts data array.                                             |
| \_embedded\[contacts]\[0]                          | object      | Linked contact data                                                                                                |
| \_embedded\[contacts]\[0]\[id]                     | ints        | Linked contact ID                                                                                                  |
| \_embedded\[contacts]\[0]\[is\_main]\[is\_main]    | bool        | Defines whether the contact is main for the lead                                                                   |
| \_embedded\[companies]                             | array       | Linked company data array. This array always consists of 1 element as a lead can have only 1 company linked to it. |
| \_embedded\[companies]\[0]                         | object      | Linked company data                                                                                                |
| \_embedded\[companies]\[0]\[id]                    | int         | Linked company ID                                                                                                  |
| \_embedded\[catalog\_elements]\[catalog\_elements] | array       | **GET parameter “with” is required.**<br />Linked lists’ elements data array.                                      |
| \_embedded\[catalog\_elements]\[0]                 | object      | Linked list element data                                                                                           |
| \_embedded\[catalog\_elements]\[0]\[id]            | int         | Linked element ID                                                                                                  |
| \_embedded\[catalog\_elements]\[0]\[metadata]      | object      | Meta-data of the element                                                                                           |
| \_embedded\[catalog\_elements]\[0]\[quantity]      | int         | Linked element quantity                                                                                            |
| \_embedded\[source]                                | object      | **GET parameter "with" is required**. Lead source                                                                  |
| \_embedded\[source]\[id]                           | int         | Lead source ID                                                                                                     |
| \_embedded\[source]\[id]                           | string      | Lead source name                                                                                                   |

# OpenAPI definition

```json
{
  "openapi": "3.1.0",
  "info": {
    "title": "kommo-api-references",
    "version": "1.0"
  },
  "servers": [
    {
      "url": "https://{subdomain}.kommo.com",
      "variables": {
        "subdomain": {
          "default": "subdomain"
        }
      }
    }
  ],
  "components": {
    "securitySchemes": {
      "sec0": {
        "type": "oauth2",
        "flows": {}
      }
    }
  },
  "security": [
    {
      "sec0": []
    }
  ],
  "paths": {
    "/api/v4/leads": {
      "get": {
        "summary": "Get leads",
        "description": "This method allows getting a list of leads in the account",
        "operationId": "leads-list",
        "parameters": [
          {
            "name": "with",
            "in": "query",
            "description": "This parameter accepts a string which may consist of several values (look at the table above) separated by commas.",
            "schema": {
              "type": "string"
            }
          },
          {
            "name": "page",
            "in": "query",
            "description": "Page of leads list",
            "schema": {
              "type": "integer",
              "format": "int32"
            }
          },
          {
            "name": "limit",
            "in": "query",
            "description": "The number of entities returned per request (limit – 250)",
            "schema": {
              "type": "string"
            }
          },
          {
            "name": "query",
            "in": "query",
            "description": "Search query (Searches through the filled fields of the entity)",
            "schema": {
              "type": "string"
            }
          },
          {
            "name": "order[created_at]",
            "in": "query",
            "description": "Sorting the results",
            "schema": {
              "type": "string",
              "enum": [
                "asc",
                "desc"
              ]
            }
          },
          {
            "name": "order[updated_at]",
            "in": "query",
            "description": "Sorting the results",
            "schema": {
              "type": "string",
              "enum": [
                "asc",
                "desc"
              ]
            }
          },
          {
            "name": "order[id]",
            "in": "query",
            "description": "Sorting the results",
            "schema": {
              "type": "string",
              "enum": [
                "asc",
                "desc"
              ]
            }
          },
          {
            "name": "filter[id][]",
            "in": "query",
            "description": "Filter by lead ID",
            "schema": {
              "type": "array",
              "items": {
                "type": "integer",
                "format": "int32"
              }
            }
          },
          {
            "name": "filter[name][]",
            "in": "query",
            "description": "Filter by lead name",
            "schema": {
              "type": "array",
              "items": {
                "type": "string"
              }
            }
          },
          {
            "name": "filter[price]",
            "in": "query",
            "schema": {
              "type": "integer",
              "format": "int32"
            }
          },
          {
            "name": "filter[created_by][]",
            "in": "query",
            "description": "Filter by ID of the user who created the entity.",
            "schema": {
              "type": "array",
              "items": {
                "type": "integer",
                "format": "int32"
              }
            }
          },
          {
            "name": "filter[updated_by][]",
            "in": "query",
            "description": "Filter by ID of the user who changed the entity last",
            "schema": {
              "type": "array",
              "items": {
                "type": "integer",
                "format": "int32"
              }
            }
          },
          {
            "name": "filter[responsible_user_id][]",
            "in": "query",
            "description": "Filter by ID of the entity responsible user",
            "schema": {
              "type": "array",
              "items": {
                "type": "integer",
                "format": "int32"
              }
            }
          },
          {
            "name": "filter[created_at][from]",
            "in": "query",
            "description": "Filter by the creation date of the lead. Date in Unix Timestamp format",
            "schema": {
              "type": "integer",
              "format": "int32"
            }
          },
          {
            "name": "filter[created_at][to]",
            "in": "query",
            "description": "Filter by the creation date of the lead. Date in Unix Timestamp format",
            "schema": {
              "type": "integer",
              "format": "int32"
            }
          },
          {
            "name": "filter[updated_at][from]",
            "in": "query",
            "description": "Filter by the last update date of the lead. Date in Unix Timestamp format.",
            "schema": {
              "type": "integer",
              "format": "int32"
            }
          },
          {
            "name": "filter[updated_at][to]",
            "in": "query",
            "description": "Filter by the last update date of the lead. Date in Unix Timestamp format.",
            "schema": {
              "type": "integer",
              "format": "int32"
            }
          },
          {
            "name": "filter[closed_at][from]",
            "in": "query",
            "description": "Filter by the lead closing date. Date in Unix Timestamp format.",
            "schema": {
              "type": "integer",
              "format": "int32"
            }
          },
          {
            "name": "filter[closed_at][to]",
            "in": "query",
            "description": "Filter by the lead closing date. Date in Unix Timestamp format.",
            "schema": {
              "type": "integer",
              "format": "int32"
            }
          },
          {
            "name": "filter[closest_task_at][from]",
            "in": "query",
            "description": "Filter leads by the date of the task closest to completion. Date in Unix Timestamp format.",
            "schema": {
              "type": "integer",
              "format": "int32"
            }
          },
          {
            "name": "filter[closest_task_at][to]",
            "in": "query",
            "description": "Date in Unix Timestamp format. Date in Unix Timestamp format.",
            "schema": {
              "type": "integer",
              "format": "int32"
            }
          },
          {
            "name": "filter[pipeline_id][]",
            "in": "query",
            "description": "Filter by pipeline ID",
            "schema": {
              "type": "array",
              "items": {
                "type": "integer",
                "format": "int32"
              }
            }
          },
          {
            "name": "filter[statuses][0][pipeline_id]",
            "in": "query",
            "description": "Should be used with filter[statuses][0][status_id]. The filter allows you to filter leads based on their specific stages.",
            "schema": {
              "type": "integer",
              "format": "int32"
            }
          },
          {
            "name": "filter[statuses][0][status_id]",
            "in": "query",
            "description": "Should be used with filter[statuses][0][pipeline_id]. The filter allows you to filter leads based on their specific stages.",
            "schema": {
              "type": "integer",
              "format": "int32"
            }
          }
        ],
        "responses": {
          "200": {
            "description": "200",
            "content": {
              "application/json": {
                "examples": {
                  "Request successful": {
                    "value": {
                      "_page": 1,
                      "_links": {
                        "self": {
                          "href": "https://subdomain.kommo.com/api/v4/leads?page=1&limit=250"
                        }
                      },
                      "_embedded": {
                        "leads": [
                          {
                            "id": 20024930,
                            "name": "Lead 1",
                            "price": 0,
                            "responsible_user_id": 11087123,
                            "group_id": 0,
                            "status_id": 94386187,
                            "pipeline_id": 12215168,
                            "loss_reason_id": null,
                            "created_by": 11087123,
                            "updated_by": 11087123,
                            "created_at": 1760976072,
                            "updated_at": 1760976072,
                            "closed_at": null,
                            "closest_task_at": null,
                            "is_deleted": false,
                            "custom_fields_values": [
                              {
                                "field_id": 1928052,
                                "field_name": "Specialty",
                                "field_code": null,
                                "field_type": "select",
                                "values": [
                                  {
                                    "value": "Diagnostic",
                                    "enum_id": 1669868,
                                    "enum_code": null
                                  }
                                ],
                                "is_computed": false
                              },
                              {
                                "field_id": 1928056,
                                "field_name": "Date and time",
                                "field_code": null,
                                "field_type": "date_time",
                                "values": [
                                  {
                                    "value": 1723653000
                                  }
                                ],
                                "is_computed": false
                              }
                            ],
                            "score": null,
                            "account_id": 35379952,
                            "labor_cost": null,
                            "is_price_computed": false,
                            "_links": {
                              "self": {
                                "href": "https://subdomain.kommo.com/api/v4/leads/20024930?page=1&limit=250"
                              }
                            },
                            "_embedded": {
                              "tags": [],
                              "companies": []
                            }
                          },
                          {
                            "id": 20026102,
                            "name": "Lead 2",
                            "price": 0,
                            "responsible_user_id": 11087123,
                            "group_id": 0,
                            "status_id": 94386187,
                            "pipeline_id": 12215168,
                            "loss_reason_id": null,
                            "created_by": 11087123,
                            "updated_by": 11087123,
                            "created_at": 1760976113,
                            "updated_at": 1760976113,
                            "closed_at": null,
                            "closest_task_at": null,
                            "is_deleted": false,
                            "custom_fields_values": [
                              {
                                "field_id": 1928070,
                                "field_name": "Payment",
                                "field_code": null,
                                "field_type": "select",
                                "values": [
                                  {
                                    "value": "Full",
                                    "enum_id": 1669906,
                                    "enum_code": null
                                  }
                                ],
                                "is_computed": false
                              },
                              {
                                "field_id": 1928060,
                                "field_name": "Discount",
                                "field_code": null,
                                "field_type": "select",
                                "values": [
                                  {
                                    "value": "10%",
                                    "enum_id": 1669892,
                                    "enum_code": null
                                  }
                                ],
                                "is_computed": false
                              },
                              {
                                "field_id": 1928054,
                                "field_name": "Specialist",
                                "field_code": null,
                                "field_type": "select",
                                "values": [
                                  {
                                    "value": "Carl Woo",
                                    "enum_id": 1669878,
                                    "enum_code": null
                                  }
                                ],
                                "is_computed": false
                              }
                            ],
                            "score": null,
                            "account_id": 35379952,
                            "labor_cost": null,
                            "is_price_computed": true,
                            "_links": {
                              "self": {
                                "href": "https://subdomain.kommo.com/api/v4/leads/20026102?page=1&limit=250"
                              }
                            },
                            "_embedded": {
                              "tags": [],
                              "companies": [
                                {
                                  "id": 29610174,
                                  "_links": {
                                    "self": {
                                      "href": "https://subdomain.kommo.com/api/v4/companies/29610174?page=1&limit=250"
                                    }
                                  }
                                }
                              ]
                            }
                          }
                        ]
                      }
                    }
                  }
                },
                "schema": {
                  "type": "object",
                  "properties": {
                    "_page": {
                      "type": "integer",
                      "example": 1,
                      "default": 0
                    },
                    "_links": {
                      "type": "object",
                      "properties": {
                        "self": {
                          "type": "object",
                          "properties": {
                            "href": {
                              "type": "string",
                              "example": "LINK"
                            }
                          }
                        }
                      }
                    },
                    "_embedded": {
                      "type": "object",
                      "properties": {
                        "leads": {
                          "type": "array",
                          "items": {
                            "type": "object",
                            "properties": {
                              "id": {
                                "type": "integer",
                                "example": 152462,
                                "default": 0
                              },
                              "name": {
                                "type": "string",
                                "example": "Example Lead 1"
                              },
                              "price": {
                                "type": "integer",
                                "example": 15000,
                                "default": 0
                              },
                              "responsible_user_id": {
                                "type": "integer",
                                "example": 8375357,
                                "default": 0
                              },
                              "group_id": {
                                "type": "integer",
                                "example": 0,
                                "default": 0
                              },
                              "status_id": {
                                "type": "integer",
                                "example": 58141807,
                                "default": 0
                              },
                              "pipeline_id": {
                                "type": "integer",
                                "example": 6950551,
                                "default": 0
                              },
                              "loss_reason_id": {},
                              "created_by": {
                                "type": "integer",
                                "example": 8375357,
                                "default": 0
                              },
                              "updated_by": {
                                "type": "integer",
                                "example": 0,
                                "default": 0
                              },
                              "created_at": {
                                "type": "integer",
                                "example": 1686673336,
                                "default": 0
                              },
                              "updated_at": {
                                "type": "integer",
                                "example": 1686747000,
                                "default": 0
                              },
                              "closed_at": {},
                              "closest_task_at": {
                                "type": "integer",
                                "example": 1686850200,
                                "default": 0
                              },
                              "is_deleted": {
                                "type": "boolean",
                                "example": false,
                                "default": true
                              },
                              "custom_fields_values": {
                                "type": "array",
                                "items": {
                                  "type": "object",
                                  "properties": {
                                    "field_id": {
                                      "type": "integer",
                                      "example": 184994,
                                      "default": 0
                                    },
                                    "field_name": {
                                      "type": "string",
                                      "example": "Sale"
                                    },
                                    "field_code": {},
                                    "field_type": {
                                      "type": "string",
                                      "example": "checkbox"
                                    },
                                    "values": {
                                      "type": "array",
                                      "items": {
                                        "type": "object",
                                        "properties": {
                                          "value": {
                                            "type": "boolean",
                                            "example": true,
                                            "default": true
                                          }
                                        }
                                      }
                                    },
                                    "is_computed": {
                                      "type": "boolean",
                                      "example": false,
                                      "default": true
                                    }
                                  }
                                }
                              },
                              "score": {},
                              "account_id": {
                                "type": "integer",
                                "example": 31361463,
                                "default": 0
                              },
                              "labor_cost": {},
                              "is_price_computed": {
                                "type": "boolean",
                                "example": false,
                                "default": true
                              },
                              "source_id": {
                                "type": "integer",
                                "example": 20692839,
                                "default": 0
                              },
                              "is_price_modified_by_robot": {
                                "type": "boolean",
                                "example": true,
                                "default": true
                              },
                              "_links": {
                                "type": "object",
                                "properties": {
                                  "self": {
                                    "type": "object",
                                    "properties": {
                                      "href": {
                                        "type": "string",
                                        "example": "LINK"
                                      }
                                    }
                                  }
                                }
                              },
                              "_embedded": {
                                "type": "object",
                                "properties": {
                                  "tags": {
                                    "type": "array"
                                  },
                                  "catalog_elements": {
                                    "type": "array"
                                  },
                                  "loss_reason": {
                                    "type": "array"
                                  },
                                  "companies": {
                                    "type": "array"
                                  },
                                  "contacts": {
                                    "type": "array"
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
            }
          },
          "204": {
            "description": "204",
            "content": {
              "text/plain": {
                "examples": {
                  "Result": {
                    "value": "No Content"
                  }
                }
              }
            }
          },
          "400": {
            "description": "400",
            "content": {
              "text/plain": {
                "examples": {
                  "Result": {
                    "value": ""
                  }
                }
              }
            }
          },
          "401": {
            "description": "401",
            "content": {
              "application/json": {
                "examples": {
                  "The user is not authorized": {
                    "value": {
                      "title": "Unauthorized",
                      "type": "https://httpstatus.es/401",
                      "status": 401,
                      "detail": "Invalid user name or password"
                    }
                  }
                },
                "schema": {
                  "type": "object",
                  "properties": {
                    "title": {
                      "type": "string",
                      "example": "Unauthorized"
                    },
                    "type": {
                      "type": "string",
                      "example": "https://httpstatus.es/401"
                    },
                    "status": {
                      "type": "integer",
                      "example": 401,
                      "default": 0
                    },
                    "detail": {
                      "type": "string",
                      "example": "Invalid user name or password"
                    }
                  }
                }
              }
            }
          },
          "403": {
            "description": "403",
            "content": {
              "text/plain": {
                "examples": {
                  "Forbidden": {
                    "value": "Forbidden",
                    "summary": "Forbidden"
                  }
                }
              }
            }
          },
          "429": {
            "description": "429",
            "content": {
              "text/plain": {
                "examples": {
                  "Too many requests": {
                    "value": "Too many requests",
                    "summary": "Too many requests"
                  }
                }
              }
            }
          },
          "500": {
            "description": "500",
            "content": {
              "application/json": {
                "examples": {
                  "Result": {
                    "value": "Internal server error"
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
    "headers": [],
    "explorer-enabled": true,
    "proxy-enabled": true
  },
  "x-readme-fauxas": true
}
```