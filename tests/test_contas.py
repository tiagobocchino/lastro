"""LST-32: troca da própria senha, senha provisória do convite e isolamento entre empresas."""

from __future__ import annotations

import importlib

import pytest


@pytest.fixture
def api(monkeypatch, tmp_path):
    from fastapi.testclient import TestClient

    monkeypatch.setenv("LASTRO_HOME", str(tmp_path))
    import lastro.api as modulo

    modulo = importlib.reload(modulo)
    for t in ("acme", "outra"):
        modulo.banco.criar_tenant(t, t)
        modulo.banco.criar_usuario(t, f"adm@{t}", "Adm", "admin", "senha-inicial-forte")
    modulo.banco.criar_usuario("acme", "ana@acme", "Ana", "demandante", "senha-da-ana-forte")
    c = TestClient(modulo.app)

    def entrar(email: str, senha: str) -> dict:
        r = c.post("/api/login", json={"email": email, "senha": senha})
        return r.json() | {"status": r.status_code}

    def cab(token: str) -> dict:
        return {"Authorization": f"Bearer {token}"}

    return modulo, c, entrar, cab


def test_troca_a_propria_senha(api):
    _, c, entrar, cab = api
    tok = entrar("ana@acme", "senha-da-ana-forte")["token"]
    r = c.post("/api/conta/senha", headers=cab(tok), json={"atual": "senha-da-ana-forte", "nova": "outra-senha-bem-longa"})
    assert r.status_code == 200
    assert entrar("ana@acme", "senha-da-ana-forte")["status"] == 401
    assert entrar("ana@acme", "outra-senha-bem-longa")["status"] == 200


@pytest.mark.parametrize(("atual", "nova", "codigo"), [
    ("senha-errada-qualquer", "nova-senha-bem-longa", 403),
    ("senha-da-ana-forte", "curta", 400),
    ("senha-da-ana-forte", "senha-da-ana-forte", 400),
])
def test_troca_recusada(api, atual, nova, codigo):
    _, c, entrar, cab = api
    tok = entrar("ana@acme", "senha-da-ana-forte")["token"]
    r = c.post("/api/conta/senha", headers=cab(tok), json={"atual": atual, "nova": nova})
    assert r.status_code == codigo
    assert entrar("ana@acme", "senha-da-ana-forte")["status"] == 200  # nada mudou


def test_convite_com_senha_provisoria_obriga_a_troca(api):
    modulo, c, entrar, cab = api
    adm = entrar("adm@acme", "senha-inicial-forte")["token"]
    r = c.post("/api/usuarios", headers=cab(adm), json={"email": "Rui@Acme", "nome": "Rui", "papel": "revisor"})
    assert r.status_code == 200
    prov = r.json()["senha_provisoria"]
    assert len(prov) >= 12 and r.json()["email"] == "rui@acme"
    login = entrar("rui@acme", prov)
    assert login["status"] == 200 and login["trocar_senha"] is True
    # com senha provisória, só a troca e o /api/eu funcionam
    assert c.get("/api/demandas", headers=cab(login["token"])).status_code == 403
    assert c.get("/api/eu", headers=cab(login["token"])).json()["trocar_senha"] is True
    novo = c.post("/api/conta/senha", headers=cab(login["token"]), json={"atual": prov, "nova": "senha-definitiva-do-rui"}).json()["token"]
    assert c.get("/api/demandas", headers=cab(novo)).status_code == 200
    assert entrar("rui@acme", "senha-definitiva-do-rui")["trocar_senha"] is False
    # a senha provisória nunca vai para o banco nem para o rastro
    bruto = (modulo.cfg.home / "lastro.db").read_bytes()
    assert prov.encode() not in bruto and b"senha-definitiva-do-rui" not in bruto
    lista = c.get("/api/usuarios", headers=cab(adm)).json()
    assert {u["email"] for u in lista} == {"adm@acme", "ana@acme", "rui@acme"} and "senha_hash" not in str(lista)


def test_admin_redefine_senha_de_quem_esqueceu(api):
    _, c, entrar, cab = api
    adm = entrar("adm@acme", "senha-inicial-forte")["token"]
    prov = c.post("/api/usuarios", headers=cab(adm), json={"email": "ana@acme", "nome": "Ana", "papel": "demandante"}).json()["senha_provisoria"]
    assert entrar("ana@acme", "senha-da-ana-forte")["status"] == 401
    assert entrar("ana@acme", prov)["trocar_senha"] is True


def test_outra_empresa_nao_toma_nem_ve_usuario(api):
    modulo, c, entrar, cab = api
    intruso = entrar("adm@outra", "senha-inicial-forte")["token"]
    r = c.post("/api/usuarios", headers=cab(intruso), json={"email": "ana@acme", "nome": "Ana", "papel": "admin"})
    assert r.status_code == 409 and "acme" not in r.text  # não revela de qual empresa é
    assert entrar("ana@acme", "senha-da-ana-forte")["status"] == 200  # a conta da Ana segue intacta
    assert {u["email"] for u in c.get("/api/usuarios", headers=cab(intruso)).json()} == {"adm@outra"}
    with pytest.raises(PermissionError):  # nem o comando da demo move um e-mail entre empresas
        modulo.banco.criar_usuario("outra", "ana@acme", "Ana", "admin", "qualquer-senha-longa")


def test_so_admin_convida(api):
    _, c, entrar, cab = api
    ana = entrar("ana@acme", "senha-da-ana-forte")["token"]
    assert c.post("/api/usuarios", headers=cab(ana), json={"email": "x@acme", "nome": "X"}).status_code == 403
    assert c.get("/api/usuarios", headers=cab(ana)).status_code == 403
