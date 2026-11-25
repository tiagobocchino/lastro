---
type: armadilha
description: Chave secreta nova do Supabase (sb_secret_) vai só no cabeçalho apikey; no Authorization Bearer ela falha por não ser JWT
---

# Chave secreta do Supabase vai no `apikey`

**Regra:** com as chaves novas (`sb_publishable_…`, `sb_secret_…`), mande só o cabeçalho `apikey`. Só a `service_role` antiga, que é JWT e começa com `eyJ`, vai também no `Authorization: Bearer`. O `EspelhoStorage` já decide sozinho pelo formato da chave.

**Why:** a documentação de chaves da API (`docs/infra/fontes/supabase-chaves-api.txt`) diz que as chaves novas não são JWT e que tudo que tenta validá-las como JWT falha. As chaves antigas serão aposentadas até o fim de 2026.

**How to apply:**
- Qualquer cliente HTTP do Supabase (Storage, REST) segue a mesma regra.
- Para conferir o espelho em produção: `python scripts/conferir_espelho.py` com `LASTRO_STORAGE_URL` e `LASTRO_STORAGE_CHAVE`.
- Com a chave pública, o bucket `tenants` responde 400 na gravação e lista vazio. Isso é o esperado: o bucket é privado.
