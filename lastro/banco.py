"""Banco da plataforma (SQLite local; em produção, Supabase com RLS — ver supabase/migrations).

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
CREATE TABLE IF NOT EXISTS eventos (
  id INTEGER PRIMARY KEY, tenant_id TEXT NOT NULL, demanda_id INTEGER, ator TEXT NOT NULL,
  acao TEXT NOT NULL, detalhe TEXT NOT NULL, em REAL NOT NULL);
"""

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

    def atualizar_demanda(self, demanda_id: int, **campos: object) -> None:
        sets, vals = [], []
        for k, v in campos.items():
            if k not in {"status", "grill", "respostas", "resultado"}:
                raise ValueError(k)
            sets.append(f"{k}=?")
            vals.append(v if isinstance(v, str) else json.dumps(v, ensure_ascii=False, default=str))
        self.con.execute(f"UPDATE demandas SET {', '.join(sets)} WHERE tenant_id=? AND id=?", (*vals, self.tenant, demanda_id))
        self.con.commit()
