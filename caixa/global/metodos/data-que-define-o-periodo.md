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

# O que o agente faz (interpretação)

- Com mais de uma data, o grill mostra quantas estão preenchidas e avisa que a escolha muda a contagem por mês.
- Diz quantos registros ficam fora da série por não ter a data escolhida.
- Data que não é data (`0000-00-00`) não vira data: fica vazia na leitura, sem inventar um dia.

# O que o cliente responde (regra de negócio, nunca deduzida)

- **Qual data define o período** desta análise.
- **No funil, se cada etapa tem data própria** e qual é. O agente não supõe que é a data da etapa nem a de criação.
