"""LST-6: Postgres do Supabase com RLS. Roda com LASTRO_TESTE_PG apontando para um Postgres
onde o teste possa criar bancos (ex.: postgresql://postgres@localhost:54329/postgres)."""

from __future__ import annotations

import json
import os
import shutil
import uuid
from pathlib import Path

import pytest

from lastro.banco import BancoSqlite
from lastro.config import RAIZ, carregar
from lastro.servico import Plataforma

PG = os.environ.get("LASTRO_TESTE_PG", "")
pytestmark = pytest.mark.skipif(not PG, reason="defina LASTRO_TESTE_PG para testar o Postgres")
MIGRACOES = [RAIZ / "supabase" / "teste" / "auth_simulado.sql", *sorted((RAIZ / "supabase" / "migrations").glob("*.sql"))]
EXEMPLO = RAIZ / "exemplos" / "orcamentos.csv"


@pytest.fixture(scope="module")
def url_pg():
    import psycopg

    nome = f"lastro_t_{uuid.uuid4().hex[:8]}"
    with psycopg.connect(PG, autocommit=True) as adm:
        adm.execute(f"CREATE DATABASE {nome}")
    url = PG.rsplit("/", 1)[0] + f"/{nome}"
    with psycopg.connect(url, autocommit=True) as con:
        for arq in MIGRACOES:
            con.execute(arq.read_text())
    yield url
    with psycopg.connect(PG, autocommit=True) as adm:
        adm.execute(f"DROP DATABASE {nome} WITH (FORCE)")


@pytest.fixture
def banco_pg(url_pg):
    from lastro.banco_postgres import BancoPostgres

    b = BancoPostgres(url_pg, max_conexoes=12)
    yield b
    b.fechar()


@pytest.fixture(params=["sqlite", "postgres"])
def banco(request, tmp_path):
    if request.param == "sqlite":
        b = BancoSqlite(tmp_path / "lastro.db")
    else:
        b = request.getfixturevalue("banco_pg")
    sufixo = uuid.uuid4().hex[:6]
    a, o = f"acme{sufixo}", f"outra{sufixo}"
    for t in (a, o):
        b.criar_tenant(t, t.title())
    return b, a, o


# --- Mesma interface nos dois bancos ---------------------------------------------------

def test_repo_faz_o_mesmo_nos_dois_bancos(banco):
    b, a, _ = banco
    r = b.repo(a, f"ana@{a}", "admin")
    fid = r.adicionar_fonte("orcamentos", "arquivo", "/x.csv")
    did = r.criar_demanda(f"ana@{a}", "Quanto vendemos?", [fid])
    r.atualizar_demanda(did, status="grill", respostas={"orcamentos:medida": "valor_vendido"})
    r.registrar("ana", "abriu_demanda", {"fontes": [fid]}, did)
    d = r.demanda(did)
    assert d["status"] == "grill" and d["fontes"] == [fid] and d["respostas"] == {"orcamentos:medida": "valor_vendido"}
    assert [x["id"] for x in r.demandas()] == [did]
    ev = r.eventos(did)
    assert ev[0]["acao"] == "abriu_demanda" and json.loads(ev[0]["detalhe"]) == {"fontes": [fid]}
    assert isinstance(ev[0]["em"], float)


def test_outro_tenant_nao_ve_nem_usa_nada(banco):
    b, a, o = banco
    ra = b.repo(a, f"ana@{a}", "admin")
    fid = ra.adicionar_fonte("orcamentos", "arquivo", "/x.csv")
    did = ra.criar_demanda(f"ana@{a}", "Quanto vendemos?", [fid])
    ro = b.repo(o, f"zed@{o}", "admin")
    assert ro.fontes() == [] and ro.demandas() == [] and ro.demanda(did) is None
    with pytest.raises(PermissionError):
        ro.criar_demanda(f"zed@{o}", "pergunta", [fid])


def test_login_proprio_nos_dois_bancos(banco):
    b, a, _ = banco
    b.criar_usuario(a, "Rui@Acme.com", "Rui", "revisor", "senha123")
    u = b.autenticar("rui@acme.com", "senha123")
    assert u["tenant_id"] == a and u["papel"] == "revisor"
    assert b.autenticar("rui@acme.com", "errada") is None


# --- RLS direto no SQL, com dois tokens (sem o filtro por tenant do Repo) -----------------

@pytest.fixture
def dois_tokens(banco_pg):
    from lastro.banco_postgres import claims

    a, o = f"a{uuid.uuid4().hex[:6]}", f"b{uuid.uuid4().hex[:6]}"
    for t in (a, o):
        banco_pg.criar_tenant(t, t)
        r = banco_pg.repo(t, f"adm@{t}", "admin")
        fid = r.adicionar_fonte("f", "arquivo", "/f.csv")
        r.registrar("adm", "x", {}, r.criar_demanda(f"adm@{t}", "p", [fid]))

    def como(tenant: str, papel: str = "admin", email: str | None = None):
        con = banco_pg.pool.getconn()
        con.execute("SET ROLE authenticated")
        con.execute("SELECT set_config('request.jwt.claims', %s, false)", (claims(tenant, email or f"adm@{tenant}", papel),))
        con.commit()  # papel e claims de sessão sobrevivem aos rollbacks dos erros esperados
        return con

    abertas = []

    def abrir(*args, **kw):
        con = como(*args, **kw)
        abertas.append(con)
        return con

    yield a, o, abrir
    for con in abertas:
        con.rollback()
        con.execute("RESET ROLE")
        con.execute("RESET request.jwt.claims")
        con.commit()
        banco_pg.pool.putconn(con)


def test_rls_select_so_devolve_o_proprio_tenant(dois_tokens):
    a, o, como = dois_tokens
    con = como(a)
    for tabela in ("fontes", "demandas", "eventos", "tenants"):
        coluna = "id" if tabela == "tenants" else "tenant_id"
        vistos = {r[coluna] for r in con.execute(f"SELECT {coluna} FROM {tabela}").fetchall()}
        assert vistos == {a}, tabela


def test_rls_nao_grava_nem_altera_outro_tenant(dois_tokens):
    import psycopg

    a, o, como = dois_tokens
    con = como(a)
    with pytest.raises(psycopg.errors.InsufficientPrivilege):
        con.execute("INSERT INTO fontes (tenant_id, nome, tipo, caminho) VALUES (%s,'x','arquivo','/x')", (o,))
    con.rollback()
    con.execute("SET ROLE authenticated")
    alteradas = con.execute("UPDATE demandas SET status='aprovada' WHERE tenant_id=%s", (o,)).rowcount
    assert alteradas == 0
    with pytest.raises(psycopg.errors.InsufficientPrivilege):
        con.execute("INSERT INTO eventos (tenant_id, ator, acao, detalhe) VALUES (%s,'x','x','{}')", (o,))
    con.rollback()
    con.execute("SET ROLE authenticated")
    with pytest.raises(psycopg.errors.InsufficientPrivilege):  # mover a própria demanda para outro tenant
        con.execute("UPDATE demandas SET tenant_id=%s WHERE tenant_id=%s", (o, a))


def test_rls_respeita_papel_e_autor(dois_tokens):
    import psycopg

    a, _, como = dois_tokens
    dem = como(a, "demandante", f"ana@{a}")
    with pytest.raises(psycopg.errors.InsufficientPrivilege):  # só admin conecta fonte
        dem.execute("INSERT INTO fontes (tenant_id, nome, tipo, caminho) VALUES (%s,'x','arquivo','/x')", (a,))
    dem.rollback()
    dem.execute("SET ROLE authenticated")
    with pytest.raises(psycopg.errors.InsufficientPrivilege):  # não abre demanda em nome de outro
        dem.execute("INSERT INTO demandas (tenant_id, autor, pergunta, fontes, status) VALUES (%s,'outro@x','p','{}','nova')", (a,))
    leitor = como(a, "leitor")
    assert leitor.execute("UPDATE demandas SET status='aprovada'").rowcount == 0


def test_rls_fecha_senhas_rastro_e_chave_anon(dois_tokens):
    import psycopg

    a, _, como = dois_tokens
    for sql in ("SELECT * FROM usuarios", "DELETE FROM eventos", "DELETE FROM demandas", "INSERT INTO tenants (id, nome) VALUES ('z','z')"):
        con = como(a)
        with pytest.raises(psycopg.errors.InsufficientPrivilege):
            con.execute(sql)
    anon = como(a)
    anon.execute("SET ROLE anon")
    for tabela in ("tenants", "fontes", "demandas", "eventos", "usuarios", "perfis"):
        with pytest.raises(psycopg.errors.InsufficientPrivilege):
            anon.execute(f"SELECT 1 FROM {tabela}")
        anon.rollback()
        anon.execute("SET ROLE anon")


# --- Ciclo completo de uma demanda no Postgres ------------------------------------------

def test_ciclo_completo_no_postgres(banco_pg, monkeypatch, tmp_path: Path):
    monkeypatch.setenv("LASTRO_HOME", str(tmp_path))
    cfg = carregar()
    t = f"c{uuid.uuid4().hex[:6]}"
    banco_pg.criar_tenant(t, t)
    destino = cfg.pasta_tenant(t) / "fontes" / "orcamentos.csv"
    destino.parent.mkdir(parents=True)
    shutil.copy(EXEMPLO, destino)
    fid = banco_pg.repo(t, f"adm@{t}", "admin").adicionar_fonte("orcamentos", "arquivo", str(destino))

    ana = Plataforma(cfg, banco_pg.repo(t, f"ana@{t}", "demandante"))
    d = ana.abrir(f"ana@{t}", "Quanto cada vendedor vendeu, em valor vendido, nos contratos fechados?", [fid])
    d = ana.executar(ana.responder_grill(d["id"], f"ana@{t}", {"geral:revisor": "Rui"})["id"], f"ana@{t}")
    assert d["status"] == "em_revisao" and d["resultado"]["auditoria"]["aprovado_camada1"]
    assert d["resultado"]["resposta"]["total"] == pytest.approx(14030477.92, abs=0.01)

    rui = Plataforma(cfg, banco_pg.repo(t, f"rui@{t}", "revisor"))
    d = rui.revisar(d["id"], f"rui@{t}", True, "Confere com o notebook.")
    assert d["status"] == "aprovada"
    acoes = [e["acao"] for e in banco_pg.repo(t, f"ana@{t}", "leitor").eventos(d["id"])]
    assert acoes[0] == "abriu_demanda" and acoes[-1] == "revisou"


# --- LST-9: cofre no Vault --------------------------------------------------------------

def test_cofre_supabase_guarda_atualiza_e_authenticated_nao_le(banco_pg):
    import psycopg

    from lastro.cofre import CofreSupabase

    cofre = CofreSupabase(banco_pg)
    nome = f"lastro:t{uuid.uuid4().hex[:6]}:oauth:contaazul"
    cofre.guardar(nome, '{"refresh_token": "rt-1"}')
    cofre.guardar(nome, '{"refresh_token": "rt-2"}')  # rotação: atualiza, não duplica
    assert cofre.ler(nome) == '{"refresh_token": "rt-2"}' and cofre.ler("nao-existe") is None
    with banco_pg.repo("acme", "adm@acme", "admin")._con() as con:  # noqa: SLF001
        with pytest.raises(psycopg.errors.InsufficientPrivilege):
            con.execute("SELECT * FROM vault.decrypted_secrets")
