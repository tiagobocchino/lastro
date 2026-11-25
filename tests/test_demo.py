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
               json={"respostas": {"planilha:medida": "valor_vendido", "planilha:filtro": "status = 'Fechado'"}})
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
