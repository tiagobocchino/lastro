# ADR 0003: LLM opcional; heurística determinística é o caminho padrão

**Status:** aceito · 2026-11-25

## Decisão

Os agentes funcionam sem modelo de linguagem (perfil, grill, modelo, SQL e auditoria por regras). Com `LASTRO_LLM` configurado (Ollama, Groq, Gemini ou chave do cliente em endpoint compatível com a OpenAI), o LLM sugere termos ambíguos no grill e escreve o SQL do Analista; o SQL passa pela trava de leitura e, se falhar, cai na heurística.

## Consequências

Custo zero e resultado reproduzível no plano gratuito; perguntas fora do padrão "medida por dimensão/tempo" precisam do LLM.
