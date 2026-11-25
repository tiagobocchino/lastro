"""Conectores às fontes primárias. Todos abrem a fonte em modo leitura.

A plataforma nunca escreve numa fonte primária. Escrita só acontece no `Sandbox`
(DuckDB próprio da demanda) e na pasta de staging da demanda.
"""

from __future__ import annotations

import sqlite3
import tempfile
from dataclasses import dataclass
from pathlib import Path

import duckdb

from .somente_leitura import verificar

EXTENSOES = {".csv", ".parquet", ".xlsx", ".json"}


@dataclass
class Fonte:
    nome: str
    tipo: str  # arquivo | sqlite
    caminho: str

    def ident(self) -> str:
        return "".join(c if c.isalnum() else "_" for c in self.nome.lower()).strip("_")


def _leitor(caminho: Path) -> str:
    p = str(caminho).replace("'", "''")
    suf = caminho.suffix.lower()
    if suf == ".csv":
        return f"read_csv_auto('{p}', header=true)"
    if suf == ".parquet":
        return f"read_parquet('{p}')"
    if suf == ".json":
        return f"read_json_auto('{p}')"
    raise ValueError(f"extensão não suportada: {suf}")


def nome_seguro(nome: object, posicao: int = 0) -> str:
    """Nome de coluna que atravessa SQL, grill e painel sem quebrar: sem aspas, sem quebra de linha,
    espaços colapsados. Cabeçalho vazio (ou o "Unnamed: n" do pandas) vira coluna_<posição>."""
    texto = " ".join(str(nome if nome is not None else "").replace('"', "").replace("`", "").split())
    if not texto or texto.lower().startswith("unnamed:"):
        return f"coluna_{posicao + 1}"
    return texto


def _renomear_colunas(con: duckdb.DuckDBPyConnection, tabela: str) -> None:
    """Planilha do mundo real (LST-36): aspas, quebra de linha, cabeçalho vazio e nome repetido."""
    atuais = [r[0] for r in con.execute(f"DESCRIBE {tabela}").fetchall()]
    usados: set[str] = set()
    for i, atual in enumerate(atuais):
        novo = base = nome_seguro(atual, i)
        n = 2
        while novo.lower() in usados:
            novo, n = f"{base}_{n}", n + 1
        usados.add(novo.lower())
        if novo != atual:
            antigo = atual.replace('"', '""')
            con.execute(f'ALTER TABLE {tabela} RENAME COLUMN "{antigo}" TO "{novo}"')


# "R$ 1.234,56", "R$ 526530", "1.234,56": número em formato brasileiro gravado como texto.
_MOEDA = r"^-?\s*(R\$)?\s*-?\s*([0-9]{1,3}(\.[0-9]{3})+|[0-9]+)(,[0-9]+)?$"


def _converter_moeda(con: duckdb.DuckDBPyConnection, tabela: str) -> None:
    """Coluna de texto em que todo valor preenchido é número brasileiro (com ou sem R$) vira DOUBLE.
    Basta um valor que não seja número para a coluna ficar como está; sem R$ nem vírgula, também fica
    (código como "0012" não é valor)."""
    for col, tipo, *_ in con.execute(f"DESCRIBE {tabela}").fetchall():
        if tipo != "VARCHAR":
            continue
        q = '"' + col.replace('"', '""') + '"'
        v = f"trim({q})"
        preenchidos, casam, marcados = con.execute(
            f"SELECT count({q}) FILTER (WHERE {v} <> ''), count(*) FILTER (WHERE regexp_matches({v}, '{_MOEDA}')), "
            f"count(*) FILTER (WHERE {v} LIKE '%R$%' OR {v} LIKE '%,%') FROM {tabela}"
        ).fetchone() or (0, 0, 0)
        if not preenchidos or casam != preenchidos or not marcados:
            continue
        limpo = f"replace(replace(replace(replace({v}, 'R$', ''), ' ', ''), '.', ''), ',', '.')"
        con.execute(f"ALTER TABLE {tabela} ALTER COLUMN {q} TYPE DOUBLE USING "
                    f"CASE WHEN {v} = '' THEN NULL ELSE CAST({limpo} AS DOUBLE) END")


class Sandbox:
    """DuckDB da demanda. As fontes são copiadas para dentro dele e, depois de `travar`, nenhum
    SQL alcança disco, rede ou outra empresa: só a pasta da própria demanda (onde o pipeline grava o gold).

    O arquivo do DuckDB fica no disco local do container, fora do staging: o staging pode ser
    um bucket do Cloud Storage montado como volume (ADR 0007), ruim para escrita aleatória.
    """

    def __init__(self, staging: Path, gravavel: Path | None = None):
        self.staging = staging.resolve()
        self.staging.mkdir(parents=True, exist_ok=True)
        # Única pasta que o DuckDB alcança depois de travar: a da demanda (staging, gold, relatório).
        self.gravavel = (gravavel or staging).resolve()
        self._tmp = tempfile.TemporaryDirectory(prefix="lastro-sandbox-")
        self.con = duckdb.connect(str(Path(self._tmp.name) / "sandbox.duckdb"))
        self.fontes: dict[str, Fonte] = {}
        self.travado = False

    def anexar(self, fonte: Fonte) -> str:
        if self.travado:
            raise PermissionError("sandbox travado: as fontes entram antes de travar")
        nome = f"fonte_{fonte.ident()}"
        if fonte.tipo == "arquivo":
            caminho = Path(fonte.caminho)
            if caminho.suffix.lower() == ".xlsx":
                import pandas as pd  # noqa: PLC0415  (só quando há Excel)

                df = pd.read_excel(caminho)
                self.con.register(f"_{nome}", df)
                self.con.execute(f"CREATE OR REPLACE TABLE {nome} AS SELECT * FROM _{nome}")
                self.con.unregister(f"_{nome}")
            else:
                self.con.execute(f"CREATE OR REPLACE TABLE {nome} AS SELECT * FROM {_leitor(caminho)}")
        elif fonte.tipo == "sqlite":
            # mode=ro: a credencial em si não permite escrita.
            uri = f"file:{fonte.caminho}?mode=ro"
            src = sqlite3.connect(uri, uri=True)
            tabelas = [r[0] for r in src.execute("SELECT name FROM sqlite_master WHERE type='table'")]
            import pandas as pd  # noqa: PLC0415

            for t in tabelas:
                df = pd.read_sql_query(f'SELECT * FROM "{t}"', src)
                self.con.register(f"_{nome}_{t}", df)
                self.con.execute(f"CREATE OR REPLACE TABLE {nome}_{t} AS SELECT * FROM _{nome}_{t}")
                self.con.unregister(f"_{nome}_{t}")
            src.close()
        else:
            raise ValueError(f"tipo de fonte desconhecido: {fonte.tipo}")
        if fonte.tipo == "arquivo":
            _renomear_colunas(self.con, nome)
            _converter_moeda(self.con, nome)
        self.fontes[nome] = fonte
        return nome

    def travar(self) -> None:
        """Segunda linha de defesa, além da trava de SQL: daqui em diante o DuckDB só enxerga o
        staging. Sem leitura de arquivo de fora, sem rede, sem extensão, sem mudar a configuração."""
        pasta = self.gravavel.as_posix().replace("'", "''")
        self.con.execute(f"SET allowed_directories = ['{pasta}/']")
        self.con.execute("SET enable_external_access = false")
        self.con.execute("SET autoinstall_known_extensions = false")
        self.con.execute("SET autoload_known_extensions = false")
        self.con.execute("SET lock_configuration = true")
        self.travado = True

    def consultar(self, sql: str) -> tuple[list[str], list[tuple]]:
        """Consulta de agente: passa pela trava de somente leitura."""
        verificar(sql)
        cur = self.con.execute(sql)
        colunas = [d[0] for d in cur.description]
        return colunas, cur.fetchall()

    def executar_pipeline(self, sql: str) -> None:
        """Só o pipeline gerado e aprovado escreve, e só dentro do sandbox (staging)."""
        self.con.execute(sql)

    def fechar(self) -> None:
        self.con.close()
        self._tmp.cleanup()
