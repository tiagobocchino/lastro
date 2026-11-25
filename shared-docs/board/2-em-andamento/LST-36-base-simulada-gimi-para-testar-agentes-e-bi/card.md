---
chave: LST-36
jira: https://adelecrm.atlassian.net/browse/LST-36
secao: INT
status: em-andamento
especialista: tiago
---

# Base simulada no padrão GIMI (vendas, orçamentos e RH) para testar os agentes e conectar Power BI e Data Studio

**Responsáveis:** Tiago (contas e conexões) e Claude (base, agentes e painéis).
**Fecha:** o LST-34 (PBIP aberto no Power BI) e confirma o LST-33 com um BI real.

**Por quê:** ainda não há bases de clientes conectadas. Para medir a potência dos agentes, vamos montar aqui uma base **sintética**, no mesmo formato bruto que recebemos da GIMI (antes do tratamento), com as nossas regras de vendas, orçamentos e RH. Depois, usar os agentes para construir os painéis de teste no Power BI e no Data Studio.

**Regra de ouro:** nenhum dado real da GIMI. Nomes, CNPJs, valores e contratos são gerados. Copiamos só o **formato** e as **regras**, lidos da estrutura do repositório `engenhadev-iapp-powerbi-etl`.

## Fase 1 · Base simulada (Claude)

- [ ] Gerador reprodutível (com semente) no formato bruto da API IApp, com as mesmas entidades do bruto da GIMI: contratos (com produtos aninhados), tarefas, funcionários, usuários, clientes, vendedores e grupos
- [ ] 4 empresas (gimi, gbl, gpb, filial), pelo menos 2 anos de histórico, com sazonalidade e volume parecido com o real
- [ ] Sujeiras que as regras tratam: registros de teste, contrato com valor 0, datas antes do corte 2024-01-01, vendedor com sufixo " - (id)" e "_", classe entre parênteses no grupo, duplicados, nulos e campos aninhados
- [ ] Gabarito de vendas e carteira: tipo de venda GIMI × representante, vendedor limpo e classe
- [ ] Gabarito de orçamentos: funil orçado → aprovado ou perdido, e orçado × vendido
- [ ] Gabarito de produtos: classificação por prefixo de SKU
- [ ] Gabarito de RH: quadro, admissões, desligamentos e vendedor ativo
- [ ] A base disponível como API simulada no catálogo de conectores (iapp, com paginação real) e como arquivos brutos

## Fase 2 · Agentes contra o gabarito (Claude)

- [ ] Demandas de vendas, orçamentos, produtos e RH rodadas pelos agentes, com as duas camadas
- [ ] O resultado dos agentes conferido com o gabarito; cada diferença vira achado
- [ ] Gold aprovado publicado no BI (LST-33) de uma empresa de teste

## Fase 3 · Power BI e Data Studio (Tiago, com os agentes)

- [ ] Tiago cria a conta do Power BI e a do Data Studio
- [ ] Conexão das duas ao BI do Lastro (`docs/infra/bi.md`)
- [ ] Painéis de teste feitos pelos agentes: projeto do Power BI (LST-34) aberto e atualizado no Desktop, e fonte e relatório no Data Studio
- [ ] Conversa com o Intérprete (LST-35) sobre os mesmos painéis, com insights provados

## Verificação

Gabarito × agentes sem diferença inexplicada, PBIP aberto no Power BI Desktop e relatório no Data Studio com os mesmos números.

## Histórico

- 25/11: escopo original (só testar o BI da lixum no Looker e no Power BI) trocado por este, a pedido do Tiago. Ainda não há bases reais conectadas.
