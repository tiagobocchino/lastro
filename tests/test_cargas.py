"""LST-7: cargas incrementais agendadas, com marca d'água, cota diária e tudo ou nada."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

import httpx
import pandas as pd
import pytest

from lastro import cargas
from lastro.banco import BancoSqlite
from lastro.cofre import CofreLocal
from lastro.config import carregar
from lastro.saas.simulador import Simulador

DIA1 = datetime(2026, 11, 24, 7, 0, tzinfo=cargas.FUSO).timestamp()  # 07h em Brasília
DIA2 = DIA1 + 24 * 3600


@pytest.fixture
def ambiente(monkeypatch, tmp_path: Path):
    monkeypatch.setenv("LASTRO_HOME", str(tmp_path))
    cfg = carregar()
    banco = BancoSqlite(cfg.banco)
    banco.criar_tenant("acme", "Acme")
    cofre = CofreLocal(cfg.home)
    cofre.guardar(cargas.nome_credencial("acme", "sienge"), json.dumps({"usuario": "leitor", "senha": "s"}))
    destino = cfg.pasta_tenant("acme") / "fontes" / "sienge_contratos_venda.csv"
    destino.parent.mkdir(parents=True)
    repo = banco.repo("acme")
    fid = repo.adicionar_fonte("sienge_contratos_venda", "arquivo", str(destino))
    sim = Simulador("sienge", n=450)  # 3 páginas de 200
    cid = repo.criar_carga(fid, "sienge", "contratos_venda", {"subdominio": "acme"}, hora=6)

    def rodar(agora: float) -> dict:
        return cargas.executar(banco, cofre, cfg, repo.carga(cid), agora, httpx.Client(transport=sim.transporte()))

    return banco, repo, cid, destino, sim, rodar, cofre, cfg


def test_primeira_carga_completa_e_depois_so_o_que_mudou(ambiente):
    banco, repo, cid, destino, sim, rodar, _, _ = ambiente
    r = rodar(DIA1)
    assert r["status"] == "ok" and r["incremental"] is False and r["linhas_na_fonte"] == 450 and r["chamadas"] == 3
    c = repo.carga(cid)
    assert c["marca_dagua"] == DIA1 and c["ultimo_status"] == "ok" and c["chamadas_no_dia"] == 3

    # entre um dia e outro, o sistema mudou um contrato e ganhou um novo
    sim.dados["contratos_venda"][4] |= {"valor": 1.5, "atualizado_em": "2026-11-24T15:00:00Z"}
    sim.dados["contratos_venda"].append({"id": 451, "nome": "contrato 0451", "valor": 99.0, "status": "aberto", "atualizado_em": "2026-11-24T16:00:00Z"})
    r = rodar(DIA2)
    assert r["status"] == "ok" and r["incremental"] is True
    assert r["novos_ou_alterados"] == 2 and r["chamadas"] == 1  # só o que mudou: uma página
    fonte = pd.read_csv(destino)
    assert len(fonte) == 451 and fonte["id"].is_unique
    assert fonte.loc[fonte["id"] == 5, "valor"].item() == 1.5
    assert repo.carga(cid)["marca_dagua"] == DIA2


def test_cota_esgotada_no_meio_nao_deixa_carga_parcial(ambiente):
    banco, repo, cid, destino, sim, rodar, _, _ = ambiente
    destino.write_text("id,valor\n1,10\n")
    antes = destino.read_bytes()
    repo.atualizar_carga(cid, cota_diaria=2)  # a carga completa precisa de 3 requisições
    r = rodar(DIA1)
    assert r["status"] == "cota" and r["chamadas"] == 2 and "amanhã" in r["aviso"]
    assert destino.read_bytes() == antes  # duas páginas lidas, nada gravado
    c = repo.carga(cid)
    assert c["marca_dagua"] is None and c["chamadas_no_dia"] == 2 and c["ultimo_status"] == "cota"
    assert not cargas.devida(c, DIA1 + 3600)  # cota: só amanhã
    assert cargas.devida(c, DIA2)
    assert not list(destino.parent.glob(".*.tmp"))


def test_cota_e_do_contrato_somada_entre_cargas_do_mesmo_sistema(ambiente):
    banco, repo, cid, destino, sim, rodar, cofre, cfg = ambiente
    repo.atualizar_carga(cid, cota_diaria=5)
    assert rodar(DIA1)["chamadas"] == 3
    fid2 = repo.adicionar_fonte("sienge_clientes", "arquivo", str(destino.with_name("sienge_clientes.csv")))
    cid2 = repo.criar_carga(fid2, "sienge", "clientes", {"subdominio": "acme"}, cota_diaria=5)
    r2 = cargas.executar(banco, cofre, cfg, repo.carga(cid2), DIA1 + 60, httpx.Client(transport=sim.transporte()))
    assert r2["status"] == "cota" and r2["chamadas"] == 2  # sobraram 2 das 5 do dia


def test_falha_vira_aviso_e_nao_mexe_na_fonte(ambiente):
    banco, repo, cid, destino, sim, rodar, cofre, _ = ambiente
    destino.write_text("id,valor\n1,10\n")
    antes = destino.read_bytes()
    cofre.guardar(cargas.nome_credencial("acme", "sienge"), json.dumps({"usuario": "leitor", "senha": "invalida"}))
    r = rodar(DIA1)
    assert r["status"] == "falhou" and "Nada foi alterado" in r["aviso"]
    assert destino.read_bytes() == antes
    c = repo.carga(cid)
    assert c["ultimo_aviso"] == r["aviso"] and c["marca_dagua"] is None
    assert cargas.devida(c, DIA1 + 3600)  # falha comum tenta de novo na hora seguinte
    eventos = banco.con.execute("SELECT detalhe FROM eventos WHERE acao='executou_carga'").fetchall()
    assert "invalida" not in str([tuple(e) for e in eventos])  # credencial não vai para o rastro


def test_chave_ausente_nao_grava(ambiente):
    banco, repo, cid, destino, _, rodar, _, _ = ambiente
    banco.con.execute("UPDATE cargas SET chave='codigo_inexistente' WHERE id=?", (cid,))
    r = rodar(DIA1)
    assert r["status"] == "falhou" and "chave" in r["aviso"] and not destino.exists()


def test_regras_de_horario():
    base = {"ativa": True, "hora": 6, "marca_dagua": None, "ultimo_status": "nunca", "ultima_execucao": None}
    madrugada = datetime(2026, 11, 24, 5, 59, tzinfo=cargas.FUSO).timestamp()
    assert not cargas.devida(base, madrugada) and cargas.devida(base, madrugada + 60)
    assert not cargas.devida(base | {"marca_dagua": DIA1}, DIA1 + 3600)  # já rodou bem hoje
    assert not cargas.devida(base | {"ativa": False}, DIA1)


def test_cota_pelo_pacote_do_catalogo():
    assert cargas.cota_do_contrato("sienge", "Free") == 100 and cargas.cota_do_contrato("sienge", None) is None
    with pytest.raises(ValueError):
        cargas.cota_do_contrato("sienge", "Gratis")


def test_sandbox_roda_sem_credencial(ambiente):
    banco, repo, _, destino, _, _, cofre, cfg = ambiente
    fid = repo.adicionar_fonte("rd", "arquivo", str(destino.with_name("rd.csv")))
    cid = repo.criar_carga(fid, "rdstation_crm", "negocios", {}, modo="sandbox")
    r = cargas.executar(banco, cofre, cfg, repo.carga(cid), DIA1)
    assert r["status"] == "ok" and r["linhas_na_fonte"] == 180


# --- pela API ---------------------------------------------------------------------------

@pytest.fixture
def api_cargas(monkeypatch, tmp_path):
    import importlib

    from fastapi.testclient import TestClient

    from lastro.politica import politica_padrao

    monkeypatch.setenv("LASTRO_HOME", str(tmp_path))
    monkeypatch.setenv("LASTRO_TAREFA_SEGREDO", "t" * 40)
    import lastro.api as api

    api = importlib.reload(api)
    for t, plano in (("acme", "operacao"), ("basico", "consulta")):
        api.banco.criar_tenant(t, t)
        api.banco.criar_usuario(t, f"adm@{t}", "Adm", "admin", "senha123")
        pol = politica_padrao()
        pol.plano = plano
        (api.cfg.pasta_tenant(t)).mkdir(parents=True, exist_ok=True)
        pol.salvar(api.cfg.pasta_tenant(t) / "politica.yaml")
    sim = Simulador("sienge", n=50)
    monkeypatch.setattr(api, "_cliente_oauth", lambda: httpx.Client(transport=sim.transporte()))
    c = TestClient(api.app)

    def entrar(email):
        return {"Authorization": "Bearer " + c.post("/api/login", json={"email": email, "senha": "senha123"}).json()["token"]}

    return api, c, entrar


def _importar(c, cab):
    r = c.post("/api/saas/sienge/testar", headers=cab, json={"entidade": "contratos_venda", "credenciais": {"usuario": "u", "senha": "s"},
                                                            "variaveis": {"subdominio": "acme"}, "modo": "sandbox", "importar": True})
    return r.json()["fonte_id"]


def test_api_agenda_guarda_credencial_no_cofre_e_executa_pela_tarefa(api_cargas):
    api, c, entrar = api_cargas
    cab = entrar("adm@acme")
    fid = _importar(c, cab)
    r = c.post("/api/cargas", headers=cab, json={"fonte_id": fid, "saas": "sienge", "entidade": "contratos_venda", "variaveis": {"subdominio": "acme"},
                                                 "credenciais": {"usuario": "leitor", "senha": "senha-do-cliente"}, "hora": 0, "pacote": "Free"})
    carga = r.json()
    assert r.status_code == 200 and carga["cota_diaria"] == 100 and carga["ultimo_status"] == "nunca", carga
    assert "senha-do-cliente" in api.cofre.ler("lastro:acme:cred:sienge")
    assert b"senha-do-cliente" not in (api.cfg.home / "lastro.db").read_bytes() and "senha" not in r.text

    assert c.post("/tarefas/cargas").status_code == 401
    assert c.post("/tarefas/cargas", headers={"X-Lastro-Tarefa": "errado"}).status_code == 401
    # a carga acabou de ser importada: hoje não roda de novo; amanhã sim
    api.banco.con.execute("UPDATE cargas SET marca_dagua = marca_dagua - 86400")
    r = c.post("/tarefas/cargas", headers={"X-Lastro-Tarefa": "t" * 40})
    assert r.json() == {"executadas": 1, "por_status": {"ok": 1, "cota": 0, "falhou": 0}}
    lista = c.get("/api/cargas", headers=cab).json()
    assert lista[0]["ultimo_status"] == "ok" and lista[0]["fonte"].startswith("sienge_contratos_venda")


def test_api_carga_exige_plano_operacao_e_admin(api_cargas):
    api, c, entrar = api_cargas
    cab = entrar("adm@basico")
    fid = _importar(c, cab)
    r = c.post("/api/cargas", headers=cab, json={"fonte_id": fid, "saas": "sienge", "entidade": "contratos_venda", "credenciais": {"usuario": "u", "senha": "s"}})
    assert r.status_code == 403 and "Operação" in r.json()["detail"]
    r = c.post("/api/cargas", headers=entrar("adm@acme"), json={"fonte_id": fid, "saas": "sienge", "entidade": "contratos_venda", "credenciais": {"usuario": "u", "senha": "s"}})
    assert r.status_code == 404  # fonte de outra empresa


def test_tarefa_sem_segredo_configurado_nao_roda(api_cargas, monkeypatch):
    _, c, _ = api_cargas
    monkeypatch.setenv("LASTRO_TAREFA_SEGREDO", "curto")
    assert c.post("/tarefas/cargas", headers={"X-Lastro-Tarefa": "curto"}).status_code == 503
