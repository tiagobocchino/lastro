"""Painéis da demanda (card LST-34): o agente monta e edita o painel; a mesma especificação vira
um HTML estático (Python, sem custo) e um projeto aberto do Power BI (PBIP com TMDL e PBIR).

A especificação é um JSON pequeno guardado na pasta da demanda (`painel/v<n>.json`, uma versão por mudança):
- `medidas`: id estável, nome de exibição, coluna da fato e agregação;
- `visuais`: id estável, tipo (kpi, barras, linha, tabela), a medida e, quando há, o eixo (uma dimensão ou o tempo).

Toda mudança é uma operação validada contra o gold da demanda: o que não existe é recusado antes de
gravar, ids existentes nunca mudam e uma medida em uso não pode ser removida. Assim o painel do cliente
no Power BI não quebra quando o agente acrescenta algo.
"""

from __future__ import annotations

import copy
import html
import json
import re
import unicodedata
import uuid
from pathlib import Path
from typing import Any

import duckdb

from . import painel_html
from .agents.construtores import (
    ident,  # o mesmo nome que o Engenheiro dá às colunas do gold
)

AGREGACOES = {  # nome no painel → (SQL do DuckDB, DAX, rótulo)
    "soma": ("sum", "SUM", "Soma"),
    "media": ("avg", "AVERAGE", "Média"),
    "contagem": ("count", "COUNT", "Contagem"),
    "distintos": ("count(DISTINCT", "DISTINCTCOUNT", "Distintos"),
    "minimo": ("min", "MIN", "Mínimo"),
    "maximo": ("max", "MAX", "Máximo"),
}
TIPOS = {"kpi", "barras", "linha", "tabela"}
TEMPO = {"ano_mes": "mês", "ano": "ano"}


class PedidoInvalido(ValueError):
    """Mudança que o painel não aceita (coluna inexistente, visual sem medida...)."""


def _slug(texto: str) -> str:
    s = unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode().lower()
    return re.sub(r"[^a-z0-9]+", "_", s).strip("_")[:40] or "x"


def _nome(coluna: str) -> str:
    return coluna.replace("_", " ").strip().capitalize()


# ---- o que o gold da demanda oferece ---------------------------------------------------

def catalogo(gold: Path, modelo: dict) -> dict:
    """Colunas numéricas da fato, dimensões com tabela própria e eixos de tempo, lidos do próprio gold."""
    fato = gold / "fato.parquet"
    if not fato.exists():
        raise PedidoInvalido("esta demanda ainda não tem gold (rode e aprove a demanda primeiro)")
    tipos = {r[0]: str(r[1]) for r in duckdb.sql(f"DESCRIBE SELECT * FROM read_parquet('{_q(fato)}')").fetchall()}
    # chave e identificadores (nº do processo, código) identificam a linha: somar não faz sentido
    fora = {ident(c) for c in [modelo.get("chave"), *modelo.get("identificadores", [])] if c}
    numericas = [c for c, t in tipos.items() if not c.endswith("_id") and c not in fora
                 and any(x in t for x in ("INT", "DOUBLE", "DECIMAL", "FLOAT", "REAL"))]
    if modelo.get("medida") and ident(modelo["medida"]) in numericas:  # a medida do grill vem primeiro
        numericas.remove(ident(modelo["medida"]))
        numericas.insert(0, ident(modelo["medida"]))
    dims = [d for d in modelo.get("dimensoes", []) if (gold / f"dim_{_slug(d)}.parquet").exists()]
    tempo = list(TEMPO) if (gold / "dim_data.parquet").exists() and "data" in tipos else []
    return {"medidas": numericas, "dimensoes": [_slug(d) for d in dims], "tempo": tempo, "tipos": tipos}


def _q(p: Path) -> str:
    return str(p).replace("'", "''")


# ---- especificação ---------------------------------------------------------------------

def inicial(demanda: dict, gold: Path) -> dict:
    """O que o agente propõe a partir do modelo da demanda: o número principal, a quebra pedida e a evolução."""
    modelo = demanda["resultado"]["modelo"]
    cat = catalogo(gold, modelo)
    medida = (cat["medidas"] or [None])[0]
    if not medida:
        raise PedidoInvalido("o gold não tem coluna numérica para medir")
    m = {"id": f"{_slug(medida)}_soma", "nome": _nome(medida), "coluna": medida, "agregacao": "soma"}
    agrupado = [_slug(d) for d in demanda["resultado"].get("resposta", {}).get("agrupado_por", []) if _slug(d) in cat["dimensoes"]]
    eixo = agrupado[0] if agrupado else (cat["dimensoes"] or [None])[0]
    visuais = [{"id": "v1", "tipo": "kpi", "titulo": f"{m['nome']} (total)", "medida": m["id"]}]
    if eixo:
        visuais.append({"id": "v2", "tipo": "barras", "titulo": f"{m['nome']} por {eixo}", "medida": m["id"], "eixo": eixo})
    if "ano_mes" in cat["tempo"]:
        visuais.append({"id": "v3", "tipo": "linha", "titulo": f"{m['nome']} por mês", "medida": m["id"], "eixo": "ano_mes"})
    if eixo:
        visuais.append({"id": "v4", "tipo": "tabela", "titulo": f"Detalhe por {eixo}", "medida": m["id"], "eixo": eixo})
    spec = {"versao": 1, "demanda": demanda["id"], "titulo": demanda["pergunta"][:90], "medidas": [m], "visuais": visuais}
    validar(spec, cat)
    return spec


FORMATOS = {"ranking": "barras", "tabela": "tabela", "evolucao": "linha", "numero": "kpi"}


def para_visitante(demanda: dict, gold: Path, quebra: str | None, periodo: str | None, formato: str,
                   excluir: set[str] | None = None) -> dict:
    """Grill de "como mostrar" da demonstração (LST-40) direto na especificação do painel: o número principal
    sempre, mais o visual escolhido (ranking ou tabela pela quebra, ou evolução pelo período)."""
    modelo = demanda["resultado"]["modelo"]
    cat = catalogo(gold, modelo)
    fora = {_slug(c) for c in (excluir or set())}  # LST-41: colunas com dado pessoal nunca entram no painel
    cat["medidas"] = [c for c in cat["medidas"] if _slug(c) not in fora]
    cat["dimensoes"] = [d for d in cat["dimensoes"] if d not in fora]
    medida = (cat["medidas"] or [None])[0]
    if not medida:
        raise PedidoInvalido("a planilha não tem coluna numérica para medir")
    if formato not in FORMATOS:
        raise PedidoInvalido(f"formato '{formato}' não existe; use {sorted(FORMATOS)}")
    m = {"id": f"{_slug(medida)}_soma", "nome": _nome(medida), "coluna": medida, "agregacao": "soma"}
    visuais = [{"id": "v1", "tipo": "kpi", "titulo": f"{m['nome']} (total)", "medida": m["id"]}]
    tipo = FORMATOS[formato]
    eixo_q = _slug(quebra) if quebra else None
    if tipo in {"barras", "tabela"}:
        eixo = eixo_q if eixo_q in cat["dimensoes"] else (cat["dimensoes"] or [None])[0]
        if eixo:
            visuais.append({"id": "v2", "tipo": tipo, "titulo": f"{m['nome']} por {eixo.replace('_', ' ')}", "medida": m["id"], "eixo": eixo})
    elif tipo == "linha" and cat["tempo"]:
        eixo = periodo if periodo in cat["tempo"] else "ano_mes"
        visuais.append({"id": "v2", "tipo": "linha", "titulo": f"{m['nome']} por {TEMPO[eixo]}", "medida": m["id"], "eixo": eixo})
    spec = {"versao": 1, "demanda": demanda["id"], "titulo": f"{m['nome']}: painel da sua planilha", "medidas": [m], "visuais": visuais,
            "modo": "demonstracao",
            # filtros do painel só entre as dimensões liberadas: coluna com dado pessoal nunca vai para o cubo embutido (LST-41/55)
            "filtros": [*cat["dimensoes"], *(["ano"] if cat["tempo"] else [])]}
    validar(spec, cat)
    return spec


def validar(spec: dict, cat: dict) -> None:
    ids_m = [m["id"] for m in spec["medidas"]]
    if len(ids_m) != len(set(ids_m)):
        raise PedidoInvalido("há medidas com o mesmo id")
    for m in spec["medidas"]:
        if m["agregacao"] not in AGREGACOES:
            raise PedidoInvalido(f"agregação '{m['agregacao']}' não existe; use {sorted(AGREGACOES)}")
        if m["coluna"] not in cat["tipos"]:
            raise PedidoInvalido(f"a coluna '{m['coluna']}' não existe na fato desta demanda")
        if m["agregacao"] in {"soma", "media"} and m["coluna"] not in cat["medidas"]:
            raise PedidoInvalido(f"'{m['coluna']}' não é numérica: use contagem ou distintos")
    ids_v = [v["id"] for v in spec["visuais"]]
    if len(ids_v) != len(set(ids_v)):
        raise PedidoInvalido("há visuais com o mesmo id")
    for v in spec["visuais"]:
        if v["tipo"] not in TIPOS:
            raise PedidoInvalido(f"tipo de visual '{v['tipo']}' não existe; use {sorted(TIPOS)}")
        if v["medida"] not in ids_m:
            raise PedidoInvalido(f"o visual {v['id']} usa uma medida que não existe: {v['medida']}")
        eixo = v.get("eixo")
        if v["tipo"] == "kpi":
            if eixo:
                raise PedidoInvalido("um KPI não tem eixo")
        elif eixo not in cat["dimensoes"] + cat["tempo"]:
            raise PedidoInvalido(f"eixo '{eixo}' não existe; use {cat['dimensoes'] + cat['tempo']}")


def mudar(spec: dict, op: dict, cat: dict) -> tuple[dict, str]:
    """Aplica uma operação e devolve a nova versão e a frase que vai para o rastro. Nada muda se for recusada."""
    novo = copy.deepcopy(spec)
    tipo = op.get("op")
    if tipo == "adicionar_medida":
        coluna, agg = op.get("coluna", ""), op.get("agregacao", "soma")
        mid = _slug(op.get("id") or f"{coluna}_{agg}")
        if any(m["id"] == mid for m in novo["medidas"]):
            raise PedidoInvalido(f"a medida '{mid}' já existe")
        nome = op.get("nome") or f"{AGREGACOES.get(agg, ('', '', agg))[2]} de {_nome(coluna).lower()}"
        novo["medidas"].append({"id": mid, "nome": nome, "coluna": coluna, "agregacao": agg})
        frase = f"adicionou a medida '{nome}' ({agg} de {coluna})"
    elif tipo == "adicionar_visual":
        extra = ""
        if (nova := op.get("medida_nova")) and not any(m["id"] == nova["id"] for m in novo["medidas"]):
            novo["medidas"].append(nova)  # "gráfico de média de valor orçado": cria a medida e o visual numa versão só
            extra = f" e a medida '{nova['nome']}'"
        vid = f"v{1 + max([int(v['id'][1:]) for v in novo['visuais'] if v['id'][1:].isdigit()] or [0])}"
        v = {"id": vid, "tipo": op.get("tipo", ""), "medida": op.get("medida", "")}
        if op.get("eixo"):
            v["eixo"] = _slug(op["eixo"])
        igual = next((x for x in novo["visuais"] if (x["tipo"], x["medida"], x.get("eixo")) == (v["tipo"], v["medida"], v.get("eixo"))), None)
        if igual:  # 26/11: um clique duplo criou v6 e v7 iguais
            raise PedidoInvalido(f"esse visual já existe no painel: {igual['id']} ({igual['titulo']})")
        med = next((m for m in novo["medidas"] if m["id"] == v["medida"]), None)
        v["titulo"] = op.get("titulo") or (f"{med['nome'] if med else v['medida']}" + (f" por {v['eixo']}" if v.get("eixo") else ""))
        novo["visuais"].append(v)
        frase = f"adicionou o visual {vid} ({v['tipo']}: {v['titulo']}){extra}"
    elif tipo == "remover_visual":
        antes = len(novo["visuais"])
        novo["visuais"] = [v for v in novo["visuais"] if v["id"] != op.get("id")]
        if len(novo["visuais"]) == antes:
            raise PedidoInvalido(f"não existe o visual '{op.get('id')}'")
        frase = f"removeu o visual {op['id']}"
    elif tipo == "remover_medida":
        mid = op.get("id")
        if any(v["medida"] == mid for v in novo["visuais"]):
            raise PedidoInvalido(f"a medida '{mid}' está em uso; remova antes os visuais que a usam")
        antes = len(novo["medidas"])
        novo["medidas"] = [m for m in novo["medidas"] if m["id"] != mid]
        if len(novo["medidas"]) == antes:
            raise PedidoInvalido(f"não existe a medida '{mid}'")
        frase = f"removeu a medida {mid}"
    elif tipo == "renomear":
        titulo = str(op.get("titulo", "")).strip()
        if not titulo:
            raise PedidoInvalido("título vazio")
        alvo = op.get("id")
        if alvo:
            item = next((x for x in novo["visuais"] if x["id"] == alvo), None) or next((x for x in novo["medidas"] if x["id"] == alvo), None)
            if not item:
                raise PedidoInvalido(f"não existe '{alvo}'")
            item["titulo" if "tipo" in item else "nome"] = titulo
        else:
            novo["titulo"] = titulo
        frase = f"renomeou {alvo or 'o painel'} para '{titulo}'"
    else:
        raise PedidoInvalido("operação desconhecida; use adicionar_medida, adicionar_visual, remover_visual, remover_medida ou renomear")
    validar(novo, cat)
    novo["versao"] = spec["versao"] + 1
    return novo, frase


AGG = r"(soma|m[eé]dia|contagem|distintos|m[ií]nimo|m[aá]ximo)"
PADRAO_MEDIDA = re.compile(
    r"(?:nova medida|adicion\w* (?:a |uma )?medida)\s*(?:\"([^\"]+)\"\s*)?(?:=|:|com|de)?\s*" + AGG + r"\s+(?:de|do|da|dos|das)\s+([\w ]+)",
    re.IGNORECASE)
PADRAO_MEDIDA_SIMPLES = re.compile(r"(?:nova medida|adicion\w* (?:a |uma )?medida)\s+(?:de |do |da |dos |das )?([\w ]+)$", re.IGNORECASE)
TIPO_VISUAL = r"(gr[aá]fico de barras|barras|gr[aá]fico de linha|linha|tabela|kpi|cart[aã]o|n[uú]mero|gr[aá]fico)"
PADRAO_VISUAL = re.compile(
    r"(?:adicion\w*|cri\w*|inclu\w*|coloc\w*|mostr\w*)\s+(?:um |uma |o |a )?" + TIPO_VISUAL
    + r"\s+(?:de|do|da|com)\s+([\w ]+?)(?:\s+por\s+([\w ]+))?$", re.IGNORECASE)
PADRAO_REMOVER = re.compile(r"(?:remov\w*|tir\w*|apag\w*|exclu\w*)\s+(?:o )?(?:visual )?(v\d+)\b", re.IGNORECASE)
PADRAO_REMOVER_NOME = re.compile(
    r"(?:remov\w*|tir\w*|apag\w*|exclu\w*)\s+(?:um dos |uma das |o |a |os |as )?(?:gr[aá]ficos?|visua(?:l|is)|tabelas?|cart(?:ão|ões|ao|oes))\s+(?:de |do |da )?([\w ]+)$",
    re.IGNORECASE)
# Medidas calculadas que o designer ainda não monta (26/11: conversão vendido ÷ orçado, variação mês a mês, mês até hoje)
PADRAO_CALCULADA = re.compile(r"convers|taxa|dividid|raz[aã]o|percentual|%|m[eê]s passado|m[eê]s anterior|mesmo dia| x ", re.IGNORECASE)


def _medida_do_texto(texto: str, spec: dict, cat: dict) -> tuple[str, dict | None]:
    """Medida do painel pelo nome ("valor vendido", "média de valor orçado"); se não houver, a que o texto descreve."""
    alvo = _slug(texto)
    existente = next((x["id"] for x in spec["medidas"] if alvo in (x["id"], _slug(x["nome"]), _slug(x["coluna"]))), None)
    if existente:
        return existente, None
    m = re.match(AGG + r"\s+(?:de|do|da|dos|das)\s+(.+)", texto.strip(), re.IGNORECASE)
    agg, coluna = (_slug(m.group(1)), _achar(m.group(2), cat["tipos"])) if m else ("soma", _achar(texto, cat["tipos"]))
    if coluna not in cat["tipos"]:
        raise PedidoInvalido(f"não achei '{texto}' no painel nem nos dados; medidas: {[x['nome'] for x in spec['medidas']]}")
    nova = {"id": f"{coluna}_{agg}", "nome": f"{AGREGACOES[agg][2]} de {_nome(coluna).lower()}", "coluna": coluna, "agregacao": agg}
    existente = next((x["id"] for x in spec["medidas"] if x["id"] == nova["id"]), None)
    return (existente, None) if existente else (nova["id"], nova)


def interpretar(pedido: str, spec: dict, cat: dict) -> dict:
    """Pedido em português → operação. Determinístico (sem LLM): o que não reconhece, recusa com exemplos."""
    t = re.sub(r"\s+", " ", pedido.strip().rstrip("."))
    if m := PADRAO_REMOVER.search(t):
        return {"op": "remover_visual", "id": m.group(1).lower()}
    if m := PADRAO_REMOVER_NOME.search(t):
        alvo = _slug(m.group(1))
        achados = [v for v in spec["visuais"] if alvo in _slug(v["titulo"]) or _slug(v["titulo"]) in alvo]
        if not achados:
            raise PedidoInvalido(f"não achei esse visual; os do painel são: {', '.join(v['id'] + ' ' + v['titulo'] for v in spec['visuais'])}")
        return {"op": "remover_visual", "id": achados[-1]["id"]}  # se há repetidos, sai o mais novo
    if PADRAO_CALCULADA.search(t):
        raise PedidoInvalido(
            "esse pedido precisa de uma medida calculada (razão entre duas colunas, como vendido ÷ orçado, ou variação entre "
            "períodos, como mês contra mês anterior). O designer ainda não monta esse tipo: o pedido ficou anotado para a equipe "
            "do Lastro. Por enquanto dá para pôr as duas medidas lado a lado, por exemplo: 'adicione um gráfico de linha de valor "
            "orçado por mês'")
    if m := PADRAO_MEDIDA.search(t):
        nome, agg, coluna = m.group(1), _slug(m.group(2)), _achar(m.group(3), cat["tipos"])
        return {"op": "adicionar_medida", "coluna": coluna, "agregacao": agg} | ({"nome": nome} if nome else {})
    if m := PADRAO_VISUAL.search(t):
        palavra = _slug(m.group(1))
        med, nova = _medida_do_texto(m.group(2), spec, cat)
        eixo = _slug(m.group(3)) if m.group(3) else None
        eixo = {"mes": "ano_mes", "meses": "ano_mes", "ano_mes": "ano_mes", "ano": "ano", "anos": "ano"}.get(eixo, eixo) if eixo else None
        if "linha" in palavra:
            tipo = "linha"
        elif "barras" in palavra:
            tipo = "barras"
        elif palavra.startswith("tabela"):
            tipo = "tabela"
        elif palavra in ("kpi", "cartao", "numero"):
            tipo = "kpi"
        else:  # "gráfico de X": barras com eixo (linha se for no tempo), cartão sem eixo
            tipo = ("linha" if eixo in TEMPO else "barras") if eixo else "kpi"
        if tipo == "kpi":
            eixo = None
        op = {"op": "adicionar_visual", "tipo": tipo, "medida": med} | ({"eixo": eixo} if eixo else {})
        return op | ({"medida_nova": nova} if nova else {})
    if m := PADRAO_MEDIDA_SIMPLES.search(t):  # "nova medida de valor orçado": soma, a agregação mais comum
        return {"op": "adicionar_medida", "coluna": _achar(m.group(1), cat["tipos"]), "agregacao": "soma"}
    raise PedidoInvalido(
        "não entendi o pedido. Exemplos: 'nova medida média de valor orçado', "
        "'adicione um gráfico de barras de valor vendido por estado', 'adicione um gráfico de valor orçado', "
        "'remova o gráfico de valor vendido por estado' ou 'remova o v3'")


def _achar(texto: str, colunas: dict) -> str:
    alvo = _slug(texto)
    for c in colunas:
        if alvo == c or alvo.startswith(c) or c.startswith(alvo):
            return c
    return alvo


# ---- versões em disco ------------------------------------------------------------------

def pasta(pasta_demanda: Path) -> Path:
    return pasta_demanda / "painel"


def atual(pasta_demanda: Path) -> dict | None:
    versoes = sorted(pasta(pasta_demanda).glob("v*.json"), key=lambda p: int(p.stem[1:]))
    return json.loads(versoes[-1].read_text()) if versoes else None


def gravar(pasta_demanda: Path, spec: dict) -> Path:
    destino = pasta(pasta_demanda) / f"v{spec['versao']}.json"
    if destino.exists():
        raise PedidoInvalido("esta versão do painel já existe")
    destino.parent.mkdir(parents=True, exist_ok=True)
    destino.write_text(json.dumps(spec, ensure_ascii=False, indent=2))
    return destino


def versoes(pasta_demanda: Path) -> list[int]:
    return sorted(int(p.stem[1:]) for p in pasta(pasta_demanda).glob("v*.json"))


# ---- números do painel (DuckDB sobre o gold) -------------------------------------------

def _agg_sql(m: dict) -> str:
    f = AGREGACOES[m["agregacao"]][0]
    col = f"fato.\"{m['coluna']}\""
    return f"{f} {col})" if f.endswith("DISTINCT") else f"{f}({col})"


def dados(spec: dict, gold: Path) -> dict[str, Any]:
    con = duckdb.connect()
    try:
        for arq in gold.glob("*.parquet"):
            con.execute(f"CREATE VIEW \"{arq.stem}\" AS SELECT * FROM read_parquet('{_q(arq)}')")
        med = {m["id"]: m for m in spec["medidas"]}
        out: dict[str, Any] = {}
        for v in spec["visuais"]:
            agg = _agg_sql(med[v["medida"]])
            if v["tipo"] == "kpi":
                out[v["id"]] = con.execute(f"SELECT {agg} FROM fato").fetchone()[0]
                continue
            eixo = v["eixo"]
            if eixo in TEMPO:
                sql = (f"SELECT dim_data.{eixo} AS eixo, {agg} AS valor FROM fato JOIN dim_data USING (data) "
                       f"GROUP BY 1 ORDER BY 1")
            else:
                ordem = "2 DESC" if v["tipo"] != "linha" else "1"
                sql = (f"SELECT dim_{eixo}.{eixo} AS eixo, {agg} AS valor FROM fato JOIN dim_{eixo} USING ({eixo}_id) "
                       f"GROUP BY 1 ORDER BY {ordem} LIMIT 50")
            out[v["id"]] = con.execute(sql).fetchall()
        return out
    finally:
        con.close()


# ---- HTML estático ---------------------------------------------------------------------

def _num(v: Any) -> str:
    if v is None:
        return "—"
    s = f"{float(v):,.2f}" if isinstance(v, float) and not float(v).is_integer() else f"{float(v):,.0f}"
    return s.replace(",", "X").replace(".", ",").replace("X", ".")


def _e(v: Any) -> str:
    return html.escape("" if v is None else str(v))


def _origem(spec: dict, gerado_em: str) -> str:
    if spec.get("modo") == "previa":  # LST-57: o revisor vê antes de aprovar; ninguém mais
        return f"Prévia para o revisor · demanda {spec['demanda']} · gerado em {gerado_em} · aguardando revisão de negócio: ainda não foi entregue"
    if spec.get("modo") == "demonstracao":  # ADR 0010: ninguém aprovou; dizer o que é
        return f"Demonstração do Lastro · gerado em {gerado_em} · conferência automática, sem revisão humana · seus dados já foram apagados"
    return f"Painel da demanda {spec['demanda']} · versão {spec['versao']} · gerado em {gerado_em} pelo Lastro a partir do gold aprovado"


def html_painel(spec: dict, gold: Path, gerado_em: str) -> str:
    """Painel de entrega com filtros, cartões com comparação, ranking e conferência (LST-55, `painel_html`).
    Se o cubo passar do limite, sai o painel fixo de antes, que não depende do tamanho do gold."""
    c = painel_html.cubo(spec, gold)
    if c["grande"]:
        return _html_fixo(spec, gold, gerado_em)
    return painel_html.html(spec, gold, _origem(spec, gerado_em), c)


def _html_fixo(spec: dict, gold: Path, gerado_em: str) -> str:
    valores = dados(spec, gold)
    blocos = []
    for v in spec["visuais"]:
        d = valores[v["id"]]
        if v["tipo"] == "kpi":
            corpo = f'<b class="kpi">{_num(d)}</b>'
        elif v["tipo"] == "barras":
            maior = max((abs(x[1] or 0) for x in d), default=0) or 1
            corpo = '<div class="barras">' + "".join(
                f'<div class="linha-b"><span>{_e(x[0])}</span><i style="width:{100 * abs(x[1] or 0) / maior:.1f}%"></i><b>{_num(x[1])}</b></div>'
                for x in d) + "</div>"
        elif v["tipo"] == "linha":
            pts = [(i, float(x[1] or 0)) for i, x in enumerate(d)]
            maior = max((p[1] for p in pts), default=0) or 1
            n = max(len(pts) - 1, 1)
            poli = " ".join(f"{100 * i / n:.2f},{100 - 92 * y / maior:.2f}" for i, y in pts)
            corpo = (f'<svg viewBox="0 0 100 100" preserveAspectRatio="none" role="img" aria-label="{_e(v["titulo"])}">'
                     f'<polyline points="{poli}" fill="none" stroke="var(--ouro)" stroke-width="2" vector-effect="non-scaling-stroke"/></svg>'
                     f'<div class="datas"><span>{_e(d[0][0]) if d else ""}</span><span>máx. {_num(maior)}</span><span>{_e(d[-1][0]) if d else ""}</span></div>')
        else:
            corpo = ('<div class="rolar"><table><thead><tr><th>' + _e(v["eixo"]) + "</th><th>" +
                     _e(next(m["nome"] for m in spec["medidas"] if m["id"] == v["medida"])) + "</th></tr></thead><tbody>" +
                     "".join(f"<tr><td>{_e(x[0])}</td><td class='n'>{_num(x[1])}</td></tr>" for x in d) + "</tbody></table></div>")
        largo = " largo" if v["tipo"] in {"linha", "tabela"} else ""
        blocos.append(f'<section class="bloco {v["tipo"]}{largo}" id="{_e(v["id"])}"><h2>{_e(v["titulo"])}</h2>{corpo}</section>')
    return f"""<!doctype html>
<html lang="pt-BR"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>{_e(spec['titulo'][:60])}</title>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Bricolage+Grotesque:opsz,wght@12..96,700&family=IBM+Plex+Mono:wght@400;500&family=IBM+Plex+Sans:wght@400;600&display=swap">
<style>
:root {{ --chao:#EEF1F3; --sup:#FFFFFF; --tinta:#111820; --quieta:#56606B; --linha:#D6DCE2; --ouro:#B58324;
  --f-disp:'Bricolage Grotesque','Segoe UI',system-ui,sans-serif; --f-texto:'IBM Plex Sans','Segoe UI',system-ui,sans-serif; --f-dado:'IBM Plex Mono',ui-monospace,monospace }}
@media (prefers-color-scheme: dark) {{ :root:not([data-theme="light"]) {{ --chao:#0D1116; --sup:#151B22; --tinta:#E7ECF1; --quieta:#98A3AE; --linha:#26303A; --ouro:#E1B24F; color-scheme:dark }} }}
:root[data-theme="dark"] {{ --chao:#0D1116; --sup:#151B22; --tinta:#E7ECF1; --quieta:#98A3AE; --linha:#26303A; --ouro:#E1B24F; color-scheme:dark }}
* {{ box-sizing:border-box }} body {{ margin:0; background:var(--chao); color:var(--tinta); font:15px/1.5 var(--f-texto) }}
main {{ max-width:1100px; margin:0 auto; padding-block:28px 64px; padding-left:max(16px, env(safe-area-inset-left, 0px)); padding-right:max(16px, env(safe-area-inset-right, 0px)) }}
h1 {{ font:700 26px/1.2 var(--f-disp); margin:0 0 4px; text-wrap:balance }} h2 {{ font:600 15px var(--f-disp); margin:0 0 10px }}
.quieta {{ color:var(--quieta); font-size:13px; margin:0 0 18px }}
.grade {{ display:grid; grid-template-columns:repeat(auto-fit, minmax(min(280px, 100%), 1fr)); gap:14px }}
.bloco {{ background:var(--sup); border:1px solid var(--linha); border-radius:10px; padding:16px; min-width:0 }} .largo {{ grid-column:1/-1 }}
.bloco.kpi {{ align-self:start }} @media (min-width: 900px) {{ .bloco.barras {{ grid-column:span 2 }} }}
.kpi {{ font:700 34px var(--f-disp); font-variant-numeric:tabular-nums }}
.barras {{ display:grid; gap:6px }} .linha-b {{ display:grid; grid-template-columns:minmax(80px, 30%) 1fr auto; gap:8px; align-items:center; font-size:13px }}
.linha-b span {{ overflow:hidden; text-overflow:ellipsis; white-space:nowrap }} .linha-b i {{ height:10px; background:var(--ouro); border-radius:2px; min-width:2px }}
.linha-b b {{ font:500 12px var(--f-dado); font-variant-numeric:tabular-nums }}
svg {{ width:100%; height:180px; display:block; border-bottom:1px solid var(--linha) }}
.datas {{ display:flex; justify-content:space-between; font:12px var(--f-dado); color:var(--quieta); margin-top:6px }}
.rolar {{ overflow-x:auto }} table {{ border-collapse:collapse; width:100%; font-size:14px }}
th, td {{ text-align:left; padding:6px 10px; border-bottom:1px solid var(--linha) }} th {{ color:var(--quieta); font-weight:600 }}
td.n {{ text-align:right; font-family:var(--f-dado); font-variant-numeric:tabular-nums }}
</style></head><body><main>
<h1>{_e(spec['titulo'])}</h1>
<p class="quieta">{_e(_origem(spec, gerado_em))}</p>
<div class="grade">{''.join(blocos)}</div>
</main></body></html>
"""


# ---- projeto do Power BI (PBIP: TMDL + PBIR) ---------------------------------------------

SCHEMAS = {
    "pbip": "https://developer.microsoft.com/json-schemas/fabric/pbip/pbipProperties/1.0.0/schema.json",
    "pbir": "https://developer.microsoft.com/json-schemas/fabric/item/report/definitionProperties/2.0.0/schema.json",
    "pbism": "https://developer.microsoft.com/json-schemas/fabric/item/semanticModel/definitionProperties/1.0.0/schema.json",
    "version": "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/versionMetadata/1.0.0/schema.json",
    "report": "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/report/3.3.0/schema.json",
    "pages": "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/pagesMetadata/1.1.0/schema.json",
    "page": "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/page/2.1.0/schema.json",
    "visual": "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/visualContainer/2.8.0/schema.json",
}
TIPO_TMDL = {"BIGINT": "int64", "INTEGER": "int64", "SMALLINT": "int64", "DOUBLE": "double", "FLOAT": "double",
             "DATE": "dateTime", "TIMESTAMP": "dateTime", "BOOLEAN": "boolean", "VARCHAR": "string"}
VISUAL_PBI = {"kpi": ("card", None, "Values"), "barras": ("clusteredBarChart", "Category", "Y"),
              "linha": ("lineChart", "Category", "Y"), "tabela": ("tableEx", "Values", "Values")}


def _tmdl_nome(n: str) -> str:
    return f"'{n.replace(chr(39), chr(39) * 2)}'" if re.search(r"[.=:' ]", n) else n


def _uuid(*partes: Any) -> str:
    return str(uuid.uuid5(uuid.NAMESPACE_URL, "lastro:" + ":".join(map(str, partes))))


def _colunas_gold(gold: Path, tabela: str) -> list[tuple[str, str]]:
    return [(r[0], TIPO_TMDL.get(str(r[1]).split("(")[0], "string"))
            for r in duckdb.sql(f"DESCRIBE SELECT * FROM read_parquet('{_q(gold / (tabela + '.parquet'))}')").fetchall()]


def projeto_powerbi(spec: dict, gold: Path, conexao: dict) -> dict[str, str]:
    """Arquivos do PBIP (caminho → conteúdo). O modelo lê as tabelas do BI da empresa (LST-33) no Postgres;
    servidor, banco e schema ficam em parâmetros do Power Query, trocáveis sem editar consultas."""
    did = spec["demanda"]
    nome = f"Lastro_demanda_{did}"
    sm, rp = f"{nome}.SemanticModel", f"{nome}.Report"
    dims = sorted({v["eixo"] for v in spec["visuais"] if v.get("eixo") and v["eixo"] not in TEMPO})
    usa_tempo = any(v.get("eixo") in TEMPO for v in spec["visuais"])
    tabelas = ["fato"] + [f"dim_{d}" for d in dims] + (["dim_data"] if usa_tempo else [])
    pbi = {t: f"d{did}_{t}" for t in tabelas}  # nomes publicados no BI (LST-33)
    arqs: dict[str, str] = {}
    arqs[f"{nome}.pbip"] = _json({"$schema": SCHEMAS["pbip"], "version": "1.0", "artifacts": [{"report": {"path": rp}}],
                                  "settings": {"enableAutoRecovery": True}})
    arqs[f"{sm}/definition.pbism"] = _json({"$schema": SCHEMAS["pbism"], "version": "4.2", "settings": {}})
    arqs[f"{sm}/definition/database.tmdl"] = "database\n\tcompatibilityLevel: 1567\n"
    arqs[f"{sm}/definition/model.tmdl"] = (
        "model Model\n\tculture: pt-BR\n\tdefaultPowerBIDataSourceVersion: powerBI_V3\n\tdiscourageImplicitMeasures\n"
        "\tsourceQueryCulture: pt-BR\n\n" + "".join(f"ref table {_tmdl_nome(pbi[t])}\n" for t in tabelas))
    https = conexao.get("via") == "https"  # LST-47: sem certificado do Supabase e sem gateway no Power BI Service
    params = ((("Api", conexao["api"]), ("ChaveLastro", conexao.get("chave", "COLE_A_CHAVE_DE_LEITURA"))) if https else
              (("Servidor", f"{conexao['host']}:{conexao['porta']}"), ("Banco", conexao["banco"]), ("Esquema", conexao["esquema"])))
    arqs[f"{sm}/definition/expressions.tmdl"] = "".join(
        f'expression {p} = "{v}" meta [IsParameterQuery=true, Type="Text", IsParameterQueryRequired=true]\n'
        f"\tlineageTag: {_uuid(did, 'param', p)}\n\n"
        for p, v in params)
    for t in tabelas:
        linhas = [f"/// Lastro · demanda {did} · {t} (gold aprovado)", f"table {_tmdl_nome(pbi[t])}", f"\tlineageTag: {_uuid(did, t)}", ""]
        if t == "fato":
            for m in spec["medidas"]:
                f = AGREGACOES[m["agregacao"]][1]
                linhas += [f"\tmeasure {_tmdl_nome(m['nome'])} = {f}({_tmdl_nome(pbi[t])}[{m['coluna']}])",
                           "\t\tformatString: #,##0.00" if m["agregacao"] in {"soma", "media", "minimo", "maximo"} else "\t\tformatString: 0",
                           f"\t\tlineageTag: {_uuid(did, 'medida', m['id'])}", ""]
        for c, tp in _colunas_gold(gold, t):
            linhas += [f"\tcolumn {_tmdl_nome(c)}", f"\t\tdataType: {tp}", f"\t\tsourceColumn: {c}", "\t\tsummarizeBy: none",
                       f"\t\tlineageTag: {_uuid(did, t, c)}"]
            if c.endswith("_id") or (t == "fato" and c == "data"):
                linhas.append("\t\tisHidden")
            if tp == "dateTime":
                linhas.append("\t\tformatString: dd/mm/yyyy")
            linhas.append("")
        if https:  # URL base fixa + RelativePath: o Service consegue agendar a atualização (fonte não dinâmica)
            fonte = [(f'\t\t\t\t    Binario = Web.Contents(Api, [RelativePath = "bi/v1/{pbi[t]}.parquet", '
                      'Headers = [#"X-Lastro-Chave" = ChaveLastro]]),'), "\t\t\t\t    Tabela = Parquet.Document(Binario)"]
        else:
            fonte = ["\t\t\t\t    Fonte = PostgreSQL.Database(Servidor, Banco),",
                     f'\t\t\t\t    Tabela = Fonte{{[Schema = Esquema, Item = "{pbi[t]}"]}}[Data]']
        linhas += [f"\tpartition {_tmdl_nome(pbi[t])} = m", "\t\tmode: import", "\t\tsource =", "\t\t\t\tlet", *fonte,
                   "\t\t\t\tin", "\t\t\t\t    Tabela", ""]
        arqs[f"{sm}/definition/tables/{pbi[t]}.tmdl"] = "\n".join(linhas)
    rel = [f"relationship {_uuid(did, 'rel', d)}\n\tfromColumn: {pbi['fato']}.{d}_id\n\ttoColumn: {pbi['dim_' + d]}.{d}_id\n" for d in dims]
    if usa_tempo:
        rel.append(f"relationship {_uuid(did, 'rel', 'data')}\n\tfromColumn: {pbi['fato']}.data\n\ttoColumn: {pbi['dim_data']}.data\n")
    if rel:
        arqs[f"{sm}/definition/relationships.tmdl"] = "\n".join(rel)
    # relatório (PBIR): uma página, um visual por item do painel, em grade de 2 colunas
    arqs[f"{rp}/definition.pbir"] = _json({"$schema": SCHEMAS["pbir"], "version": "4.0", "datasetReference": {"byPath": {"path": f"../{sm}"}}})
    d = f"{rp}/definition"
    arqs[f"{d}/version.json"] = _json({"$schema": SCHEMAS["version"], "version": "2.0.0"})
    arqs[f"{d}/report.json"] = _json({"$schema": SCHEMAS["report"], "themeCollection": {"baseTheme": {
        "name": "CY24SU10", "reportVersionAtImport": {"visual": "1.8.50", "report": "2.0.50", "page": "1.3.50"}, "type": "SharedResources"}}})
    arqs[f"{d}/pages/pages.json"] = _json({"$schema": SCHEMAS["pages"], "pageOrder": ["painel"], "activePageName": "painel"})
    arqs[f"{d}/pages/painel/page.json"] = _json({"$schema": SCHEMAS["page"], "name": "painel", "displayName": spec["titulo"][:60],
                                                 "displayOption": "FitToPage", "height": 720, "width": 1280})
    med = {m["id"]: m for m in spec["medidas"]}
    y = 20
    col = 0
    for i, v in enumerate(spec["visuais"]):
        tipo, papel_eixo, papel_valor = VISUAL_PBI[v["tipo"]]
        largo = v["tipo"] in {"linha", "tabela"}
        if largo and col:
            col, y = 0, y + 220
        w, h = (1240, 200) if largo else (610, 200)
        x = 20 + col * 630
        m = med[v["medida"]]
        campo_m = {"Measure": {"Expression": {"SourceRef": {"Entity": pbi["fato"]}}, "Property": m["nome"]}}
        proj_m = {"field": campo_m, "queryRef": f"{pbi['fato']}.{m['nome']}", "nativeQueryRef": m["nome"]}
        estado: dict[str, Any] = {}
        if v.get("eixo"):
            tab = pbi["dim_data"] if v["eixo"] in TEMPO else pbi[f"dim_{v['eixo']}"]
            campo_e = {"Column": {"Expression": {"SourceRef": {"Entity": tab}}, "Property": v["eixo"]}}
            proj_e = {"field": campo_e, "queryRef": f"{tab}.{v['eixo']}", "nativeQueryRef": v["eixo"]}
            if papel_eixo == papel_valor:
                estado[papel_valor] = {"projections": [proj_e, proj_m]}
            else:
                estado[papel_eixo] = {"projections": [proj_e]}
                estado[papel_valor] = {"projections": [proj_m]}
        else:
            estado[papel_valor] = {"projections": [proj_m]}
        arqs[f"{d}/pages/painel/visuals/{v['id']}/visual.json"] = _json({
            "$schema": SCHEMAS["visual"], "name": v["id"],
            "position": {"x": x, "y": y, "z": i, "width": w, "height": h, "tabOrder": i},
            "visual": {"visualType": tipo, "query": {"queryState": estado}, "drillFilterOtherVisuals": True}})
        if largo or col == 1:
            col, y = 0, y + 220
        else:
            col = 1
    if y + 220 > 720:  # página mais alta quando há muitos visuais
        pg = json.loads(arqs[f"{d}/pages/painel/page.json"])
        pg["height"] = y + 240
        arqs[f"{d}/pages/painel/page.json"] = _json(pg)
    arqs[".gitignore"] = "**/.pbi/localSettings.json\n**/.pbi/cache.abf\n"
    arqs["LEIA-ME.txt"] = (
        f"Projeto do Power BI gerado pelo Lastro para a demanda {did} (painel versão {spec['versao']}).\n\n"
        f"1. Descompacte e abra {nome}.pbip no Power BI Desktop (gratuito).\n"
        + ("2. Em Transformar dados → Gerenciar parâmetros, cole em ChaveLastro a chave de leitura do BI\n"
           "   (portal → conta → Conectar ao BI → chave de leitura). Ela aparece uma vez só; guarde como senha.\n"
           "3. Se o Power BI pedir credencial para o endereço do Lastro, escolha Anônimo: quem autentica é a chave.\n"
           "   Clique em Atualizar para carregar os dados.\n"
           "4. No Power BI Service: publique, e em Configurações do modelo semântico → Credenciais da fonte de dados\n"
           "   escolha Anônimo e marque 'Ignorar conexão de teste' se aparecer. Não precisa de gateway.\n\n"
           if https else
           "2. Na primeira abertura, informe o usuário e a senha do BI da sua empresa (portal → conta → Conectar ao BI)\n"
           "   e clique em Atualizar para carregar os dados.\n"
           "3. Servidor, banco e schema estão em Transformar dados → Gerenciar parâmetros.\n\n")
        +
        "As medidas e os visuais vêm do painel aprovado no Lastro. Pode editar à vontade: o Lastro não sobrescreve este arquivo.\n")
    return arqs


def _json(obj: dict) -> str:
    return json.dumps(obj, ensure_ascii=False, indent=2) + "\n"
