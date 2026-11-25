# Trocar o código recebido por um access_token 🔑

### 🔄 Trocar o Código de Autorização por Tokens

Agora que você realizou a Etapa 1,  onde o cliente Conta Azul concede permissão à sua aplicação e você recebe um código de autorização, a Etapa 2 consiste em **trocar esse código por um token de acesso (`access_token`)**. É esse `access_token` que sua aplicação usará para acessar os recursos protegidos do cliente Conta Azul por meio da API.

### **Como realizar?**

Para esta chamada, é necessário incluir no cabeçalho da requisição a autorização do tipo **Basic**, utilizando seu `SEU_CLIENT_ID` e `SEU_CLIENT_SECRET` codificados em Base64.

Você pode gerar o valor em Base64 clicando aqui e informando o conteúdo no seguinte formato: `SEU_CLIENT_ID:SEU_CLIENT_SECRET`

```bash
curl --location 'https://api-v2.contaazul.com/oauth/token' \
--header 'Authorization: Basic BASE64(SEU_CLIENT_ID:SEU_CLIENT_SECRET)' \
--header 'Content-Type: application/x-www-form-urlencoded' \
--data-urlencode 'code=CODIGO_AUTORIZACAO' \
--data-urlencode 'grant_type=authorization_code' \
--data-urlencode 'redirect_uri=SUA_URL_REDIRECIONAMENTO'
```

### Exemplo de resposta

```bash
{
  "access_token": "ACCESS_TOKEN_GERADO",
  "expires_in": 3600,
  "refresh_token": "REFRESH_TOKEN_GERADO",
  "token_type": "Bearer"
}
```

### Entendendo os tokens:

- **`access_token`**: usado para autenticar chamadas futuras à API.
- **`refresh_token`**: usado para renovar o `access_token` após a expiração.


> **Atenção**
É necessário salvar cada um desses tokens de forma segura, pois eles são importantes para os próximos passos do fluxo OAuth 2.0. Abaixo está algumas informações importantes:


| Token | Validade | Finalidade |
|  --- | --- | --- |
| access_token | 3600 segundos (1 hora) | Este token é a credencial da sua integração para fazer requisições autenticadas e autorizadas aos recursos da API |
| refresh_token | até 2 anos ou até a próxima renovação do access_token (a cada renovação, um novo refresh_token é emitido e o anterior deixa de valer) | Este token é de uso mais prolongado e seguro. Usado para renovar o access_token quando ele expira. Deve ser armazenado de forma segura. Deve-se armazenar um novo refresh_token em toda requisição de renovação do access_token |