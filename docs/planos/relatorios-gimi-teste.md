# Relatórios da gimi-teste nas três ferramentas (como entrega a cliente)

**Estado:** aprovado pelo Tiago em 26/11/2026 (grill respondido no chat) · **Base:** gimi-teste (GIMI simulada, LST-36)

## O que o Tiago pediu

- **Quatro relatórios:** vendas por vendedor, funil de orçamentos, vendas por produto e RH. A entrega é como se fosse para um cliente.
- **Power BI e Looker Studio:** relatórios **arrojados**, no nível dos que o Tiago entrega para a GIMI. São várias páginas, com KPIs, funil, evolução, rankings, mapa e segmentações.
- **Python:** soluções **rápidas** de demonstração, com KPIs e análises gerais. Não descem em regras e subdivisões; no máximo chegam a **setor, geografia (estado e região) e data**.
  - **LangChain:** um agente recebe o pedido em português e monta o relatório. Os números saem de SQL conferido.
  - **Formato:** Streamlit em primeiro lugar. Se não houver como rodar de graça, HTML interativo.
- **Looker Studio:** o Tiago monta um **modelo** uma vez, com o roteiro do Lastro. Depois o Lastro gera um **link** que copia o modelo já ligado à planilha de qualquer cliente (Linking API).

## Regras que valem para os três (ADR 0011)

- Nenhuma regra de negócio é deduzida. Os relatórios usam só o que está no gold aprovado e nas respostas do grill.
- Uma regra nova, como "tipo de venda GIMI × representante", só entra quando o Tiago responder.
- Todo número de KPI tem um **total de controle** conferido contra o BI publicado:
  - vendido 211.290.267,16;
  - orçado 532.781.125,76;
  - 239 funcionários.

  Os totais mudam se a base for regenerada (card de geografia); o gabarito novo sai do gerador.

## Cards

| Card | Escopo | Depende |
| --- | --- | --- |
| Geografia na base simulada | Estado e região do cliente e do projeto no contrato bruto (formato IApp), gabarito por UF e região, gimi-teste regenerada e republicada | — |
| Power BI de entrega | PBIP multipágina por relatório: KPIs com comparação, funil, evolução mensal, ranking, mapa por UF, segmentações (empresa, período, região), tema da marca; lê por HTTPS (LST-47) | geografia |
| Looker Studio por modelo | Roteiro do modelo (página a página, visual a visual) sobre as abas `painel_*`, link de criação pela Linking API gerado pelo Lastro, botão no portal | geografia |
| Python rápido com LangChain | Streamlit (Community Cloud, gratuito) com KPIs gerais e um agente LangChain que monta gráficos a partir de pedidos em português; ferramentas só de leitura (SQL conferido por `somente_leitura`) sobre as tabelas `painel_*` lidas por HTTPS; plano B em HTML interativo (Plotly) | geografia |

## Decisões pendentes com o Tiago

1. **LLM do agente (decidido em 26/11): gratuita.** "Claude não é gratuito; vamos usar uma LLM gratuita, mesmo que limitada" (regra 5, grátis por padrão).
   - **Padrão:** Gemini Flash no nível gratuito do Google AI Studio (`langchain-google-genai`).
   - **Plano B:** Groq gratuito (Llama).
   - No nível gratuito o provedor pode usar o que recebe, então o agente manda só a pergunta e os nomes das colunas, nunca linhas de dados. Os números saem do SQL do Lastro.
   - A chave fica nos secrets do Streamlit e no Render.
2. **Hospedagem do Streamlit:** Community Cloud exige login com GitHub e o deploy feito pelo Tiago.
3. **Referência visual da GIMI:** usar a estrutura das páginas dos relatórios GIMI do Tiago (Relatório 0 analítico, 5 performance da carteira), só a estrutura, sem dado.
