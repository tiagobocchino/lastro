"""Contas de teste em produção só durante a fase de testes (pedido do Tiago, 26/11; card de remoção no board)."""

from __future__ import annotations

import pytest

from lastro import cli
from lastro.banco import abrir_banco
from lastro.config import carregar


@pytest.fixture
def producao(monkeypatch, tmp_path):
    monkeypatch.setenv("LASTRO_HOME", str(tmp_path))
    monkeypatch.setenv("LASTRO_AMBIENTE", "producao")
    monkeypatch.setenv("LASTRO_SEGREDO", "x" * 40)
    monkeypatch.delenv("LASTRO_BANCO_URL", raising=False)
    monkeypatch.delenv("LASTRO_CONTAS_DEMO", raising=False)
    return monkeypatch


def _entra(email: str) -> bool:
    return abrir_banco(carregar()).autenticar(email, cli.DEMO_SENHA) is not None


def test_em_producao_so_com_a_variavel_e_desligar_tranca(producao):
    assert cli.contas_demo() == "trancadas" and not _entra("admin@demo.lastro")  # sem a variável: nada entra
    producao.setenv("LASTRO_CONTAS_DEMO", "1")
    assert cli.contas_demo() == "ligadas"
    assert all(_entra(e) for e, _, _ in cli.DEMO_USUARIOS)
    papeis = {e: abrir_banco(carregar()).autenticar(e, cli.DEMO_SENHA)["papel"] for e, _, _ in cli.DEMO_USUARIOS}
    assert papeis == {"ana@demo.lastro": "demandante", "rui@demo.lastro": "revisor", "admin@demo.lastro": "admin"}
    producao.delenv("LASTRO_CONTAS_DEMO")
    assert cli.contas_demo() == "trancadas"
    assert not any(_entra(e) for e, _, _ in cli.DEMO_USUARIOS)  # o fim da fase de testes é tirar a variável


def test_tela_de_login_em_producao_nao_mostra_as_contas_mesmo_ligadas(monkeypatch, tmp_path):
    from fastapi.testclient import TestClient

    monkeypatch.setenv("LASTRO_HOME", str(tmp_path))
    monkeypatch.delenv("LASTRO_BANCO_URL", raising=False)
    import lastro.api as modulo  # importado em modo local (produção exige o cofre do Supabase)

    monkeypatch.setenv("LASTRO_AMBIENTE", "producao")  # /api/config lê o ambiente a cada pedido
    monkeypatch.setenv("LASTRO_CONTAS_DEMO", "1")
    assert TestClient(modulo.app).get("/api/config").json() == {"contas_demo": False}
