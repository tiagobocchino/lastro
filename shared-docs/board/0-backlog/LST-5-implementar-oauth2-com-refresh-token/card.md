---
chave: LST-5
jira: pendente (subir quando o projeto LST existir)
secao: INT
status: backlog
especialista: engenheiro-backend
---

# Implementar OAuth2 com refresh_token

**Por quê:** Conta Azul e RD Station expiram o token de acesso.

## Critérios de aceite

- [ ] Fluxo de autorização uma vez pelo admin do cliente
- [ ] Renovação automática antes do vencimento, testada no simulador
- [ ] Token guardado só no cofre (Vault), nunca no banco em texto

## Verificação

Comandos da seção INT em `docs/agents/secoes.yaml` + os critérios acima.
