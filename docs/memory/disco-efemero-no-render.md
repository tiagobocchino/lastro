---
type: armadilha
description: "Se o disco do servidor perder os arquivos (deploy, troca de instância), um 'publicar' apagaria o BI do cliente: publicar só apaga o que recria"
---

# Disco efêmero no Render: o BI não pode depender do arquivo ainda existir

**Regra:** a publicação do BI (`AcessoBI.publicar`) só apaga a tabela que vai recriar. Se o arquivo da fonte ou o gold de uma demanda aprovada não existe neste servidor (`bi.sem_arquivo`), a versão já publicada fica e o portal avisa.

**Why:**
- O `render.yaml` não declara disco persistente (`LASTRO_HOME=/dados` no container), então perder os arquivos é possível em troca de instância ou de plano.
- Antes desta proteção, publicar sem os arquivos apagava todas as tabelas do schema e não recriava nenhuma.
- **Fato observado em 25/11:** no deploy do LST-46 os arquivos da `gimi-teste` **sobreviveram**. As demandas 7 a 10 republicaram normalmente.
- Supor o disco zerado levou a enviar as fontes de novo e a rodar as demandas outra vez, o que duplicou fontes e demandas (11 a 14). Antes de refazer, confira se o arquivo sumiu mesmo: publicar e ler os avisos já diz isso.

**How to apply:**
- Antes de reenviar fontes ou rodar demandas de novo, publique e leia os avisos: só refaça o que aparecer como "mantida".
- Para atualizar, envie a fonte e rode a demanda de novo.
- A solução definitiva é armazenamento persistente (bucket da ADR 0007 ou disco pago no Render). Até lá, trate o arquivo antigo no servidor como "provável", não como garantido.
- Teste: `test_bi_publicar_depois_do_disco_zerado_mantem_o_que_ja_estava`.
