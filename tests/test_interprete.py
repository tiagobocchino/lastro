"""LST-35: o Intérprete conversa sobre a demanda aprovada e devolve insights com prova (duas camadas)."""

from __future__ import annotations

import hashlib
import importlib
import shutil

import duckdb
import pytest

from lastro import paineis
from lastro.agents.interprete import InsightSemProva, Interprete, auditar, carregar_gold
from lastro.banco import BancoSqlite
from lastro.config import RAIZ, carregar
from lastro.servico import Plataforma

EXEMPLO = RAIZ / "exemplos" / "orcamentos.csv"
PERGUNTA = "Quanto cada vendedor vendeu, em valor vendido, nos contratos fechados?"


def _aprovada(cfg, banco, tenant: str):
    banco.criar_tenant(tenant, tenant)
    repo = banco.repo(tenant, f"adm@{tenant}", "admin")
    dest = cfg.pasta_tenant(tenant) / "fontes" / "orcamentos.csv"
    dest.parent.mkdir(parents=True)
    shutil.copy(EXEMPLO, dest)
    fid = repo.adicionar_fonte("orcamentos", "arquivo", str(dest))
    p = Plataforma(cfg, repo)
    d = p.abrir(f"adm@{tenant}", PERGUNTA, [fid])
    d = p.executar(p.responder_grill(d["id"], f"adm@{tenant}", {"geral:revisor": "Rui"})["id"], f"adm@{tenant}")
    return p, p.revisar(d["id"], f"adm@{tenant}", True, "ok")


@pytest.fixture(scope="module")
def cenario(tmp_path_factory):
    mp = pytest.MonkeyPatch()
    mp.setenv("LASTRO_HOME", str(tmp_path_factory.mktemp("home")))
    cfg = carregar()
    banco = BancoSqlite(cfg.banco)
    p, d = _aprovada(cfg, banco, "acme")
    yield p, d
    mp.undo()


def _resp(p, d, pergunta):
    ag = Interprete(d, p.pasta_demanda(d["id"]))
    try:
        return ag.responder(pergunta)
    finally:
        ag.fechar()


def test_quem_lidera_com_prova(cenario):
    p, d = cenario
    r = _resp(p, d, "Quem lidera em valor vendido por vendedor?")
    (ins,) = [i for i in r["insights"] if i["tipo"] == "maior"]
    assert ins["texto"].startswith("Eva Martins lidera") and "2.567.582,13" in ins["texto"] and "% do total" in ins["texto"]
    assert ins["sql"].startswith("WITH") and ins["linhas"][0][0] == "Eva Martins" and ins["camada1"] == "conferido"
    assert r["recusados"] == [] and r["reconhecida"]


def test_total_bate_com_o_relatorio_aprovado(cenario):
    p, d = cenario
    (ins,) = _resp(p, d, "Qual o total?")["insights"]
    assert "14.030.477,92" in ins["texto"] and "Bate com o total do relatório aprovado" in ins["texto"]


def test_categoria_citada_concentracao_e_tendencia(cenario):
    p, d = cenario
    r = _resp(p, d, "O valor está concentrado em poucos estados? E como evoluiu no último mês?")
    tipos = {i["tipo"]: i for i in r["insights"]}
    assert tipos["concentracao"]["eixo"] == "estado" and "Os 3 maiores em estado concentram" in tipos["concentracao"]["texto"]
    t = tipos["tendencia"]
    m1, v1, m0, v0, var = t["linhas"][0]
    assert m1 > m0 and round(100 * (v1 - v0) / v0, 1) == var  # a variação citada vem da própria consulta


def test_pergunta_aberta_vira_resumo_com_sugestoes(cenario):
    p, d = cenario
    r = _resp(p, d, "me conta algo interessante")
    assert not r["reconhecida"] and {i["tipo"] for i in r["insights"]} >= {"total", "maior", "concentracao"}
    assert any("lidera" in s for s in r["sugestoes"])


def test_le_a_definicao_do_painel(cenario):
    p, d = cenario
    pasta = p.pasta_demanda(d["id"])
    spec = paineis.inicial(d, pasta / "gold")
    cat = paineis.catalogo(pasta / "gold", d["resultado"]["modelo"])
    spec, _ = paineis.mudar(spec, {"op": "renomear", "id": spec["medidas"][0]["id"], "titulo": "Vendas fechadas"}, cat)
    spec["versao"] = 1
    paineis.gravar(pasta, spec)
    try:
        r = _resp(p, d, "Quem lidera?")
        assert r["base"] == "medida 'Vendas fechadas' do painel v1" and "vendas fechadas" in r["insights"][0]["texto"]
    finally:
        shutil.rmtree(paineis.pasta(pasta))


# ---- camada 1: insight sem prova é recusado ----------------------------------------------------

def test_insight_sem_prova_e_recusado(cenario):
    p, d = cenario
    pasta = p.pasta_demanda(d["id"])
    bom = next(i for i in _resp(p, d, "Quem lidera em valor vendido por vendedor?")["insights"] if i["tipo"] == "maior")
    auditar(bom, pasta)  # o original passa
    with pytest.raises(InsightSemProva, match="sem consulta"):
        auditar({**bom, "sql": None}, pasta)
    with pytest.raises(InsightSemProva, match="número sem prova: 9.999.999,00"):
        auditar({**bom, "texto": bom["texto"].replace("2.567.582,13", "9.999.999,00")}, pasta)
    with pytest.raises(InsightSemProva, match="não confere"):
        auditar({**bom, "linhas": [["Eva Martins", 9_999_999.0, 50.0]]}, pasta)
    with pytest.raises(InsightSemProva, match="não roda"):
        auditar({**bom, "sql": "DROP TABLE fato"}, pasta)


# ---- só leitura e isolamento ---------------------------------------------------------------------

def test_so_leitura_gold_intacto_e_sem_acesso_externo(cenario):
    p, d = cenario
    gold = p.pasta_demanda(d["id"]) / "gold"
    antes = {f.name: hashlib.sha256(f.read_bytes()).hexdigest() for f in gold.glob("*.parquet")}
    _resp(p, d, "me conta algo interessante")
    assert {f.name: hashlib.sha256(f.read_bytes()).hexdigest() for f in gold.glob("*.parquet")} == antes
    con = carregar_gold(p.pasta_demanda(d["id"]))
    with pytest.raises(duckdb.Error):  # conexão travada: nem arquivo de fora, nem mudar a configuração
        con.execute(f"SELECT * FROM read_csv('{EXEMPLO}')").fetchall()
    with pytest.raises(duckdb.Error):
        con.execute("SET enable_external_access = true")
    con.close()


def test_link_para_gold_de_outra_empresa_e_recusado(monkeypatch, tmp_path):
    monkeypatch.setenv("LASTRO_HOME", str(tmp_path))
    cfg = carregar()
    banco = BancoSqlite(cfg.banco)
    pa, da = _aprovada(cfg, banco, "acme")
    pb, db = _aprovada(cfg, banco, "outra")
    alvo = pa.pasta_demanda(da["id"]) / "gold" / "fato.parquet"
    (pb.pasta_demanda(db["id"]) / "gold" / "roubado.parquet").symlink_to(alvo)
    with pytest.raises(PermissionError, match="fora da pasta"):
        Interprete(db, pb.pasta_demanda(db["id"]))


# ---- API: conversa, camada 2 e outra empresa ------------------------------------------------------

def test_conversa_pelo_portal_com_revisor(monkeypatch, tmp_path):
    from fastapi.testclient import TestClient

    monkeypatch.setenv("LASTRO_HOME", str(tmp_path))
    monkeypatch.delenv("LASTRO_BANCO_URL", raising=False)
    import lastro.api as modulo

    modulo = importlib.reload(modulo)
    for t in ("acme", "outra"):
        modulo.banco.criar_tenant(t, t)
        for papel in ("admin", "demandante", "revisor", "leitor"):
            modulo.banco.criar_usuario(t, f"{papel}@{t}", papel, papel, "senha-longa-de-teste")
    c = TestClient(modulo.app)

    def cab(email):
        return {"Authorization": "Bearer " + c.post("/api/login", json={"email": email, "senha": "senha-longa-de-teste"}).json()["token"]}

    adm, dem, rev, lei = (cab(f"{x}@acme") for x in ("admin", "demandante", "revisor", "leitor"))
    fid = c.post("/api/fontes", headers=adm, files={"arquivo": ("orcamentos.csv", EXEMPLO.read_bytes(), "text/csv")}).json()["id"]
    did = c.post("/api/demandas", headers=dem, json={"pergunta": PERGUNTA, "fontes": [fid]}).json()["id"]
    c.post(f"/api/demandas/{did}/grill", headers=dem, json={"geral:revisor": "Rui"})
    c.post(f"/api/demandas/{did}/executar", headers=dem)
    assert c.post(f"/api/demandas/{did}/conversa", headers=dem, json={"pergunta": "quem lidera?"}).status_code == 409
    c.post(f"/api/demandas/{did}/revisao", headers=rev, json={"aprovado": True, "parecer": "ok"})
    t = c.post(f"/api/demandas/{did}/conversa", headers=lei, json={"pergunta": "Quem lidera em valor vendido por vendedor?"}).json()
    assert t["n"] == 1 and t["camada2"] == "aguardando revisor" and t["insights"][0]["camada1"] == "conferido"
    assert c.post(f"/api/demandas/{did}/conversa/1/revisao", headers=dem, json={"aprovado": True}).status_code == 403
    r = c.post(f"/api/demandas/{did}/conversa/1/revisao", headers=rev, json={"aprovado": True, "parecer": "confere com o painel"}).json()
    assert r["camada2"] == "aprovado" and r["revisao"]["revisor"] == "revisor@acme"
    assert c.get(f"/api/demandas/{did}/conversa", headers=dem).json()[0]["camada2"] == "aprovado"
    acoes = [e["acao"] for e in c.get(f"/api/demandas/{did}", headers=dem).json()["eventos"]]
    assert "interpretou" in acoes and "revisou_insights" in acoes
    intruso = cab("admin@outra")
    assert c.get(f"/api/demandas/{did}/conversa", headers=intruso).status_code == 404
    assert c.post(f"/api/demandas/{did}/conversa", headers=intruso, json={"pergunta": "total"}).status_code == 404
    assert c.post(f"/api/demandas/{did}/conversa/1/revisao", headers=cab("revisor@outra"), json={"aprovado": False}).status_code == 404
