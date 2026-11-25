"""LST-9: OAuth2 com refresh_token, testado no simulador (servidor de token com validade e refresh rotativo)."""

from __future__ import annotations

import stat
from urllib.parse import parse_qs, urlparse

import httpx
import pytest

from lastro.cofre import CofreLocal
from lastro.saas.motor import Credencial, Leitor, carregar_catalogo
from lastro.saas.oauth import AppOAuth, GerenteToken, emitir_state, ler_state, nome_no_cofre, renovar, trocar_codigo, url_autorizacao
from lastro.saas.simulador import Simulador

CAT = carregar_catalogo()
OAUTH = [k for k, c in CAT.items() if c["auth"]["tipo"] == "oauth2_refresh"]
APP = AppOAuth("cliente-lastro", "segredo-do-app", "https://lastro.exemplo/oauth/retorno")
VARS = {"google_sheets": {"planilha_id": "abc", "aba": "Vendas"}}


def test_quatro_sistemas_tem_contrato_oauth_completo():
    assert set(OAUTH) == {"rdstation_crm", "contaazul", "google_sheets", "google_drive"}
    for k in OAUTH:
        a = CAT[k]["auth"]
        assert a["url_autorizar"].startswith("https://") and a["url_token"].startswith("https://"), k
        assert a["cliente_no"] in ("basic", "corpo") and a["validade_s"] > 0, k


def test_url_de_autorizacao_leva_o_que_cada_sistema_pede():
    ca = parse_qs(url_autorizacao(CAT["contaazul"], APP, "st").split("?", 1)[1])  # a query vem depois do "#/"
    assert ca["scope"] == ["openid profile aws.cognito.signin.user.admin"] and ca["state"] == ["st"]
    g = parse_qs(urlparse(url_autorizacao(CAT["google_sheets"], APP, "st")).query)
    assert g["access_type"] == ["offline"] and g["prompt"] == ["consent"] and "readonly" in g["scope"][0]
    rd = url_autorizacao(CAT["rdstation_crm"], APP, "st")
    assert rd.startswith("https://accounts.rdstation.com/oauth/authorize?response_type=code&client_id=cliente-lastro")


def test_state_assinado_recusa_adulterado_e_vencido():
    st = emitir_state("s" * 40, "acme", "contaazul", "adm@acme", agora=1000)
    assert ler_state("s" * 40, st, agora=1100) | {"n": ""} == {"t": "acme", "s": "contaazul", "e": "adm@acme", "x": 1600, "n": ""}
    with pytest.raises(Credencial):
        ler_state("s" * 40, st.replace(st[3], "Z" if st[3] != "Z" else "Y", 1), agora=1100)
    with pytest.raises(Credencial):
        ler_state("outro-segredo" * 4, st, agora=1100)
    with pytest.raises(Credencial):
        ler_state("s" * 40, st, agora=1601)


def _conectar(saas: str, tmp_path, validade: float = 3600):
    sim = Simulador(saas, n=60, validade_token_s=validade)
    http = httpx.Client(transport=sim.transporte())
    cofre = CofreLocal(tmp_path)
    tokens = trocar_codigo(CAT[saas], APP, Simulador.CODIGO_SANDBOX, http, agora=sim.relogio.agora())
    cofre.guardar(nome_no_cofre("acme", saas), tokens.para_cofre())
    gerente = GerenteToken(CAT[saas], APP, cofre, "acme", saas, http, sim.relogio)
    leitor = Leitor(saas, {}, VARS.get(saas, {}), cliente=http, relogio=sim.relogio, oauth=gerente)
    return sim, http, cofre, gerente, leitor, tokens


@pytest.mark.parametrize("saas", OAUTH)
def test_renova_antes_de_vencer_e_guarda_o_par_novo(saas, tmp_path):
    sim, http, cofre, gerente, leitor, primeiro = _conectar(saas, tmp_path)
    ent = next(iter(CAT[saas]["entidades"]))
    assert leitor.extrair(ent).registros and gerente.renovacoes == 0
    sim.relogio.dormir(3600 - 120)  # faltam 2 minutos: dentro da margem de 5
    assert leitor.extrair(ent).registros
    assert gerente.renovacoes == 1
    assert leitor.relogins == 0  # renovou antes de vencer: nenhuma chamada tomou 401
    guardado = cofre.ler(nome_no_cofre("acme", saas))
    assert gerente.tokens.access_token in guardado and gerente.tokens.access_token != primeiro.access_token
    if CAT[saas]["auth"]["refresh_rotativo"]:
        assert gerente.tokens.refresh_token != primeiro.refresh_token
        with pytest.raises(Credencial):  # o refresh antigo morreu: por isso o cofre é regravado na hora
            renovar(CAT[saas], APP, primeiro.refresh_token, http, sim.relogio.agora())
    else:
        assert gerente.tokens.refresh_token == primeiro.refresh_token


@pytest.mark.parametrize("saas", ["rdstation_crm", "contaazul"])
def test_401_no_meio_da_carga_renova_uma_vez_e_segue(saas, tmp_path):
    sim, _, _, gerente, leitor, _ = _conectar(saas, tmp_path)
    sim._oauth_acesso.clear()  # o sistema derrubou o token antes da hora
    ext = leitor.extrair(next(iter(CAT[saas]["entidades"])))
    assert ext.registros and gerente.renovacoes == 1 and ext.relogins == 1


def test_refresh_recusado_pede_nova_autorizacao(tmp_path):
    sim, _, _, gerente, leitor, _ = _conectar("contaazul", tmp_path)
    sim._oauth_refresh.clear()
    sim.relogio.dormir(3600)
    with pytest.raises(Credencial, match="autorizar de novo"):
        leitor.extrair("vendas")


def test_sem_autorizacao_no_cofre_explica_o_que_fazer(tmp_path):
    with pytest.raises(Credencial, match="autorizar"):
        GerenteToken(CAT["contaazul"], APP, CofreLocal(tmp_path), "acme", "contaazul", httpx.Client())


def test_cofre_local_fica_fora_das_empresas_e_so_o_dono_le(tmp_path):
    cofre = CofreLocal(tmp_path)
    cofre.guardar("x", "segredo")
    assert stat.S_IMODE(cofre.arquivo.stat().st_mode) == 0o600
    assert stat.S_IMODE(cofre.arquivo.parent.stat().st_mode) == 0o700
    assert "tenants" not in cofre.arquivo.parts
    cofre.guardar("x", "novo")
    assert cofre.ler("x") == "novo" and cofre.ler("y") is None
