"""Explorador: lê as fontes e escreve uma nota de fonte na Caixa do tenant."""

from __future__ import annotations

import re

from ..caixa import gravar_nota
from ..pessoal import NOMES as NOMES_PESSOAIS
from ..pessoal import detectar as detectar_pessoal
from .base import Agente, Contexto

NUMERICOS = ("INT", "DECIMAL", "DOUBLE", "FLOAT", "REAL", "NUMERIC", "HUGEINT", "BIGINT")
DATAS = ("DATE", "TIMESTAMP")
MAX_CATEGORIAS = 30


# "Nº", "N º E", "No.", "Num", "Número", "ID", "Cód", "Código": número que identifica, não valor que soma.
_NOME_ID = re.compile(r"^(n\s*[º°]|no\.|num\.?|n[uú]mero|id|c[oó]d\.?|c[oó]digo)(?=$|[\s_.\-º°:])", re.IGNORECASE)


def _eh_identificador(col: str, tipo: str, distintos: int, total: int) -> bool:
    nome = col.strip()
    pelo_nome = bool(_NOME_ID.match(nome)) or nome.lower().rstrip("_").endswith(("id", "codigo", "numero"))
    inteiro = tipo.upper().startswith(("INT", "BIGINT", "HUGEINT", "SMALLINT", "TINYINT", "UBIGINT", "UINTEGER"))
    return pelo_nome and inteiro and total > 0 and distintos >= 0.95 * total


def _eh_data_por_nome(col: str) -> bool:
    c = col.lower()
    return c.startswith("data") or c.startswith("dt_") or c.endswith("_em") or "date" in c


class Explorador(Agente):
    nome = "explorador"

    def executar(self, ctx: Contexto) -> dict:
        ctx.politica.exigir(self.nome, "ler_fontes")
        perfis = {}
        for view, fonte in ctx.sandbox.fontes.items():
            cols, linhas = ctx.sandbox.consultar(f"DESCRIBE {view}")
            total = ctx.sandbox.consultar(f"SELECT count(*) FROM {view}")[1][0][0]
            colunas = []
            for nome_col, tipo, *_ in linhas:
                q = f'"{nome_col}"'
                distintos, nulos = ctx.sandbox.consultar(
                    f"SELECT count(DISTINCT {q}), count(*) - count({q}) FROM {view}"
                )[1][0]
                amostra = [r[0] for r in ctx.sandbox.consultar(f"SELECT DISTINCT {q} FROM {view} WHERE {q} IS NOT NULL LIMIT 3")[1]]
                papel = "texto"
                t = tipo.upper()
                if t.startswith(NUMERICOS):
                    papel = "identificador" if _eh_identificador(nome_col, tipo, distintos, total) else "numero"
                if t.startswith(DATAS) or (_eh_data_por_nome(nome_col) and t.startswith(("VARCHAR", "DATE", "TIMESTAMP"))):
                    papel = "data"
                coluna = {"nome": nome_col, "tipo": tipo, "papel": papel, "distintos": distintos, "nulos": nulos, "amostra": [str(a) for a in amostra]}
                if papel != "data":  # LST-41: dado pessoal pelo formato dos valores, não pelo nome
                    valores = [r[0] for r in ctx.sandbox.consultar(
                        f"SELECT DISTINCT CAST({q} AS VARCHAR) FROM {view} WHERE {q} IS NOT NULL LIMIT 500")[1]]
                    pessoal = detectar_pessoal(valores, numerico=t.startswith(NUMERICOS))
                    if pessoal:
                        coluna["pessoal"] = pessoal
                        coluna["amostra"] = [f"(dado pessoal: {NOMES_PESSOAIS[pessoal]})"]  # nunca guardar CPF na nota
                # Coluna categórica (poucos valores): guarda os valores para o grill achar o recorte citado na pergunta.
                if papel == "texto" and 0 < distintos <= MAX_CATEGORIAS and distintos < total:
                    coluna["valores"] = [
                        str(r[0]) for r in ctx.sandbox.consultar(f"SELECT DISTINCT {q} FROM {view} WHERE {q} IS NOT NULL ORDER BY 1")[1]
                    ]
                colunas.append(coluna)
            # Chave candidata: única, ou quase única (>= 95%) com nome de identificador.
            # Quase única é o caso comum de registro reenviado: vira chave e a silver deduplica.
            chaves = [
                c["nome"]
                for c in sorted(colunas, key=lambda c: -c["distintos"])
                if c["nulos"] == 0
                and (
                    (c["distintos"] == total and c["papel"] != "numero")
                    or (c["distintos"] >= 0.95 * total and c["nome"].lower().rstrip("_").endswith(("id", "codigo", "numero")))
                )
            ]
            for c in colunas:
                c["repetidos"] = total - c["distintos"] if c["nome"] in chaves else 0
            perfil = {"view": view, "fonte": fonte.nome, "linhas": total, "colunas": colunas, "chaves_candidatas": chaves}
            perfis[view] = perfil
            self._gravar_nota(ctx, perfil)
        ctx.memoria["perfis"] = perfis
        self.anotar(ctx, "perfilou_fontes", {v: {"linhas": p["linhas"], "colunas": len(p["colunas"])} for v, p in perfis.items()})
        pessoais = {p["fonte"]: {c["nome"]: NOMES_PESSOAIS[c["pessoal"]] for c in p["colunas"] if c.get("pessoal")} for p in perfis.values()}
        pessoais = {f: cols for f, cols in pessoais.items() if cols}
        if pessoais:  # aviso no rastro da demanda: só nomes de coluna e o tipo, nunca valores
            self.anotar(ctx, "dados_pessoais", pessoais)
        return perfis

    def _gravar_nota(self, ctx: Contexto, perfil: dict) -> None:
        linhas = ["| Coluna | Tipo | Papel | Distintos | Nulos | Amostra |", "| --- | --- | --- | --- | --- | --- |"]
        for c in perfil["colunas"]:
            linhas.append(f"| {c['nome']} | {c['tipo']} | {c['papel']} | {c['distintos']} | {c['nulos']} | {', '.join(c['amostra'])} |")
        corpo = (
            f"# Fonte {perfil['fonte']}\n\n{perfil['linhas']} linhas. Chaves candidatas: {', '.join(perfil['chaves_candidatas']) or 'nenhuma'}.\n\n"
            "## Colunas\n\n" + "\n".join(linhas)
        )
        gravar_nota(
            ctx.pasta_tenant_caixa / "fontes",
            f"fonte-{perfil['fonte']}",
            f"Perfil da fonte {perfil['fonte']}: {perfil['linhas']} linhas, {len(perfil['colunas'])} colunas",
            "fonte",
            corpo,
            tags=[c["nome"] for c in perfil["colunas"]],
        )
