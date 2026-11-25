"""LST-15: o pipeline traduzido para BigQuery, Azure SQL e Athena dá o mesmo gold que o sandbox."""

from __future__ import annotations

import ast
import shutil

import duckdb
import pytest
import sqlglot

from lastro.banco import Repo, conectar, criar_tenant
from lastro.config import RAIZ, carregar
from lastro.servico import Plataforma
from lastro.trilhas import TRILHAS, ida_e_volta

EXEMPLO = RAIZ / "exemplos" / "orcamentos.csv"


@pytest.fixture(scope="module")
def demanda(tmp_path_factory, request):
    mp = pytest.MonkeyPatch()
    home = tmp_path_factory.mktemp("trilhas")
    mp.setenv("LASTRO_HOME", str(home))
    cfg = carregar()
    con = conectar(cfg.banco)
    criar_tenant(con, "acme", "Acme")
    fonte = cfg.pasta_tenant("acme") / "fontes" / "orcamentos.csv"
    fonte.parent.mkdir(parents=True)
    shutil.copy(EXEMPLO, fonte)
    repo = Repo(con, "acme")
    fid = repo.adicionar_fonte("orcamentos", "arquivo", str(fonte))
    plat = Plataforma(cfg, repo)
    d = plat.abrir("ana@acme", "Quanto cada vendedor vendeu, em valor vendido, nos contratos fechados?", [fid])
    d = plat.executar(plat.responder_grill(d["id"], "ana@acme", {"geral:revisor": "Rui"})["id"], "ana@acme")
    pasta = plat.pasta_demanda(d["id"])
    arvore = ast.parse((pasta / "pipeline.py").read_text())
    etapas = next(ast.literal_eval(n.value) for n in arvore.body if isinstance(n, ast.Assign) and n.targets[0].id == "ETAPAS")
    yield d["resultado"]["modelo"], etapas, pasta, fonte
    mp.undo()


def test_engenheiro_grava_um_script_por_trilha(demanda):
    modelo, etapas, pasta, _ = demanda
    for t in TRILHAS.values():
        texto = (pasta / "trilhas" / t.arquivo).read_text()
        assert texto.startswith(f"-- Pipeline gerado pelo Lastro · {t.nome}")
        assert modelo["filtro"] in texto.replace("`", "").replace('"', "").replace("[", "").replace("]", "")
        sqlglot.parse(texto, read=t.dialeto)  # o parser do próprio dialeto aceita o script inteiro


@pytest.mark.parametrize("trilha", list(TRILHAS))
def test_ida_e_volta_da_o_mesmo_gold(demanda, trilha):
    modelo, etapas, pasta, fonte = demanda
    con = duckdb.connect()
    con.execute(f"CREATE VIEW {modelo['view']} AS SELECT * FROM read_csv_auto('{fonte.as_posix()}', header=true)")
    for (nome, original), (_, traduzido) in zip(etapas, ida_e_volta(etapas, modelo, trilha)):
        con.execute(original)
        con.execute(traduzido)
        if nome == "bronze":  # tem o horário da carga: compara sem ele
            continue
        a = con.execute(f"SELECT * FROM {nome} EXCEPT ALL SELECT * FROM {nome}_ida").fetchall()
        b = con.execute(f"SELECT * FROM {nome}_ida EXCEPT ALL SELECT * FROM {nome}").fetchall()
        assert a == [] and b == [], f"{trilha}: {nome} mudou na tradução"
        assert con.execute(f"SELECT count(*) FROM {nome}").fetchone()[0] > 0
        con.execute(f"DROP TABLE {nome}_ida")
    # a conta que o demandante viu é a mesma em todas as nuvens
    total = con.execute(f"SELECT round(sum({modelo['medida']}), 2) FROM fato").fetchone()[0]
    assert total == pytest.approx(14030477.92, abs=0.01)


def test_dialetos_sem_construcoes_que_a_nuvem_recusa(demanda):
    _, _, pasta, _ = demanda
    bq = (pasta / "trilhas" / "pipeline_bigquery.sql").read_text()
    tsql = (pasta / "trilhas" / "pipeline_azure_sql.sql").read_text()
    athena = (pasta / "trilhas" / "pipeline_athena.sql").read_text()
    assert "QUALIFY" not in bq.upper() and "SAFE_CAST" in bq and "lastro_gold.fato" in bq
    assert " USING " not in tsql.upper() and "QUALIFY" not in tsql.upper() and "SELECT * INTO gold.fato" in tsql
    assert "CREATE OR REPLACE" not in athena.upper() and "external_location = 's3://<bucket>/gold/fato/'" in athena


def test_caixa_acha_o_playbook_de_cada_trilha():
    from lastro.caixa import Caixa
    from lastro.config import CAIXA_GLOBAL

    caixa = Caixa({"global": CAIXA_GLOBAL})
    topo = [x.caminho for x in caixa.buscar("bigquery sandbox looker studio camadas", k=2)]
    assert "global:playbooks/google-bigquery-looker.md" in topo  # ao lado da nota da trilha, que aponta para ele
    assert caixa.buscar("azure sql camada gratuita power bi vcore")[0].caminho == "global:playbooks/microsoft-azure-sql-power-bi.md"
    trecho = caixa.ler("global:playbooks/microsoft-azure-sql-power-bi.md", "Custo gratuito (conferido em 25/11/2026 em learn.microsoft.com)")
    assert "100 mil vCore-segundos" in trecho
