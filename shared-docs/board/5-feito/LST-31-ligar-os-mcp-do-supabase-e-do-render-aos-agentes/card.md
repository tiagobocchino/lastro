---
chave: LST-31
jira: https://adelecrm.atlassian.net/browse/LST-31
secao: OPS
status: feito
especialista: engenheiro-backend
---

# Ligar os MCP do Supabase e do Render aos agentes, com leitura liberada e ações sob aprovação

**Por quê:** pedido do Tiago: os agentes e subagentes devem consultar o Supabase e o Render diretamente, sem abrir mão da regra de que agente só lê.

## Critérios de aceite

- [x] `.mcp.json` com o MCP oficial do Supabase (projeto do Lastro, read_only=true) e o do Render, sem nenhuma chave no repositório
- [x] Subagentes de engenharia com as ferramentas de leitura; nenhum com deploy, variáveis ou criação de recursos
- [x] Na sessão principal, ações do Render pedem aprovação (`ask` em `.claude/settings.json`)
- [x] Regras e setup em `docs/agents/mcp.md`
- [x] Conectado na máquina do Tiago (chave do Render e login do Supabase) e conferido com uma listagem em cada um

## Entrega (25/11)

- Endereços e opções conferidos na documentação oficial: Render em `https://mcp.render.com/mcp` com Bearer; Supabase em `mcp.supabase.com` com `project_ref`, `read_only` e `features`. Lista de ferramentas tirada do README oficial do Render.
- `.mcp.json`: a chave do Render vem de `${RENDER_API_KEY}`; o Supabase usa login no navegador.
- Subagentes: backend e dados leem Supabase e Render; frontend lê Render; o pesquisador só busca na documentação do Supabase; designer e redator não têm acesso.
- Falta: o Tiago ligar na máquina dele (passos em `docs/agents/mcp.md`).

## QA (25/11)

Na máquina do Tiago: `/mcp` conectou o `supabase-lastro` ("Authentication successful"), e "liste meus serviços no Render" respondeu com o serviço `lastro-api`. No caminho, foi limpa uma configuração antiga do Claude Code que apontava para um intermediário do OpenRouter na porta 3456 (`apiKeyHelper`, `*_BASE_URL`, `ANTHROPIC_MODEL`), com backups `settings.json.bak*`.
