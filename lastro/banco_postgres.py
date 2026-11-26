"""Banco da plataforma no Postgres do Supabase, com a RLS valendo também para o backend (ADR 0008).

Cada operação do `RepoPostgres` roda numa transação aberta como `authenticated`, com as claims
do usuário em `request.jwt.claims`. As políticas de `supabase/migrations` decidem o que a linha
mostra; o filtro por tenant no SQL fica como segunda trava, não como a única.
"""

from __future__ import annotations

import json
import time
from contextlib import contextmanager
from typing import Iterator

from psycopg import Connection
from psycopg.rows import dict_row
from psycopg.types.json import Jsonb
from psycopg_pool import ConnectionPool

from .banco import (
    CAMPOS_CARGA_ATUALIZAVEIS,
    SQL_METRICA,
    confere_senha,
    evento_demo,
    gerar_senha_provisoria,
    hash_senha,
    hora_cheia,
    validar_nova_senha,
)


def claims(tenant: str, email: str, papel: str) -> str:
    return json.dumps({"role": "authenticated", "email": email.lower(), "app_metadata": {"tenant_id": tenant, "papel": papel}})


class BancoPostgres:
    def __init__(self, url: str, max_conexoes: int = 4):
        # prepare_threshold=None: o pooler do Supabase em modo transação não aceita prepared statements.
        self.pool = ConnectionPool(
            url, min_size=1, max_size=max_conexoes, open=True,
            kwargs={"row_factory": dict_row, "prepare_threshold": None, "autocommit": False},
        )

    @contextmanager
    def _como(self, tenant: str, email: str, papel: str) -> Iterator[Connection]:
        with self.pool.connection() as con, con.transaction():
            con.execute("SET LOCAL ROLE authenticated")
            con.execute("SELECT set_config('request.jwt.claims', %s, true)", (claims(tenant, email, papel),))
            yield con

    @contextmanager
    def _dono(self) -> Iterator[Connection]:
        """Conexão do dono do banco: só para login (antes de saber o tenant) e cadastro de tenant."""
        with self.pool.connection() as con, con.transaction():
            yield con

    def ping(self) -> None:
        with self._dono() as con:
            con.execute("SELECT 1").fetchone()

    def registrar_metrica(self, status: int, ms: int, agora: float | None = None) -> None:
        agora = time.time() if agora is None else agora
        sql = SQL_METRICA.format(t="interno.metricas_api", h="to_timestamp(%s)", p="%s")
        with self._dono() as con:
            con.execute(sql, (hora_cheia(agora), int(400 <= status < 500), int(status >= 500), ms))

    def registrar_demo(self, etapa: str, **campos: object) -> None:
        e = evento_demo(etapa, **campos)  # type: ignore[arg-type]
        with self._dono() as con:
            con.execute("INSERT INTO interno.demo_eventos (etapa, duracao_ms, faixa_tamanho, n_colunas, visual, motivo) "
                        "VALUES (%s,%s,%s,%s,%s,%s)", tuple(e.values()))

    def eventos_demo(self) -> list[dict]:
        with self._dono() as con:
            return [dict(r) for r in con.execute(
                "SELECT etapa, duracao_ms, faixa_tamanho, n_colunas, visual, motivo FROM interno.demo_eventos ORDER BY id")]

    def metricas(self) -> list[dict]:
        with self._dono() as con:
            return [dict(r) for r in con.execute(
                "SELECT extract(epoch FROM hora)::float AS hora, requisicoes, erros_4xx, erros_5xx, latencia_ms "
                "FROM interno.metricas_api ORDER BY hora")]

    def criar_tenant(self, tenant_id: str, nome: str) -> None:
        with self._dono() as con:
            con.execute("INSERT INTO tenants (id, nome) VALUES (%s, %s) ON CONFLICT (id) DO NOTHING", (tenant_id, nome))

    def criar_usuario(self, tenant_id: str, email: str, nome: str, papel: str, senha: str) -> None:
        with self._dono() as con:
            r = con.execute(
                # Só demo e primeiro admin. Nunca move um e-mail de empresa: conflito com outra empresa falha.
                "INSERT INTO usuarios (email, tenant_id, nome, papel, senha_hash) VALUES (%s,%s,%s,%s,%s) "
                "ON CONFLICT (email) DO UPDATE SET nome=excluded.nome, papel=excluded.papel, senha_hash=excluded.senha_hash "
                "WHERE usuarios.tenant_id = excluded.tenant_id RETURNING email",
                (email.lower(), tenant_id, nome, papel, hash_senha(senha)),
            ).fetchone()
            if r is None:
                raise PermissionError("este e-mail já pertence a outra empresa")

    def trancar_usuario(self, tenant_id: str, email: str) -> bool:
        """Bloqueia o login trocando a senha por uma aleatória que ninguém conhece. Não apaga: o rastro aponta para o usuário."""
        import secrets

        with self._dono() as con:
            r = con.execute("UPDATE usuarios SET senha_hash=%s WHERE email=%s AND tenant_id=%s RETURNING email",
                            (hash_senha(secrets.token_urlsafe(32)), email.lower(), tenant_id)).fetchone()
        return r is not None

    def autenticar(self, email: str, senha: str) -> dict | None:
        with self._dono() as con:
            u = con.execute("SELECT * FROM usuarios WHERE email=%s", (email.lower(),)).fetchone()
        if u and confere_senha(senha, u["senha_hash"]):
            return u
        return None

    # ---- contas (LST-32): conexão de dono, sempre filtrando pela empresa ---------------------
    def senha_provisoria(self, tenant: str, email: str, nome: str, papel: str) -> str:
        email = email.lower()
        senha = gerar_senha_provisoria()
        with self._dono() as con:
            dono = con.execute("SELECT tenant_id FROM usuarios WHERE email=%s FOR UPDATE", (email,)).fetchone()
            if dono and dono["tenant_id"] != tenant:
                raise PermissionError("este e-mail já pertence a outra empresa")
            if dono:
                con.execute("UPDATE usuarios SET nome=%s, papel=%s, senha_hash=%s, trocar_senha=true WHERE email=%s AND tenant_id=%s",
                            (nome, papel, hash_senha(senha), email, tenant))
            else:
                con.execute("INSERT INTO usuarios (email, tenant_id, nome, papel, senha_hash, trocar_senha) VALUES (%s,%s,%s,%s,%s,true)",
                            (email, tenant, nome, papel, hash_senha(senha)))
        return senha

    def trocar_senha(self, email: str, atual: str, nova: str) -> bool:
        if not self.autenticar(email, atual):
            return False
        validar_nova_senha(atual, nova)
        with self._dono() as con:
            con.execute("UPDATE usuarios SET senha_hash=%s, trocar_senha=false WHERE email=%s", (hash_senha(nova), email.lower()))
        return True

    def usuarios(self, tenant: str) -> list[dict]:
        with self._dono() as con:
            return [dict(r) for r in con.execute(
                "SELECT email, nome, papel, trocar_senha FROM usuarios WHERE tenant_id=%s ORDER BY email", (tenant,))]

    def repo(self, tenant: str, email: str = "sistema@lastro", papel: str = "admin") -> RepoPostgres:
        return RepoPostgres(self, tenant, email, papel)

    def cargas_ativas(self) -> list[dict]:
        """Todas as empresas: só o executor agendado usa (conexão de dono)."""
        with self._dono() as con:
            return [dict(r) for r in con.execute(f"SELECT {_COLS_CARGA} FROM cargas WHERE ativa ORDER BY id").fetchall()]

    def fechar(self) -> None:
        self.pool.close()


_COLS_CARGA = (
    "id, tenant_id, fonte_id, saas, entidade, variaveis, chave, modo, hora, cota_diaria, marca_dagua, ultima_execucao, "
    "ultimo_status, ultimo_aviso, dia_cota, chamadas_no_dia, ativa, extract(epoch FROM criado_em)::float AS criado_em"
)


class RepoPostgres:
    """Mesma interface do `Repo` do SQLite; cada chamada é uma transação com as claims do usuário."""

    def __init__(self, banco: BancoPostgres, tenant: str, email: str, papel: str):
        self.banco, self.tenant, self.email, self.papel = banco, tenant, email.lower(), papel

    def _con(self):  # noqa: ANN202
        return self.banco._como(self.tenant, self.email, self.papel)

    def registrar(self, ator: str, acao: str, detalhe: dict | str, demanda_id: int | None = None) -> None:
        if isinstance(detalhe, str):
            detalhe = {"texto": detalhe}
        with self._con() as con:
            con.execute(
                "INSERT INTO eventos (tenant_id, demanda_id, ator, acao, detalhe) VALUES (%s,%s,%s,%s,%s)",
                (self.tenant, demanda_id, ator, acao, Jsonb(json.loads(json.dumps(detalhe, default=str)))),
            )

    def eventos(self, demanda_id: int) -> list[dict]:
        with self._con() as con:
            rows = con.execute(
                "SELECT ator, acao, detalhe::text AS detalhe, extract(epoch FROM em)::float AS em FROM eventos "
                "WHERE tenant_id=%s AND demanda_id=%s ORDER BY id",
                (self.tenant, demanda_id),
            ).fetchall()
        return [dict(r) for r in rows]

    def adicionar_fonte(self, nome: str, tipo: str, caminho: str) -> int:
        with self._con() as con:
            r = con.execute(
                "INSERT INTO fontes (tenant_id, nome, tipo, caminho) VALUES (%s,%s,%s,%s) RETURNING id",
                (self.tenant, nome, tipo, caminho),
            ).fetchone()
        return int(r["id"])

    def fontes(self, ids: list[int] | None = None) -> list[dict]:
        with self._con() as con:
            rows = con.execute(
                "SELECT id, tenant_id, nome, tipo, caminho, extract(epoch FROM criado_em)::float AS criado_em "
                "FROM fontes WHERE tenant_id=%s ORDER BY id",
                (self.tenant,),
            ).fetchall()
        return [dict(r) for r in rows if ids is None or r["id"] in ids]

    def criar_demanda(self, autor: str, pergunta: str, fontes: list[int]) -> int:
        validas = {f["id"] for f in self.fontes()}
        if not set(fontes) <= validas:
            raise PermissionError("fonte fora deste tenant")
        with self._con() as con:
            r = con.execute(
                "INSERT INTO demandas (tenant_id, autor, pergunta, fontes, status) VALUES (%s,%s,%s,%s,'nova') RETURNING id",
                (self.tenant, autor.lower(), pergunta, fontes),
            ).fetchone()
        return int(r["id"])

    def demanda(self, demanda_id: int) -> dict | None:
        with self._con() as con:
            r = con.execute(
                "SELECT id, tenant_id, autor, pergunta, fontes, status, grill, respostas, resultado, "
                "extract(epoch FROM criado_em)::float AS criado_em FROM demandas WHERE tenant_id=%s AND id=%s",
                (self.tenant, demanda_id),
            ).fetchone()
        if r is None:
            return None
        d = dict(r)
        d["fontes"] = [int(x) for x in d["fontes"]]
        return d

    def demandas(self) -> list[dict]:
        with self._con() as con:
            ids = [r["id"] for r in con.execute("SELECT id FROM demandas WHERE tenant_id=%s ORDER BY id DESC", (self.tenant,))]
        return [self.demanda(i) for i in ids]  # type: ignore[misc]

    # ---- cargas agendadas (LST-7) ----------------------------------------------------
    def criar_carga(self, fonte_id: int, saas: str, entidade: str, variaveis: dict, chave: str = "id", modo: str = "real",
                    hora: int = 6, cota_diaria: int | None = None, marca_dagua: float | None = None) -> int:
        if fonte_id not in {f["id"] for f in self.fontes()}:
            raise PermissionError("fonte fora deste tenant")
        with self._con() as con:
            r = con.execute(
                "INSERT INTO cargas (tenant_id, fonte_id, saas, entidade, variaveis, chave, modo, hora, cota_diaria, marca_dagua) "
                "VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s) RETURNING id",
                (self.tenant, fonte_id, saas, entidade, Jsonb(variaveis), chave, modo, hora, cota_diaria, marca_dagua),
            ).fetchone()
        return int(r["id"])

    def cargas(self) -> list[dict]:
        with self._con() as con:
            return [dict(r) for r in con.execute(f"SELECT {_COLS_CARGA} FROM cargas WHERE tenant_id=%s ORDER BY id", (self.tenant,))]

    def carga(self, carga_id: int) -> dict | None:
        with self._con() as con:
            r = con.execute(f"SELECT {_COLS_CARGA} FROM cargas WHERE tenant_id=%s AND id=%s", (self.tenant, carga_id)).fetchone()
        return dict(r) if r else None

    def atualizar_carga(self, carga_id: int, **campos: object) -> None:
        if not set(campos) <= CAMPOS_CARGA_ATUALIZAVEIS:
            raise ValueError(sorted(set(campos) - CAMPOS_CARGA_ATUALIZAVEIS))
        sets = ", ".join(f"{k}=%s" for k in campos)
        with self._con() as con:
            con.execute(f"UPDATE cargas SET {sets} WHERE tenant_id=%s AND id=%s", (*campos.values(), self.tenant, carga_id))

    def atualizar_demanda(self, demanda_id: int, **campos: object) -> None:
        sets, vals = [], []
        for k, v in campos.items():
            if k not in {"status", "grill", "respostas", "resultado"}:
                raise ValueError(k)
            sets.append(f"{k}=%s")
            if k == "status":
                vals.append(v)
            else:
                vals.append(Jsonb(json.loads(v) if isinstance(v, str) else json.loads(json.dumps(v, default=str))))
        with self._con() as con:
            con.execute(f"UPDATE demandas SET {', '.join(sets)} WHERE tenant_id=%s AND id=%s", (*vals, self.tenant, demanda_id))

