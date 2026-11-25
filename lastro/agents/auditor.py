"""Auditor técnico (camada 1): checa o pipeline e a resposta e gera o notebook de auditoria.

O notebook reproduz cada checagem em pandas, para o revisor de negócio (camada 2)
abrir no Google Colab e conferir sem depender da plataforma.
"""

from __future__ import annotations

import json

from .base import Agente, Contexto
from .construtores import ident


def br(v: object) -> str:
    """Número no formato brasileiro: 14.030.477,92."""
    return f"{float(v):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


class Auditor(Agente):
    nome = "auditor"

    def executar(self, ctx: Contexto) -> dict:
        ctx.politica.exigir(self.nome, "sandbox_temporario")
        m = ctx.memoria["modelo"]
        sb = ctx.sandbox
        um = lambda sql: sb.consultar(sql)[1][0][0]  # noqa: E731
        checks: list[dict] = []

        def check(nome: str, ok: bool, detalhe: str, grave: bool = True) -> None:
            checks.append({"checagem": nome, "ok": bool(ok), "detalhe": detalhe, "nivel": "erro" if grave else "aviso"})

        fonte_n = um(f"SELECT count(*) FROM {m['view']}")
        silver_n = um("SELECT count(*) FROM silver")
        fato_n = um("SELECT count(*) FROM fato")
        check("linhas: fonte → silver", True, f"{fonte_n} na fonte, {silver_n} na silver ({fonte_n - silver_n} removidas por filtro ou duplicidade)", grave=False)
        check("linhas: silver → fato", silver_n == fato_n, f"{silver_n} na silver, {fato_n} no fato")
        if m["chave"]:
            k = ident(m["chave"])
            dup = um(f"SELECT count(*) FROM (SELECT {k} FROM silver GROUP BY {k} HAVING count(*) > 1)")
            check("duplicidade na chave", dup == 0, f"{dup} chaves repetidas em '{m['chave']}' após a limpeza")
            dup_fonte = um(f'SELECT count(*) FROM (SELECT "{m["chave"]}" FROM {m["view"]} GROUP BY 1 HAVING count(*) > 1)')
            check("duplicidade na fonte", dup_fonte == 0, f"{dup_fonte} chaves repetidas na fonte original (tratadas na silver)", grave=False)
        perfil = ctx.memoria.get("perfis", {}).get(m["view"], {})
        cols_perfil = {c["nome"]: c for c in perfil.get("colunas", [])}
        med_sql = ident(m["medida"]) if m["medida"] else None
        for d in m["dimensoes"]:
            i = ident(d)
            # Card × tabela (caixa/global/metodos/conferencia-card-x-tabela.md): linha sem categoria entra no
            # total e some do gráfico por essa categoria. Dizer quanto some evita a pergunta "por que não fecha?".
            sem = sb.consultar(f"SELECT count(*), coalesce(sum({med_sql}), 0) FROM silver WHERE {i} IS NULL" if med_sql
                               else f"SELECT count(*), 0 FROM silver WHERE {i} IS NULL")[1][0]
            if sem[0]:
                valor = f" ({br(sem[1])} de {m['medida']})" if med_sql else ""
                check(f"fora do gráfico por {d}", False, f"{sem[0]} linhas{valor} sem {d}: entram no total e não aparecem "
                      f"em visual quebrado por {d}. Como mostrar essas linhas é regra do cliente: pergunte antes de mudar.", grave=False)
            qual = cols_perfil.get(d, {}).get("qualidade", {})
            regra = m.get("regras_texto", {}).get(d, {})
            if qual.get("variantes") and not regra.get("unificar_grafias"):
                check(f"grafias diferentes em {d}", False, f"{qual['variantes']} grupos com grafias diferentes do mesmo valor "
                      f"(ex.: {'; '.join(qual['exemplos_variantes'][:2])}): viram barras separadas. Se são o mesmo valor, só o cliente diz (pergunta do grill).", grave=False)
            if qual.get("marcadores_vazio") and not regra.get("vazios"):
                check(f"marcador de vazio em {d}", False, f"valores com cara de 'vazio' contando como categoria: {', '.join(qual['marcadores_vazio'])}. O cliente decide no grill se são vazio.", grave=False)
            if qual.get("acentos_quebrados"):
                check(f"acentos quebrados em {d}", False, f"{qual['acentos_quebrados']} valores com codificação errada (ex.: 'Ã§' no lugar de 'ç'): "
                      "o arquivo foi salvo em latin-1/cp1252 e lido como UTF-8", grave=False)
        for d in m["dimensoes"]:
            i = ident(d)
            orf = um(
                f"SELECT count(*) FROM silver s LEFT JOIN dim_{i} d ON s.{i} IS NOT DISTINCT FROM d.{i} WHERE d.{i}_id IS NULL AND s.{i} IS NOT NULL"
            )
            check(f"integridade: dim_{i}", orf == 0, f"{orf} linhas sem correspondência na dimensão")
        if m["medida"]:
            med = ident(m["medida"])
            soma_silver = um(f"SELECT coalesce(sum({med}), 0) FROM silver")
            soma_fato = um(f"SELECT coalesce(sum({med}), 0) FROM fato")
            check("valores: silver = fato", abs(float(soma_silver) - float(soma_fato)) < 0.01, f"soma de {m['medida']}: silver {br(soma_silver)} · fato {br(soma_fato)}")
            nulos = um(f"SELECT count(*) FROM silver WHERE {med} IS NULL")
            check("nulos na medida", nulos == 0, f"{nulos} linhas sem {m['medida']}: contam em 'quantidade' e somem de tabela e "
                  "gráfico de valor (é a diferença clássica entre o cartão e a tabela)", grave=False)
            neg = um(f"SELECT count(*) FROM silver WHERE {med} < 0")
            check("valores negativos", neg == 0, f"{neg} linhas com {m['medida']} negativo", grave=False)
            r = ctx.memoria.get("resposta", {})
            if r.get("total") is not None:
                check("resposta: total recalculado", abs(float(r["total"]) - float(soma_silver)) < 0.01, f"total da resposta {br(r['total'])} · recalculado na silver {br(soma_silver)}")
        if m["data"]:
            dt = ident(m["data"])
            sem_data = um(f"SELECT count(*) FROM silver WHERE {dt} IS NULL")
            futuras = um(f"SELECT count(*) FROM silver WHERE {dt} > current_date")
            check("datas inválidas ou vazias", sem_data == 0, f"{sem_data} linhas sem {m['data']} válida", grave=False)
            check("datas no futuro", futuras == 0, f"{futuras} linhas com {m['data']} depois de hoje", grave=False)
        aprovado = all(c["ok"] for c in checks if c["nivel"] == "erro")
        caminho = ctx.pasta_demanda / "auditoria_colab.ipynb"
        caminho.write_text(json.dumps(self._notebook(ctx, m, checks), ensure_ascii=False, indent=1), encoding="utf-8")
        resultado = {"aprovado_camada1": aprovado, "checagens": checks, "notebook": caminho.name}
        ctx.memoria["auditoria"] = resultado
        self.anotar(ctx, "auditou", {"aprovado": aprovado, "falhas": [c["checagem"] for c in checks if not c["ok"]]})
        return resultado

    def _notebook(self, ctx: Contexto, m: dict, checks: list[dict]) -> dict:
        def md(t: str) -> dict:
            return {"cell_type": "markdown", "metadata": {}, "source": t}

        def code(t: str) -> dict:
            return {"cell_type": "code", "metadata": {}, "execution_count": None, "outputs": [], "source": t}

        r = ctx.memoria.get("resposta", {})
        celulas = [
            md(f"# Auditoria da demanda {ctx.demanda_id}\n\n**Pergunta:** {ctx.pergunta}\n\nCamada 1 (técnica) já rodou na plataforma. "
               "Este notebook é a **camada 2**: o revisor de negócio refaz as contas sozinho e compara com o painel.\n\n"
               "Suba os arquivos da pasta `gold/` desta demanda quando o Colab pedir."),
            code("import pandas as pd\ntry:\n    from google.colab import files\n    files.upload()  # silver.parquet, fato.parquet e dims\nexcept ImportError:\n    pass  # rodando local: deixe os parquet na mesma pasta"),
            code("silver = pd.read_parquet('silver.parquet')\nfato = pd.read_parquet('fato.parquet')\nprint(len(silver), 'linhas na silver;', len(fato), 'no fato')\nsilver.head()"),
            md("## Resultado da camada 1\n\n| Checagem | OK | Detalhe |\n| --- | --- | --- |\n" + "\n".join(f"| {c['checagem']} | {'sim' if c['ok'] else 'NÃO'} | {c['detalhe']} |" for c in checks)),
        ]
        if m["chave"]:
            k = ident(m["chave"])
            celulas += [md("## Duplicidade na chave"), code(f"dup = silver['{k}'].duplicated().sum()\nprint('chaves repetidas:', dup)\nassert dup == 0")]
        if m["medida"]:
            med = ident(m["medida"])
            celulas += [
                md("## Valores: a soma bate entre silver e fato?"),
                code(f"print(silver['{med}'].sum(), fato['{med}'].sum())\nassert abs(silver['{med}'].sum() - fato['{med}'].sum()) < 0.01"),
            ]
            if r.get("total") is not None:
                celulas += [md("## A resposta entregue"), code(f"total_entregue = {r['total']!r}\nprint('recalculado:', silver['{med}'].sum(), '· entregue:', total_entregue)")]
        for d in m["dimensoes"]:
            i = ident(d)
            celulas += [md(f"## Integridade: dim_{i}"), code(f"dim = pd.read_parquet('dim_{i}.parquet')\nprint('sem correspondência:', (~silver['{i}'].dropna().isin(dim['{i}'])).sum())")]
        if r.get("sql"):
            celulas += [md("## Consulta usada na resposta\n\n```sql\n" + r["sql"] + "\n```\n\nRefaça o agrupamento abaixo com pandas e compare com o relatório.")]
        celulas.append(md("## Parecer do revisor\n\n- [ ] Números conferem com o relatório\n- [ ] Regras de negócio corretas\n- Observações:"))
        return {"nbformat": 4, "nbformat_minor": 5, "metadata": {"colab": {"name": f"auditoria_demanda_{ctx.demanda_id}.ipynb"}, "kernelspec": {"name": "python3", "display_name": "Python 3"}}, "cells": celulas}
