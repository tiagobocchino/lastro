---
chave: LST-34
jira: https://adelecrm.atlassian.net/browse/LST-34
secao: NUC
status: em-andamento
especialista: engenheiro-de-dados
---

# Agentes criam e editam dashboards (Python, Power BI e Looker Studio)

**Por quê:** além de responder perguntas, o agente precisa montar o painel: em Python (gratuito, para o nosso sistema e os exemplos do site) e, para quem já tem BI, deixar o painel pronto na ferramenta do cliente.

## Critérios de aceite

- [x] Dashboard em Python (HTML estático, sem custo) gerado pelo agente a partir da gold de uma demanda aprovada
- [ ] Projeto do Power BI em formato aberto (PBIP/TMDL) gerado pelo agente: modelo, relações e medidas DAX, que abre no Power BI Desktop gratuito
- [ ] Looker Studio: link de criação (Linking API, gratuita) apontando para a fonte do cliente
- [x] O agente edita um painel existente a pedido (nova medida, novo visual) sem quebrar o que já existe
- [x] Toda mudança no painel fica no rastro da demanda

## Verificação

`uv run pytest -q` + abrir o PBIP no Power BI Desktop e o HTML no navegador (QA em 375 px e 1440 px).

## Fora do escopo agora

Publicação no serviço pago do Power BI ou do Looker.

## Origem

Visão do Tiago em 25/11: o Lastro conecta bases e APIs aos BIs self-service; nosso próprio sistema e os exemplos do site usam dashboards em Python (gratuito), e Looker Studio no pior caso.

## Evidência (25/11)

**Desenho:** uma especificação JSON por versão (`demandas/<id>/painel/v<n>.json`) gera as duas saídas.
- O designer (`lastro/paineis.py`, skill `skills/designer-de-painel`) é determinístico.
- Ids estáveis e nunca reaproveitados.
- Toda mudança é validada contra o gold antes de gravar.

**Testes: 242 passed**, com Postgres e fastembed.
- `tests/test_paineis.py`, 15 testes:
  - painel inicial com KPI igual ao total auditado (14.030.477,92);
  - mudanças em português e estruturadas;
  - 9 mudanças inválidas recusadas sem alterar nada;
  - HTML sem script;
  - API de ponta a ponta com o rastro (`criou_painel`, `alterou_painel`, `recusou_mudanca_painel`, `baixou_powerbi`);
  - outra empresa recebe 404.
- **Power BI:** todos os JSON do PBIP (`.pbip`, `.pbism`, `.pbir`, `version`, `report`, `pages`, `page`, `visual`) validados contra os **schemas oficiais da Microsoft**. Os 12 schemas foram baixados de `microsoft/json-schemas` para `tests/dados/powerbi_schemas`.
- **TMDL:** conferidos a indentação por tab, o `ref table` de cada tabela, a partição lendo `PostgreSQL.Database(Servidor, Banco)` no schema do BI, as medidas DAX sobre colunas que existem e as relações fato–dimensões.
- **Fontes oficiais** em `docs/infra/fontes/powerbi-*.txt` (Microsoft Learn: projects-overview, projects-dataset, projects-report, tmdl-overview).

**QA no portal (Playwright):**
- fluxo demandante → revisor aprova → monta painel → pede "adicione um gráfico de barras de valor vendido por estado" (v5) → pedido ruim volta com exemplos → baixa o HTML e o `.zip` do Power BI;
- 375 px e 1440 px sem rolagem horizontal, sem erro de JavaScript.

Prints em `evidencias/`.

**Achado e corrigido** (commit `e459c26`, já em produção): a `baixar()` duplicada do LST-33 tinha quebrado os downloads da demanda. Há teste novo (`tests/test_portal_js.py`) e uma nota em `docs/memory/portal-app-js-nome-repetido.md`.

## Falta

1. **Power BI Desktop (Tiago):** baixar o projeto de uma demanda aprovada, abrir o `.pbip` no Desktop e clicar em Atualizar. Os JSON passam nos schemas oficiais, mas o TMDL e o carregamento só o Desktop confirma.
2. **Looker Studio — bloqueado:** a referência da Linking API só existe em `developers.google.com`, que a rede desta sessão não alcança.
   - O host foi liberado no ambiente, mas o download foi barrado pelo classificador de permissões, e o leitor de páginas também não resolve o endereço.
   - Uma fonte de terceiros (antiga) diz que a Linking API não aceita PostgreSQL, só BigQuery, Sheets, Spanner, Analytics, Cloud Storage, Surveys e Search Console.
   - Não gero link com parâmetro adivinhado. Para fechar este item: ler a referência oficial numa sessão que alcance o site e decidir entre (a) link para um modelo com Google Sheets/BigQuery ou (b) passo a passo do conector PostgreSQL, que já está em `docs/infra/bi.md`.
