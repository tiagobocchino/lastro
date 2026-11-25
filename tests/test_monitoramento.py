"""LST-26: a API conta requisições e erros por hora sem nunca derrubar a resposta; o painel desenha os números."""

from __future__ import annotations

import importlib
from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

import pytest

from lastro.painel import renderizar

SP = ZoneInfo("America/Sao_Paulo")


@pytest.fixture
def api(monkeypatch, tmp_path):
    from fastapi.testclient import TestClient

    monkeypatch.setenv("LASTRO_HOME", str(tmp_path))
    import lastro.api as modulo

    modulo = importlib.reload(modulo)

    @modulo.app.get("/api/_quebra")
    def quebra() -> dict:
        raise RuntimeError("falha de teste")

    return modulo, TestClient(modulo.app, raise_server_exceptions=False)


def test_conta_requisicoes_4xx_e_5xx_por_hora(api):
    modulo, c = api
    c.get("/saude")
    c.get("/web/app.js")
    c.post("/api/login", json={"email": "ninguem@x", "senha": "errada"})  # 401
    c.get("/api/_quebra")  # 500
    c.get("/api/saas")  # 401 sem sessão
    (m,) = modulo.banco.metricas()
    assert (m["requisicoes"], m["erros_4xx"], m["erros_5xx"]) == (3, 2, 1)  # /saude e /web ficam de fora
    assert m["hora"] % 3600 == 0


def test_falha_ao_gravar_metrica_nao_derruba_a_resposta(api, monkeypatch):
    modulo, c = api

    def quebrado(*a, **k):
        raise OSError("disco cheio")

    monkeypatch.setattr(modulo.banco, "registrar_metrica", quebrado)
    r = c.post("/api/login", json={"email": "ninguem@x", "senha": "errada"})
    assert r.status_code == 401 and r.json()["detail"] == "e-mail ou senha inválidos"


def test_painel_desenha_os_numeros_e_escapa_texto():
    hoje = date(2026, 11, 25)
    dados = {
        "requisicoes": [{"dia": hoje, "requisicoes": 1200, "erros_4xx": 30, "erros_5xx": 12, "taxa_5xx": 0.01, "latencia_media_ms": 85.5}],
        "disponibilidade": [{"dia": hoje, "verificacoes": 288, "ok": 287, "disponibilidade_pct": 99.65}],
        "demandas": [{"dia": hoje - timedelta(days=1), "empresa": "lixum", "status": "aprovada", "demandas": 3}],
        "uso": [{"recurso": "banco", "usado_mb": 450.0, "limite_mb": 500}, {"recurso": "storage", "usado_mb": 12.5, "limite_mb": 1024}],
        "cargas": [{"empresa": "lixum", "saas": "bling", "entidade": "pedidos", "ultimo_status": "ok", "ultimo_aviso": "<script>x</script>",
                    "ultima_carga_boa": datetime(2026, 11, 25, 9, 0, tzinfo=SP)}],
        "alertas": [{"tipo": "banco_cheio", "detalhe": "banco com 450 MB de 500 MB", "aberto_em": datetime(2026, 11, 25, 8, tzinfo=SP), "fechado_em": None, "aberto": True}],
    }
    h = renderizar(dados, datetime(2026, 11, 25, 12, 0, tzinfo=SP))
    assert "1.200" in h and "99,65%" in h and "1,00%" in h and "86 ms" in h  # formato brasileiro
    assert "90,0% do plano gratuito" in h and "var(--erro)" in h  # banco acima de 80%: medidor vermelho
    assert "<script>x</script>" not in h and "&lt;script&gt;" in h
    assert h.count("<rect") >= 30 and "últimos 30 dias" in h
