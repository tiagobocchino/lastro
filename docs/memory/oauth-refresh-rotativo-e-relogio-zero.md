---
type: armadilha
description: OAuth2 de RD Station e Conta Azul invalida o refresh_token antigo a cada renovação; relógio em 0.0 engana "agora or time.time()"
---

# OAuth2: refresh rotativo e relógio zero

Regras:

1. **Gravar o par novo de tokens no cofre na hora da renovação, antes de usar o token.** RD Station CRM e Conta Azul devolvem um `refresh_token` novo a cada renovação e matam o antigo. Se o processo cair depois de renovar e antes de gravar, a conexão morre e o cliente precisa autorizar de novo.
2. **Nunca escrever `agora or time.time()`.** O relógio virtual do simulador começa em `0.0`, que é falso em Python, e o código passa a usar a hora real sem avisar.
3. **A RD Station CRM tem duas APIs.** A v1 (`crm.rdstation.com/api/v1`) usa token fixo por usuário e respeita a visibilidade dele. A v2 (`api.rd.services/crm/v2`) usa OAuth2. O Lastro usa a v2.

**Why:** o item 2 fez 4 testes de renovação passarem sem renovar nada, até o `0 == 1` aparecer. Os itens 1 e 3 vêm das páginas oficiais salvas em `docs/fontes-saas/_bruto/md/` (rdstation-crm-v2-*, contaazul-*).

**How to apply:**
- Qualquer conector OAuth novo entra pelo `GerenteToken` (`lastro/saas/oauth.py`).
- Para "agora", use `time.time() if agora is None else agora`.
- Para conferir um contrato de API, busque com `curl` pelo proxy: o WebFetch desta sessão não resolve os portais de documentação.
