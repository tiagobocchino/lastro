# Conectar as bases do Lastro a um BI (card LST-33)

Cada empresa liga o próprio acesso de BI no portal, em **conta → Conectar ao BI**. Só o admin faz isso.

## O que o BI enxerga

Um schema só, com o mesmo nome do usuário (`bi_<10 letras e números>`). O nome não revela a empresa. Dentro dele:

| Tabela | De onde vem |
| --- | --- |
| `fonte_<nome>` | cada fonte de arquivo da empresa. Numa fonte SQLite, uma tabela por tabela |
| `d<id>_fato`, `d<id>_dim_*` | o gold de cada demanda **aprovada**, em esquema estrela: a fato liga nas dimensões pelas colunas `*_id` |
| `d<id>_silver` | a tabela limpa da demanda, antes do modelo dimensional |

O Lastro atualiza essas tabelas:
- quando o admin clica em **publicar agora**;
- depois de cada carga agendada boa (LST-7);
- depois de cada demanda aprovada.

A troca acontece numa transação só: o BI vê a versão antiga inteira ou a nova inteira. Cada tabela tem limite de 1 milhão de linhas (o banco gratuito tem 500 MB); se passar disso, a tabela é cortada e o portal avisa.

## O que o usuário do BI não consegue fazer

As travas valem no próprio Postgres e são testadas em `tests/test_postgres.py`:
- ler o schema de outra empresa, as tabelas do Lastro (`usuarios`, `demandas`…), o `interno` ou o Vault;
- gravar, apagar ou criar tabela, mesmo desligando o modo só leitura da sessão (falta o privilégio);
- ficar numa consulta por mais de 120 segundos, ou abrir mais de 5 conexões.

A senha aparece **uma única vez**, ao ligar o BI ou ao trocar a senha. No banco fica só o hash do Postgres. Na hora, o Lastro entra com a credencial nova pelo mesmo caminho do BI e mostra o resultado na tela.

## Dados de conexão

O portal mostra cada um com botão de copiar:

| Campo | Valor em produção |
| --- | --- |
| Servidor | host do Session pooler do Supabase (`aws-…-sa-east-1.pooler.supabase.com`) |
| Porta | `5432`, o modo sessão, que aceita os BIs |
| Banco | `postgres` |
| Usuário | `bi_xxxxxxxxxx.<ref do projeto>` |
| SSL | obrigatório |

## Power BI Desktop (gratuito)

1. **Página Inicial → Obter dados → Banco de dados PostgreSQL**.
2. Servidor: `HOST:5432`. Banco de dados: `postgres`. Modo: **Importar**, ou DirectQuery se quiser sempre o dado da hora.
3. Credenciais: aba **Banco de dados**, com o usuário e a senha do portal.
4. Marque as tabelas `d<id>_fato` e `d<id>_dim_*`. As relações saem pelas colunas `*_id`.

O Power BI Desktop pode recusar o certificado do Supabase ("a cadeia de certificados foi emitida por uma autoridade que não é confiável"). Se acontecer, há duas saídas:
- baixe o certificado em **Supabase → Database → Settings → SSL Configuration → Download certificate** e importe no Windows em **Autoridades de Certificação Raiz Confiáveis**;
- ou aceite a conexão sem criptografia quando o Power BI perguntar. Prefira a primeira.

## Looker Studio (gratuito)

**Adicionar dados → PostgreSQL**. Preencha host, porta 5432, banco, usuário e senha, e marque **Ativar SSL**. Cada tabela vira uma fonte de dados. Para juntar fato e dimensões, use **Combinar dados** ou uma consulta personalizada.

## Metabase OSS (gratuito, testado)

**Admin → Bancos de dados → Adicionar → PostgreSQL**, com os mesmos dados e SSL.

Testado em 25/11 com o Metabase v0.52.4 (Docker) contra o Postgres local, usando a credencial que o portal gerou:
- o Metabase listou só o schema da empresa, com 9 tabelas;
- o total vendido saiu igual ao da auditoria, 14.030.477,92;
- ler a outra empresa, gravar e ler os usuários do Lastro deu erro de permissão.

## Sem conector de banco

Em **conta → Exportar fontes**, o admin ou o demandante baixa cada fonte em **CSV** (Excel, Google Sheets, upload no Looker Studio) ou **Parquet** (Power BI, Python). É uma cópia: a fonte original não é alterada.

## Desligar

Use **desligar** no portal: o usuário perde o login na hora. Ao ligar de novo, o usuário e o schema continuam os mesmos e a senha é nova.
