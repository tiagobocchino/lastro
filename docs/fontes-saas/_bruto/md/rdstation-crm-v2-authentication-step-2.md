---
updatedAt: 2025-10-22T17:16:19.000Z
agentTools:
  projectIndex: https://developers.rdstation.com/llms.txt
---

# Passo 2: Gerar código de autorização

# Como gerar o código de autorização

No passo anterior, você criou o aplicativo na RD Station App Store e obteve as credenciais. Neste passo, vamos utilizar as credenciais `client_id` e `redirect_uri` para obter o `code`.

O objetivo dessa etapa é autorizar o aplicativo (criado no [passo 1](crm-v2-authentication-step-1)) a se conectar com a conta desejada do RD Station CRM.

# Compondo a URL de autorização

Você deve substituir o parâmetro `client_id` da URL de autorização indicada abaixo, pelas credenciais obtidas no passo anterior.

O parâmetro `redirect_uri` deve ser substituído pela URL de callback cadastrada no aplicativo criado no [passo 1](crm-v2-authentication-step-1).

```text URL de autorização
https://accounts.rdstation.com/oauth/authorize?response_type=code&client_id=YOUR_CLIENT_ID&redirect_uri=YOUR_REDIRECT_URI
```

## Gerador de URL de autorização

<AuthenticationUrlGenerator />

> ℹ️
>
> Certifique-se de que a sua URL de callback foi inserida por completo, exatamente como foi [cadastrada no aplicativo](crm-v2-authentication-step-1).

## Exemplo de URL de autorização

Veja um exemplo de como ficaria a URL de autorização após substituir o `client_id` e `redirect_uri`  pelas credenciais geradas por um aplicativo.

```text Exemplo de URL de autorização completa
https://accounts.rdstation.com/oauth/authorize?response_type=code&client_id=68956445-3421-4a0f-a0dd-3142a97621f4&redirect_uri=https://www.rdstation.com/contato
```

# Autorizando o aplicativo

Após gerar a URL de autorização, é necessário acessá-la para obter o `code`.

Ao acessar/ser redirecionado para a URL de autorização, o usuário poderá selecionar qual conta da RD Station deseja integrar e será exibida a caixa de permissões para confirmar a autorização.

Se o redirecionamento for feito corretamente, o `code` será retornado na URL de callback fornecida no parâmetro `redirect_uri` com a estrutura similar:

```
https://yourapp.org/auth/callback?code={code}
```

Pode realizar essa etapa acessando a URL de autorização pela barra de endereço do seu navegador para ser redirecionado para a sua conta da RD Station, autorizar a conexão e obter o `code`.