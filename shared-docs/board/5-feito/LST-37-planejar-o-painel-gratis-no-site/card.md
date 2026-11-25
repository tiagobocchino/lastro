---
chave: LST-37
jira: https://adelecrm.atlassian.net/browse/LST-37
secao: MKT
status: feito
especialista: engenheiro-backend
---

# Planejar o painel grátis no site: o visitante sobe uma planilha e sai com um painel

**Seção:** MKT, com NUC e OPS. **Especialistas:** engenheiro-backend e redator-de-copy.

**Por quê:** fazer o visitante ver o Lastro funcionando com os dados dele, sem cadastro, e sair com um motivo para contratar.

**Jornada (pedido do Tiago):**
1. O visitante sobe os próprios dados no site.
2. O agente lê, interpreta e faz um grill rápido: o que mostrar e como mostrar.
3. O agente entrega um painel.
4. O Lastro apaga todo e qualquer dado temporário usado na análise.

## Critérios de aceite (deste card de planejamento)

- [x] Plano em `docs/planos/painel-gratis-no-site.md`, com:
  - a jornada e a arquitetura do modo visitante;
  - a tabela de apagamento: onde o dado pode ficar e como cada lugar é fechado e provado;
  - a regra das duas camadas, o anti-abuso, as métricas e as fatias de entrega.
- [x] Grill respondido pelo Tiago: 8 perguntas, na seção 9 do plano.
- [x] Cards de execução criados no Jira e no board a partir das respostas.

## Verificação

Plano revisado pelo Tiago e cards conferidos com `scripts/conferir_board.py`.

## Fechamento (25/11)

O Tiago aceitou as 8 recomendações do grill. Cards de execução: LST-38 a LST-44. O caminho mínimo para ir ao ar é LST-38, 39, 40, 42 e 43.
