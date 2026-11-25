"""LST-5: embeddings locais na Caixa. Roda só com o extra `vetores` e o modelo já baixado."""

from __future__ import annotations

import shutil
from pathlib import Path

import pytest

from lastro.banco import Repo, conectar, criar_tenant
from lastro.config import RAIZ, carregar
from lastro.servico import Plataforma
from lastro import vetores

MODELOS = RAIZ / ".lastro" / "modelos"
pytest.importorskip("fastembed")
pytestmark = pytest.mark.skipif(not any(MODELOS.glob("**/*.onnx")), reason="modelo não baixado: rode uma vez com LASTRO_EMBEDDER=fastembed")


@pytest.fixture()
def plataforma(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    def montar(embedder: str) -> Plataforma:
        home = tmp_path / embedder
        home.mkdir()
        (home / "modelos").symlink_to(MODELOS)
        monkeypatch.setenv("LASTRO_HOME", str(home))
        monkeypatch.setenv("LASTRO_EMBEDDER", embedder)
        cfg = carregar()
        con = conectar(cfg.banco)
        criar_tenant(con, "acme", "Acme")
        repo = Repo(con, "acme")
        fonte = cfg.pasta_tenant("acme") / "fontes" / "orcamentos.csv"
        fonte.parent.mkdir(parents=True)
        shutil.copy(RAIZ / "exemplos" / "orcamentos.csv", fonte)
        fid = repo.adicionar_fonte("orcamentos", "arquivo", str(fonte))
        plat = Plataforma(cfg, repo)
        d = plat.abrir("ana@acme", "Quanto cada vendedor vendeu, em valor vendido, nos contratos fechados?", [fid])
        plat.responder_grill(d["id"], "ana@acme", {"orcamentos:medida": "valor_vendido", "orcamentos:filtro": "status = 'Fechado'"})
        return plat

    return montar


def test_faturamento_acha_a_decisao_sobre_valor_vendido_entre_as_3_primeiras(plataforma):
    plat = plataforma("fastembed")
    achados = plat.caixa().buscar("faturamento", k=3)
    assert any("medida" in t.caminho and "valor_vendido" in plat.caixa().ler(t.caminho, "Resposta") for t in achados), [t.caminho for t in achados]
    assert any("vetor" in t.fontes for t in achados)


def test_sem_embedder_a_busca_por_sinonimo_nao_acha_nada(plataforma):
    plat = plataforma("nenhum")
    assert plat.caixa().buscar("faturamento", k=3) == []


def test_vetores_ficam_em_cache_entre_reindexacoes(plataforma):
    plat = plataforma("fastembed")
    emb = vetores.obter(plat.cfg.home, "fastembed")
    plat.caixa()
    antes = emb.calculados
    plat.caixa().reindexar()
    assert emb.calculados == antes, "reindexar o mesmo acervo não deve recalcular vetores"


def test_medida_vai_para_o_historico_e_o_grill_pergunta_de_novo(plataforma):
    plat = plataforma("nenhum")
    hist = list((plat.pasta / "caixa" / "decisoes" / "historico").glob("*.md"))
    assert any("medida" in p.name for p in hist)
    fid = plat.repo.fontes()[0]["id"]
    d2 = plat.abrir("ana@acme", "Qual o valor orçado por estado?", [fid])
    assert {q["id"] for q in d2["grill"]} == {"orcamentos:medida", "orcamentos:filtro"}
