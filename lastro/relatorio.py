"""Relatório HTML autocontido de uma demanda, com as cores da marca Lastro."""

from __future__ import annotations

import html

ESTILO = """
:root{--bg:#EEF1F3;--sup:#FFFFFF;--tinta:#111820;--quieta:#56606B;--linha:#D6DCE2;--ouro:#B58324;--ouro-f:#F4EAD3;--ok:#2E6B4E;--erro:#A3392B;--aviso:#8D6210}
@media (prefers-color-scheme:dark){:root{--bg:#0D1116;--sup:#151B22;--tinta:#E7ECF1;--quieta:#98A3AE;--linha:#26303A;--ouro:#E1B24F;--ouro-f:#2E2716;--ok:#7CC4A0;--erro:#F08A7C;--aviso:#E7C06B;color-scheme:dark}}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--tinta);font:16px/1.55 'IBM Plex Sans',system-ui,sans-serif}
main{max-width:920px;margin:0 auto;padding:32px 16px 64px}h1{font-size:28px;line-height:1.2;margin:8px 0 4px}h2{font-size:18px;margin:36px 0 12px}
.marca{font:600 14px 'IBM Plex Mono',monospace;letter-spacing:.04em;color:var(--quieta)}.marca b{color:var(--ouro)}
.card{background:var(--sup);border:1px solid var(--linha);border-radius:10px;padding:16px 18px;overflow-x:auto}
table{border-collapse:collapse;width:100%;font-size:14px}th,td{text-align:left;padding:6px 10px;border-bottom:1px solid var(--linha);white-space:nowrap}
th{color:var(--quieta);font-weight:600}td.n{text-align:right;font-variant-numeric:tabular-nums}
.selo{display:inline-block;padding:2px 10px;border-radius:99px;font:600 12px 'IBM Plex Mono',monospace}
.ok{color:var(--ok)}.erro{color:var(--erro)}.aviso{color:var(--aviso)}.selo.pend{background:var(--ouro-f);color:var(--tinta)}
code,pre{font-family:'IBM Plex Mono',monospace;font-size:13px}pre{white-space:pre-wrap;margin:0}
.barra{height:10px;background:var(--ouro);border-radius:3px}.total{font-size:32px;font-weight:600;font-variant-numeric:tabular-nums}
"""


def _fmt(v: object) -> str:
    if isinstance(v, float):
        return f"{v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    if isinstance(v, int):
        return f"{v:,}".replace(",", ".")
    return html.escape("" if v is None else str(v))


def gerar(demanda: dict, resultado: dict) -> str:
    r = resultado.get("resposta", {})
    a = resultado.get("auditoria", {})
    m = resultado.get("modelo", {})
    status = demanda.get("status", "")
    selo = {"aprovada": ("ok", "aprovada nas duas camadas"), "reprovada": ("erro", "reprovada pelo revisor")}.get(
        status, ("pend", "aguardando revisor de negócio (camada 2)")
    )
    linhas = r.get("linhas", [])
    cols = r.get("colunas", [])
    idx_val = next((i for i, c in enumerate(cols) if c.startswith("total_")), None)
    maior = max((abs(float(l[idx_val] or 0)) for l in linhas), default=0) if idx_val is not None else 0
    tabela = ["<table><thead><tr>" + "".join(f"<th>{html.escape(c)}</th>" for c in cols) + ("<th></th>" if idx_val is not None else "") + "</tr></thead><tbody>"]
    for l in linhas:
        tds = "".join(f"<td class='{'n' if isinstance(v, (int, float)) else ''}'>{_fmt(v)}</td>" for v in l)
        barra = ""
        if idx_val is not None and maior:
            barra = f"<td style='width:30%'><div class='barra' style='width:{100 * abs(float(l[idx_val] or 0)) / maior:.1f}%'></div></td>"
        tabela.append(f"<tr>{tds}{barra}</tr>")
    tabela.append("</tbody></table>")
    checks = "".join(
        f"<tr><td class='{'ok' if c['ok'] else c['nivel']}'>{'ok' if c['ok'] else c['nivel']}</td><td>{html.escape(c['checagem'])}</td><td>{html.escape(c['detalhe'])}</td></tr>"
        for c in a.get("checagens", [])
    )
    revisao = resultado.get("revisao")
    bloco_rev = ""
    if revisao:
        bloco_rev = f"<h2>Parecer da camada 2</h2><div class='card'><p><b>{html.escape(revisao['revisor'])}</b>: {html.escape(revisao.get('parecer') or '(sem parecer)')}</p></div>"
    return f"""<!doctype html><html lang="pt-BR"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Demanda {demanda['id']} · Lastro</title><style>{ESTILO}</style></head><body><main>
<div class="marca"><b>▤</b> lastro · demanda {demanda['id']}</div>
<h1>{html.escape(demanda['pergunta'])}</h1>
<p><span class="selo {selo[0]}">{selo[1]}</span></p>
{f"<p class='quieta'>Total de {html.escape(str(r.get('medida')))}</p><div class='total'>{_fmt(r.get('total'))}</div>" if r.get('total') is not None else ''}
<h2>Resposta</h2><div class="card">{''.join(tabela)}</div>
<h2>Auditoria técnica (camada 1)</h2><div class="card"><table><tbody>{checks}</tbody></table></div>
{bloco_rev}
<h2>Como chegamos aqui</h2><div class="card"><p>Fonte <b>{html.escape(str(m.get('fonte')))}</b> · medida <code>{html.escape(str(m.get('medida')))}</code> · data <code>{html.escape(str(m.get('data')))}</code> · chave <code>{html.escape(str(m.get('chave')))}</code> · dimensões: {html.escape(', '.join(m.get('dimensoes', [])))}</p>
<p>Playbook consultado: <code>{html.escape(str(m.get('playbook')))}</code></p><pre>{html.escape(r.get('sql', ''))}</pre></div>
</main></body></html>"""
