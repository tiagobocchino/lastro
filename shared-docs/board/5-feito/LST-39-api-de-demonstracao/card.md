---
chave: LST-39
jira: https://adelecrm.atlassian.net/browse/LST-39
secao: NUC
status: feito
especialista: engenheiro-backend
---

# API de demonstração /api/demo: sessão temporária, perfil, grill rápido, painel e apagamento com recibo

**Plano:** `docs/planos/painel-gratis-no-site.md`, fatia 2. **Depende de:** LST-38.

## Critérios de aceite

- [x] Rotas públicas sem login: enviar arquivo (ou usar o exemplo) → perfil → perguntas → painel → apagar
- [x] Sessão em `tmp/demo-<id aleatório>`, com no máximo 15 minutos de vida; varredura a cada 5 minutos apaga as abandonadas
- [x] Entrega do painel (HTML) na resposta e, em seguida, apagamento com recibo: arquivos, tabelas, bytes e hora
- [x] Logs só com etapa, tempo, tamanho e número de colunas, nunca valores ou nomes de coluna
- [x] Testes provam que, depois da sessão, nada sobra no disco, no banco, no Storage nem no log

## Verificação

`uv run pytest -q` + os critérios acima.

## Evidência (25/11)

**`lastro/demo.py` + rotas públicas, sem login:**
- `POST /api/demo/sessoes`: envia arquivo CSV ou Excel, ou `exemplo=true`. Devolve o perfil (linhas, colunas e papel de cada uma), as perguntas (sem a do revisor) e a hora em que a sessão expira.
- `POST /api/demo/sessoes/{id}/painel`: roda a análise em modo visitante e monta o painel (LST-34). Devolve o HTML, o resultado da auditoria (camada 1) e o **recibo**. O apagamento acontece antes da resposta sair, e também quando a análise falha.
- `DELETE /api/demo/sessoes/{id}`: o visitante desiste e recebe o recibo.

**Recibo:** hora, arquivos, bytes, tabelas, registros em memória e `conferido` (a pasta não existe mais).

**Sessões:**
- Cada sessão fica em `demo-<id de 128 bits>`, na pasta temporária local (`LASTRO_DEMO_DIR`).
- Duram no máximo 15 minutos. Uma varredura a cada 5 minutos, em thread, apaga as vencidas.
- Ao subir o servidor, qualquer resto `demo-*` é apagado.

**Log:** só etapa, ms, bytes, número de colunas ou visuais e o nome do erro. Nunca valores nem nomes de coluna.

**Segurança até o LST-42:**
- Desligada por padrão: só `LASTRO_DEMO=1` liga, e em produção ela fica desligada até existirem os limites.
- Já recusa arquivo acima de 5 MB e extensões fora de CSV e Excel.

**Testes:** `tests/test_demo.py`, 8 testes.
- Ponta a ponta com o exemplo: o total sai 14.030.477,92, com o filtro "Fechado" respondido no grill.
- Recibo conferido, nenhuma pasta `demo-*` sobrando e nenhuma linha nova no banco.
- O espelho nunca é tocado.
- Planilha própria em CSV e em Excel sem vazar no log: nomes de coluna e valores marcados são procurados no log inteiro e não aparecem.
- Recusas (extensão, 5 MB, Excel quebrado) não deixam pasta.
- Desistir gera recibo.
- A rota fica desligada sem a variável.
- Sessão abandonada é varrida aos 15 minutos, com relógio simulado.
- Restos são apagados ao reiniciar.

Suíte completa: **252 passed**.
