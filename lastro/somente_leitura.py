"""Trava de somente leitura para SQL vindo de agentes.

É a segunda linha de defesa. A primeira é a credencial: cada conector abre a fonte em modo
leitura (SQLite `mode=ro`, DuckDB `read_only=True`, usuário de banco só com SELECT).
"""

from __future__ import annotations

import re

PERMITIDOS = {"select", "with", "describe", "show", "explain", "summarize", "from", "values", "table"}
PROIBIDOS = {
    "insert", "update", "delete", "merge", "upsert", "drop", "create", "alter", "truncate",
    "attach", "detach", "copy", "export", "import", "install", "load", "pragma", "call",
    "set", "reset", "grant", "revoke", "vacuum", "checkpoint", "use", "begin", "commit", "rollback",
}


class EscritaBloqueada(PermissionError):
    """O agente tentou algo que não é leitura."""


def _limpar(sql: str) -> str:
    sql = re.sub(r"--[^\n]*", " ", sql)
    sql = re.sub(r"/\*.*?\*/", " ", sql, flags=re.S)
    sql = re.sub(r"'(?:[^']|'')*'", "''", sql)
    sql = re.sub(r'"(?:[^"]|"")*"', '""', sql)
    return sql


def verificar(sql: str) -> str:
    """Devolve o SQL se for uma única instrução de leitura; senão levanta `EscritaBloqueada`."""
    limpo = _limpar(sql).strip().rstrip(";").strip()
    if not limpo:
        raise EscritaBloqueada("consulta vazia")
    if ";" in limpo:
        raise EscritaBloqueada("só uma instrução por vez")
    primeira = limpo.split(None, 1)[0].lower().lstrip("(")
    if primeira not in PERMITIDOS:
        raise EscritaBloqueada(f"instrução '{primeira}' não é leitura")
    palavras = set(re.findall(r"[a-z_]+", limpo.lower()))
    achadas = palavras & PROIBIDOS
    if achadas:
        raise EscritaBloqueada(f"palavra proibida em consulta de leitura: {sorted(achadas)}")
    return sql
