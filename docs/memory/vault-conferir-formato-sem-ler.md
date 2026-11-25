---
type: fato-operacional
description: "segredo gravado pelo Tiago no Vault: confira o formato com SQL sem ler o valor; exemplo de instrução costuma ir parar no Vault"
---

# Conferir um segredo do Vault sem ler o valor

**Regra:** depois que o Tiago grava um segredo no Supabase Vault, confira só o formato, nunca o valor. Use `length(...)`, `like 're\_%'` (prefixo esperado), `like '%@%'` (e-mail) e uma comparação com os textos de exemplo que você mandou. Se o serviço externo recusar, olhe primeiro a resposta em `net._http_response` (pg_net).

**Why:** no LST-26, o Resend respondeu "API key is invalid" três vezes. O Vault guardava o texto de exemplo das instruções (`re_…`, depois `PASTE_THE_FULL_RESEND_KEY`). A conferência de formato achou o problema sem expor a chave.

**How to apply:**
- Nas instruções, use marcadores em português e óbvios (`COLE_A_CHAVE_AQUI`).
- Mande junto a consulta de conferência que devolve `true`/`false`.
- Explique de onde vem o valor (qual painel, qual tela). Deixe claro quando o segredo não tem relação com usuários do Lastro: o Tiago perguntou se a chave era do usuário de teste ou do admin.
- Responda ao Tiago em português.
