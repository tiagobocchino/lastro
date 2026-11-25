"""API HTTP e portal. Login próprio; cada token carrega o tenant e o papel do usuário."""

from __future__ import annotations

import hmac
import html
import json
import logging
import os
import re
import time
from pathlib import Path
from typing import Annotated

import httpx
from fastapi import Depends, FastAPI, File, Form, Header, HTTPException, UploadFile
from fastapi.responses import FileResponse, HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from . import cargas
from .banco import (
    PAPEIS_QUE_DEMANDAM,
    PAPEIS_QUE_REVISAM,
    SenhaInvalida,
    abrir_banco,
    emitir_token,
    ler_token,
)
from .bi import AcessoBI, BIIndisponivel
from .cofre import abrir_cofre
from .conectores import EXTENSOES
from .config import carregar
from .espelho import abrir_espelho
from .politica import PermissaoNegada
from .saas import oauth
from .servico import Plataforma
from .somente_leitura import EscritaBloqueada

cfg = carregar()
log = logging.getLogger("lastro")
banco = abrir_banco(cfg)
cofre = abrir_cofre(cfg, banco)
espelho = abrir_espelho()
WEB = Path(__file__).parent / "web"
app = FastAPI(title="Lastro", version="0.1.0")


NAO_MEDIR = ("/saude", "/web/", "/favicon")


@app.middleware("http")
async def medir(request, call_next):
    """Conta requisições, 4xx, 5xx e latência por hora (LST-26). Falha ao gravar nunca derruba a resposta."""
    from starlette.concurrency import run_in_threadpool

    inicio = time.perf_counter()
    status = 500
    try:
        resposta = await call_next(request)
        status = resposta.status_code
        return resposta
    finally:
        if not request.url.path.startswith(NAO_MEDIR):
            ms = int((time.perf_counter() - inicio) * 1000)
            try:
                await run_in_threadpool(banco.registrar_metrica, status, ms)
            except Exception as e:  # noqa: BLE001
                log.warning("métrica não gravada: %s", type(e).__name__)


class Sessao(BaseModel):
    email: str
    tenant: str
    papel: str
    trocar_senha: bool = False


def sessao_para_troca(authorization: Annotated[str | None, Header()] = None) -> Sessao:
    """Aceita também quem está com senha provisória: só para trocar a senha e ver quem é."""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(401, "faça login")
    carga = ler_token(cfg.segredo, authorization[7:])
    if not carga:
        raise HTTPException(401, "sessão expirada")
    return Sessao(email=carga["e"], tenant=carga["t"], papel=carga["p"], trocar_senha=bool(carga.get("m")))


def sessao(s: Annotated[Sessao, Depends(sessao_para_troca)]) -> Sessao:
    if s.trocar_senha:  # senha provisória: nada além da troca (LST-32)
        raise HTTPException(403, "troque a senha provisória antes de continuar")
    return s


def plataforma(s: Annotated[Sessao, Depends(sessao)]):  # noqa: ANN201
    p = Plataforma(cfg, banco.repo(s.tenant, s.email, s.papel), espelho)
    yield p
    try:  # o que a requisição gravou vai para o Storage (plano B, ADR 0009)
        p.sincronizar()
    except Exception as e:  # noqa: BLE001
        log.error("espelho: falha ao sincronizar %s: %s", s.tenant, type(e).__name__)


def _papel(s: Sessao, permitidos: set[str]) -> None:
    if s.papel not in permitidos:
        raise HTTPException(403, f"papel '{s.papel}' não pode fazer isso")


@app.get("/saude")
def saude() -> dict:
    """Verificação de saúde do Cloud Run: sem login, sem detalhe interno."""
    try:
        banco.ping()
        estado = "ok"
    except Exception:  # noqa: BLE001
        estado = "erro"
    if estado != "ok":
        raise HTTPException(503, "banco indisponível")
    return {"estado": "ok", "versao": app.version, "banco": estado}


class Login(BaseModel):
    email: str
    senha: str


@app.post("/api/login")
def login(dados: Login) -> dict:
    u = banco.autenticar(dados.email, dados.senha)
    if not u:
        raise HTTPException(401, "e-mail ou senha inválidos")
    trocar = bool(u.get("trocar_senha"))
    return {"token": emitir_token(cfg.segredo, u["email"], u["tenant_id"], u["papel"], trocar_senha=trocar),
            "nome": u["nome"], "papel": u["papel"], "tenant": u["tenant_id"], "trocar_senha": trocar}


# ---- Conta e equipe (LST-32) -------------------------------------------------------------

class TrocaSenha(BaseModel):
    atual: str
    nova: str


@app.post("/api/conta/senha")
def trocar_senha(dados: TrocaSenha, s: Annotated[Sessao, Depends(sessao_para_troca)]) -> dict:
    try:
        ok = banco.trocar_senha(s.email, dados.atual, dados.nova)
    except SenhaInvalida as e:
        raise HTTPException(400, str(e)) from e
    if not ok:
        raise HTTPException(403, "senha atual incorreta")
    banco.repo(s.tenant, s.email, s.papel).registrar(s.email, "trocou_senha", {})
    return {"token": emitir_token(cfg.segredo, s.email, s.tenant, s.papel), "trocar_senha": False}


class Convite(BaseModel):
    email: str
    nome: str
    papel: str = "demandante"


@app.get("/api/usuarios")
def listar_usuarios(s: Annotated[Sessao, Depends(sessao)]) -> list[dict]:
    _papel(s, {"admin"})
    return banco.usuarios(s.tenant)


@app.post("/api/usuarios")
def convidar(dados: Convite, s: Annotated[Sessao, Depends(sessao)]) -> dict:
    """Cria o usuário (ou gera nova senha provisória) na empresa do admin. A senha volta uma única vez."""
    _papel(s, {"admin"})
    email = dados.email.strip().lower()
    if dados.papel not in {"admin", "demandante", "revisor", "leitor"} or "@" not in email or not dados.nome.strip():
        raise HTTPException(400, "e-mail, nome ou papel inválidos")
    try:
        senha = banco.senha_provisoria(s.tenant, email, dados.nome.strip(), dados.papel)
    except PermissionError as e:
        raise HTTPException(409, "este e-mail já está em uso") from e  # não diz em qual empresa
    banco.repo(s.tenant, s.email, s.papel).registrar(s.email, "gerou_senha_provisoria", {"usuario": email, "papel": dados.papel})
    return {"email": email, "papel": dados.papel, "senha_provisoria": senha}


@app.get("/api/eu")
def eu(s: Annotated[Sessao, Depends(sessao_para_troca)]) -> Sessao:
    return s


@app.get("/api/fontes")
def listar_fontes(p: Annotated[Plataforma, Depends(plataforma)]) -> list[dict]:
    return [{k: f[k] for k in ("id", "nome", "tipo")} for f in p.repo.fontes()]


@app.post("/api/fontes")
async def enviar_fonte(
    s: Annotated[Sessao, Depends(sessao)], p: Annotated[Plataforma, Depends(plataforma)], arquivo: UploadFile = File(...), nome: str = Form("")
) -> dict:
    _papel(s, {"admin"})
    suf = Path(arquivo.filename or "").suffix.lower()
    if suf not in EXTENSOES:
        raise HTTPException(400, f"formato não suportado; use {sorted(EXTENSOES)}")
    nome = re.sub(r"[^a-z0-9_]+", "_", (nome or Path(arquivo.filename or "fonte").stem).lower()).strip("_") or "fonte"
    limite = int(os.environ.get("LASTRO_UPLOAD_MAX_MB", "50")) * 1024 * 1024
    conteudo = await arquivo.read(limite + 1)
    if len(conteudo) > limite:
        raise HTTPException(413, f"arquivo acima de {limite // (1024 * 1024)} MB; conecte o sistema de origem em vez de enviar o arquivo")
    destino = p.pasta / "fontes" / f"{nome}_{int(time.time())}{suf}"
    destino.parent.mkdir(parents=True, exist_ok=True)
    destino.write_bytes(conteudo)
    fid = p.repo.adicionar_fonte(nome, "arquivo", str(destino))
    p.repo.registrar(s.email, "conectou_fonte", {"fonte": nome}, None)
    return {"id": fid, "nome": nome}


class NovaDemanda(BaseModel):
    pergunta: str
    fontes: list[int]


def _resumo(d: dict) -> dict:
    r = d.get("resultado") or {}
    return {
        "id": d["id"], "pergunta": d["pergunta"], "status": d["status"], "autor": d["autor"], "grill": d["grill"],
        "respostas": d["respostas"], "resposta": r.get("resposta"), "auditoria": r.get("auditoria"), "modelo": r.get("modelo"), "revisao": r.get("revisao"),
    }


def _erro(e: Exception) -> HTTPException:
    if isinstance(e, (PermissaoNegada, EscritaBloqueada, PermissionError)):
        return HTTPException(403, str(e))
    if isinstance(e, LookupError):
        return HTTPException(404, str(e))
    return HTTPException(400, str(e))


@app.get("/api/demandas")
def listar(p: Annotated[Plataforma, Depends(plataforma)]) -> list[dict]:
    return [_resumo(d) for d in p.repo.demandas()]


@app.post("/api/demandas")
def abrir(dados: NovaDemanda, s: Annotated[Sessao, Depends(sessao)], p: Annotated[Plataforma, Depends(plataforma)]) -> dict:
    _papel(s, PAPEIS_QUE_DEMANDAM)
    try:
        return _resumo(p.abrir(s.email, dados.pergunta, dados.fontes))
    except Exception as e:  # noqa: BLE001
        raise _erro(e) from e


@app.get("/api/demandas/{did}")
def ver(did: int, p: Annotated[Plataforma, Depends(plataforma)]) -> dict:
    d = p.repo.demanda(did)
    if not d:
        raise HTTPException(404, "demanda não encontrada")
    return _resumo(d) | {"eventos": p.repo.eventos(did)}


@app.post("/api/demandas/{did}/grill")
def grill(did: int, respostas: dict[str, str], s: Annotated[Sessao, Depends(sessao)], p: Annotated[Plataforma, Depends(plataforma)]) -> dict:
    _papel(s, PAPEIS_QUE_DEMANDAM)
    try:
        return _resumo(p.responder_grill(did, s.email, respostas))
    except Exception as e:  # noqa: BLE001
        raise _erro(e) from e


@app.post("/api/demandas/{did}/executar")
def executar(did: int, s: Annotated[Sessao, Depends(sessao)], p: Annotated[Plataforma, Depends(plataforma)]) -> dict:
    _papel(s, PAPEIS_QUE_DEMANDAM)
    try:
        return _resumo(p.executar(did, s.email))
    except Exception as e:  # noqa: BLE001
        raise _erro(e) from e


class Revisao(BaseModel):
    aprovado: bool
    parecer: str = ""


@app.post("/api/demandas/{did}/revisao")
def revisar(did: int, dados: Revisao, s: Annotated[Sessao, Depends(sessao)], p: Annotated[Plataforma, Depends(plataforma)]) -> dict:
    _papel(s, PAPEIS_QUE_REVISAM)
    try:
        d = p.revisar(did, s.email, dados.aprovado, dados.parecer)
    except Exception as e:  # noqa: BLE001
        raise _erro(e) from e
    if dados.aprovado:  # o gold aprovado entra no BI da empresa (LST-33)
        _republicar(s.tenant, p.repo, p.pasta)
    return _resumo(d)


ARQUIVOS = {"relatorio": "relatorio.html", "notebook": "auditoria_colab.ipynb", "pipeline": "pipeline.py",
            "bigquery": "trilhas/pipeline_bigquery.sql", "azure": "trilhas/pipeline_azure_sql.sql", "athena": "trilhas/pipeline_athena.sql"}


@app.get("/api/demandas/{did}/arquivo/{tipo}")
def arquivo(did: int, tipo: str, p: Annotated[Plataforma, Depends(plataforma)]) -> FileResponse:
    if tipo not in ARQUIVOS or not p.repo.demanda(did):
        raise HTTPException(404, "arquivo não encontrado")
    caminho = p.pasta_demanda(did) / ARQUIVOS[tipo]
    if not caminho.exists():
        raise HTTPException(404, "arquivo ainda não gerado")
    return FileResponse(caminho, filename=f"demanda{did}_{Path(ARQUIVOS[tipo]).name}")


@app.get("/api/caixa")
def buscar_caixa(q: str, p: Annotated[Plataforma, Depends(plataforma)]) -> dict:
    caixa = p.caixa()
    return {"indice": caixa.indice(), "achados": [t.__dict__ for t in caixa.buscar(q)]}


@app.get("/", response_class=HTMLResponse)
def portal() -> str:
    return (WEB / "index.html").read_text(encoding="utf-8")


app.mount("/web", StaticFiles(directory=WEB), name="web")


# ---- Conectores SaaS: catálogo, teste de conexão, importação, Postman e sandbox -------------

from datetime import date as _date  # noqa: E402

from fastapi import Request  # noqa: E402
from fastapi.responses import JSONResponse, Response  # noqa: E402

from .saas import servico as saas_servico  # noqa: E402
from .saas.motor import RelogioReal  # noqa: E402
from .saas.simulador import Simulador  # noqa: E402

_SIMULADORES: dict[str, Simulador] = {}


class TesteConexao(BaseModel):
    entidade: str
    credenciais: dict[str, str]
    variaveis: dict[str, str] = {}
    desde: str | None = None
    modo: str = "sandbox"
    importar: bool = False


@app.get("/api/saas")
def catalogo_saas(s: Annotated[Sessao, Depends(sessao)]) -> list[dict]:
    return saas_servico.resumo_catalogo()


# ---- OAuth2 (LST-9): o admin do cliente autoriza uma vez; o token vive só no cofre ----------

def _cliente_oauth() -> httpx.Client:  # trocado nos testes pelo transporte do simulador
    return httpx.Client(timeout=30)


def _url_publica(request: Request) -> str:
    return os.environ.get("LASTRO_URL_PUBLICA") or str(request.base_url).rstrip("/")


def _contrato_oauth(saas: str) -> dict:
    c = saas_servico.CAT.get(saas)
    if not c or c["auth"]["tipo"] != "oauth2_refresh":
        raise HTTPException(404, "sistema sem OAuth2 no catálogo")
    return c


@app.get("/api/saas/{saas}/oauth/iniciar")
def oauth_iniciar(saas: str, request: Request, s: Annotated[Sessao, Depends(sessao)]) -> dict:
    _papel(s, {"admin"})
    contrato = _contrato_oauth(saas)
    try:
        app_oauth = oauth.app_do_ambiente(saas, _url_publica(request))
    except oauth.Credencial as e:
        raise HTTPException(409, str(e)) from e
    state = oauth.emitir_state(cfg.segredo, s.tenant, saas, s.email)
    return {"url": oauth.url_autorizacao(contrato, app_oauth, state)}


@app.get("/oauth/retorno", include_in_schema=False)
def oauth_retorno(request: Request, state: str = "", code: str = "", error: str = "") -> Response:
    """O sistema do cliente volta aqui. O `state` assinado diz de qual empresa e de qual admin é a autorização."""
    try:
        carga = oauth.ler_state(cfg.segredo, state)
        if error or not code:
            raise oauth.Credencial(f"autorização não concedida ({error or 'sem código'})")
        saas = carga["s"]
        contrato = _contrato_oauth(saas)
        with _cliente_oauth() as http:
            tokens = oauth.trocar_codigo(contrato, oauth.app_do_ambiente(saas, _url_publica(request)), code, http)
        cofre.guardar(oauth.nome_no_cofre(carga["t"], saas), tokens.para_cofre())
    except (oauth.Credencial, HTTPException) as e:
        motivo = e.detail if isinstance(e, HTTPException) else str(e)
        return HTMLResponse(f"<p>Não foi possível concluir a autorização: {html.escape(str(motivo))}</p><p><a href='/'>voltar ao Lastro</a></p>", 400)
    banco.repo(carga["t"], carga["e"], "admin").registrar(carga["e"], "autorizou_conector", {"saas": saas})  # sem token
    return RedirectResponse("/?autorizado=" + saas, status_code=303)


@app.post("/api/saas/{saas}/testar")
def testar_saas(saas: str, dados: TesteConexao, s: Annotated[Sessao, Depends(sessao)], p: Annotated[Plataforma, Depends(plataforma)]) -> dict:
    _papel(s, {"admin"})
    # Modo real: só admin, credencial do cliente (somente leitura), nada é guardado além do laudo.
    gerente = None
    try:
        desde = _date.fromisoformat(dados.desde) if dados.desde else None
        c = saas_servico.CAT.get(saas)
        if dados.modo == "real" and c and c["auth"]["tipo"] == "oauth2_refresh":
            try:
                http = _cliente_oauth()
                gerente = oauth.GerenteToken(c, oauth.app_do_ambiente(saas, ""), cofre, s.tenant, saas, http)
            except oauth.Credencial as e:
                raise HTTPException(409, str(e)) from e
        laudo = saas_servico.testar(
            saas, dados.entidade, dados.credenciais, dados.variaveis, desde, dados.modo, oauth=gerente,
            cliente=gerente.http if gerente else None,
        )
    except (LookupError, ValueError) as e:
        raise HTTPException(400, str(e)) from e
    p.repo.registrar(s.email, "testou_conector", {k: v for k, v in laudo.items() if k not in ("_extracao", "amostra")}, None)
    if laudo["ok"] and dados.importar:
        destino = saas_servico.importar_como_fonte(p.pasta, p.repo.tenant, laudo)
        fid = p.repo.adicionar_fonte(f"{saas}_{dados.entidade}", "arquivo", str(destino))
        laudo["fonte_id"] = fid
    laudo.pop("_extracao", None)
    return laudo


@app.get("/api/saas/{saas}/postman")
def postman(saas: str, request: Request, s: Annotated[Sessao, Depends(sessao)]) -> JSONResponse:
    if saas not in saas_servico.CAT:
        raise HTTPException(404, "SaaS fora do catálogo")
    base = str(request.base_url).rstrip("/")
    return JSONResponse(saas_servico.colecao_postman(saas, base), headers={"Content-Disposition": f'attachment; filename="lastro-{saas}.postman_collection.json"'})


# ---- Cargas agendadas (LST-7, plano Operação) ---------------------------------------------

class NovaCarga(BaseModel):
    fonte_id: int
    saas: str
    entidade: str
    variaveis: dict[str, str] = {}
    credenciais: dict[str, str] = {}
    modo: str = "real"
    hora: int = 6
    pacote: str | None = None
    cota_diaria: int | None = None
    chave: str = "id"


def _publica(c: dict, nomes: dict[int, str]) -> dict:
    return {k: c[k] for k in ("id", "fonte_id", "saas", "entidade", "modo", "hora", "cota_diaria", "marca_dagua",
                              "ultima_execucao", "ultimo_status", "ultimo_aviso", "chamadas_no_dia", "ativa")} | {"fonte": nomes.get(c["fonte_id"], "")}


@app.post("/api/cargas")
def criar_carga(dados: NovaCarga, s: Annotated[Sessao, Depends(sessao)], p: Annotated[Plataforma, Depends(plataforma)]) -> dict:
    _papel(s, {"admin"})
    if p.politica.plano != "operacao":
        raise HTTPException(403, "carga agendada é do plano Operação")
    contrato = saas_servico.CAT.get(dados.saas)
    if not contrato or dados.entidade not in contrato["entidades"] or dados.modo not in ("real", "sandbox") or not 0 <= dados.hora <= 23:
        raise HTTPException(400, "sistema, entidade, modo ou hora inválidos")
    try:
        cota = dados.cota_diaria or cargas.cota_do_contrato(dados.saas, dados.pacote)
    except ValueError as e:
        raise HTTPException(400, str(e)) from e
    if dados.modo == "real" and contrato["auth"]["tipo"] != "oauth2_refresh":
        if not dados.credenciais:
            raise HTTPException(400, "informe a credencial somente leitura do sistema")
        cofre.guardar(cargas.nome_credencial(s.tenant, dados.saas), json.dumps(dados.credenciais))  # só no cofre
    try:
        # a fonte acabou de ser importada inteira: a próxima carga já pede só o que mudou
        cid = p.repo.criar_carga(dados.fonte_id, dados.saas, dados.entidade, dados.variaveis, dados.chave, dados.modo,
                                 dados.hora, cota, marca_dagua=time.time())
    except PermissionError as e:
        raise HTTPException(404, "fonte não encontrada") from e
    p.repo.registrar(s.email, "agendou_carga", {"carga": cid, "saas": dados.saas, "entidade": dados.entidade, "hora": dados.hora, "cota_diaria": cota})
    nomes = {f["id"]: f["nome"] for f in p.repo.fontes()}
    return _publica(p.repo.carga(cid), nomes)


@app.get("/api/cargas")
def listar_cargas(s: Annotated[Sessao, Depends(sessao)], p: Annotated[Plataforma, Depends(plataforma)]) -> list[dict]:
    nomes = {f["id"]: f["nome"] for f in p.repo.fontes()}
    return [_publica(c, nomes) for c in p.repo.cargas()]


@app.post("/tarefas/cargas", include_in_schema=False)
def tarefa_cargas(x_lastro_tarefa: Annotated[str | None, Header()] = None) -> dict:
    """Chamado pelo Cloud Scheduler de hora em hora. Protegido por segredo próprio, não por login."""
    esperado = os.environ.get("LASTRO_TAREFA_SEGREDO", "")
    if len(esperado) < 32:
        raise HTTPException(503, "LASTRO_TAREFA_SEGREDO não configurado")
    if not x_lastro_tarefa or not hmac.compare_digest(x_lastro_tarefa, esperado):
        raise HTTPException(401, "tarefa não autorizada")
    feitas = cargas.executar_devidas(banco, cofre, cfg, cliente=_cliente_oauth, espelho=espelho)
    for tenant in sorted({f["tenant"] for f in feitas if f["status"] == "ok"}):  # fonte nova chega ao BI (LST-33)
        _republicar(tenant, banco.repo(tenant, "agendador@lastro", "admin"), cfg.pasta_tenant(tenant))
    return {"executadas": len(feitas), "por_status": {st: sum(f["status"] == st for f in feitas) for st in ("ok", "cota", "falhou")}}


@app.api_route("/sandbox/{saas}/{caminho:path}", methods=["GET", "POST", "PUT", "PATCH", "DELETE"], include_in_schema=False)
async def sandbox(saas: str, caminho: str, request: Request) -> Response:
    """API simulada, sem login do Lastro: é o alvo do Postman e de testes externos. Nada aqui toca dado real."""
    if saas not in saas_servico.CAT:
        return JSONResponse({"erro": "SaaS fora do catálogo"}, status_code=404)
    sim = _SIMULADORES.setdefault(saas, Simulador(saas, n=180, relogio=RelogioReal()))
    corpo = None
    if await request.body():
        try:
            corpo = await request.json()
        except ValueError:
            return JSONResponse({"erro": "corpo não é JSON"}, status_code=400)
    st, cab, resp = sim.responder(request.method, "/" + caminho, dict(request.query_params), dict(request.headers), corpo)
    if resp is None:
        return Response(status_code=st, headers=cab)
    return JSONResponse(resp, status_code=st, headers=cab)


# ---- BI self-service por empresa (LST-33) -------------------------------------------------

def _bi() -> AcessoBI:
    try:
        return AcessoBI(banco, os.environ.get("LASTRO_BANCO_URL", ""))
    except BIIndisponivel as e:
        raise HTTPException(409, str(e)) from e


def _republicar(tenant: str, repo: object, pasta: Path) -> None:
    """Atualiza o BI da empresa se ele estiver ligado. Falha vira log: nunca derruba a aprovação ou a carga."""
    try:
        bi = AcessoBI(banco, os.environ.get("LASTRO_BANCO_URL", ""))
        acesso = bi.acesso(tenant)
        if acesso and acesso["ativo"]:
            bi.publicar(tenant, repo, pasta)
    except BIIndisponivel:
        return
    except Exception as e:  # noqa: BLE001
        log.error("bi: falha ao republicar %s: %s", tenant, type(e).__name__)


def _estado_bi(bi: AcessoBI, tenant: str) -> dict:
    a = bi.acesso(tenant)
    if not a:
        return {"disponivel": True, "ligado": False}
    return {"disponivel": True, "ligado": a["ativo"], "conexao": bi.conexao(a["nome"]),
            "senha_trocada_em": a["senha_trocada_em"].isoformat(),
            "publicado_em": a["publicado_em"].isoformat() if a["publicado_em"] else None, "tabelas": a["tabelas"]}


@app.get("/api/bi")
def estado_bi(s: Annotated[Sessao, Depends(sessao)]) -> dict:
    _papel(s, {"admin"})
    try:
        bi = AcessoBI(banco, os.environ.get("LASTRO_BANCO_URL", ""))
    except BIIndisponivel as e:
        return {"disponivel": False, "motivo": str(e)}
    return _estado_bi(bi, s.tenant)


@app.post("/api/bi/credencial")
def credencial_bi(s: Annotated[Sessao, Depends(sessao)], p: Annotated[Plataforma, Depends(plataforma)]) -> dict:
    """Liga o BI ou troca a senha. A senha volta só nesta resposta."""
    _papel(s, {"admin"})
    bi = _bi()
    primeira = bi.acesso(s.tenant) is None
    cred = bi.gerar_credencial(s.tenant)
    p.repo.registrar(s.email, "gerou_credencial_bi" if primeira else "trocou_senha_bi", {"usuario": cred["usuario"]})
    publicado = bi.publicar(s.tenant, p.repo, p.pasta) if primeira else None
    teste = bi.testar(cred)  # entra como o BI entraria: confirma pooler, senha e só leitura
    p.repo.registrar(s.email, "testou_credencial_bi", {"ok": teste["ok"], "detalhe": teste["detalhe"]})
    return {"credencial": cred, "publicado": publicado, "teste": teste}


@app.post("/api/bi/publicar")
def publicar_bi(s: Annotated[Sessao, Depends(sessao)], p: Annotated[Plataforma, Depends(plataforma)]) -> dict:
    _papel(s, {"admin"})
    try:
        r = _bi().publicar(s.tenant, p.repo, p.pasta)
    except BIIndisponivel as e:
        raise HTTPException(409, str(e)) from e
    p.repo.registrar(s.email, "publicou_bi", {"tabelas": len(r["tabelas"]), "avisos": r["avisos"]})
    return r


@app.delete("/api/bi/credencial")
def desligar_bi(s: Annotated[Sessao, Depends(sessao)], p: Annotated[Plataforma, Depends(plataforma)]) -> dict:
    _papel(s, {"admin"})
    _bi().desligar(s.tenant)
    p.repo.registrar(s.email, "desligou_bi", {})
    return {"ligado": False}


@app.get("/api/fontes/{fid}/exportar")
def exportar_fonte(fid: int, s: Annotated[Sessao, Depends(sessao)], p: Annotated[Plataforma, Depends(plataforma)],
                   formato: str = "csv") -> FileResponse:
    """Cópia da fonte em CSV ou Parquet, para BI sem conector de banco. A fonte original não é tocada."""
    import tempfile

    import duckdb

    from .bi import _rel_arquivo, ident

    _papel(s, {"admin", "demandante"})
    if formato not in {"csv", "parquet"}:
        raise HTTPException(400, "formato deve ser csv ou parquet")
    fonte = p.repo.fontes([fid])
    if not fonte or fonte[0]["tipo"] != "arquivo" or not Path(fonte[0]["caminho"]).exists():
        raise HTTPException(404, "fonte não encontrada (só fontes de arquivo exportam)")
    destino = Path(tempfile.mkdtemp(prefix="lastro-exp-")) / f"{ident(fonte[0]['nome'], 'fonte')}.{formato}"
    con = duckdb.connect()
    try:
        rel = _rel_arquivo(Path(fonte[0]["caminho"]))(con)
        rel.write_csv(str(destino), header=True) if formato == "csv" else rel.write_parquet(str(destino))
    finally:
        con.close()
    p.repo.registrar(s.email, "exportou_fonte", {"fonte": fid, "formato": formato})
    tipo = "text/csv" if formato == "csv" else "application/vnd.apache.parquet"
    return FileResponse(destino, media_type=tipo, filename=destino.name)


# ---- Painel da demanda (LST-34): o agente monta e edita; HTML e Power BI saem da mesma especificação ----

def _painel_ctx(did: int, p: Plataforma) -> tuple[dict, Path, dict]:
    from . import paineis

    d = p.repo.demanda(did)
    if not d:
        raise HTTPException(404, "demanda não encontrada")
    if d["status"] != "aprovada":
        raise HTTPException(409, "o painel nasce do gold aprovado: aprove a demanda antes")
    gold = p.pasta_demanda(did) / "gold"
    try:
        cat = paineis.catalogo(gold, d["resultado"]["modelo"])
    except paineis.PedidoInvalido as e:
        raise HTTPException(409, str(e)) from e
    return d, gold, cat


def _salvar_painel(p: Plataforma, did: int, spec: dict, gold: Path) -> None:
    from datetime import datetime
    from zoneinfo import ZoneInfo

    from . import paineis

    pasta = p.pasta_demanda(did)
    paineis.gravar(pasta, spec)
    agora = datetime.now(ZoneInfo("America/Sao_Paulo")).strftime("%d/%m/%Y %H:%M")
    (paineis.pasta(pasta) / "painel.html").write_text(paineis.html_painel(spec, gold, agora), encoding="utf-8")


@app.get("/api/demandas/{did}/painel")
def ver_painel(did: int, p: Annotated[Plataforma, Depends(plataforma)]) -> dict:
    from . import paineis

    _, _, cat = _painel_ctx(did, p)
    pasta = p.pasta_demanda(did)
    return {"spec": paineis.atual(pasta), "versoes": paineis.versoes(pasta),
            "opcoes": {"colunas": cat["medidas"], "eixos": cat["dimensoes"] + cat["tempo"],
                       "agregacoes": sorted(paineis.AGREGACOES), "tipos": sorted(paineis.TIPOS)}}


@app.post("/api/demandas/{did}/painel")
def criar_painel(did: int, s: Annotated[Sessao, Depends(sessao)], p: Annotated[Plataforma, Depends(plataforma)]) -> dict:
    from . import paineis

    _papel(s, PAPEIS_QUE_DEMANDAM)
    d, gold, _ = _painel_ctx(did, p)
    if paineis.atual(p.pasta_demanda(did)):
        raise HTTPException(409, "esta demanda já tem painel: peça mudanças a ele")
    try:
        spec = paineis.inicial(d, gold)
    except paineis.PedidoInvalido as e:
        raise HTTPException(400, str(e)) from e
    _salvar_painel(p, did, spec, gold)
    p.repo.registrar("designer", "criou_painel", {"versao": 1, "visuais": [v["titulo"] for v in spec["visuais"]], "pedido_por": s.email}, did)
    return spec


class MudancaPainel(BaseModel):
    pedido: str | None = None  # em português: "adicione um gráfico de barras de valor vendido por estado"
    op: dict | None = None  # ou a operação já estruturada (formulário do portal)


@app.post("/api/demandas/{did}/painel/mudancas")
def mudar_painel(did: int, dados: MudancaPainel, s: Annotated[Sessao, Depends(sessao)], p: Annotated[Plataforma, Depends(plataforma)]) -> dict:
    from . import paineis

    _papel(s, PAPEIS_QUE_DEMANDAM)
    _, gold, cat = _painel_ctx(did, p)
    spec = paineis.atual(p.pasta_demanda(did))
    if not spec:
        raise HTTPException(409, "crie o painel antes de pedir mudanças")
    try:
        op = dados.op or paineis.interpretar(dados.pedido or "", spec, cat)
        novo, frase = paineis.mudar(spec, op, cat)
    except paineis.PedidoInvalido as e:
        p.repo.registrar("designer", "recusou_mudanca_painel", {"pedido": dados.pedido or dados.op, "motivo": str(e), "pedido_por": s.email}, did)
        raise HTTPException(400, str(e)) from e
    _salvar_painel(p, did, novo, gold)
    p.repo.registrar("designer", "alterou_painel", {"versao": novo["versao"], "mudanca": frase, "pedido": dados.pedido or op, "pedido_por": s.email}, did)
    return novo


@app.get("/api/demandas/{did}/painel/html")
def painel_html(did: int, p: Annotated[Plataforma, Depends(plataforma)]) -> FileResponse:
    from . import paineis

    arq = paineis.pasta(p.pasta_demanda(did)) / "painel.html"
    if not p.repo.demanda(did) or not arq.exists():
        raise HTTPException(404, "painel não encontrado")
    return FileResponse(arq, media_type="text/html", filename=f"painel_demanda_{did}.html")


@app.get("/api/demandas/{did}/painel/powerbi")
def painel_powerbi(did: int, s: Annotated[Sessao, Depends(sessao)], p: Annotated[Plataforma, Depends(plataforma)]) -> Response:
    """Projeto aberto do Power BI (PBIP) num .zip. Aponta para o BI da empresa quando ele está ligado (LST-33)."""
    import io
    import zipfile

    from . import paineis

    _, gold, _ = _painel_ctx(did, p)
    spec = paineis.atual(p.pasta_demanda(did))
    if not spec:
        raise HTTPException(409, "crie o painel antes de baixar o projeto do Power BI")
    con = {"host": "SEU_SERVIDOR", "porta": 5432, "banco": "postgres", "esquema": "SEU_SCHEMA"}
    try:
        bi = AcessoBI(banco, os.environ.get("LASTRO_BANCO_URL", ""))
        a = bi.acesso(s.tenant)
        if a and a["ativo"]:
            c = bi.conexao(a["nome"])
            con = {"host": c["host"], "porta": c["porta"], "banco": c["banco"], "esquema": a["nome"]}
    except BIIndisponivel:
        pass
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        for caminho, conteudo in paineis.projeto_powerbi(spec, gold, con).items():
            z.writestr(caminho, conteudo)
    p.repo.registrar(s.email, "baixou_powerbi", {"versao": spec["versao"], "aponta_para_bi": con["esquema"] != "SEU_SCHEMA"}, did)
    return Response(buf.getvalue(), media_type="application/zip",
                    headers={"Content-Disposition": f'attachment; filename="lastro_demanda_{did}_powerbi.zip"'})
