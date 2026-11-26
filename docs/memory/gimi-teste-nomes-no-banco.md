---
type: fato-operacional
description: "Os nomes alfa/beta/gama/delta da gimi-teste foram trocados direto no banco do BI; uma nova publicação volta os nomes antigos até a base ser recarregada"
---

# gimi-teste: nomes das empresas trocados só no banco do BI

**Regra:** antes de publicar de novo o BI da gimi-teste (`/api/bi/publicar` da conta robo@gimi-teste), recarregue a base com o simulador atual. Ele já gera `alfa`, `beta`, `gama` e `delta`.

**Why:**
- Em 26/11 o Tiago pediu nomes fictícios no lugar dos códigos das empresas (gimi, gbl, gpb, filial) e escolheu trocar direto no banco.
- A troca foi feita no schema `bi_e3e3f5e1b6`, numa transação, em 15 tabelas: `painel_15` a `painel_18`, `d15`–`d18_dim_company`, `d15`–`d18_silver` e `fonte_*`.
- Os totais conferiram depois da troca: 211.290.267,16 vendido e 239 no RH.
- Os arquivos das fontes e o gold no disco do Render continuam com os nomes antigos. Publicar recria as tabelas a partir deles e desfaz a troca.

**How to apply:**
- Para republicar, recarregue as 3 fontes geradas por `lastro.simulados.gimi` (commit 2cbcb46 em diante) e refaça as demandas.
- Os totais não mudam: o nome não entra no sorteio.
- A planilha do Data Studio só recebe os nomes novos no próximo envio. O Streamlit guarda as tabelas por até 1 hora: reinicie o app para ver na hora.
