---
name: power-bi-servico-gateway-nuvem
description: Atualiza no Desktop e falha no Serviço com Premium_ASWL_Error ou 'No such host is known' por mistura de fonte na nuvem com gateway
type: erro-conhecido
tags: [power bi, serviço, gateway, refresh, Premium_ASWL_Error, cloud data source, no such host is known, credenciais, postgres]
---

# Sintoma

- No Desktop a atualização funciona; no Serviço falha com `Premium_ASWL_Error: Cloud data source setting is not allowed refresh through gateway`.
- Ao criar a conexão na nuvem aparece: "Não foi possível conectar… credenciais inválidas", com o detalhe `No such host is known`.

# Causa

- O modelo mistura uma fonte de nuvem (Postgres gerenciado) com uma fonte que exige gateway (ODBC ou arquivo local), ou a fonte de nuvem ficou mapeada no gateway.
- O "host desconhecido" aparece quando o servidor gravado no modelo não resolve a partir do Serviço: host antigo, endpoint trocado ou nome digitado errado.

# Correção

1. Nas configurações do modelo semântico, deixe as fontes de nuvem como **conexão de nuvem**, fora do gateway. Use gateway só para o que é local.
2. Confira o host exatamente como está no projeto: parâmetro de servidor e porta.
3. Melhor ainda: **não misture**. Leve tudo para uma fonte só, na nuvem.
4. O Lastro entrega o gold por HTTPS (plano docs/planos/bi-sem-atrito.md) justamente para não depender de gateway nem de certificado.
