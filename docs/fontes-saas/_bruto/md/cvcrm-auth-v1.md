---
updatedAt: 2026-05-11T17:00:38.000Z
agentTools:
  projectIndex: https://desenvolvedor.cvcrm.com.br/llms.txt
---

# Como autenticar nas APIs do CV CRM na v1 com E-mail e Token

Um guia direto ao ponto para você configurar suas credenciais e fazer sua primeira requisição com sucesso no CV CRM.

<br />

> 📘 Antes de começar
>
> Esta página é um complemento à [Informações gerais](https://desenvolvedor.cvcrm.com.br/docs/getting-started). Se você ainda não leu, recomendamos começar por lá — ela explica a arquitetura das nossas APIs, os métodos HTTP disponíveis e como funciona o CVIO.

***

<br />

> 🚧 **Atenção**
>
> **Este tutorial é destinado às APIs que estão na v1 (versão 1).**
>
> Para identificar a versão da API que você precisa utilizar é necessário observar a URL da API como no exemplo abaixo:
>
> * **Cadastrar Leads:** [https://dominiodocliente.cvcrm.com.br/api/**v1**/comercial/leads](https://desenvolvedor.cvcrm.com.br/reference/postlead-1) — perceba que no meio da URL existe a versão: **v1**.
>
> ### 👉 Para saber como se autenticar nas APIs na versão v3 acesse:
>
> [Como autenticar nas APIs do CV CRM na v3 com Bearer Token](https://desenvolvedor.cvcrm.com.br/update/docs/como-autenticar-nas-apis-do-cv-crm-com-bearer-token)

# 🔑 O que é a API Key e por que ela é obrigatória?

Todas as APIs do CV CRM utilizam autenticação baseada em **e-mail + token**. Esses dois dados funcionam como a sua identidade nas requisições: sem eles configurados corretamente, o sistema não consegue identificar quem está fazendo a chamada e retorna um erro **401 - Unauthorized**.

O token é gerado diretamente no painel do gestor e está vinculado a um usuário administrativo do CV CRM. Por isso, é importante entender desde o início: **o e-mail utilizado deve pertencer ao mesmo ambiente CVCRM onde os dados serão consumidos.**

Por exemplo, se você está integrando com `suaempresa.cvcrm.com.br`, o e-mail do usuário precisa estar cadastrado nesse domínio — e não em outro ambiente ou subdomínio diferente.

***

# 🗂️ Etapa 1: Criando o usuário de acesso

Antes de gerar o token, é necessário ter um usuário administrativo ativo no CV CRM com as permissões adequadas para os endpoints que você vai consumir.

Se você não sabe como cadastrar esse usuário, entre em contato com o administrador do CV CRM da sua empresa ou consulte o endereço que você usa para acessar o painel do gestor — ele segue o mesmo padrão.

> 📘 [Como cadastrar um usuário administrativo - Painel do Gestor](https://ajuda.cvcrm.com.br/support/solutions/articles/157000357185-cadastro-de-usu%C3%A1rios-administrativos-painel-do-gestor)

> ⚠️ **Atenção**
>
> Cada endpoint do CV CRM exige que o perfil do usuário tenha as permissões correspondentes habilitadas. Acessar uma API sem a permissão correta retorna um erro **403 - Forbidden** — o sistema reconhece o usuário, mas nega o acesso ao recurso solicitado.
>
> Antes de começar sua integração, verifique quais permissões são necessárias:
>
> ### 👉 [Permissões dos Endpoints da API CVCRM](https://desenvolvedor.cvcrm.com.br/docs/permissões-dos-endpoints-da-api-cvcrm)

Para entender como criar e configurar perfis de acesso no painel:

> 📘 [Configuração de Perfis de Acesso - Painel do Gestor](https://ajuda.cvcrm.com.br/support/solutions/articles/157000357217-configurac%C3%A3o-de-perfis-de-acesso-painel-do-gestor)

***

# 🔐 Etapa 2: Gerando o token de acesso

Com o usuário criado e as permissões configuradas, é hora de gerar o token. Acesse o cadastro de usuários administrativos no CV CRM, localize o usuário desejado e clique na opção **"Token"**.

Você também pode definir uma **data de vencimento** para o token gerado — recomendamos fazer isso para manter a segurança da sua integração, mas ao chegar na data de vencimento será necessário gerar um novo token para continuar a utilizar as nossas APIs.

> 👍 Veja o passo a passo detalhado: [Como gerar um token - Painel do Gestor](https://ajuda.cvcrm.com.br/support/solutions/articles/157000357205-como-gerar-um-token-painel-do-gestor)

Ao final desta etapa, você terá em mãos dois dados essenciais:

* ✅ **E-mail** do usuário administrativo
* ✅ **Token** gerado no painel

Guarde esses dados com segurança. Você vai precisar deles em todas as requisições.

***

# 🌐 Etapa 3: Identificando o domínio correto

Esse é um ponto crítico que causa muita confusão. A URL base das APIs do CV CRM **varia de acordo com o domínio do cliente**, e não existe uma URL genérica que funcione para todos.

O padrão correto é:

```
https://{{dominiodocliente}}.cvcrm.com.br/api/v1/...
```

Substitua `{{dominiodocliente}}` pelo subdomínio da sua empresa. Por exemplo:

| Empresa             | URL base                                 |
| ------------------- | ---------------------------------------- |
| Construtora Exemplo | `https://exemplo.cvcrm.com.br/api/v1/`   |
| Grupo Horizonte     | `https://horizonte.cvcrm.com.br/api/v1/` |

> ⚠️ **Atenção**
>
> Usar o domínio errado é uma das causas mais comuns de erros **404 - Not Found** no endpoint de autenticação. Certifique-se de que está usando o subdomínio correto da sua incorporadora antes de fazer qualquer requisição.

Se você não sabe qual é o seu subdomínio, entre em contato com o administrador do CV CRM da sua empresa ou consulte o endereço que você usa para acessar o painel do gestor — ele segue o mesmo padrão.

***

# 💻 Etapa 4: Fazendo sua primeira requisição

Com o e-mail, o token e o domínio corretos em mãos, você está pronto para fazer sua primeira chamada. Veja abaixo um exemplo de requisição usando o endpoint de leads — o mais utilizado no portal.

### Exemplo: Consultando um lead (GET)

```http
GET https://{{dominiodocliente}}.cvcrm.com.br/api/v1/comercial/leads
email: seu-email@empresa.com.br
token: seu-token-gerado-no-painel
```

<Callout icon="📘" theme="info">
  O e-mail e o token são enviados como **headers** da requisição, não no body. Verifique se o seu cliente HTTP (Postman, Insomnia, código, etc.) está configurando os headers corretamente.
</Callout>

Se a requisição retornar **200 - OK**, parabéns — sua API Key está configurada e funcionando! 🎉

Você pode explorar agora os endpoints mais utilizados do CV CRM:

* 📄 [GET Lead](https://desenvolvedor.cvcrm.com.br/reference/getlead-1) — Consultar dados de um lead
* 📝 [POST Lead](https://desenvolvedor.cvcrm.com.br/reference/postlead-1) — Cadastrar um novo lead
* 👥 [Leads Corretores](https://desenvolvedor.cvcrm.com.br/reference/leadscorretores-1) — Consultar leads por corretor

***

# 🚦 Entendendo os erros mais comuns

Se algo der errado, a tabela abaixo vai ajudá-lo a identificar rapidamente o que precisa ser ajustado:

| Código  | Significado         | Causa mais provável                                               | O que fazer                                                                                                                                        |
| ------- | ------------------- | ----------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------- |
| **401** | Não autorizado      | E-mail ou token ausentes, incorretos ou expirados                 | Verifique se os headers `email` e `token` estão sendo enviados e se o token ainda é válido                                                         |
| **403** | Proibido            | Usuário autenticado, mas sem permissão para o endpoint            | Revise o perfil de acesso do usuário nas [Permissões dos Endpoints](https://desenvolvedor.cvcrm.com.br/docs/permissões-dos-endpoints-da-api-cvcrm) |
| **404** | Não encontrado      | Domínio incorreto na URL ou endpoint inexistente naquele ambiente | Confirme o subdomínio correto da sua incorporadora e revise a URL da requisição                                                                    |
| **400** | Requisição inválida | Payload com campos obrigatórios ausentes ou formato incorreto     | Revise os parâmetros obrigatórios na referência do endpoint                                                                                        |
| **429** | Muitas requisições  | Limite de rate limit atingido (200 req/min para REST)             | Adicione um intervalo entre as requisições — veja mais em [Informações gerais](https://desenvolvedor.cvcrm.com.br/docs/getting-started)            |

***

# 🔍 Monitorando suas requisições com o CVIO

Depois de começar a fazer requisições, o **CVIO** é a sua melhor ferramenta para acompanhar o que está acontecendo. Ele registra todas as entradas e saídas de informações, mostrando status, data, descrição e outros filtros que ajudam a diagnosticar erros rapidamente.

Acesse o CVIO da sua empresa pelo endereço:

> 👍 `https://{{dominiodocliente}}.cvcrm.com.br/cvio`

⚠️ *As requisições ficam armazenadas por 30 dias.*

***

# ✅ Checklist: Tudo pronto para integrar?

Antes de avançar para os tutoriais e referências de API, confira se você já tem tudo configurado:

* [ ] Usuário administrativo criado com perfil de acesso adequado
* [ ] Token gerado no painel do gestor (com data de vencimento definida)
* [ ] E-mail e token salvos com segurança
* [ ] Domínio correto da incorporadora identificado
* [ ] Primeira requisição realizada com retorno 200

Com tudo isso em ordem, você está pronto para explorar os módulos do CV CRM e começar suas integrações!

***

# 🚀 Próximos passos

Agora que sua API Key está configurada, sugerimos continuar a jornada por aqui:

👉  [Referências das APIs](https://desenvolvedor.cvcrm.com.br/reference) — Acesse a documentação completa de todos os endpoints disponíveis, com exemplos de requisição e resposta.

👉  [Os módulos do CV](https://desenvolvedor.cvcrm.com.br/docs/melhores-práticas) — Entenda como o CV CRM está organizado em Prospectar, Vender, Relacionar e Gerenciar, e quais APIs estão disponíveis em cada módulo.

👉  [Gerenciamento de Permissões de APIs por Perfil e Módulo](https://ajuda.cvcrm.com.br/support/solutions/articles/157000358302-gerenciamento-de-permiss%C3%B5es-de-apis-por-perfil-e-m%C3%B3dulo-integrac%C3%B5es-e-api) — Guia completo sobre como configurar permissões para cada tipo de integração.

***

# 🫱🏽‍🫲🏿 Estamos aqui para ajudar!

Se tiver qualquer dúvida durante a configuração, entre em contato com o nosso suporte ou use o chat disponível no CV.

> 👍 Endereço de e-mail do CV CRM: <atendimento@cvcrm.com.br>

Estamos torcendo pelo sucesso da sua integração! 💚