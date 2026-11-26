"""LST-52: relatório Power BI de entrega gerado da tabela pronta, validado nos schemas oficiais."""

import json
import re

from lastro import relatorio_powerbi as rp
from tests.test_paineis import _registro

# colunas reais das tabelas prontas da gimi-teste (information_schema em produção, 26/11)
VENDAS = rp.colunas_do_postgres([("id", "bigint"), ("motivo_perda", "text"), ("company", "text"), ("status_nome", "text"),
    ("cliente_nome", "text"), ("cliente_documento", "text"), ("cliente_cidade", "text"), ("cliente_estado", "text"),
    ("cliente_regiao", "text"), ("projeto_cidade", "text"), ("projeto_estado", "text"), ("projeto_regiao", "text"),
    ("vendedor_nome", "text"), ("grupo_nome", "text"), ("data", "date"), ("ano", "bigint"), ("mes", "bigint"),
    ("ano_mes", "text"), ("valores_produtos", "double precision"), ("valores_desconto", "double precision"), ("registros", "integer")])
RH = rp.colunas_do_postgres([("id", "bigint"), ("ativo", "text"), ("company", "text"), ("cargo_nome", "text"), ("setor_nome", "text"),
                             ("data", "date"), ("ano", "bigint"), ("mes", "bigint"), ("ano_mes", "text"), ("registros", "integer")])


def _validar(arqs: dict) -> dict:
    import jsonschema

    reg = _registro()
    jsons = {k: json.loads(v) for k, v in arqs.items() if k.endswith((".json", ".pbir", ".pbism", ".pbip")) and "RegisteredResources" not in k}
    for caminho, doc in jsons.items():
        schema = reg.get_or_retrieve(doc["$schema"]).value.contents
        erros = sorted(jsonschema.Draft7Validator(schema, registry=reg).iter_errors(doc), key=str)
        assert not erros, f"{caminho}: {erros[0].message}"
    return jsons


def test_relatorio_de_vendas_multipagina_valida_e_aponta_para_o_que_existe():
    arqs = rp.projeto(15, "Quanto cada vendedor vendeu, em valor de produtos, nos contratos aprovados?",
                      "painel_15_vendas", VENDAS, "valores_produtos", "https://lastro.exemplo/")
    jsons = _validar(arqs)
    nome = "Lastro_relatorio_15"
    paginas = jsons[f"{nome}.Report/definition/pages/pages.json"]["pageOrder"]
    titulos = [jsons[f"{nome}.Report/definition/pages/{p}/page.json"]["displayName"] for p in paginas]
    assert titulos[0] == "Visão geral" and titulos[1] == "Total valores produtos por vendedor"  # a dimensão citada na pergunta vem primeiro
    assert "Geografia" in titulos and titulos[-1] == "Detalhe"
    tab = arqs[f"{nome}.SemanticModel/definition/tables/painel_15_vendas.tmdl"]
    medidas = dict(re.findall(r"^\tmeasure (.+?) = (.+)$", tab, re.MULTILINE))
    assert medidas["'Total valores produtos'"] == "SUM(painel_15_vendas[valores_produtos])"
    assert "SAMEPERIODLASTYEAR(Calendario[Date])" in medidas["'Total valores produtos ano anterior'"]
    assert 'RelativePath = "bi/v1/painel_15_vendas.parquet"' in tab and "dataCategory: StateOrProvince" in tab
    cal = arqs[f"{nome}.SemanticModel/definition/tables/Calendario.tmdl"]
    assert "partition Calendario = calculated" in cal and "dataCategory: Time" in cal
    assert "toColumn: Calendario.Date" in arqs[f"{nome}.SemanticModel/definition/relationships.tmdl"]
    colunas = set(VENDAS)
    nomes_medidas = {m.strip("'") for m in medidas}
    for k, doc in jsons.items():
        if not k.endswith("visual.json"):
            continue
        for papel in doc["visual"]["query"]["queryState"].values():
            for p in papel["projections"]:
                f = p["field"]
                if "Measure" in f:
                    assert f["Measure"]["Property"] in nomes_medidas, k
                else:
                    ent, prop = f["Column"]["Expression"]["SourceRef"]["Entity"], f["Column"]["Property"]
                    assert (ent == "Calendario" and prop in ("Ano", "AnoMes")) or (ent == "painel_15_vendas" and prop in colunas), k
        assert "documento" not in json.dumps(doc)  # documento do cliente não vira eixo nem coluna de detalhe
    filtros = [d for k, d in jsons.items() if "/visao_geral/" in k and k.endswith("visual.json") and d["visual"]["visualType"] == "slicer"]
    assert len(filtros) == 3  # empresa, região e ano no topo, como nos relatórios do Looker
    funil = [d for k, d in jsons.items() if k.endswith("visual.json") and d["visual"]["visualType"] == "funnel"]
    assert funil and funil[0]["visual"]["query"]["queryState"]["Category"]["projections"][0]["field"]["Column"]["Property"] == "status_nome"
    assert json.loads(arqs[f"{nome}.Report/StaticResources/RegisteredResources/Lastro.json"])["dataColors"][0] == "#B58324"


def test_relatorio_de_rh_sem_valor_conta_registros_e_tem_paginas_por_setor_e_cargo():
    arqs = rp.projeto(18, "Quantos funcionários ativos temos por setor e cargo?", "painel_18_rh", RH, None, "https://lastro.exemplo/")
    jsons = _validar(arqs)
    pgs = jsons["Lastro_relatorio_18.Report/definition/pages/pages.json"]["pageOrder"]
    titulos = [jsons[f"Lastro_relatorio_18.Report/definition/pages/{p}/page.json"]["displayName"] for p in pgs]
    assert titulos == ["Visão geral", "Nº de registros por setor", "Nº de registros por cargo", "Detalhe"]
    tab = arqs["Lastro_relatorio_18.SemanticModel/definition/tables/painel_18_rh.tmdl"]
    assert "measure 'Nº de registros' = SUM(painel_18_rh[registros])" in tab and "Total" not in tab.split("column")[0]


def test_coluna_de_um_valor_so_nao_vira_pagina():
    dist = {"status_nome": 1, "motivo_perda": 0, "vendedor_nome": 12, "grupo_nome": 6, "cliente_nome": 236, "company": 4,
            "projeto_regiao": 5, "projeto_estado": 17, "projeto_cidade": 30, "cliente_cidade": 20, "cliente_estado": 7, "cliente_regiao": 4}
    arqs = rp.projeto(15, "Quanto cada vendedor vendeu, em valor de produtos, nos contratos aprovados?",
                      "painel_15_vendas", VENDAS, "valores_produtos", "https://lastro.exemplo/", distintos=dist)
    jsons = _validar(arqs)
    pgs = jsons["Lastro_relatorio_15.Report/definition/pages/pages.json"]["pageOrder"]
    assert pgs == ["visao_geral", "por_vendedor_nome", "por_cliente_nome", "por_grupo_nome", "geografia", "detalhe"]
    assert not any(d["visual"]["visualType"] == "funnel" for k, d in jsons.items() if k.endswith("visual.json"))  # status de um valor só


def test_nenhuma_medida_tem_o_nome_de_uma_coluna():
    """O Power BI recusa abrir o projeto se medida e coluna da mesma tabela tiverem o mesmo nome (sem diferenciar caixa)."""
    itens = rp.colunas_do_postgres([("id", "bigint"), ("company", "text"), ("produto_descricao", "text"), ("data", "date"),
                                    ("quantidade", "bigint"), ("valores_total", "double precision"), ("registros", "integer")])
    for cols, med in ((VENDAS, "valores_produtos"), (RH, None), (itens, "valores_total")):
        arqs = rp.projeto(1, "Quanto por produto?", "painel_1_x", cols, med, "https://lastro.exemplo/")
        tab = arqs["Lastro_relatorio_1.SemanticModel/definition/tables/painel_1_x.tmdl"]
        medidas = {m.strip("'").lower() for m in re.findall(r"^\tmeasure (.+?) = ", tab, re.MULTILINE)}
        colunas = {c.strip("'").lower() for c in re.findall(r"^\tcolumn (.+)$", tab, re.MULTILINE)}
        assert not medidas & colunas, medidas & colunas
