---
updatedAt: 2026-11-23T13:25:47.000Z
agentTools:
  projectIndex: https://developers.rdstation.com/llms.txt
---

# Introdução

Te damos boas-vindas à documentação da API v2 do RD Station CRM, projetada para ser poderosa, previsível e fácil de usar. Com ela, você pode criar integrações robustas para estender e conectar o RD Station CRM a outras ferramentas.

A API (Application Programming Interface ou Interface de Programação de Aplicativos) é um padrão de programação, com conjuntos de instruções cuja finalidade é desenvolver a integração entre diferentes plataformas de softwares, como o RD Station CRM e outra ferramenta que você utilize.

Todas as nossas APIs são organizadas em torno da arquitetura REST e são acessadas via protocolo HTTPS. Então, se você já interagiu com uma API [RESTful](https://restfulapi.net/), muitos dos conceitos serão familiares.

<Recipe slug="primeiro-uso-da-api-v2-do-rd-station-crm" title="Sua primeira chamada para a API v2 do RD Station CRM" />

# Requisitos para começar

* Possuir uma conta do RD Station CRM. Se ainda não tiver, [crie uma aqui](https://crm.rdstation.com/signup).
* Ter uma conta do plano Basic, Pro ou Advanced do RD Station CRM.
* Um pouco de conhecimento de programação.

> 📘 Dica
>
> O [Modo Desenvolvedor](https://ajuda.rdstation.com/s/article/Ativar-modo-Desenvolvedor) pode ser ativado, para facilitar a coleta do ID dos registros.

# Entidades

As nomenclaturas das entidades utilizadas na API deverão seguir o padrão conforme a tabela a seguir:

| RD Station CRM                | API                  |
| :---------------------------- | :------------------- |
| Negociação                    | deal                 |
| Empresa                       | organization         |
| Contato                       | contact              |
| Lead                          | lead                 |
| Tarefa                        | task                 |
| Reunião                       | meeting              |
| Disponibilidade para reuniões | meeting availability |
| Produto                       | product              |
| Campanha                      | campaign             |
| Motivo de perda               | lost reason          |
| Fonte                         | source               |
| Segmento                      | segment              |
| Campo personalizado           | custom field         |
| Usuário                       | user                 |

# Domínio base

Todas as requisições para a API v2 do RD Station CRM devem usar a seguinte URL base:

```
https://api.rd.services/crm/v2/
```

Exemplo:

Para listar os contatos, deve-se usar o endereço completo: `GET https://api.rd.services/crm/v2/contacts`

# Segurança

A API está disponível apenas no protocolo HTTPS com criptografia TLS versão 1.3.

# Formatos de dados

## Payload

O dados da API v2 são sempre trafegados usando JSON.

Assim, o `Content-Type` sempre será `application/json`.

## Data e hora

As propriedades de data e hora (`DateTime`) seguem o padrão [ISO 8601](https://en.wikipedia.org/wiki/ISO_8601) com timezone padrão sendo o UTC.

# Autenticação

Todas as requisições para a API v2 devem ser autenticadas.

Para mais detalhes, leia sobre a [autenticação](crm-v2-authentication).

# Limite de requisições

Para garantir a estabilidade da plataforma para todos os usuários, a API impõe limites no número de requisições que podem ser feitas em um determinado período.

Se você exceder esse limite, receberá uma resposta com o código de status `429 Too Many Requests`. A resposta incluirá um cabeçalho `Retry-After` indicando quantos segundos você deve esperar antes de fazer uma nova tentativa.

| Plano                | Limite máximo              |
| :------------------- | :------------------------- |
| Basic, Pro, Advanced | 120 requisições por minuto |

Saiba mais sobre os [planos do RD Station CRM](https://www.rdstation.com/planos/crm/).

# Status de retorno

A API v2 utiliza códigos de status HTTP padrão para indicar o sucesso ou a falha de uma requisição.

| Código                      | Significado         | Descrição                                                                                                                                |
| :-------------------------- | :------------------ | :--------------------------------------------------------------------------------------------------------------------------------------- |
| `200 OK`                    | Sucesso             | A requisição foi bem-sucedida.                                                                                                           |
| `201 Created`               | Criado              | O recurso foi criado com sucesso. Exemplo: em respostas do método `POST`.                                                                |
| `204 No Content`            | Sem conteúdo        | A requisição foi bem-sucedida mas não há conteúdo para retornar. Exemplo: em respostas do método `DELETE`.                               |
| `400 Bad Request`           | Requisição inválida | A requisição está malformada e não consegue ser processada. Exemplo: o corpo JSON está inválido ou tem parâmetros obrigatórios ausentes. |
| `401 Unauthorized`          | Não autorizado      | O token da API está ausente ou inválido.                                                                                                 |
| `403 Forbidden`             | Proibido            | O token não tem permissão para acessar o recurso solicitado.                                                                             |
| `404 Not Found`             | Não encontrado      | O recurso solicitado não existe.                                                                                                         |
| `422 Unprocessable Entity`  | Entidade inválida   | A entidade não pode ser processada.                                                                                                      |
| `429 Too Many Requests`     | Muitas requisições  | O limite de requisições foi excedido.                                                                                                    |
| `500 Internal Server Error` | Erro interno        | Erro interno ou inesperado no servidor.                                                                                                  |

# Estrutura do playload

A estrutura base de payload a ser enviados para a API será sempre a seguinte:

```json
{
  "data": {} /* ou [] */
}
```

Sendo o retorno das requisições em caso de sucesso:

```json
{
  "data": {}, /* ou [] */
  "links": {}
}
```

E em caso de erros:

```json
{
  "errors": []
}
```

| Propriedade | Tipo                     | Descrição                                                                                                                    |
| :---------- | :----------------------- | :--------------------------------------------------------------------------------------------------------------------------- |
| `data`      | `Object`/`Array<Object>` | Dados a serem enviados ou retornados nos end-points.                                                                         |
| `links`     | `Object`                 | Dados extras como a navegação de listagens. Nem todos os end-points utilizam essa propriedade.                               |
| `errors`    | `Array<Object>`          | Em caso de erro, essa propriedade retorna a lista de problemas. Essa propriedade nunca é retornada em conjunto com a `data`. |

# Tratamento de erros

E em caso de erros, cada um será listado na propriedade `errors` e também será informado pelo status HTTP seguindo os [status de retorno](#status-de-retorno).

```json
{
  "errors": []
}
```

# Paginação

End-points que retornam listas de recursos (como `GET /contacts` ou `GET /deals`) utilizam paginação para gerenciar grandes volumes de dados.

Use os parâmetros de consulta `page[number]` e `page[size]` para navegar pelos resultados.
Os parâmetros são passados como query params (URL) através do argumento `page`. Exemplo:

```
https://api.rd.services/crm/v2/contacts?page[number]=2&page[size]=10
```

| Propriedade    | Tipo      | Descrição                                                                       |
| :------------- | :-------- | :------------------------------------------------------------------------------ |
| `page[number]` | `Integer` | Indica a página a ser retornada. Padrão: `1`.                                   |
| `page[size]`   | `Integer` | Indica a quantidade de objetos a serem retornados em cada página. Padrão: `20`. |

Para facilitar, as requisições de listagens informam os links de navegação de páginas dentro da propriedade `links`. Dessa forma, pode-se simplesmente navegar por esses simples sem precisar recriar toda a URL.

Exemplo de uma requisição para `https://api.rd.services/crm/v2/contacts?filter=name:Walter&sort[created_at]=asc&page[number]=5&page[size]=10` que tem 85 registros:

```json
{
  "data": [
    /* { ... }, ... */
  ],
  "links": {
    "first": "https://api.rd.services/crm/v2/contacts?filter=name:Walter&sort[created_at]=asc&page[number]=1&page[size]=10",
    "prev": "https://api.rd.services/crm/v2/contacts?filter=name:Walter&sort[created_at]=asc&page[number]=4&page[size]=10",
    "self": "https://api.rd.services/crm/v2/contacts?filter=name:Walter&sort[created_at]=asc&page[number]=5&page[size]=10",
    "next": "https://api.rd.services/crm/v2/contacts?filter=name:Walter&sort[created_at]=asc&page[number]=6&page[size]=10",
    "last": "https://api.rd.services/crm/v2/contacts?filter=name:Walter&sort[created_at]=asc&page[number]=9&page[size]=10"
  }
}
```

Os `links` de uma requisição de listagem já terão os parâmetros `filter`, `sort` e `page` reproduzidos para seguir a navegação de páginas.

# Ordenação

End-points que retornam listas de registros podem modificar a ordenação dos dados baseado em algumas das propriedades da entidade. Mas atenção, nem todas as propriedades podem ser usadas para ordenação. Para mais detalhes acesse a página da documentação referente ao recurso para identificar as possíveis propriedades de ordenação.

A ordenação é feita através do parâmetro `sort[propriedade]=direção` onde "propriedade" refere-se ao campo de ordenação e a "direção" pode ser `asc` para ascendente e `desc` para descendente.

Exemplo:

```
https://api.rd.services/crm/v2/contacts?sort[created_at]=asc
```

O exemplo acima retorna a lista de contatos ordenados de forma decrescente pela data de criação, que retorna a lista de contatos com os criados mais recentemente primeiro.

Ordenar por uma propriedade que não aceita ordenação, usar uma direção diferente de `asc` ou `desc`, ou passar mais propriedades que o permitido responde `400 Bad Request` com `type: INVALID_PARAMETER`. O campo `source.parameter` indica o parâmetro: `sort` para propriedade inválida ou excesso de propriedades, `sort[propriedade]` para direção inválida.

Os `links` de uma requisição de listagem já terão os parâmetros `filter`, `sort` e `page` reproduzidos para seguir a navegação de páginas.

# Filtro

Saiba mais sobre como filtrar os dados [aqui](crm-v2-rdql-filtering).

Os `links` de uma requisição de listagem já terão os parâmetros `filter`, `sort` e `page` reproduzidos para seguir a navegação de páginas.

# Bases legais

As principais Leis de Proteção de Dados, como a LGPD (Brasil) e o GDPR (União Europeia), estabelecem que, para que qualquer pessoa, física ou jurídica, possa realizar qualquer operação com um dado pessoal − seja coletar, transmitir ou processar −, é necessário possuir uma base legal presente na LGPD, ou seja, uma hipótese da lei que justifique o tratamento desses dados.

Lei mais sobre [como utilizar as bases legais](crm-v2-legal-bases).

# Notas sobre a listagem

Ao utilizar o método listar das entidades de negociação, empresa, contato e lead é possível listar apenas os 10 mil primeiros registros do filtro especificado.