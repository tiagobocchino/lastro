"""Painel HTML de entrega (LST-55): filtros → 4 cartões → gráfico principal → ranking → tabela de conferência.

Decisões do grill do Tiago (26/11):
- a comparação dos cartões é com o **mesmo período do ano anterior** (jan até o último mês com dado);
- o ranking mostra o **top 10 + "outros"** e o % do total;
- o painel tem **filtros interativos** dentro do próprio arquivo.

Como funciona: um cubo pequeno, agregado por (filtros × eixos × mês), vai embutido no HTML. O Python desenha a
primeira tela com as mesmas contas que o script refaz ao filtrar. Por isso o painel funciona sem JavaScript
(a demonstração do site abre num iframe sem script) e o total do cartão é o mesmo da tabela de conferência.
"""

from __future__ import annotations

import json
from decimal import Decimal
from pathlib import Path
from typing import Any

import duckdb

MESES = ["jan", "fev", "mar", "abr", "mai", "jun", "jul", "ago", "set", "out", "nov", "dez"]
LIMITE_CUBO = 15_000  # linhas do cubo embutido (~1 MB); acima disso os filtros saem e o painel fica fixo
REAGREGAVEL = {"soma", "contagem", "media", "minimo", "maximo"}  # "distintos" não se soma entre grupos
SOMAVEL = {"soma", "contagem"}  # só estas têm "outros" e % do total
VAZIO = "(vazio)"
PREFERIDOS = ("empresa", "company", "regiao", "estado", "uf", "segmento", "setor", "status")


def _q(p: Path) -> str:
    return str(p).replace("'", "''")


def _num(v: Any) -> str:
    if v is None:
        return "—"
    f = float(v)
    s = f"{f:,.2f}" if not f.is_integer() else f"{f:,.0f}"
    return s.replace(",", "X").replace(".", ",").replace("X", ".")


def _pct(v: float | None) -> str:
    return "—" if v is None else f"{v * 100:+.1f}%".replace(".", ",")


def _p1(frac: float | None) -> str:
    """Parte do total com uma casa: 0.183 → 18,3%."""
    return "—" if frac is None else f"{frac * 100:.1f}%".replace(".", ",")


def _e(v: Any) -> str:
    import html

    return html.escape("" if v is None else str(v))


# ---- o cubo ----------------------------------------------------------------------------------

def _dims_do_gold(con: duckdb.DuckDBPyConnection, gold: Path) -> list[str]:
    cols = {r[0] for r in con.execute(f"DESCRIBE SELECT * FROM read_parquet('{_q(gold / 'fato.parquet')}')").fetchall()}
    dims = [p.stem[4:] for p in sorted(gold.glob("dim_*.parquet")) if p.stem != "dim_data" and f"{p.stem[4:]}_id" in cols]
    return sorted(dims, key=lambda d: (not any(x in d for x in PREFERIDOS), dims.index(d)))


def _filtros(spec: dict, con: duckdb.DuckDBPyConnection, gold: Path, eixos: set[str], tem_tempo: bool) -> list[str]:
    """Até dois filtros de dimensão (2 a 30 valores, fora os eixos dos visuais) e o ano, quando há mais de um."""
    candidatos = spec.get("filtros")
    dims = _dims_do_gold(con, gold)
    lista = [d for d in (candidatos if candidatos is not None else dims) if d in dims and d not in eixos]
    escolhidos = []
    for d in lista:
        n = con.execute(f'SELECT count(DISTINCT "{d}") FROM "dim_{d}"').fetchall()[0][0]
        if 2 <= n <= 30:
            escolhidos.append(d)
        if len(escolhidos) == 2:
            break
    if (tem_tempo and (candidatos is None or "ano" in candidatos)
            and con.execute("SELECT count(DISTINCT ano) FROM fato JOIN dim_data USING (data)").fetchall()[0][0] > 1):
        escolhidos.append("ano")
    return escolhidos


def _colunas_medida(m: dict) -> list[tuple[str, str]]:
    col = f'fato."{m["coluna"]}"'
    a = m["agregacao"]
    if a == "soma":
        return [(f"{m['id']}__s", f"sum({col})")]
    if a == "contagem":
        return [(f"{m['id']}__c", f"count({col})")]
    if a == "media":
        return [(f"{m['id']}__s", f"sum({col})"), (f"{m['id']}__c", f"count({col})")]
    if a == "minimo":
        return [(f"{m['id']}__min", f"min({col})")]
    if a == "maximo":
        return [(f"{m['id']}__max", f"max({col})")]
    return []


def cubo(spec: dict, gold: Path) -> dict:
    """Linhas agregadas por (filtros × eixos × ano/mês) com registros e as partes de cada medida reagregável."""
    con = duckdb.connect()
    try:
        for arq in gold.glob("*.parquet"):
            con.execute(f"CREATE VIEW \"{arq.stem}\" AS SELECT * FROM read_parquet('{_q(arq)}')")
        tem_tempo = (gold / "dim_data.parquet").exists()
        eixos = {v["eixo"] for v in spec["visuais"] if v.get("eixo") and v["eixo"] not in {"ano", "ano_mes"}}
        filtros = _filtros(spec, con, gold, eixos, tem_tempo)
        medidas = [m for m in spec["medidas"] if m["agregacao"] in REAGREGAVEL]
        partes = [c for m in medidas for c in _colunas_medida(m)]
        while True:
            dims = [d for d in filtros if d != "ano"] + sorted(eixos)
            sel = [f'coalesce(CAST("dim_{d}"."{d}" AS VARCHAR), \'{VAZIO}\') AS "{d}"' for d in dims]
            joins = [f'LEFT JOIN "dim_{d}" USING ("{d}_id")' for d in dims]
            if tem_tempo:
                sel += ["dim_data.ano AS ano", "dim_data.mes AS mes", "dim_data.ano_mes AS ano_mes"]
                joins.append("LEFT JOIN dim_data USING (data)")
            sel += ["count(*) AS registros"] + [f'{expr} AS "{nome}"' for nome, expr in partes]
            grupos = ", ".join(str(i + 1) for i in range(len(dims) + (3 if tem_tempo else 0))) or "()"
            sql = f"SELECT {', '.join(sel)} FROM fato {' '.join(joins)} GROUP BY {grupos}"
            res = con.execute(sql)
            nomes = [d[0] for d in res.description]
            linhas = res.fetchall()
            if len(linhas) <= LIMITE_CUBO or not [f for f in filtros if f != "ano"]:
                break
            filtros = filtros[:-1] if filtros[-1] != "ano" else [*filtros[:-2], "ano"]  # tira o último filtro de dimensão
        valores = {f: sorted({r[nomes.index(f)] for r in linhas if r[nomes.index(f)] is not None}, key=str) for f in filtros}
        return {"colunas": nomes, "linhas": [[(float(x) if isinstance(x, Decimal) else x) for x in r] for r in linhas],
                "filtros": filtros, "valores": valores, "tempo": tem_tempo, "grande": len(linhas) > LIMITE_CUBO}
    finally:
        con.close()


# ---- as contas (o script do painel faz as mesmas) ------------------------------------------------

def _valor(m: dict, linhas: list[list], ix: dict[str, int]) -> float | None:
    a, i = m["agregacao"], m["id"]
    if a == "soma":
        return sum(r[ix[f"{i}__s"]] or 0 for r in linhas)
    if a == "contagem":
        return sum(r[ix[f"{i}__c"]] or 0 for r in linhas)
    if a == "media":
        s, c = sum(r[ix[f"{i}__s"]] or 0 for r in linhas), sum(r[ix[f"{i}__c"]] or 0 for r in linhas)
        return s / c if c else None
    vals = [r[ix[f"{i}__{'min' if a == 'minimo' else 'max'}"]] for r in linhas]
    vals = [v for v in vals if v is not None]
    return (min(vals) if a == "minimo" else max(vals)) if vals else None


def _grupos(m: dict, linhas: list[list], ix: dict[str, int], eixo: str) -> list[tuple[Any, float | None]]:
    por: dict[Any, list] = {}
    for r in linhas:
        por.setdefault(r[ix[eixo]], []).append(r)
    return [(k, _valor(m, v, ix)) for k, v in por.items()]


def contas(spec: dict, c: dict, escolha: dict[str, str] | None = None) -> dict:
    """Cartões e séries do painel para uma escolha de filtros (None = todos)."""
    ix = {n: i for i, n in enumerate(c["colunas"])}
    escolha = escolha or {}
    linhas = [r for r in c["linhas"] if all(str(r[ix[f]]) == str(v) for f, v in escolha.items() if v not in ("", None))]
    med = {m["id"]: m for m in spec["medidas"]}
    kpi = next((v for v in spec["visuais"] if v["tipo"] == "kpi"), None)
    m = med[kpi["medida"]] if kpi else spec["medidas"][0]
    out: dict[str, Any] = {"medida": m["id"], "registros": sum(r[ix["registros"]] for r in linhas)}
    out["total"] = _valor(m, linhas, ix) if m["agregacao"] in REAGREGAVEL else None
    out["media"] = (out["total"] / out["registros"]) if m["agregacao"] == "soma" and out["registros"] else None
    out["comparacao"] = None
    if c["tempo"] and m["agregacao"] in REAGREGAVEL:
        com_data = [r for r in linhas if r[ix["ano"]] is not None]
        if com_data:
            ano = int(max(r[ix["ano"]] for r in com_data))
            mes = int(max(r[ix["mes"]] for r in com_data if int(r[ix["ano"]]) == ano))
            atual = _valor(m, [r for r in com_data if int(r[ix["ano"]]) == ano and int(r[ix["mes"]]) <= mes], ix)
            anterior = [r for r in com_data if int(r[ix["ano"]]) == ano - 1 and int(r[ix["mes"]]) <= mes]
            base = _valor(m, anterior, ix) if anterior else None
            out["comparacao"] = {"ano": ano, "mes": mes, "atual": atual, "anterior": base,
                                 "variacao": (atual / base - 1) if atual is not None and base else None}
    for v in spec["visuais"]:
        mv = med[v["medida"]]
        if v["tipo"] == "kpi":
            out[v["id"]] = _valor(mv, linhas, ix) if mv["agregacao"] in REAGREGAVEL else None
        elif mv["agregacao"] not in REAGREGAVEL:
            out[v["id"]] = None
        elif v["eixo"] in ("ano_mes", "ano"):
            out[v["id"]] = sorted(((k, val) for k, val in _grupos(mv, [r for r in linhas if r[ix["ano"]] is not None], ix, v["eixo"])),
                                  key=lambda x: str(x[0]))
        else:
            g = sorted(_grupos(mv, linhas, ix, v["eixo"]), key=lambda x: -(x[1] or 0))
            total = sum(x[1] or 0 for x in g) if mv["agregacao"] in SOMAVEL else None
            if v["tipo"] == "barras":
                topo = g[:10]
                if len(g) > 10 and mv["agregacao"] in SOMAVEL:
                    topo.append((f"outros ({len(g) - 10})", sum(x[1] or 0 for x in g[10:])))
                g = topo
            out[v["id"]] = {"linhas": [(k, val, (val / total) if total and val is not None else None) for k, val in g], "total": total,
                            "registros": out["registros"]}
    return out


# ---- HTML ------------------------------------------------------------------------------------------

def _rot_filtro(f: str) -> str:
    return {"ano": "Ano", "company": "Empresa"}.get(f, f.replace("_", " ").capitalize())


def _corpo(v: dict, d: Any, mv: dict) -> str:
    if d is None:
        return '<p class="quieta">Esta medida (valores distintos) não se soma entre filtros: use o Power BI para esta visão.</p>'
    if v["tipo"] == "kpi":
        return f'<b class="kpi">{_num(d)}</b>'
    if v["tipo"] == "linha":
        if not d:
            return '<p class="quieta">Sem dados no filtro escolhido.</p>'
        vals = [float(x[1] or 0) for x in d]
        maior = max(vals) or 1
        n = max(len(vals) - 1, 1)
        poli = " ".join(f"{100 * i / n:.2f},{100 - 92 * y / maior:.2f}" for i, y in enumerate(vals))
        tabela = "".join(f"<tr><td>{_e(x[0])}</td><td class='n'>{_num(x[1])}</td></tr>" for x in d)
        return (f'<div class="eixo-y"><span>{_num(maior)}</span><span>{_num(maior / 2)}</span><span>0</span></div>'
                f'<svg viewBox="0 0 100 100" preserveAspectRatio="none" role="img" aria-label="{_e(v["titulo"])}">'
                f'<line x1="0" y1="54" x2="100" y2="54" class="grade-l"/><polyline points="{poli}" fill="none" stroke="var(--ouro)" stroke-width="2" vector-effect="non-scaling-stroke"/></svg>'
                f'<div class="datas"><span>{_e(d[0][0])}</span><span>{_e(d[-1][0])}</span></div>'
                f'<details><summary>ver os números</summary><div class="rolar"><table><tbody>{tabela}</tbody></table></div></details>')
    linhas = d["linhas"]
    if not linhas:
        return '<p class="quieta">Sem dados no filtro escolhido.</p>'
    if v["tipo"] == "barras":
        maior = max((abs(x[1] or 0) for x in linhas), default=0) or 1
        return '<div class="barras">' + "".join(
            f'<div class="linha-b"><span title="{_e(x[0])}">{_e(x[0])}</span><i style="width:{100 * abs(x[1] or 0) / maior:.1f}%"></i>'
            f'<b>{_num(x[1])}{f" <small>{_p1(x[2])}</small>" if x[2] is not None else ""}</b></div>' for x in linhas) + "</div>"
    pct = d["total"] is not None
    corpo = "".join(f"<tr><td>{_e(x[0])}</td><td class='n'>{_num(x[1])}</td>{f'<td class=n>{_p1(x[2])}</td>' if pct else ''}</tr>"
                    for x in linhas)
    rodape = f"<tfoot><tr><td>Total</td><td class='n'>{_num(d['total'])}</td><td class='n'>100%</td></tr></tfoot>" if pct else ""
    return (f'<div class="rolar"><table><thead><tr><th>{_e(v["eixo"].replace("_", " "))}</th><th class="n">{_e(mv["nome"])}</th>'
            f'{"<th class=n>% do total</th>" if pct else ""}</tr></thead><tbody>{corpo}</tbody>{rodape}</table></div>')


def _cartoes(spec: dict, k: dict) -> str:
    med = {m["id"]: m for m in spec["medidas"]}
    m = med[k["medida"]]
    cards = [(f"{m['nome']} (total)", _num(k["total"]), ""), ("Registros", _num(k["registros"]), "")]
    if k["media"] is not None:
        cards.append(("Média por registro", _num(k["media"]), ""))
    comp = k["comparacao"]
    if comp:
        var = comp["variacao"]
        seta = "" if var is None else ("▲ " if var >= 0 else "▼ ")
        classe = "" if var is None else ("sobe" if var >= 0 else "desce")
        base = f"{comp['ano'] - 1}: {_num(comp['anterior'])}" if comp["anterior"] is not None else f"sem dados de {comp['ano'] - 1}"
        cards.append((f"{comp['ano']} até {MESES[comp['mes'] - 1]} vs mesmo período", _num(comp["atual"]),
                      f'<span class="delta {classe}">{seta}{_pct(var)}</span> <span class="quieta">{base}</span>'))
    return "".join(f'<div class="cartao"><span class="rot">{_e(r)}</span><b data-k="{i}">{val}</b><span class="sub" data-s="{i}">{sub}</span></div>'
                   for i, (r, val, sub) in enumerate(cards))


def html(spec: dict, gold: Path, origem: str, c: dict | None = None) -> str:
    c = c or cubo(spec, gold)
    k = contas(spec, c)
    med = {m["id"]: m for m in spec["medidas"]}
    tem_linha = any(v["tipo"] == "linha" for v in spec["visuais"])
    tem_barras = any(v["tipo"] == "barras" for v in spec["visuais"])
    blocos = []
    for i, v in enumerate(spec["visuais"]):
        if v["tipo"] == "kpi" and i == next(j for j, x in enumerate(spec["visuais"]) if x["tipo"] == "kpi"):
            continue  # o primeiro KPI vira os cartões
        largura = {"kpi": "c3", "linha": "c8" if tem_barras else "c12", "barras": "c4" if tem_linha else "c12", "tabela": "c12"}[v["tipo"]]
        blocos.append(f'<section class="bloco {v["tipo"]} {largura}" id="{_e(v["id"])}"><h2>{_e(v["titulo"])}</h2>'
                      f'<div class="corpo">{_corpo(v, k[v["id"]], med[v["medida"]])}</div></section>')
    filtros = "".join(
        f'<label>{_e(_rot_filtro(f))}<select data-f="{_e(f)}"><option value="">{"todos" if f == "ano" else "todas"}</option>'
        + "".join(f'<option value="{_e(x)}">{_e(int(x) if f == "ano" else x)}</option>' for x in c["valores"][f]) + "</select></label>"
        for f in c["filtros"])
    dados = json.dumps({"spec": {"medidas": spec["medidas"], "visuais": spec["visuais"]}, "cubo": c}, ensure_ascii=False)
    dados = dados.replace("<", "\\u003c").replace(">", "\\u003e").replace("&", "\\u0026")  # nada fecha o <script>
    return f"""<!doctype html>
<html lang="pt-BR"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>{_e(spec['titulo'][:60])}</title>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Bricolage+Grotesque:opsz,wght@12..96,700&family=IBM+Plex+Mono:wght@400;500&family=IBM+Plex+Sans:wght@400;600&display=swap">
<style>
:root {{ --chao:#EEF1F3; --sup:#FFFFFF; --sup-2:#F6F8F9; --tinta:#111820; --quieta:#56606B; --linha:#D6DCE2; --campo:#8C959F; --ouro:#B58324; --ok:#2E6B4E; --erro:#A3392B;
  --f-disp:'Bricolage Grotesque','Segoe UI',system-ui,sans-serif; --f-texto:'IBM Plex Sans','Segoe UI',system-ui,sans-serif; --f-dado:'IBM Plex Mono',ui-monospace,monospace }}
@media (prefers-color-scheme: dark) {{ :root:not([data-theme="light"]) {{ --chao:#0D1116; --sup:#151B22; --sup-2:#1B222B; --tinta:#E7ECF1; --quieta:#98A3AE; --linha:#26303A; --campo:#5E6974; --ouro:#E1B24F; --ok:#7CC4A0; --erro:#F08A7C; color-scheme:dark }} }}
:root[data-theme="dark"] {{ --chao:#0D1116; --sup:#151B22; --sup-2:#1B222B; --tinta:#E7ECF1; --quieta:#98A3AE; --linha:#26303A; --campo:#5E6974; --ouro:#E1B24F; --ok:#7CC4A0; --erro:#F08A7C; color-scheme:dark }}
* {{ box-sizing:border-box }} body {{ margin:0; background:var(--chao); color:var(--tinta); font:15px/1.5 var(--f-texto) }}
main {{ max-width:1240px; margin:0 auto; padding-block:24px 64px; padding-left:max(16px, env(safe-area-inset-left, 0px)); padding-right:max(16px, env(safe-area-inset-right, 0px)) }}
h1 {{ font:700 26px/1.2 var(--f-disp); margin:0 0 4px; text-wrap:balance }} h2 {{ font:600 15px var(--f-disp); margin:0 0 12px }}
.quieta {{ color:var(--quieta); font-size:13px }} main > .quieta {{ margin:0 0 16px }}
.filtros {{ position:sticky; top:0; z-index:1; display:flex; flex-wrap:wrap; align-items:end; gap:10px; padding:10px 0 12px; margin-bottom:12px; background:var(--chao); border-bottom:1px solid var(--linha) }}
.filtros label {{ display:grid; gap:4px; font:500 11px var(--f-dado); text-transform:uppercase; letter-spacing:.08em; color:var(--quieta) }}
.filtros select {{ min-height:44px; min-width:150px; padding:0 12px; border-radius:8px; background:var(--sup); color:var(--tinta); border:1px solid var(--campo); font:15px var(--f-texto); text-transform:none; letter-spacing:0 }}
.filtros button {{ min-height:44px; padding:0 14px; border-radius:8px; border:1px solid var(--campo); background:transparent; color:var(--tinta); font:600 14px var(--f-texto); cursor:pointer }}
.cartoes {{ display:grid; grid-template-columns:repeat(auto-fit, minmax(min(220px, 100%), 1fr)); gap:12px; margin-bottom:12px }}
.cartao {{ background:var(--sup); border:1px solid var(--linha); border-radius:10px; padding:14px 16px; display:grid; gap:4px; min-width:0 }}
.cartao .rot {{ font:500 11px var(--f-dado); text-transform:uppercase; letter-spacing:.08em; color:var(--quieta) }}
.cartao b {{ font:700 28px/1.15 var(--f-disp); font-variant-numeric:tabular-nums; overflow-wrap:anywhere }}
.sub {{ font-size:13px }} .delta {{ font:600 13px var(--f-dado) }} .delta.sobe {{ color:var(--ok) }} .delta.desce {{ color:var(--erro) }}
.grade {{ display:grid; grid-template-columns:repeat(12, minmax(0, 1fr)); gap:12px }}
.bloco.linha {{ order:-1 }} .c3 {{ grid-column:span 3 }} .c4 {{ grid-column:span 4 }} .c8 {{ grid-column:span 8 }} .c12 {{ grid-column:1/-1 }}
.bloco {{ background:var(--sup); border:1px solid var(--linha); border-radius:10px; padding:16px; min-width:0 }}
.kpi {{ font:700 30px var(--f-disp); font-variant-numeric:tabular-nums }}
.barras {{ display:grid; gap:7px }} .linha-b {{ display:grid; grid-template-columns:minmax(70px, 34%) 1fr auto; gap:8px; align-items:center; font-size:13px }}
.linha-b span {{ overflow:hidden; text-overflow:ellipsis; white-space:nowrap }} .linha-b i {{ height:10px; background:var(--ouro); border-radius:2px; min-width:2px }}
.linha-b b {{ font:500 12px var(--f-dado); font-variant-numeric:tabular-nums; text-align:right }} .linha-b small {{ color:var(--quieta); font-weight:400 }}
.linha .corpo {{ display:grid; grid-template-columns:auto 1fr; column-gap:8px }}
.eixo-y {{ display:flex; flex-direction:column; justify-content:space-between; font:11px var(--f-dado); color:var(--quieta); text-align:right; height:200px; padding-block:8px 0 }}
svg {{ width:100%; height:200px; display:block; border-bottom:1px solid var(--linha); border-left:1px solid var(--linha) }} .grade-l {{ stroke:var(--linha); stroke-dasharray:2 3; vector-effect:non-scaling-stroke }}
.datas {{ grid-column:2; display:flex; justify-content:space-between; font:12px var(--f-dado); color:var(--quieta); margin-top:6px }}
.linha details {{ grid-column:1/-1; margin-top:8px; font-size:13px }} summary {{ cursor:pointer; color:var(--quieta) }}
.rolar {{ overflow-x:auto }} table {{ border-collapse:collapse; width:100%; font-size:14px }}
th, td {{ text-align:left; padding:7px 10px; border-bottom:1px solid var(--linha) }} th {{ color:var(--quieta); font-weight:600 }}
.n {{ text-align:right; font-family:var(--f-dado); font-variant-numeric:tabular-nums }}
tfoot td {{ font-weight:600; border-top:2px solid var(--tinta); border-bottom:0 }}
@media (max-width: 900px) {{ .c3 {{ grid-column:span 6 }} .c4, .c8 {{ grid-column:1/-1 }} }}
@media (max-width: 520px) {{ .c3 {{ grid-column:1/-1 }} .filtros select {{ min-width:0; width:100% }} .filtros label {{ flex:1 1 140px }} .cartao b {{ font-size:24px }} }}
</style></head><body><main>
<h1>{_e(spec['titulo'])}</h1>
<p class="quieta">{_e(origem)}</p>
{f'<div class="filtros" id="filtros" hidden>{filtros}<button type="button" id="limpar">limpar filtros</button></div>' if c["filtros"] else ""}
<div class="cartoes" id="cartoes">{_cartoes(spec, k)}</div>
<div class="grade">{''.join(blocos)}</div>
<p class="quieta" style="margin-top:14px">A soma da tabela de conferência é o total do primeiro cartão. {"Filtros mudam todos os números da página." if c["filtros"] else ""}</p>
</main>
<script type="application/json" id="dados">{dados}</script>
<script>{_SCRIPT}</script>
</body></html>
"""


# O mesmo cálculo do `contas`, no navegador, para os filtros. Sem biblioteca; desenha só com textContent e escape.
_SCRIPT = r"""
(() => {
  const D = JSON.parse(document.getElementById("dados").textContent), S = D.spec, C = D.cubo;
  const ix = Object.fromEntries(C.colunas.map((n, i) => [n, i]));
  const MESES = ["jan","fev","mar","abr","mai","jun","jul","ago","set","out","nov","dez"];
  const REAG = new Set(["soma","contagem","media","minimo","maximo"]), SOMA = new Set(["soma","contagem"]);
  const esc = (v) => String(v ?? "").replace(/[&<>"']/g, (c) => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"})[c]);
  const num = (v) => v == null ? "—" : Number(v).toLocaleString("pt-BR", { minimumFractionDigits: Number.isInteger(+v) ? 0 : 2, maximumFractionDigits: Number.isInteger(+v) ? 0 : 2 });
  const p1 = (f) => f == null ? "—" : (f * 100).toLocaleString("pt-BR", { minimumFractionDigits: 1, maximumFractionDigits: 1 }) + "%";
  const pct = (v) => v == null ? "—" : (v >= 0 ? "+" : "") + (v * 100).toLocaleString("pt-BR", { minimumFractionDigits: 1, maximumFractionDigits: 1 }) + "%";
  const med = Object.fromEntries(S.medidas.map((m) => [m.id, m]));
  function valor(m, L) {
    const s = (k) => L.reduce((a, r) => a + (r[ix[m.id + k]] || 0), 0), a = m.agregacao;
    if (a === "soma") return s("__s"); if (a === "contagem") return s("__c");
    if (a === "media") { const c = s("__c"); return c ? s("__s") / c : null; }
    const vs = L.map((r) => r[ix[m.id + (a === "minimo" ? "__min" : "__max")]]).filter((v) => v != null);
    return vs.length ? (a === "minimo" ? Math.min(...vs) : Math.max(...vs)) : null;
  }
  function grupos(m, L, eixo) { const g = new Map(); L.forEach((r) => { const k = r[ix[eixo]]; if (!g.has(k)) g.set(k, []); g.get(k).push(r); }); return [...g].map(([k, v]) => [k, valor(m, v)]); }
  function desenhar() {
    const esc_ = Object.fromEntries([...document.querySelectorAll("[data-f]")].map((s) => [s.dataset.f, s.value]));
    const L = C.linhas.filter((r) => Object.entries(esc_).every(([f, v]) => v === "" || String(r[ix[f]]) === v));
    const kpi = S.visuais.find((v) => v.tipo === "kpi"), m = kpi ? med[kpi.medida] : S.medidas[0];
    const regs = L.reduce((a, r) => a + r[ix.registros], 0), total = REAG.has(m.agregacao) ? valor(m, L) : null;
    const vals = [num(total), num(regs)];
    if (m.agregacao === "soma") vals.push(regs ? num(total / regs) : "—");
    let sub = null;
    if (C.tempo && REAG.has(m.agregacao)) {
      const T = L.filter((r) => r[ix.ano] != null);
      if (T.length) {
        const ano = Math.max(...T.map((r) => r[ix.ano])), mes = Math.max(...T.filter((r) => r[ix.ano] === ano).map((r) => r[ix.mes]));
        const atual = valor(m, T.filter((r) => r[ix.ano] === ano && r[ix.mes] <= mes));
        const ant = T.filter((r) => r[ix.ano] === ano - 1 && r[ix.mes] <= mes), base = ant.length ? valor(m, ant) : null;
        const v = atual != null && base ? atual / base - 1 : null;
        vals.push(num(atual));
        sub = { rot: `${ano} até ${MESES[mes - 1]} vs mesmo período`, html: `<span class="delta ${v == null ? "" : v >= 0 ? "sobe" : "desce"}">${v == null ? "" : v >= 0 ? "▲ " : "▼ "}${pct(v)}</span> <span class="quieta">${base != null ? (ano - 1) + ": " + num(base) : "sem dados de " + (ano - 1)}</span>` };
      } else vals.push("—");
    }
    vals.forEach((t, i) => { const b = document.querySelector(`[data-k="${i}"]`); if (b) b.textContent = t; });
    const ult = document.querySelector(`[data-k="${vals.length - 1}"]`);
    if (sub && ult) { ult.previousElementSibling.textContent = sub.rot; document.querySelector(`[data-s="${vals.length - 1}"]`).innerHTML = sub.html; }
    const primeiro = S.visuais.indexOf(kpi);
    S.visuais.forEach((v, i) => {
      const el = document.querySelector(`#${CSS.escape(v.id)} .corpo`); if (!el || i === primeiro) return;
      const mv = med[v.medida]; if (!REAG.has(mv.agregacao)) return;
      if (v.tipo === "kpi") { el.innerHTML = `<b class="kpi">${esc(num(valor(mv, L)))}</b>`; return; }
      if (v.eixo === "ano_mes" || v.eixo === "ano") {
        const d = grupos(mv, L.filter((r) => r[ix.ano] != null), v.eixo).sort((a, b) => String(a[0]).localeCompare(String(b[0])));
        if (!d.length) { el.innerHTML = '<p class="quieta">Sem dados no filtro escolhido.</p>'; return; }
        const vs = d.map((x) => +(x[1] || 0)), maior = Math.max(...vs) || 1, n = Math.max(vs.length - 1, 1);
        const poli = vs.map((y, i) => `${(100 * i / n).toFixed(2)},${(100 - 92 * y / maior).toFixed(2)}`).join(" ");
        el.innerHTML = `<div class="eixo-y"><span>${num(maior)}</span><span>${num(maior / 2)}</span><span>0</span></div><svg viewBox="0 0 100 100" preserveAspectRatio="none" role="img" aria-label="${esc(v.titulo)}"><line x1="0" y1="54" x2="100" y2="54" class="grade-l"/><polyline points="${poli}" fill="none" stroke="var(--ouro)" stroke-width="2" vector-effect="non-scaling-stroke"/></svg><div class="datas"><span>${esc(d[0][0])}</span><span>${esc(d[d.length - 1][0])}</span></div><details><summary>ver os números</summary><div class="rolar"><table><tbody>${d.map((x) => `<tr><td>${esc(x[0])}</td><td class="n">${num(x[1])}</td></tr>`).join("")}</tbody></table></div></details>`;
        return;
      }
      let g = grupos(mv, L, v.eixo).sort((a, b) => (b[1] || 0) - (a[1] || 0));
      const tot = SOMA.has(mv.agregacao) ? g.reduce((a, x) => a + (x[1] || 0), 0) : null;
      if (!g.length) { el.innerHTML = '<p class="quieta">Sem dados no filtro escolhido.</p>'; return; }
      if (v.tipo === "barras") {
        const resto = g.slice(10); g = g.slice(0, 10);
        if (resto.length && SOMA.has(mv.agregacao)) g.push([`outros (${resto.length})`, resto.reduce((a, x) => a + (x[1] || 0), 0)]);
        const maior = Math.max(...g.map((x) => Math.abs(x[1] || 0))) || 1;
        el.innerHTML = `<div class="barras">${g.map((x) => `<div class="linha-b"><span title="${esc(x[0])}">${esc(x[0])}</span><i style="width:${(100 * Math.abs(x[1] || 0) / maior).toFixed(1)}%"></i><b>${num(x[1])}${tot ? ` <small>${p1((x[1] || 0) / tot)}</small>` : ""}</b></div>`).join("")}</div>`;
        return;
      }
      el.innerHTML = `<div class="rolar"><table><thead><tr><th>${esc(v.eixo.replace(/_/g, " "))}</th><th class="n">${esc(mv.nome)}</th>${tot != null ? '<th class="n">% do total</th>' : ""}</tr></thead><tbody>${g.map((x) => `<tr><td>${esc(x[0])}</td><td class="n">${num(x[1])}</td>${tot != null ? `<td class="n">${tot ? p1((x[1] || 0) / tot) : "—"}</td>` : ""}</tr>`).join("")}</tbody>${tot != null ? `<tfoot><tr><td>Total</td><td class="n">${num(tot)}</td><td class="n">100%</td></tr></tfoot>` : ""}</table></div>`;
    });
  }
  const barra = document.getElementById("filtros");
  if (barra) {
    barra.hidden = false;
    barra.querySelectorAll("select").forEach((s) => (s.onchange = desenhar));
    document.getElementById("limpar").onclick = () => { barra.querySelectorAll("select").forEach((s) => (s.value = "")); desenhar(); };
  }
})();
"""
