---
chave: LST-17
jira: https://adelecrm.atlassian.net/browse/LST-17
secao: NUC
status: feito
especialista: engenheiro-backend
---

# Fechar falhas de segurança achadas na revisão antes da nuvem

**Por quê:** A revisão geral achou leitura de arquivos entre empresas pela trava de SQL e desvio de credencial por variável de URL.

## Critérios de aceite

- [x] Trava recusa funções de leitura de arquivo/ambiente e arquivo como tabela
- [x] Variáveis de host validadas; de caminho, codificadas
- [x] Produção sem LASTRO_SEGREDO forte não sobe
- [x] Upload acima do limite volta 413
- [x] Suíte verde

## Verificação

Comandos da seção NUC em `docs/agents/secoes.yaml` + os critérios acima.

## Situação

QA aprovou em clone limpo (1af1ac4) com os payloads originais. Bug, prioridade máxima, Sprint 1.
