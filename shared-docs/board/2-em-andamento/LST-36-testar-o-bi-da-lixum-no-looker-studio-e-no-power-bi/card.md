---
chave: LST-36
jira: https://adelecrm.atlassian.net/browse/LST-36
secao: INT
status: em-andamento
especialista: tiago
---

# Testar o BI da lixum no Looker Studio (Data Studio) e depois no Power BI Desktop

**Responsável:** Tiago. **Fecha:** o LST-34; também confirma o LST-33 com um BI real em produção.

**Por quê:** os arquivos e a conexão passaram nos testes automáticos e no Metabase. Só uma conexão real do Tiago, de fora, confirma o Looker Studio e o Power BI Desktop.

## Critérios de aceite

- [ ] **Looker Studio (Data Studio), primeiro:**
  - fonte de dados PostgreSQL com os dados de **conta → Conectar ao BI**;
  - SSL ativado com o certificado do Supabase (**Database → Settings → SSL Configuration → Download certificate**);
  - a tabela `fonte_orcamentos_exemplo` aparece e vira um gráfico.
- [ ] Anotar no card a mensagem de erro, se houver. Nunca a senha.
- [ ] **Power BI Desktop, por último:**
  - numa demanda aprovada, **Painel → baixar projeto do Power BI**;
  - abrir o `.pbip`, informar usuário e senha do BI e clicar em **Atualizar**;
  - o modelo carrega com relações e medidas, e os visuais mostram os mesmos números do HTML.

## Como

Passo a passo em `docs/infra/bi.md`, seções Looker Studio e Power BI.
