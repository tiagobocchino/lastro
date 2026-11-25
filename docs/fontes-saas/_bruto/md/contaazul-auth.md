# Autenticação na API da Conta Azul

Este guia detalha o processo de autenticação utilizando o fluxo **Authorization Code** do protocolo OAuth 2.0 para integração com a API da Conta Azul, permitindo acesso seguro aos recursos disponíveis.

## Visão Geral do Fluxo OAuth 2.0

A autenticação é o primeiro passo para garantir acesso seguro e autorizado aos recursos da API Conta Azul.
O processo segue o padrão OAuth 2.0, utilizando o fluxo Authorization Code, o mais seguro e recomendado para aplicações que acessam dados em nome de um usuário.

Este guia descreve, de forma detalhada, cada etapa necessária para autenticar sua aplicação, desde a solicitação do código de autorização até o uso do token de acesso.

Ao final, você será capaz de conectar sua aplicação à API da Conta Azul com segurança e boas práticas de integração.

### 🎥 App de DESENVOLVIMENTO

Assista ao vídeo abaixo para acompanhar, de forma prática, o fluxo de autenticação OAuth 2.0 utilizando um app de **DESENVOLVIMENTO**.

### 🎥 App de PRODUÇÃO

Assista ao vídeo abaixo para acompanhar, de forma prática, o fluxo de criação de credenciais e autenticação OAuth 2.0 utilizando um app de **PRODUÇÃO**.

### **Etapas do processo de autenticação**

A autenticação via OAuth 2.0 é composta por 4 etapas principais:

1. **Solicitar o código de autorização**
  * Inicia o fluxo de autenticação redirecionando o usuário para o login seguro.
2. **Trocar o código pelo token de acesso (access_token)**
  * Após o login autorizado, sua aplicação recebe um código que será trocado por tokens de acesso.
3. **Renovar o token de acesso (refresh_token)**
  * Quando o token expirar, ele deve ser renovado para continuar acessando os recursos da API.
4. **Utilizar o token de acesso nas requisições à API**
  * O token é enviado no cabeçalho de autenticação (Authorization: Bearer) em todas as chamadas.


### O que você vai aprender neste guia

Entender o fluxo completo de autenticação OAuth 2.0.

Configurar corretamente sua aplicação no Portal do Desenvolvedor.

Executar as chamadas de autenticação e renovação de token.

Garantir acesso seguro e contínuo aos endpoints da API Conta Azul.