---
name: data-que-define-o-periodo
description: Cada coluna de data põe o registro num mês diferente; a escolha da data muda contagens e funil
type: metodo
tags: [data, período, mês, competência, funil, criação, solicitação, aprovação, data de referência]
---

# O problema

O mesmo cartão "Solicitado, setembro" deu três números:
- 58 pela data de criação;
- 32 pela data de solicitação;
- 30 com deduplicação por projeto.

Cada etapa do funil pode ter a sua própria data de referência: a solicitação, o envio, a aprovação.

# Regra

- Com mais de uma data, o grill pergunta qual define o período e mostra quantas estão preenchidas.
- Quem não tem a data escolhida fica fora da série temporal. Diga quantos são.
- No funil, a data de referência é a da **etapa**, não a de criação. Se o negócio usa datas diferentes por etapa, anote como regra.
- Datas de mentira (`0000-00-00`, `1900-01-01`) viram vazio, nunca uma data.
