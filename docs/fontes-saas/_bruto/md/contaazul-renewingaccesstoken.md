# Renovando seu Access Token (Essencial para Acesso Contínuo) 🔑

Realizadas as etapas 1 e 2, agora você precisará compreender como utilizar o **refresh_token.**
O **access_token** é uma credencial temporária, **projetada para expirar após 1 hora**. Para garantir que sua integração continue funcionando sem interrupções e sem precisar passar por todo o processo de autorização novamente, o protocolo OAuth 2.0 oferece um mecanismo de renovação usando o refresh_token.

### **Como realizar?**

Quando seu access_token expirar (após o tempo informado em expires_in — tempo em segundos), você deve renová-lo:

```bash
curl --location 'https://api-v2.contaazul.com/oauth/token' \
--header 'Authorization: Basic BASE64(SEU_CLIENT_ID:SEU_CLIENT_SECRET)' \
--header 'Content-Type: application/x-www-form-urlencoded' \
--data-urlencode 'refresh_token=REFRESH_TOKEN_GERADO' \
--data-urlencode 'grant_type=refresh_token'
```

### Exemplo de resposta

```bash
{
  "access_token": "NOVO_ACCESS_TOKEN",
  "expires_in": 3600,
  "refresh_token": "NOVO_REFRESH_TOKEN",
  "token_type": "Bearer"
}
```

> ⚠️  **Atenção**
Sempre guarde o novo `refresh_token`, pois ele muda após cada renovação.


Com o cURL acima, você observará os parâmetros que informam ao servidor de autorização sobre sua solicitação:

| Parâmetros | Valor | Valor Fixo? | Finalidade | Descrição |
|  --- | --- | --- | --- | --- |
| grant_type | refresh_token | Sim | Indica que você está solicitando um novo access_token usando um refresh_token | - 
 |
| client_id | Disponível nos detalhes da sua integração no Portal do Desenvolvedor | Não | Identificador único do aplicativo | - 
 |
| client_secret | Disponível nos detalhes da sua integração no Portal do Desenvolvedor | Não | Identificador que comprova a identidade do aplicativo | - 
 |
| Authorization | Basic BASE64(client_id:client_secret) | Não | Este é um cabeçalho HTTP necessário. Ele contém seu client_id e client_secret combinados (client_id:client_secret) e codificados em Base64 | Para mais detalhes sobre a codificação em Base64, consulte o guia FAQ desta documentação |
| REFRESH_TOKEN_GERADO | refresh_token obtido na etapa anterior do fluxo OAuth 2.0 | Não | Permite que sua aplicação obtenha um novo access_token após o token original expirar | É crucial que o refresh_token seja exatamente o mesmo recebido na etapa anterior |


## Erros na Renovação

Quando a renovação falha, a resposta é `400` com `error: invalid_grant` e um campo `error_subtype`, que identifica a causa.

```json
{
  "error": "invalid_grant",
  "error_subtype": "access_revoked",
  "error_description": "O acesso desta empresa à sua aplicação foi revogado, seja pela própria empresa, seja pelo parceiro integrador. Os tokens emitidos para essa conexão deixaram de ser válidos e não podem ser renovados. Para voltar a acessar os dados, inicie um novo fluxo de autorização em /authorize e obtenha um novo consentimento da empresa."
}
```

| error_subtype | Causa | O que fazer |
|  --- | --- | --- |
| access_revoked | O acesso à empresa foi revogado — pela própria empresa, pelo suporte da Conta Azul ou pela sua aplicação | Não há reativação automática. Inicie um novo fluxo de autorização e obtenha novo consentimento. |
| invalid_refresh_token | O `refresh_token` não existe ou já foi utilizado | Envie o último `refresh_token` recebido. Se não tiver, inicie um novo fluxo de autorização. |
| invalid_client | O cabeçalho `Authorization: Basic` está malformado e não pôde ser decodificado | Confira a codificação em Base64 de `client_id:client_secret`. |