---
updatedAt: 2026-11-16T11:14:29.000Z
agentTools:
  projectIndex: https://developers.kommo.com/llms.txt
---

# Long-lived token

When you need to develop an integration that will only be used in your account, there’s no need to go through the difficult process of getting an authorization code through the redirect mechanism. Long-lived tokens do not have a `refresh_token`: you don't have to exchange them or write logic to monitor the relevance of the tokens. Instead, you can receive a long-lived token. In this case, the integration will work with your rights, i.e. administrator rights (*only a user with account administrator rights can create it in the account*).

## What to start with

Start by creating a [private integration](https://kommo.readme.io/docs/private-integration#the-development-of-a-private-integration).

<Image align="center" alt="You don't have to fill in the **Redirect URL** or **Access revoked notification web hook**." border={true} caption="You don't have to fill in the **Redirect URL** or **Access revoked notification web hook**." src="https://files.readme.io/574331be54348c44a9a5242f0ce2bccf358a7decb9d51851a1e68212ae3bd5e2-One_click_EN.png" width="700px" />

## Generate long-lived token

<Image align="center" alt="To create a long-lived token, open the **Keys and scopes** tab, click the **Generate long-lived token** button, select the expiration date of the token and copy the token." border={true} caption="To create a long-lived token, open the **Keys and scopes** tab, click the **Generate long-lived token** button, select the expiration date of the token and copy the token." src="https://files.readme.io/6ba314ef148c76b39f7923f6c7c42a8a139a4852122df3a2ce0d69cab2746652-_.png" width="700px" />

<Image align="center" alt="The user selects the expirations date of the token and it is valid from 1 day to 5 years." border={true} caption="The user selects the expirations date of the token and it is valid from 1 day to 5 years." src="https://files.readme.io/8f0cc4dc91e01f0b5ac755fa0854b62c010f11c904af4f2ce295f749012f35f9-Screenshot_1.png" width="700px" />

> 🚧 Important!
>
> * Once a token has been generated, make sure to save it. You won’t be able to access it again
> * Such tokens are suitable only for private integrations
> * It is less safe to use this kind of authorization. Be aware that if your long-lived token is compromised, your account is in danger.

You will use the token to make requests to your Kommo account via a private integration.

## Use the token

An example of a token - `eyJ0eXAiOiJKV1QiLCJhbGiOiJSUz…JrIa3zT0Q`

Paste the token into the body of the request to get all the leads of your account.

```shell
curl --request GET \
     --url https://$PASTE_YOUR_SUBDOMAIN_HERE$.kommo.com/api/v4/leads \
     --header 'accept: application/json' \
     --header 'authorization: Bearer $PASTE_YOUR_TOKEN_HERE$'
```
```python
import requests

SUBDOMAIN = ''
API_KEY = ''


CREATE_LEAD_URL = f'https://{SUBDOMAIN}.kommo.com/api/v4/leads'

body = {
    'name' : "Example Lead 1",
    "price": 1000,
}

headers = {
    'Authorization' : f'Bearer {API_KEY}',
    'Content-Type': 'application/json'
}

requests.post(CREATE_LEAD_URL, json=body, headers=headers)
```
```javascript
const options = {
  method: 'GET',
  headers: {
    accept: 'application/json',
    authorization: 'Bearer $PASTE_YOUR_TOKEN_HERE$'
  }
};

subdomain = 'PASTE_YOUR_SUBDOMAIN_HERE'

fetch(`https://${subdomain}.kommo.com/api/v4/leads`, options)
  .then(response => response.json())
  .then(response => console.log(response))
  .catch(err => console.error(err));
```
```php
<?php
require_once('vendor/autoload.php');

$client = new \GuzzleHttp\Client();

$response = $client->request('GET', 'https://$PASTE_YOUR_SUBDOMAIN_HERE$.kommo.com/api/v4/leads', [
  'headers' => [
    'accept' => 'text/plain',
    'authorization' => 'Bearer $PASTE_YOUR_TOKEN_HERE$',
  ],
]);

echo $response->getBody();

```

You can practice using tokens and sending requests in the [API References section](https://kommo.readme.io/reference/getting-started-with-your-api).

## Revoke access

In the **Authorization** tab, you can see that long-lived tokens have not only an issue date, but also an expiration date, and you can always revoke access by clicking the **Revoke access** button.

<Image align="center" width="700px" src="https://files.readme.io/dacb34d2be25ec940a4b74833784d636da806ba91e6232d0a18316e5a42d43e0-609c94d-bfc727fb-5b3b-42e6-9bea-d951a1e2e89e.png" />