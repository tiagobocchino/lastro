---
updatedAt: 2025-09-08T22:19:21.000Z
agentTools:
  projectIndex: https://desenvolvedor.cvcrm.com.br/llms.txt
---

# CVDW API

##Uma massa de dados para você chamar de seu.

# 📈 Introdução

O CVDW é um bulk de dados que foi desenvolvido para simplificar o seu acesso aos dados do CV, essa solução disponibiliza APIs que possibilitam integração com diversas plataformas, como Power BI, Google Looker Studio, MySQL e outras. Com ela, é possível gerenciar as tabelas utilizadas e obter informações em tempo real sobre os dados da incorporadora.

Em nossa Referência de API's existe uma categoria exclusiva para o CVDW

<br />

# 💭Dúvidas Frequentes sobre o CVDW

### 🚦É necessário atualizar a base de dados com a carga completa de todas as tabelas a cada atualização?

Após carregar todos os dados na sua base, é possível seguir apenas com atualizações dos registros. Para isso, pode-se utilizar o parâmetro **a\_partir\_data\_referencia**, que retornará apenas os registros criados ou atualizados a partir da data informada. Dessa forma, a primeira carga será completa, e, posteriormente, trabalharemos apenas com atualizações e novos cadastros.

### 🚦O retorno da consulta está exibindo apenas 30 registros por página. Isso é o comportamento esperado?

É possível ajustar o limite para até 500 registros por página utilizando o parâmetro ***registros\_por\_pagina***. No entanto, o padrão é de 30 registros por página.

### 🚦Como não exceder o limite de requisições ?

Sabendo que as APIs do CVDW têm o limite de 20 requisições por minuto, é possível implementar um intervalo entre as requisições para respeitar essa restrição.

Por exemplo:

Ao configurar um intervalo de 3 segundos entre cada requisição, conseguimos realizar exatamente 20 requisições dentro de um minuto, garantindo que o limite estabelecido pela API não seja excedido.

<br />

<br />

# ⚙️Conectando com o Power BI

Conectar uma API web no Power BI é uma tarefa relativamente simples e útil para integrar dados externos diretamente em relatórios e painéis interativos. Vamos dividir o processo em etapas detalhadas:

### 1. Abrir o Power BI Desktop

Inicie o Power BI Desktop.\
No menu superior, clique em "Obter Dado de outra Fonte" e selecione "Web"

![](https://files.readme.io/ffdf8f15a708ed9981b5d7e2d6601a02b3dd8bdb4b9491769565b50dd8e6e711-API_-_Power_BI.gif)

### 2. Configurar a Conexão

No modo avançado, você pode configurar uma solicitação HTTP mais completa:

![](https://files.readme.io/dc9425e2a9ff7a8902a9902378e932fa3bbd9301b3c35e2a419560c8c25dde87-image.png)

### 3. Permissão e Conclusão

Para que a consulta ocorre com sucesso é preciso liberar o uso anônimo, caso não seja liberado irá ocorrer erro na conexão.

<br />

![](https://files.readme.io/42c5de48a150fe826edbb1f30a2247f9331de597764599882e2d6a71dd1114a7-Conexo_final.gif)

Exemplo de erro de conexão devido à ausência de permissão para acesso anônimo:

![](https://files.readme.io/babe4b75ac943f994581bf4cb8084cbee509216714c3359ddcf057ac00451bd0-image.png)

<br />

### 💡Dica

Caso a tela abaixo não apareça, ocorre, pois, há alguma permissão que foi inclusa previamente.

<br />

<Image align="center" src="https://files.readme.io/ca66cba1dd72de36d97aeb629e76a5c24430fc978936a00345e4d422d7f105da-image.png" />

Para ajustar basta ir no Power Query em "Configurações da fonte de dados" e limpar as permissões.

![](https://files.readme.io/48de34c12cd3ba72b6a6a9a3d0ecc2964ffe542ec2b3ddd12c76b67640a046a7-Limpar_Permisses_-_Power_BI.gif)

<br />

# 📽️Conectando o Power BI na pratica.

<Embed url="https://www.youtube.com/watch?v=-POw1T7iqgo" title="Conectando as APIs do CVDW com Power BI" favicon="https://www.youtube.com/favicon.ico" image="https://i.ytimg.com/vi/-POw1T7iqgo/hqdefault.jpg" provider="youtube.com" href="https://www.youtube.com/watch?v=-POw1T7iqgo" typeOfEmbed="youtube" html="%3Ciframe%20class%3D%22embedly-embed%22%20src%3D%22%2F%2Fcdn.embedly.com%2Fwidgets%2Fmedia.html%3Fsrc%3Dhttps%253A%252F%252Fwww.youtube.com%252Fembed%252F-POw1T7iqgo%253Ffeature%253Doembed%26display_name%3DYouTube%26url%3Dhttps%253A%252F%252Fwww.youtube.com%252Fwatch%253Fv%253D-POw1T7iqgo%26image%3Dhttps%253A%252F%252Fi.ytimg.com%252Fvi%252F-POw1T7iqgo%252Fhqdefault.jpg%26type%3Dtext%252Fhtml%26schema%3Dyoutube%22%20width%3D%22854%22%20height%3D%22480%22%20scrolling%3D%22no%22%20title%3D%22YouTube%20embed%22%20frameborder%3D%220%22%20allow%3D%22autoplay%3B%20fullscreen%3B%20encrypted-media%3B%20picture-in-picture%3B%22%20allowfullscreen%3D%22true%22%3E%3C%2Fiframe%3E" />