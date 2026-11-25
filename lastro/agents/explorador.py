"""Explorador: lê as fontes e escreve uma nota de fonte na Caixa do tenant."""

from __future__ import annotations

from ..caixa import gravar_nota
from .base import Agente, Contexto

NUMERICOS = ("INT", "DECIMAL", "DOUBLE", "FLOAT", "REAL", "NUMERIC", "HUGEINT", "BIGINT")
DATAS = ("DATE", "TIMESTAMP")
MAX_CATEGORIAS = 30


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
                    papel = "numero"
                if t.startswith(DATAS) or (_eh_data_por_nome(nome_col) and t.startswith(("VARCHAR", "DATE", "TIMESTAMP"))):
                    papel = "data"
                coluna = {"nome": nome_col, "tipo": tipo, "papel": papel, "distintos": distintos, "nulos": nulos, "amostra": [str(a) for a in amostra]}
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
