"""LST-20: o container responde a verificação de saúde e não cria contas de demonstração em produção."""

from __future__ import annotations

import importlib

import pytest


@pytest.fixture
def api(monkeypatch, tmp_path):
    monkeypatch.setenv("LASTRO_HOME", str(tmp_path))
    import lastro.api as modulo

    return importlib.reload(modulo)


def test_saude_responde_versao_e_banco(api):
    from fastapi.testclient import TestClient

    r = TestClient(api.app).get("/saude")
    assert r.status_code == 200
    corpo = r.json()
    assert corpo["estado"] == "ok" and corpo["banco"] == "ok"
    assert corpo["versao"] == api.app.version


def test_saude_nao_exige_login_nem_expoe_segredo(api):
    from fastapi.testclient import TestClient

    texto = TestClient(api.app).get("/saude").text
    assert api.cfg.segredo not in texto and "home" not in texto


def test_serve_cria_demo_so_fora_de_producao(monkeypatch, tmp_path):
    from lastro import cli

    chamadas = []
    monkeypatch.setattr(cli, "preparar_demo", lambda: chamadas.append(1))
    monkeypatch.setattr("uvicorn.run", lambda *a, **k: chamadas.append(k["port"]))
    monkeypatch.setenv("LASTRO_HOME", str(tmp_path))
    monkeypatch.setenv("PORT", "9090")
    cli.main(["serve"])
    assert chamadas == [1, 9090]  # local: demo + porta vinda de $PORT

    chamadas.clear()
    monkeypatch.setenv("LASTRO_AMBIENTE", "producao")
    monkeypatch.setenv("LASTRO_SEGREDO", "x" * 40)
    cli.main(["serve"])
    assert chamadas == [9090]  # produção: sem contas de demonstração
