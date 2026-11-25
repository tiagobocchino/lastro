# BI sem atrito: levar o gold do Lastro ao Power BI e ao Data Studio sem as dores do Tiago

**Estado:** proposta (25/11/2026) · **Origem:** LST-36 fase 3. A base GIMI simulada já está no BI da empresa `gimi-teste`, que é o mesmo cenário de um cliente.

## O que aprendemos com o uso real do Tiago (sessões e repositórios dele)

| Onde | Como ele faz | O que doeu |
| --- | --- | --- |
| Power BI | Projeto PBIP com os `.tmdl` editados pelo Claude Code. Fonte `PostgreSQL.Database(host, banco)` no Neon, ou Athena por ODBC com gateway na máquina dele (`PBIEgwService`) | Depois de publicar no Serviço, a atualização falhou com `Premium_ASWL_Error: Cloud data source setting is not allowed refresh through gateway`. Depois veio "não foi possível conectar… credenciais inválidas". O ODBC obriga a ter gateway ligado no PC. O egress do Power BI custou US$ 24 em 10 dias |
| Looker Studio | **Planilha Google** como base (`RH - Base Looker Studio`). Um Apps Script monta uma tabela larga (`f_resumo_mensal`) a cada 6 h, e o Looker lê só ela | Não tem conector gratuito para Athena. O OWOX é pago, ou exige hospedar e confiar uma chave AWS a terceiro |
| Os dois | Documentação por relatório: notebook e diagramas Mermaid de linhagem, até cada visual | Manual: cada relatório exige uma sessão inteira |

**Fato técnico que agrava tudo (doc oficial do Supabase):** o certificado do banco vem de uma CA própria do Supabase (`prod-supabase.cer`, usado com `sslrootcert`). Por isso:
- o Power BI Desktop recusa o certificado até ele ser importado no Windows;
- o Data Studio exige o upload do certificado em cada fonte de dados;
- o **Serviço do Power BI** não aceita importar certificado. Resta gateway ou conexão sem criptografia, que é a mesma armadilha de setembro.

**Conclusão:** o cliente não deve depender de certificado, gateway nem SQL para ver o gold. O Postgres continua como caminho avançado.

## Estratégia em três frentes

### 1. Uma tabela pronta por demanda (vale para tudo, custo baixo)

- Em cada publicação, além do esquema estrela, o BI ganha `painel_<n>_<assunto>`: fato já ligada às dimensões, nomes de coluna legíveis, data como `date`, "NAO DEFINIDO" no lugar de nulo e uma coluna `registros = 1` para contar.
- É o padrão `f_resumo_mensal` que o Tiago já usa no Looker: o usuário escolhe **uma tabela**, sem consulta personalizada e sem relações.
- O PBIP continua usando o esquema estrela; a tabela larga é para quem monta à mão.
- Resolve também o achado da contagem: o RH vira "soma de registros".

### 2. Power BI por HTTPS, sem certificado e sem gateway

- O Lastro serve cada tabela do BI em `https://<api>/bi/v1/<tabela>.parquet`. O certificado é o do Render, emitido por CA pública e aceito pelo Windows e pela Microsoft.
- A autenticação é uma **chave de leitura do BI** por empresa: revogável, só leitura, a mesma regra da credencial Postgres. Ela vai no cabeçalho da requisição.
- O PBIP gerado passa a usar `Parquet.Document(Web.Contents(Api, [RelativePath = ..., Headers = ...]))`, com a URL base fixa. O Serviço atualiza na nuvem **sem gateway**; a credencial no Serviço é "Anônimo" e a chave vai no cabeçalho.
- O Lastro também gera um arquivo `.pbids` (fonte de dados do Power BI): dois cliques abrem o Desktop com a conexão preenchida.
- O Postgres direto fica como opção "avançado/DirectQuery", com o guia de certificado.
- **A validar no teste do Tiago:** atualização agendada no Serviço com fonte Web e cabeçalho fixo; e o volume, já que o egress do Render no plano gratuito tem limite.

### 3. Data Studio pela planilha Google, o caminho que o Tiago já usa

- Opção "Enviar para o Google Sheets": a cada publicação, o Lastro grava as tabelas `painel_*` numa planilha **do próprio cliente**.
  - O cliente autoriza com OAuth e escopo `drive.file`, que só alcança arquivos criados pelo Lastro. O fluxo OAuth do Google já existe no LST-14.
  - O cliente liga o Data Studio na planilha com o conector nativo, gratuito, sem certificado e sem senha de banco.
- Limite: a planilha aceita 10 milhões de células. A tabela de itens da GIMI simulada tem 13 mil linhas × 6 colunas, bem abaixo. Acima disso, o portal sugere o caminho Postgres ou BigQuery.
- Depois: um **conector de comunidade do Lastro** (Apps Script) na galeria do Data Studio. O usuário escolhe "Lastro", cola a chave de leitura e escolhe a tabela. É o que o OWOX vende, só que para o nosso gold.

### De brinde: documentação automática de linhagem

- O Lastro já sabe a origem de cada coluna: fonte → silver → gold → visual.
- Gerar, junto do painel, o diagrama Mermaid de linhagem e o notebook de conferência faz automaticamente o que o Tiago hoje faz à mão por relatório.

## Tela "Conectar ao BI" do portal (como fica para o usuário)

1. O usuário escolhe a ferramenta: **Power BI**, **Data Studio** ou **Outro (Postgres)**.
2. **Power BI:** baixar o projeto pronto (PBIP) ou o atalho `.pbids`, e copiar a chave de leitura. Sem certificado.
3. **Data Studio:** "Enviar para minha planilha Google". A tela mostra o link da planilha e os 3 cliques no Data Studio.
4. **Postgres:** os dados de hoje, com o guia de certificado.
5. **Conferência:** para cada tabela, o portal mostra o total de controle, por exemplo "vendido 211.290.267,16". O usuário compara com o cartão do painel e sabe na hora se está certo.
6. **Erros conhecidos:** cada mensagem real tem a sua correção. Entram o `Premium_ASWL_Error`, o certificado não confiável e as credenciais inválidas.

## Cards propostos

| Card | Escopo | Depende |
| --- | --- | --- |
| A · Tabela pronta por demanda | `painel_<n>_*` na publicação do BI, `registros`, NAO DEFINIDO e testes | — |
| B · Power BI por HTTPS | endpoint Parquet com chave de leitura, PBIP com `Web.Contents`, `.pbids` e teste no Serviço | A |
| C · Data Studio pela planilha Google | envio para planilha do cliente com `drive.file`, a cada publicação, e guia de 3 cliques | A |
| D · Conectar ao BI, a tela | escolha da ferramenta, conferência por total de controle e tabela de erros conhecidos | B, C |
| E · Linhagem automática | Mermaid e notebook de conferência por painel | — |
| (depois) Conector de comunidade do Lastro | Apps Script na galeria do Data Studio | C |

**Validação de cada card:** o Tiago conecta a empresa `gimi-teste` pela ferramenta e confere os totais de controle (vendido 211.290.267,16; orçado 532.781.125,76; 239 funcionários ativos). Se bater nas duas ferramentas, o caminho vale para o cliente.
