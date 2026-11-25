---
chave: LST-30
jira: https://adelecrm.atlassian.net/browse/LST-30
secao: OPS
status: em-andamento
especialista: engenheiro-de-dados
---

# Espelhar os arquivos das empresas no Supabase Storage (disco do Render é efêmero)

**Por quê:** plano B (ADR 0009). No Render gratuito, o disco é apagado quando o serviço reinicia, publica de novo ou dorme. As fontes, o gold, os relatórios e a Caixa de cada empresa precisam sobreviver.

## Critérios de aceite

- [ ] Cada gravação na pasta da empresa vai para o bucket privado `tenants/<empresa>/...` do Supabase Storage
- [ ] Pasta ausente no disco é restaurada inteira do bucket antes do uso
- [ ] Teste: apagar o disco local e o ciclo da demanda continua com os mesmos dados
- [ ] Sem `LASTRO_STORAGE_URL`, nada muda (modo local e bucket montado da ADR 0007)
- [ ] Chave do Storage só em variável de ambiente; nunca no repositório, no rastro ou no laudo

## Verificação

`uv run pytest -q` + teste contra o Storage do projeto lastro-teste.
