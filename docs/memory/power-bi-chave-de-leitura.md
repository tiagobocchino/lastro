---
type: armadilha
description: "Power BI com chave de leitura dá 'Não foi possível autenticar' (401) quando o parâmetro ChaveLastro não é exatamente a chave salva; diagnosticar por interno.bi_recusas, nunca pedindo a chave"
---

# Power BI · "Não foi possível autenticar com as credenciais fornecidas"

**Regra:** com o BI por HTTPS (LST-47), esse erro é sempre 401 do Lastro: a chave que o Power BI envia não confere. Diagnosticar pelo banco, sem pedir a chave a ninguém:
- `interno.bi_acessos.chave_usada_em` só muda quando uma chave é aceita;
- `interno.bi_recusas` guarda o motivo de cada recusa:
  - `sem_cabecalho`: o Power BI não enviou a chave;
  - `prefixo`: o valor não começa com `lst_`. Fica gravado o tamanho e os 3 primeiros caracteres, que não são segredo, porque o valor não é uma chave;
  - `desconhecida`: tem `lst_`, mas não é a chave salva.

**Why:** em 26/11 o Tiago levou cerca de 1 h no Power BI Desktop. Os diagnósticos às cegas foram espaço, maiúscula e aspas. O registro de motivos mostrou `tam=36 inicio='cha'`: o parâmetro estava sem o `lst_` do começo, e a chave salva pelo SQL Editor tinha o prefixo.

**How to apply:**
- Peça para a pessoa tentar de novo e leia `interno.bi_recusas`. O motivo diz o que corrigir.
- A chave do portal (`lst_` + 48 caracteres hexadecimais) já vem completa e só em minúsculas: prefira o portal ao SQL Editor.
- O servidor ignora espaço, aspas, caractere invisível nas pontas e maiúscula (`bi.normalizar_chave`).
- A janela de credencial do Power BI aparece em todo 401: escolher "Anônimo" está certo, quem autentica é a chave.
