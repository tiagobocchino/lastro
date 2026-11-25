"""LST-33 no modo local (SQLite): exportação CSV/Parquet por fonte e o BI por SQL avisando que precisa do Postgres."""

from __future__ import annotations

import importlib

import duckdb
import pytest


@pytest.fixture
def api(monkeypatch, tmp_path):
    from fastapi.testclient import TestClient

    monkeypatch.setenv("LASTRO_HOME", str(tmp_path))
    monkeypatch.delenv("LASTRO_BANCO_URL", raising=False)
    import lastro.api as modulo

    modulo = importlib.reload(modulo)
    for t in ("acme", "outra"):
        modulo.banco.criar_tenant(t, t)
        modulo.banco.criar_usuario(t, f"adm@{t}", "Adm", "admin", "senha-longa-de-teste")
    modulo.banco.criar_usuario("acme", "leo@acme", "Leo", "leitor", "senha-longa-de-teste")
    c = TestClient(modulo.app)

    def cab(email: str) -> dict:
        tok = c.post("/api/login", json={"email": email, "senha": "senha-longa-de-teste"}).json()["token"]
        return {"Authorization": f"Bearer {tok}"}

    return modulo, c, cab


def test_exporta_fonte_em_csv_e_parquet(api, tmp_path):
    _, c, cab = api
    adm = cab("adm@acme")
    fid = c.post("/api/fontes", headers=adm, files={"arquivo": ("Vendas Março.csv", b"id,valor\n1,10.5\n2,20\n", "text/csv")}).json()["id"]
    r = c.get(f"/api/fontes/{fid}/exportar?formato=csv", headers=adm)
    assert r.status_code == 200 and r.text.splitlines() == ["id,valor", "1,10.5", "2,20.0"]
    assert r.headers["content-disposition"].startswith('attachment; filename="vendas_mar')
    r = c.get(f"/api/fontes/{fid}/exportar?formato=parquet", headers=adm)
    arq = tmp_path / "x.parquet"
    arq.write_bytes(r.content)
    assert duckdb.sql(f"SELECT sum(valor) FROM read_parquet('{arq}')").fetchall()[0][0] == 30.5
    assert c.get(f"/api/fontes/{fid}/exportar?formato=xlsx", headers=adm).status_code == 400
    assert c.get(f"/api/fontes/{fid}/exportar", headers=cab("leo@acme")).status_code == 403  # leitor não exporta
    assert c.get(f"/api/fontes/{fid}/exportar", headers=cab("adm@outra")).status_code == 404  # outra empresa não acha


def test_bi_por_sql_avisa_que_precisa_do_postgres(api):
    _, c, cab = api
    adm = cab("adm@acme")
    assert c.get("/api/bi", headers=adm).json() == {"disponivel": False, "motivo": "o BI pela conexão SQL só existe com o banco Postgres (produção)"}
    assert c.post("/api/bi/credencial", headers=adm).status_code == 409
    assert c.get("/api/bi", headers=cab("leo@acme")).status_code == 403
