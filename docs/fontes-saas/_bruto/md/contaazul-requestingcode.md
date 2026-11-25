# Solicitando um Código de Autorização

## 🔄 Solicitar um Código de Autorização

A solicitação do código de autorização é a primeira etapa crucial no processo de autorização do **OAuth 2.0**. Neste ponto, você será direcionado para o servidor de autorização da Conta Azul (`login.contaazul.com`). Isso permite que um cliente Conta Azul vincule sua conta ERP à sua aplicação, concedendo permissão para que seu aplicativo acesse os dados necessários.

**Nosso Endpoint de requisição do código de autorização:** ➡️
`https://login.contaazul.com/#/oauth/authorize`

### **Como realizar?**

Ao criar uma aplicação de **produção**, fornecemos uma URL pronta para ser utilizada no navegador e iniciar o processo de autorização.

Basta copiar a URL gerada e colá-la no navegador. Em seguida, você será direcionado para a tela de autorização.

Nessa etapa, utilize uma conta válida do ERP — não a do Portal do Desenvolvedor.

Veja abaixo como a URL de autorização é estruturada:

`https://login.contaazul.com/#/oauth/authorize?response_type=code&client_id=SEU_CLIENT_ID&redirect_uri=SUA_URL_REDIRECIONAMENTO&state=ESTADO&scope=openid+profile+aws.cognito.signin.user.admin`

### 💡 Dicas

- Para a criação de aplicação de Desenvolvimento, utilizamos como URL de testes **https://www.contaazul.com**. Para o processo de Produção, siga os passos acima indicados pois será necessário que você indique a sua URL de redirecionamento para capturar as informações necessárias para o processo de Autenticação.
- A criação de aplicação de Desenvolvimento, fornecerá dados ficticios para apoio durante o desenvolvimento.


### **Paramêtros obrigatórios**

| Parâmetro | Valor | Valor Fixo? | Finalidade | Detalhes |
|  --- | --- | --- | --- | --- |
| response_type | code | Sim | Informa ao servidor que está buscando um código de autorização | - 
 |
| client_id | Obtido no Gerenciador de Aplicações da Conta Azul. | Não | Identificador único do aplicativo | - 
 |
| redirect_uri | Disponível nos detalhes da sua integração no Portal do Desenvolvedor | Não | Esta é a URL que o servidor deve redirecionar o navegador após a autorização | É crucial que esta URL seja **exatamente igual** à URL informada na integração pelo Portal do Desenvolvedor, ao contrário resultará em um erro de redirecionamento |
| state | **Valor aleatório** e único para cada solicitação de autorização | Não | Quando o servidor redireciona de volta para sua redirect_url, ele inclui o mesmo valor state, pois os dois precisam ser idênticos | Proteção contra CSRF (Cross-Site Request Forgery) e ajuda na manutenção de contexto caso exista várias solicitações pendentes |
| scope | openid+profile+aws.cognito.signin.user.admin | Sim | Define as permissões que seu aplicativo está solicitando | No Conta Azul, seu aplicativo terá a permissão de administrador |


Após a autorização do usuário, haverá um redirecionamento automático para a URL configurada, contendo um **code**:

`https://SUA_URL_REDIRECIONAMENTO?code=CODIGO_AUTORIZACAO&state=ESTADO`

Exemplo de URL com o code: