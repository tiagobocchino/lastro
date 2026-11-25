"""Arquiteto, Engenheiro e Analista: do perfil da fonte à resposta."""

from __future__ import annotations

import re
from pathlib import Path

from ..somente_leitura import EscritaBloqueada, verificar
from .base import Agente, Contexto
from .orquestrador import _sem_acento, colunas_citadas

SEM_CHAVE = "(nenhuma: manter todas as linhas)"


def q(col: str) -> str:
    return '"' + col.replace('"', '""') + '"'


def ident(col: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", _sem_acento(col)).strip("_") or "col"


def dimensoes_candidatas(perfil: dict, chave: str | None) -> list[str]:
    """Colunas de texto que viram dimensão: mais de um valor e no máximo max(40, 20% das linhas), fora a chave.
    Regra única: o Arquiteto modela com ela e a demonstração do site oferece as mesmas opções (LST-40)."""
    limite = max(40, int(perfil["linhas"] * 0.2))
    return [c["nome"] for c in perfil["colunas"] if c["papel"] == "texto" and c["nome"] != chave and 1 < c["distintos"] <= limite]


class Arquiteto(Agente):
    nome = "arquiteto"

    def executar(self, ctx: Contexto) -> dict:
        view, perfil = next(iter(ctx.memoria["perfis"].items()))
        fonte = perfil["fonte"]
        cols = {c["nome"]: c for c in perfil["colunas"]}
        r = lambda k: (ctx.respostas.get(f"{fonte}:{k}") or "").strip()
        numeros = [n for n, c in cols.items() if c["papel"] == "numero" and not n.lower().endswith("id")]
        medida = r("medida") if r("medida") in cols else (numeros[0] if numeros else None)
        data = r("data") if r("data") in cols else next((n for n, c in cols.items() if c["papel"] == "data"), None)
        chave = r("chave") if r("chave") in cols else None
        filtro = r("filtro")
        if filtro.lower() in {"", "nenhum", "não", "nao"}:
            filtro = ""
        if filtro:
            verificar(f"SELECT 1 FROM {view} WHERE {filtro} LIMIT 0")
            ctx.sandbox.consultar(f"SELECT 1 FROM {view} WHERE {filtro} LIMIT 0")
        dims = dimensoes_candidatas(perfil, chave)
        playbook = self.buscar(ctx, "modelo dimensional star schema planilha fato dimensão", k=1)
        modelo = {
            "fonte": fonte,
            "view": view,
            "medida": medida,
            "medidas": numeros,
            "data": data,
            "chave": chave,
            "identificadores": [n for n, c in cols.items() if c["papel"] == "identificador"],
            "filtro": filtro,
            "dimensoes": dims,
            "playbook": f"{playbook[0].caminho} § {playbook[0].secao}" if playbook else None,
        }
        ctx.memoria["modelo"] = modelo
        self.anotar(ctx, "propos_modelo", modelo)
        return modelo


class Engenheiro(Agente):
    nome = "engenheiro"

    def executar(self, ctx: Contexto) -> dict:
        ctx.politica.exigir(self.nome, "sandbox_temporario")
        m = ctx.memoria["modelo"]
        perfil = ctx.memoria["perfis"][m["view"]]
        etapas: list[tuple[str, str]] = []
        etapas.append(("bronze", f"CREATE OR REPLACE TABLE bronze AS SELECT *, current_timestamp AS _carregado_em FROM {m['view']}"))
        selecao = []
        for c in perfil["colunas"]:
            n = c["nome"]
            if c["papel"] == "texto":
                # trim e espaços repetidos colapsados: 'Recebido ' e 'Recebido' viram a mesma categoria
                # (replace aninhado e não regex: traduz igual para BigQuery, Azure e Athena)
                selecao.append(f"NULLIF(replace(replace(trim(CAST({q(n)} AS VARCHAR)), '  ', ' '), '  ', ' '), '') AS {ident(n)}")
            elif c["papel"] == "data":
                selecao.append(f"TRY_CAST({q(n)} AS DATE) AS {ident(n)}")
            else:
                selecao.append(f"{q(n)} AS {ident(n)}")
        silver = f"CREATE OR REPLACE TABLE silver AS SELECT {', '.join(selecao)} FROM bronze"
        if m["filtro"]:
            silver += f" WHERE {m['filtro']}"
        if m["chave"]:
            ordem = f"{q(m['data'])} DESC NULLS LAST" if m["data"] else "_carregado_em DESC"
            silver += f" QUALIFY row_number() OVER (PARTITION BY {q(m['chave'])} ORDER BY {ordem}) = 1"
        etapas.append(("silver", silver))
        juncoes, chaves_fato = [], []
        for d in m["dimensoes"]:
            i = ident(d)
            # SQL portável (sem USING e com apelido na subconsulta) para a tradução por trilha (LST-15)
            etapas.append((f"dim_{i}", f"CREATE OR REPLACE TABLE dim_{i} AS SELECT row_number() OVER (ORDER BY {i}) AS {i}_id, {i} FROM (SELECT DISTINCT {i} FROM silver) AS d"))
            juncoes.append(f"LEFT JOIN dim_{i} ON dim_{i}.{i} = silver.{i}")
            chaves_fato.append(f"dim_{i}.{i}_id")
        if m["data"]:
            dt = ident(m["data"])
            etapas.append((
                "dim_data",
                f"CREATE OR REPLACE TABLE dim_data AS SELECT DISTINCT {dt} AS data, year({dt}) AS ano, month({dt}) AS mes,"
                f" strftime({dt}, '%Y-%m') AS ano_mes FROM silver WHERE {dt} IS NOT NULL",
            ))
            chaves_fato.append(f"silver.{dt} AS data")
        medidas = [f"silver.{ident(x)}" for x in m["medidas"]]
        extra = [f"silver.{ident(m['chave'])}"] if m["chave"] else []
        etapas.append(("fato", f"CREATE OR REPLACE TABLE fato AS SELECT {', '.join(extra + chaves_fato + medidas) or '*'} FROM silver {' '.join(juncoes)}"))
        for nome, sql in etapas:
            ctx.sandbox.executar_pipeline(sql)
        gold = ctx.pasta_demanda / "gold"
        gold.mkdir(parents=True, exist_ok=True)
        tabelas = ["silver"] + [n for n, _ in etapas if n.startswith("dim_")] + ["fato"]
        for t in tabelas:
            ctx.sandbox.executar_pipeline(f"COPY {t} TO '{(gold / f'{t}.parquet').as_posix()}' (FORMAT parquet)")
        script = self._script(etapas, m)
        (ctx.pasta_demanda / "pipeline.py").write_text(script, encoding="utf-8")
        from ..trilhas import TRILHAS, gerar

        pasta_trilhas = ctx.pasta_demanda / "trilhas"
        pasta_trilhas.mkdir(exist_ok=True)
        for chave, texto in gerar(etapas, m).items():
            (pasta_trilhas / TRILHAS[chave].arquivo).write_text(texto, encoding="utf-8")
        ctx.memoria["etapas_sql"] = etapas
        resultado = {"etapas": [n for n, _ in etapas], "gold": [f"gold/{t}.parquet" for t in tabelas], "script": "pipeline.py",
                     "trilhas": [f"trilhas/{t.arquivo}" for t in TRILHAS.values()]}
        ctx.memoria["pipeline"] = resultado
        self.anotar(ctx, "construiu_pipeline", resultado)
        return resultado

    def _script(self, etapas: list[tuple[str, str]], m: dict) -> str:
        linhas = [
            '"""Pipeline gerado pelo Lastro. Bronze -> Silver -> Gold (star schema).',
            "",
            f"Fonte: {m['fonte']}  |  medida: {m['medida']}  |  data: {m['data']}  |  chave: {m['chave']}",
            "Rode com: python pipeline.py CAMINHO_DA_FONTE.csv",
            '"""',
            "import sys",
            "import duckdb",
            "",
            "con = duckdb.connect('pipeline.duckdb')",
            f"con.execute(\"CREATE OR REPLACE VIEW {m['view']} AS SELECT * FROM read_csv_auto(?, header=true)\", [sys.argv[1]])",
            "ETAPAS = [",
        ]
        for nome, sql in etapas:
            linhas.append(f"    ({nome!r}, {sql!r}),")
        linhas += ["]", "for nome, sql in ETAPAS:", "    con.execute(sql)", "    print('ok', nome)", ""]
        return "\n".join(linhas)


class Analista(Agente):
    nome = "analista"

    def executar(self, ctx: Contexto) -> dict:
        ctx.politica.exigir(self.nome, "sandbox_temporario")
        m = ctx.memoria["modelo"]
        medida = ident(m["medida"]) if m["medida"] else None
        p = _sem_acento(ctx.pergunta)
        dims = colunas_citadas(ctx.pergunta, m["dimensoes"])
        tempo = None
        if m["data"] and re.search(r"\b(mes|meses|mensal|evolu|ao longo|tendencia|periodo)", p):
            tempo = "ano_mes"
        elif m["data"] and re.search(r"\b(ano|anual|anos)\b", p):
            tempo = "ano"
        sql = self._sql_llm(ctx, m) or self._sql_heuristico(m, medida, dims, tempo)
        colunas, linhas = ctx.sandbox.consultar(sql)
        total = None
        if medida:
            total = ctx.sandbox.consultar(f"SELECT sum({medida}) FROM fato")[1][0][0]
        resposta = {"sql": sql, "colunas": colunas, "linhas": [list(map(_json, l)) for l in linhas], "total": _json(total), "medida": m["medida"], "agrupado_por": dims + ([tempo] if tempo else [])}
        ctx.memoria["resposta"] = resposta
        self.anotar(ctx, "respondeu", {"sql": sql, "linhas": len(linhas)})
        return resposta

    def _sql_heuristico(self, m: dict, medida: str | None, dims: list[str], tempo: str | None) -> str:
        grupos = [f"dim_{ident(d)}.{ident(d)}" for d in dims]
        juncoes = [f"JOIN dim_{ident(d)} USING ({ident(d)}_id)" for d in dims]
        if tempo:
            grupos.append(f"dim_data.{tempo}")
            juncoes.append("JOIN dim_data USING (data)")
        valor = f"round(sum(fato.{medida}), 2) AS total_{medida}" if medida else "count(*) AS registros"
        if not grupos:
            return f"SELECT count(*) AS registros{', ' + valor if medida else ''} FROM fato"
        ordem = f"dim_data.{tempo}" if tempo and not dims else f"{len(grupos) + 1} DESC"
        if tempo and dims:
            ordem = f"dim_data.{tempo}, {len(grupos) + 1} DESC"
        return (
            f"SELECT {', '.join(grupos)}, {valor}{', count(*) AS registros' if medida else ''} FROM fato {' '.join(juncoes)}"
            f" GROUP BY {', '.join(grupos)} ORDER BY {ordem} LIMIT 50"
        )

    def _sql_llm(self, ctx: Contexto, m: dict) -> str | None:
        if not ctx.llm.ativo:
            return None
        esquema = []
        for t in ["fato"] + [f"dim_{ident(d)}" for d in m["dimensoes"]] + (["dim_data"] if m["data"] else []):
            cols, linhas = ctx.sandbox.consultar(f"DESCRIBE {t}")
            esquema.append(f"{t}({', '.join(l[0] for l in linhas)})")
        resposta = ctx.llm.responder(
            self.instrucoes(),
            "Esquema DuckDB:\n" + "\n".join(esquema) + f"\n\nPergunta: {ctx.pergunta}\nResponda só com uma consulta SELECT, sem comentários.",
        )
        if not resposta:
            return None
        sql = re.sub(r"^```\w*|```$", "", resposta.strip(), flags=re.MULTILINE).strip()
        try:
            verificar(sql)
            ctx.sandbox.consultar(f"SELECT * FROM ({sql.rstrip(';')}) LIMIT 0")
        except (EscritaBloqueada, Exception):  # noqa: BLE001 - qualquer erro cai na heurística
            self.anotar(ctx, "descartou_sql_llm", sql)
            return None
        return sql


def _json(v: object) -> object:
    if v is None or isinstance(v, (int, float, str, bool)):
        return v
    try:
        return float(v)  # Decimal
    except (TypeError, ValueError):
        return str(v)


__all__ = ["SEM_CHAVE", "Analista", "Arquiteto", "Engenheiro", "Path", "ident", "q"]
