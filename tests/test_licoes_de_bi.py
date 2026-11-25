"""Regras tiradas do dia a dia de BI do Tiago (conferência card × tabela, texto sujo, data do período)."""

import pandas as pd

from lastro.agents.explorador import _qualidade_texto
from lastro.config import carregar
from lastro.servico import Plataforma


def test_qualidade_texto_acha_grafias_marcadores_e_acentos():
    q = _qualidade_texto(["Recebido", "Recebido ", "RECEBIDO", "Aprovado", "N/A", "-", "SÃ£o Paulo", "São Paulo"])
    assert q["variantes"] == 2  # Recebido (3 grafias) e São Paulo (acento quebrado conta como outra grafia)
    assert "'Recebido'" in q["exemplos_variantes"][0] or "'Recebido'" in q["exemplos_variantes"][1]
    assert set(q["marcadores_vazio"]) == {"-", "N/A"}
    assert q["acentos_quebrados"] == 1
    assert _qualidade_texto(["Ana", "Bia"]) == {}


def _demanda(tmp_path, df, respostas):
    arq = tmp_path / "orcamentos.csv"
    df.to_csv(arq, index=False)
    plat = Plataforma.visitante(carregar(), tmp_path / "v")
    fid = plat.repo.adicionar_fonte("orcamentos", "arquivo", str(arq))
    d = plat.abrir("visitante", "Quanto cada vendedor orçou?", [fid])
    return plat, d, respostas


def test_auditor_avisa_o_que_some_do_grafico_e_o_grill_explica_a_data(tmp_path):
    df = pd.DataFrame({
        "id": range(1, 9),
        "vendedor": ["Ana", "Ana ", "ANA", "Bia", None, "N/A", "Bia", "Bia"],
        "valor": [100.0, 50.0, 10.0, 200.0, 70.0, 5.0, None, 30.0],
        "data_criacao": ["2026-09-01"] * 8,
        "data_solicitacao": ["2026-08-20", None, None, "2026-09-02", None, None, None, "2026-09-03"],
    })
    plat, d, _ = _demanda(tmp_path, df, {})
    q_data = next(q for q in d["grill"] if q["id"].endswith(":data"))
    assert "contagem por mês muda" in q_data["pergunta"] and "data_solicitacao 3" in q_data["pergunta"]
    resp = {"orcamentos:medida": "valor", "orcamentos:data": "data_criacao", "orcamentos:chave": "id", "orcamentos:filtro": "nenhum",
            "geral:revisor": "teste"}
    ids = {q["id"] for q in d["grill"]}
    d = plat.executar(plat.responder_grill(d["id"], "visitante", {k: v for k, v in resp.items() if k in ids})["id"], "visitante")
    checks = {c["checagem"]: c for c in d["resultado"]["auditoria"]["checagens"]}
    assert d["resultado"]["auditoria"]["aprovado_camada1"]  # avisos não reprovam
    fora = checks["fora do gráfico por vendedor"]
    assert fora["nivel"] == "aviso" and fora["detalhe"].startswith("1 linhas (70,00")
    assert "grafias diferentes em vendedor" in checks and "'Ana'" in checks["grafias diferentes em vendedor"]["detalhe"]
    assert "N/A" in checks["marcador de vazio em vendedor"]["detalhe"]
    assert "cartão e a tabela" in checks["nulos na medida"]["detalhe"]
    # o espaço no fim some na silver: 'Ana ' e 'Ana' viram a mesma categoria (ANA continua separada: é aviso, não conserto)
    gold = plat.pasta_demanda(d["id"]) / "gold"
    import duckdb
    nomes = sorted(r[0] for r in duckdb.sql(f"SELECT vendedor FROM '{gold / 'dim_vendedor.parquet'}' WHERE vendedor IS NOT NULL").fetchall())
    assert nomes == ["ANA", "Ana", "Bia", "N/A"]


def test_interprete_explica_por_que_nao_bate(tmp_path):
    from lastro import paineis
    from lastro.agents.interprete import Interprete

    df = pd.DataFrame({"id": range(1, 7), "vendedor": ["Ana", "Bia", None, "Bia", "Ana", None],
                       "valor": [10.0, 20.0, 30.0, 40.0, 50.0, 60.0], "data_criacao": ["2026-09-01"] * 6})
    plat, d, _ = _demanda(tmp_path, df, {})
    ids = {q["id"] for q in d["grill"]}
    resp = {"orcamentos:medida": "valor", "orcamentos:data": "data_criacao", "orcamentos:chave": "id", "geral:revisor": "t"}
    d = plat.executar(plat.responder_grill(d["id"], "visitante", {k: v for k, v in resp.items() if k in ids})["id"], "visitante")
    pasta = plat.pasta_demanda(d["id"])
    paineis.gravar(pasta, paineis.inicial(d, pasta / "gold"))
    ag = Interprete(d, pasta)
    try:
        r = ag.responder("Por que o total não bate com a soma das barras por vendedor?")
        assert r["reconhecida"] and r["conferencia"]["metodo"].endswith("conferencia-card-x-tabela.md")
        assert any("2 linhas (90,00" in m for m in r["conferencia"]["motivos"])
        assert "Por que o total não bate com a soma das barras?" in r["sugestoes"]
    finally:
        ag.fechar()
