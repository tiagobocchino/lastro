"""LST-54: relatórios Python rápidos com agente LangChain (LLM falsa no teste; nenhum dado vai para a LLM)."""

import io

import pandas as pd
import pytest

from lastro.rapido import nucleo as n


def _parquet(df: pd.DataFrame) -> bytes:
    buf = io.BytesIO()
    df.to_parquet(buf, index=False)
    return buf.getvalue()


@pytest.fixture
def con():
    vendas = pd.DataFrame({"id": range(1, 7), "company": ["gimi", "gbl"] * 3, "vendedor_nome": ["Ana", "Bia", "Ana", "Caio", "Bia", "Ana"],
                           "cliente_nome": ["X", "Y", "Z", "X", "Y", "Z"], "projeto_regiao": ["Sul", "Sudeste", "Sul", None, "Norte", "Sul"],
                           "projeto_estado": ["PR", "SP", "SC", None, "PA", "PR"], "ano_mes": ["2026-01", "2026-01", "2026-02", "2026-02", "2026-03", "2026-03"],
                           "valores_produtos": [100.0, 200.0, 50.0, 25.0, 10.0, 5.5], "registros": [1] * 6})
    rh = pd.DataFrame({"id": range(1, 5), "company": ["gimi"] * 4, "setor_nome": ["A", "A", "B", "B"], "cargo_nome": ["x", "y", "x", "z"],
                       "ano_mes": ["2025-01"] * 4, "registros": [1] * 4})
    return n.carregar({"painel_15_quanto_cada_vendedor_vendeu": _parquet(vendas), "painel_18_quantos_funcionarios_ativos": _parquet(rh)})


def test_catalogo_so_tem_dimensoes_de_demonstracao(con):
    cat = n.catalogo(con)
    v = cat["painel_15_quanto_cada_vendedor_vendeu"]
    assert v["assunto"] == "Vendas" and v["medidas"] == ["valores_produtos"]
    assert set(v["dimensoes"]) == {"company", "projeto_regiao", "projeto_estado", "ano_mes"}  # sem vendedor nem cliente
    assert cat["painel_18_quantos_funcionarios_ativos"]["dimensoes"] == ["setor_nome"]  # empresa e mês com um valor só saem


def test_plano_valida_e_sql_bate_com_os_dados(con):
    cat = n.catalogo(con)
    p = n.validar(n.Plano(tabela="painel_15_quanto_cada_vendedor_vendeu", medida="valores_produtos", dimensao="projeto_regiao"), cat)
    assert p.titulo == "Soma de valor de produtos por região da obra"
    cols, linhas = n.executar(con, p)
    assert cols == ["projeto_regiao", "valor"] and dict(linhas) == {"Sul": 155.5, "Sudeste": 200.0, "Norte": 10.0, None: 25.0}
    p = n.validar(n.Plano(tabela="painel_15_quanto_cada_vendedor_vendeu", medida="valores_produtos", por_mes=True, grafico="linha"), cat)
    assert n.executar(con, p)[1] == [("2026-01", 300.0), ("2026-02", 75.0), ("2026-03", 15.5)]


def test_detalhe_alem_da_demonstracao_e_injecao_sao_recusados(con):
    cat = n.catalogo(con)
    with pytest.raises(n.PlanoInvalido, match="detalha demais"):
        n.validar(n.Plano(tabela="painel_15_quanto_cada_vendedor_vendeu", medida="valores_produtos", dimensao="vendedor_nome"), cat)
    with pytest.raises(n.PlanoInvalido, match="não é um valor"):
        n.validar(n.Plano(tabela="painel_15_quanto_cada_vendedor_vendeu", medida="valores_produtos; drop table x"), cat)
    with pytest.raises(n.PlanoInvalido, match="não conheço"):
        n.validar(n.Plano(tabela="usuarios"), cat)
    p = n.validar(n.Plano(tabela="painel_15_quanto_cada_vendedor_vendeu", medida="valores_produtos", filtro_coluna="company",
                          filtro_valor="gimi' OR '1'='1"), cat)
    assert n.executar(con, p)[1] == [(None,)]  # o valor vai como parâmetro: nada casa, nada vaza


def test_rh_sem_valor_vira_contagem(con):
    cat = n.catalogo(con)
    p = n.validar(n.Plano(tabela="painel_18_quantos_funcionarios_ativos", medida="salario", dimensao="setor_nome"), cat)
    assert p.agregacao == "contagem" and dict(n.executar(con, p)[1]) == {"A": 2, "B": 2} and p.avisos


def test_interpretacao_simples_sem_llm(con):
    cat = n.catalogo(con)
    p = n.interpretar_simples("Quanto vendemos por região ao longo dos meses?", cat)
    assert (p.tabela, p.dimensao, p.por_mes, p.grafico) == ("painel_15_quanto_cada_vendedor_vendeu", "projeto_regiao", True, "linha")
    p = n.interpretar_simples("Quantos funcionários por setor?", cat)
    assert (p.tabela, p.agregacao, p.dimensao) == ("painel_18_quantos_funcionarios_ativos", "contagem", "setor_nome")


def test_agente_langchain_recebe_so_pergunta_e_catalogo(con):
    from langchain_core.language_models.fake_chat_models import FakeListChatModel

    visto: list[str] = []

    class Espiao(FakeListChatModel):
        def _call(self, messages, *a, **k):
            visto.append("\n".join(str(m.content) for m in messages))
            return super()._call(messages, *a, **k)

    cat = n.catalogo(con)
    resposta = ('Aqui está: {"tabela": "painel_15_quanto_cada_vendedor_vendeu", "agregacao": "soma", "medida": "valores_produtos", '
                '"dimensao": "projeto_estado", "por_mes": false, "grafico": "barras", "titulo": "Vendas por UF"}')
    p = n.interpretar_llm("vendas por estado", cat, Espiao(responses=[resposta]))
    assert (p.dimensao, p.titulo) == ("projeto_estado", "Vendas por UF")
    enviado = visto[-1]
    assert "vendas por estado" in enviado and "projeto_estado" in enviado
    for dado in ("Ana", "200.0", "PR", "gimi", "155.5"):  # nenhum valor das tabelas chega ao modelo
        assert dado not in enviado
    ruim = '{"tabela": "painel_15_quanto_cada_vendedor_vendeu", "medida": "valores_produtos", "dimensao": "cliente_nome"}'
    with pytest.raises(n.PlanoInvalido):
        n.interpretar_llm("vendas por cliente", cat, Espiao(responses=[ruim]))  # o que o modelo inventa passa pela mesma validação


def test_app_streamlit_abre_com_indicadores_e_responde_pergunta(con, monkeypatch):
    from streamlit.testing.v1 import AppTest

    vendas = con.execute('SELECT * FROM "painel_15_quanto_cada_vendedor_vendeu"').df()
    rh = con.execute('SELECT * FROM "painel_18_quantos_funcionarios_ativos"').df()
    monkeypatch.setattr(n, "baixar", lambda api, chave: {"painel_15_quanto_cada_vendedor_vendeu": _parquet(vendas),
                                                         "painel_18_quantos_funcionarios_ativos": _parquet(rh)})
    at = AppTest.from_file("../lastro/rapido/app.py", default_timeout=60)
    at.secrets["LASTRO_CHAVE"] = "lst_teste"
    at.run()
    assert not at.exception, at.exception
    metricas = {m.label: m.value for m in at.metric}
    assert metricas["Total de valor de produtos"] == "390,50" and metricas["Registros"] == "6"
    at.text_input[0].input("vendas por região").run()
    assert not at.exception and any("região da obra" in s.value for s in at.subheader)


def test_consultas_em_paralelo_com_cursor_por_sessao():
    """Streamlit Cloud, 26/11: a conexão em cache, usada por várias sessões ao mesmo tempo, dava ResourceInUseException."""
    import threading

    import duckdb

    con = duckdb.connect()
    con.execute("CREATE TABLE painel_1_vendas AS SELECT range AS registros, range % 7 AS company FROM range(300000)")
    erros: list[str] = []

    def consultar() -> None:
        c = n.por_sessao(con)
        try:
            for _ in range(15):
                c.execute('SELECT company, sum(registros) FROM "painel_1_vendas" GROUP BY 1 ORDER BY 2 DESC').fetchall()
        except Exception as e:  # noqa: BLE001
            erros.append(type(e).__name__)

    ts = [threading.Thread(target=consultar) for _ in range(4)]
    for t in ts:
        t.start()
    for t in ts:
        t.join()
    assert erros == []


def test_resumo_compara_o_mesmo_periodo_do_ano_anterior():
    """Grill de 26/11: jan até o último mês com dado contra o mesmo intervalo do ano anterior."""
    df = pd.DataFrame({"company": ["a", "b", "a", "a", "b", "a"], "ano_mes": ["2025-01", "2025-02", "2025-07", "2026-01", "2026-02", "2026-02"],
                       "valor": [100.0, 50.0, 999.0, 120.0, 30.0, 30.0], "registros": [1] * 6})
    con = n.carregar({"painel_9_vendas": _parquet(df)})
    r = n.resumo(con, "painel_9_vendas", "valor", {})
    assert r["total"] == pytest.approx(1329) and r["registros"] == 6
    c = r["comparacao"]  # 2026 até fev (180) contra 2025 até fev (150): julho de 2025 fica fora
    assert (c["ano"], c["mes"], c["atual"], c["anterior"]) == (2026, 2, 180, 150) and c["variacao"] == pytest.approx(0.2)
    so_a = n.resumo(con, "painel_9_vendas", "valor", {"company": ["a"]})["comparacao"]
    assert (so_a["atual"], so_a["anterior"]) == (150, 100)
    assert n.resumo(con, "painel_9_vendas", "valor", {"ano": [2025]})["total"] == pytest.approx(1149)


def test_ranking_top_10_com_outros_e_conferencia(con):
    topo, detalhe = n.ranking(con, "painel_15_quanto_cada_vendedor_vendeu", "projeto_regiao", "valores_produtos", {}, top=2)
    assert [t[0] for t in topo] == ["Sudeste", "Sul", "outros (2)"]
    assert sum(t[1] for t in topo) == pytest.approx(sum(d[1] for d in detalhe)) == pytest.approx(390.5)
    assert sum(d[3] for d in detalhe) == pytest.approx(1) and sum(d[2] for d in detalhe) == 6
    with pytest.raises(n.PlanoInvalido):
        n.ranking(con, "painel_15_quanto_cada_vendedor_vendeu", "cliente_nome", "valores_produtos", {})  # fora do escopo do app rápido


def test_app_relatorio_sem_medida_rh_abre_sem_erro(con, monkeypatch):
    """26/11: no relatório de RH (sem coluna de valor) a conferência tinha duas colunas "Registros" e o st.dataframe quebrava."""
    from streamlit.testing.v1 import AppTest

    vendas = con.execute('SELECT * FROM "painel_15_quanto_cada_vendedor_vendeu"').df()
    rh = con.execute('SELECT * FROM "painel_18_quantos_funcionarios_ativos"').df()
    monkeypatch.setattr(n, "baixar", lambda api, chave: {"painel_15_quanto_cada_vendedor_vendeu": _parquet(vendas),
                                                         "painel_18_quantos_funcionarios_ativos": _parquet(rh)})
    at = AppTest.from_file("../lastro/rapido/app.py", default_timeout=60)
    at.secrets["LASTRO_CHAVE"] = "lst_teste"
    at.run()
    at.selectbox[0].select("painel_18_quantos_funcionarios_ativos").run()
    assert not at.exception, at.exception
    rotulos = [m.label for m in at.metric]
    assert rotulos.count("Registros") == 1 and "Média por registro" not in rotulos
    assert {m.label: m.value for m in at.metric}["Registros"] == "4"
    tabela = at.dataframe[0].value
    assert list(tabela.columns) == ["Setor", "Registros", "% do total"]


def test_aba_pergunte_responde_sobre_rh_e_uma_aba_nao_derruba_a_outra(con, monkeypatch):
    from streamlit.testing.v1 import AppTest

    vendas = con.execute('SELECT * FROM "painel_15_quanto_cada_vendedor_vendeu"').df()
    rh = con.execute('SELECT * FROM "painel_18_quantos_funcionarios_ativos"').df()
    monkeypatch.setattr(n, "baixar", lambda api, chave: {"painel_15_quanto_cada_vendedor_vendeu": _parquet(vendas),
                                                         "painel_18_quantos_funcionarios_ativos": _parquet(rh)})
    at = AppTest.from_file("../lastro/rapido/app.py", default_timeout=60)
    at.secrets["LASTRO_CHAVE"] = "lst_teste"
    at.run()
    at.text_input[0].input("quantos funcionários por setor").run()
    assert not at.exception, at.exception
    assert any("setor" in s.value.lower() for s in at.subheader)
    monkeypatch.setattr(n, "resumo", lambda *a, **k: 1 / 0)  # indicadores quebram: o Pergunte continua respondendo
    at.run()
    assert not at.exception and any("não carregou" in e.value for e in at.error)
    assert any("setor" in s.value.lower() for s in at.subheader)
