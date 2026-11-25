---
name: mudar-sem-mudar-o-numero
description: Otimizar ou refatorar painel validado pelo negócio sem mudar nenhum número visível, com roteiro de validação antes e depois
type: metodo
tags: [refatoração, performance, refresh, validação, regressão, relatório validado, roteiro, antes e depois]
---

# Regra de ouro

Um relatório validado pela área de negócio **não pode mudar de valor sem que alguém perceba**. O critério de toda mudança: eliminar o custo sem mudar o resultado que o usuário vê.

# Como fazer

1. **Mapeie antes** tudo que consome o que vai mudar:
   - medidas e colunas calculadas;
   - filtros de visual e segmentações;
   - indicadores e marcadores.
   Liste antes de alterar.
2. **Se algum caso de borda puder mudar o número, pare e avise.**
3. **Mude uma coisa de cada vez**, com o arquivo fechado, numa cópia de estudo.
4. **Entregue o roteiro de validação:** qual visual abrir, qual número comparar com o de antes e o que indicaria quebra.
5. **Estimativa honesta:** quanto do problema foi resolvido e o que falta, sem inflar.

# O que o Lastro já faz

A auditoria em duas camadas e o total de controle de cada tabela são o "antes e depois" automático.
