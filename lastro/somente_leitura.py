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


# Funções do DuckDB que leem disco, rede ou ambiente: uma consulta de agente nunca precisa delas
# (as fontes já chegam como views do sandbox). Sem isso, uma empresa leria arquivos de outra.
FUNCOES_PROIBIDAS = {
    "read_csv", "read_csv_auto", "read_parquet", "parquet_scan", "read_json", "read_json_auto",
    "read_json_objects", "read_ndjson", "read_ndjson_auto", "read_ndjson_objects", "read_text", "read_blob",
    "read_xlsx", "sniff_csv", "glob", "getenv", "current_setting", "st_read", "iceberg_scan", "delta_scan",
    "query", "query_table", "duckdb_settings", "duckdb_secrets", "duckdb_extensions", "which_secret",
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
    funcoes = palavras & FUNCOES_PROIBIDAS
    if funcoes:
        raise EscritaBloqueada(f"função que lê disco ou ambiente: {sorted(funcoes)}")
    baixo = limpo.lower()
    # DuckDB aceita arquivo como tabela: FROM 'x.csv', JOIN 'x.parquet', FROM v, 'x.csv'
    if re.search(r"\b(from|join)\s+''", baixo) or re.search(r"\bfrom\s+[\w.\"]+(\s+(as\s+)?\w+)?\s*,\s*''", baixo):
        raise EscritaBloqueada("arquivo usado como tabela")
    return sql
