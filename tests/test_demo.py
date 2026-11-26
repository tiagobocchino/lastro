"""LST-39: demonstração do site — sessão temporária, perguntas, painel e apagamento com recibo."""

from __future__ import annotations

import importlib
import io
import logging
import sqlite3

import pandas as pd
import pytest

from lastro.config import RAIZ, carregar
from lastro.demo import Demos, ErroDemo

EXEMPLO = RAIZ / "exemplos" / "orcamentos.csv"


@pytest.fixture
def api(monkeypatch, tmp_path):
    from fastapi.testclient import TestClient

    monkeypatch.setenv("LASTRO_HOME", str(tmp_path / "home"))
    monkeypatch.setenv("LASTRO_DEMO", "1")
    monkeypatch.setenv("LASTRO_DEMO_DIR", str(tmp_path / "demo"))
    monkeypatch.delenv("LASTRO_BANCO_URL", raising=False)
    import lastro.api as modulo

    modulo = importlib.reload(modulo)

    class SemEspelho:
        def __getattr__(self, nome):
            raise AssertionError("a demonstração tocou o espelho do Storage")

    monkeypatch.setattr(modulo, "espelho", SemEspelho())
    return modulo, TestClient(modulo.app), tmp_path / "demo"


def _linhas_no_banco(modulo) -> int:
    con = sqlite3.connect(modulo.cfg.banco)
    try:
        return sum(con.execute(f"SELECT count(*) FROM {t}").fetchone()[0] for t in ("tenants", "usuarios", "fontes", "demandas", "eventos"))
    finally:
        con.close()


def test_exemplo_de_ponta_a_ponta_e_nada_sobra(api, caplog):
    modulo, c, base = api
    caplog.set_level(logging.INFO)
    antes = _linhas_no_banco(modulo)
    r = c.post("/api/demo/sessoes", data={"exemplo": "true"})
    assert r.status_code == 200
    s = r.json()
    assert s["perfil"]["linhas"] == 612 and {"nome": "valor_vendido", "papel": "numero"} in s["perfil"]["colunas"]
    ids = {q["id"] for q in s["perguntas"]}
    assert "geral:revisor" not in ids and "planilha:medida" in ids  # sem segunda camada na demonstração
    assert len(list(base.glob("demo-*"))) == 1
    r = c.post(f"/api/demo/sessoes/{s['sessao']}/painel",
               json={"respostas": {"planilha:medida": "valor_vendido", "demo:quebra": "vendedor", "demo:formato": "ranking (barras)"}})
    p = r.json()
    assert r.status_code == 200 and "14.030.477,92" in p["html"] and p["modo"] == "demonstracao" and p["auditoria"]["aprovada"]
    assert "sem revisão humana" in p["html"] and "gold aprovado" not in p["html"]  # o painel diz o que é
    recibo = p["recibo"]
    assert recibo["conferido"] and recibo["arquivos"] > 5 and recibo["tabelas"] >= 3 and recibo["bytes"] > 0 and recibo["registros_em_memoria"] > 0
    assert list(base.glob("demo-*")) == [] and modulo._DEMOS.abertas == 0
    assert _linhas_no_banco(modulo) == antes  # nada no banco
    assert c.post(f"/api/demo/sessoes/{s['sessao']}/painel", json={}).status_code == 404  # a sessão não existe mais
    assert "etapa=apagou" in caplog.text


def test_planilha_propria_csv_e_excel_sem_vazar_no_log(api, caplog):
    _, c, base = api
    caplog.set_level(logging.DEBUG)
    df = pd.DataFrame({"regiao_secreta_xyz": ["Norte", "Sul", "Norte", "Leste"], "receita": [10.5, 20, 30, 40],
                       "cliente_confidencial": ["ACME_VALOR_SECRETO", "B", "C", "D"]})
    for nome, conteudo in (("vendas.csv", df.to_csv(index=False).encode()), ("vendas.xlsx", _xlsx(df))):
        s = c.post("/api/demo/sessoes", files={"arquivo": (nome, conteudo)}).json()
        assert s["perfil"]["linhas"] == 4
        p = c.post(f"/api/demo/sessoes/{s['sessao']}/painel", json={"respostas": {}}).json()
        assert "html" in p and p["recibo"]["conferido"]
    texto = caplog.text
    for segredo in ("regiao_secreta_xyz", "cliente_confidencial", "ACME_VALOR_SECRETO", "Norte", "receita"):
        assert segredo not in texto, f"o log vazou '{segredo}'"
    assert list(base.glob("demo-*")) == []


def _xlsx(df: pd.DataFrame) -> bytes:
    buf = io.BytesIO()
    df.to_excel(buf, index=False)
    return buf.getvalue()


@pytest.mark.parametrize(("nome", "conteudo", "trecho"), [
    ("dados.txt", b"a,b\n1,2\n", "CSV ou Excel"),
    ("grande.csv", b"a,b\n" + b"1,2\n" * (5 * 1024 * 1024 // 4 + 10), "5 MB"),
    ("quebrado.xlsx", b"isto nao e excel", "não consegui ler"),
    ("so-cabecalho.csv", b"empresa,valor\n", "não tem linhas"),
])
def test_recusas_nao_deixam_nada(api, nome, conteudo, trecho):
    _, c, base = api
    r = c.post("/api/demo/sessoes", files={"arquivo": (nome, conteudo)})
    assert r.status_code == 400 and trecho in r.json()["detail"]
    assert list(base.glob("demo-*")) == []


def test_desistir_apaga_com_recibo(api):
    _, c, base = api
    s = c.post("/api/demo/sessoes", data={"exemplo": "true"}).json()
    r = c.delete(f"/api/demo/sessoes/{s['sessao']}").json()
    assert r["recibo"]["conferido"] and r["recibo"]["arquivos"] > 0 and list(base.glob("demo-*")) == []
    assert c.delete(f"/api/demo/sessoes/{s['sessao']}").status_code == 404


def test_desligada_por_padrao(monkeypatch, tmp_path):
    from fastapi.testclient import TestClient

    monkeypatch.setenv("LASTRO_HOME", str(tmp_path))
    monkeypatch.delenv("LASTRO_DEMO", raising=False)
    import lastro.api as modulo

    modulo = importlib.reload(modulo)
    assert TestClient(modulo.app).post("/api/demo/sessoes", data={"exemplo": "true"}).status_code == 404


def test_sessao_abandonada_e_varrida_e_restos_somem_ao_reiniciar(monkeypatch, tmp_path):
    monkeypatch.setenv("LASTRO_HOME", str(tmp_path / "home"))
    base = tmp_path / "demo"
    demos = Demos(carregar(), base, ttl_s=900)
    s, _ = demos.abrir(None, None, agora=1_000.0)
    assert demos.varrer(agora=1_000.0 + 899) == 0 and s.pasta.exists()
    assert demos.varrer(agora=1_000.0 + 901) == 1 and not s.pasta.exists()
    with pytest.raises(ErroDemo, match="expirou"):
        demos.responder(s.id, {}, agora=1_000.0 + 902)
    resto = base / "demo-sobra-de-antes"
    (resto / "fontes").mkdir(parents=True)
    (resto / "fontes" / "x.csv").write_text("a\n1\n")
    Demos(carregar(), base)  # servidor reiniciou
    assert not resto.exists()


# ---- LST-40: grill de "como mostrar" ---------------------------------------------------------

def test_no_maximo_quatro_perguntas_cada_uma_com_sugestao(api):
    _, c, _ = api
    s = c.post("/api/demo/sessoes", data={"exemplo": "true"}).json()
    ps = {q["id"]: q for q in s["perguntas"]}
    assert list(ps) == ["planilha:medida", "demo:quebra", "demo:periodo", "demo:formato"]
    assert all(q["sugestao"] in q["opcoes"] for q in ps.values())
    assert ps["demo:formato"]["opcoes"] == ["ranking (barras)", "tabela", "evolução no tempo", "só o número"]
    assert set(ps["demo:quebra"]["opcoes"]) == {"empresa", "vendedor", "estado", "segmento", "status"}


@pytest.mark.parametrize(("respostas", "esperado"), [
    ({"demo:formato": "só o número"}, [("kpi", None)]),
    ({"demo:formato": "ranking (barras)", "demo:quebra": "estado"}, [("kpi", None), ("barras", "estado")]),
    ({"demo:formato": "tabela", "demo:quebra": "segmento"}, [("kpi", None), ("tabela", "segmento")]),
    ({"demo:formato": "evolução no tempo", "demo:periodo": "por ano"}, [("kpi", None), ("linha", "ano")]),
    ({"demo:formato": "evolução no tempo"}, [("kpi", None), ("linha", "ano_mes")]),
])
def test_respostas_viram_o_painel(api, monkeypatch, respostas, esperado):
    _, c, _ = api
    s = c.post("/api/demo/sessoes", data={"exemplo": "true"}).json()
    capturado = {}
    import lastro.demo as demo_mod

    original = demo_mod.paineis.para_visitante

    def espiao(*a, **k):
        capturado["spec"] = original(*a, **k)
        return capturado["spec"]

    monkeypatch.setattr(demo_mod.paineis, "para_visitante", espiao)
    p = c.post(f"/api/demo/sessoes/{s['sessao']}/painel", json={"respostas": respostas}).json()
    assert [(v["tipo"], v.get("eixo")) for v in capturado["spec"]["visuais"]] == esperado
    assert p["visuais"] == [v["titulo"] for v in capturado["spec"]["visuais"]] and p["recibo"]["conferido"]


def test_resposta_fora_das_opcoes_volta_sem_perder_a_sessao(api):
    _, c, base = api
    s = c.post("/api/demo/sessoes", data={"exemplo": "true"}).json()
    r = c.post(f"/api/demo/sessoes/{s['sessao']}/painel", json={"respostas": {"demo:quebra": "cidade"}})
    assert r.status_code == 400 and "escolha uma das opções" in r.json()["detail"]
    assert len(list(base.glob("demo-*"))) == 1  # a sessão continua: o visitante corrige e tenta de novo
    assert c.post(f"/api/demo/sessoes/{s['sessao']}/painel", json={"respostas": {"demo:quebra": "estado"}}).json()["recibo"]["conferido"]


def test_planilha_so_com_numeros_oferece_so_o_numero(api):
    _, c, _ = api
    s = c.post("/api/demo/sessoes", files={"arquivo": ("n.csv", b"custo,receita\n1,10\n2,20\n3,30\n")}).json()
    ps = {q["id"]: q for q in s["perguntas"]}
    assert list(ps) == ["planilha:medida", "demo:formato"] and ps["demo:formato"]["opcoes"] == ["só o número"]
    p = c.post(f"/api/demo/sessoes/{s['sessao']}/painel", json={"respostas": {"planilha:medida": "receita"}}).json()
    assert "60" in p["html"] and p["visuais"] == ["Receita (total)"]


def test_toda_combinacao_de_respostas_gera_painel_valido_contra_o_gold(monkeypatch, tmp_path):
    """Critério do LST-40: cada combinação (medida × quebra × período × formato) vira especificação válida
    e os números saem do gold sem erro."""
    import itertools

    from lastro import paineis
    from lastro.demo import FORMATOS, PERIODOS

    monkeypatch.setenv("LASTRO_HOME", str(tmp_path / "home"))
    demos = Demos(carregar(), tmp_path / "demo")
    s, abertura = demos.abrir(None, None)
    ps = {q["id"]: q for q in abertura["perguntas"]}
    plat = s.plataforma
    d = plat.executar(plat.responder_grill(s.demanda_id, "visitante", {"geral:revisor": "demo"})["id"], "visitante")
    gold = plat.pasta_demanda(d["id"]) / "gold"
    combinacoes = list(itertools.product(ps["demo:quebra"]["opcoes"], ps["demo:periodo"]["opcoes"], ps["demo:formato"]["opcoes"]))
    assert len(combinacoes) == 5 * 2 * 4
    assert d["resultado"]["auditoria"]["aprovado_camada1"]
    esperado_total = d["resultado"]["resposta"]["total"]  # o total que a auditoria (camada 1) conferiu, já sem repetidos
    for quebra, periodo, formato in combinacoes:
        spec = paineis.para_visitante(d, gold, quebra, PERIODOS[periodo], FORMATOS[formato])
        valores = paineis.dados(spec, gold)
        assert valores["v1"] == pytest.approx(esperado_total, abs=0.01)
        if FORMATOS[formato] == "numero":
            assert len(spec["visuais"]) == 1
        else:
            assert len(valores["v2"]) > 0, (quebra, periodo, formato)
    assert demos.apagar(s.id)["conferido"]


# ---- LST-42: limites e anti-abuso ------------------------------------------------------------

def test_mais_de_50_mil_linhas_e_recusada_sem_deixar_nada(api):
    _, c, base = api
    csv = b"valor\n" + b"1\n" * 50_001
    assert len(csv) < 5 * 1024 * 1024
    r = c.post("/api/demo/sessoes", files={"arquivo": ("muitas.csv", csv)})
    assert r.status_code == 400 and "50.000 linhas" in r.json()["detail"]
    assert list(base.glob("demo-*")) == []


def test_limite_por_ip_e_ip_nao_fica_guardado(api):
    modulo, c, _ = api
    cab = {"x-forwarded-for": "203.0.113.7, 10.0.0.1"}
    for _ in range(5):
        s = c.post("/api/demo/sessoes", data={"exemplo": "true"}, headers=cab).json()
        c.delete(f"/api/demo/sessoes/{s['sessao']}")
    r = c.post("/api/demo/sessoes", data={"exemplo": "true"}, headers=cab)
    assert r.status_code == 429 and "última hora" in r.json()["detail"]
    outro = c.post("/api/demo/sessoes", data={"exemplo": "true"}, headers={"x-forwarded-for": "198.51.100.2"})
    assert outro.status_code == 200
    guardado = str(modulo._DEMOS.limites._vezes)
    assert "203.0.113.7" not in guardado and "198.51.100.2" not in guardado  # só hash com sal


def test_limite_por_dia_com_relogio():
    from lastro.demo import LimiteIP, Limites

    lim = Limites()
    t = 1_000_000.0
    for h in range(4):  # 5 por hora, 4 horas = 20 no dia
        for i in range(5):
            lim.registrar("1.2.3.4", t + h * 3_600 + i)
    with pytest.raises(LimiteIP, match="hoje"):
        lim.registrar("1.2.3.4", t + 4 * 3_600)
    lim.registrar("1.2.3.4", t + 86_400 + 10)  # no dia seguinte volta


def test_fila_de_um_por_vez_responde_voce_e_o_proximo(monkeypatch, tmp_path):
    from lastro.demo import Ocupado

    monkeypatch.setenv("LASTRO_HOME", str(tmp_path / "home"))
    demos = Demos(carregar(), tmp_path / "demo", espera_fila_s=0.2)
    demos._fila.acquire()  # alguém analisando agora
    try:
        with pytest.raises(Ocupado, match="você é o próximo"):
            demos.abrir(None, None)
        assert list((tmp_path / "demo").glob("demo-*")) == []
    finally:
        demos._fila.release()
    s, _ = demos.abrir(None, None)  # vaga liberada: entra
    assert demos.apagar(s.id)["conferido"]


def test_fila_ocupada_vira_503_com_retry_after(api):
    modulo, c, _ = api
    d = modulo._demos()
    d.espera_fila_s = 0.1
    d._fila.acquire()
    try:
        r = c.post("/api/demo/sessoes", data={"exemplo": "true"})
        assert r.status_code == 503 and r.headers["retry-after"] == "10" and "próximo" in r.json()["detail"]
    finally:
        d._fila.release()


def test_prazo_estourado_cancela_e_apaga_quando_a_analise_para(monkeypatch, tmp_path):
    import time as _time

    from lastro.demo import Demorou
    from lastro.servico import Plataforma

    monkeypatch.setenv("LASTRO_HOME", str(tmp_path / "home"))
    base = tmp_path / "demo"
    demos = Demos(carregar(), base, prazo_s=0.3)
    s, _ = demos.abrir(None, None)
    original = Plataforma.executar

    def lento(self, *a, **k):
        _time.sleep(1.0)
        return original(self, *a, **k)

    monkeypatch.setattr(Plataforma, "executar", lento)
    with pytest.raises(Demorou, match="passou de 0 segundos|passou de"):
        demos.responder(s.id, {})
    assert demos._fila.acquire(timeout=5)  # a vaga só volta quando a análise termina de verdade
    demos._fila.release()
    for _ in range(50):  # a análise terminou e apagou a sessão sozinha
        if not list(base.glob("demo-*")):
            break
        _time.sleep(0.1)
    assert list(base.glob("demo-*")) == [] and demos.abertas == 0


def test_prazo_estourado_na_leitura_apaga_a_sessao_que_nasce_depois(monkeypatch, tmp_path):
    import time as _time

    from lastro.demo import Demorou
    from lastro.servico import Plataforma

    monkeypatch.setenv("LASTRO_HOME", str(tmp_path / "home"))
    base = tmp_path / "demo"
    demos = Demos(carregar(), base, prazo_s=0.3)
    original = Plataforma.abrir

    def lento(self, *a, **k):
        _time.sleep(1.0)
        return original(self, *a, **k)

    monkeypatch.setattr(Plataforma, "abrir", lento)
    with pytest.raises(Demorou):
        demos.abrir(None, None)
    assert demos._fila.acquire(timeout=5)
    demos._fila.release()
    for _ in range(50):
        if not list(base.glob("demo-*")) and demos.abertas == 0:
            break
        _time.sleep(0.1)
    assert list(base.glob("demo-*")) == [] and demos.abertas == 0  # a sessão que nasceu tarde foi apagada


# ---- LST-43: o site servido pelo Render ---------------------------------------------------------

def test_site_servido_com_a_secao_e_o_script(api):
    _, c, _ = api
    h = c.get("/site/")
    assert h.status_code == 200 and h.text.startswith("<!doctype html>") and 'id="teste"' in h.text and 'src="demo.js"' in h.text
    assert "apagamos tudo" in h.text.lower()
    js = c.get("/site/demo.js")
    assert js.status_code == 200 and "/api/demo/sessoes" in js.text
    assert c.get("/site/marca/simbolo-cotejo-claro.svg").status_code == 200


def test_sair_da_pagina_apaga_a_sessao(api):
    _, c, base = api
    s = c.post("/api/demo/sessoes", data={"exemplo": "true"}).json()
    assert c.post(f"/api/demo/sessoes/{s['sessao']}/apagar").json()["recibo"]["conferido"]
    assert list(base.glob("demo-*")) == []
    assert c.post(f"/api/demo/sessoes/{s['sessao']}/apagar").json() == {"recibo": None}  # repetido não dá erro


# ---- LST-44: funil anônimo ------------------------------------------------------------------------

def test_funil_registra_as_etapas_sem_nada_do_visitante(api):
    modulo, c, _ = api
    s = c.post("/api/demo/sessoes", data={"exemplo": "true"}).json()
    c.post(f"/api/demo/sessoes/{s['sessao']}/painel", json={"respostas": {"demo:formato": "ranking (barras)"}})
    assert c.post("/api/demo/contato", json={"visual": "ranking"}).json() == {"ok": True}
    secreto = pd.DataFrame({"coluna_super_secreta": ["VALOR_SIGILOSO_1", "VALOR_SIGILOSO_2", "x", "y"], "faturamento_oculto": [1, 2, 3, 4]})
    s2 = c.post("/api/demo/sessoes", files={"arquivo": ("segredo.csv", secreto.to_csv(index=False).encode())}).json()
    c.delete(f"/api/demo/sessoes/{s2['sessao']}")
    c.post("/api/demo/sessoes", files={"arquivo": ("x.txt", b"a\n1\n")})
    ev = modulo.banco.eventos_demo()
    assert [e["etapa"] for e in ev] == ["subiu", "painel", "clicou_contato", "subiu", "desistiu", "recusou"]
    assert ev[0]["faixa_tamanho"] == "até 100 KB" and ev[0]["n_colunas"] == 9 and ev[0]["duracao_ms"] >= 0
    assert ev[1]["visual"] == "ranking" and ev[2]["visual"] == "ranking" and ev[5]["motivo"] == "formato"
    tudo = str(ev)
    for segredo in ("coluna_super_secreta", "VALOR_SIGILOSO", "faturamento_oculto", "segredo.csv", "testclient", "127.0.0.1"):
        assert segredo not in tudo, f"o funil guardou '{segredo}'"


def test_clique_forjado_nao_injeta_texto(api):
    modulo, c, _ = api
    c.post("/api/demo/contato", json={"visual": "<script>alert(1)</script> dados do cliente"})
    assert modulo.banco.eventos_demo()[-1]["visual"] is None


def test_limite_de_ip_vira_recusa_no_funil(api):
    modulo, c, _ = api
    cab = {"x-forwarded-for": "203.0.113.9"}
    for _ in range(6):
        r = c.post("/api/demo/sessoes", data={"exemplo": "true"}, headers=cab)
        if r.status_code == 200:
            c.delete(f"/api/demo/sessoes/{r.json()['sessao']}")
    assert modulo.banco.eventos_demo()[-1] == {**modulo.banco.eventos_demo()[-1], "etapa": "recusou", "motivo": "limite_ip"}


def test_falha_ao_gravar_o_funil_nao_derruba_a_demonstracao(api, monkeypatch):
    modulo, c, _ = api

    def quebrado(*a, **k):
        raise OSError("banco fora")

    monkeypatch.setattr(modulo._demos(), "ao_evento", quebrado)
    s = c.post("/api/demo/sessoes", data={"exemplo": "true"})
    assert s.status_code == 200
    assert c.post(f"/api/demo/sessoes/{s.json()['sessao']}/painel", json={}).json()["recibo"]["conferido"]


def test_evento_so_aceita_lista_fechada():
    from lastro.banco import evento_demo

    with pytest.raises(ValueError):
        evento_demo("qualquer_coisa")
    e = evento_demo("recusou", motivo="CPF 123", faixa_tamanho="enorme", visual="pizza", n_colunas=-1)
    assert e == {"etapa": "recusou", "duracao_ms": None, "faixa_tamanho": None, "n_colunas": None, "visual": None, "motivo": None}


def test_funil_no_painel_de_operacao():
    from datetime import date, datetime
    from zoneinfo import ZoneInfo

    from lastro.painel import renderizar

    vazio = {k: [] for k in ("requisicoes", "disponibilidade", "demandas", "uso", "cargas", "alertas")}
    dados = vazio | {"demo": [{"dia": date(2026, 11, 25), "subiram": 40, "paineis": 30, "clicaram": 6, "recusas": 5, "desistencias": 4}]}
    h = renderizar(dados, datetime(2026, 11, 25, 18, tzinfo=ZoneInfo("America/Sao_Paulo")))
    assert "Funil da demonstração do site" in h and "75,0% da etapa anterior" in h and "20,0% da etapa anterior" in h
    assert "Funil da demonstração" in renderizar(vazio, datetime(2026, 11, 25, 18, tzinfo=ZoneInfo("America/Sao_Paulo")))  # sem dados ainda, não quebra


def test_site_publica_robots_e_sitemap_na_raiz(api):
    """LST-55: só o site é indexável; o sitemap aponta para o próprio host do pedido."""
    _, c, _ = api
    r = c.get("/robots.txt", headers={"host": "exemplo.com.br", "x-forwarded-proto": "https"})
    assert r.status_code == 200 and "Allow: /site/" in r.text and "Disallow: /api/" in r.text
    assert "Sitemap: https://exemplo.com.br/sitemap.xml" in r.text
    s = c.get("/sitemap.xml", headers={"host": "exemplo.com.br", "x-forwarded-proto": "https"})
    assert s.status_code == 200 and "<loc>https://exemplo.com.br/site/</loc>" in s.text and "<lastmod>" in s.text


def test_site_tem_seo_e_ids_da_demo():
    """O HTML do site carrega o SEO do LST-55 e mantém os ids de que o demo.js depende."""
    import json
    import re

    html = (RAIZ / "site" / "index.html").read_text(encoding="utf-8")
    titulo = re.search(r"<title>(.*?)</title>", html).group(1)
    desc = re.search(r'name="description" content="(.*?)"', html).group(1)
    assert titulo.lower().startswith("dashboard para empresas") and len(titulo) <= 60
    assert 120 <= len(desc) <= 156
    for trecho in ('rel="canonical"', 'og:image" content="', 'twitter:card', "fontes/bricolage"):
        assert trecho in html
    grafo = json.loads(re.search(r'<script type="application/ld\+json">(.*?)</script>', html, re.DOTALL).group(1))["@graph"]
    faq = next(n for n in grafo if n["@type"] == "FAQPage")
    for q in faq["mainEntity"]:  # a resposta marcada para o Google é idêntica ao texto visível
        assert f"<h3>{q['name']}</h3></summary><p>{q['acceptedAnswer']['text']}</p>" in html
    for i in ("palco", "t-envio", "t-arquivo", "t-exemplo", "t-aceite", "t-analisar", "t-erro", "t-nome", "copiar", "email-txt"):
        assert f'id="{i}"' in html
    assert len(re.findall(r"<h1[ >]", html)) == 1
    for arq in ("img/og-lastro.jpg", "marca/favicon-32.png", "marca/apple-touch-icon.png"):
        assert (RAIZ / "site" / arq).exists()
