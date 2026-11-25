# ADR 0011 · Regra de negócio vem do cliente; o agente interpreta

**Data:** 25/11/2026 · **Status:** aceita · **Origem:** pedido do Tiago, ao revisar o LST-45

## Contexto

Ao transformar o dia a dia de BI em regras dos agentes (LST-45), algumas regras de negócio entraram como dedução:
- unir grafias;
- "a versão mais recente vence";
- "no funil, a data é a da etapa";
- RH só em agregado como regra geral.

Cada cliente tem as suas regras de vendas, de clientes e de negócio. A mesma situação pede respostas diferentes em empresas diferentes.

## Decisão

1. **Regra de negócio é sempre respondida pelo cliente**, nunca deduzida pelo agente. São regras de negócio:
   - como contar;
   - qual data define o período;
   - o que é o mesmo valor;
   - o que significa vazio;
   - o que entra e o que sai;
   - como classificar;
   - como mostrar dado de pessoas.
2. **A inteligência do agente é de interpretação:** detectar o que é ambíguo, medir o impacto de cada escolha (quantas linhas, quanto valor), explicar divergências e perguntar no momento certo.
3. **Nas regras que transformam o dado** (unificar, tratar como vazio, excluir, reclassificar), a sugestão padrão do grill é a opção que não muda nada ("manter como está"), nunca um palpite sobre o negócio. **Nas escolhas de leitura** (qual coluna é o valor, a data ou a chave), o agente propõe a partir do perfil e o cliente confirma ou troca antes de qualquer execução.
4. **A resposta do cliente é a regra:** fica gravada como decisão da fonte na Caixa do tenant e é seguida nas demandas seguintes, sem perguntar de novo.
5. Sem resposta, o dado segue como veio e o Auditor avisa o impacto.

## Consequências

- O Explorador detecta grafias diferentes e marcadores de vazio; o grill pergunta; o Engenheiro só aplica o que foi respondido.
- O padrão técnico de leitura não é regra de negócio e continua: `trim` nas pontas e data inválida que fica vazia.
- As notas da Caixa global separam "o que o agente faz" de "o que o cliente responde".
- Mais perguntas no grill na primeira demanda de cada fonte; nas seguintes, as respostas gravadas valem.
