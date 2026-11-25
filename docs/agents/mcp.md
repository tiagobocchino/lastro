# MCP do Supabase e do Render para os agentes

Configuração em `.mcp.json` (servidores) e `.claude/settings.json` (o que roda sem perguntar e o que pede aprovação).

## Servidores

| Nome | O que é | Autenticação |
| --- | --- | --- |
| `supabase-lastro` | MCP oficial do Supabase, preso ao projeto `lastro-teste`, em **modo somente leitura** e só com os grupos database, docs, debugging e development | login no navegador na primeira vez (`/mcp` no Claude Code); nenhum token no repositório |
| `render` | MCP oficial do Render (`https://mcp.render.com/mcp`) | chave de API do Render na variável de ambiente `RENDER_API_KEY` da máquina; nunca no repositório |

## Regras (mesma filosofia do produto: agente só lê)

- **Supabase:** o modo somente leitura é imposto pelo próprio servidor, que roda as consultas com um usuário de banco só de leitura. Migração continua sendo feita pela sessão principal, revisada, com o arquivo versionado em `supabase/migrations/`.
- **Render, leitura:** serviços, deploys, eventos, logs e métricas rodam sem perguntar e estão liberados para os subagentes de engenharia.
- **Render, ações** (deploy, alterar variáveis, criar serviço ou cron, aplicar Blueprint): só a sessão principal, e o Claude Code pede aprovação a cada uso (`ask`). Nenhum subagente tem essas ferramentas.
- **Segredos:** o MCP do Render tenta não expor connection strings, mas não garante. Não peça ao agente para ler variáveis de ambiente do serviço.

## Quem tem o quê

| Subagente | Supabase (leitura) | Render (leitura) |
| --- | --- | --- |
| engenheiro-backend | sim | sim |
| engenheiro-de-dados | sim | sim |
| engenheiro-frontend | não | sim |
| pesquisador-de-apis | só a busca na documentação | não |
| designer-de-marca, redator-de-copy | não | não |

## Como ligar na máquina do Tiago (uma vez)

1. Render → **Account Settings → API Keys → Create API Key**. Copie a chave.
2. No PowerShell, rode `setx RENDER_API_KEY "<chave>"` e feche e abra o terminal.
3. Abra o Claude Code na pasta do `lastro` e aprove os servidores do projeto quando ele perguntar.
4. Rode `/mcp`, escolha `supabase-lastro` e faça o login no navegador. Para conferir, peça "liste meus serviços no Render" e "liste as tabelas do Supabase".

Nas sessões na nuvem, o Supabase já chega pelo conector do claude.ai, com acesso de escrita. Por isso as migrações continuam sendo feitas com revisão, pela sessão principal.
