"""LST-39: demonstração do site — sessão temporária, perguntas, painel e apagamento com recibo."""

from __future__ import annotations

import importlib
import io
import logging
import sqlite3

import pandas as pd
import pytest

from lastro.config import RAIZ, carregar
from lastro.demo import Demos, ErroDemo

EXEMPLO = RAIZ / "exemplos" / "orcamentos.csv"


@pytest.fixture
def api(monkeypatch, tmp_path):
    from fastapi.testclient import TestClient

    monkeypatch.setenv("LASTRO_HOME", str(tmp_path / "home"))
    monkeypatch.setenv("LASTRO_DEMO", "1")
    monkeypatch.setenv("LASTRO_DEMO_DIR", str(tmp_path / "demo"))
    monkeypatch.delenv("LASTRO_BANCO_URL", raising=False)
    import lastro.api as modulo

    modulo = importlib.reload(modulo)

    class SemEspelho:
        def __getattr__(self, nome):
            raise AssertionError("a demonstração tocou o espelho do Storage")

    monkeypatch.setattr(modulo, "espelho", SemEspelho())
    return modulo, TestClient(modulo.app), tmp_path / "demo"


def _linhas_no_banco(modulo) -> int:
    con = sqlite3.connect(modulo.cfg.banco)
    try:
        return sum(con.execute(f"SELECT count(*) FROM {t}").fetchone()[0] for t in ("tenants", "usuarios", "fontes", "demandas", "eventos"))
    finally:
        con.close()


def test_exemplo_de_ponta_a_ponta_e_nada_sobra(api, caplog):
    modulo, c, base = api
    caplog.set_level(logging.INFO)
    antes = _linhas_no_banco(modulo)
    r = c.post("/api/demo/sessoes", data={"exemplo": "true"})
    assert r.status_code == 200
    s = r.json()
    assert s["perfil"]["linhas"] == 612 and {"nome": "valor_vendido", "papel": "numero"} in s["perfil"]["colunas"]
    ids = {q["id"] for q in s["perguntas"]}
    assert "geral:revisor" not in ids and "planilha:medida" in ids  # sem segunda camada na demonstração
    assert len(list(base.glob("demo-*"))) == 1
    r = c.post(f"/api/demo/sessoes/{s['sessao']}/painel",
               json={"respostas": {"planilha:medida": "valor_vendido", "demo:quebra": "vendedor", "demo:formato": "ranking (barras)"}})
    p = r.json()
    assert r.status_code == 200 and "14.030.477,92" in p["html"] and p["modo"] == "demonstracao" and p["auditoria"]["aprovada"]
    recibo = p["recibo"]
    assert recibo["conferido"] and recibo["arquivos"] > 5 and recibo["tabelas"] >= 3 and recibo["bytes"] > 0 and recibo["registros_em_memoria"] > 0
    assert list(base.glob("demo-*")) == [] and modulo._DEMOS.abertas == 0
    assert _linhas_no_banco(modulo) == antes  # nada no banco
    assert c.post(f"/api/demo/sessoes/{s['sessao']}/painel", json={}).status_code == 404  # a sessão não existe mais
    assert "etapa=apagou" in caplog.text


def test_planilha_propria_csv_e_excel_sem_vazar_no_log(api, caplog):
    _, c, base = api
    caplog.set_level(logging.DEBUG)
    df = pd.DataFrame({"regiao_secreta_xyz": ["Norte", "Sul", "Norte", "Leste"], "receita": [10.5, 20, 30, 40],
                       "cliente_confidencial": ["ACME_VALOR_SECRETO", "B", "C", "D"]})
    for nome, conteudo in (("vendas.csv", df.to_csv(index=False).encode()), ("vendas.xlsx", _xlsx(df))):
        s = c.post("/api/demo/sessoes", files={"arquivo": (nome, conteudo)}).json()
        assert s["perfil"]["linhas"] == 4
        p = c.post(f"/api/demo/sessoes/{s['sessao']}/painel", json={"respostas": {}}).json()
        assert "html" in p and p["recibo"]["conferido"]
    texto = caplog.text
    for segredo in ("regiao_secreta_xyz", "cliente_confidencial", "ACME_VALOR_SECRETO", "Norte", "receita"):
        assert segredo not in texto, f"o log vazou '{segredo}'"
    assert list(base.glob("demo-*")) == []


def _xlsx(df: pd.DataFrame) -> bytes:
    buf = io.BytesIO()
    df.to_excel(buf, index=False)
    return buf.getvalue()


@pytest.mark.parametrize(("nome", "conteudo", "trecho"), [
    ("dados.txt", b"a,b\n1,2\n", "CSV ou Excel"),
    ("grande.csv", b"a,b\n" + b"1,2\n" * (5 * 1024 * 1024 // 4 + 10), "5 MB"),
    ("quebrado.xlsx", b"isto nao e excel", "não consegui ler"),
])
def test_recusas_nao_deixam_nada(api, nome, conteudo, trecho):
    _, c, base = api
    r = c.post("/api/demo/sessoes", files={"arquivo": (nome, conteudo)})
    assert r.status_code == 400 and trecho in r.json()["detail"]
    assert list(base.glob("demo-*")) == []


def test_desistir_apaga_com_recibo(api):
    _, c, base = api
    s = c.post("/api/demo/sessoes", data={"exemplo": "true"}).json()
    r = c.delete(f"/api/demo/sessoes/{s['sessao']}").json()
    assert r["recibo"]["conferido"] and r["recibo"]["arquivos"] > 0 and list(base.glob("demo-*")) == []
    assert c.delete(f"/api/demo/sessoes/{s['sessao']}").status_code == 404


def test_desligada_por_padrao(monkeypatch, tmp_path):
    from fastapi.testclient import TestClient

    monkeypatch.setenv("LASTRO_HOME", str(tmp_path))
    monkeypatch.delenv("LASTRO_DEMO", raising=False)
    import lastro.api as modulo

    modulo = importlib.reload(modulo)
    assert TestClient(modulo.app).post("/api/demo/sessoes", data={"exemplo": "true"}).status_code == 404


def test_sessao_abandonada_e_varrida_e_restos_somem_ao_reiniciar(monkeypatch, tmp_path):
    monkeypatch.setenv("LASTRO_HOME", str(tmp_path / "home"))
    base = tmp_path / "demo"
    demos = Demos(carregar(), base, ttl_s=900)
    s, _ = demos.abrir(None, None, agora=1_000.0)
    assert demos.varrer(agora=1_000.0 + 899) == 0 and s.pasta.exists()
    assert demos.varrer(agora=1_000.0 + 901) == 1 and not s.pasta.exists()
    with pytest.raises(ErroDemo, match="expirou"):
        demos.responder(s.id, {}, agora=1_000.0 + 902)
    resto = base / "demo-sobra-de-antes"
    (resto / "fontes").mkdir(parents=True)
    (resto / "fontes" / "x.csv").write_text("a\n1\n")
    Demos(carregar(), base)  # servidor reiniciou
    assert not resto.exists()


# ---- LST-40: grill de "como mostrar" ---------------------------------------------------------

def test_no_maximo_quatro_perguntas_cada_uma_com_sugestao(api):
    _, c, _ = api
    s = c.post("/api/demo/sessoes", data={"exemplo": "true"}).json()
    ps = {q["id"]: q for q in s["perguntas"]}
    assert list(ps) == ["planilha:medida", "demo:quebra", "demo:periodo", "demo:formato"]
    assert all(q["sugestao"] in q["opcoes"] for q in ps.values())
    assert ps["demo:formato"]["opcoes"] == ["ranking (barras)", "tabela", "evolução no tempo", "só o número"]
    assert set(ps["demo:quebra"]["opcoes"]) == {"empresa", "vendedor", "estado", "segmento", "status"}


@pytest.mark.parametrize(("respostas", "esperado"), [
    ({"demo:formato": "só o número"}, [("kpi", None)]),
    ({"demo:formato": "ranking (barras)", "demo:quebra": "estado"}, [("kpi", None), ("barras", "estado")]),
    ({"demo:formato": "tabela", "demo:quebra": "segmento"}, [("kpi", None), ("tabela", "segmento")]),
    ({"demo:formato": "evolução no tempo", "demo:periodo": "por ano"}, [("kpi", None), ("linha", "ano")]),
    ({"demo:formato": "evolução no tempo"}, [("kpi", None), ("linha", "ano_mes")]),
])
def test_respostas_viram_o_painel(api, monkeypatch, respostas, esperado):
    _, c, _ = api
    s = c.post("/api/demo/sessoes", data={"exemplo": "true"}).json()
    capturado = {}
    import lastro.demo as demo_mod

    original = demo_mod.paineis.para_visitante

    def espiao(*a, **k):
        capturado["spec"] = original(*a, **k)
        return capturado["spec"]

    monkeypatch.setattr(demo_mod.paineis, "para_visitante", espiao)
    p = c.post(f"/api/demo/sessoes/{s['sessao']}/painel", json={"respostas": respostas}).json()
    assert [(v["tipo"], v.get("eixo")) for v in capturado["spec"]["visuais"]] == esperado
    assert p["visuais"] == [v["titulo"] for v in capturado["spec"]["visuais"]] and p["recibo"]["conferido"]


def test_resposta_fora_das_opcoes_volta_sem_perder_a_sessao(api):
    _, c, base = api
    s = c.post("/api/demo/sessoes", data={"exemplo": "true"}).json()
    r = c.post(f"/api/demo/sessoes/{s['sessao']}/painel", json={"respostas": {"demo:quebra": "cidade"}})
    assert r.status_code == 400 and "escolha uma das opções" in r.json()["detail"]
    assert len(list(base.glob("demo-*"))) == 1  # a sessão continua: o visitante corrige e tenta de novo
    assert c.post(f"/api/demo/sessoes/{s['sessao']}/painel", json={"respostas": {"demo:quebra": "estado"}}).json()["recibo"]["conferido"]


def test_planilha_so_com_numeros_oferece_so_o_numero(api):
    _, c, _ = api
    s = c.post("/api/demo/sessoes", files={"arquivo": ("n.csv", b"custo,receita\n1,10\n2,20\n3,30\n")}).json()
    ps = {q["id"]: q for q in s["perguntas"]}
    assert list(ps) == ["planilha:medida", "demo:formato"] and ps["demo:formato"]["opcoes"] == ["só o número"]
    p = c.post(f"/api/demo/sessoes/{s['sessao']}/painel", json={"respostas": {"planilha:medida": "receita"}}).json()
    assert "60" in p["html"] and p["visuais"] == ["Receita (total)"]


def test_toda_combinacao_de_respostas_gera_painel_valido_contra_o_gold(monkeypatch, tmp_path):
    """Critério do LST-40: cada combinação (medida × quebra × período × formato) vira especificação válida
    e os números saem do gold sem erro."""
    import itertools

    from lastro import paineis
    from lastro.demo import FORMATOS, PERIODOS

    monkeypatch.setenv("LASTRO_HOME", str(tmp_path / "home"))
    demos = Demos(carregar(), tmp_path / "demo")
    s, abertura = demos.abrir(None, None)
    ps = {q["id"]: q for q in abertura["perguntas"]}
    plat = s.plataforma
    d = plat.executar(plat.responder_grill(s.demanda_id, "visitante", {"geral:revisor": "demo"})["id"], "visitante")
    gold = plat.pasta_demanda(d["id"]) / "gold"
    combinacoes = list(itertools.product(ps["demo:quebra"]["opcoes"], ps["demo:periodo"]["opcoes"], ps["demo:formato"]["opcoes"]))
    assert len(combinacoes) == 5 * 2 * 4
    assert d["resultado"]["auditoria"]["aprovado_camada1"]
    esperado_total = d["resultado"]["resposta"]["total"]  # o total que a auditoria (camada 1) conferiu, já sem repetidos
    for quebra, periodo, formato in combinacoes:
        spec = paineis.para_visitante(d, gold, quebra, PERIODOS[periodo], FORMATOS[formato])
        valores = paineis.dados(spec, gold)
        assert valores["v1"] == pytest.approx(esperado_total, abs=0.01)
        if FORMATOS[formato] == "numero":
            assert len(spec["visuais"]) == 1
        else:
            assert len(valores["v2"]) > 0, (quebra, periodo, formato)
    assert demos.apagar(s.id)["conferido"]
