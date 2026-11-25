"""Planilha real com aspas, quebra de linha, cabeçalho vazio e nome repetido nas colunas: tem que ser lida."""

import pandas as pd

from lastro.conectores import Fonte, Sandbox, nome_seguro


def test_nome_seguro():
    assert nome_seguro('N º "E"') == "N º E"
    assert nome_seguro("Valor\ntotal ") == "Valor total"
    assert nome_seguro("", 3) == "coluna_4"
    assert nome_seguro("Unnamed: 2", 2) == "coluna_3"


def _abrir(tmp_path, df, ext):
    arq = tmp_path / f"p{ext}"
    if ext == ".xlsx":
        df.to_excel(arq, index=False)
    else:
        df.to_csv(arq, index=False)
    sb = Sandbox(tmp_path)
    view = sb.anexar(Fonte("planilha", "arquivo", str(arq)))
    return sb, view


def test_planilha_com_aspas_quebra_e_repetido(tmp_path):
    df = pd.DataFrame([[1, 2, "Ana", 10.5, "x"]], columns=['N º "E"', 'N º "G"', "Vendedor", "Valor\ntotal", "Vendedor "])
    for ext in (".xlsx", ".csv"):
        sb, view = _abrir(tmp_path, df, ext)
        cols = [r[0] for r in sb.consultar(f"DESCRIBE {view}")[1]]
        assert cols[:4] == ["N º E", "N º G", "Vendedor", "Valor total"], (ext, cols)
        assert cols[4].startswith("Vendedor_") and len({c.lower() for c in cols}) == 5, (ext, cols)
        for c in cols:  # todas consultáveis entre aspas, como os agentes fazem
            sb.consultar(f'SELECT count(DISTINCT "{c}") FROM {view}')


def test_moeda_em_texto_vira_numero(tmp_path):
    df = pd.DataFrame({"Previsão": ["R$ 526530", "R$ 1.234,56", "R$ -10,00", None], "Obs": ["R$ 5", "texto", "R$ 7", "x"],
                       "Br": ["1.234,50", "10,00", "3,5", "7"]})
    sb, view = _abrir(tmp_path, df, ".xlsx")
    tipos = {r[0]: r[1] for r in sb.consultar(f"DESCRIBE {view}")[1]}
    assert tipos["Previsão"].startswith(("DOUBLE", "DECIMAL")), tipos
    assert tipos["Obs"] == "VARCHAR"  # mistura texto com moeda: não mexe
    assert tipos["Br"].startswith(("DOUBLE", "DECIMAL")), tipos
    soma = sb.consultar(f'SELECT round(sum("Previsão"), 2), round(sum("Br"), 2) FROM {view}')[1][0]
    assert soma == (527754.56, 1255.0)


def test_numero_do_processo_nao_vira_medida(tmp_path):
    from lastro.config import carregar
    from lastro.servico import Plataforma

    df = pd.DataFrame({'N º "E"': range(100, 140), "Vendedor": ["Ana", "Bia"] * 20, "Previsão": [f"R$ {i * 1000}" for i in range(40)]})
    arq = tmp_path / "processos.xlsx"
    df.to_excel(arq, index=False)
    plat = Plataforma.visitante(carregar(), tmp_path / "v")
    fid = plat.repo.adicionar_fonte("planilha", "arquivo", str(arq))
    d = plat.abrir("visitante", "Quanto cada vendedor tem previsto?", [fid])
    cols = {c["nome"]: c["papel"] for c in next(iter(d["resultado"]["perfis"].values()))["colunas"]}
    assert cols["N º E"] == "identificador" and cols["Previsão"] == "numero"
    medida = next(q for q in d["grill"] if q["id"].endswith(":medida"))
    assert medida["sugestao"] == "Previsão"


def test_painel_usa_a_medida_acentuada_e_nunca_a_chave(tmp_path):
    from lastro import paineis
    from lastro.config import carregar
    from lastro.servico import Plataforma

    df = pd.DataFrame({'N º "E"': range(100, 140), "Vendedor": ["Ana", "Bia"] * 20, "Previsão": [f"R$ {i * 1000}" for i in range(40)]})
    arq = tmp_path / "processos.xlsx"
    df.to_excel(arq, index=False)
    plat = Plataforma.visitante(carregar(), tmp_path / "v")
    fid = plat.repo.adicionar_fonte("planilha", "arquivo", str(arq))
    d = plat.abrir("visitante", "Quanto cada vendedor tem previsto?", [fid])
    d = plat.executar(plat.responder_grill(d["id"], "visitante", {"geral:revisor": "teste"})["id"], "visitante")
    gold = plat.pasta_demanda(d["id"]) / "gold"
    assert "n_e" not in paineis.catalogo(gold, d["resultado"]["modelo"])["medidas"]
    spec = paineis.para_visitante(d, gold, "Vendedor", None, "ranking")
    assert spec["medidas"][0]["coluna"] == "previsao"
