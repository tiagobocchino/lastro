"""Banco da plataforma: SQLite local ou Postgres do Supabase com RLS (`banco_postgres.py`, ADR 0008).

Os dois ficam atrás da mesma interface: `abrir_banco(cfg)` devolve um banco com `criar_tenant`,
`criar_usuario`, `autenticar`, `ping` e `repo(tenant, email, papel)`.

Toda leitura e escrita passa por `Repo`, que recebe o tenant na construção e filtra
por ele em todas as consultas: é o equivalente local da RLS.
"""

from __future__ import annotations

import hashlib
import hmac
import json
import os
import sqlite3
import time
from base64 import urlsafe_b64decode, urlsafe_b64encode
from pathlib import Path

ESQUEMA = """
CREATE TABLE IF NOT EXISTS tenants (id TEXT PRIMARY KEY, nome TEXT NOT NULL, criado_em REAL NOT NULL);
CREATE TABLE IF NOT EXISTS usuarios (
  email TEXT PRIMARY KEY, tenant_id TEXT NOT NULL REFERENCES tenants(id), nome TEXT NOT NULL,
  papel TEXT NOT NULL CHECK (papel IN ('admin','demandante','revisor','leitor')),
  senha_hash TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS fontes (
  id INTEGER PRIMARY KEY, tenant_id TEXT NOT NULL REFERENCES tenants(id), nome TEXT NOT NULL,
  tipo TEXT NOT NULL, caminho TEXT NOT NULL, criado_em REAL NOT NULL);
CREATE TABLE IF NOT EXISTS demandas (
  id INTEGER PRIMARY KEY, tenant_id TEXT NOT NULL REFERENCES tenants(id), autor TEXT NOT NULL,
  pergunta TEXT NOT NULL, fontes TEXT NOT NULL, status TEXT NOT NULL,
  grill TEXT NOT NULL DEFAULT '[]', respostas TEXT NOT NULL DEFAULT '{}',
  resultado TEXT NOT NULL DEFAULT '{}', criado_em REAL NOT NULL);
CREATE TABLE IF NOT EXISTS cargas (
  id INTEGER PRIMARY KEY, tenant_id TEXT NOT NULL REFERENCES tenants(id), fonte_id INTEGER NOT NULL REFERENCES fontes(id),
  saas TEXT NOT NULL, entidade TEXT NOT NULL, variaveis TEXT NOT NULL DEFAULT '{}', chave TEXT NOT NULL DEFAULT 'id',
  modo TEXT NOT NULL DEFAULT 'real', hora INTEGER NOT NULL DEFAULT 6, cota_diaria INTEGER,
  marca_dagua REAL, ultima_execucao REAL, ultimo_status TEXT NOT NULL DEFAULT 'nunca', ultimo_aviso TEXT NOT NULL DEFAULT '',
  dia_cota TEXT NOT NULL DEFAULT '', chamadas_no_dia INTEGER NOT NULL DEFAULT 0, ativa INTEGER NOT NULL DEFAULT 1,
  criado_em REAL NOT NULL);
CREATE TABLE IF NOT EXISTS eventos (
  id INTEGER PRIMARY KEY, tenant_id TEXT NOT NULL, demanda_id INTEGER, ator TEXT NOT NULL,
  acao TEXT NOT NULL, detalhe TEXT NOT NULL, em REAL NOT NULL);
"""

CAMPOS_CARGA_ATUALIZAVEIS = {"marca_dagua", "ultima_execucao", "ultimo_status", "ultimo_aviso", "dia_cota", "chamadas_no_dia", "ativa", "hora", "cota_diaria"}
PAPEIS_QUE_DEMANDAM = {"admin", "demandante"}
PAPEIS_QUE_REVISAM = {"admin", "revisor"}


def conectar(caminho: Path) -> sqlite3.Connection:
    con = sqlite3.connect(caminho, check_same_thread=False)
    con.row_factory = sqlite3.Row
    con.executescript(ESQUEMA)
    return con


def hash_senha(senha: str, sal: bytes | None = None) -> str:
    sal = sal or os.urandom(16)
    h = hashlib.scrypt(senha.encode(), salt=sal, n=2**14, r=8, p=1)
    return sal.hex() + "$" + h.hex()


def confere_senha(senha: str, guardado: str) -> bool:
    sal, _ = guardado.split("$", 1)
    return hmac.compare_digest(hash_senha(senha, bytes.fromhex(sal)), guardado)


def emitir_token(segredo: str, email: str, tenant: str, papel: str, validade_s: int = 8 * 3600) -> str:
    carga = json.dumps({"e": email, "t": tenant, "p": papel, "x": int(time.time()) + validade_s}).encode()
    b = urlsafe_b64encode(carga).decode().rstrip("=")
    assinatura = hmac.new(segredo.encode(), b.encode(), hashlib.sha256).hexdigest()
    return f"{b}.{assinatura}"


def ler_token(segredo: str, token: str) -> dict | None:
    try:
        b, assinatura = token.rsplit(".", 1)
    except ValueError:
        return None
    esperado = hmac.new(segredo.encode(), b.encode(), hashlib.sha256).hexdigest()
    if not hmac.compare_digest(esperado, assinatura):
        return None
    carga = json.loads(urlsafe_b64decode(b + "=" * (-len(b) % 4)))
    if carga["x"] < time.time():
        return None
    return carga


def criar_tenant(con: sqlite3.Connection, tenant_id: str, nome: str) -> None:
    con.execute("INSERT OR IGNORE INTO tenants VALUES (?,?,?)", (tenant_id, nome, time.time()))
    con.commit()


def criar_usuario(con: sqlite3.Connection, tenant_id: str, email: str, nome: str, papel: str, senha: str) -> None:
    con.execute(
        "INSERT OR REPLACE INTO usuarios VALUES (?,?,?,?,?)", (email.lower(), tenant_id, nome, papel, hash_senha(senha))
    )
    con.commit()


def autenticar(con: sqlite3.Connection, email: str, senha: str) -> sqlite3.Row | None:
    u = con.execute("SELECT * FROM usuarios WHERE email=?", (email.lower(),)).fetchone()
    if u and confere_senha(senha, u["senha_hash"]):
        return u
    return None


class Repo:
    """Acesso a dados preso a um tenant. Não existe método que leia outro tenant."""

    def __init__(self, con: sqlite3.Connection, tenant: str):
        self.con = con
        self.tenant = tenant

    def registrar(self, ator: str, acao: str, detalhe: dict | str, demanda_id: int | None = None) -> None:
        if not isinstance(detalhe, str):
            detalhe = json.dumps(detalhe, ensure_ascii=False, default=str)
        self.con.execute(
            "INSERT INTO eventos (tenant_id, demanda_id, ator, acao, detalhe, em) VALUES (?,?,?,?,?,?)",
            (self.tenant, demanda_id, ator, acao, detalhe, time.time()),
        )
        self.con.commit()

    def eventos(self, demanda_id: int) -> list[dict]:
        rows = self.con.execute(
            "SELECT ator, acao, detalhe, em FROM eventos WHERE tenant_id=? AND demanda_id=? ORDER BY id", (self.tenant, demanda_id)
        ).fetchall()
        return [dict(r) for r in rows]

    def adicionar_fonte(self, nome: str, tipo: str, caminho: str) -> int:
        cur = self.con.execute(
            "INSERT INTO fontes (tenant_id, nome, tipo, caminho, criado_em) VALUES (?,?,?,?,?)",
            (self.tenant, nome, tipo, caminho, time.time()),
        )
        self.con.commit()
        return int(cur.lastrowid)

    def fontes(self, ids: list[int] | None = None) -> list[dict]:
        rows = self.con.execute("SELECT * FROM fontes WHERE tenant_id=? ORDER BY id", (self.tenant,)).fetchall()
        lista = [dict(r) for r in rows]
        return [f for f in lista if ids is None or f["id"] in ids]

    def criar_demanda(self, autor: str, pergunta: str, fontes: list[int]) -> int:
        validas = {f["id"] for f in self.fontes()}
        if not set(fontes) <= validas:
            raise PermissionError("fonte fora deste tenant")
        cur = self.con.execute(
            "INSERT INTO demandas (tenant_id, autor, pergunta, fontes, status, criado_em) VALUES (?,?,?,?,?,?)",
            (self.tenant, autor, pergunta, json.dumps(fontes), "nova", time.time()),
        )
        self.con.commit()
        return int(cur.lastrowid)

    def demanda(self, demanda_id: int) -> dict | None:
        r = self.con.execute("SELECT * FROM demandas WHERE tenant_id=? AND id=?", (self.tenant, demanda_id)).fetchone()
        if r is None:
            return None
        d = dict(r)
        for k in ("fontes", "grill", "respostas", "resultado"):
            d[k] = json.loads(d[k])
        return d

    def demandas(self) -> list[dict]:
        rows = self.con.execute("SELECT id FROM demandas WHERE tenant_id=? ORDER BY id DESC", (self.tenant,)).fetchall()
        return [self.demanda(r["id"]) for r in rows]  # type: ignore[misc]

    # ---- cargas agendadas (LST-7) ----------------------------------------------------
    def criar_carga(self, fonte_id: int, saas: str, entidade: str, variaveis: dict, chave: str = "id", modo: str = "real",
                    hora: int = 6, cota_diaria: int | None = None, marca_dagua: float | None = None) -> int:
        if fonte_id not in {f["id"] for f in self.fontes()}:
            raise PermissionError("fonte fora deste tenant")
        cur = self.con.execute(
            "INSERT INTO cargas (tenant_id, fonte_id, saas, entidade, variaveis, chave, modo, hora, cota_diaria, marca_dagua, criado_em) "
            "VALUES (?,?,?,?,?,?,?,?,?,?,?)",
            (self.tenant, fonte_id, saas, entidade, json.dumps(variaveis), chave, modo, hora, cota_diaria, marca_dagua, time.time()),
        )
        self.con.commit()
        return int(cur.lastrowid)

    def cargas(self) -> list[dict]:
        rows = self.con.execute("SELECT * FROM cargas WHERE tenant_id=? ORDER BY id", (self.tenant,)).fetchall()
        return [_carga_sqlite(r) for r in rows]

    def carga(self, carga_id: int) -> dict | None:
        r = self.con.execute("SELECT * FROM cargas WHERE tenant_id=? AND id=?", (self.tenant, carga_id)).fetchone()
        return _carga_sqlite(r) if r else None

    def atualizar_carga(self, carga_id: int, **campos: object) -> None:
        if not set(campos) <= CAMPOS_CARGA_ATUALIZAVEIS:
            raise ValueError(sorted(set(campos) - CAMPOS_CARGA_ATUALIZAVEIS))
        sets = ", ".join(f"{k}=?" for k in campos)
        self.con.execute(f"UPDATE cargas SET {sets} WHERE tenant_id=? AND id=?", (*campos.values(), self.tenant, carga_id))
        self.con.commit()

    def atualizar_demanda(self, demanda_id: int, **campos: object) -> None:
        sets, vals = [], []
        for k, v in campos.items():
            if k not in {"status", "grill", "respostas", "resultado"}:
                raise ValueError(k)
            sets.append(f"{k}=?")
            vals.append(v if isinstance(v, str) else json.dumps(v, ensure_ascii=False, default=str))
        self.con.execute(f"UPDATE demandas SET {', '.join(sets)} WHERE tenant_id=? AND id=?", (*vals, self.tenant, demanda_id))
        self.con.commit()


def _carga_sqlite(r: sqlite3.Row) -> dict:
    d = dict(r)
    d["variaveis"] = json.loads(d["variaveis"])
    d["ativa"] = bool(d["ativa"])
    return d


class BancoSqlite:
    """Banco local (desenvolvimento e testes). Mesma interface do `BancoPostgres`."""

    def __init__(self, caminho: Path):
        self.con = conectar(caminho)

    def ping(self) -> None:
        self.con.execute("SELECT 1").fetchone()

    def criar_tenant(self, tenant_id: str, nome: str) -> None:
        criar_tenant(self.con, tenant_id, nome)

    def criar_usuario(self, tenant_id: str, email: str, nome: str, papel: str, senha: str) -> None:
        criar_usuario(self.con, tenant_id, email, nome, papel, senha)

    def autenticar(self, email: str, senha: str) -> dict | None:
        u = autenticar(self.con, email, senha)
        return dict(u) if u else None

    def repo(self, tenant: str, email: str = "sistema@lastro", papel: str = "admin") -> Repo:  # noqa: ARG002
        return Repo(self.con, tenant)

    def cargas_ativas(self) -> list[dict]:
        """Todas as empresas: só o executor agendado usa (conexão de dono)."""
        return [_carga_sqlite(r) for r in self.con.execute("SELECT * FROM cargas WHERE ativa=1 ORDER BY id").fetchall()]

    def fechar(self) -> None:
        self.con.close()


def abrir_banco(cfg):  # noqa: ANN001, ANN201  (Config; evita import circular)
    """Postgres do Supabase quando LASTRO_BANCO_URL existe; senão, SQLite em LASTRO_HOME."""
    if cfg.banco_url:
        from .banco_postgres import BancoPostgres  # noqa: PLC0415  (psycopg só com o extra postgres)

        return BancoPostgres(cfg.banco_url)
    return BancoSqlite(cfg.banco)
