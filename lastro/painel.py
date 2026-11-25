"""Painel de operação do Lastro em Python puro (card LST-26): um HTML estático, sem custo e sem servidor.

Lê as views do schema `painel` (migração 0006), as mesmas que um BI usa com o usuário `painel_leitor`,
e desenha os gráficos em SVG inline. Uso: `uv run lastro painel --saida painel.html`, com
LASTRO_PAINEL_URL (ou LASTRO_BANCO_URL) apontando para o Postgres do Supabase.
"""

from __future__ import annotations

import html
import os
from datetime import date, datetime, timedelta
from typing import Any
from zoneinfo import ZoneInfo

FUSO = ZoneInfo("America/Sao_Paulo")

DIAS = 30


def coletar(url: str, dias: int = DIAS) -> dict[str, list[dict]]:
    import psycopg
    from psycopg.rows import dict_row

    desde = datetime.now(FUSO).date() - timedelta(days=dias - 1)
    consultas = {
        "requisicoes": ("SELECT * FROM painel.requisicoes_dia WHERE dia >= %s ORDER BY dia", (desde,)),
        "disponibilidade": ("SELECT * FROM painel.disponibilidade_dia WHERE dia >= %s ORDER BY dia", (desde,)),
        "demandas": ("SELECT * FROM painel.demandas_dia WHERE dia >= %s ORDER BY dia, empresa, status", (desde,)),
        "uso": ("SELECT * FROM painel.uso_gratuito ORDER BY recurso", ()),
        "cargas": ("SELECT * FROM painel.cargas ORDER BY empresa, saas, entidade", ()),
        "alertas": ("SELECT * FROM painel.alertas ORDER BY aberto_em DESC LIMIT 20", ()),
        "demo": ("SELECT * FROM painel.demo_funil_dia WHERE dia >= %s ORDER BY dia", (desde,)),
    }
    with psycopg.connect(url, row_factory=dict_row, prepare_threshold=None) as con:
        return {k: [dict(r) for r in con.execute(sql, args)] for k, (sql, args) in consultas.items()}


# ---- desenho ------------------------------------------------------------------------------

def _e(v: Any) -> str:
    return html.escape("" if v is None else str(v))


def _n(v: Any, casas: int = 0) -> str:
    if v is None:
        return "—"
    txt = f"{float(v):,.{casas}f}"
    return txt.replace(",", "X").replace(".", ",").replace("X", ".")  # formato brasileiro


def _dias(dias: int, hoje: date) -> list[date]:
    return [hoje - timedelta(days=i) for i in range(dias - 1, -1, -1)]


def _barras(serie: list[tuple[date, float, float]], rotulo: str, rotulo_parte: str) -> str:
    """Barras por dia; a parte de baixo (ex.: erros 5xx) em vermelho. Textos em HTML para não escalar com o SVG."""
    largura, altura = 300, 100
    maior = max((t for _, t, _ in serie), default=0) or 1
    passo = largura / max(len(serie), 1)
    barras = []
    for i, (d, total, parte) in enumerate(serie):
        h, hp, x = altura * total / maior, altura * parte / maior, i * passo + passo * 0.1
        dica = f"{d:%d/%m}: {_n(total)} {rotulo}" + (f", {_n(parte)} {rotulo_parte}" if parte else "")
        barras.append(
            f'<g><title>{_e(dica)}</title><rect x="{x:.2f}" y="{altura - h:.2f}" width="{passo * 0.8:.2f}" height="{h:.2f}" fill="var(--ouro)"/>'
            + (f'<rect x="{x:.2f}" y="{altura - max(hp, 1.5):.2f}" width="{passo * 0.8:.2f}" height="{max(hp, 1.5):.2f}" fill="var(--erro)"/>' if parte else "")
            + "</g>")
    marcas = [serie[0][0], serie[len(serie) // 2][0], serie[-1][0]] if serie else []
    return (f'<div class="grafico"><span class="eixo">máx. {_n(maior)} por dia</span>'
            f'<svg viewBox="0 0 {largura} {altura}" preserveAspectRatio="none" role="img" '
            f'aria-label="{_e(rotulo)} por dia, últimos {len(serie)} dias">{"".join(barras)}</svg>'
            f'<div class="eixo datas">{"".join(f"<span>{d:%d/%m}</span>" for d in marcas)}</div></div>')


def _medidor(rotulo: str, usado: float, limite: float, alerta: float = 0.8) -> str:
    frac = usado / limite if limite else 0
    cor = "var(--erro)" if frac > alerta else "var(--ok)"
    return (f'<div class="medidor"><div class="lin"><span>{_e(rotulo)}</span><b>{_n(usado, 1)} de {_n(limite)} MB</b></div>'
            f'<div class="trilho" role="meter" aria-valuemin="0" aria-valuemax="{limite}" aria-valuenow="{usado}" aria-label="{_e(rotulo)}">'
            f'<i style="width:{min(frac, 1) * 100:.1f}%;background:{cor}"></i><u style="left:{alerta * 100:.0f}%"></u></div>'
            f'<small>{_n(frac * 100, 1)}% do plano gratuito · alerta em {_n(alerta * 100)}%</small></div>')


def _tabela(cab: list[str], linhas: list[list[Any]], vazio: str) -> str:
    if not linhas:
        return f'<p class="quieta">{_e(vazio)}</p>'
    corpo = "".join("<tr>" + "".join(f"<td>{c}</td>" for c in lin) + "</tr>" for lin in linhas)
    return f'<div class="rolar"><table><thead><tr>{"".join(f"<th>{_e(c)}</th>" for c in cab)}</tr></thead><tbody>{corpo}</tbody></table></div>'


def _quando(v: Any) -> str:
    if not isinstance(v, datetime):
        return "—"
    return _e((v.astimezone(FUSO) if v.tzinfo else v).strftime("%d/%m %H:%M"))


def _funil(linhas: list[dict]) -> str:
    """Funil da demonstração do site (LST-44): subiu → painel → clicou para conversar, sem nada do visitante."""
    t = {k: sum(int(r[k] or 0) for r in linhas) for k in ("subiram", "paineis", "clicaram", "recusas", "desistencias")}
    pct = lambda a, b: f"{_n(100 * a / b, 1)}%" if b else "—"
    etapas = [("subiram uma planilha", t["subiram"], ""), ("receberam o painel", t["paineis"], pct(t["paineis"], t["subiram"])),
              ("clicaram para conversar", t["clicaram"], pct(t["clicaram"], t["paineis"]))]
    maior = max(t["subiram"], 1)
    barras = "".join(
        f'<div class="medidor"><div class="lin"><span>{_e(n)}</span><b>{_n(v)}{f" · {_e(x)} da etapa anterior" if x else ""}</b></div>'
        f'<div class="trilho"><i style="width:{100 * v / maior:.1f}%;background:var(--ouro)"></i></div></div>' for n, v, x in etapas)
    dias = [[_e(f"{r['dia']:%d/%m}"), _n(r["subiram"]), _n(r["paineis"]), _n(r["clicaram"]), _n(r["recusas"]), _n(r["desistencias"])]
            for r in sorted(linhas, key=lambda r: r["dia"], reverse=True)[:7]]
    return (f'<section class="bloco"><h2>Funil da demonstração do site</h2>'
            f'<p class="quieta">Últimos 30 dias, anônimo: sem IP e sem nada das planilhas. {_n(t["recusas"])} recusas (formato, tamanho, limite) e '
            f'{_n(t["desistencias"])} desistências.</p>{barras}'
            f'{_tabela(["dia", "subiram", "painéis", "clicaram", "recusas", "desistiram"], dias, "Nenhuma demonstração ainda.")}</section>')


def renderizar(dados: dict[str, list[dict]], gerado_em: datetime, dias: int = DIAS) -> str:
    hoje = gerado_em.date()
    req = {r["dia"]: r for r in dados["requisicoes"]}
    disp = {r["dia"]: r for r in dados["disponibilidade"]}
    serie_req = [(d, float(req.get(d, {}).get("requisicoes") or 0), float(req.get(d, {}).get("erros_5xx") or 0)) for d in _dias(dias, hoje)]
    ult7 = [d for d in _dias(7, hoje)]
    r7 = sum(float(req[d]["requisicoes"]) for d in ult7 if d in req)
    e7 = sum(float(req[d]["erros_5xx"]) for d in ult7 if d in req)
    lat = sum(float(req[d]["latencia_media_ms"] or 0) * float(req[d]["requisicoes"]) for d in ult7 if d in req)
    v7 = sum(int(disp[d]["verificacoes"]) for d in ult7 if d in disp)
    ok7 = sum(int(disp[d]["ok"]) for d in ult7 if d in disp)
    abertos = [a for a in dados["alertas"] if a["aberto"]]
    kpis = [
        ("disponibilidade (7 dias)", f"{_n(100 * ok7 / v7, 2)}%" if v7 else "—", f"{_n(v7)} verificações de /saude"),
        ("requisições (7 dias)", _n(r7), f"{_n(e7)} com erro 5xx"),
        ("taxa de 5xx (7 dias)", f"{_n(100 * e7 / r7, 2)}%" if r7 else "—", "alerta acima de 5% na hora"),
        ("latência média", f"{_n(lat / r7)} ms" if r7 else "—", "média ponderada, 7 dias"),
        ("alertas abertos", _n(len(abertos)), "e-mail pelo Resend ao abrir e ao fechar"),
    ]
    dem: dict[tuple[date, str], dict[str, int]] = {}
    for r in dados["demandas"]:
        dem.setdefault((r["dia"], r["empresa"]), {})[r["status"]] = int(r["demandas"])
    serie_dem = [(d, float(sum(sum(v.values()) for (dd, _), v in dem.items() if dd == d)), 0.0) for d in _dias(dias, hoje)]
    disp_linhas = [[_e(f"{d:%d/%m}"), _n(disp[d]["verificacoes"]), _n(disp[d]["ok"]),
                    f'<span class="{"ok" if float(disp[d]["disponibilidade_pct"]) >= 99 else "erro"}">{_n(disp[d]["disponibilidade_pct"], 2)}%</span>']
                   for d in sorted(disp, reverse=True)[:7]]
    cargas = [[_e(c["empresa"]), _e(f'{c["saas"]} · {c["entidade"]}'), _e(c["ultimo_status"]), _quando(c["ultima_carga_boa"]),
               f'<span class="quieta">{_e(c["ultimo_aviso"])}</span>'] for c in dados["cargas"]]
    alertas = [[_e(a["tipo"]), _e(a["detalhe"]), _quando(a["aberto_em"]),
                '<span class="erro">aberto</span>' if a["aberto"] else _quando(a["fechado_em"])] for a in dados["alertas"]]
    return f"""<!doctype html>
<html lang="pt-BR"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Lastro · Operação</title>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Bricolage+Grotesque:opsz,wght@12..96,700&family=IBM+Plex+Mono:wght@400;500&family=IBM+Plex+Sans:wght@400;600&display=swap">
<style>
:root {{ --chao:#EEF1F3; --sup:#FFFFFF; --tinta:#111820; --quieta:#56606B; --linha:#D6DCE2; --ouro:#B58324; --ok:#2E6B4E; --erro:#A3392B;
  --f-disp:'Bricolage Grotesque','Segoe UI',system-ui,sans-serif; --f-texto:'IBM Plex Sans','Segoe UI',system-ui,sans-serif; --f-dado:'IBM Plex Mono',ui-monospace,monospace }}
@media (prefers-color-scheme: dark) {{ :root:not([data-theme="light"]) {{ --chao:#0D1116; --sup:#151B22; --tinta:#E7ECF1; --quieta:#98A3AE; --linha:#26303A; --ouro:#E1B24F; --ok:#7CC4A0; --erro:#F08A7C; color-scheme:dark }} }}
:root[data-theme="dark"] {{ --chao:#0D1116; --sup:#151B22; --tinta:#E7ECF1; --quieta:#98A3AE; --linha:#26303A; --ouro:#E1B24F; --ok:#7CC4A0; --erro:#F08A7C; color-scheme:dark }}
* {{ box-sizing:border-box }} body {{ margin:0; background:var(--chao); color:var(--tinta); font:15px/1.5 var(--f-texto) }}
main {{ max-width:1080px; margin:0 auto; padding-block:28px 64px; padding-left:max(16px, env(safe-area-inset-left, 0px)); padding-right:max(16px, env(safe-area-inset-right, 0px)); display:grid; gap:16px }}
h1 {{ font:700 28px/1.15 var(--f-disp); margin:0 }} h2 {{ font:700 17px var(--f-disp); margin:0 }}
.quieta, small {{ color:var(--quieta) }} .ok {{ color:var(--ok) }} .erro {{ color:var(--erro) }}
.kpis {{ display:grid; grid-template-columns:repeat(auto-fit, minmax(170px, 1fr)); gap:12px }}
.kpi, .bloco {{ background:var(--sup); border:1px solid var(--linha); border-radius:10px; padding:16px; display:grid; gap:6px; min-width:0 }}
.kpi span {{ font:500 11px var(--f-dado); text-transform:uppercase; letter-spacing:.08em; color:var(--quieta) }}
.kpi b {{ font:700 26px var(--f-disp); font-variant-numeric:tabular-nums }}
.duas {{ display:grid; grid-template-columns:repeat(auto-fit, minmax(300px, 1fr)); gap:16px }}
svg {{ width:100%; height:160px; display:block; border-bottom:1px solid var(--linha) }} .eixo {{ font:12px var(--f-dado); color:var(--quieta) }}
.grafico {{ display:grid; gap:6px }} .datas {{ display:flex; justify-content:space-between }}
.medidor {{ display:grid; gap:6px }} .medidor .lin {{ display:flex; justify-content:space-between; gap:8px; flex-wrap:wrap }}
.trilho {{ position:relative; height:10px; background:var(--chao); border-radius:99px; overflow:hidden }}
.trilho i {{ position:absolute; inset:0 auto 0 0; border-radius:99px }} .trilho u {{ position:absolute; top:0; bottom:0; width:2px; background:var(--tinta); opacity:.4 }}
.rolar {{ overflow-x:auto }} table {{ border-collapse:collapse; width:100%; font-size:14px }}
th, td {{ text-align:left; padding:7px 10px; border-bottom:1px solid var(--linha); white-space:nowrap }} th {{ color:var(--quieta); font-weight:600 }}
td:last-child {{ white-space:normal }}
</style></head><body><main>
<header><h1>Operação do Lastro</h1><p class="quieta">Gerado em {gerado_em:%d/%m/%Y %H:%M} · últimos {dias} dias · fonte: schema <code>painel</code> do Supabase</p></header>
<section class="kpis">{"".join(f'<div class="kpi"><span>{_e(t)}</span><b>{v}</b><small>{_e(s)}</small></div>' for t, v, s in kpis)}</section>
<section class="bloco"><h2>Requisições por dia</h2><p class="quieta">Em vermelho, as respostas 5xx. Sem contar /saude e os arquivos do portal.</p>
{_barras(serie_req, "requisições", "com erro 5xx")}</section>
<div class="duas">
<section class="bloco"><h2>Disponibilidade</h2><p class="quieta">Verificação de /saude a cada 5 minutos pelo próprio Supabase.</p>
{_tabela(["dia", "verificações", "ok", "disponível"], disp_linhas, "Nenhuma verificação ainda.")}</section>
<section class="bloco"><h2>Uso do plano gratuito</h2>{"".join(_medidor(u["recurso"], float(u["usado_mb"]), float(u["limite_mb"])) for u in dados["uso"])}
<small>Render: 750 horas de instância por mês; com a verificação a cada 5 minutos o serviço fica sempre acordado (~744 h).</small></section>
</div>
<section class="bloco"><h2>Demandas por dia</h2>{_barras(serie_dem, "demandas", "")}</section>
<section class="bloco"><h2>Cargas agendadas</h2>{_tabela(["empresa", "sistema", "situação", "última carga boa", "aviso"], cargas, "Nenhuma carga agendada.")}</section>
{_funil(dados.get("demo", []))}
<section class="bloco"><h2>Alertas</h2>{_tabela(["tipo", "detalhe", "aberto em", "fechado em"], alertas, "Nenhum alerta até agora.")}</section>
</main></body></html>
"""


def gerar(url: str | None = None, dias: int = DIAS) -> str:
    url = url or os.environ.get("LASTRO_PAINEL_URL") or os.environ.get("LASTRO_BANCO_URL")
    if not url:
        raise RuntimeError("defina LASTRO_PAINEL_URL (ou LASTRO_BANCO_URL) com o endereço do Postgres")
    return renderizar(coletar(url, dias), datetime.now(FUSO), dias)
