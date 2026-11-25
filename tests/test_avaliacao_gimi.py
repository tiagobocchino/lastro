"""LST-36: os agentes contra o gabarito da base GIMI simulada, em volume pequeno."""

from lastro.simulados import avaliacao


def test_agentes_batem_com_o_gabarito(tmp_path, monkeypatch):
    monkeypatch.setenv("LASTRO_HOME", str(tmp_path))
    r = avaliacao.avaliar(tmp_path, contratos_por_empresa=150, semente=7)
    falhas = [c for c in r["checagens"] if not c["ok"]]
    assert not falhas, falhas
    assert len(r["checagens"]) == 8
    assert "| D4" in avaliacao.relatorio_md(r)
