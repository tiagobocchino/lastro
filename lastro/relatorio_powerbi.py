"""Relatório Power BI de entrega (LST-52): um PBIP multipágina por demanda, no padrão dos relatórios do Tiago no
Looker Studio (filtros no topo, cartões com comparação, "Visão geral" → "<indicador> por <dimensão>" → geografia → detalhe).

Lê a tabela pronta da demanda (`painel_<n>_…`, LST-46) por HTTPS com a chave de leitura (LST-47): sem certificado e sem
gateway. Só interpreta o que está no gold aprovado; nenhuma regra de negócio é deduzida (ADR 0011): KPIs são somas,
contagens e a média aritmética; a comparação é com o mesmo período do ano anterior.
"""

from __future__ import annotations

import json
import re
import unicodedata
from typing import Any

from .paineis import SCHEMAS, _json, _tmdl_nome, _uuid

LARGURA, ALTURA = 1280, 720
TIPO_TMDL = {"bigint": "int64", "integer": "int64", "smallint": "int64", "double precision": "double", "numeric": "double",
             "real": "double", "date": "dateTime", "timestamp without time zone": "dateTime", "boolean": "boolean", "text": "string"}
# Colunas técnicas ou de identificação que não viram eixo nem filtro (ids, documentos, partes da data já no calendário).
FORA_DOS_EIXOS = re.compile(r"(^id$|_id$|documento|^ano$|^mes$|^ano_mes$|^registros$|^data$)")
TEMA = {
    "name": "Lastro",
    "dataColors": ["#B58324", "#2F5D7C", "#8E98A3", "#A4602F", "#4F7A5A", "#56606B", "#C9A15B", "#3E4A57", "#7A8D9C", "#D6B677"],
    "background": "#FFFFFF", "foreground": "#111820", "tableAccent": "#B58324",
    "textClasses": {"title": {"fontFace": "Segoe UI Semibold", "fontSize": 12, "color": "#111820"},
                    "callout": {"fontFace": "Segoe UI Semibold", "fontSize": 26, "color": "#111820"},
                    "label": {"fontFace": "Segoe UI", "fontSize": 10, "color": "#56606B"}},
    "visualStyles": {"*": {"*": {"background": [{"color": {"solid": {"color": "#FFFFFF"}}, "transparency": 0}],
                                 "border": [{"show": True, "color": {"solid": {"color": "#D6DCE2"}}, "radius": 6}],
                                 "dropShadow": [{"show": False}]}},
                     "page": {"*": {"background": [{"color": {"solid": {"color": "#EEF1F3"}}, "transparency": 0}]}}},
}


def _sem_acento(t: str) -> str:
    return unicodedata.normalize("NFKD", t).encode("ascii", "ignore").decode().lower()


def rotulo(col: str) -> str:
    """Nome legível para título e medida: valores_produtos → Valores produtos; projeto_regiao → Região da obra."""
    especiais = {"projeto_regiao": "Região da obra", "projeto_estado": "UF da obra", "projeto_cidade": "Cidade da obra",
                 "cliente_regiao": "Região do cliente", "cliente_estado": "UF do cliente", "cliente_cidade": "Cidade do cliente",
                 "company": "Empresa", "status_nome": "Status", "vendedor_nome": "Vendedor", "grupo_nome": "Grupo",
                 "cliente_nome": "Cliente", "projeto_nome": "Obra", "produto_descricao": "Produto", "setor_nome": "Setor",
                 "cargo_nome": "Cargo", "motivo_perda": "Motivo da perda", "contrato_status": "Status do contrato"}
    if col in especiais:
        return especiais[col]
    t = col.replace("_", " ").strip()
    return t[:1].upper() + t[1:]


def eixos(colunas: dict[str, str], pergunta: str) -> list[str]:
    """Dimensões de texto da tabela pronta, as citadas na pergunta primeiro (interpretação, não regra de negócio)."""
    cands = [c for c, t in colunas.items() if t == "string" and not FORA_DOS_EIXOS.search(c)]
    p = _sem_acento(pergunta)

    def posicao(c: str) -> int:
        """Onde a dimensão aparece na pergunta ("por setor e cargo": setor antes de cargo); não citada vai para o fim."""
        achados = [p.find(_sem_acento(x)[:-1]) for x in re.split(r"_+", c) if len(x) >= 4 and _sem_acento(x)[:-1] in p]
        return min(achados) if achados else 10**6

    geo = [c for c in cands if re.search(r"_(estado|regiao|cidade)$", c)]
    resto = [c for c in cands if c not in geo and c not in ("company", "ativo")]
    return sorted(resto, key=lambda c: (posicao(c), resto.index(c))) + geo


class _Pagina:
    def __init__(self, nome: str, titulo: str):
        self.nome, self.titulo, self.visuais = nome, titulo, []

    def add(self, v: dict) -> None:
        v["name"] = f"v{len(self.visuais) + 1:02d}"
        v["position"]["z"] = v["position"]["tabOrder"] = len(self.visuais)
        self.visuais.append(v)


def _lit(texto: str) -> dict:
    return {"expr": {"Literal": {"Value": "'" + texto.replace("'", "''") + "'"}}}


def _campo(tab: str, prop: str, medida: bool = False) -> dict:
    tipo = "Measure" if medida else "Column"
    return {tipo: {"Expression": {"SourceRef": {"Entity": tab}}, "Property": prop}}


def _proj(tab: str, prop: str, medida: bool = False) -> dict:
    return {"field": _campo(tab, prop, medida), "queryRef": f"{tab}.{prop}", "nativeQueryRef": prop}


def _visual(tipo: str, x: int, y: int, w: int, h: int, papeis: dict[str, list[dict]], titulo: str | None = None,
            ordem: dict | None = None, objetos: dict | None = None) -> dict:
    vis: dict[str, Any] = {"visualType": tipo, "query": {"queryState": {p: {"projections": ps} for p, ps in papeis.items()}},
                           "drillFilterOtherVisuals": True}
    if ordem:
        vis["query"]["sortDefinition"] = {"sort": [ordem], "isDefaultSort": False}
    if titulo:
        vis["visualContainerObjects"] = {"title": [{"properties": {"show": {"expr": {"Literal": {"Value": "true"}}}, "text": _lit(titulo)}}]}
    if objetos:
        vis["objects"] = objetos
    return {"$schema": SCHEMAS["visual"], "position": {"x": x, "y": y, "z": 0, "width": w, "height": h, "tabOrder": 0}, "visual": vis}


def projeto(did: int, pergunta: str, tabela: str, colunas: dict[str, str], medida: str | None, api: str,
            chave: str = "COLE_A_CHAVE_DE_LEITURA") -> dict[str, str]:
    """Arquivos do PBIP (caminho → conteúdo). `colunas`: nome → tipo TMDL; `medida`: a coluna de valor do grill."""
    nome = f"Lastro_relatorio_{did}"
    sm, rp = f"{nome}.SemanticModel", f"{nome}.Report"
    t = tabela
    tem_data = colunas.get("data") == "dateTime"
    valores = [c for c, tp in colunas.items() if tp == "double" or (tp == "int64" and not FORA_DOS_EIXOS.search(c))]
    principal = medida if medida in valores else (valores[0] if valores else None)
    dims = eixos(colunas, pergunta)
    regiao = next((c for c in ("projeto_regiao", "cliente_regiao") if c in colunas), None)
    estado = next((c for c in ("projeto_estado", "cliente_estado") if c in colunas), None)

    # ---- medidas (DAX): só soma, contagem e média; comparação com o mesmo período do ano anterior ----------------
    med: list[tuple[str, str, str]] = [("Registros", f"SUM({_tmdl_nome(t)}[registros])", "#,##0")]
    if principal:
        tot = f"Total {rotulo(principal).lower()}"
        med += [(tot, f"SUM({_tmdl_nome(t)}[{principal}])", "#,##0.00"),
                ("Média por registro", f"DIVIDE([{tot}], [Registros])", "#,##0.00"),
                (f"% do {tot.lower()}", f"DIVIDE([{tot}], CALCULATE([{tot}], ALLSELECTED({_tmdl_nome(t)})))", "0.0%")]
        for c in valores:
            if c != principal and c != "quantidade":
                med.append((f"Total {rotulo(c).lower()}", f"SUM({_tmdl_nome(t)}[{c}])", "#,##0.00"))
        if "quantidade" in valores:
            med.append(("Quantidade", f"SUM({_tmdl_nome(t)}[quantidade])", "#,##0"))
    kpi = f"Total {rotulo(principal).lower()}" if principal else "Registros"
    if tem_data:
        med += [(f"{kpi} ano anterior", f"CALCULATE([{kpi}], SAMEPERIODLASTYEAR(Calendario[Date]))", "#,##0.00"),
                ("Var. vs ano anterior", f"DIVIDE([{kpi}] - [{kpi} ano anterior], [{kpi} ano anterior])", "+0.0%;-0.0%;0.0%")]

    arqs: dict[str, str] = {}
    arqs[f"{nome}.pbip"] = _json({"$schema": SCHEMAS["pbip"], "version": "1.0", "artifacts": [{"report": {"path": rp}}],
                                  "settings": {"enableAutoRecovery": True}})
    arqs[f"{sm}/definition.pbism"] = _json({"$schema": SCHEMAS["pbism"], "version": "4.2", "settings": {}})
    arqs[f"{sm}/definition/database.tmdl"] = "database\n\tcompatibilityLevel: 1567\n"
    tabelas_modelo = [t] + (["Calendario"] if tem_data else [])
    arqs[f"{sm}/definition/model.tmdl"] = (
        "model Model\n\tculture: pt-BR\n\tdefaultPowerBIDataSourceVersion: powerBI_V3\n\tdiscourageImplicitMeasures\n"
        "\tsourceQueryCulture: pt-BR\n\n" + "".join(f"ref table {_tmdl_nome(x)}\n" for x in tabelas_modelo))
    arqs[f"{sm}/definition/expressions.tmdl"] = "".join(
        f'expression {p} = "{v}" meta [IsParameterQuery=true, Type="Text", IsParameterQueryRequired=true]\n'
        f"\tlineageTag: {_uuid(did, 'rel', 'param', p)}\n\n" for p, v in (("Api", api), ("ChaveLastro", chave)))
    linhas = [f"/// Lastro · relatório da demanda {did} (tabela pronta do BI, LST-46)", f"table {_tmdl_nome(t)}",
              f"\tlineageTag: {_uuid(did, 'rel', t)}", ""]
    for m, dax, fmt in med:
        linhas += [f"\tmeasure {_tmdl_nome(m)} = {dax}", f"\t\tformatString: {fmt}", f"\t\tlineageTag: {_uuid(did, 'rel', 'm', m)}", ""]
    for c, tp in colunas.items():
        linhas += [f"\tcolumn {_tmdl_nome(c)}", f"\t\tdataType: {tp}", f"\t\tsourceColumn: {c}", "\t\tsummarizeBy: none",
                   f"\t\tlineageTag: {_uuid(did, 'rel', t, c)}"]
        if c == "registros" or c.endswith("_id") or c in ("id", "ano", "mes", "ano_mes"):
            linhas.append("\t\tisHidden")
        if tp == "dateTime":
            linhas.append("\t\tformatString: dd/mm/yyyy")
        if c.endswith("_estado"):
            linhas.append("\t\tdataCategory: StateOrProvince")
        elif c.endswith("_cidade"):
            linhas.append("\t\tdataCategory: City")
        linhas.append("")
    linhas += [f"\tpartition {_tmdl_nome(t)} = m", "\t\tmode: import", "\t\tsource =", "\t\t\t\tlet",
               (f'\t\t\t\t    Binario = Web.Contents(Api, [RelativePath = "bi/v1/{t}.parquet", '
                'Headers = [#"X-Lastro-Chave" = ChaveLastro]]),'), "\t\t\t\t    Tabela = Parquet.Document(Binario)",
               "\t\t\t\tin", "\t\t\t\t    Tabela", ""]
    arqs[f"{sm}/definition/tables/{t}.tmdl"] = "\n".join(linhas)
    if tem_data:
        arqs[f"{sm}/definition/tables/Calendario.tmdl"] = "\n".join([
            "/// Calendário do relatório (do primeiro ao último ano da tabela), para a comparação com o ano anterior",
            "table Calendario", f"\tlineageTag: {_uuid(did, 'rel', 'cal')}", "\tdataCategory: Time", "",
            "\tcolumn Date", "\t\tdataType: dateTime", "\t\tisKey", "\t\tformatString: dd/mm/yyyy",
            f"\t\tlineageTag: {_uuid(did, 'rel', 'cal', 'Date')}", "\t\tsummarizeBy: none", "\t\tisNameInferred", "\t\tsourceColumn: [Date]", "",
            "\tcolumn Ano = YEAR(Calendario[Date])", "\t\tdataType: int64", "\t\tformatString: 0",
            f"\t\tlineageTag: {_uuid(did, 'rel', 'cal', 'Ano')}", "\t\tsummarizeBy: none", "",
            '\tcolumn AnoMes = FORMAT(Calendario[Date], "yyyy-MM")', "\t\tdataType: string",
            f"\t\tlineageTag: {_uuid(did, 'rel', 'cal', 'AnoMes')}", "\t\tsummarizeBy: none", "",
            "\tpartition Calendario = calculated", "\t\tmode: import",
            f"\t\tsource = CALENDAR(DATE(YEAR(MIN({_tmdl_nome(t)}[data])), 1, 1), DATE(YEAR(MAX({_tmdl_nome(t)}[data])), 12, 31))", ""])
        arqs[f"{sm}/definition/relationships.tmdl"] = (
            f"relationship {_uuid(did, 'rel', 'calendario')}\n\tfromColumn: {_tmdl_nome(t)}.data\n\ttoColumn: Calendario.Date\n")

    # ---- páginas -------------------------------------------------------------------------------------------------
    paginas: list[_Pagina] = []
    filtros = [c for c in ("company", regiao) if c] + (["__ano"] if tem_data else [])

    def faixa_de_filtros(pg: _Pagina) -> None:
        w = (LARGURA - 40 - 10 * (len(filtros) - 1)) // max(len(filtros), 1)
        for i, f in enumerate(filtros):
            campo = _proj("Calendario", "Ano") if f == "__ano" else _proj(t, f)
            pg.add(_visual("slicer", 20 + i * (w + 10), 12, w, 56, {"Values": [campo]}, "Ano" if f == "__ano" else rotulo(f),
                           objetos={"data": [{"properties": {"mode": _lit("Dropdown")}}]}))

    def cartoes(pg: _Pagina, y: int = 80) -> None:
        cs = [kpi, "Registros"] + (["Média por registro"] if principal else []) + (["Var. vs ano anterior"] if tem_data else [])
        w = (LARGURA - 40 - 10 * (len(cs) - 1)) // len(cs)
        for i, m in enumerate(cs):
            pg.add(_visual("card", 20 + i * (w + 10), y, w, 96, {"Values": [_proj(t, m, True)]}, m))

    def barras(pg: _Pagina, eixo: str, x: int, y: int, w: int, h: int, tipo: str = "clusteredBarChart") -> None:
        pg.add(_visual(tipo, x, y, w, h, {"Category": [_proj(t, eixo)], "Y": [_proj(t, kpi, True)]}, f"{kpi} por {rotulo(eixo).lower()}",
                       ordem={"field": _campo(t, kpi, True), "direction": "Descending"}))

    def evolucao(pg: _Pagina, x: int, y: int, w: int, h: int) -> None:
        if tem_data:
            pg.add(_visual("lineChart", x, y, w, h, {"Category": [_proj("Calendario", "AnoMes")], "Y": [_proj(t, kpi, True)]},
                           f"{kpi} por mês", ordem={"field": _campo("Calendario", "AnoMes"), "direction": "Ascending"}))

    # 1. Visão geral: filtros, cartões, evolução, a dimensão principal e a composição por empresa (ou funil por status)
    pg = _Pagina("visao_geral", "Visão geral")
    faixa_de_filtros(pg)
    cartoes(pg)
    evolucao(pg, 20, 190, 760, 250)
    if dims:
        barras(pg, dims[0], 790, 190, 470, 510)
    status = next((d for d in dims if "status" in d), None)
    if status:
        pg.add(_visual("funnel", 20, 450, 760, 250, {"Category": [_proj(t, status)], "Y": [_proj(t, "Registros", True)]},
                       f"Registros por {rotulo(status).lower()}", ordem={"field": _campo(t, "Registros", True), "direction": "Descending"}))
    elif "company" in colunas:
        pg.add(_visual("donutChart", 20, 450, 760, 250, {"Category": [_proj(t, "company")], "Y": [_proj(t, kpi, True)]},
                       f"{kpi} por empresa"))
    paginas.append(pg)
    # 2. Uma página por dimensão (no máximo três): ranking, evolução e a matriz dimensão × ano
    for d in [x for x in dims if not re.search(r"_(estado|regiao|cidade)$", x)][:3]:
        pg = _Pagina(f"por_{re.sub(r'[^a-z0-9]+', '_', _sem_acento(d))}", f"{kpi} por {rotulo(d).lower()}"[:60])
        faixa_de_filtros(pg)
        barras(pg, d, 20, 80, 620, 620)
        if tem_data:
            pg.add(_visual("pivotTable", 650, 80, 610, 360, {"Rows": [_proj(t, d)], "Columns": [_proj("Calendario", "Ano")],
                                                              "Values": [_proj(t, kpi, True)]}, f"{rotulo(d)} × ano"))
            pg.add(_visual("tableEx", 650, 450, 610, 250, {"Values": [_proj(t, d), _proj(t, kpi, True), _proj(t, "Registros", True)]
                                                            + ([_proj(t, f"% do {kpi.lower()}", True)] if principal else [])},
                           f"{rotulo(d)}: participação"))
        paginas.append(pg)
    # 3. Geografia: região e UF (estado e região no máximo, como pedido para os relatórios rápidos e de entrega)
    if regiao or estado:
        pg = _Pagina("geografia", "Geografia")
        faixa_de_filtros(pg)
        if regiao:
            barras(pg, regiao, 20, 80, 400, 300, "clusteredColumnChart")
        if estado:
            barras(pg, estado, 430, 80, 830, 300, "clusteredColumnChart")
        geo_cols = [c for c in (regiao, estado, estado and estado.replace("_estado", "_cidade")) if c and c in colunas]
        pg.add(_visual("tableEx", 20, 390, 1240, 310, {"Values": [_proj(t, c) for c in geo_cols] + [_proj(t, kpi, True), _proj(t, "Registros", True)]},
                       "Detalhe por local"))
        paginas.append(pg)
    # 4. Detalhe: a tabela para conferência, com os mesmos números dos cartões
    pg = _Pagina("detalhe", "Detalhe")
    faixa_de_filtros(pg)
    cols_det = ([_proj(t, "data")] if tem_data else []) + [_proj(t, d) for d in dims[:4]]
    pg.add(_visual("tableEx", 20, 80, 1240, 620, {"Values": cols_det + [_proj(t, kpi, True), _proj(t, "Registros", True)]}, "Detalhe para conferência"))
    paginas.append(pg)

    arqs[f"{rp}/definition.pbir"] = _json({"$schema": SCHEMAS["pbir"], "version": "4.0", "datasetReference": {"byPath": {"path": f"../{sm}"}}})
    d = f"{rp}/definition"
    arqs[f"{d}/version.json"] = _json({"$schema": SCHEMAS["version"], "version": "2.0.0"})
    arqs[f"{d}/report.json"] = _json({
        "$schema": SCHEMAS["report"],
        "themeCollection": {"baseTheme": {"name": "CY24SU10", "reportVersionAtImport": {"visual": "1.8.50", "report": "2.0.50", "page": "1.3.50"},
                                          "type": "SharedResources"},
                            "customTheme": {"name": "Lastro.json", "reportVersionAtImport": {"visual": "1.8.50", "report": "2.0.50", "page": "1.3.50"},
                                            "type": "RegisteredResources"}},
        "resourcePackages": [{"name": "RegisteredResources", "type": "RegisteredResources",
                              "items": [{"name": "Lastro.json", "path": "Lastro.json", "type": "CustomTheme"}]}]})
    arqs[f"{rp}/StaticResources/RegisteredResources/Lastro.json"] = json.dumps(TEMA, ensure_ascii=False, indent=2) + "\n"
    arqs[f"{d}/pages/pages.json"] = _json({"$schema": SCHEMAS["pages"], "pageOrder": [p.nome for p in paginas], "activePageName": paginas[0].nome})
    for p in paginas:
        arqs[f"{d}/pages/{p.nome}/page.json"] = _json({"$schema": SCHEMAS["page"], "name": p.nome, "displayName": p.titulo,
                                                        "displayOption": "FitToPage", "height": ALTURA, "width": LARGURA})
        for v in p.visuais:
            arqs[f"{d}/pages/{p.nome}/visuals/{v['name']}/visual.json"] = _json(v)
    arqs[".gitignore"] = "**/.pbi/localSettings.json\n**/.pbi/cache.abf\n"
    arqs["LEIA-ME.txt"] = (
        f"Relatório de entrega do Lastro · demanda {did}\n\"{pergunta}\"\n\n"
        f"Páginas: {', '.join(p.titulo for p in paginas)}.\n\n"
        f"1. Descompacte e abra {nome}.pbip no Power BI Desktop.\n"
        "2. Transformar dados → Gerenciar parâmetros → ChaveLastro: cole a chave de leitura do BI (portal → conta → Conectar ao BI).\n"
        "3. Se pedir credencial para o endereço do Lastro, escolha Anônimo. Clique em Atualizar.\n\n"
        "Os cartões somam a tabela pronta da demanda aprovada; a página Detalhe traz os mesmos números para conferência.\n"
        "Regras de negócio (o que conta como venda, qual data vale) são as que o cliente respondeu no grill do Lastro.\n")
    return arqs


def colunas_do_postgres(tipos: list[tuple[str, str]]) -> dict[str, str]:
    return {n: TIPO_TMDL.get(tp, "string") for n, tp in tipos}
