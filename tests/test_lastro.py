"""Testes de comportamento: Caixa, trava de leitura, política, isolamento de tenant e o ciclo completo."""

from __future__ import annotations

import shutil
from pathlib import Path

import pytest

from lastro.banco import Repo, conectar, criar_tenant, emitir_token, hash_senha, confere_senha, ler_token
from lastro.caixa import Caixa, gravar_nota, rrf
from lastro.config import CAIXA_GLOBAL, RAIZ, carregar
from lastro.politica import PermissaoNegada, Politica
from lastro.servico import Plataforma
from lastro.somente_leitura import EscritaBloqueada, verificar

EXEMPLO = RAIZ / "exemplos" / "orcamentos.csv"


# --- Caixa de Ferramenta -------------------------------------------------------------

def test_caixa_global_acha_playbook_por_busca():
    caixa = Caixa({"global": CAIXA_GLOBAL})
    achados = caixa.buscar("como ligar o power bi no athena da aws", k=3)
    assert "global:playbooks/medalhao-aws-athena-power-bi.md" in [t.caminho for t in achados]
    especifica = caixa.buscar("arquitetura data lake com camadas bronze silver gold no s3 e glue")
    assert especifica[0].caminho == "global:playbooks/medalhao-aws-athena-power-bi.md"
    assert caixa.buscar("crawler INVALID_VIEW")[0].caminho == "global:erros/athena-invalid-view-crawler.md"


def test_indice_tem_uma_linha_por_nota_e_ler_devolve_so_a_secao():
    caixa = Caixa({"global": CAIXA_GLOBAL})
    assert len(caixa.indice().splitlines()) == len(caixa.notas)
    trecho = caixa.ler("global:metodos/auditoria-em-duas-camadas.md", "Camada 2: negócio")
    assert trecho.startswith("## Camada 2") and "Camada 1" not in trecho


def test_tenant_tem_prioridade_sobre_global(tmp_path: Path):
    gravar_nota(tmp_path, "glossario venda", "O que conta como venda na empresa", "glossario", "# Definição\n\nVenda é contrato com status Fechado e power bi.")
    caixa = Caixa({"global": CAIXA_GLOBAL, "tenant": tmp_path})
    assert caixa.buscar("o que conta como venda")[0].escopo == "tenant"


def test_rrf_soma_posicoes_de_listas():
    p = rrf([["a", "b"], ["b", "c"]])
    assert p["b"] > p["a"] > p["c"]


def test_busca_ignora_operadores_fts_do_usuario():
    caixa = Caixa({"global": CAIXA_GLOBAL})
    caixa.buscar('athena" OR * NEAR(')  # não pode levantar erro de sintaxe FTS


# --- Somente leitura e política -----------------------------------------------------

@pytest.mark.parametrize("sql", ["SELECT 1", "with x as (select 1) select * from x", "DESCRIBE fato", "select 'drop table' as texto"])
def test_leitura_passa(sql):
    assert verificar(sql) == sql


@pytest.mark.parametrize(
    "sql",
    ["DROP TABLE fato", "select 1; delete from fato", "INSERT INTO x VALUES (1)", "COPY fato TO 'x.csv'", "ATTACH 'x.db'", "update t set a=1", "/* */ create table x(a int)"],
)
def test_escrita_bloqueada(sql):
    with pytest.raises(EscritaBloqueada):
        verificar(sql)


def test_politica_comeca_fechada_e_respeita_plano():
    pol = Politica(plano="consulta", agentes={"engenheiro": {"sandbox_temporario", "agendar_pipeline"}})
    assert pol.pode("explorador", "ler_fontes")
    assert not pol.pode("explorador", "sandbox_temporario")
    assert pol.pode("engenheiro", "sandbox_temporario")
    with pytest.raises(PermissaoNegada):
        pol.exigir("engenheiro", "agendar_pipeline")  # liberado ao agente, mas o plano Consulta não permite
    assert not pol.pode("analista", "pesquisar_fora")


# --- Login e isolamento --------------------------------------------------------------

def test_senha_e_token():
    h = hash_senha("segredo")
    assert confere_senha("segredo", h) and not confere_senha("outra", h)
    t = emitir_token("k", "a@b", "t1", "admin")
    assert ler_token("k", t)["t"] == "t1"
    assert ler_token("outra-chave", t) is None


@pytest.fixture()
def ambiente(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("LASTRO_HOME", str(tmp_path / "home"))
    monkeypatch.setenv("LASTRO_LLM", "nenhum")
    cfg = carregar()
    con = conectar(cfg.banco)
    for t in ("acme", "outra"):
        criar_tenant(con, t, t.title())
    fonte = cfg.pasta_tenant("acme") / "fontes" / "orcamentos.csv"
    fonte.parent.mkdir(parents=True)
    shutil.copy(EXEMPLO, fonte)
    repo = Repo(con, "acme")
    fid = repo.adicionar_fonte("orcamentos", "arquivo", str(fonte))
    return cfg, con, repo, fid, fonte


def test_tenant_nao_ve_nem_usa_fonte_de_outro(ambiente):
    cfg, con, repo, fid, _ = ambiente
    outra = Repo(con, "outra")
    assert outra.fontes() == []
    with pytest.raises(PermissionError):
        outra.criar_demanda("x@outra", "pergunta", [fid])


# --- Ciclo completo -----------------------------------------------------------------

def test_ciclo_completo_grill_execucao_auditoria_revisao(ambiente):
    cfg, con, repo, fid, fonte = ambiente
    original = fonte.read_bytes()
    plat = Plataforma(cfg, repo)

    d = plat.abrir("ana@acme", "Quanto cada vendedor vendeu, em valor vendido, nos contratos fechados?", [fid])
    assert d["status"] == "grill"
    ids = {q["id"] for q in d["grill"]}
    assert {"orcamentos:medida", "orcamentos:chave", "orcamentos:filtro", "geral:revisor"} <= ids
    medida = next(q for q in d["grill"] if q["id"] == "orcamentos:medida")
    assert medida["sugestao"] == "valor_vendido"  # a pergunta cita "valor vendido"
    chave = next(q for q in d["grill"] if q["id"] == "orcamentos:chave")
    assert chave["sugestao"] == "contrato_id" and "12 valores repetidos" in chave["pergunta"]

    d = plat.responder_grill(d["id"], "ana@acme", {"orcamentos:filtro": "status = 'Fechado'", "geral:revisor": "Rui"})
    d = plat.executar(d["id"], "ana@acme")
    assert d["status"] == "em_revisao"
    r, a = d["resultado"]["resposta"], d["resultado"]["auditoria"]
    assert r["colunas"][0] == "vendedor" and len(r["linhas"]) == 7
    assert a["aprovado_camada1"]
    nomes = {c["checagem"]: c for c in a["checagens"]}
    assert nomes["duplicidade na chave"]["ok"]
    assert not nomes["duplicidade na fonte"]["ok"]  # a armadilha do exemplo foi vista
    assert nomes["resposta: total recalculado"]["ok"]

    pasta = plat.pasta_demanda(d["id"])
    for arq in ("relatorio.html", "auditoria_colab.ipynb", "pipeline.py", "gold/fato.parquet"):
        assert (pasta / arq).exists(), arq
    assert fonte.read_bytes() == original  # a fonte primária não foi tocada

    d = plat.revisar(d["id"], "rui@acme", False, "Faltou separar por empresa; 61 no gráfico, 69 no indicador.")
    assert d["status"] == "reprovada"
    assert (plat.pasta / "caixa" / "aprendizados").exists()

    # Segunda demanda: data, chave e revisor já foram decididos e não voltam ao grill.
    d2 = plat.abrir("ana@acme", "Como evoluiu o valor orçado por mês em cada segmento?", [fid])
    ids2 = {q["id"] for q in d2["grill"]}
    assert ids2 == {"orcamentos:medida", "orcamentos:filtro"}
    assert next(q for q in d2["grill"] if q["id"] == "orcamentos:medida")["sugestao"] == "valor_orcado"
    d2 = plat.responder_grill(d2["id"], "ana@acme", {})
    d2 = plat.executar(d2["id"], "ana@acme")
    assert d2["resultado"]["resposta"]["colunas"][:2] == ["segmento", "ano_mes"]
    # o aprendizado da reprovação é achável pela busca do tenant
    assert any(t.caminho.startswith("tenant:aprendizados") for t in plat.caixa().buscar("separar por empresa"))


def test_executar_fora_de_ordem_falha(ambiente):
    cfg, con, repo, fid, _ = ambiente
    plat = Plataforma(cfg, repo)
    d = plat.abrir("ana@acme", "Total orçado", [fid])
    with pytest.raises(ValueError):
        plat.executar(d["id"], "ana@acme")
