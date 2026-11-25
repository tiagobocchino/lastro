---
updatedAt: 2026-06-16T19:53:51.000Z
agentTools:
  projectIndex: https://desenvolvedor.cvcrm.com.br/llms.txt
---

# Como autenticar nas APIs do CV CRM a partir da v3 com Bearer Token

Um guia passo a passo para obter e utilizar o Bearer Token nas requisições do CV CRM.

<br />

> 📘 **Antes de começar**
>
> Esta página é um complemento à [Informações gerais](https://desenvolvedor.cvcrm.com.br/docs/getting-started). Se você ainda não leu, recomendamos começar por lá — ela explica a arquitetura das nossas APIs, os métodos HTTP disponíveis e como funciona o CVIO. Se você já usa APIs na v1 e quer entender as diferenças de autenticação, veja também o guia de [Como autenticar nas APIs do CV CRM com e-mail e token.](https://desenvolvedor.cvcrm.com.br/docs/api-v1).

***

<br />

> 🚧 **Atenção**
>
> **Este tutorial é destinado às APIs que estão na v3 (versão 3).**
>
> Para identificar a versão da API que você precisa utilizar é necessário observar a URL da API como no exemplo abaixo:
>
> * **Cadastrar Comissão da Reserva:** [https://dominiodocliente.cvcrm.com.br/api/**v3**/comercial/reservas/idReserva/comissoes](https://desenvolvedor.cvcrm.com.br/reference/cadastrarcomissoesreserva)  — perceba que no meio da URL existe a versão: **v3**.
>
> ### 👉Para saber como se autenticar nas APIs na versão v1 acesse:
>
> [Como autenticar nas APIs do CV CRM na v1 com E-mail e Token.](https://desenvolvedor.cvcrm.com.br/docs/como-autenticar-apis-cvcrm-email-token)

# 🔑  O que é o Bearer Token e por que a v3 é diferente?

As APIs da v1 do CV CRM utilizam autenticação estática via **e-mail + token permanente** enviados como headers em cada requisição. **As APIs na v3 adotam um modelo diferente**: você faz uma requisição de login com suas credenciais e, em troca, recebe um **token temporário (Bearer Token)** válido por **6 horas**. Esse token é então enviado no header `Authorization` de todas as chamadas subsequentes.

Como identificar se uma API é v3? Observe a versão na URL:

* **v1:** `https://dominiodocliente.cvcrm.com.br/api/`**`v1`**`/comercial/leads` → autenticação por e-mail + token permanente
* **v3:** `https://dominiodocliente.cvcrm.com.br/api/`**`v3`**`/...` → autenticação por Bearer Token (este guia)

***

# 🗂️  Etapa 1: Pré-requisitos — usuário e credenciais

Antes de gerar o Bearer Token, você precisa de um usuário administrativo ativo no CV CRM com as permissões corretas para os endpoints que deseja consumir. O fluxo é o mesmo que na v1:

> ⚠️ **Atenção**
>
> Cada endpoint do CV CRM exige que o perfil do usuário tenha as permissões correspondentes habilitadas. Acessar uma API sem a permissão correta retorna um erro **403 - Forbidden** — o sistema reconhece o usuário, mas nega o acesso ao recurso solicitado.
>
> Antes de começar sua integração, verifique quais permissões são necessárias:
>
> ### 👉 [Permissões dos Endpoints da API CVCRM](https://desenvolvedor.cvcrm.com.br/docs/permissões-dos-endpoints-da-api-cvcrm)

Para criar e configurar perfis de acesso, consulte o guia completo:

> 📘 👉 [Configuração de Perfis de Acesso - Painel do Gestor](https://ajuda.cvcrm.com.br/support/solutions/articles/157000357217-configurac%C3%A3o-de-perfis-de-acesso-painel-do-gestor)

Você vai precisar de três informações para continuar:

* **E-mail** do usuário administrativo
* **Senha** do usuário administrativo
* **Painel** do usuário: `gestor`, `corretor` ou `imobiliaria`

***

# 🌐  Etapa 2: Identificando o domínio correto

Assim como na v1, a URL base das APIs v3 **varia de acordo com o domínio do cliente**. O padrão é:

`https://{{dominiodocliente}}.cvcrm.com.br/api/v3/...`

Substitua `{{dominiodocliente}}` pelo subdomínio da sua empresa. Exemplo:

| **Empresa**         | **URL base (v3)**                        |
| ------------------- | ---------------------------------------- |
| Construtora Exemplo | `https://exemplo.cvcrm.com.br/api/v3/`   |
| Grupo Horizonte     | `https://horizonte.cvcrm.com.br/api/v3/` |

> ⚠️ **Atenção**
>
> Usar o domínio errado é uma das causas mais comuns de erros **404 - Not Found**. Se você não sabe qual é o seu subdomínio, consulte o endereço que você usa para acessar o painel do gestor — ele segue o mesmo padrão.

***

# 🔐  Etapa 3: Obtendo o Bearer Token

Com as credenciais e o domínio em mãos, faça uma requisição POST para o endpoint de autenticação:

### Endpoint de autenticação

**POST** `https://{{dominiodocliente}}.cvcrm.com.br/api/v3/auth/token`

### Body (JSON)

```json
{
  "email": "seu-email@empresa.com.br",
  "senha": "sua-senha",
  "painel": "gestor"
}
```

> 📘 **Valores aceitos para o campo painel**
>
> * `gestor` — Administrador da incorporadora
> * `corretor` — Corretor de imóveis
> * `imobiliaria` — Imobiliária parceira

### Resposta de sucesso (200 OK)

Se as credenciais estiverem corretas, a API retorna um objeto JSON com o token de acesso:

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "Bearer",
  "expires_in": 21600
}
```

O campo `expires_in` indica a validade em segundos — **21600 segundos = 6 horas**. Após esse período, o token expira e você precisará autenticar novamente.

***

# 💻  Etapa 4: Usando o Bearer Token nas requisições

Com o token em mãos, adicione-o ao header `Authorization` de todas as chamadas às APIs v3:

### Formato do header

**Authorization:** Bearer `{seu_access_token}`

> 📘 **Atenção — Bearer com espaço**
>
> O valor do header deve conter a palavra **Bearer** seguida de um espaço e depois o token. Não inclua aspas nem outros caracteres adicionais.

### Exemplo completo de requisição

```http
GET https://{{dominiodocliente}}.cvcrm.com.br/api/v3/...
Content-Type: application/json
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

> 📘 **Diferença em relação à v1**
>
> Na v1, você enviava e-mail e token em headers separados em cada requisição. Na v3, o fluxo é:
>
> * Autentique uma vez com e-mail + senha → receba o Bearer Token
> * Use o Bearer Token em todas as chamadas subsequentes (por até 6 horas)
> * Quando expirar, autentique novamente para obter um novo token

***

# 🚦  Entendendo os erros mais comuns

| **Código** | **Significado**     | **Causa mais provável**                                                                    | **O que fazer**                                                                                            |
| ---------- | ------------------- | ------------------------------------------------------------------------------------------ | ---------------------------------------------------------------------------------------------------------- |
| **400**    | Requisição inválida | Campos obrigatórios ausentes no body (email, senha ou painel) ou painel com valor inválido | Verifique se os três campos estão presentes e se o valor de painel é `gestor`, `corretor` ou `imobiliaria` |
| **401**    | Não autorizado      | Credenciais incorretas ou token Bearer ausente/expirado na requisição                      | Verifique e-mail e senha no login; se o token expirou, autentique novamente                                |
| **403**    | Proibido            | Usuário autenticado, mas sem permissão para o endpoint acessado                            | Revise o perfil de acesso do usuário nas Permissões dos Endpoints                                          |
| **404**    | Não encontrado      | Domínio incorreto na URL ou endpoint inexistente naquele ambiente                          | Confirme o subdomínio correto e revise a URL da requisição                                                 |
| **429**    | Muitas requisições  | Limite de rate limit atingido                                                              | Adicione intervalos entre as requisições — veja mais em Informações gerais                                 |

***

# 🔄  Gerenciando a expiração do token

O Bearer Token tem validade de **6 horas**. Para garantir que sua integração não interrompa o serviço, leve em conta as seguintes boas práticas:

* Armazene o token e o horário de geração **em memória ou em variável de ambiente** — não faça login a cada requisição.
* Implemente lógica de **renovação automática**: ao receber um erro 401, autentique novamente e repita a chamada.
* Considere renovar o token proativamente **antes de expirar** (por exemplo, após 5h30min), especialmente em integrações de longa duração.

***

# 🔍  Monitorando suas requisições com o CVIO

Depois de começar a fazer requisições, o CVIO é a sua melhor ferramenta para acompanhar o que está acontecendo. Ele registra todas as entradas e saídas de informações, mostrando status, data, descrição e outros filtros que ajudam a diagnosticar erros rapidamente.

Acesse o CVIO da sua empresa pelo endereço:

👉  **`https://{{dominiodocliente}}.cvcrm.com.br/cvio`**

*⚠️  As requisições ficam armazenadas por **30 dias**.*

***

# ✅  Checklist: Tudo pronto para integrar?

Antes de avançar para os tutoriais e referências de API, confira se você já tem tudo configurado:

* [ ] Usuário administrativo criado com perfil de acesso adequado
* [ ] E-mail, senha e painel (gestor/corretor/imobiliaria) identificados
* [ ] Domínio correto da incorporadora identificado
* [ ] Bearer Token obtido com sucesso via POST /api/v3/auth/token
* [ ] Requisição de teste realizada com o token (retorno 200)
* [ ] Estratégia de renovação do token implementada (validade de 6 horas)

***

# 🚀  Próximos passos

Agora que seu Bearer Token está configurado, sugerimos continuar a jornada por aqui:

👉  [Referências das APIs](https://desenvolvedor.cvcrm.com.br/reference) — Acesse a documentação completa de todos os endpoints disponíveis, com exemplos de requisição e resposta.

👉  [Os módulos do CV](https://desenvolvedor.cvcrm.com.br/docs/melhores-práticas) — Entenda como o CV CRM está organizado em Prospectar, Vender, Relacionar e Gerenciar, e quais APIs estão disponíveis em cada módulo.

👉  [Gerenciamento de Permissões de APIs por Perfil e Módulo](https://ajuda.cvcrm.com.br/support/solutions/articles/157000358302-gerenciamento-de-permiss%C3%B5es-de-apis-por-perfil-e-m%C3%B3dulo-integrac%C3%B5es-e-api) — Guia completo sobre como configurar permissões para cada tipo de integração.

***

# 🫱🏽‍🫲🏿  Estamos aqui para ajudar!

Se tiver qualquer dúvida durante a configuração, entre em contato com o nosso suporte ou use o chat disponível no CV.

> 👍 Endereço de e-mail do CV CRM: <atendimento@cvcrm.com.br>

Estamos torcendo pelo sucesso da sua integração! 💚