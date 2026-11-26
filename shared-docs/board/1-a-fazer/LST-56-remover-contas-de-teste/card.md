---
chave: LST-56
jira: https://adelecrm.atlassian.net/browse/LST-56
secao: OPS
status: a-fazer
especialista: engenheiro-backend
---

# Remover as contas de teste da produção ao fim da fase de testes

**Pedido do Tiago (26/11):** as contas de teste (ana, rui e admin @demo.lastro) foram ligadas em produção só durante a fase de testes e implementação. A senha delas é conhecida e está no código. Este card garante que elas saiam antes de entrar o primeiro cliente.

## Como está hoje

- Em produção, `lastro/cli.py` → `contas_demo()` só cria as contas com a variável `LASTRO_CONTAS_DEMO=1` no Render.
- Sem a variável, o servidor **tranca** as contas ao subir: troca a senha por uma aleatória. Ninguém é apagado, porque o rastro das demandas aponta para essas contas.
- A tela de login em produção nunca mostra nem preenche as contas (`/api/config` → `contas_demo: false`).
- As contas ficam na empresa `demo`, que só tem dados fictícios e é separada da `gimi-teste`.
- Testes: `tests/test_contas_demo.py`.

## Critérios de aceite

- [ ] Variável `LASTRO_CONTAS_DEMO` removida do serviço no Render (o Tiago faz no painel).
- [ ] Depois do deploy, entrar com `admin@demo.lastro` em produção falha com "E-mail ou senha não conferem".
- [ ] Decidido com o Tiago se a empresa `demo` e as demandas dela ficam no banco (histórico) ou são arquivadas.
- [ ] Qualquer menção à variável no `render.yaml` e na documentação removida.
- [ ] Nota em `docs/memory/` se algo inesperado aparecer.

**Quando:** ao fim da fase de testes e implementação, antes do primeiro cliente real no portal.
