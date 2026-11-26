---
chave: LST-57
jira: https://adelecrm.atlassian.net/browse/LST-57
secao: NUC
status: em-andamento
especialista: engenheiro-frontend
---

# Dashboard e "Pergunte" dentro de cada demanda do portal (padrão Streamlit, para clientes pagantes)

**Pedido do Tiago (26/11):** levar para dentro do portal os dashboards com a qualidade do Streamlit, para os usuários pagantes.

## Grill (respondido pelo Tiago em 26/11)

- **Arquitetura: nativo no portal.**
  - O dashboard nasce do resultado da própria demanda (fontes e modelo do agente). Cada demanda tem o seu escopo, e outra base gera outro dashboard.
  - Não há serviço externo; o Streamlit Cloud segue como demonstração.
- **Lugar:** dentro de cada demanda.
- **Aprovação:** enquanto a demanda aguarda revisão, revisor e admin veem uma prévia marcada como "prévia, aguardando revisão". Os outros usuários só veem depois da aprovação (regra 2).
- **"Pergunte":**
  - Usa a chave do Lastro (Gemini grátis), e o portal avisa o cliente dos limites.
  - O cliente pode cadastrar as chaves dos modelos ou LLMs dele.
  - O padrão dos dashboards só é garantido com os modelos do Lastro, ou nos pacotes que incluem implementação nos modelos do cliente. Fora disso o padrão pode mudar, e o portal avisa.

## Tickets

1. **Dashboard na demanda.** Filtros, 4 cartões com o mesmo período do ano anterior, evolução, ranking top 10 + outros e conferência. Aparece sozinho, sem "montar painel", e vira prévia para o revisor em "aguardando revisor".
2. **"Pergunte" na demanda.** Um pedido em português vira gráfico sobre os dados da demanda.
   - A LLM usa a chave do Lastro (`GOOGLE_API_KEY` no Render). Se falhar, a interpretação cai para palavras-chave.
   - Só a pergunta e os nomes das colunas vão ao provedor.
3. **Chave própria do cliente** (conta → modelos de IA). Fica guardada no cofre, com o aviso de que o padrão não é garantido fora dos modelos do Lastro.

## Critérios de aceite

- [x] Cada usuário vê só as demandas da própria empresa (tenant), inclusive no dashboard e no "Pergunte".
- [x] Demanda em revisão: revisor e admin veem a prévia marcada; o demandante não vê o dashboard antes da aprovação.
- [x] Os números do dashboard conferem com a resposta auditada da demanda.
- [x] O "Pergunte" nunca manda linhas de dados ao provedor de LLM; o SQL é montado e validado pelo Lastro.
- [x] O portal mostra o aviso de limites (chave do Lastro) e o aviso de padrão não garantido (chave do cliente).
- [x] QA em 375 px e 1440 px, sem rolagem horizontal.

## Andamento (26/11)

- **Ticket 1 (commit b4f0162).** `GET /api/demandas/{id}/dashboard` monta o dashboard na hora a partir do gold da demanda.
  - Aparece sem "montar painel"; "personalizar o painel" cria a versão editável.
  - Na demanda em revisão, só revisor e admin veem a prévia.
  - A moldura é isolada (`sandbox`) e cresce com o conteúdo.
- **Ticket 2.** `POST /api/demandas/{id}/pergunte` (`lastro/pergunte.py`) usa o núcleo do Streamlit sobre a tabela da demanda.
  - A interpretação por palavras-chave reconhece qualquer dimensão do modelo.
  - Cada pedido entra no rastro como `pergunte`.
  - A imagem do Render ganhou o extra `llm` (LangChain e Gemini, sem Streamlit).
- **Ticket 3.** `GET`, `PUT` e `DELETE /api/conta/llm`: só o admin cadastra; a chave fica no cofre e nunca volta para a tela. Na aba conta, a seção "Modelo de IA do Pergunte" mostra o aviso de padrão não garantido.
- **Testes:** `test_dashboard_na_demanda_previa_so_para_o_revisor` e `test_pergunte_na_demanda_com_a_chave_do_lastro_ou_do_cliente`, com a LLM espiã. A suíte tem 364 testes passando.
- **Falta (Tiago):** pôr `GOOGLE_API_KEY` no Render (a chave do Lastro) e validar no ar.
