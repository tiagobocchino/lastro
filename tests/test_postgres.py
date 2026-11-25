"""LST-6: Postgres do Supabase com RLS. Roda com LASTRO_TESTE_PG apontando para um Postgres
onde o teste possa criar bancos (ex.: postgresql://postgres@localhost:54329/postgres)."""

from __future__ import annotations

import json
import os
import shutil
import uuid
from decimal import Decimal
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
        tem_cron = con.execute("SELECT 1 FROM pg_available_extensions WHERE name='pg_cron'").fetchone()
        for arq in MIGRACOES:
            if "pg_cron" in arq.read_text() and not tem_cron:
                continue  # agenda do Supabase (plano C): o Postgres local não tem a extensão
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


# --- LST-7: cargas agendadas --------------------------------------------------------------

def test_cargas_mesma_interface_e_isoladas(banco):
    b, a, o = banco
    ra = b.repo(a, f"adm@{a}", "admin")
    fid = ra.adicionar_fonte("sienge_contratos", "arquivo", "/x.csv")
    cid = ra.criar_carga(fid, "sienge", "contratos_venda", {"subdominio": "acme"}, hora=7, cota_diaria=100)
    ra.atualizar_carga(cid, ultimo_status="ok", marca_dagua=123.5, dia_cota="2026-11-24", chamadas_no_dia=3)
    c = ra.carga(cid)
    assert (c["saas"], c["variaveis"], c["hora"], c["cota_diaria"], c["marca_dagua"], c["chamadas_no_dia"], c["ativa"]) == (
        "sienge", {"subdominio": "acme"}, 7, 100, 123.5, 3, True)
    ro = b.repo(o, f"zed@{o}", "admin")
    assert ro.cargas() == [] and ro.carga(cid) is None
    with pytest.raises(PermissionError):
        ro.criar_carga(fid, "sienge", "contratos_venda", {})
    assert cid in {x["id"] for x in b.cargas_ativas()}  # o executor (dono) vê todas as empresas


def test_rls_carga_so_admin_cria_e_ninguem_mexe_na_de_outro(dois_tokens, banco_pg):
    import psycopg

    a, o, como = dois_tokens
    fid_o = banco_pg.repo(o, f"adm@{o}", "admin").fontes()[0]["id"]
    banco_pg.repo(o, f"adm@{o}", "admin").criar_carga(fid_o, "sienge", "clientes", {})
    con = como(a)
    assert con.execute("SELECT count(*) AS n FROM cargas WHERE tenant_id=%s", (o,)).fetchone()["n"] == 0
    assert con.execute("UPDATE cargas SET ativa=false WHERE tenant_id=%s", (o,)).rowcount == 0
    dem = como(a, "demandante", f"ana@{a}")
    fid_a = banco_pg.repo(a, f"adm@{a}", "admin").fontes()[0]["id"]
    with pytest.raises(psycopg.errors.InsufficientPrivilege):
        dem.execute("INSERT INTO cargas (tenant_id, fonte_id, saas, entidade) VALUES (%s,%s,'sienge','clientes')", (a, fid_a))


def test_contas_nos_dois_bancos(banco):
    """LST-32: senha provisória obriga a troca; um admin não toma o e-mail de outra empresa."""
    from lastro.banco import SenhaInvalida

    b, a, o = banco
    b.criar_usuario(a, f"ana@{a}", "Ana", "demandante", "senha-da-ana-forte")
    prov = b.senha_provisoria(a, f"rui@{a}", "Rui", "revisor")
    assert bool(b.autenticar(f"rui@{a}", prov)["trocar_senha"]) is True
    assert b.trocar_senha(f"rui@{a}", "errada-qualquer-coisa", "nova-senha-bem-longa") is False
    with pytest.raises(SenhaInvalida):
        b.trocar_senha(f"rui@{a}", prov, "curta")
    assert b.trocar_senha(f"rui@{a}", prov, "nova-senha-bem-longa") is True
    assert bool(b.autenticar(f"rui@{a}", "nova-senha-bem-longa")["trocar_senha"]) is False
    with pytest.raises(PermissionError):
        b.senha_provisoria(o, f"ana@{a}", "Ana", "admin")
    with pytest.raises(PermissionError):
        b.criar_usuario(o, f"ana@{a}", "Ana", "admin", "outra-senha-longa")
    assert b.autenticar(f"ana@{a}", "senha-da-ana-forte")["tenant_id"] == a
    assert [u["email"] for u in b.usuarios(o)] == []
    assert [u["email"] for u in b.usuarios(a)] == [f"ana@{a}", f"rui@{a}"]


# --- Monitoramento (LST-26) -------------------------------------------------------------

@pytest.fixture
def monitor(url_pg):
    import psycopg

    con = psycopg.connect(url_pg, autocommit=True)
    for t in ("interno.alertas", "interno.verificacoes", "interno.emails", "interno.metricas_api", "net.pedidos", "net._http_response"):
        con.execute(f"TRUNCATE {t}")
    con.execute("DELETE FROM vault.secrets WHERE name LIKE 'lastro_%'")
    con.execute("SELECT vault.create_secret('https://api.exemplo', 'lastro_url_api')")
    yield con
    con.close()


def _responder(con, status: int, corpo: str = '{"estado":"ok","banco":"ok"}') -> None:
    pedido = con.execute("SELECT max(pedido) FROM interno.verificacoes").fetchone()[0]
    con.execute("INSERT INTO net._http_response (id, status_code, content) VALUES (%s, %s, %s)", (pedido, status, corpo))


def _alertas(con) -> dict:
    return dict(con.execute("SELECT tipo, fechado_em IS NULL FROM interno.alertas").fetchall())


def test_api_fora_do_ar_abre_alerta_e_fecha_quando_volta(monitor):
    con = monitor
    con.execute("SELECT interno.monitorar()")
    url, = con.execute("SELECT url FROM net.pedidos WHERE metodo='GET'").fetchone()
    assert url == "https://api.exemplo/saude"
    _responder(con, 503, "")
    con.execute("SELECT interno.monitorar()")
    assert _alertas(con) == {}  # uma falha só não é queda
    _responder(con, 200, '{"estado":"ok","banco":"erro"}')  # respondeu, mas sem banco: também é falha
    con.execute("SELECT interno.monitorar()")
    assert _alertas(con) == {"fora_do_ar": True}
    assert con.execute("SELECT enviado FROM interno.emails").fetchall() == [(False,)]  # sem Resend: fica no painel
    con.execute("SELECT vault.create_secret('re_chave_falsa', 'lastro_resend_chave')")
    con.execute("SELECT vault.create_secret('alertas@exemplo.com', 'lastro_alerta_email')")
    _responder(con, 200)
    con.execute("SELECT interno.monitorar()")
    assert _alertas(con) == {"fora_do_ar": False}
    url, corpo, cab = con.execute("SELECT url, corpo, cabecalhos FROM net.pedidos WHERE metodo='POST'").fetchone()
    assert url == "https://api.resend.com/emails" and corpo["to"] == ["alertas@exemplo.com"]
    assert cab["Authorization"] == "Bearer re_chave_falsa" and "normalizado" in corpo["subject"]
    assert con.execute("SELECT disponibilidade_pct FROM painel.disponibilidade_dia").fetchone()[0] == pytest.approx(Decimal("33.33"))


def test_pedido_sem_resposta_vira_falha(monitor):
    con = monitor
    con.execute("SELECT interno.monitorar()")
    con.execute("UPDATE interno.verificacoes SET em = now() - interval '5 minutes'")
    con.execute("SELECT interno.monitorar()")
    assert con.execute("SELECT ok FROM interno.verificacoes WHERE resolvida").fetchall() == [(False,)]


def test_taxa_de_5xx_e_limite_gratuito(monitor, banco_pg):
    con = monitor
    for i in range(30):
        banco_pg.registrar_metrica(500 if i < 3 else 200, 40)
    assert banco_pg.metricas()[0]["requisicoes"] == 30
    con.execute("SELECT interno.avaliar_alertas()")
    assert _alertas(con) == {"erros_5xx": True}  # 3 de 30 = 10%, acima de 5%
    con.execute("UPDATE interno.limites SET valor = 0.001 WHERE nome = 'banco_mb'")
    try:
        con.execute("SELECT interno.avaliar_alertas()")
        assert _alertas(con)["banco_cheio"] is True
    finally:
        con.execute("UPDATE interno.limites SET valor = 500 WHERE nome = 'banco_mb'")
    r = con.execute("SELECT requisicoes, erros_5xx, taxa_5xx FROM painel.requisicoes_dia").fetchone()
    assert r[0] == 30 and r[1] == 3 and float(r[2]) == 0.1


def test_painel_leitor_so_le_as_views(monitor, url_pg):
    import psycopg

    con = monitor
    with psycopg.connect(url_pg) as leitor:
        leitor.execute("SET ROLE painel_leitor")
        for v in ("requisicoes_dia", "disponibilidade_dia", "demandas_dia", "cargas", "uso_gratuito", "alertas"):
            leitor.execute(f"SELECT * FROM painel.{v}").fetchall()
        for proibido in ("SELECT * FROM interno.metricas_api", "SELECT * FROM public.usuarios", "SELECT interno.monitorar()",
                         "SELECT * FROM vault.decrypted_secrets"):
            with pytest.raises(psycopg.errors.InsufficientPrivilege):
                leitor.execute(proibido)
            leitor.rollback()
            leitor.execute("SET ROLE painel_leitor")
    assert con.execute("SELECT rolcanlogin FROM pg_roles WHERE rolname='painel_leitor'").fetchone() == (False,)


def test_painel_html_a_partir_do_banco(monitor, url_pg, banco_pg):
    from lastro.painel import gerar

    banco_pg.registrar_metrica(200, 120)
    h = gerar(url_pg)
    assert "Operação do Lastro" in h and "storage" in h and "banco" in h


# --- BI self-service por empresa (LST-33) ---------------------------------------------------

def _empresa_com_gold(banco_pg, cfg, aprovar: bool = True):
    t = f"b{uuid.uuid4().hex[:6]}"
    banco_pg.criar_tenant(t, t)
    destino = cfg.pasta_tenant(t) / "fontes" / "orçamentos 2025.csv"
    destino.parent.mkdir(parents=True)
    shutil.copy(EXEMPLO, destino)
    adm = banco_pg.repo(t, f"adm@{t}", "admin")
    fid = adm.adicionar_fonte("Orçamentos 2025", "arquivo", str(destino))
    plat = Plataforma(cfg, adm)
    d = plat.abrir(f"adm@{t}", "Quanto cada vendedor vendeu, em valor vendido, nos contratos fechados?", [fid])
    d = plat.executar(plat.responder_grill(d["id"], f"adm@{t}", {"geral:revisor": "Rui"})["id"], f"adm@{t}")
    if aprovar:
        plat.revisar(d["id"], f"adm@{t}", True, "ok")
    return t, adm, plat, d["id"]


def _entrar_como(url_pg: str, cred: dict, senha: str | None = None):
    import psycopg

    base = psycopg.conninfo.conninfo_to_dict(url_pg)
    return psycopg.connect(host="127.0.0.1", port=base.get("port", 5432), dbname=base["dbname"],
                           user=cred["usuario"], password=cred["senha"] if senha is None else senha, autocommit=True)


def test_bi_publica_fontes_e_gold_e_isola_as_empresas(banco_pg, url_pg, monkeypatch, tmp_path: Path):
    import psycopg

    from lastro.bi import AcessoBI

    monkeypatch.setenv("LASTRO_HOME", str(tmp_path))
    cfg = carregar()
    a, repo_a, plat_a, did = _empresa_com_gold(banco_pg, cfg)
    o, repo_o, plat_o, _ = _empresa_com_gold(banco_pg, cfg, aprovar=False)
    bi = AcessoBI(banco_pg, url_pg)
    cred_a, cred_o = bi.gerar_credencial(a), bi.gerar_credencial(o)
    assert a not in cred_a["usuario"] and cred_a["usuario"].startswith("bi_")  # nome opaco: não revela a empresa
    pub = bi.publicar(a, repo_a, plat_a.pasta)
    bi.publicar(o, repo_o, plat_o.pasta)
    nomes = {t["tabela"]: t["linhas"] for t in pub["tabelas"]}
    linhas_csv = len(EXEMPLO.read_text(encoding="utf-8").splitlines()) - 1
    assert nomes["fonte_orcamentos_2025"] == linhas_csv and pub["avisos"] == []
    assert {f"d{did}_fato", f"d{did}_silver"} <= set(nomes) and any(n.startswith(f"d{did}_dim_") for n in nomes)

    with _entrar_como(url_pg, cred_a) as c:
        # o BI enxerga só o próprio schema, já no search_path
        assert c.execute("SELECT count(*) FROM fonte_orcamentos_2025").fetchone()[0] == linhas_csv
        assert c.execute(f"SELECT sum(valor_vendido) FROM d{did}_fato").fetchone()[0] is not None
        painel = next(n for n in nomes if n.startswith(f"painel_{did}_"))  # LST-46: tabela pronta, mesmo total da fato
        assert c.execute(f"SELECT round(sum(valor_vendido)::numeric, 2), sum(registros) FROM {painel}").fetchone() == \
            c.execute(f"SELECT round(sum(valor_vendido)::numeric, 2), count(*) FROM d{did}_fato").fetchone()
        visiveis = {r[0] for r in c.execute(
            "SELECT table_schema FROM information_schema.tables WHERE table_schema NOT IN ('pg_catalog','information_schema')")}
        assert visiveis == {cred_a["usuario"]}
        proibidos = [
            f"SELECT * FROM {cred_o['usuario']}.fonte_orcamentos_2025",  # outra empresa
            "SELECT * FROM public.usuarios", "SELECT * FROM public.demandas", "SELECT * FROM interno.bi_acessos",
            "SELECT * FROM vault.decrypted_secrets", "SELECT interno.monitorar()",
        ]
        for q in proibidos:
            with pytest.raises(psycopg.errors.InsufficientPrivilege):
                c.execute(q)
        with pytest.raises(psycopg.errors.ReadOnlySqlTransaction):  # 1ª trava: sessão só leitura
            c.execute("DELETE FROM fonte_orcamentos_2025")
        c.execute("SET default_transaction_read_only = off")
        for q in ("DELETE FROM fonte_orcamentos_2025", "CREATE TABLE x (a int)", "CREATE TABLE public.x (a int)"):
            with pytest.raises(psycopg.errors.InsufficientPrivilege):  # 2ª trava: sem privilégio de escrita
                c.execute(q)

    # a empresa sem demanda aprovada só tem a fonte
    with _entrar_como(url_pg, cred_o) as c:
        assert [r[0] for r in c.execute("SELECT table_name FROM information_schema.tables WHERE table_schema = current_schema()")] == ["fonte_orcamentos_2025"]


def test_bi_senha_troca_e_desliga(banco_pg, url_pg, monkeypatch, tmp_path: Path):
    import psycopg

    from lastro.bi import AcessoBI

    monkeypatch.setenv("LASTRO_HOME", str(tmp_path))
    t = f"s{uuid.uuid4().hex[:6]}"
    banco_pg.criar_tenant(t, t)
    bi = AcessoBI(banco_pg, url_pg)
    velha = bi.gerar_credencial(t)
    nova = bi.gerar_credencial(t)  # trocar a senha mantém usuário e schema
    assert nova["usuario"] == velha["usuario"] and nova["senha"] != velha["senha"] and len(nova["senha"]) >= 32
    exige_senha = True
    try:
        _entrar_como(url_pg, nova, senha="errada").close()
        exige_senha = False  # Postgres local em trust: a senha não é conferida
    except psycopg.OperationalError:
        pass
    if exige_senha:
        with pytest.raises(psycopg.OperationalError):
            _entrar_como(url_pg, velha)  # a senha antiga para de valer
    _entrar_como(url_pg, nova).close()
    assert bi.testar(nova | {"host": "127.0.0.1"})["ok"]
    assert not bi.testar(nova | {"host": "127.0.0.1", "senha": "errada"})["ok"] or not exige_senha
    bi.desligar(t)
    with pytest.raises(psycopg.OperationalError):
        _entrar_como(url_pg, nova)
    assert bi.acesso(t)["ativo"] is False
    assert "senha" not in bi.acesso(t) and nova["senha"] not in str(bi.acesso(t))  # a senha não fica no registro


def test_bi_publicacao_atomica_e_fonte_quebrada_vira_aviso(banco_pg, url_pg, monkeypatch, tmp_path: Path):
    from lastro.bi import AcessoBI

    monkeypatch.setenv("LASTRO_HOME", str(tmp_path))
    cfg = carregar()
    t = f"q{uuid.uuid4().hex[:6]}"
    banco_pg.criar_tenant(t, t)
    pasta = cfg.pasta_tenant(t) / "fontes"
    pasta.mkdir(parents=True)
    (pasta / "boa.csv").write_text("id,valor\n1,10\n2,20\n")
    (pasta / "ruim.parquet").write_text("isto não é parquet")
    repo = banco_pg.repo(t, "adm@x", "admin")
    repo.adicionar_fonte("boa", "arquivo", str(pasta / "boa.csv"))
    repo.adicionar_fonte("ruim", "arquivo", str(pasta / "ruim.parquet"))
    bi = AcessoBI(banco_pg, url_pg)
    cred = bi.gerar_credencial(t)
    r = bi.publicar(t, repo, cfg.pasta_tenant(t))
    assert [x["tabela"] for x in r["tabelas"]] == ["fonte_boa"] and "fonte ruim" in r["avisos"][0]
    (pasta / "boa.csv").write_text("id,valor\n1,10\n2,20\n3,30\n")
    bi.publicar(t, repo, cfg.pasta_tenant(t))
    with _entrar_como(url_pg, cred) as c:
        assert c.execute("SELECT count(*), sum(valor) FROM fonte_boa").fetchone() == (3, 60)
    assert bi.acesso(t)["tabelas"][0]["linhas"] == 3


def test_bi_conexao_pelo_pooler_do_supabase(banco_pg):
    from lastro.bi import AcessoBI

    url = "postgresql://postgres.abcdefghijklmnop:x@aws-1-sa-east-1.pooler.supabase.com:6543/postgres"
    c = AcessoBI(banco_pg, url).conexao("bi_0123456789")
    assert c == {"host": "aws-1-sa-east-1.pooler.supabase.com", "porta": 5432, "banco": "postgres",
                 "usuario": "bi_0123456789.abcdefghijklmnop", "ssl": "obrigatório"}


def test_bi_pelo_portal_no_postgres(url_pg, monkeypatch, tmp_path: Path):
    """Fluxo do admin: liga o BI, recebe a senha uma vez, a fonte já está lá; aprovação republica."""
    import importlib

    from fastapi.testclient import TestClient

    monkeypatch.setenv("LASTRO_HOME", str(tmp_path))
    monkeypatch.setenv("LASTRO_BANCO_URL", url_pg)
    import lastro.api as modulo

    modulo = importlib.reload(modulo)
    t = f"p{uuid.uuid4().hex[:6]}"
    modulo.banco.criar_tenant(t, t)
    modulo.banco.criar_usuario(t, f"adm@{t}", "Adm", "admin", "senha-longa-de-teste")
    modulo.banco.criar_usuario(t, f"ana@{t}", "Ana", "demandante", "senha-longa-de-teste")
    c = TestClient(modulo.app)

    def cab(email: str) -> dict:
        return {"Authorization": "Bearer " + c.post("/api/login", json={"email": email, "senha": "senha-longa-de-teste"}).json()["token"]}

    adm = cab(f"adm@{t}")
    assert c.get("/api/bi", headers=adm).json() == {"disponivel": True, "ligado": False}
    c.post("/api/fontes", headers=adm, files={"arquivo": ("orcamentos.csv", EXEMPLO.read_bytes(), "text/csv")})
    assert c.post("/api/bi/credencial", headers=cab(f"ana@{t}")).status_code == 403
    r = c.post("/api/bi/credencial", headers=adm).json()
    assert [x["tabela"] for x in r["publicado"]["tabelas"]] == ["fonte_orcamentos"]
    assert r["teste"]["ok"] and "1 tabelas visíveis, sessão só leitura: sim" in r["teste"]["detalhe"]
    estado = c.get("/api/bi", headers=adm).json()
    assert estado["ligado"] and estado["conexao"]["usuario"] == r["credencial"]["usuario"]
    assert r["credencial"]["senha"] not in str(estado)  # a senha não volta de novo
    with _entrar_como(url_pg, r["credencial"]) as con:
        assert con.execute("SELECT count(*) FROM fonte_orcamentos").fetchone()[0] > 0
    assert c.delete("/api/bi/credencial", headers=adm).json() == {"ligado": False}
    modulo.banco.fechar()


def test_funil_da_demo_no_postgres(monitor, banco_pg, url_pg):
    import psycopg

    con = monitor
    con.execute("TRUNCATE interno.demo_eventos")
    for etapa, campos in (("subiu", {"faixa_tamanho": "até 100 KB", "n_colunas": 9}), ("subiu", {}), ("painel", {"visual": "ranking", "duracao_ms": 800}),
                          ("clicou_contato", {"visual": "ranking"}), ("recusou", {"motivo": "limite_ip"})):
        banco_pg.registrar_demo(etapa, **campos)
    assert [e["etapa"] for e in banco_pg.eventos_demo()] == ["subiu", "subiu", "painel", "clicou_contato", "recusou"]
    linha = con.execute("SELECT subiram, paineis, clicaram, recusas, ms_medio_painel FROM painel.demo_funil_dia").fetchone()
    assert linha == (2, 1, 1, 1, 800)
    with pytest.raises(psycopg.errors.CheckViolation):  # texto livre não entra nem por SQL direto
        con.execute("INSERT INTO interno.demo_eventos (etapa, motivo) VALUES ('recusou', 'cpf do cliente 123')")
    with psycopg.connect(url_pg) as leitor:
        leitor.execute("SET ROLE painel_leitor")
        assert leitor.execute("SELECT count(*) FROM painel.demo_funil_dia").fetchone()[0] == 1
        with pytest.raises(psycopg.errors.InsufficientPrivilege):
            leitor.execute("SELECT * FROM interno.demo_eventos")


def test_bi_publicar_depois_do_disco_zerado_mantem_o_que_ja_estava(banco_pg, url_pg, monkeypatch, tmp_path: Path):
    """Deploy no Render zera o disco: publicar de novo não pode apagar o BI do cliente."""
    import shutil

    from lastro.bi import AcessoBI

    monkeypatch.setenv("LASTRO_HOME", str(tmp_path))
    cfg = carregar()
    a, repo_a, plat_a, did = _empresa_com_gold(banco_pg, cfg)
    bi = AcessoBI(banco_pg, url_pg)
    cred = bi.gerar_credencial(a)
    antes = {t["tabela"] for t in bi.publicar(a, repo_a, plat_a.pasta)["tabelas"]}
    shutil.rmtree(plat_a.pasta / "demandas")  # o disco do servidor foi zerado
    for f in repo_a.fontes():
        Path(f["caminho"]).unlink()
    r = bi.publicar(a, repo_a, plat_a.pasta)
    assert {t["tabela"] for t in r["tabelas"] if t.get("mantida")} == antes
    assert any(f"demanda {did}" in x for x in r["avisos"]) and any("fonte" in x for x in r["avisos"])
    with _entrar_como(url_pg, cred) as c:
        assert c.execute(f"SELECT count(*) FROM d{did}_fato").fetchone()[0] > 0
