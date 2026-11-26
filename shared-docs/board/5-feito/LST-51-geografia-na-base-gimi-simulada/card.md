---
chave: LST-51
jira: https://adelecrm.atlassian.net/browse/LST-51
secao: NUC
status: feito
especialista: engenheiro-de-dados
---

# Geografia (estado e região) na base GIMI simulada

**Plano:** `docs/planos/relatorios-gimi-teste.md`.

## Critérios de aceite

- [x] Estado e região do cliente e do projeto no contrato bruto, no formato IApp
- [x] Gabarito por UF e por região
- [x] gimi-teste regenerada, demandas rodadas de novo e BI republicado (painel_*, HTTPS, planilha)
- [x] Totais por região no BI iguais ao gabarito

## Evidência (26/11)

- **Gerador:** a geografia é sorteada com um Random próprio por contrato e por cliente, então os totais de antes não mudaram. A região sai da UF pelo IBGE e 3% das obras ficam sem local. Teste `test_geografia_no_contrato_sem_mudar_os_totais`; a suíte inteira está verde (334).
- **Produção (gimi-teste):**
  - fontes 14 a 16 com estado e região;
  - demandas 15 a 18 executadas, auditadas e aprovadas pelo produto;
  - as demandas 7 a 10 e as fontes 8 a 10 foram removidas, com autorização do Tiago;
  - BI republicado (56 tabelas, sem avisos) e planilha Google atualizada com 4 abas.
- **`painel_15` por região da obra, igual ao gabarito:**

| Região | Vendido | Contratos |
| --- | --- | --- |
| Centro-Oeste | 65.289.780,98 | 1.220 |
| Sudeste | 60.666.831,79 | 1.080 |
| Sul | 46.577.412,28 | 820 |
| Nordeste | 26.327.606,76 | 452 |
| Norte | 6.333.487,19 | 106 |
| Sem local | 6.095.148,16 | 112 |
| **Total** | **211.290.267,16** | **3.790** |

- **Outros totais:** orçado 532.781.125,76 (`painel_16`), itens 211.290.267,16 (`painel_17`), RH 239 (`painel_18`).
