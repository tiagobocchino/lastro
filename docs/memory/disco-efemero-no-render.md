---
type: armadilha
description: "O disco do Render é zerado a cada deploy: fontes e gold somem e um 'publicar' apagaria o BI do cliente"
---

# Disco efêmero no Render: o BI não pode depender do arquivo ainda existir

**Regra:** a publicação do BI (`AcessoBI.publicar`) só apaga a tabela que vai recriar. Se o arquivo da fonte ou o gold de uma demanda aprovada não existe neste servidor (`bi.sem_arquivo`), a versão já publicada fica e o portal avisa.

**Why:** o `render.yaml` não tem disco persistente (`LASTRO_HOME=/dados` no container). Em 25/11, depois do deploy do LST-46, republicar a empresa `gimi-teste` teria apagado as 38 tabelas do BI. O script foi parado a tempo e o banco confirmou que nada mudou.

**How to apply:**
- Depois de um deploy, demanda antiga não pode ser re-executada sem reenviar a fonte.
- Para atualizar, envie a fonte e rode a demanda de novo.
- A solução definitiva é armazenamento persistente (bucket da ADR 0007 ou disco pago no Render). Até lá, não conte com arquivo antigo no servidor.
- Teste: `test_bi_publicar_depois_do_disco_zerado_mantem_o_que_ja_estava`.
