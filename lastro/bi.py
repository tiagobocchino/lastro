"""BI self-service por empresa (card LST-33): as bases e o gold do Lastro num Postgres que qualquer BI lê.

Cada empresa que liga o BI ganha um schema e um papel com o mesmo nome opaco (`bi_<10 hex>`):
- o papel só tem SELECT no próprio schema, com `default_transaction_read_only`, tempo máximo por consulta
  e limite de conexões. Não alcança `public`, `interno`, o Vault nem o schema de outra empresa;
- o nome não diz de qual empresa é, porque `pg_namespace` e `pg_roles` são legíveis por qualquer papel.

O que vai para o BI (publicação atômica, numa transação só):
- cada fonte da empresa vira `fonte_<nome>` (uma tabela por tabela, quando a fonte é um SQLite);
- cada demanda aprovada vira `d<id>_fato`, `d<id>_dim_*` e `d<id>_silver`: o esquema estrela do gold.

A senha volta uma única vez, para o admin copiar; no banco fica só o hash SCRAM do próprio Postgres.
"""

from __future__ import annotations

import re
import secrets
import sqlite3
import unicodedata
from collections.abc import Iterator
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import duckdb

LIMITE_LINHAS = 1_000_000  # por tabela: o banco gratuito do Supabase tem 500 MB
LOTE = 5_000
NOME_ACESSO = re.compile(r"^bi_[a-f0-9]{10}$")

TIPOS = {  # DuckDB → Postgres; o que não estiver aqui vai como texto
    "BOOLEAN": "boolean", "TINYINT": "smallint", "SMALLINT": "smallint", "INTEGER": "integer", "BIGINT": "bigint",
    "UTINYINT": "smallint", "USMALLINT": "integer", "UINTEGER": "bigint", "UBIGINT": "numeric", "HUGEINT": "numeric",
    "FLOAT": "real", "DOUBLE": "double precision", "DATE": "date", "TIME": "time", "TIMESTAMP": "timestamp",
    "TIMESTAMP WITH TIME ZONE": "timestamptz", "TIMESTAMP_NS": "timestamp", "TIMESTAMP_MS": "timestamp",
    "TIMESTAMP_S": "timestamp", "VARCHAR": "text", "UUID": "uuid",
}


def normalizar_chave(chave: str) -> str:
    """Espaço, aspas e caractere invisível nas pontas e maiúscula não contam: o HTTP corta espaços do cabeçalho e o
    usuário cola a chave à mão no Power BI (achado de 26/11: o valor chegava sem começar por lst_)."""
    return (chave or "").strip().strip("\"'\u200b\ufeff\u00a0").strip().lower()


def hash_chave(chave: str) -> str:
    import hashlib

    return hashlib.sha256(normalizar_chave(chave).encode()).hexdigest()


class BIIndisponivel(RuntimeError):
    """O BI pela conexão SQL precisa do Postgres (produção); no modo local (SQLite) não existe."""


def ident(nome: str, prefixo: str = "c") -> str:
    """Nome seguro e legível no BI: minúsculas, sem acento, só letras, números e _."""
    s = unicodedata.normalize("NFKD", str(nome)).encode("ascii", "ignore").decode().lower()
    s = re.sub(r"[^a-z0-9]+", "_", s).strip("_") or prefixo
    if s[0].isdigit():
        s = f"{prefixo}_{s}"
    return s[:55]


def tipo_pg(tipo_duckdb: str) -> str:
    t = tipo_duckdb.upper()
    if t.startswith("DECIMAL"):
        return t.replace("DECIMAL", "numeric")
    return TIPOS.get(t, "text")


@dataclass
class Tabela:
    nome: str
    origem: str
    ler: Any = field(repr=False)  # (con duckdb) -> relação


def _rel_arquivo(caminho: Path):
    suf = caminho.suffix.lower()
    p = str(caminho).replace("'", "''")

    def ler(con: duckdb.DuckDBPyConnection):
        if suf == ".xlsx":
            import pandas as pd

            df = pd.read_excel(caminho)
            con.register("_xlsx", df)
            return con.sql("SELECT * FROM _xlsx")
        leitor = {".csv": f"read_csv_auto('{p}', header=true)", ".parquet": f"read_parquet('{p}')",
                  ".json": f"read_json_auto('{p}')"}.get(suf)
        if not leitor:
            raise ValueError(f"extensão não suportada no BI: {suf}")
        return con.sql(f"SELECT * FROM {leitor}")

    return ler


def _rel_sqlite(caminho: str, tabela: str):
    def ler(con: duckdb.DuckDBPyConnection):
        import pandas as pd

        src = sqlite3.connect(f"file:{caminho}?mode=ro", uri=True)  # a fonte só em leitura, como no Sandbox
        try:
            df = pd.read_sql_query(f'SELECT * FROM "{tabela}"', src)
        finally:
            src.close()
        con.register("_sqlite", df)
        return con.sql("SELECT * FROM _sqlite")

    return ler


def _rel_painel(gold: Path):
    """LST-46: a fato já ligada às dimensões, numa tabela só: o usuário escolhe uma tabela, sem relações nem SQL.
    Vazio continua vazio (ADR 0011: rótulo para o vazio é regra do cliente). `registros = 1` permite contar."""
    def q(p: Path) -> str:
        return str(p).replace("'", "''")

    def ler(con: duckdb.DuckDBPyConnection):
        fato = gold / "fato.parquet"
        cols = [r[0] for r in con.sql(f"DESCRIBE SELECT * FROM read_parquet('{q(fato)}')").fetchall()]
        sel, juncoes = [], []
        for c in cols:
            dim = gold / f"dim_{c[:-3]}.parquet"
            if c.endswith("_id") and dim.exists():
                n = c[:-3]
                juncoes.append(f'LEFT JOIN read_parquet(\'{q(dim)}\') AS "d_{n}" ON "d_{n}"."{c}" = f."{c}"')
                sel.append(f'"d_{n}"."{n}"')
            elif c == "data":
                sel += ["CAST(f.data AS DATE) AS data", "year(f.data) AS ano", "month(f.data) AS mes",
                        "strftime(f.data, '%Y-%m') AS ano_mes"]
            else:
                sel.append(f'f."{c}"')
        sel.append("1 AS registros")
        return con.sql(f"SELECT {', '.join(sel)} FROM read_parquet('{q(fato)}') AS f {' '.join(juncoes)}")

    return ler


def tabelas_da_empresa(repo: Any, pasta: Path) -> list[Tabela]:
    """Tudo o que a empresa tem pronto para o BI: fontes e o gold das demandas aprovadas."""
    out: list[Tabela] = []
    for f in repo.fontes():
        base = f"fonte_{ident(f['nome'], 'f')}"
        if f["tipo"] == "arquivo" and Path(f["caminho"]).exists():
            out.append(Tabela(base, f"fonte {f['nome']}", _rel_arquivo(Path(f["caminho"]))))
        elif f["tipo"] == "sqlite" and Path(f["caminho"]).exists():
            src = sqlite3.connect(f"file:{f['caminho']}?mode=ro", uri=True)
            nomes = [r[0] for r in src.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")]
            src.close()
            out += [Tabela(f"{base}_{ident(t)}"[:60], f"fonte {f['nome']} · {t}", _rel_sqlite(f["caminho"], t)) for t in nomes]
    for d in repo.demandas():
        if d["status"] != "aprovada":
            continue
        gold = pasta / "demandas" / str(d["id"]) / "gold"
        for arq in sorted(gold.glob("*.parquet")):
            out.append(Tabela(f"d{d['id']}_{ident(arq.stem)}", f"demanda {d['id']} · {arq.stem}", _rel_arquivo(arq)))
        if (gold / "fato.parquet").exists():
            nome = f"painel_{d['id']}_{ident(d['pergunta'])}"[:60].rstrip("_")
            out.append(Tabela(nome, f"demanda {d['id']} · tabela pronta (fato + dimensões)", _rel_painel(gold)))
    vistos: dict[str, int] = {}
    for t in out:  # nomes únicos mesmo com fontes de nomes parecidos
        n = vistos.get(t.nome, 0)
        vistos[t.nome] = n + 1
        if n:
            t.nome = f"{t.nome[:57]}_{n + 1}"
    return out


def sem_arquivo(repo: Any, pasta: Path) -> dict[str, str]:
    """Prefixo de tabela → origem, para o que está no banco mas cujo arquivo não existe mais neste servidor
    (disco efêmero: um deploy no Render zera a pasta). A publicação mantém essas tabelas em vez de apagar o BI."""
    faltam: dict[str, str] = {}
    for f in repo.fontes():
        if f["tipo"] in ("arquivo", "sqlite") and not Path(f["caminho"]).exists():
            faltam[f"fonte_{ident(f['nome'], 'f')}"] = f"fonte {f['nome']}"
    for d in repo.demandas():
        if d["status"] == "aprovada" and not (pasta / "demandas" / str(d["id"]) / "gold" / "fato.parquet").exists():
            faltam[f"d{d['id']}_"] = faltam[f"painel_{d['id']}_"] = f"demanda {d['id']}"
    return faltam


def _colunas(rel: Any) -> list[tuple[str, str]]:
    usados: dict[str, int] = {}
    cols = []
    for nome, tipo in zip(rel.columns, rel.types):
        c = ident(nome)
        usados[c] = usados.get(c, 0) + 1
        if usados[c] > 1:
            c = f"{c[:52]}_{usados[c]}"
        cols.append((c, tipo_pg(str(tipo))))
    return cols


def _linhas(con: duckdb.DuckDBPyConnection, rel: Any, limite: int) -> Iterator[tuple]:
    """Em lotes, por cursor: uma relação do DuckDB não guarda resultado entre chamadas."""
    cur = con.execute(rel.limit(limite).sql_query())
    while lote := cur.fetchmany(LOTE):
        yield from lote


class AcessoBI:
    """Opera o BI de uma empresa no Postgres, sempre pela conexão do dono do banco."""

    def __init__(self, banco: Any, url_banco: str = ""):
        if not hasattr(banco, "pool"):
            raise BIIndisponivel("o BI pela conexão SQL só existe com o banco Postgres (produção)")
        self.banco = banco
        self.url_banco = url_banco

    # ---- registro -------------------------------------------------------------------
    def acesso(self, tenant: str) -> dict | None:
        with self.banco._dono() as con:
            r = con.execute("SELECT tenant_id, nome, ativo, criado_em, senha_trocada_em, publicado_em, tabelas, "
                            "chave_hash IS NOT NULL AS chave_ativa, chave_criada_em, chave_usada_em "
                            "FROM interno.bi_acessos WHERE tenant_id=%s", (tenant,)).fetchone()
        return dict(r) if r else None

    def conexao(self, nome: str) -> dict:
        """Dados de conexão para o BI: mesmo host do banco, porta 5432 (Session pooler, aceita os BIs)."""
        from psycopg.conninfo import conninfo_to_dict

        info = conninfo_to_dict(self.url_banco) if self.url_banco else {}
        host = str(info.get("host", ""))
        usuario_base = str(info.get("user", ""))
        sufixo = usuario_base.split(".", 1)[1] if "." in usuario_base else ""  # postgres.<ref> no pooler
        porta = 5432 if "pooler.supabase.com" in host else int(info.get("port", 5432) or 5432)
        return {"host": host, "porta": porta, "banco": str(info.get("dbname", "postgres")),
                "usuario": f"{nome}.{sufixo}" if sufixo else nome, "ssl": "obrigatório" if "supabase" in host else "opcional"}

    # ---- credencial -----------------------------------------------------------------
    def gerar_credencial(self, tenant: str) -> dict:
        """Liga o BI (ou troca a senha, se já existe). A senha volta só aqui, uma vez."""
        from psycopg import sql

        senha = secrets.token_urlsafe(24)
        atual = self.acesso(tenant)
        nome = atual["nome"] if atual else f"bi_{secrets.token_hex(5)}"
        if not NOME_ACESSO.match(nome):
            raise ValueError("nome de acesso inválido")
        n = sql.Identifier(nome)
        with self.banco._dono() as con:
            existe = con.execute("SELECT 1 FROM pg_roles WHERE rolname=%s", (nome,)).fetchone()
            if existe:
                con.execute(sql.SQL("ALTER ROLE {} LOGIN PASSWORD {}").format(n, sql.Literal(senha)))
            else:
                con.execute(sql.SQL("CREATE ROLE {} LOGIN NOINHERIT CONNECTION LIMIT 5 PASSWORD {}").format(n, sql.Literal(senha)))
            con.execute(sql.SQL("ALTER ROLE {} SET default_transaction_read_only = on").format(n))
            con.execute(sql.SQL("ALTER ROLE {} SET statement_timeout = '120s'").format(n))
            con.execute(sql.SQL("ALTER ROLE {} SET search_path = {}").format(n, n))
            con.execute(sql.SQL("CREATE SCHEMA IF NOT EXISTS {}").format(n))
            con.execute(sql.SQL("REVOKE ALL ON SCHEMA {} FROM PUBLIC").format(n))
            con.execute(sql.SQL("GRANT USAGE ON SCHEMA {} TO {}").format(n, n))
            con.execute(sql.SQL("GRANT SELECT ON ALL TABLES IN SCHEMA {} TO {}").format(n, n))
            con.execute(
                "INSERT INTO interno.bi_acessos (tenant_id, nome) VALUES (%s, %s) "
                "ON CONFLICT (tenant_id) DO UPDATE SET ativo = true, senha_trocada_em = now()",
                (tenant, nome),
            )
        return self.conexao(nome) | {"senha": senha}

    def testar(self, cred: dict) -> dict:
        """Entra com a credencial do BI pelo mesmo caminho que o BI usa (pooler, SSL) e lista as tabelas."""
        import psycopg

        try:
            with psycopg.connect(host=cred["host"], port=cred["porta"], dbname=cred["banco"], user=cred["usuario"],
                                 password=cred["senha"], connect_timeout=15, prepare_threshold=None,
                                 sslmode="require" if cred["ssl"] == "obrigatório" else "prefer") as con:
                n = con.execute("SELECT count(*) FROM information_schema.tables WHERE table_schema = current_schema()").fetchone()[0]
                so_leitura = con.execute("SHOW default_transaction_read_only").fetchone()[0] == "on"
            return {"ok": True, "detalhe": f"conexão aceita: {n} tabelas visíveis, sessão só leitura: {'sim' if so_leitura else 'não'}"}
        except Exception as e:  # noqa: BLE001
            return {"ok": False, "detalhe": f"o BI não conseguiu entrar ({type(e).__name__}): {str(e).splitlines()[0][:160]}"}

    # ---- chave de leitura por HTTPS (LST-47) ------------------------------------------
    def gerar_chave(self, tenant: str) -> str:
        """Liga (ou troca) a chave de leitura do BI por HTTPS. Só o hash fica no banco; a chave volta só aqui."""
        atual = self.acesso(tenant)
        if not atual or not atual["ativo"]:
            raise BIIndisponivel("ligue o BI da empresa antes de gerar a chave de leitura")
        chave = f"lst_{secrets.token_hex(24)}"  # só minúsculas e números: nada se perde ao copiar ou digitar
        with self.banco._dono() as con:
            con.execute("UPDATE interno.bi_acessos SET chave_hash = %s, chave_criada_em = now(), chave_usada_em = NULL "
                        "WHERE tenant_id = %s", (hash_chave(chave), tenant))
        return chave

    def revogar_chave(self, tenant: str) -> None:
        with self.banco._dono() as con:
            con.execute("UPDATE interno.bi_acessos SET chave_hash = NULL, chave_criada_em = NULL WHERE tenant_id = %s", (tenant,))

    def pela_chave(self, chave: str | None, agente: str = "") -> dict | None:
        """Empresa e schema donos da chave, se ela vale (BI ligado). Busca pelo hash: a chave nunca é comparada em claro.
        Recusa grava só o motivo (nunca a chave), para o suporte saber se faltou cabeçalho ou a chave não confere."""
        c = normalizar_chave(chave or "")
        motivo = "sem_cabecalho" if not c else "prefixo" if not c.startswith("lst_") or len(c) > 100 else None
        r = None
        with self.banco._dono() as con:
            if not motivo:
                r = con.execute("UPDATE interno.bi_acessos SET chave_usada_em = now() WHERE chave_hash = %s AND ativo "
                                "RETURNING tenant_id, nome", (hash_chave(c),)).fetchone()
                motivo = None if r else "desconhecida"
            if motivo:
                # pista sem a chave: tamanho e os 3 primeiros caracteres só quando nem começa com lst_ (então não é chave)
                pista = f" | tam={len(c)} inicio={c[:3]!r}" if motivo == "prefixo" else ""
                con.execute("INSERT INTO interno.bi_recusas (motivo, agente) VALUES (%s, %s)", (motivo, (agente or "")[:120] + pista))
        return dict(r) if r else None

    def tabelas_publicadas(self, esquema: str) -> list[str]:
        with self.banco._dono() as con:
            return [r["tablename"] for r in con.execute(
                "SELECT tablename FROM pg_tables WHERE schemaname = %s ORDER BY tablename", (esquema,))]

    def parquet(self, esquema: str, tabela: str) -> bytes:
        """A tabela publicada no BI da empresa, em Parquet. Lê do Postgres (o que foi publicado), não do disco:
        sobrevive a deploy. Só tabela que existe no schema da própria empresa; o nome nunca entra cru no SQL."""
        import tempfile

        import pandas as pd
        from psycopg import sql

        if tabela not in self.tabelas_publicadas(esquema):
            raise LookupError("tabela não publicada no BI desta empresa")
        with self.banco._dono() as con:
            cur = con.execute(sql.SQL("SELECT * FROM {}.{} LIMIT %s").format(sql.Identifier(esquema), sql.Identifier(tabela)),
                              (LIMITE_LINHAS,))
            tipos = {d.name: d.type_code for d in cur.description}
            linhas = cur.fetchall()
        nomes = list(tipos)
        df = pd.DataFrame({n: pd.Series([r[n] for r in linhas], dtype="object") for n in nomes}, columns=nomes)
        # O tipo vem da coluna no Postgres, não dos valores: coluna toda vazia ou inteiro com vazio mantém o tipo
        # (senão o pandas vira float/NULL e as relações do modelo do Power BI deixam de bater).
        for n, oid in tipos.items():
            if oid in (20, 21, 23):
                df[n] = df[n].astype("Int64")
            elif oid in (700, 701, 1700):
                df[n] = df[n].map(lambda v: None if v is None else float(v)).astype("Float64")
            elif oid == 16:
                df[n] = df[n].astype("boolean")
            elif oid in (25, 1043, 1042):
                df[n] = df[n].astype("string")
        with tempfile.TemporaryDirectory() as tmp:
            destino = Path(tmp) / "t.parquet"
            duck = duckdb.connect()
            try:
                duck.register("t", df)
                duck.execute(f"COPY t TO '{destino.as_posix()}' (FORMAT parquet)")
            finally:
                duck.close()
            return destino.read_bytes()

    def desligar(self, tenant: str) -> None:
        from psycopg import sql

        atual = self.acesso(tenant)
        if not atual:
            return
        with self.banco._dono() as con:
            con.execute(sql.SQL("ALTER ROLE {} NOLOGIN").format(sql.Identifier(atual["nome"])))
            con.execute("UPDATE interno.bi_acessos SET ativo = false WHERE tenant_id=%s", (tenant,))

    # ---- publicação -----------------------------------------------------------------
    def publicar(self, tenant: str, repo: Any, pasta: Path) -> dict:
        """Recria o schema da empresa com as tabelas atuais. Atômico: o BI vê a versão velha ou a nova."""
        from psycopg import sql

        atual = self.acesso(tenant)
        if not atual or not atual["ativo"]:
            raise BIIndisponivel("o BI desta empresa está desligado: gere a credencial primeiro")
        esquema = sql.Identifier(atual["nome"])
        tabelas = tabelas_da_empresa(repo, pasta)
        resumo, avisos = [], []
        duck = duckdb.connect()
        try:
            with self.banco._dono() as con:
                existentes = [r["tablename"] for r in con.execute(
                    "SELECT tablename FROM pg_tables WHERE schemaname=%s", (atual["nome"],))]
                novas = {t.nome for t in tabelas}
                faltam = sem_arquivo(repo, pasta)
                mantidas: dict[str, str] = {}
                for t in existentes:
                    origem = next((o for pre, o in faltam.items() if t.startswith(pre)), None)
                    if origem and t not in novas:  # o arquivo sumiu do servidor: manter a versão publicada, nunca apagar o BI
                        mantidas[t] = origem
                        continue
                    con.execute(sql.SQL("DROP TABLE {}.{}").format(esquema, sql.Identifier(t)))
                for origem in sorted(set(mantidas.values())):
                    avisos.append(f"{origem}: os arquivos não estão neste servidor; a versão já publicada foi mantida. "
                                  "Rode a demanda (ou envie a fonte) de novo para atualizar.")
                for t in tabelas:
                    try:
                        with con.transaction():  # savepoint: uma fonte quebrada não derruba as outras
                            resumo.append(self._copiar(con, duck, esquema, t, avisos))
                    except Exception as e:  # noqa: BLE001
                        avisos.append(f"{t.origem}: não foi publicada ({type(e).__name__})")
                resumo += [{"tabela": t, "origem": o, "linhas": None, "colunas": None, "mantida": True} for t, o in sorted(mantidas.items())]
                con.execute(sql.SQL("GRANT SELECT ON ALL TABLES IN SCHEMA {} TO {}").format(esquema, esquema))
                con.execute("UPDATE interno.bi_acessos SET publicado_em = now(), tabelas = %s WHERE tenant_id=%s",
                            (_json(resumo), tenant))
        finally:
            duck.close()
        return {"tabelas": resumo, "avisos": avisos}

    @staticmethod
    def _copiar(con: Any, duck: duckdb.DuckDBPyConnection, esquema: Any, t: Tabela, avisos: list[str]) -> dict:
        from psycopg import sql

        rel = t.ler(duck)
        cols = _colunas(rel)
        alvo = sql.SQL("{}.{}").format(esquema, sql.Identifier(t.nome))
        con.execute(sql.SQL("CREATE TABLE {} ({})").format(alvo, sql.SQL(", ").join(
            sql.SQL("{} {}").format(sql.Identifier(c), sql.SQL(tp)) for c, tp in cols)))
        con.execute(sql.SQL("COMMENT ON TABLE {} IS {}").format(alvo, sql.Literal(f"Lastro · {t.origem}")))
        linhas = 0
        with con.cursor().copy(sql.SQL("COPY {} ({}) FROM STDIN").format(
                alvo, sql.SQL(", ").join(sql.Identifier(c) for c, _ in cols))) as cp:
            for linha in _linhas(duck, rel, LIMITE_LINHAS + 1):
                if linhas == LIMITE_LINHAS:
                    avisos.append(f"{t.origem}: cortada em {LIMITE_LINHAS:,} linhas".replace(",", "."))
                    break
                cp.write_row(linha)
                linhas += 1
        return {"tabela": t.nome, "origem": t.origem, "linhas": linhas, "colunas": len(cols)}


def _json(v: Any) -> Any:
    from psycopg.types.json import Jsonb

    return Jsonb(v)
