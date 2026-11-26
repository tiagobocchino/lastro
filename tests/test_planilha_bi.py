"""LST-48: tabelas prontas do BI numa planilha Google do cliente (Sheets API simulada)."""

from datetime import date
from decimal import Decimal

import httpx

from lastro import planilha_bi
from tests.google_falso import GoogleFalso


def _planilha(g: GoogleFalso) -> planilha_bi.Planilha:
    http = httpx.Client(transport=g.transporte())
    estado = {"t": g.token_valido}

    def token(forcar: bool = False) -> str:
        if forcar:
            http.post("https://oauth2.googleapis.com/token", data={"grant_type": "refresh_token"})
            estado["t"] = g.token_valido
        return estado["t"]

    return planilha_bi.Planilha(http, token)


def test_cria_planilha_uma_aba_por_tabela_tamanho_exato_e_sem_formula():
    g = GoogleFalso()
    tabelas = {
        "painel_7_vendas": (["vendedor", "data", "valor", "registros"],
                            [("Ana", date(2026, 1, 5), Decimal("10.50"), 1), (None, None, Decimal(2), 1), ("=HYPERLINK(1)", date(2026, 2, 1), 3, 1)]),
        "painel_10_rh": (["setor", "registros"], [("A", 1), ("B", 1)]),
    }
    r = planilha_bi.enviar(_planilha(g), tabelas, None, "Lastro · BI · t", "26/11/2026 10:00")
    p = g.planilhas[r["planilha_id"]]
    assert r["url"].endswith(f"/d/{r['planilha_id']}/edit") and p["titulo"] == "Lastro · BI · t"
    assert set(p["abas"]) == {"LEIA-ME", "painel_7_vendas", "painel_10_rh"}
    vendas = p["abas"]["painel_7_vendas"]
    assert (vendas["linhas"], vendas["colunas"]) == (4, 4)  # cabeçalho + 3 linhas, nada sobrando na grade
    assert vendas["valores"][0] == ["vendedor", "data", "valor", "registros"]
    assert vendas["valores"][1] == ["Ana", "2026-01-05", 10.5, 1] and vendas["valores"][2] == ["", "", 2.0, 1]
    assert vendas["valores"][3][0] == "=HYPERLINK(1)"  # gravado com RAW (o falso recusa outra coisa): fica texto
    assert [a["linhas"] for a in r["abas"]] == [2, 3] and r["avisos"] == []


def test_reenvio_reaproveita_a_planilha_encolhe_aba_e_remove_so_as_abas_do_lastro():
    g = GoogleFalso()
    pl = _planilha(g)
    r = planilha_bi.enviar(pl, {"painel_7_v": (["a"], [(1,), (2,), (3,)]), "painel_8_f": (["b"], [(1,)])}, None, "T", "x")
    pid = r["planilha_id"]
    g.planilhas[pid]["abas"]["minha aba"] = {"id": 999, "linhas": 5, "colunas": 2, "valores": [["meu cálculo"]]}  # aba do cliente
    r2 = planilha_bi.enviar(pl, {"painel_7_v": (["a"], [(9,)])}, pid, "T", "y")
    abas = g.planilhas[pid]["abas"]
    assert r2["planilha_id"] == pid and len(g.planilhas) == 1
    assert "painel_8_f" not in abas and abas["minha aba"]["valores"] == [["meu cálculo"]]  # a do cliente fica
    assert abas["painel_7_v"]["valores"] == [["a"], [9]] and abas["painel_7_v"]["linhas"] == 2  # encolheu: sem sobra da versão anterior


def test_planilha_apagada_pelo_cliente_vira_outra_e_token_vencido_renova():
    g = GoogleFalso()
    pl = _planilha(g)
    r = planilha_bi.enviar(pl, {"painel_1_x": (["a"], [(1,)])}, "planilhaQueNaoExisteMais0000", "T", "x")
    assert r["planilha_id"] in g.planilhas
    g.token_valido = "at-revogado"  # o Google invalidou o token no meio do caminho: 401 → renova uma vez e segue
    r2 = planilha_bi.enviar(pl, {"painel_1_x": (["a"], [(2,)])}, r["planilha_id"], "T", "y")
    assert g.renovacoes == 1 and g.planilhas[r2["planilha_id"]]["abas"]["painel_1_x"]["valores"] == [["a"], [2]]


def test_limite_de_celulas_deixa_tabela_fora_com_aviso(monkeypatch):
    monkeypatch.setattr(planilha_bi, "LIMITE_CELULAS", 10)
    g = GoogleFalso()
    r = planilha_bi.enviar(_planilha(g), {"painel_1_a": (["x", "y"], [(1, 2), (3, 4)]), "painel_2_b": (["z"], [(i,) for i in range(9)])}, None, "T", "x")
    assert [a["aba"] for a in r["abas"]] == ["painel_1_a"] and "painel_2_b" in r["avisos"][0]
