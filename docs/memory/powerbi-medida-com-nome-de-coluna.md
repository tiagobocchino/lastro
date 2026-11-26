---
type: armadilha
description: "PBIP gerado não abre ('A medida X não pode ser criada porque já existe uma coluna com o mesmo nome') quando medida e coluna da mesma tabela têm o mesmo nome, mesmo com caixa diferente"
---

# Power BI · medida com o nome de uma coluna

**Regra:** no TMDL, uma medida não pode ter o nome de uma coluna da mesma tabela. O Power BI não diferencia maiúsculas: "Registros" × "registros" já conflita. `relatorio_powerbi.projeto` recusa gerar se houver conflito, e o teste `test_nenhuma_medida_tem_o_nome_de_uma_coluna` cobre os três formatos da gimi-teste.

**Why:** em 26/11 os 4 relatórios do LST-52 passaram nos schemas oficiais (os JSON do relatório), mas o Desktop do Tiago recusou abrir. O TMDL não tem schema público: esse tipo de erro só aparece na abertura.

**How to apply:**
- Medida nova ganha um nome que não existe como coluna: "Nº de registros", "Quantidade total".
- Todo gerador de PBIP precisa de teste que leia o TMDL e cruze os nomes.
- A validação real é a abertura no Desktop: entregue e peça o print do erro.
