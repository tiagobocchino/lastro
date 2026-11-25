---
chave: LST-7
jira: https://adelecrm.atlassian.net/browse/LST-7
secao: NUC
status: feito
especialista: engenheiro-de-dados
---

# Agendar cargas incrementais por conector (plano Operação)

**Por quê:** O empresário quer o número de hoje sem pedir de novo.

## Critérios de aceite

- [x] Agenda por fonte com marca d'água da última data
- [x] Execução respeita a cota diária do contrato (ex.: Sienge Free 100/dia)
- [x] Falha vira aviso no portal, sem carga parcial na gold

## Verificação

Comandos da seção NUC em `docs/agents/secoes.yaml` + os critérios acima.

## Evidência (25/11)

**Agenda e marca d'água:**
- Tabela `cargas` no SQLite e no Postgres (`supabase/migrations/0003_cargas.sql`), com RLS. No `lastro-teste`: o tenant A só vê as próprias cargas, não desativa as de B (0 linhas), e o demandante não cria carga. O verificador de segurança não trouxe nada novo.
- A marca d'água é o início da última carga boa. A próxima pede só o que mudou, com 1 hora de sobreposição, e deduplica pela chave.
- No teste, a primeira carga trouxe 450 registros em 3 requisições. A seguinte trouxe só os 2 que mudaram, em 1 requisição, e a fonte ficou com 451 linhas, sem duplicata e com o valor atualizado.

**Cota diária:**
- O `Leitor` recebe um orçamento e para antes de passar dele (`CotaEsgotada`).
- A cota vem do pacote do contrato do cliente no catálogo (Sienge Free = 100) e é somada entre as cargas do mesmo sistema no dia.
- Com cota 2 para uma carga de 3 páginas: 2 requisições, fonte intacta, aviso "volta amanhã", e não roda de novo no mesmo dia.

**Falha vira aviso, sem carga parcial:**
- A fonte nova é escrita num temporário e entra com `os.replace` só se a extração inteira deu certo.
- Testado com credencial recusada, chave ausente e cota no meio da carga: a fonte fica byte a byte igual e a marca d'água não anda. A falha comum tenta de novo na hora seguinte.
- O aviso aparece no topo da aba de demandas e na lista de cargas. A credencial não vai para o rastro.

**Disparo:**
- `POST /tarefas/cargas` com `X-Lastro-Tarefa`: sem o cabeçalho, 401; com o segredo errado, 401; sem segredo configurado, 503.
- Localmente, `lastro cargas`.
- `POST /api/cargas` exige admin e plano Operação. A credencial vai só para o cofre (procurada nos bytes do banco: ausente).

**Tela:**
- Depois de "testar e importar", aparece "Manter esta fonte atualizada", com horário e pacote.
- Playwright em 1440 e 375 px: agendou, `lastro cargas` com falha forçada gerou o aviso no portal, sem rolagem lateral e sem erro no console.

**Suíte:** 177 passed, com Postgres.
