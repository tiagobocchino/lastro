"""LST-17: falhas achadas na revisão antes da nuvem."""

from __future__ import annotations

import pytest

from lastro.somente_leitura import EscritaBloqueada, verificar


@pytest.mark.parametrize("sql", [
    "SELECT 1 FROM v WHERE 1=1 OR (SELECT count(*) FROM read_text('/etc/passwd'))>0",
    "SELECT * FROM '/home/outra_empresa/fontes/x.csv'",
    "SELECT * FROM v JOIN 'x.parquet' USING (id)",
    "SELECT getenv('LASTRO_SEGREDO')",
    "SELECT * FROM read_csv_auto('/tmp/a.csv')",
    "SELECT * FROM glob('/home/*')",
    "SELECT * FROM read_parquet('s3://bucket/x')",
    "SELECT current_setting('home_directory')",
])
def test_trava_recusa_leitura_de_arquivo_e_ambiente(sql):
    with pytest.raises(EscritaBloqueada):
        verificar(sql)


def test_trava_continua_aceitando_consultas_normais():
    for sql in ["SELECT status, sum(valor) FROM fato GROUP BY 1", "SELECT 'texto com read_csv dentro' AS x", "status = 'Fechado'"]:
        verificar(sql if sql.startswith("SELECT") else f"SELECT 1 FROM v WHERE {sql}")


def test_variavel_de_host_maliciosa_nao_monta_url():
    from lastro.saas.motor import Credencial, Leitor

    with pytest.raises(ValueError, match="subdominio"):
        Leitor("kommo", {"token": "x"}, {"subdominio": "atacante.com/x?"})
    l = Leitor("google_sheets", {"token": "x"}, {"planilha_id": "abc", "aba": "Vendas 2026/../x"})
    assert l._url("/values/{aba}").endswith("/values/Vendas%202026%2F..%2Fx")
    assert l._url("/values/{aba}").startswith("https://sheets.googleapis.com/")
    _ = Credencial


def test_producao_sem_segredo_forte_nao_sobe(monkeypatch, tmp_path):
    from lastro.config import carregar

    monkeypatch.setenv("LASTRO_HOME", str(tmp_path))
    monkeypatch.setenv("LASTRO_AMBIENTE", "producao")
    monkeypatch.delenv("LASTRO_SEGREDO", raising=False)
    with pytest.raises(RuntimeError, match="LASTRO_SEGREDO"):
        carregar()
    monkeypatch.setenv("LASTRO_SEGREDO", "curto")
    with pytest.raises(RuntimeError):
        carregar()
    monkeypatch.setenv("LASTRO_SEGREDO", "x" * 40)
    assert carregar().segredo == "x" * 40


def test_upload_acima_do_limite_volta_413(monkeypatch, tmp_path):
    import importlib

    monkeypatch.setenv("LASTRO_HOME", str(tmp_path))
    monkeypatch.setenv("LASTRO_UPLOAD_MAX_MB", "1")
    import lastro.api as api
    from fastapi.testclient import TestClient

    importlib.reload(api)
    api.banco.criar_tenant("acme", "Acme")
    api.banco.criar_usuario("acme", "adm@acme", "Adm", "admin", "senha123")
    c = TestClient(api.app)
    tok = c.post("/api/login", json={"email": "adm@acme", "senha": "senha123"}).json()["token"]
    grande = b"a,b\n" + b"1,2\n" * 400_000  # ~1,6 MB
    r = c.post("/api/fontes", headers={"Authorization": f"Bearer {tok}"}, files={"arquivo": ("x.csv", grande, "text/csv")})
    assert r.status_code == 413
    ok = c.post("/api/fontes", headers={"Authorization": f"Bearer {tok}"}, files={"arquivo": ("y.csv", b"a,b\n1,2\n", "text/csv")})
    assert ok.status_code == 200
