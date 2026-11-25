---
name: unidade-de-contagem
description: "Quantos" depende da chave: orçamentos, propostas, projetos e números de controle dão contagens diferentes do mesmo recorte
type: metodo
tags: [contagem, distinct, projeto, proposta, orçamento, chave, deduplicação, última versão, quantidade]
---

# O problema

Num mesmo mês, o mesmo recorte deu quatro números diferentes:
- 174 orçamentos (id);
- 169 números de controle;
- 167 projetos (projeto_id);
- 156 projetos (nome do projeto).

Os números diferem porque:
- um projeto recebe mais de um orçamento;
- o mesmo nome de projeto aponta para mais de um id.

# O que o agente faz (interpretação)

- Mede quantos valores distintos cada chave candidata dá no mesmo recorte e mostra a diferença.
- Explica por que diferem: o mesmo nome em mais de um id, ou mais de um registro por projeto.

# O que o cliente responde (regra de negócio, nunca deduzida)

- **Qual é a unidade** da contagem: registro, documento, projeto ou outra.
- **Se a mesma coisa aparece mais de uma vez, qual vale:** a mais recente, a primeira, a de maior valor ou todas. O agente não escolhe.
- A resposta vira decisão do cliente e é seguida nas demandas seguintes. O título do painel diz a unidade que o cliente definiu.
