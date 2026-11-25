# 🔄 Autorização de Múltiplos Clientes na API Conta Azul

Este guia mostra como conectar seu app a **vários clientes Conta Azul**, permitindo que cada um autorize seu acesso de forma independente, utilizando o padrão OAuth 2.0.

## ✅ Visão Geral

A Conta Azul usa o padrão OAuth 2.0 com `Authorization Code Flow`.

Cada cliente precisa autorizar individualmente seu app. Após a autorização, você deve armazenar os tokens `access_token` e `refresh_token` de forma segura e associada a cada cliente.

## 🚀 Passo a Passo

### 1. Direcionar o cliente para a tela de autorização

Monte a URL abaixo com os parâmetros adequados:

```
https://login.contaazul.com/#/oauth/authorize?
  response_type=code&
  client_id=SEU_CLIENT_ID&
  redirect_uri=SUA_REDIRECT_URI&
  state=ESTADO&
  scope=openid+profile+aws.cognito.signin.user.admin
```

📌 Essa URL deve ser aberta sempre que um novo cliente quiser conectar sua conta Conta Azul ao seu app.

### 2. Cliente autoriza e recebe o código

Após aceitar, o cliente é redirecionado para sua `redirect_uri` com o `code`:

```
https://SUA_REDIRECT_URI/?code=AUTORIZATION_CODE&state=ESTADO
```

### 3. Trocar o código por tokens

Envie um `POST` para:

```
https://api-v2.contaazul.com/oauth/token
```

**Headers:**

```
Authorization: Basic base64(client_id:client_secret)
Content-Type: application/x-www-form-urlencoded
```

**Body:**

```
client_id=SEU_CLIENT_ID&
client_secret=SEU_CLIENT_SECRET&
grant_type=authorization_code
&code=AUTORIZATION_CODE
&redirect_uri=SUA_REDIRECT_URI
```

A resposta conterá:

```json
{
  "access_token": "ACCESS_TOKEN_GERADO",
  "expires_in": 3600,
  "refresh_token": "REFRESH_TOKEN_GERADO",
  "token_type": "Bearer"
}
```

### 4. Armazenar os tokens por cliente

Você deve salvar os tokens separadamente para cada cliente que autorizar seu app.

**Exemplo de estrutura:**

| Cliente | Access Token | Refresh Token | Expira em |
|  --- | --- | --- | --- |
| Cliente A | ... | ... | ... |
| Cliente B | ... | ... | ... |


### 5. Usar o token nas requisições

```http
GET https://api-v2.contaazul.com/v1/pessoas
Authorization: Bearer ACCESS_TOKEN_DO_CLIENTE
```

### 🔄 Renovação do token

Quando o `access_token` expirar, use o `refresh_token` para gerar um novo:

```http
POST https://api-v2.contaazul.com/oauth/token
Authorization: Basic base64(client_id:client_secret)
Content-Type: application/x-www-form-urlencoded

grant_type=refresh_token
&refresh_token=REFRESH_TOKEN_DO_CLIENTE
```

## 📘 Dica prática

Implemente um botão “Conectar Conta Azul” no seu painel por cliente.
Assim, cada empresa pode autorizar sua conta de forma independente.