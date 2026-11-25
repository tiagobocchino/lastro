# Lições do dia a dia de BI com IA → regras dos agentes (LST-45)

**Fonte:** as sessões de trabalho do Tiago com Power BI e Looker Studio entre setembro e novembro de 2026:
- erro e lentidão de refresh;
- discrepância card × tabela;
- query única de conferência;
- comparativos de etapas;
- documentação do relatório de RH;
- e a frente Looker × Athena do engenhadev.

Nenhum dado de cliente foi copiado: só o padrão do problema e a regra.

| O que aconteceu | Regra | Onde está no Lastro |
| --- | --- | --- |
| Cartão com 174 orçamentos, tabela com 120. 54 não tinham itens (medida em branco) e 11 caíam no filtro de página | Decompor o universo por motivo; a linha sem valor conta e some | Auditor: aviso "nulos na medida" (explica cartão × tabela) e "fora do gráfico por X". Intérprete: "por que não bate?". Nota `metodos/conferencia-card-x-tabela` |
| A mesma pergunta deu 174, 169, 167 e 156 contando orçamento, número de controle, id e nome do projeto | Perguntar a unidade da contagem; a versão mais recente vence | Nota `metodos/unidade-de-contagem` |
| "Solicitado" deu 58, 32 ou 30 conforme a data | Com várias datas, mostrar quanto cada uma cobre | Grill: a pergunta da data mostra quantas estão preenchidas. Nota `metodos/data-que-define-o-periodo` |
| 7 de 247 estágios com espaço no fim quebraram o mapeamento; acentos `Ã§`; `N/A` como categoria | Trim e espaços colapsados na silver; caixa e acento não se corrigem em silêncio | Engenheiro: silver com trim e espaços colapsados. Explorador: `qualidade` (grafias, marcadores, acentos). Auditor: avisos por dimensão. Nota `erros/texto-sujo-em-categoria` |
| Atualiza no Desktop e falha no Serviço: `Premium_ASWL_Error`, "No such host is known" | Não misturar nuvem com gateway; host exato | Nota `erros/power-bi-servico-gateway-nuvem`; plano `docs/planos/bi-sem-atrito.md` |
| Refresh lento: data/hora automática em 53 visuais, `FILTER(ALL)` em coluna calculada, calendário sem limite | Uma mudança por vez, sem mudar número | Notas `erros/power-bi-refresh-lento` e `metodos/mudar-sem-mudar-o-numero` |
| Relatório validado pelo negócio não pode mudar de valor | Mapear quem consome antes de mudar; roteiro de validação | Nota `metodos/mudar-sem-mudar-o-numero`; auditoria em duas camadas |
| O negócio pediu uma tabela só, com todas as regras, para conferir no DBeaver | Tabela larga com as regras do painel | Nota `metodos/tabela-unica-de-conferencia`; card A do plano BI sem atrito |
| Classificação jogou 100% em "MATERIAL AVULSO" depois de a API mudar o formato | Teste com o formato real; "outros" crescendo é alarme | Nota `erros/formato-da-origem-mudou` |
| Nunca alterar planilha do cliente; RH só agregado; quem publica é o dono | Somente leitura; LGPD | Nota `metodos/regras-com-dados-do-cliente` (já valia para os agentes; agora está escrito) |

**Testes:** `tests/test_licoes_de_bi.py`.
