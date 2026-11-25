---
chave: LST-10
jira: pendente (subir quando o projeto LST existir)
secao: MKT
status: em-qa
especialista: redator-de-copy
---

# Reescrever o site para o empresário

**Por quê:** O site atual explica o sistema; o empresário quer resposta para as preocupações dele.

## Critérios de aceite

- [ ] Perguntas do empresário respondidas na ordem dele
- [ ] Toda afirmação tem prova no produto
- [ ] Sem rolagem horizontal em 375px; temas claro e escuro

## Verificação

Comandos da seção MKT em `docs/agents/secoes.yaml` + os critérios acima.

## Entrega (aguardando QA)

- `site/index.html` + `site/img/` (telas reais da demo, dados fictícios)
- Prévia privada: https://claude.ai/artifact/Nz5EVywrMvaxR39K1riCme
- 375px sem rolagem horizontal (Playwright)
