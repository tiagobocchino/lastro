"""Intérprete (card LST-35): conversa sobre a base e o painel de uma demanda aprovada e devolve insights com prova.

- Lê só a pasta da demanda: o gold (num DuckDB em memória, travado: sem disco, sem rede, sem mudar a
  configuração), a especificação do painel (a mesma que gera o HTML e o projeto do Power BI) e a resposta do
  relatório aprovado. Toda consulta passa pela trava de somente leitura.
- Cada insight tem a consulta que o sustenta, o resultado e um texto cujos números saem **só** do resultado.
- Camada 1: `auditar` roda a consulta de novo numa conexão separada, compara o resultado e recusa o texto com
  número que não está no resultado. Camada 2: o turno fica "aguardando revisor" até um humano aprovar.
- Determinístico (ADR 0003): o que não reconhece vira um resumo com sugestões, sem inventar resposta.
"""

from __future__ import annotations

import re
import unicodedata
from pathlib import Path
from typing import Any

import duckdb

from .. import paineis
from ..somente_leitura import verificar
from .base import Agente
from .orquestrador import colunas_citadas

NUM = re.compile(r"\d{1,3}(?:\.\d{3})+(?:,\d+)?|\d+(?:,\d+)?")


def _sem_acento(t: str) -> str:
    return unicodedata.normalize("NFKD", t).encode("ascii", "ignore").decode().lower()


def fmt(v: Any, casas: int = 2) -> str:
    s = f"{float(v):,.{casas}f}"
    return s.replace(",", "X").replace(".", ",").replace("X", ".")


class InsightSemProva(ValueError):
    pass


def carregar_gold(pasta_demanda: Path) -> duckdb.DuckDBPyConnection:
    """Gold da demanda em memória. Só arquivos de dentro da pasta da demanda; depois, conexão travada."""
    pasta = pasta_demanda.resolve()
    gold = pasta / "gold"
    con = duckdb.connect()
    for arq in sorted(gold.glob("*.parquet")):
        real = arq.resolve()
        if not real.is_relative_to(pasta):  # link apontando para fora (outra empresa): recusa
            raise PermissionError("o gold aponta para fora da pasta da demanda")
        caminho = str(real).replace("'", "''")
        con.execute(f'CREATE TABLE "{arq.stem}" AS SELECT * FROM read_parquet(\'{caminho}\')')
    con.execute("SET enable_external_access = false")
    con.execute("SET autoinstall_known_extensions = false")
    con.execute("SET autoload_known_extensions = false")
    con.execute("SET lock_configuration = true")
    return con


def _consultar(con: duckdb.DuckDBPyConnection, sql: str) -> list[list]:
    verificar(sql)
    return [[float(x) if isinstance(x, (int, float)) and not isinstance(x, bool) else x for x in r] for r in con.execute(sql).fetchall()]


def permitidos(linhas: list[list], constantes: tuple = ()) -> set[str]:
    """Todo número que um texto honesto pode citar: os do resultado (em 0, 1 ou 2 casas) e as constantes da consulta."""
    ok = {str(c) for c in constantes}
    for linha in linhas:
        for v in linha:
            if isinstance(v, float):
                ok |= {fmt(a, c) for a in (v, abs(v)) for c in (0, 1, 2)}
            elif v is not None:
                ok |= set(NUM.findall(str(v)))
    return ok


def auditar(insight: dict, pasta_demanda: Path) -> None:
    """Camada 1. Levanta InsightSemProva se faltar consulta, se o resultado não se repetir ou se o texto citar
    número que não está no resultado."""
    sql = insight.get("sql")
    if not sql or not insight.get("texto"):
        raise InsightSemProva("insight sem consulta que o sustente")
    con = carregar_gold(pasta_demanda)  # conexão separada: o auditor não confia na do intérprete
    try:
        linhas = _consultar(con, sql)
    except Exception as e:
        raise InsightSemProva(f"a consulta não roda: {type(e).__name__}") from e
    finally:
        con.close()
    if [[round(x, 6) if isinstance(x, float) else x for x in r] for r in linhas] != \
       [[round(x, 6) if isinstance(x, float) else x for x in r] for r in insight.get("linhas", [])]:
        raise InsightSemProva("o resultado da consulta não confere com o insight")
    soltos = [n for n in NUM.findall(insight["texto"]) if n not in permitidos(linhas, tuple(insight.get("constantes", ())))]
    if soltos:
        raise InsightSemProva(f"o texto cita número sem prova: {', '.join(soltos)}")


class Interprete(Agente):
    nome = "interprete"

    def __init__(self, demanda: dict, pasta_demanda: Path):
        super().__init__()
        self.demanda, self.pasta = demanda, pasta_demanda
        self.modelo = demanda["resultado"]["modelo"]
        self.relatorio = demanda["resultado"].get("resposta", {})
        self.spec = paineis.atual(pasta_demanda)  # o painel define o que importa: medida e eixos
        self.con = carregar_gold(pasta_demanda)
        self.tabelas = {r[0] for r in self.con.execute("SHOW TABLES").fetchall()}
        self.dims = [d for d in (paineis._slug(x) for x in self.modelo.get("dimensoes", [])) if f"dim_{d}" in self.tabelas]
        self.medida = self._medida()

    def fechar(self) -> None:
        self.con.close()

    def _medida(self) -> dict:
        if self.spec and self.spec.get("medidas"):
            m = self.spec["medidas"][0]
            return {"coluna": m["coluna"], "agregacao": m["agregacao"], "nome": m["nome"], "origem": f"medida '{m['nome']}' do painel v{self.spec['versao']}"}
        col = self.modelo.get("medida")
        return {"coluna": col, "agregacao": "soma", "nome": paineis._nome(col), "origem": "medida do relatório aprovado"}

    def _eixo(self, pergunta: str) -> str | None:
        citadas = [paineis._slug(c) for c in colunas_citadas(pergunta, self.dims)]
        if citadas:
            return citadas[0]
        if self.spec:
            for v in self.spec["visuais"]:
                if v.get("eixo") in self.dims:
                    return v["eixo"]
        return self.dims[0] if self.dims else None

    # ---- tipos de insight: cada um monta a consulta e o texto só com o resultado ----------------
    def _agg(self) -> str:
        return paineis._agg_sql({"coluna": self.medida["coluna"], "agregacao": self.medida["agregacao"]})

    def _por_eixo(self, eixo: str) -> str:
        return f"SELECT dim_{eixo}.{eixo} AS item, {self._agg()} AS valor FROM fato JOIN dim_{eixo} USING ({eixo}_id) GROUP BY 1"

    def total(self) -> dict:
        sql = f"SELECT round({self._agg()}, 2) AS total FROM fato"
        linhas = _consultar(self.con, sql)
        texto = f"{self.medida['nome']} soma {fmt(linhas[0][0])} no total."
        rel = self.relatorio.get("total")
        if rel is not None and self.relatorio.get("medida") == self.medida["coluna"] and round(float(rel), 2) == linhas[0][0]:
            texto += " Bate com o total do relatório aprovado."
        return {"tipo": "total", "texto": texto, "sql": sql, "linhas": linhas}

    def extremo(self, eixo: str, maior: bool = True) -> dict:
        ordem = "DESC" if maior else "ASC"
        sql = (f"WITH t AS ({self._por_eixo(eixo)}) SELECT item, round(valor, 2) AS valor, "
               f"round(100 * valor / sum(valor) OVER (), 1) AS pct FROM t ORDER BY valor {ordem} LIMIT 1")
        linhas = _consultar(self.con, sql)
        item, valor, pct = linhas[0]
        verbo = "lidera" if maior else "fica por último"
        return {"tipo": "maior" if maior else "menor", "eixo": eixo, "sql": sql, "linhas": linhas,
                "texto": f"{item} {verbo} em {self.medida['nome'].lower()} por {eixo.replace('_', ' ')}: {fmt(valor)} ({fmt(pct, 1)}% do total)."}

    def concentracao(self, eixo: str, n: int = 3) -> dict:
        sql = (f"WITH t AS ({self._por_eixo(eixo)}), r AS (SELECT valor, row_number() OVER (ORDER BY valor DESC) AS n FROM t) "
               f"SELECT round(100 * sum(valor) FILTER (WHERE n <= {n}) / sum(valor), 1) AS pct, count(*) AS itens FROM r")
        linhas = _consultar(self.con, sql)
        pct, itens = linhas[0]
        return {"tipo": "concentracao", "eixo": eixo, "sql": sql, "linhas": linhas, "constantes": (n,),
                "texto": f"Os {n} maiores em {eixo.replace('_', ' ')} concentram {fmt(pct, 1)}% de {self.medida['nome'].lower()} "
                         f"(entre {fmt(itens, 0)})."}

    def tendencia(self) -> dict | None:
        if "dim_data" not in self.tabelas:
            return None
        sql = (f"WITH m AS (SELECT dim_data.ano_mes AS mes, round({self._agg()}, 2) AS valor FROM fato JOIN dim_data USING (data) "
               f"GROUP BY 1 ORDER BY 1 DESC LIMIT 2), o AS (SELECT mes, valor, row_number() OVER (ORDER BY mes DESC) AS n FROM m) "
               f"SELECT max(mes) FILTER (WHERE n = 1) AS mes_atual, max(valor) FILTER (WHERE n = 1) AS valor_atual, "
               f"max(mes) FILTER (WHERE n = 2) AS mes_anterior, max(valor) FILTER (WHERE n = 2) AS valor_anterior, "
               f"round(100 * (max(valor) FILTER (WHERE n = 1) - max(valor) FILTER (WHERE n = 2)) "
               f"/ nullif(max(valor) FILTER (WHERE n = 2), 0), 1) AS variacao_pct FROM o")
        linhas = _consultar(self.con, sql)
        m1, v1, m0, v0, var = linhas[0]
        if m0 is None or var is None:
            return None
        sentido = "subiu" if var >= 0 else "caiu"
        return {"tipo": "tendencia", "sql": sql, "linhas": linhas,
                "texto": f"Em {m1}, {self.medida['nome'].lower()} {sentido} {fmt(abs(var), 1)}% frente a {m0} "
                         f"({fmt(v1)} contra {fmt(v0)})."}

    # ---- conversa -------------------------------------------------------------------------
    def responder(self, pergunta: str) -> dict:
        p = _sem_acento(pergunta)
        eixo = self._eixo(pergunta)
        pedidos: list[Any] = []
        if re.search(r"\b(total|quanto|soma)\b", p):
            pedidos.append(self.total)
        if eixo and re.search(r"\b(menor|pior|ultimo|menos)\b", p):
            pedidos.append(lambda: self.extremo(eixo, maior=False))
        if eixo and re.search(r"\b(maior|melhor|lider|lidera|quem|top|mais)\b", p):
            pedidos.append(lambda: self.extremo(eixo))
        if eixo and re.search(r"concentr|depend|ranking", p):
            pedidos.append(lambda: self.concentracao(eixo))
        if re.search(r"evolu|tendenc|cresc|caiu|queda|subiu|mes|mensal|periodo", p):
            pedidos.append(self.tendencia)
        reconhecida = bool(pedidos)
        if not pedidos:  # pergunta aberta: resumo com o que é seguro dizer
            pedidos = [self.total] + ([lambda: self.extremo(eixo), lambda: self.concentracao(eixo)] if eixo else []) + [self.tendencia]
        insights, recusados = [], []
        for fazer in pedidos:
            ins = fazer()
            if ins is None:
                continue
            try:
                auditar(ins, self.pasta)
                ins["camada1"] = "conferido"
                insights.append(ins)
            except InsightSemProva as e:
                recusados.append({"tipo": ins.get("tipo"), "motivo": str(e)})
        ins_origem = self.medida["origem"]
        r = {"pergunta": pergunta, "reconhecida": reconhecida, "base": ins_origem, "insights": insights, "recusados": recusados,
             "sugestoes": self.sugestoes(eixo)}
        if re.search(r"nao bate|nao fecha|diferen|diverg|por que .*(cartao|card|tabela|total|grafico|barra)", p):
            r["conferencia"] = self.conferencia()
            r["reconhecida"] = True
        return r

    def avisos_de_conferencia(self) -> list[dict]:
        """O que o Auditor já mediu e explica número que 'não bate' (caixa/global/metodos/conferencia-card-x-tabela.md)."""
        checks = (self.demanda["resultado"].get("auditoria") or {}).get("checagens", [])
        chaves = ("fora do gráfico", "nulos na medida", "grafias diferentes", "marcador de vazio", "linhas: fonte")
        return [c for c in checks if c["checagem"].startswith(chaves) and (not c["ok"] or c["checagem"].startswith("linhas: fonte"))]

    def conferencia(self) -> dict:
        """Resposta para 'por que o cartão não bate com a tabela?': os motivos medidos pela auditoria, sem inventar."""
        avisos = self.avisos_de_conferencia()
        motivos = [f"{a['checagem']}: {a['detalhe']}" for a in avisos]
        if not any(not a["ok"] for a in avisos):
            motivos.append("A auditoria não achou linha fora de visual: total e soma das fatias batem. Confira filtros de página "
                           "ou de relatório no seu BI e a unidade da contagem (registro, documento ou projeto).")
        return {"metodo": "global:metodos/conferencia-card-x-tabela.md", "motivos": motivos,
                "texto": "Motivos medidos na auditoria desta demanda, do maior suspeito ao menor."}

    def sugestoes(self, eixo: str | None) -> list[str]:
        nome = self.medida["nome"].lower()
        s = [f"Quanto foi o {nome} total?"]
        if eixo:
            s += [f"Quem lidera em {nome} por {eixo.replace('_', ' ')}?", f"Quem fica por último em {nome} por {eixo.replace('_', ' ')}?",
                  f"O {nome} por {eixo.replace('_', ' ')} está concentrado?"]
        if "dim_data" in self.tabelas:
            s.append(f"Como evoluiu o {nome} no último mês?")
        if any(not a["ok"] for a in self.avisos_de_conferencia()):
            s.append("Por que o total não bate com a soma das barras?")
        return s
