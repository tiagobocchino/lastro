# Agentes contra a base GIMI simulada (LST-36, fases 1 e 2)

**Objetivo:** testar os agentes do Lastro sem dado real, com uma base que copia o **formato** do IApp da GIMI e as **regras** do ETL (`carteira_simulacao` do engenhadev). Nenhum dado real foi copiado.

## Base (fase 1)

- Gerador: `lastro/simulados/gimi.py` (`lastro simular-gimi --saida PASTA --semente 36 --contratos 3000`).
- 4 empresas (gimi, gbl, gpb, filial), 3000 contratos cada, de 07/2023 a 10/2026; funil Orçado → Em negociação → Aprovado/Perdido; RH com cargo e setor, sem salário.
- Sujeira proposital: registros TESTE (371), antes do corte de 2024-01-01 (1983), valor zero (245), contratos repetidos (120), vendedor com " - (id)" e "_" no nome, vendedor nulo.
- `gabarito.json` traz as respostas certas, calculadas com as regras do ETL.
- A API simulada (`SaasSimulado(dados_base=...)`) serve a mesma base no formato bruto, paginada, para testar conectores.

## Avaliação (fase 2)

`lastro/simulados/avaliacao.py` usa o produto como um cliente: empresa `gimi-teste`, as planilhas como fontes, quatro demandas em português, grill respondido com as regras que cabem nele (status, corte de data, valor zero, registros de teste) e execução normal.

Rodar de novo:

```bash
uv run python -c "from pathlib import Path; from lastro.simulados import avaliacao as a; print(a.relatorio_md(a.avaliar(Path('/tmp/aval'))))"
```

Semente 36, 3000 contratos por empresa:

| Checagem | Gabarito | Agente | Bate |
| --- | --- | --- | --- |
| D1 total vendido (aprovados, sem teste, desde 2024, sem valor zero) | 211290267.16 | 211290267.16 | ✅ |
| D1 auditoria camada 1 aprovada | True | True | ✅ |
| D1 soma por vendedor = total (sem vendedor fica de fora do agrupamento?) | 203116853.46 | 203116853.46 | ✅ |
| D1 por vendedor, depois de aplicar a limpeza do ETL | {"Elisa Ramos": 19155267.34, "Bruno Teles": 18769542.55, "Joana Freitas": 17570068.92, "Diego": 17427883.02, "Aline Castro": 17260864.12, "Fabio Rocha": 1722453 | {"Elisa Ramos": 19155267.34, "Bruno Teles": 18769542.55, "Joana Freitas": 17570068.92, "Diego": 17427883.02, "Aline Castro": 17260864.12, "Fabio Rocha": 1722453 | ✅ |
| D2 contratos por status (funil) | {"Aprovado": 3790, "Perdido": 2380, "Orçado": 2109, "Em negociação": 1243} | {"Aprovado": 3790, "Perdido": 2380, "Orçado": 2109, "Em negociação": 1243} | ✅ |
| D2 valor orçado total (carteira limpa) | 532781125.76 | 532781125.76 | ✅ |
| D3 total vendido pelos itens | 211290267.16 | 211290267.16 | ✅ |
| D4 funcionários ativos por setor | {"Administrativo": 33, "Comercial": 58, "Engenharia": 44, "Instalação": 58, "Produção": 46} | {"Administrativo": 33, "Comercial": 58, "Engenharia": 44, "Instalação": 58, "Produção": 46} | ✅ |

## Achados

1. O agente agrupa pelo nome **bruto** do vendedor ("Carla Moura - (…)", "diego_vaz"). A regra de limpeza do ETL (cortar " - (" e "_") não tem lugar no grill: o painel mostraria o mesmo vendedor com o nome do sistema.
2. Contratos **sem vendedor** (NAO DEFINIDO no ETL) somem do agrupamento por vendedor: 8,173,413.70 ficam fora da tabela, embora estejam no total.
3. **Tipo de venda (GIMI × representante)** e **classe (texto entre parênteses do grupo)** são colunas derivadas por regra. O grill só aceita recorte (WHERE): não há como o agente criar a coluna. O gabarito tem GIMI: 88,346,378.27, REPRESENTANTE: 122,943,888.89.
4. **Categoria de produto por prefixo de SKU** (ESQ = Esquadria, POR = Porta…, fora da lista = MATERIAL AVULSO) também é regra derivada: o agente só enxerga o código do produto, que tem valores demais para virar dimensão.
5. No RH, o agente agrupou também por `ativo`: a palavra "ativos" da pergunta virou dimensão, embora já esteja no filtro. O número por setor bate, mas a tabela ganha uma coluna inútil.
6. **Contagem não é medida declarada:** o RH não tem coluna de valor, o grill fica sem `medida` e a contagem só sai pelo `registros` implícito. "Quantos funcionários" deveria ter contagem como medida explícita.
7. A regra real de limpeza da GIMI corta no primeiro "_": `diego_vaz` vira **"Diego"** e perde o sobrenome. O simulador reproduz a regra como ela é; vale confirmar com o cliente se é o desejado.

## Corrigido durante o teste

- Sem medida numérica, o Engenheiro gerava `count(*) AS registros` duas vezes no SELECT (`lastro/agents/construtores.py`). Agora sai uma vez.

## Leitura

Os números que os agentes entregam batem com o gabarito em tudo que o grill consegue expressar (recorte, medida, data, chave). O que falta é **coluna derivada por regra** (nome limpo do vendedor, tipo de venda, classe, categoria por SKU) e **contagem como medida**. São esses os próximos cards.
