---
updatedAt: 2025-09-18T21:25:50.000Z
agentTools:
  projectIndex: https://developers.rdstation.com/llms.txt
---

# Limite de requisições da API

<HTMLBlock>{`
<script>
    (function(h,o,t,j,a,r){
        h.hj=h.hj||function(){(h.hj.q=h.hj.q||[]).push(arguments)};
        h._hjSettings={hjid:2958222,hjsv:6};
        a=o.getElementsByTagName('head')[0];
        r=o.createElement('script');r.async=1;
        r.src=t+h._hjSettings.hjid+j+h._hjSettings.hjsv;
        a.appendChild(r);
    })(window,document,'https://static.hotjar.com/c/hotjar-','.js?sv=');
</script>
`}</HTMLBlock>

Para preservar a integridade e a confiabilidade da plataforma, as nossas APIs têm o seguinte limite de taxa (rate limit):

## [Contatos](https://developers.rdstation.com/reference/contatos)

Limite de requisições para atualização de um contato específico

| Limite máximo  | Período  | Método HTTP | Plano                                                            |
| -------------- | -------- | ----------- | ---------------------------------------------------------------- |
| 24 Requisições | 24 horas | PATCH       | [Light, Basic, Pro, Advanced](https://www.rdstation.com/precos/) |

Limite de requisições por conta

| Limite máximo   | Período  | Método HTTP              | Plano                                                  |
| --------------- | -------- | ------------------------ | ------------------------------------------------------ |
| 120 Requisições | 1 Minuto | GET, POST, PATCH, DELETE | [Light, Basic, Pro](https://www.rdstation.com/precos/) |
| 500 Requisições | 1 Minuto | GET, POST, PATCH, DELETE | [Advanced](https://www.rdstation.com/precos/)          |

<br />

***

<br />

## [Criar tag para o Lead](https://developers.rdstation.com/reference/post_platform-contacts-identifier-value-tag)

Limite de requisições por contato/lead

| Limite máximo  | Período  | Método HTTP | Plano                                                            |
| -------------- | -------- | ----------- | ---------------------------------------------------------------- |
| 24 Requisições | 24 horas | POST        | [Light, Basic, Pro, Advanced](https://www.rdstation.com/precos/) |

Limite de requisições por conta

| Limite máximo      | Período | Método HTTP | Plano                                                            |
| ------------------ | ------- | ----------- | ---------------------------------------------------------------- |
| 15.000 Requisições | 1 dia   | POST        | [Light, Basic, Pro, Advanced](https://www.rdstation.com/precos/) |

<br />

***

<br />

<br />

## [Segmentações](https://developers.rdstation.com/reference/segmenta%C3%A7%C3%B5es)

Limite de requisições da lista de segmentações

| Limite máximo   | Período  | Método HTTP | Plano                                                  |
| --------------- | -------- | ----------- | ------------------------------------------------------ |
| 120 Requisições | 1 minuto | GET         | [Light, Basic, Pro](https://www.rdstation.com/precos/) |
| 240 Requisições | 1 minuto | GET         | [Advanced](https://www.rdstation.com/precos/)          |

<br />

***

<br />

## [Funis de Contatos](https://developers.rdstation.com/reference/funis-de-contatos)

Limite de requisições do lead

| Limite máximo  | Período  | Método HTTP | Plano                                                            |
| -------------- | -------- | ----------- | ---------------------------------------------------------------- |
| 24 Requisições | 24 horas | GET, PUT    | [Light, Basic, Pro, Advanced](https://www.rdstation.com/precos/) |

Limite de requisições por conta

| Limite máximo         | Período  | Método HTTP | Plano                                                            |
| --------------------- | -------- | ----------- | ---------------------------------------------------------------- |
| 1.000.000 Requisições | 24 horas | GET, PUT    | [Light, Basic, Pro, Advanced](https://www.rdstation.com/precos/) |

<br />

***

<br />

## [Campos Personalizados](https://developers.rdstation.com/reference/get_platform-contacts-fields)

Limite de requisições por conta

| Limite máximo         | Período  | Método HTTP              | Plano                                                            |
| --------------------- | -------- | ------------------------ | ---------------------------------------------------------------- |
| 1.000.000 Requisições | 24 horas | GET, POST, PATCH, DELETE | [Light, Basic, Pro, Advanced](https://www.rdstation.com/precos/) |

<br />

***

<br />

## [Webhooks](https://developers.rdstation.com/reference/webhooks)

Limite de requisições por conta

| Limite máximo         | Período  | Método HTTP            | Plano                                                            |
| --------------------- | -------- | ---------------------- | ---------------------------------------------------------------- |
| 1.000.000 Requisições | 24 horas | GET, POST, PUT, DELETE | [Light, Basic, Pro, Advanced](https://www.rdstation.com/precos/) |

<br />

***

<br />

## [Eventos](https://developers.rdstation.com/reference/eventos)

Limite de requisições por lead

| Limite máximo   | Período  | Método HTTP | Plano                                                            |
| --------------- | -------- | ----------- | ---------------------------------------------------------------- |
| 120 Requisições | 24 horas | POST        | [Light, Basic, Pro, Advanced](https://www.rdstation.com/precos/) |

Limite de requisições por conta

| Limite máximo   | Período  | Método HTTP | Plano                                                  |
| --------------- | -------- | ----------- | ------------------------------------------------------ |
| 120 Requisições | 1 minuto | POST        | [Light, Basic, Pro](https://www.rdstation.com/precos/) |
| 500 Requisições | 1 minuto | POST        | [Advanced](https://www.rdstation.com/precos/)          |

<br />

***

<br />

## [Análise](https://developers.rdstation.com/reference/estatisticas)

Limite de requisições para consultar estatísticas de e-mail marketing

| Limite máximo  | Período | Método HTTP | Plano                                              |
| -------------- | ------- | ----------- | -------------------------------------------------- |
| 60 Requisições | 1 hora  | GET         | [Pro, Advanced](https://www.rdstation.com/precos/) |

Limite de requisições para consultar estatísticas de e-mail via fluxo de automação

| Limite máximo  | Período | Método HTTP | Plano                                         |
| -------------- | ------- | ----------- | --------------------------------------------- |
| 60 Requisições | 1 hora  | GET         | [Advanced](https://www.rdstation.com/precos/) |

Limite de requisições para consultar estatísticas do funil de vendas

| Limite máximo  | Período | Método HTTP | Plano                                         |
| -------------- | ------- | ----------- | --------------------------------------------- |
| 60 Requisições | 1 hora  | GET         | [Advanced](https://www.rdstation.com/precos/) |

Limite de requisições para consultar estatísticas dos ativos de conversão

| Limite máximo  | Período | Método HTTP | Plano                                         |
| -------------- | ------- | ----------- | --------------------------------------------- |
| 60 Requisições | 1 hora  | GET         | [Advanced](https://www.rdstation.com/precos/) |

<br />

***

<br />

## [Fluxos de automação](https://developers.rdstation.com/reference/get_platform-workflows)

Limite de requisições para [consultar os fluxos de automação](https://developers.rdstation.com/reference/get_platform-workflows).

| Limite máximo  | Período | Método HTTP | Plano                                                            |
| -------------- | ------- | ----------- | ---------------------------------------------------------------- |
| 40 Requisições | 1 hora  | GET         | [Light, Basic, Pro, Advanced](https://www.rdstation.com/precos/) |

Limite de requisições para [consultar os dados de um fluxo de automação a partir de um id](https://developers.rdstation.com/reference/get_platform-workflows-id).

| Limite máximo  | Período | Método HTTP | Plano                                             |
| -------------- | ------- | ----------- | ------------------------------------------------- |
| 1 Requisição   | 1 hora  | GET         | [Light, Basic](https://www.rdstation.com/precos/) |
| 5 Requisições  | 1 hora  | GET         | [Pro](https://www.rdstation.com/precos/)          |
| 15 Requisições | 1 hora  | GET         | [Advanced](https://www.rdstation.com/precos/)     |

Limite de requisições para [inserir leads em um fluxo de automação](https://developers.rdstation.com/reference/post_platform-workflows-id-leads?lng=pt-BR).

| Limite máximo   | Período | Método HTTP | Plano                                             |
| --------------- | ------- | ----------- | ------------------------------------------------- |
| 1 Requisição    | 1 hora  | POST        | [Light, Basic](https://www.rdstation.com/precos/) |
| 10 Requisições  | 1 hora  | POST        | [Pro](https://www.rdstation.com/precos/)          |
| 100 Requisições | 1 hora  | POST        | [Advanced](https://www.rdstation.com/precos/)     |

Limite de requisições para [consultar os leads que iniciaram em um fluxo de automação](https://developers.rdstation.com/reference/get_platform-workflows-id-leads-started).

| Limite máximo  | Período | Método HTTP | Plano                                             |
| -------------- | ------- | ----------- | ------------------------------------------------- |
| 1 Requisição   | 1 hora  | GET         | [Light, Basic](https://www.rdstation.com/precos/) |
| 3 Requisições  | 1 hora  | GET         | [Pro](https://www.rdstation.com/precos/)          |
| 12 Requisições | 1 hora  | GET         | [Advanced](https://www.rdstation.com/precos/)     |

Limite de requisições para [consultar os leads que encerraram em um fluxo de automação](https://developers.rdstation.com/reference/get_platform-workflows-id-leads-left).

| Limite máximo  | Período | Método HTTP | Plano                                             |
| -------------- | ------- | ----------- | ------------------------------------------------- |
| 1 Requisição   | 1 hora  | GET         | [Light, Basic](https://www.rdstation.com/precos/) |
| 3 Requisições  | 1 hora  | GET         | [Pro](https://www.rdstation.com/precos/)          |
| 12 Requisições | 1 hora  | GET         | [Advanced](https://www.rdstation.com/precos/)     |

Limite de requisições para [consultar os leads que atingiram uma ação específica de um fluxo de automação](https://developers.rdstation.com/reference/get_platform-workflows-id-leads-action-action-id).

| Limite máximo  | Período | Método HTTP | Plano                                             |
| -------------- | ------- | ----------- | ------------------------------------------------- |
| 1 Requisição   | 1 hora  | GET         | [Light, Basic](https://www.rdstation.com/precos/) |
| 3 Requisições  | 1 hora  | GET         | [Pro](https://www.rdstation.com/precos/)          |
| 12 Requisições | 1 hora  | GET         | [Advanced](https://www.rdstation.com/precos/)     |

<br />

***

<br />

## [Emails](https://developers.rdstation.com/reference/get_platform-emails)

| Limite máximo  | Período | Método HTTP | Plano                                                            |
| -------------- | ------- | ----------- | ---------------------------------------------------------------- |
| 60 Requisições | 1 hora  | GET         | [Light, Basic, Pro, Advanced](https://www.rdstation.com/precos/) |

<br />

***

<br />

## [Landing Page](https://developers.rdstation.com/reference/get_platform-landing-pages)

| Limite máximo  | Período | Método HTTP | Plano                                                            |
| -------------- | ------- | ----------- | ---------------------------------------------------------------- |
| 60 Requisições | 1 hora  | GET         | [Light, Basic, Pro, Advanced](https://www.rdstation.com/precos/) |

<br />

***

<br />

## [Pop-ups](https://developers.rdstation.com/reference/get_platform-popups)

| Limite máximo  | Período | Método HTTP | Plano                                                            |
| -------------- | ------- | ----------- | ---------------------------------------------------------------- |
| 60 Requisições | 1 hora  | GET         | [Light, Basic, Pro, Advanced](https://www.rdstation.com/precos/) |

<br />

***

<br />

### [Formulários](https://developers.rdstation.com/reference/get_platform-embeddables)

| Limite máximo  | Período | Método HTTP | Plano                                                            |
| -------------- | ------- | ----------- | ---------------------------------------------------------------- |
| 60 Requisições | 1 hora  | GET         | [Light, Basic, Pro, Advanced](https://www.rdstation.com/precos/) |

***

### Erro: 429 "Too Many Requests"

Ao projetar seu aplicativo pense em controlar o fluxo de solicitações de API para uma melhor produtividade sem exceder o máximo de requisições permitido que foram apresentados acima, caso contrário, você receberá um erro  `429 - Too Many Requests`.

##### Exemplo

```
{
  "error": "'lead_limiter' rate limit exceeded for 86400 second(s) period for key 'lead@example.org'",
  "max": 24,
  "usage": 25,
  "remaining_time": 43067
}
```

**error**: Detalhes sobre a causa que excedeu o limite de requisições permitido\
**max**: Número máximo de requisições permitido\
**usage**: Número máximo de requisições alcançado\
**remaining\_time**: Período restante para envio de requisições (milissegundos)

### Erro: 414 "URI Too Long"

Ao projetar seu aplicativo pense em controlar o tamanho da URL para não passar do limite de 8kb. Caso a URL passe do limite de 8kb de tamanho, você receberá um erro  `414 URI Too Long`.

> 👍 Dicas rápidas
>
> * Assuma que sua aplicação irá competir por cotas, taxas e recursos de concorrência com outros aplicativos, defina limites de uso conservadores.
> * Evite fazer chamadas de API simultâneas se o seu caso de uso não se beneficiar.
> * Sempre que possível utilize requisições assíncronas para as APIs, assim você poderá lidar melhor com os limites e erros.