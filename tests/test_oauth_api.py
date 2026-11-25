"""LST-9 pela API: o admin autoriza uma vez, o token vai só para o cofre e o teste real usa o cofre."""

from __future__ import annotations

import importlib
from urllib.parse import parse_qs

import httpx
import pytest

from lastro.saas.simulador import Simulador


@pytest.fixture
def cliente(monkeypatch, tmp_path):
    from fastapi.testclient import TestClient

    monkeypatch.setenv("LASTRO_HOME", str(tmp_path))
    monkeypatch.setenv("LASTRO_OAUTH_CONTAAZUL_CLIENT_ID", "app-lastro")
    monkeypatch.setenv("LASTRO_OAUTH_CONTAAZUL_CLIENT_SECRET", "segredo-app")
    import lastro.api as api

    api = importlib.reload(api)
    sim = Simulador("contaazul", n=40)
    monkeypatch.setattr(api, "_cliente_oauth", lambda: httpx.Client(transport=sim.transporte()))
    api.banco.criar_tenant("acme", "Acme")
    api.banco.criar_usuario("acme", "adm@acme", "Adm", "admin", "senha123")
    api.banco.criar_usuario("acme", "ana@acme", "Ana", "demandante", "senha123")
    c = TestClient(api.app)

    def entrar(email: str) -> dict:
        return {"Authorization": "Bearer " + c.post("/api/login", json={"email": email, "senha": "senha123"}).json()["token"]}

    return api, c, entrar, sim, tmp_path


def _autorizar(c, entrar):
    url = c.get("/api/saas/contaazul/oauth/iniciar", headers=entrar("adm@acme")).json()["url"]
    q = parse_qs(url.split("?", 1)[1])
    assert url.startswith("https://login.contaazul.com/#/oauth/authorize?") and q["client_id"] == ["app-lastro"]
    assert q["redirect_uri"] == ["http://testserver/oauth/retorno"]
    return c.get("/oauth/retorno", params={"code": Simulador.CODIGO_SANDBOX, "state": q["state"][0]}, follow_redirects=False)


def test_admin_autoriza_uma_vez_e_o_token_vai_so_para_o_cofre(cliente):
    api, c, entrar, sim, home = cliente
    r = _autorizar(c, entrar)
    assert r.status_code == 303 and r.headers["location"] == "/?autorizado=contaazul"
    guardado = api.cofre.ler("lastro:acme:oauth:contaazul")
    assert "sim-rt-1" in guardado
    banco_bruto = (home / "lastro.db").read_bytes()
    assert b"sim-rt" not in banco_bruto and b"sim-at" not in banco_bruto  # nem tabela nem rastro têm token
    eventos = api.banco.con.execute("SELECT acao, detalhe FROM eventos").fetchall()
    assert [tuple(e) for e in eventos] == [("autorizou_conector", '{"saas": "contaazul"}')]


def test_teste_real_usa_o_cofre_e_regrava_ao_renovar(cliente):
    api, c, entrar, sim, _ = cliente
    _autorizar(c, entrar)
    sim._oauth_acesso.clear()  # força 401 e renovação
    r = c.post("/api/saas/contaazul/testar", headers=entrar("adm@acme"),
               json={"entidade": "vendas", "credenciais": {}, "modo": "real"})
    laudo = r.json()
    assert r.status_code == 200 and laudo["ok"] and laudo["renovacoes_token"] == 1, laudo
    assert "sim-rt-2" in api.cofre.ler("lastro:acme:oauth:contaazul")
    assert "sim-at" not in r.text and "sim-rt" not in r.text


def test_sem_autorizacao_o_teste_real_explica(cliente):
    _, c, entrar, _, _ = cliente
    r = c.post("/api/saas/contaazul/testar", headers=entrar("adm@acme"), json={"entidade": "vendas", "credenciais": {}, "modo": "real"})
    assert r.status_code == 409 and "autorizar" in r.json()["detail"]


def test_so_admin_inicia_e_state_adulterado_e_recusado(cliente):
    api, c, entrar, _, _ = cliente
    assert c.get("/api/saas/contaazul/oauth/iniciar", headers=entrar("ana@acme")).status_code == 403
    r = c.get("/oauth/retorno", params={"code": Simulador.CODIGO_SANDBOX, "state": "abc.def"})
    assert r.status_code == 400 and api.cofre.ler("lastro:acme:oauth:contaazul") is None
    r = c.get("/oauth/retorno", params={"error": "access_denied", "state": "x"})
    assert r.status_code == 400


def test_sandbox_roda_o_fluxo_inteiro_sem_token_no_formulario(cliente):
    _, c, entrar, _, _ = cliente
    for saas, ent in (("rdstation_crm", "negocios"), ("contaazul", "vendas"), ("google_drive", "planilhas")):
        r = c.post(f"/api/saas/{saas}/testar", headers=entrar("adm@acme"), json={"entidade": ent, "credenciais": {}, "modo": "sandbox"})
        laudo = r.json()
        assert laudo["ok"] and laudo["renovacoes_token"] == 1, (saas, laudo)
        assert "sim-at" not in r.text and "sim-rt" not in r.text


def test_formulario_nao_pede_token_para_oauth(cliente):
    _, c, entrar, _, _ = cliente
    cat = {x["id"]: x for x in c.get("/api/saas", headers=entrar("adm@acme")).json()}
    assert "token" not in cat["contaazul"]["campos"] and "token" in cat["hubspot"]["campos"]
