"""LST-30: a pasta de cada empresa sobrevive ao disco efêmero do Render, espelhada no Supabase Storage."""

from __future__ import annotations

import json
import shutil
from pathlib import Path

import httpx
import pytest

from lastro.banco import Repo, conectar, criar_tenant
from lastro.config import RAIZ, carregar
from lastro.espelho import EspelhoStorage, abrir_espelho
from lastro.servico import Plataforma

EXEMPLO = RAIZ / "exemplos" / "orcamentos.csv"
CHAVE = "sb_secret_chave-de-teste"


class StorageFalso:
    """Imita as três rotas do Supabase Storage que o espelho usa."""

    def __init__(self) -> None:
        self.objetos: dict[str, bytes] = {}
        self.envios = 0

    def transporte(self) -> httpx.MockTransport:
        def h(req: httpx.Request) -> httpx.Response:
            if req.headers.get("apikey") != CHAVE:
                return httpx.Response(401, json={"error": "sem chave"})
            if "authorization" in req.headers:  # chave secreta nova não é JWT: no Authorization ela falha
                return httpx.Response(401, json={"error": "Invalid JWT"})
            caminho = req.url.path.removeprefix("/storage/v1/")
            if caminho.startswith("object/list/tenants") and req.method == "POST":
                corpo = json.loads(req.content)
                prefixo = corpo["prefix"].rstrip("/") + "/" if corpo["prefix"] else ""
                filhos: dict[str, bool] = {}
                for k in self.objetos:
                    if k.startswith(prefixo):
                        resto = k[len(prefixo):].split("/", 1)
                        filhos[resto[0]] = len(resto) == 1
                nomes = sorted(filhos)[corpo["offset"]:corpo["offset"] + corpo["limit"]]
                return httpx.Response(200, json=[{"name": n, "id": "x" if filhos[n] else None} for n in nomes])
            chave = httpx.URL(str(req.url)).path.removeprefix("/storage/v1/object/tenants/")
            from urllib.parse import unquote

            chave = unquote(chave)
            if req.method == "POST":
                if chave in self.objetos and req.headers.get("x-upsert") != "true":
                    return httpx.Response(409)
                self.objetos[chave] = req.content
                self.envios += 1
                return httpx.Response(200, json={"Key": f"tenants/{chave}"})
            if req.method == "GET":
                return httpx.Response(200, content=self.objetos[chave]) if chave in self.objetos else httpx.Response(404)
            return httpx.Response(405)

        return httpx.MockTransport(h)


@pytest.fixture
def storage():
    falso = StorageFalso()
    return falso, EspelhoStorage("https://projeto.supabase.co", CHAVE, http=httpx.Client(transport=falso.transporte()))


def test_envia_so_o_que_mudou(tmp_path: Path, storage):
    falso, esp = storage
    pasta = tmp_path / "acme"
    (pasta / "fontes").mkdir(parents=True)
    (pasta / "fontes" / "a.csv").write_text("x\n1\n")
    (pasta / "politica.yaml").write_text("plano: consulta\n")
    (pasta / "fontes" / ".a.csv.123.tmp").write_text("meio gravado")
    (pasta / "sandbox.duckdb").write_text("banco de trabalho")
    assert esp.sincronizar(pasta, "acme") == 2
    assert set(falso.objetos) == {"acme/fontes/a.csv", "acme/politica.yaml"}  # temporários e duckdb ficam fora
    assert esp.sincronizar(pasta, "acme") == 0
    (pasta / "fontes" / "a.csv").write_text("x\n1\n2\n")
    assert esp.sincronizar(pasta, "acme") == 1 and falso.objetos["acme/fontes/a.csv"] == b"x\n1\n2\n"


def test_disco_apagado_a_demanda_continua(monkeypatch, tmp_path: Path, storage):
    falso, esp = storage
    monkeypatch.setenv("LASTRO_HOME", str(tmp_path))
    cfg = carregar()
    con = conectar(cfg.banco)  # o banco fica no Supabase em produção; aqui sobrevive no SQLite
    criar_tenant(con, "acme", "Acme")
    repo = Repo(con, "acme")
    plat = Plataforma(cfg, repo, esp)
    fonte = plat.pasta / "fontes" / "orcamentos.csv"
    fonte.parent.mkdir(parents=True)
    shutil.copy(EXEMPLO, fonte)
    fid = repo.adicionar_fonte("orcamentos", "arquivo", str(fonte))
    d = plat.abrir("ana@acme", "Quanto cada vendedor vendeu, em valor vendido, nos contratos fechados?", [fid])
    d = plat.executar(plat.responder_grill(d["id"], "ana@acme", {"geral:revisor": "Rui"})["id"], "ana@acme")
    plat.sincronizar()
    relatorio = (plat.pasta_demanda(d["id"]) / "relatorio.html").read_bytes()

    shutil.rmtree(plat.pasta)  # o Render dormiu: o disco sumiu
    plat2 = Plataforma(cfg, repo, esp)
    assert (plat2.pasta_demanda(d["id"]) / "relatorio.html").read_bytes() == relatorio
    assert fonte.exists()
    # as decisões do grill voltaram com a Caixa: a segunda demanda pergunta só medida e recorte
    d2 = plat2.abrir("ana@acme", "Como evoluiu o valor orçado por mês em cada segmento?", [fid])
    assert {q["id"] for q in d2["grill"]} == {"orcamentos:medida", "orcamentos:filtro"}
    d2 = plat2.executar(plat2.responder_grill(d2["id"], "ana@acme", {})["id"], "ana@acme")
    assert d2["status"] == "em_revisao"
    assert plat2.sincronizar() > 0 and any(k.startswith(f"acme/demandas/{d2['id']}/") for k in falso.objetos)


def test_api_espelha_o_upload_e_nao_expoe_a_chave(monkeypatch, tmp_path: Path, storage):
    import importlib

    from fastapi.testclient import TestClient

    falso, esp = storage
    monkeypatch.setenv("LASTRO_HOME", str(tmp_path))
    import lastro.api as api

    api = importlib.reload(api)
    monkeypatch.setattr(api, "espelho", esp)
    api.banco.criar_tenant("acme", "Acme")
    api.banco.criar_usuario("acme", "adm@acme", "Adm", "admin", "senha123")
    c = TestClient(api.app)
    cab = {"Authorization": "Bearer " + c.post("/api/login", json={"email": "adm@acme", "senha": "senha123"}).json()["token"]}
    r = c.post("/api/fontes", headers=cab, files={"arquivo": ("vendas.csv", b"a,b\n1,2\n", "text/csv")})
    assert r.status_code == 200 and CHAVE not in r.text
    assert any(k.startswith("acme/fontes/") and k.endswith(".csv") for k in falso.objetos)
    assert CHAVE.encode() not in (tmp_path / "lastro.db").read_bytes()


def test_sem_storage_configurado_nada_muda(monkeypatch):
    monkeypatch.delenv("LASTRO_STORAGE_URL", raising=False)
    assert abrir_espelho() is None
    monkeypatch.setenv("LASTRO_STORAGE_URL", "https://x.supabase.co")
    monkeypatch.delenv("LASTRO_STORAGE_CHAVE", raising=False)
    with pytest.raises(RuntimeError, match="CHAVE"):
        abrir_espelho()


def test_chave_antiga_jwt_vai_tambem_no_authorization():
    esp = EspelhoStorage("https://p.supabase.co", "eyJhbGciOi.parte.assinatura")
    assert esp._cab == {"apikey": "eyJhbGciOi.parte.assinatura", "Authorization": "Bearer eyJhbGciOi.parte.assinatura"}
    assert EspelhoStorage("https://p.supabase.co", "sb_secret_x")._cab == {"apikey": "sb_secret_x"}


def test_chave_errada_falha_alto(tmp_path: Path):
    falso = StorageFalso()
    esp = EspelhoStorage("https://projeto.supabase.co", "errada", http=httpx.Client(transport=falso.transporte()))
    (tmp_path / "acme").mkdir()
    (tmp_path / "acme" / "x.txt").write_text("1")
    with pytest.raises(Exception, match="HTTP 401"):
        esp.sincronizar(tmp_path / "acme", "acme")


def test_rede_fora_vira_erro_do_espelho_e_a_carga_vira_aviso(monkeypatch, tmp_path: Path):

    from lastro import cargas
    from lastro.banco import BancoSqlite
    from lastro.cofre import CofreLocal
    from lastro.espelho import ErroEspelho

    def caiu(req):
        raise httpx.ConnectError("proxy recusou")

    esp = EspelhoStorage("https://p.supabase.co", CHAVE, http=httpx.Client(transport=httpx.MockTransport(caiu)))
    with pytest.raises(ErroEspelho, match="inacessível"):
        esp.listar("acme")
    monkeypatch.setenv("LASTRO_HOME", str(tmp_path))
    cfg = carregar()
    banco = BancoSqlite(cfg.banco)
    banco.criar_tenant("acme", "Acme")
    repo = banco.repo("acme")
    fid = repo.adicionar_fonte("rd", "arquivo", str(cfg.pasta_tenant("acme") / "fontes" / "rd.csv"))
    cid = repo.criar_carga(fid, "rdstation_crm", "negocios", {}, modo="sandbox")
    r = cargas.executar(banco, CofreLocal(cfg.home), cfg, repo.carga(cid), 1_795_600_000, espelho=esp)
    assert r["status"] == "falhou" and "Storage inacessível" in r["aviso"]  # aviso no portal, sem exceção solta
