"""Conectores às fontes primárias. Todos abrem a fonte em modo leitura.

A plataforma nunca escreve numa fonte primária. Escrita só acontece no `Sandbox`
(DuckDB próprio da demanda) e na pasta de staging da demanda.
"""

from __future__ import annotations

import sqlite3
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


class Sandbox:
    """DuckDB da demanda. As fontes entram como views de leitura; o staging é o único lugar gravável."""

    def __init__(self, staging: Path):
        self.staging = staging
        self.staging.mkdir(parents=True, exist_ok=True)
        self.con = duckdb.connect(str(staging / "sandbox.duckdb"))
        self.fontes: dict[str, Fonte] = {}

    def anexar(self, fonte: Fonte) -> str:
        nome = f"fonte_{fonte.ident()}"
        if fonte.tipo == "arquivo":
            caminho = Path(fonte.caminho)
            if caminho.suffix.lower() == ".xlsx":
                import pandas as pd  # noqa: PLC0415  (só quando há Excel)

                df = pd.read_excel(caminho)
                self.con.register(f"_{nome}", df)
                self.con.execute(f"CREATE OR REPLACE VIEW {nome} AS SELECT * FROM _{nome}")
            else:
                self.con.execute(f"CREATE OR REPLACE VIEW {nome} AS SELECT * FROM {_leitor(caminho)}")
        elif fonte.tipo == "sqlite":
            # mode=ro: a credencial em si não permite escrita.
            uri = f"file:{fonte.caminho}?mode=ro"
            src = sqlite3.connect(uri, uri=True)
            tabelas = [r[0] for r in src.execute("SELECT name FROM sqlite_master WHERE type='table'")]
            import pandas as pd  # noqa: PLC0415

            for t in tabelas:
                df = pd.read_sql_query(f'SELECT * FROM "{t}"', src)
                self.con.register(f"_{nome}_{t}", df)
                self.con.execute(f"CREATE OR REPLACE VIEW {nome}_{t} AS SELECT * FROM _{nome}_{t}")
            src.close()
        else:
            raise ValueError(f"tipo de fonte desconhecido: {fonte.tipo}")
        self.fontes[nome] = fonte
        return nome

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
