"""LST-46: tabela pronta por demanda (fato + dimensões numa tabela só) no BI."""

import duckdb
import pandas as pd

from lastro.bi import tabelas_da_empresa
from lastro.config import carregar
from lastro.servico import Plataforma


def _aprovada(tmp_path, df, resp, pergunta="Quanto cada vendedor vendeu por mês?", monkeypatch=None):
    from lastro.banco import BancoSqlite

    monkeypatch.setenv("LASTRO_HOME", str(tmp_path))
    cfg = carregar()
    banco = BancoSqlite(cfg.banco)
    banco.criar_tenant("t", "Teste")
    plat = Plataforma(cfg, banco.repo("t", "ana@t", "admin"))
    arq = tmp_path / "vendas.csv"
    df.to_csv(arq, index=False)
    fid = plat.repo.adicionar_fonte("vendas", "arquivo", str(arq))
    d = plat.abrir("ana@t", pergunta, [fid])
    ids = {q["id"] for q in d["grill"]}
    d = plat.executar(plat.responder_grill(d["id"], "ana@t", {k: v for k, v in resp.items() if k in ids})["id"], "ana@t")
    d = plat.revisar(d["id"], "ana@t", True, "ok")
    return plat, d


def test_tabela_pronta_liga_fato_e_dimensoes_sem_mudar_o_total(tmp_path, monkeypatch):
    df = pd.DataFrame({"id": range(1, 7), "vendedor": ["Ana", "Bia", None, "Ana", "Bia", "Ana"],
                       "status": ["Aprovado"] * 6, "valor": [10.0, 20.0, 30.0, 40.0, 50.0, 60.5],
                       "data_venda": ["2026-01-05", "2026-01-20", "2026-02-01", "2026-02-10", "2026-03-03", None]})
    resp = {"vendas:medida": "valor", "vendas:data": "data_venda", "vendas:chave": "id", "geral:revisor": "t"}
    plat, d = _aprovada(tmp_path, df, resp, monkeypatch=monkeypatch)
    tabelas = {t.nome: t for t in tabelas_da_empresa(plat.repo, plat.pasta)}
    nome = next(n for n in tabelas if n.startswith(f"painel_{d['id']}_"))
    assert nome == f"painel_{d['id']}_quanto_cada_vendedor_vendeu_por_mes"
    con = duckdb.connect()
    rel = tabelas[nome].ler(con)
    cols = dict(zip(rel.columns, (str(t) for t in rel.types)))
    assert {"vendedor", "data", "ano", "mes", "ano_mes", "valor", "registros"} <= set(cols)
    assert not any(c.endswith("_id") and c != "id" for c in cols)  # sem chave técnica: nada para relacionar
    assert cols["data"] == "DATE"
    linhas = con.execute(f"SELECT count(*), sum(registros), round(sum(valor), 2) FROM ({rel.sql_query()})").fetchone()
    fato = con.execute(f"SELECT count(*), round(sum(valor), 2) FROM read_parquet('{plat.pasta_demanda(d['id']) / 'gold' / 'fato.parquet'}')").fetchone()
    assert linhas == (fato[0], fato[0], fato[1])
    # ADR 0011: vazio continua vazio (rótulo para o vazio é regra do cliente)
    assert con.execute(f"SELECT count(*) FROM ({rel.sql_query()}) WHERE vendedor IS NULL").fetchone()[0] == 1
    por_mes = dict(con.execute(f"SELECT ano_mes, sum(valor) FROM ({rel.sql_query()}) GROUP BY 1").fetchall())
    assert por_mes["2026-01"] == 30.0 and por_mes[None] == 60.5


def test_tabela_pronta_sem_medida_conta_por_registros(tmp_path, monkeypatch):
    df = pd.DataFrame({"id": range(1, 6), "setor": ["A", "A", "B", "B", "B"], "ativo": [True] * 5})
    plat, _ = _aprovada(tmp_path, df, {"vendas:chave": "id", "geral:revisor": "t"}, "Quantos funcionários por setor?", monkeypatch=monkeypatch)
    t = next(t for t in tabelas_da_empresa(plat.repo, plat.pasta) if t.nome.startswith("painel_"))
    con = duckdb.connect()
    rel = t.ler(con)
    assert dict(con.execute(f"SELECT setor, sum(registros) FROM ({rel.sql_query()}) GROUP BY 1").fetchall()) == {"A": 2, "B": 3}
