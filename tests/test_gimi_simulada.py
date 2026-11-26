"""LST-36 fase 1: base sintética no padrão bruto da GIMI, gabarito pelas regras do ETL e API simulada com paginação real."""

from __future__ import annotations

import hashlib
import json

import httpx
import pytest

from lastro.saas.motor import Leitor
from lastro.saas.simulador import Simulador
from lastro.simulados import gimi


@pytest.fixture(scope="module")
def base():
    return gimi.gerar(semente=36, contratos_por_empresa=600)


def test_reprodutivel_pela_semente(base):
    h = lambda b: hashlib.sha256(json.dumps(b, sort_keys=True).encode()).hexdigest()
    assert h(gimi.gerar(36, 600)) == h(base) != h(gimi.gerar(37, 600))


def test_formato_bruto_e_sujeiras(base):
    assert set(base) == {"alfa", "beta", "gama", "delta"}
    c = base["alfa"]["contratos"][0]
    assert {"id", "numero", "data_criacao", "status", "cliente", "projeto", "vendedor", "grupo", "valores", "produtos"} <= set(c)
    assert isinstance(c["produtos"], list) and {"produto", "quantidade", "valores"} <= set(c["produtos"][0])  # aninhado, como na IApp
    s = gimi.gabarito(base)["sujeiras"]
    assert all(v > 0 for v in s.values()), s  # teste, antes do corte, valor zero e repetidos estão lá
    nomes = {v["nome"] for v in base["alfa"]["vendedores"]}
    assert any(" - (" in n for n in nomes) and any("_" in n for n in nomes)


def test_regras_do_etl():
    assert gimi.tipo_venda("Aline Castro - (687000001)") == "GIMI" and gimi.tipo_venda("Fabio Rocha") == "REPRESENTANTE"
    assert gimi.limpar_vendedor("Carla Moura - (68700003)") == "Carla Moura" and gimi.limpar_vendedor(None) == "NAO DEFINIDO"
    assert gimi.limpar_vendedor("diego_vaz") == "Diego"  # regra real: corta no "_" e perde o sobrenome (achado)
    assert gimi.classe("Construtoras (A)") == "A" and gimi.classe("Governo") == "-" and gimi.classe(None) == "-"
    assert gimi.categoria_sku("ESQ-1234") == "Esquadria" and gimi.categoria_sku("KIT-9") == "MATERIAL AVULSO"


def test_gabarito_fecha_as_contas(base):
    g = gimi.gabarito(base)
    assert sum(g["vendido_por_tipo_venda"].values()) == pytest.approx(g["vendido_total"], abs=0.05)
    assert sum(g["vendido_por_vendedor"].values()) == pytest.approx(g["vendido_total"], abs=0.05)
    assert sum(g["vendido_por_empresa"].values()) == pytest.approx(g["vendido_total"], abs=0.05)
    assert sum(g["funil"].values()) == g["carteira_linhas"] and 0 < g["taxa_conversao_pct"] < 100
    cart = gimi.carteira(base)
    assert not cart["cliente_nome"].str.contains("TESTE").any() and cart["id"].is_unique and (cart["valores_produtos"] > 0).all()


def test_api_simulada_entrega_pelo_conector_com_paginacao_real(base):
    sim = Simulador("iapp", dados_base=base["alfa"])
    leitor = Leitor("iapp", {"token": "t", "secret": "s"}, cliente=httpx.Client(transport=sim.transporte()), relogio=sim.relogio)
    ext = leitor.extrair("contratos")
    assert len(ext.registros) == len(base["alfa"]["contratos"])  # repetidos chegam: deduplicar é trabalho da silver
    assert leitor.chamadas >= len(ext.registros) // 50  # páginas de 50 (o "offset" da IApp é o tamanho da página)
    assert ext.registros[0]["produtos"][0]["produto"]["codigo"] == base["alfa"]["contratos"][0]["produtos"][0]["produto"]["codigo"]
    for ent in ("funcionarios", "vendedores", "grupos", "tarefas", "usuarios", "clientes"):
        assert len(leitor.extrair(ent).registros) == len(base["alfa"][ent])


def test_exportar(base, tmp_path):
    cont = gimi.exportar(base, tmp_path)
    assert cont["alfa/contratos"] == len(base["alfa"]["contratos"])
    assert {p.name for p in tmp_path.iterdir()} >= {"bruto", "contratos.csv", "itens.csv", "funcionarios.csv", "gabarito.json"}


def test_geografia_no_contrato_sem_mudar_os_totais():
    """LST-51: estado e região do cliente e da obra no contrato bruto; os totais conferidos pelo Tiago não mudam."""
    base = gimi.gerar(36, 3000)
    g = gimi.gabarito(base)
    assert (g["vendido_total"], g["orcado_total"]) == (211290267.16, 532781125.76)  # os mesmos de antes da geografia
    c = base["alfa"]["contratos"][0]
    assert {"cidade", "estado", "regiao"} <= set(c["cliente"]) and {"cidade", "estado", "regiao"} <= set(c["projeto"])
    planos = gimi.contratos_planos(base)
    ok = planos.dropna(subset=["projeto_estado"])
    assert (ok["projeto_regiao"] == ok["projeto_estado"].map(gimi.REGIOES)).all()  # região coerente com a UF
    assert all(cid in gimi.CIDADES[uf] for cid, uf in zip(ok["projeto_cidade"], ok["projeto_estado"], strict=True))
    assert 0 < planos["projeto_estado"].isna().mean() < .06  # obra sem local existe, como no sistema de origem
    assert round(sum(g["vendido_por_regiao"].values()) + g["vendido_sem_local"], 2) == g["vendido_total"]
    assert set(g["vendido_por_regiao"]) == {"Centro-Oeste", "Sudeste", "Sul", "Nordeste", "Norte"}
