---
updatedAt: 2026-04-27T21:06:02.000Z
agentTools:
  projectIndex: https://desenvolvedor.cvcrm.com.br/llms.txt
---

# Monte dashboards com o CVCRM!

Consuma as APIs analíticas do CVCRM para construir um _data mart_ voltado a funil comercial, desempenho de mídia, reservas, workflow e contratos.

# ✨Por que essa integração é importante

A maturidade comercial e operacional do mercado imobiliário depende de dados confiáveis. Ao centralizar extrações analíticas do CVCRM em um ambiente de BI, a incorporadora ganha visibilidade sobre funil, estoque, gargalos e desempenho. Adotando essa rotina, será possível tomar decisões mais estratégicas e definir próximos passos com mais segurança baseados em dados reais e atuais.

# 👍Dor que resolve

Além de entregar uma visão completa do funil de vendas, é importante destacar algumas dores que serão solucionadas ao utilizar as integrações do CVCRM para construir um BI:

* Dependência de exportações manuais.
* Divergência de números entre áreas correlatas ou não.
* Dificuldade de provar o ROI de uma determinada mídia.

# 🎯Resultados esperados

Os resultados não seguem uma receita de bolo, cada BI contará uma história e entregará insights diferentes, tudo de acordo com a maneira que a incorporadora utilizará as APIs do CVCRM e como construirá seu próprio dashboard. Pensando num cenário onde tiramos proveito de tudo o que o CVCRM oferece, podemos citar:

* Dashboards executivos consistentes.
* Leitura clara de gargalos.
* Melhor gestão de mídia e comercial.
* Visão integrada entre leads, reservas e contratos.

# 📌Quando usar

Utilize esse mecanismo quando precisar entregar dados para diferentes áreas com base nas informações presentes no CVCRM. Para isso, pode-se utilizar ferramentas como:

* Power BI
* Looker Studio
* Tableau

<br />

<Callout icon="👍">
  ## Acompanhe o passo a passo para a conexão das APIs do CVCRM com o Power BI: [Conectando com o Power BI](https://desenvolvedor.cvcrm.com.br/docs/usu%C3%A1rio-de-acesso#%EF%B8%8Fconectando-com-o-power-bi) 
</Callout>

# 👉APIs do CVCRM utilizadas neste exemplo

* 🟢[GET Leads](https://desenvolvedor.cvcrm.com.br/reference/leadscorretores-1)
* 🟢[GET Interações dos leads](https://desenvolvedor.cvcrm.com.br/reference/leadsinteracoes-1)
* 🟢[GET Unidades](https://desenvolvedor.cvcrm.com.br/reference/unidades-5)
* 🟢[GET Reservas](https://desenvolvedor.cvcrm.com.br/reference/reservas-4)
* 🟢[GET Workflow das reservas](https://desenvolvedor.cvcrm.com.br/reference/reservasworkflowtempo)
* 🟢[GET Contratos](https://desenvolvedor.cvcrm.com.br/reference/reservascontratos)

<br />

# ⚙️Passo a passo

## Estruture o modelo analítico

Para iniciar, identifique quais informações serão necessárias para construir o seu dashboard. Para este exemplo vamos utilizar as seguintes tabelas:

* 🟢 fato\_leads
* 🟢 fato\_interacoes
* 🟢 fato\_reservas
* 🟢 fato\_contratos\_reserva
* 🟢 fato\_workflow\_reserva
* 🟢 dim\_unidades
* 🟢 dim\_empreendimento
* 🟢 dim\_origem
* 🟢 dim\_conversao

## Extraia os dados por recorte incremental

Para relatórios de grande volume (nosso caso), é essencial desenvolver o recorte incremental para atualizar somente os novos dados ou que foram atualizados durante um período de tempo pré-definido.

<Callout icon="💡" theme="default">
  A atualização incremental otimiza grandes bases de dados ao processar apenas informações novas ou alteradas, economizando tempo e recursos.
</Callout>

<br />

> 📘 Exemplo:
>
> * **curl --request GET**
> * **URL** '<https://SEUDOMINIO.cvcrm.com.br/api/v1/cvdw/unidades?a_partir_data_referencia=2026-01-01&ate_data_referencia=2026-01-31&pagina=1&quantidade=100>'
> * **Header Authorization:** Bearer 'SEU\_TOKEN'

## Normalize e carregue no ambiente analítico

Padronize nomes, datas, chaves de empreendimento e status para facilitar o consumo e a leitura das suas equipes.

## 🥳 Publique os dashboards 🥳

<br />

# 📈Dashboards recomendados:

Exemplos importantes para serem acompanhados por dashboards são:

* Captação por origem e conversão do lead
* Tempo de atendimento do lead
* Reservas
* Vendas
* Estoque por status do workflow

# ✅Boas práticas

* Preserve chaves de origem do CVCRM
* Controle histórico e snapshot separadamente
* Tenha validação de contagem por carga
* Documente nomenclatura de status e origem

# 💭Métricas recomendadas

* Taxa de conversão por origem do lead
* Tempo até primeira interação do lead
* Tempo por etapa do workflow
* Estoque disponível x reservado x vendido (Reservas)
* Contratos por empreendimento

# 🚨Erros comuns

* Misturar carga histórica com snapshot atual
* Não versionar regras de transformação
* Ignorar diferenças entre ambientes
* Publicar indicador sem validação com negócio

<br />