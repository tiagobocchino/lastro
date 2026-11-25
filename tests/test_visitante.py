"""LST-38 / ADR 0010: o modo visitante roda os mesmos agentes sem deixar nada fora da pasta da sessão."""

from __future__ import annotations

import shutil
import tempfile
from dataclasses import replace
from pathlib import Path

import httpx
import pytest

from lastro import paineis
from lastro.config import CAIXA_GLOBAL, RAIZ, carregar
from lastro.memoria import RepoMemoria
from lastro.servico import Plataforma

EXEMPLO = RAIZ / "exemplos" / "orcamentos.csv"


def _foto(pasta: Path) -> dict[str, tuple[int, int]]:
    return {str(p): (p.stat().st_size, p.stat().st_mtime_ns) for p in pasta.rglob("*") if p.is_file()} if pasta.exists() else {}


def _sandboxes() -> set[str]:
    return {p.name for p in Path(tempfile.gettempdir()).glob("lastro-sandbox-*")}


@pytest.fixture
def cenario(monkeypatch, tmp_path):
    monkeypatch.setenv("LASTRO_HOME", str(tmp_path / "home"))
    # produção poderia ter LLM e embedder ligados: o modo visitante tem que desligar os dois
    cfg = replace(carregar(), llm_provedor="groq", llm_modelo="qualquer", llm_url="https://api.exemplo/v1", llm_chave="x", embedder="fastembed")

    def proibido(*a, **k):
        raise AssertionError("o modo visitante fez uma chamada HTTP de saída")

    monkeypatch.setattr(httpx.Client, "send", proibido)
    monkeypatch.setattr(httpx, "post", proibido)

    from lastro import espelho

    monkeypatch.setattr(espelho.EspelhoStorage, "sincronizar", proibido)
    monkeypatch.setattr(espelho.EspelhoStorage, "restaurar", proibido)
    return cfg, tmp_path / "sessao-abc123"


def test_analise_completa_sem_rastro_fora_da_sessao(cenario):
    cfg, sessao = cenario
    caixa_antes, home_antes, sandboxes_antes = _foto(CAIXA_GLOBAL), _foto(cfg.home), _sandboxes()

    plat = Plataforma.visitante(cfg, sessao)
    assert plat.modo == "demonstracao" and not plat.llm.ativo and plat.caixa().embedder is None and plat.espelho is None
    destino = plat.pasta / "fontes" / "planilha.csv"
    destino.parent.mkdir(parents=True)
    shutil.copy(EXEMPLO, destino)
    fid = plat.repo.adicionar_fonte("planilha", "arquivo", str(destino))
    d = plat.abrir("visitante", "Quanto cada vendedor vendeu, em valor vendido, nos contratos fechados?", [fid])
    d = plat.executar(plat.responder_grill(d["id"], "visitante", {})["id"], "visitante")
    assert d["resultado"]["modo"] == "demonstracao" and d["resultado"]["auditoria"]["aprovado_camada1"]
    assert d["resultado"]["resposta"]["total"] == pytest.approx(14030477.92, abs=0.01)
    with pytest.raises(PermissionError, match="ADR 0010"):
        plat.revisar(d["id"], "alguem", True, "ok")
    # o painel sai do gold mesmo sem aprovação humana (a demonstração não tem a segunda camada)
    gold = plat.pasta_demanda(d["id"]) / "gold"
    assert "14.030.477,92" in paineis.html_painel(paineis.inicial(d, gold), gold, "agora")

    # tudo o que a análise gravou está dentro da sessão: notas, decisões do grill, gold, relatório
    gravados = [p for p in sessao.rglob("*") if p.is_file()]
    assert any("caixa" in p.parts for p in gravados) and any(p.name == "fato.parquet" for p in gravados)
    assert _foto(CAIXA_GLOBAL) == caixa_antes  # a Caixa global não mudou
    assert _foto(cfg.home) == home_antes  # LASTRO_HOME intocado: sem banco, sem vetores, sem pasta de empresa
    assert _sandboxes() == sandboxes_antes  # o DuckDB temporário do sandbox também foi embora

    # apagar a sessão apaga tudo; o repo em memória esquece demandas, fontes e rastro
    assert plat.repo.apagar() > 0 and plat.repo.demandas() == []
    shutil.rmtree(sessao)
    assert not sessao.exists()


def test_produto_continua_igual(cenario):
    cfg, _ = cenario
    plat = Plataforma(replace(cfg, llm_provedor="nenhum", embedder="nenhum"), RepoMemoria("acme"))
    assert plat.modo == "produto"
