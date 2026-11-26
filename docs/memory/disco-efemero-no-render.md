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

## 26/11: o espelho não restaurava pasta "não vazia"

- **Sintoma:** em produção, logo depois de um deploy, a nova demanda da empresa demo falhou com `IO Error: No files found ... /dados/tenants/demo/fontes/orcamentos.csv`.
- **Causa:** `EspelhoStorage.restaurar` só baixava quando a pasta da empresa estava vazia. Na empresa demo, o servidor recria `politica.yaml` e a planilha de exemplo ao subir, então a pasta nunca estava vazia. Com isso, as fontes enviadas e o gold das demandas não voltavam do Storage.
- **Correção:**
  - `restaurar` baixa o que falta no disco, uma vez por empresa a cada vez que o servidor sobe, sem sobrescrever o que já existe;
  - `preparar_demo` recoloca a planilha de exemplo no caminho que o cadastro aponta.
  - Testes: `test_pasta_que_nao_esta_vazia_tambem_recebe_o_que_falta` e `test_planilha_de_exemplo_volta_quando_o_disco_e_apagado`.
