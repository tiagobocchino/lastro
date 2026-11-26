"""LST-34: o agente monta e edita o painel da demanda; a mesma especificação vira HTML e projeto do Power BI."""

from __future__ import annotations

import json
import re
import shutil
from pathlib import Path

import pytest

from lastro import paineis
from lastro.banco import BancoSqlite
from lastro.config import RAIZ, carregar
from lastro.servico import Plataforma

SCHEMAS = Path(__file__).parent / "dados" / "powerbi_schemas"
TOTAL_AUDITADO = 14030477.92


@pytest.fixture(scope="module")
def demanda(tmp_path_factory):
    home = tmp_path_factory.mktemp("lastro")
    mp = pytest.MonkeyPatch()
    mp.setenv("LASTRO_HOME", str(home))
    cfg = carregar()
    b = BancoSqlite(cfg.banco)
    b.criar_tenant("acme", "Acme")
    repo = b.repo("acme", "adm@acme", "admin")
    dest = cfg.pasta_tenant("acme") / "fontes" / "orcamentos.csv"
    dest.parent.mkdir(parents=True)
    shutil.copy(RAIZ / "exemplos" / "orcamentos.csv", dest)
    fid = repo.adicionar_fonte("orcamentos", "arquivo", str(dest))
    p = Plataforma(cfg, repo)
    d = p.abrir("adm@acme", "Quanto cada vendedor vendeu, em valor vendido, nos contratos fechados?", [fid])
    d = p.executar(p.responder_grill(d["id"], "adm@acme", {"geral:revisor": "Rui"})["id"], "adm@acme")
    d = p.revisar(d["id"], "adm@acme", True, "ok")
    yield d, p.pasta_demanda(d["id"]) / "gold"
    mp.undo()


def test_painel_inicial_sai_do_modelo_da_demanda(demanda):
    d, gold = demanda
    spec = paineis.inicial(d, gold)
    assert [v["tipo"] for v in spec["visuais"]] == ["kpi", "barras", "linha", "tabela"]
    assert spec["visuais"][1]["eixo"] == "vendedor" and spec["visuais"][2]["eixo"] == "ano_mes"
    valores = paineis.dados(spec, gold)
    assert valores["v1"] == pytest.approx(TOTAL_AUDITADO, abs=0.01)  # o KPI bate com a auditoria
    assert sum(x[1] for x in valores["v2"]) == pytest.approx(TOTAL_AUDITADO, abs=0.01)
    assert valores["v2"][0][0] == "Eva Martins"


def test_mudancas_validas_preservam_o_que_existe(demanda):
    d, gold = demanda
    cat = paineis.catalogo(gold, d["resultado"]["modelo"])
    spec = paineis.inicial(d, gold)
    s2, frase = paineis.mudar(spec, paineis.interpretar("nova medida média de valor orçado", spec, cat), cat)
    assert s2["versao"] == 2 and s2["medidas"][-1] == {"id": "valor_orcado_media", "nome": "Média de valor orcado", "coluna": "valor_orcado", "agregacao": "media"}
    assert "média" not in frase or "valor_orcado" in frase
    s3, _ = paineis.mudar(s2, paineis.interpretar("Adicione um gráfico de barras de valor orçado média por estado", s2, cat), cat)
    novo = s3["visuais"][-1]
    assert novo == {"id": "v5", "tipo": "barras", "medida": "valor_orcado_media", "eixo": "estado", "titulo": "Média de valor orcado por estado"}
    assert s3["visuais"][:4] == spec["visuais"]  # ids e visuais antigos intactos
    s4, _ = paineis.mudar(s3, paineis.interpretar("remova o v3", s3, cat), cat)
    assert [v["id"] for v in s4["visuais"]] == ["v1", "v2", "v4", "v5"]
    s5, _ = paineis.mudar(s4, {"op": "adicionar_visual", "tipo": "linha", "medida": "valor_vendido_soma", "eixo": "ano"}, cat)
    assert s5["visuais"][-1]["id"] == "v6"  # não reaproveita o id removido


@pytest.mark.parametrize(("op", "erro"), [
    ({"op": "adicionar_medida", "coluna": "nao_existe"}, "não existe"),
    ({"op": "adicionar_medida", "coluna": "contrato_id", "agregacao": "soma"}, "não é numérica"),
    ({"op": "adicionar_medida", "coluna": "valor_vendido", "agregacao": "mediana"}, "agregação"),
    ({"op": "adicionar_visual", "tipo": "barras", "medida": "valor_vendido_soma", "eixo": "cidade"}, "eixo 'cidade'"),
    ({"op": "adicionar_visual", "tipo": "pizza", "medida": "valor_vendido_soma", "eixo": "estado"}, "tipo de visual"),
    ({"op": "adicionar_visual", "tipo": "barras", "medida": "fantasma", "eixo": "estado"}, "medida que não existe"),
    ({"op": "remover_medida", "id": "valor_vendido_soma"}, "em uso"),
    ({"op": "remover_visual", "id": "v99"}, "não existe"),
    ({"op": "apagar_tudo"}, "operação desconhecida"),
])
def test_mudanca_invalida_e_recusada_sem_alterar(demanda, op, erro):
    d, gold = demanda
    cat = paineis.catalogo(gold, d["resultado"]["modelo"])
    spec = paineis.inicial(d, gold)
    antes = json.dumps(spec)
    with pytest.raises(paineis.PedidoInvalido, match=erro):
        paineis.mudar(spec, op, cat)
    assert json.dumps(spec) == antes


def test_pedido_nao_entendido_responde_com_exemplos(demanda):
    d, gold = demanda
    cat = paineis.catalogo(gold, d["resultado"]["modelo"])
    with pytest.raises(paineis.PedidoInvalido, match="Exemplos"):
        paineis.interpretar("deixa o painel mais bonito", paineis.inicial(d, gold), cat)


def test_html_estatico_com_os_numeros_do_gold(demanda):
    d, gold = demanda
    h = paineis.html_painel(paineis.inicial(d, gold), gold, "25/11/2026 12:00")
    assert "14.030.477,92" in h and "Eva Martins" in h and "<polyline" in h and "versão 1" in h
    # LST-55: um arquivo só, sem biblioteca externa: filtros pelo cubo embutido, números já desenhados sem script
    assert 'id="filtros" hidden' in h and 'type="application/json" id="dados"' in h and "<script src" not in h
    assert "% do total" in h and "18,3%" in h and "<tfoot>" in h


def test_cartoes_e_filtros_conferem_com_o_gold(demanda):
    """As contas do painel (as mesmas que o script refaz ao filtrar) batem com SQL direto no gold."""
    import duckdb

    from lastro import painel_html

    d, gold = demanda
    spec = paineis.inicial(d, gold)
    c = painel_html.cubo(spec, gold)
    k = painel_html.contas(spec, c)
    assert k["total"] == pytest.approx(TOTAL_AUDITADO, abs=0.01) and k["v4"]["total"] == pytest.approx(TOTAL_AUDITADO, abs=0.01)
    assert sum(x[2] for x in k["v4"]["linhas"]) == pytest.approx(1)
    fato, dim = gold / "fato.parquet", gold / "dim_vendedor.parquet"
    con = duckdb.connect()  # conexão própria: a padrão do duckdb é do processo inteiro
    for f in [x for x in c["filtros"] if x != "ano"]:
        valor = c["valores"][f][0]
        kf = painel_html.contas(spec, c, {f: valor})
        sql = (f"SELECT sum(valor_vendido), count(*) FROM read_parquet('{fato}') JOIN read_parquet('{gold / f'dim_{f}.parquet'}') "
               f"USING ({f}_id) WHERE {f} = ?")
        total, regs = con.execute(sql, [valor]).fetchall()[0]
        assert kf["total"] == pytest.approx(total, abs=0.01) and kf["registros"] == regs
    comp = k["comparacao"]  # mesmo período do ano anterior (grill do Tiago, 26/11)
    base = con.execute(f"SELECT sum(valor_vendido) FROM read_parquet('{fato}') WHERE year(data) = ? AND month(data) <= ?",
                       [comp["ano"] - 1, comp["mes"]]).fetchall()[0][0]
    con.close()
    assert comp["anterior"] == pytest.approx(base, abs=0.01)
    assert dim.exists()


def test_ranking_mostra_top_10_e_outros(demanda, tmp_path):
    from lastro import painel_html

    d, gold = demanda
    spec = paineis.inicial(d, gold)
    v2 = next(v for v in spec["visuais"] if v["tipo"] == "barras")
    c = painel_html.cubo(spec, gold)
    ix = c["colunas"].index(v2["eixo"])
    for i, linha in enumerate(c["linhas"]):  # 14 vendedores fictícios: cada linha do cubo com um nome próprio
        linha[ix] = f"vendedor {i % 14:02d}"
    k = painel_html.contas(spec, c)
    nomes = [x[0] for x in k[v2["id"]]["linhas"]]
    assert len(nomes) == 11 and nomes[-1] == "outros (4)"
    assert sum(x[1] for x in k[v2["id"]]["linhas"]) == pytest.approx(TOTAL_AUDITADO, abs=0.01)


def _registro():
    from referencing import Registry, Resource

    recursos = []
    for arq in SCHEMAS.rglob("*.json"):
        uri = "https://developer.microsoft.com/json-schemas/" + arq.relative_to(SCHEMAS).as_posix()
        recursos.append((uri, Resource.from_contents(json.loads(arq.read_text()))))
    return Registry().with_resources(recursos)


def test_projeto_power_bi_valida_contra_os_schemas_oficiais(demanda):
    import jsonschema

    d, gold = demanda
    cat = paineis.catalogo(gold, d["resultado"]["modelo"])
    spec, _ = paineis.mudar(paineis.inicial(d, gold), {"op": "adicionar_medida", "coluna": "contrato_id", "agregacao": "distintos"}, cat)
    con = {"host": "aws-1-sa-east-1.pooler.supabase.com", "porta": 5432, "banco": "postgres", "esquema": "bi_0123456789"}
    arqs = paineis.projeto_powerbi(spec, gold, con)
    reg = _registro()
    jsons = {k: json.loads(v) for k, v in arqs.items() if k.endswith((".json", ".pbir", ".pbism", ".pbip"))}
    assert len(jsons) == 7 + len(spec["visuais"])  # pbip, pbism, pbir, version, report, pages, page + 1 por visual
    for caminho, doc in jsons.items():
        schema = reg.get_or_retrieve(doc["$schema"]).value.contents
        erros = sorted(jsonschema.Draft7Validator(schema, registry=reg).iter_errors(doc), key=str)
        assert not erros, f"{caminho}: {erros[0].message}"
    did = d["id"]
    nome = f"Lastro_demanda_{did}"
    assert json.loads(arqs[f"{nome}.Report/definition.pbir"])["datasetReference"]["byPath"]["path"] == f"../{nome}.SemanticModel"
    # TMDL: tabelas declaradas, partições lendo do schema do BI, medidas sobre colunas que existem
    tmdl = {k: v for k, v in arqs.items() if k.endswith(".tmdl")}
    modelo = tmdl[f"{nome}.SemanticModel/definition/model.tmdl"]
    tabelas = re.findall(r"^ref table (\S+)$", modelo, re.MULTILINE)
    assert tabelas == [f"d{did}_fato", f"d{did}_dim_vendedor", f"d{did}_dim_data"]
    for t in tabelas:
        corpo = tmdl[f"{nome}.SemanticModel/definition/tables/{t}.tmdl"]
        assert f'Item = "{t}"' in corpo and "PostgreSQL.Database(Servidor, Banco)" in corpo
        assert all(not ln.startswith(" ") for ln in corpo.splitlines())  # indentação só com tabs
    fato = tmdl[f"{nome}.SemanticModel/definition/tables/d{did}_fato.tmdl"]
    assert f"measure 'Valor vendido' = SUM(d{did}_fato[valor_vendido])" in fato
    assert f"measure 'Distintos de contrato id' = DISTINCTCOUNT(d{did}_fato[contrato_id])" in fato
    rel = tmdl[f"{nome}.SemanticModel/definition/relationships.tmdl"]
    assert f"fromColumn: d{did}_fato.vendedor_id" in rel and f"toColumn: d{did}_dim_data.data" in rel
    exp = tmdl[f"{nome}.SemanticModel/definition/expressions.tmdl"]
    assert 'expression Esquema = "bi_0123456789"' in exp and "aws-1-sa-east-1.pooler.supabase.com:5432" in exp
    # LST-47: modo HTTPS, URL base fixa e RelativePath por tabela (o Service agenda a atualização sem gateway)
    https = paineis.projeto_powerbi(spec, gold, {"via": "https", "api": "https://lastro.exemplo/"})
    for t in tabelas:
        corpo = https[f"{nome}.SemanticModel/definition/tables/{t}.tmdl"]
        assert f'Web.Contents(Api, [RelativePath = "bi/v1/{t}.parquet", Headers = [#"X-Lastro-Chave" = ChaveLastro]])' in corpo
        assert "Parquet.Document(Binario)" in corpo and "PostgreSQL" not in corpo
    exp_https = https[f"{nome}.SemanticModel/definition/expressions.tmdl"]
    assert 'expression Api = "https://lastro.exemplo/"' in exp_https and "Servidor" not in exp_https
    # cada visual aponta para uma medida que existe no modelo
    for k, doc in jsons.items():
        if k.endswith("visual.json"):
            for papel in doc["visual"]["query"]["queryState"].values():
                for p in papel["projections"]:
                    if "Measure" in p["field"]:
                        assert f"measure {_tmdl(p['field']['Measure']['Property'])} =" in fato


def _tmdl(n: str) -> str:
    return f"'{n}'" if re.search(r"[.=:' ]", n) else n


@pytest.fixture
def api_aprovada(monkeypatch, tmp_path):
    import importlib

    from fastapi.testclient import TestClient

    monkeypatch.setenv("LASTRO_HOME", str(tmp_path))
    monkeypatch.delenv("LASTRO_BANCO_URL", raising=False)
    import lastro.api as modulo

    modulo = importlib.reload(modulo)
    for t in ("acme", "outra"):
        modulo.banco.criar_tenant(t, t)
        modulo.banco.criar_usuario(t, f"ana@{t}", "Ana", "demandante", "senha-longa-de-teste")
        modulo.banco.criar_usuario(t, f"rui@{t}", "Rui", "revisor", "senha-longa-de-teste")
        modulo.banco.criar_usuario(t, f"adm@{t}", "Adm", "admin", "senha-longa-de-teste")
    c = TestClient(modulo.app)

    def cab(email: str) -> dict:
        return {"Authorization": "Bearer " + c.post("/api/login", json={"email": email, "senha": "senha-longa-de-teste"}).json()["token"]}

    ana, rui = cab("ana@acme"), cab("rui@acme")
    fid = c.post("/api/fontes", headers=cab("adm@acme"), files={"arquivo": ("orcamentos.csv", (RAIZ / "exemplos" / "orcamentos.csv").read_bytes(), "text/csv")}).json()["id"]
    did = c.post("/api/demandas", headers=ana, json={"pergunta": "Quanto cada vendedor vendeu, em valor vendido, nos contratos fechados?", "fontes": [fid]}).json()["id"]
    c.post(f"/api/demandas/{did}/grill", headers=ana, json={"geral:revisor": "Rui"})
    c.post(f"/api/demandas/{did}/executar", headers=ana)
    return modulo, c, cab, ana, rui, did


def test_painel_pelo_portal_com_rastro(api_aprovada):
    import io
    import zipfile

    _, c, cab, ana, rui, did = api_aprovada
    assert c.post(f"/api/demandas/{did}/painel", headers=ana).status_code == 409  # ainda não aprovada
    c.post(f"/api/demandas/{did}/revisao", headers=rui, json={"aprovado": True, "parecer": "ok"})
    assert c.post(f"/api/demandas/{did}/painel", headers=rui).status_code == 403  # revisor não monta painel
    spec = c.post(f"/api/demandas/{did}/painel", headers=ana).json()
    assert spec["versao"] == 1 and c.post(f"/api/demandas/{did}/painel", headers=ana).status_code == 409
    r = c.post(f"/api/demandas/{did}/painel/mudancas", headers=ana, json={"pedido": "adicione um gráfico de barras de valor vendido por estado"})
    assert r.status_code == 200 and r.json()["versao"] == 2 and r.json()["visuais"][-1]["eixo"] == "estado"
    r = c.post(f"/api/demandas/{did}/painel/mudancas", headers=ana, json={"pedido": "gráfico de pizza por cidade"})
    assert r.status_code == 400 and "Exemplos" in r.json()["detail"]
    estado = c.get(f"/api/demandas/{did}/painel", headers=ana).json()
    assert estado["versoes"] == [1, 2] and "estado" in estado["opcoes"]["eixos"]
    h = c.get(f"/api/demandas/{did}/painel/html", headers=ana)
    assert h.status_code == 200 and "14.030.477,92" in h.text and "versão 2" in h.text
    z = zipfile.ZipFile(io.BytesIO(c.get(f"/api/demandas/{did}/painel/powerbi?via=postgres", headers=ana).content))
    assert f"Lastro_demanda_{did}.pbip" in z.namelist() and 'expression Esquema = "SEU_SCHEMA"' in z.read(
        f"Lastro_demanda_{did}.SemanticModel/definition/expressions.tmdl").decode()  # sem BI ligado: parâmetro para preencher
    # LST-47: o padrão é HTTPS com a chave de leitura (sem certificado e sem gateway)
    z = zipfile.ZipFile(io.BytesIO(c.get(f"/api/demandas/{did}/painel/powerbi", headers=ana).content))
    exp = z.read(f"Lastro_demanda_{did}.SemanticModel/definition/expressions.tmdl").decode()
    assert 'expression ChaveLastro = "COLE_A_CHAVE_DE_LEITURA"' in exp and "expression Api" in exp and "Esquema" not in exp
    assert "ChaveLastro" in z.read("LEIA-ME.txt").decode()
    acoes = [e["acao"] for e in c.get(f"/api/demandas/{did}", headers=ana).json()["eventos"]]
    assert {"criou_painel", "alterou_painel", "recusou_mudanca_painel", "baixou_powerbi"} <= set(acoes)
    # outra empresa não vê nem mexe no painel desta demanda
    intruso = cab("ana@outra")
    assert c.get(f"/api/demandas/{did}/painel", headers=intruso).status_code == 404
    assert c.post(f"/api/demandas/{did}/painel/mudancas", headers=intruso, json={"pedido": "remova o v1"}).status_code == 404
    assert c.get(f"/api/demandas/{did}/painel/html", headers=intruso).status_code == 404


def test_dashboard_na_demanda_previa_so_para_o_revisor(api_aprovada):
    """LST-57: o dashboard aparece sozinho na demanda; antes da aprovação, só revisor e admin veem a prévia marcada."""
    _, c, cab, ana, rui, did = api_aprovada
    adm = cab("adm@acme")
    assert c.get(f"/api/demandas/{did}/dashboard", headers=ana).status_code == 403  # quem demandou espera a aprovação
    for quem in (rui, adm):
        h = c.get(f"/api/demandas/{did}/dashboard", headers=quem)
        assert h.status_code == 200 and "Prévia para o revisor" in h.text and "ainda não foi entregue" in h.text
        assert "14.030.477,92" in h.text and 'id="filtros"' in h.text  # mesmo número da resposta auditada
    c.post(f"/api/demandas/{did}/revisao", headers=rui, json={"aprovado": True, "parecer": "ok"})
    h = c.get(f"/api/demandas/{did}/dashboard", headers=ana)  # aprovada: sem clicar em "montar painel"
    assert h.status_code == 200 and "gold aprovado" in h.text and "Prévia" not in h.text and "14.030.477,92" in h.text
    assert c.get(f"/api/demandas/{did}/dashboard", headers=cab("adm@outra")).status_code == 404  # outra empresa não vê
    c.post(f"/api/demandas/{did}/painel/mudancas", headers=ana, json={"pedido": "adicione um gráfico de barras de valor vendido por estado"})
    c.post(f"/api/demandas/{did}/painel", headers=ana)
    c.post(f"/api/demandas/{did}/painel/mudancas", headers=ana, json={"pedido": "adicione um gráfico de barras de valor vendido por estado"})
    assert "por estado" in c.get(f"/api/demandas/{did}/dashboard", headers=rui).text  # o personalizado vale para todos


def test_pergunte_na_demanda_com_a_chave_do_lastro_ou_do_cliente(api_aprovada, monkeypatch):
    """LST-57: pedido em português vira gráfico sobre os dados da demanda; a LLM só vê a pergunta e os nomes das colunas."""
    from langchain_core.language_models.fake_chat_models import FakeListChatModel

    from lastro.rapido import nucleo

    _, c, cab, ana, rui, did = api_aprovada
    adm = cab("adm@acme")
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
    assert c.post(f"/api/demandas/{did}/pergunte", headers=ana, json={"pergunta": "valor vendido por vendedor"}).status_code == 403
    r = c.post(f"/api/demandas/{did}/pergunte", headers=rui, json={"pergunta": "valor vendido por vendedor"}).json()  # prévia
    assert r["origem"] == "palavras-chave" and r["dimensao"] == "vendedor" and r["grafico"] == "barras"
    assert sum(linha[-1] for linha in r["linhas"]) == pytest.approx(TOTAL_AUDITADO, abs=0.05)  # confere com a resposta auditada
    c.post(f"/api/demandas/{did}/revisao", headers=rui, json={"aprovado": True, "parecer": "ok"})

    visto: list[str] = []
    usado: list[tuple[str, str]] = []

    class Espiao(FakeListChatModel):
        def _call(self, messages, *a, **k):
            visto.append("\n".join(str(m.content) for m in messages))
            return super()._call(messages, *a, **k)

    def falso(chave, modelo):
        usado.append((chave, modelo))
        plano = (f'{{"tabela": "painel_{did}_demanda", "agregacao": "soma", "medida": "valor_vendido", '
                 '"dimensao": "estado", "por_mes": false, "grafico": "barras", "titulo": "Vendido por estado"}')
        return Espiao(responses=[plano])

    monkeypatch.setattr(nucleo, "modelo_gemini", falso)
    monkeypatch.setenv("GOOGLE_API_KEY", "chave-do-lastro-de-teste-0123456789")
    r = c.post(f"/api/demandas/{did}/pergunte", headers=ana, json={"pergunta": "quanto vendemos em cada estado?"}).json()
    assert r["origem"] == "lastro" and "limites do plano gratuito" in r["aviso_modelo"] and r["titulo"] == "Vendido por estado"
    assert usado[-1][0] == "chave-do-lastro-de-teste-0123456789"
    assert "quanto vendemos em cada estado?" in visto[-1] and "estado" in visto[-1]
    for dado in ("Eva Martins", "2567582", "14030477"):  # nenhum valor da demanda vai ao provedor
        assert dado not in visto[-1]

    # chave própria do cliente: só o admin cadastra; a chave nunca volta para a tela
    corpo = {"chave": "chave-do-cliente-abcdefghijklmnop", "modelo": "gemini-modelo-do-cliente"}
    assert c.put("/api/conta/llm", headers=ana, json=corpo).status_code == 403
    assert c.put("/api/conta/llm", headers=adm, json={"chave": "curta"}).status_code == 400
    assert c.put("/api/conta/llm", headers=adm, json=corpo).status_code == 200
    estado = c.get("/api/conta/llm", headers=ana).json()
    assert estado["propria"] and estado["modelo"] == "gemini-modelo-do-cliente" and "abcdefghijklmnop" not in str(estado)
    r = c.post(f"/api/demandas/{did}/pergunte", headers=ana, json={"pergunta": "quanto vendemos em cada estado?"}).json()
    assert r["origem"] == "cliente" and "não é garantido" not in r["aviso_modelo"] and "só é garantido" in r["aviso_modelo"]
    assert usado[-1] == ("chave-do-cliente-abcdefghijklmnop", "gemini-modelo-do-cliente")
    assert c.get("/api/conta/llm", headers=cab("adm@outra")).json()["propria"] is False  # outra empresa não herda a chave
    assert c.delete("/api/conta/llm", headers=adm).json() == {"propria": False}
    acoes = [e for e in c.get(f"/api/demandas/{did}", headers=ana).json()["eventos"] if e["acao"] == "pergunte"]
    assert len(acoes) == 3 and "chave-do" not in str(acoes)  # rastro sem chave


def test_pedidos_reais_dos_testadores_ao_designer(demanda):
    """26/11, demanda 19 da demo: 48 pedidos recusados com 'não entendi'. As frases abaixo são as que o testador escreveu."""
    d, gold = demanda
    cat = paineis.catalogo(gold, d["resultado"]["modelo"])
    spec = paineis.inicial(d, gold)

    def aplica(pedido):
        nonlocal spec
        spec, frase = paineis.mudar(spec, paineis.interpretar(pedido, spec, cat), cat)
        return frase

    assert "Soma de valor orcado" in aplica("nova medida de valor orçado")  # sem agregação: soma
    frase = aplica("adicione um gráfico de média de valor orçado")  # sem tipo nem eixo: cartão, criando a medida junto
    assert "kpi" in frase and "medida 'Média de valor orcado'" in frase
    assert "barras" in aplica("adicione um gráfico de barras de media de valor orçado por vendedor")
    with pytest.raises(paineis.PedidoInvalido, match="já existe no painel"):  # o clique duplo não duplica mais
        aplica("adicione um gráfico de barras de media de valor orçado por vendedor")
    antes = [v["id"] for v in spec["visuais"]]
    assert "removeu" in aplica("remova um dos gráficos de média de valor orçado por vendedor")  # pelo nome
    assert len(spec["visuais"]) == len(antes) - 1
    assert "linha" in aplica("adicione um gráfico de valor orçado por mês")
    for pedido in ("nova medida valor vendido dividido por valor orçado",
                   "adicione um gráfico de conversão mês a mês com valor vendido x valor orçado",
                   "adicione um gráfico de evoução mes a mes com o % de evolução",
                   "Adicione os valores de evolulção mensal comparando os valores desse mês x valores do mês passado até o mesmo dia"):
        with pytest.raises(paineis.PedidoInvalido, match="medida calculada"):  # resposta específica, não 'não entendi'
            paineis.interpretar(pedido, spec, cat)
