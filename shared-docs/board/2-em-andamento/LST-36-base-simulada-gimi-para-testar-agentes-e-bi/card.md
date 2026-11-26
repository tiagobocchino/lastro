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

- [x] Gerador reprodutível (com semente) no formato bruto da API IApp, com as mesmas entidades do bruto da GIMI: contratos (com produtos aninhados), tarefas, funcionários, usuários, clientes, vendedores e grupos
- [x] 4 empresas (gimi, gbl, gpb, filial), pelo menos 2 anos de histórico, com sazonalidade e volume parecido com o real
- [x] Sujeiras que as regras tratam: registros de teste, contrato com valor 0, datas antes do corte 2024-01-01, vendedor com sufixo " - (id)" e "_", classe entre parênteses no grupo, duplicados, nulos e campos aninhados
- [x] Gabarito de vendas e carteira: tipo de venda GIMI × representante, vendedor limpo e classe
- [x] Gabarito de orçamentos: funil orçado → aprovado ou perdido, e orçado × vendido
- [x] Gabarito de produtos: classificação por prefixo de SKU
- [x] Gabarito de RH: quadro, admissões, desligamentos e vendedor ativo
- [x] A base disponível como API simulada no catálogo de conectores (iapp, com paginação real) e como arquivos brutos

## Fase 2 · Agentes contra o gabarito (Claude)

- [x] Demandas de vendas, orçamentos, produtos e RH rodadas pelos agentes, com as duas camadas
- [x] O resultado dos agentes conferido com o gabarito; cada diferença vira achado
- [x] Gold aprovado publicado no BI (LST-33) de uma empresa de teste

## Fase 3 · Power BI e Data Studio (Tiago, com os agentes)

- [ ] Tiago cria a conta do Power BI e a do Data Studio
- [ ] Conexão das duas ao BI do Lastro (`docs/infra/bi.md`)
- [ ] Painéis de teste feitos pelos agentes: projeto do Power BI (LST-34) aberto e atualizado no Desktop, e fonte e relatório no Data Studio
- [ ] Conversa com o Intérprete (LST-35) sobre os mesmos painéis, com insights provados

## Verificação

Gabarito × agentes sem diferença inexplicada, PBIP aberto no Power BI Desktop e relatório no Data Studio com os mesmos números.

## Histórico

- 25/11: escopo original (só testar o BI da lixum no Looker e no Power BI) trocado por este, a pedido do Tiago. Ainda não há bases reais conectadas.

## Evidências (25/11/2026)

- **Fase 1:** `lastro/simulados/gimi.py` e `lastro simular-gimi`. Semente 36 com 3000 contratos por empresa roda em 0,8 s. A IApp simulada serve a mesma base (`SaasSimulado(dados_base=...)`). Testes em `tests/test_gimi_simulada.py`. Commit 55ec064.
- **Fase 2:** `lastro/simulados/avaliacao.py`, relatório em `docs/testes/gimi-agentes.md`. As **8 de 8 checagens batem** com o gabarito:
  - vendido 211.290.267,16;
  - funil 3790 / 2380 / 2109 / 1243;
  - orçado 532.781.125,76;
  - itens;
  - RH por setor.

  Teste em `tests/test_avaliacao_gimi.py`. Commit b6886dc.
- **Achados (próximos cards):**
  1. coluna derivada por regra no grill (nome limpo do vendedor, tipo de venda, classe, categoria por SKU);
  2. "NAO DEFINIDO" no agrupamento (8,17 mi sem vendedor somem da tabela);
  3. contagem como medida explícita;
  4. "ativos" virando dimensão;
  5. a regra real `diego_vaz` → "Diego" perde o sobrenome (confirmar com o cliente).
- **Corrigido no caminho:** `count(*)` duplicado sem medida. A primeira planilha real do Tiago (`processos_gbl.xlsx`) não lia por três motivos, já corrigidos (commit 78949d5, nota `docs/memory/planilha-do-mundo-real.md`):
  - aspas no nome da coluna;
  - valor em texto `R$ …`;
  - painel somando o nº do processo.
- **Fase 2, BI (25/11):** empresa `gimi-teste` criada em produção, com um usuário robô admin (senha fora do repositório). Fontes, demandas 7 a 10, aprovação e publicação passaram pela API do produto. São 38 tabelas no BI. Os totais conferidos no Postgres batem com o gabarito. Painel do RH falhou: "o gold não tem coluna numérica para medir" (achado 3). Kit com PBIP, HTML e consultas do Data Studio entregue ao Tiago.

## 26/11: empresas com nomes fictícios

- No simulador, as empresas viraram alfa, beta, gama e delta; os totais continuam iguais (2cbcb46).
- No BI da gimi-teste em produção, a troca foi feita direto no banco, a pedido do Tiago.
- Publicar o BI de novo volta os nomes antigos até a base ser recarregada pelo simulador atual. Ver `docs/memory/gimi-teste-nomes-no-banco.md`.
