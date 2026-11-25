"""Cada SaaS do catálogo contra o seu simulador: extração completa, armadilhas reais e só leitura."""

from __future__ import annotations

from datetime import date

import pytest

from lastro.saas.motor import Credencial, ErroSaaS, EscritaNaFonte, Leitor, Truncamento, carregar_catalogo, gravar_bronze
from lastro.saas.simulador import RelogioVirtual, Simulador

CAT = carregar_catalogo()
TODOS = sorted(CAT)
VARS = {"subdominio": "demo", "dominio": "demo", "planilha_id": "abc123", "aba": "Vendas"}


def credenciais(saas: str, valor: str = "segredo") -> dict[str, str]:
    a = CAT[saas]["auth"]
    cred = {k: valor for k in a.get("campos", [])}
    cred |= {k: valor for k in a.get("cabecalhos", {})}
    if a["tipo"] in ("bearer_estatico", "oauth2_refresh"):
        cred["token"] = valor
    return cred


def leitor(saas: str, sim: Simulador, valor: str = "segredo") -> Leitor:
    import httpx

    return Leitor(saas, credenciais(saas, valor), VARS, cliente=httpx.Client(transport=sim.transporte()), relogio=sim.relogio)


def entidade(saas: str) -> str:
    return next(iter(CAT[saas]["entidades"]))


@pytest.mark.parametrize("saas", TODOS)
def test_extrai_tudo_e_confere_total(saas):
    sim = Simulador(saas, n=237)
    ext = leitor(saas, sim).extrair(entidade(saas))
    assert len(ext.registros) == 237
    assert sorted(r["id"] for r in ext.registros) == list(range(1, 238))
    assert sim.tentativas_escrita == 0


@pytest.mark.parametrize("saas", TODOS)
def test_respeita_limite_sem_tomar_429(saas):
    sim = Simulador(saas, n=600)
    ext = leitor(saas, sim).extrair(entidade(saas))
    assert ext.tentativas_429 == 0, "o limitador deve espaçar as chamadas antes do 429"


@pytest.mark.parametrize("saas", TODOS)
def test_recupera_de_rajada_de_429(saas):
    sim = Simulador(saas, n=50, rajada_429=3)
    ext = leitor(saas, sim).extrair(entidade(saas))
    assert len(ext.registros) == 50 and ext.tentativas_429 == 3


@pytest.mark.parametrize("saas", TODOS)
def test_credencial_invalida_para_tudo(saas):
    sim = Simulador(saas, n=10)
    with pytest.raises((Credencial, ErroSaaS)):
        leitor(saas, sim, valor="invalida").extrair(entidade(saas))


@pytest.mark.parametrize("saas", [s for s in TODOS if CAT[s].get("erro_200")])
def test_erro_com_http_200_nao_vira_carga_vazia(saas):
    sim = Simulador(saas, n=10)
    with pytest.raises(ErroSaaS, match="HTTP 200"):
        leitor(saas, sim, valor="empresa_inexistente").extrair(entidade(saas))


@pytest.mark.parametrize("saas", [s for s in TODOS if CAT[s].get("incremental")])
def test_incremental_traz_so_o_que_mudou(saas):
    sim = Simulador(saas, n=300)
    tudo = leitor(saas, sim).extrair(entidade(saas))
    parcial = leitor(saas, Simulador(saas, n=300)).extrair(entidade(saas), desde=date(2026, 9, 1))
    assert 0 < len(parcial.registros) < len(tudo.registros)
    assert all(r["atualizado_em"] >= "2026-09-01" for r in parcial.registros)


@pytest.mark.parametrize("saas", [s for s in TODOS if CAT[s]["auth"]["tipo"] == "login_bearer"])
def test_token_que_expira_no_meio_da_carga_e_renovado(saas):
    sim = Simulador(saas, n=1600, expirar_token_apos=1)  # várias páginas mesmo com teto de 500
    ext = leitor(saas, sim).extrair(entidade(saas))
    assert len(ext.registros) == 1600 and ext.relogins >= 1


def test_teto_de_pagina_menor_que_o_pedido_nao_corta_a_carga():
    # IMUV /task tem teto 10: o motor não pode achar que acabou ao receber menos que 50.
    sim = Simulador("imuv", n=95)
    ext = leitor("imuv", sim).extrair("tarefas")
    assert len(ext.registros) == 95 and ext.chamadas >= 10


def test_truncamento_e_detectado():
    class Mentiroso(Simulador):
        def _paginar(self, regs, e, params):  # a API "perde" um registro mas informa o total certo
            st, cab, corpo = super()._paginar(regs[:-1], e, params)
            if isinstance(corpo, dict) and "resultSetMetadata" in corpo:
                corpo["resultSetMetadata"]["count"] = len(regs)
            return st, cab, corpo

    with pytest.raises(Truncamento):
        leitor("sienge", Mentiroso("sienge", n=120)).extrair("contratos_venda")


def test_rpc_so_aceita_chamada_de_leitura():
    sim = Simulador("omie", n=5)
    lei = leitor("omie", sim)
    with pytest.raises(EscritaNaFonte):
        lei._chamar("/geral/clientes/", {"pagina": 1}, call="IncluirCliente")


def test_simulador_recusa_escrita():
    import httpx

    sim = Simulador("pipedrive", n=5)
    r = httpx.Client(transport=sim.transporte()).patch("https://api.pipedrive.com/api/v2/deals/1", json={"title": "x"})
    assert r.status_code == 405 and sim.tentativas_escrita == 1


def test_sienge_espera_o_limite_por_minuto():
    rel = RelogioVirtual()
    sim = Simulador("sienge", n=1000, relogio=rel)
    leitor("sienge", sim).extrair("contratos_venda")
    # 5 páginas de 200 a 200 req/min: pelo menos 4 intervalos de 0,3 s
    assert rel.dormido >= 4 * 0.3 - 1e-9


def test_bronze_grava_dados_e_metadados(tmp_path):
    sim = Simulador("cvcrm", n=42)
    ext = leitor("cvcrm", sim).extrair("leads")
    arq = gravar_bronze(tmp_path, "acme", ext, date(2026, 11, 25))
    assert arq.read_text(encoding="utf-8").count("\n") == 42
    assert (arq.parent / "_meta.json").exists()
    assert "tenant=acme" in str(arq) and "data_extracao=2026-11-25" in str(arq)


def test_credencial_faltando_e_avisada_antes_de_chamar():
    with pytest.raises(Credencial, match="faltam"):
        Leitor("sienge", {"usuario": "x"}, VARS)


def test_colecao_postman_valida_para_todos():
    from lastro.saas.servico import colecao_postman

    for saas in TODOS:
        col = colecao_postman(saas, "http://localhost:8000")
        assert col["info"]["schema"].endswith("v2.1.0/collection.json")
        assert len(col["item"]) >= len(CAT[saas]["entidades"])
        assert any(v["key"] == "base_url" for v in col["variable"])


def test_sandbox_http_responde_como_a_api(tmp_path, monkeypatch):
    monkeypatch.setenv("LASTRO_HOME", str(tmp_path))
    import importlib

    import lastro.api as api
    from fastapi.testclient import TestClient

    importlib.reload(api)
    c = TestClient(api.app)
    r = c.get("/sandbox/sienge/sales-contracts", params={"offset": 0, "limit": 500}, headers={"Authorization": "Basic ZGVtbzpkZW1v"})
    assert r.status_code == 200
    j = r.json()
    assert len(j["results"]) == 180 and j["resultSetMetadata"]["count"] == 180  # pediu 500, teto é 200, há 180
    assert c.delete("/sandbox/sienge/sales-contracts").status_code == 405


# ---- LST-11: Google Sheets e Drive (somente leitura) ----------------------------------

def test_google_pede_so_escopos_de_leitura():
    for saas in ("google_sheets", "google_drive"):
        escopos = CAT[saas]["auth"]["escopos"]
        assert escopos and all(e.endswith(".readonly") for e in escopos), escopos


def test_planilha_vira_registros_com_cabecalho_e_celulas_vazias_no_fim():
    sim = Simulador("google_sheets", n=40)
    lei = Leitor("google_sheets", credenciais("google_sheets"), VARS | {"planilha_id": "abc123", "aba": "Vendas"},
                 cliente=__import__("httpx").Client(transport=sim.transporte()), relogio=sim.relogio)
    ext = lei.extrair("valores")
    assert len(ext.registros) == 40
    assert set(ext.registros[0]) == {"id", "nome", "valor", "status", "atualizado_em", "observacao"}
    # a API omite células vazias no fim da linha: o motor completa com ""
    assert any(r["observacao"] == "" for r in ext.registros)
    assert sim.tentativas_escrita == 0


def test_drive_lista_planilhas_com_cursor():
    sim = Simulador("google_drive", n=230)
    ext = leitor("google_drive", sim).extrair("planilhas")
    assert len(ext.registros) == 230 and ext.chamadas >= 3


def test_planilha_ficticia_vira_fonte_com_perfil_do_explorador(tmp_path, monkeypatch):
    monkeypatch.setenv("LASTRO_HOME", str(tmp_path / "home"))
    from lastro.banco import Repo, conectar, criar_tenant
    from lastro.config import carregar
    from lastro.saas.servico import importar_como_fonte, testar
    from lastro.servico import Plataforma

    cfg = carregar()
    con = conectar(cfg.banco)
    criar_tenant(con, "acme", "Acme")
    repo = Repo(con, "acme")
    laudo = testar("google_sheets", "valores", credenciais("google_sheets"), {"planilha_id": "abc123", "aba": "Vendas"})
    assert laudo["ok"], laudo
    plat = Plataforma(cfg, repo)
    destino = importar_como_fonte(plat.pasta, "acme", laudo)
    fid = repo.adicionar_fonte("planilha_vendas", "arquivo", str(destino))
    d = plat.abrir("ana@acme", "Qual o valor por status?", [fid])
    perfil = next(iter(d["resultado"]["perfis"].values()))
    papeis = {c["nome"]: c["papel"] for c in perfil["colunas"]}
    assert papeis["valor"] == "numero" and papeis["status"] == "texto"
    assert "id" in perfil["chaves_candidatas"]


# --- LST-10: Bling e Ploomes ----------------------------------------------------------------

def test_bling_incremental_so_nas_rotas_que_aceitam():
    import httpx

    from lastro.cargas import cota_do_contrato
    from lastro.saas.motor import incremental_da

    assert incremental_da(CAT["bling"], "pedidos_venda")["param"] == "dataAlteracaoInicial"
    assert incremental_da(CAT["bling"], "contas_receber") is None
    sim = Simulador("bling", n=250)
    lei = Leitor("bling", {"token": "t"}, cliente=httpx.Client(transport=sim.transporte()), relogio=sim.relogio)
    ext = lei.extrair("pedidos_venda", desde=date(2026, 9, 1))
    primeira = sim.chamadas[0]["query"]
    assert primeira["dataAlteracaoInicial"] == "2026-09-01 00:00:00" and primeira["limite"] == "100" and primeira["pagina"] == "1"
    assert ext.registros and all(r["atualizado_em"] >= "2026-09-01" for r in ext.registros)
    with pytest.raises(ValueError, match="contas_receber"):
        lei.extrair("contas_receber", desde=date(2026, 9, 1))
    assert cota_do_contrato("bling", None) == 120000  # cota fixa da conta, sem pacote


def test_ploomes_odata_skip_top_e_user_key():
    import httpx

    sim = Simulador("ploomes", n=650)
    lei = Leitor("ploomes", {"user_key": "chave-de-integracao"}, cliente=httpx.Client(transport=sim.transporte()), relogio=sim.relogio)
    ext = lei.extrair("negocios")
    assert len(ext.registros) == 650
    assert [c["query"]["$skip"] for c in sim.chamadas] == ["0", "300", "600"] and sim.chamadas[0]["query"]["$top"] == "300"
    sem_chave = Leitor("ploomes", {"user_key": "invalida"}, cliente=httpx.Client(transport=Simulador("ploomes", n=5).transporte()))
    with pytest.raises(Credencial):
        sem_chave.extrair("negocios")
