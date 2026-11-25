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

# Regra

- Antes de contar, pergunte **qual é a unidade**: o registro, o documento ou o projeto. Registre a resposta como decisão da fonte.
- Contar por **nome** junta registros diferentes com o mesmo nome. Contar por **id** separa o que o negócio enxerga como uma coisa só. Diga ao negócio qual das duas foi usada.
- Quando o negócio quer uma linha por projeto, a regra costuma ser **a versão mais recente vence**: maior data de referência e, no empate, maior id.
- O painel precisa dizer a unidade no título, por exemplo "Projetos (por nome)", e não só "Quantidade".
