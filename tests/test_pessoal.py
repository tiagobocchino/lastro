"""LST-41: dado pessoal detectado pelo formato dos valores, sem acusar código de produto, CEP ou identificador."""

from __future__ import annotations

import importlib
import random

import pandas as pd
import pytest

from lastro.pessoal import cnpj_valido, cpf_valido, detectar, telefone_valido


def gerar_cpf(rng: random.Random) -> str:
    d = [rng.randint(0, 9) for _ in range(9)]
    for n in (9, 10):
        d.append((sum(d[i] * (n + 1 - i) for i in range(n)) * 10 % 11) % 10)
    return "".join(map(str, d))


def gerar_cnpj(rng: random.Random) -> str:
    d = [rng.randint(0, 9) for _ in range(8)] + [0, 0, 0, 1]
    for pesos in ([5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2], [6, 5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]):
        r = sum(x * p for x, p in zip(d, pesos)) % 11
        d.append(0 if r < 2 else 11 - r)
    return "".join(map(str, d))


RNG = random.Random(41)
CPFS = [gerar_cpf(RNG) for _ in range(60)]
CNPJS = [gerar_cnpj(RNG) for _ in range(60)]


def test_digitos_verificadores():
    assert cpf_valido("529.982.247-25") and not cpf_valido("529.982.247-26") and not cpf_valido("111.111.111-11")
    assert cnpj_valido("11.222.333/0001-81") and not cnpj_valido("11.222.333/0001-82")
    assert telefone_valido("(61) 99952-0802") and telefone_valido("+55 11 3333-4444") and not telefone_valido("(10) 99999-0000")


@pytest.mark.parametrize(("valores", "numerico", "esperado"), [
    ([f"{c[:3]}.{c[3:6]}.{c[6:9]}-{c[9:]}" for c in CPFS], False, "cpf"),  # formatado
    (CPFS, False, "cpf"),  # só dígitos
    ([str(int(c)) for c in CPFS], True, "cpf"),  # lido como número: zero à esquerda perdido
    ([f"{c[:2]}.{c[2:5]}.{c[5:8]}/{c[8:12]}-{c[12:]}" for c in CNPJS], False, "cnpj"),
    ([f"pessoa{i}@empresa.com.br" for i in range(30)], False, "email"),
    ([f"(61) 9{RNG.randint(1000, 9999)}-{RNG.randint(1000, 9999)}" for _ in range(30)], False, "telefone"),
    ([f"119{RNG.randint(10_000_000, 99_999_999)}" for _ in range(30)], False, "telefone"),
    # falsos positivos comuns: nada disso é dado pessoal
    ([str(RNG.randint(10**10, 10**11 - 1)) for _ in range(200)], False, None),  # código de produto de 11 dígitos
    ([str(RNG.randint(10**13, 10**14 - 1)) for _ in range(200)], False, None),  # código de 14 dígitos
    ([str(i) for i in range(1, 300)], True, None),  # id sequencial
    ([f"{RNG.randint(10000, 99999)}-{RNG.randint(100, 999)}" for _ in range(50)], False, None),  # CEP
    ([f"{RNG.uniform(100, 99999):.2f}" for _ in range(50)], True, None),  # valores
    (["2026-01-10", "2026-02-11", "2026-03-05"], False, None),  # datas
    (["Norte", "Sul", "Leste"], False, None),
    (CPFS[:10] + [f"COD-{i}" for i in range(10)], False, None),  # metade CPF não basta (limiar de 80%)
    (CPFS[:1], False, None),  # um valor só não decide
])
def test_detecta_pelo_formato(valores, numerico, esperado):
    assert detectar(valores, numerico=numerico) == esperado


@pytest.fixture
def api(monkeypatch, tmp_path):
    from fastapi.testclient import TestClient

    monkeypatch.setenv("LASTRO_HOME", str(tmp_path / "home"))
    monkeypatch.setenv("LASTRO_DEMO", "1")
    monkeypatch.setenv("LASTRO_DEMO_DIR", str(tmp_path / "demo"))
    monkeypatch.delenv("LASTRO_BANCO_URL", raising=False)
    import lastro.api as modulo

    modulo = importlib.reload(modulo)
    return TestClient(modulo.app)


def _planilha() -> bytes:
    n = 40
    df = pd.DataFrame({
        "cliente_doc": CPFS[:n],  # o nome não diz "cpf": a detecção é pelo valor
        "contato": [f"cliente{i}@gmail.com" for i in range(n)],
        "regiao": [["Norte", "Sul", "Leste", "Oeste"][i % 4] for i in range(n)],
        "receita": [100 + i for i in range(n)],
        "data": pd.date_range("2026-01-01", periods=n, freq="7D").strftime("%Y-%m-%d"),
    })
    return df.to_csv(index=False).encode()


def test_visitante_avisado_e_colunas_pessoais_fora_do_painel(api):
    c = api
    s = c.post("/api/demo/sessoes", files={"arquivo": ("clientes.csv", _planilha())}).json()
    papeis = {col["nome"]: col["papel"] for col in s["perfil"]["colunas"]}
    assert papeis["cliente_doc"] == "pessoal" and papeis["contato"] == "pessoal" and papeis["regiao"] == "texto"
    assert any("cliente_doc" in a and "CPF" in a for a in s["avisos"]) and any("contato" in a and "e-mail" in a for a in s["avisos"])
    opcoes = [o for q in s["perguntas"] for o in q["opcoes"]]
    assert "cliente_doc" not in opcoes and "contato" not in opcoes and "regiao" in opcoes
    for formato in ("tabela",):
        p = c.post(f"/api/demo/sessoes/{s['sessao']}/painel", json={"respostas": {"demo:formato": formato}}).json()
        assert "regiao" in p["html"].lower() or "Norte" in p["html"]
        assert CPFS[0] not in p["html"] and "cliente0@gmail.com" not in p["html"]  # nenhum valor pessoal no painel


def test_exemplo_nao_tem_falso_alarme(api):
    s = api.post("/api/demo/sessoes", data={"exemplo": "true"}).json()
    assert s["avisos"] == [] and all(col["papel"] != "pessoal" for col in s["perfil"]["colunas"])


def test_produto_avisa_no_rastro_e_nao_guarda_cpf_na_nota(monkeypatch, tmp_path):
    from lastro.banco import BancoSqlite
    from lastro.config import carregar
    from lastro.servico import Plataforma

    monkeypatch.setenv("LASTRO_HOME", str(tmp_path))
    cfg = carregar()
    b = BancoSqlite(cfg.banco)
    b.criar_tenant("acme", "Acme")
    repo = b.repo("acme", "adm@acme", "admin")
    arq = cfg.pasta_tenant("acme") / "fontes" / "clientes.csv"
    arq.parent.mkdir(parents=True)
    arq.write_bytes(_planilha())
    fid = repo.adicionar_fonte("clientes", "arquivo", str(arq))
    p = Plataforma(cfg, repo)
    d = p.abrir("adm@acme", "Quanto de receita por região?", [fid])
    eventos = {e["acao"]: e["detalhe"] for e in repo.eventos(d["id"])}
    assert "dados_pessoais" in eventos and "cliente_doc" in eventos["dados_pessoais"] and "CPF" in eventos["dados_pessoais"]
    assert CPFS[0] not in str(repo.eventos(d["id"]))  # o rastro tem o nome da coluna, nunca o valor
    notas = "".join(f.read_text() for f in (p.pasta / "caixa").rglob("*.md"))
    assert "(dado pessoal: CPF)" in notas and CPFS[0] not in notas and "cliente0@gmail.com" not in notas
    # o resto do produto não muda: a demanda segue e roda normalmente
    d = p.executar(p.responder_grill(d["id"], "adm@acme", {"geral:revisor": "Rui"})["id"], "adm@acme")
    assert d["status"] == "em_revisao"
