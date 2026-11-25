"""Gerador de pipeline por trilha (card LST-15): o mesmo modelo do Arquiteto, no SQL de cada nuvem.

O Engenheiro constrói e testa o pipeline no DuckDB do sandbox. Daqui sai o mesmo pipeline traduzido para:

- `google`: BigQuery (datasets lastro_bronze, lastro_silver, lastro_gold), para o sandbox ou a camada gratuita;
- `microsoft`: T-SQL para Azure SQL Database (camada gratuita) ou Warehouse do Fabric (schemas bronze, silver, gold);
- `aws`: Athena (CTAS em Parquet no S3), o playbook medalhão.

A tradução usa o sqlglot. A prova de que ela não muda o resultado é a ida e volta (`ida_e_volta`): o SQL de
cada nuvem volta para o DuckDB, roda nos mesmos dados e o gold tem de sair igual ao do sandbox.
Isso valida a tradução, não a execução na nuvem: a primeira execução real fica registrada no playbook.
"""

from __future__ import annotations

from dataclasses import dataclass

import sqlglot
from sqlglot import exp
from sqlglot.transforms import eliminate_qualify

CAMADA = {"bronze": "bronze", "silver": "silver"}  # dimensões e fato ficam no gold


def camada_de(tabela: str) -> str:
    return CAMADA.get(tabela, "gold")


@dataclass(frozen=True)
class Trilha:
    chave: str
    dialeto: str
    arquivo: str
    nome: str


TRILHAS = {
    "google": Trilha("google", "bigquery", "pipeline_bigquery.sql", "Google · BigQuery"),
    "microsoft": Trilha("microsoft", "tsql", "pipeline_azure_sql.sql", "Microsoft · Azure SQL / Fabric"),
    "aws": Trilha("aws", "athena", "pipeline_athena.sql", "AWS · Athena"),
}


def _nome_qualificado(trilha: str, tabela: str, fonte: bool = False) -> exp.Table:
    camada = "bronze" if fonte else camada_de(tabela)
    esquema = f"lastro_{camada}" if trilha == "google" else camada
    return exp.Table(this=exp.to_identifier(tabela), db=exp.to_identifier(esquema))


def _select(sql_duckdb: str) -> tuple[str, exp.Expression]:
    """Separa `CREATE OR REPLACE TABLE x AS SELECT ...` em (x, SELECT sem QUALIFY)."""
    arvore = sqlglot.parse_one(sql_duckdb, read="duckdb")
    if not isinstance(arvore, exp.Create):
        raise ValueError(f"etapa não é CREATE TABLE AS: {sql_duckdb[:60]}")
    tabela = arvore.this.name
    # QUALIFY vira subconsulta: T-SQL e Athena não têm, e o BigQuery só aceita com WHERE.
    return tabela, eliminate_qualify(arvore.expression)


def _qualificar(select: exp.Expression, trilha: str, tabelas: set[str], fonte_view: str) -> exp.Expression:
    def troca(no: exp.Expression) -> exp.Expression:
        if isinstance(no, exp.Table) and not no.db and no.name in tabelas | {fonte_view}:
            novo = _nome_qualificado(trilha, no.name, fonte=no.name == fonte_view)
            if no.alias:
                novo.set("alias", no.args.get("alias"))
            elif no.name != fonte_view:  # colunas citadas como silver.x continuam valendo
                novo.set("alias", exp.TableAlias(this=exp.to_identifier(no.name)))
            return novo
        return no

    return select.copy().transform(troca)


def traduzir(etapas: list[tuple[str, str]], modelo: dict, trilha: str) -> str:
    """Script SQL completo para a trilha, com cabeçalho de como rodar."""
    t = TRILHAS[trilha]
    fonte_view = modelo["view"]
    tabelas = {nome for nome, _ in etapas}
    corpo: list[str] = []
    for nome, sql in etapas:
        tabela, select = _select(sql)
        select = _qualificar(select, trilha, tabelas, fonte_view)
        destino = _nome_qualificado(trilha, tabela).sql(dialect=t.dialeto)
        texto = select.sql(dialect=t.dialeto, pretty=True)
        if trilha == "google":
            corpo.append(f"-- {nome}\nCREATE OR REPLACE TABLE {destino} AS\n{texto};")
        elif trilha == "microsoft":
            corpo.append(f"-- {nome}\nDROP TABLE IF EXISTS {destino};\nSELECT * INTO {destino} FROM (\n{texto}\n) AS q;")
        else:
            local = f"s3://<bucket>/{camada_de(tabela)}/{tabela}/"
            corpo.append(
                f"-- {nome} (antes de recriar: aws s3 rm --recursive {local})\nDROP TABLE IF EXISTS {destino};\n"
                f"CREATE TABLE {destino}\nWITH (format = 'PARQUET', external_location = '{local}') AS\n{texto};"
            )
    return _cabecalho(t, modelo) + "\n\n".join(corpo) + "\n"


def _cabecalho(t: Trilha, m: dict) -> str:
    linhas = [
        f"-- Pipeline gerado pelo Lastro · {t.nome}",
        f"-- Fonte: {m['fonte']} | medida: {m['medida']} | data: {m['data']} | chave: {m['chave']} | filtro: {m['filtro'] or 'nenhum'}",
        "-- Tradução do pipeline testado no sandbox (DuckDB), conferida por ida e volta. Playbook na Caixa global.",
    ]
    if t.chave == "google":
        linhas += [
            "-- Antes: bq mk lastro_bronze && bq mk lastro_silver && bq mk lastro_gold",
            f"--        bq load --autodetect --source_format=CSV lastro_bronze.{m['view']} fonte.csv",
            "-- Rodar: bq query --use_legacy_sql=false < pipeline_bigquery.sql",
        ]
    elif t.chave == "microsoft":
        linhas += [
            "IF SCHEMA_ID('bronze') IS NULL EXEC('CREATE SCHEMA bronze');",
            "IF SCHEMA_ID('silver') IS NULL EXEC('CREATE SCHEMA silver');",
            "IF SCHEMA_ID('gold') IS NULL EXEC('CREATE SCHEMA gold');",
            f"-- Antes: importar a fonte como bronze.{m['view']} (assistente de importação ou BULK INSERT).",
        ]
    else:
        linhas += [f"-- Antes: tabela externa bronze.{m['view']} sobre o CSV no S3 (playbook medalhão); troque <bucket>."]
    return "\n".join(linhas) + "\n\n"


def gerar(etapas: list[tuple[str, str]], modelo: dict) -> dict[str, str]:
    return {k: traduzir(etapas, modelo, k) for k in TRILHAS}


def ida_e_volta(etapas: list[tuple[str, str]], modelo: dict, trilha: str) -> list[tuple[str, str]]:
    """As etapas da trilha traduzidas de volta para DuckDB (sem esquema), para comparar com o original."""
    t = TRILHAS[trilha]
    saida = []
    tabelas = {nome for nome, _ in etapas}
    for nome, sql in etapas:
        tabela, select = _select(sql)
        no_dialeto = _qualificar(select, trilha, tabelas, modelo["view"]).sql(dialect=t.dialeto)
        de_volta = sqlglot.parse_one(no_dialeto, read=t.dialeto)
        for tb in de_volta.find_all(exp.Table):
            tb.set("db", None)
        for tipo in de_volta.find_all(exp.DataType):  # VARCHAR(MAX) do T-SQL não existe no DuckDB
            if any(e.name.upper() == "MAX" for e in tipo.expressions):
                tipo.set("expressions", [])
        saida.append((nome, f"CREATE OR REPLACE TABLE {tabela}_ida AS {de_volta.sql(dialect='duckdb')}"))
    return saida
