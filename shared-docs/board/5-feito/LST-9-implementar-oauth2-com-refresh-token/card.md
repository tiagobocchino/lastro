---
chave: LST-9
jira: https://adelecrm.atlassian.net/browse/LST-9
secao: INT
status: feito
especialista: engenheiro-backend
---

# Implementar OAuth2 com refresh_token

**Por quê:** Conta Azul e RD Station expiram o token de acesso.

## Critérios de aceite

- [x] Fluxo de autorização uma vez pelo admin do cliente
- [x] Renovação automática antes do vencimento, testada no simulador
- [x] Token guardado só no cofre (Vault), nunca no banco em texto

## Verificação

Comandos da seção INT em `docs/agents/secoes.yaml` + os critérios acima.

## Evidência (25/11)

**Contratos conferidos nas páginas oficiais** (salvas em `docs/fontes-saas/_bruto/md/`):
- **RD Station CRM:** a v1 usa token fixo e por isso o Lastro passou para a v2 (`api.rd.services/crm/v2`). Token de 2 horas; `refresh_token` rotativo, que expira após 14 dias sem uso; o app se identifica no corpo do pedido.
- **Conta Azul:** token de 1 hora; `refresh_token` rotativo; o app se identifica por Basic no cabeçalho; o escopo é fixo.
- **Google Planilhas e Drive:** pedem `access_type=offline` e `prompt=consent`; o `refresh_token` é fixo. Os endereços do Google vêm da referência pública e serão validados no piloto.

**Autorização uma vez pelo admin:**
- `GET /api/saas/{saas}/oauth/iniciar` só aceita o admin e devolve o link com `state` assinado (10 minutos).
- `GET /oauth/retorno` troca o código pelos tokens, grava no cofre e registra `autorizou_conector` sem token.
- Na tela, os sistemas OAuth mostram o botão "autorizar no …" e o formulário não pede token. QA em 375 e 1440 px, sem erro no console.

**Renovação automática:**
- O `GerenteToken` renova quando faltam menos de 5 minutos, ou uma vez ao receber 401, e regrava o par novo no cofre na hora.
- O simulador ganhou um servidor de token com validade e `refresh_token` rotativo.
- `tests/test_oauth.py`: renovação nos 4 sistemas; o refresh antigo morre nos rotativos e continua no Google; o 401 no meio da carga é absorvido; refresh recusado pede nova autorização.
- O sandbox do portal roda o fluxo inteiro e o laudo mostra "1 renovação de token".

**Token só no cofre:**
- Produção usa o Supabase Vault. No `lastro-teste`, o segredo fica cifrado em `vault.secrets` e só o dono decifra; `authenticated` e `anon` não leem; nenhuma coluna de token existe em `public`. O teste foi apagado depois.
- Desenvolvimento usa um arquivo com permissão 600 em LASTRO_HOME/cofre, recusado em produção.
- `tests/test_oauth_api.py` procura o token nos bytes do banco SQLite inteiro e na resposta da API: não aparece.

**Suíte:** `uv run pytest -q` com Postgres = 163 passed.

**Lição:** `docs/memory/oauth-refresh-rotativo-e-relogio-zero.md`.
