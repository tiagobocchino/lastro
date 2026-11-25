---
chave: LST-44
jira: https://adelecrm.atlassian.net/browse/LST-44
secao: OPS
status: feito
especialista: engenheiro-backend
---

# Funil anônimo da demonstração e ligação com o atendimento (WhatsApp e LST-24)

**Plano:** `docs/planos/painel-gratis-no-site.md`, fatia 7. **Depende de:** LST-39.

## Critérios de aceite

- [x] `interno.demo_eventos` com etapa, duração, faixa de tamanho, número de colunas e visual escolhido, sem IP e sem nada da planilha
- [x] Funil no painel de operação (`lastro painel`): subiu → painel → clicou para conversar
- [x] O clique para conversar leva o tipo de painel na mensagem do WhatsApp, nunca os dados
- [x] Teste: nenhum evento contém valor da planilha

## Verificação

`uv run pytest -q` + os critérios acima.

## Evidência (25/11)

**Migração `0009_demo_eventos`** (aplicada no Supabase, sem aviso novo da advisora):
- Tabela `interno.demo_eventos`. Etapa, faixa de tamanho, formato e motivo são validados por `CHECK` com lista fechada, então nem SQL direto consegue gravar texto livre.
- View `painel.demo_funil_dia`, com subiram, painéis, clicaram, recusas, desistências e tempo médio do painel. `painel_leitor` lê a view, mas não a tabela.

**Eventos** (`Demos.evento`; gravar nunca derruba a demonstração):
- `subiu`: faixa de tamanho, número de colunas e ms.
- `recusou`: motivo formato, tamanho, linhas, leitura, limite_ip ou fila.
- `painel`: formato e ms.
- `painel_falhou`.
- `desistiu`: desistir ou sair da página.
- `clicou_contato`: o site manda só o formato, por `sendBeacon`, ao clicar no WhatsApp.

A mensagem do WhatsApp leva o tipo de painel, nunca os dados (LST-43).

**Painel de operação** (`lastro painel`): bloco "Funil da demonstração do site", com barras subiram → receberam o painel → clicaram, a % de cada etapa sobre a anterior e uma tabela dos últimos 7 dias.

**Testes:** mais 7.
- Etapas na ordem certa.
- Uma planilha com nomes e valores "secretos", nome de arquivo e IP: nada disso aparece nos eventos.
- Clique forjado com `<script>` vira `visual = null`.
- Limite de IP vira `recusou/limite_ip`.
- Falha ao gravar o funil não derruba o fluxo.
- `evento_demo` recusa etapa desconhecida e zera valores fora da lista.
- O funil aparece no HTML do painel de operação.
- No Postgres: constraint, view e permissão do `painel_leitor`.

Suíte completa: **298 passed**.

**Produção:** o clique chegou à tabela e a view contou 1. Era um teste meu e foi apagado para não sujar o funil real.
