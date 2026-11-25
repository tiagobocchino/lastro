# Lastro

Plataforma de agentes de análise de dados. O demandante faz uma pergunta; os agentes perguntam o que não devem adivinhar, montam o modelo e o pipeline, respondem e auditam. A entrega só sai depois da revisão de um especialista de negócio.

- **Multi-empresa**: login próprio; cada empresa só vê os próprios dados.
- **Fontes só em leitura**: a credencial do conector já é somente leitura, e toda consulta de agente passa por uma trava de SQL.
- **Auditoria em duas camadas**: o auditor técnico checa o pipeline e gera um notebook do Google Colab para o revisor de negócio refazer as contas.
- **Contexto indexável**: os agentes buscam na Caixa de Ferramenta (BM25 + RRF no SQLite FTS5) em vez de carregar tudo no prompt. Com `LASTRO_EMBEDDER=fastembed` (extra `vetores`), a busca também entende sinônimos com um modelo multilíngue local e gratuito.
- **Custo zero**: Python, DuckDB, SQLite e FastAPI. O LLM é opcional: Ollama local, free tier de Groq ou Gemini, ou a chave do cliente.

## Rodar

```bash
uv sync --extra dev
uv run python exemplos/gerar_orcamentos.py   # dados fictícios com armadilhas
uv run lastro demo                           # uma demanda de ponta a ponta no terminal
uv run lastro serve                          # portal em http://localhost:8000
uv run pytest -q
# testes do Postgres com RLS (ADR 0008): precisa de um Postgres onde o teste crie bancos
LASTRO_TESTE_PG=postgresql://postgres@localhost:5432/postgres uv run --extra postgres pytest -q tests/test_postgres.py
```

Em container (o mesmo que vai para o Cloud Run):

```bash
docker build -t lastro .
docker run -p 8080:8080 lastro                  # portal em http://localhost:8080, saúde em /saude
```

Com `LASTRO_AMBIENTE=producao`, o container exige `LASTRO_SEGREDO` (32+ caracteres) e não cria contas de demonstração.

Contas de teste do tenant `demo` (senha `demo1234`): `ana@demo.lastro` (demandante), `rui@demo.lastro` (revisor de negócio), `admin@demo.lastro` (admin, conecta fontes).

## Ciclo de uma demanda

| Status | Quem age | O que acontece |
| --- | --- | --- |
| `grill` | Explorador + Orquestrador | Perfil das fontes vira nota na Caixa; perguntas com sugestão padrão |
| `pronta` | Demandante | Respostas sobre a fonte (data, chave, revisor) viram decisões gravadas |
| `em_revisao` | Arquiteto, Engenheiro, Analista, Auditor | Modelo, pipeline Bronze/Silver/Gold no sandbox, resposta, auditoria camada 1, notebook do Colab |
| `aprovada` / `reprovada` | Revisor de negócio | Camada 2; reprovação vira nota de aprendizado |

## Onde as coisas moram

| Caminho | O que é |
| --- | --- |
| `lastro/caixa.py` | Caixa de Ferramenta: índice, busca, leitura por trecho |
| `lastro/agents/` | Orquestrador, Explorador, Arquiteto, Engenheiro, Analista, Auditor |
| `skills/` | A skill (SKILL.md) de cada agente do produto |
| `caixa/global/` | Playbooks, métodos, erros conhecidos e trilhas (AWS, Google, Microsoft) |
| `lastro/somente_leitura.py`, `lastro/conectores.py` | Trava de leitura e sandbox DuckDB |
| `lastro/politica.py` | Plano de contrato e liberdades por agente |
| `lastro/api.py`, `lastro/web/` | API e portal |
| `supabase/migrations/` | Esquema de produção com RLS por tenant |
| `.claude/skills/` | Skills de desenvolvimento (o método: grill, spec, tickets, tdd) |
| `site/` | Site de apresentação |
| `BRAND.md` | Marca |

Arquitetura e decisões em `docs/adr/`; termos em `CONTEXT.md`; método de trabalho em `AGENTS.md`.
