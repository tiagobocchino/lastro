---
name: regras-com-dados-do-cliente
description: Regras de convivência com os dados e relatórios do cliente aprendidas no uso real
type: metodo
tags: [governança, somente leitura, planilha, relatório validado, lgpd, rh, versões, publicar]
---

# Garantias da plataforma (valem para todo cliente)

- **Somente leitura nas fontes.** Planilhas, relatórios e bases do cliente são referência e nunca são alterados (ADR 0002).
- **Regra de negócio vem do cliente** (ADR 0011). Como contar, qual data, o que é o mesmo valor, o que entra e o que sai: o agente pergunta, não deduz. A resposta fica gravada e é seguida.
- **Relatório validado não muda de valor sem aviso** (ver mudar-sem-mudar-o-numero).
- **Dado pessoal não aparece no painel** sem decisão explícita (LST-41).
- **Linhagem documentada:** fonte → tratamento → tabela → visual.

# O que cada cliente define (perguntar e registrar, nunca supor)

- Como mostrar dados de pessoas, por exemplo RH em agregado ou por empresa como filtro.
- Quem publica e onde.
- Quantas versões guardar e o que conta como versão.
