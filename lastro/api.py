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
from fastapi.middleware.gzip import GZipMiddleware

app.add_middleware(GZipMiddleware, minimum_size=1024)  # site, portal e painéis em HTML/JS comprimidos


CACHE_ESTATICO = (("/site/fontes/", "public, max-age=31536000, immutable"),  # woff2 nunca muda de conteúdo
                  ("/site/img/", "public, max-age=604800"), ("/site/marca/", "public, max-age=604800"))  # podem ser trocadas


@app.middleware("http")
async def cache_estatico(request, call_next):
    """Cache longo para fontes e imagens do site e do portal (LST-55: Lighthouse "uses-long-cache-ttl")."""
    resposta = await call_next(request)
    for prefixo, politica in CACHE_ESTATICO:
        if request.url.path.startswith(prefixo) and resposta.status_code == 200:
            resposta.headers["Cache-Control"] = politica
            break
    return resposta


NAO_MEDIR = ("/saude", "/web/", "/site", "/favicon", "/robots.txt", "/sitemap.xml")


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


@app.get("/api/config")
def config_publica() -> dict:
    """O que a tela de login precisa saber antes de alguém entrar (LST-55, A5): contas de demonstração só fora de produção."""
    return {"contas_demo": os.environ.get("LASTRO_AMBIENTE", "local") != "producao"}


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
SITE = Path(__file__).parent.parent / "site"
if SITE.exists():  # site de apresentação servido pelo Render até existir domínio (LST-23, LST-43)
    app.mount("/site", StaticFiles(directory=SITE, html=True), name="site")


# ---- Conectores SaaS: catálogo, teste de conexão, importação, Postman e sandbox -------------

from datetime import date as _date  # noqa: E402
from datetime import datetime as _datetime
from zoneinfo import ZoneInfo as _ZoneInfo

_FUSO_SITE = _ZoneInfo("America/Sao_Paulo")

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


@app.get("/robots.txt", include_in_schema=False)
def robots(request: Request) -> Response:
    """SEO do site (LST-55): só o site é indexável; API, portal e sandbox ficam fora."""
    base = _url_publica(request)
    corpo = (f"User-agent: *\nAllow: /site/\nDisallow: /api/\nDisallow: /web/\nDisallow: /sandbox/\nDisallow: /bi/\n\n"
             f"Sitemap: {base}/sitemap.xml\n")
    return Response(corpo, media_type="text/plain; charset=utf-8")


@app.get("/sitemap.xml", include_in_schema=False)
def sitemap(request: Request) -> Response:
    """Uma URL por página do site; lastmod = data do arquivo publicado."""
    base = _url_publica(request)
    urls = []
    for pagina in sorted(SITE.glob("**/index.html")) if SITE.exists() else []:
        caminho = pagina.parent.relative_to(SITE).as_posix()
        loc = f"{base}/site/" + (f"{caminho}/" if caminho != "." else "")
        dia = _datetime.fromtimestamp(pagina.stat().st_mtime, tz=_FUSO_SITE).date().isoformat()
        urls.append(f"  <url><loc>{loc}</loc><lastmod>{dia}</lastmod></url>")
    corpo = ('<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
             + "\n".join(urls) + "\n</urlset>\n")
    return Response(corpo, media_type="application/xml")


def _url_publica(request: Request) -> str:
    """Endereço público pelo próprio pedido (Host + X-Forwarded-Proto, que o Render envia): vale no Render e no
    domínio próprio. A variável LASTRO_URL_PUBLICA só entra se o pedido não trouxer Host (em 25/11 ela estava com
    um endereço que não existe e mandava o OAuth e o Power BI para o lugar errado)."""
    host = request.headers.get("x-forwarded-host") or request.headers.get("host")
    if not host:
        return (os.environ.get("LASTRO_URL_PUBLICA") or str(request.base_url)).rstrip("/")
    proto = request.headers.get("x-forwarded-proto", request.url.scheme).split(",")[0].strip()
    return f"{proto}://{host}".rstrip("/")


def _contrato_oauth(saas: str) -> dict:
    from . import planilha_bi

    if saas == planilha_bi.SAAS:  # destino do BI (LST-48), não é fonte: fica fora do catálogo de conectores
        return planilha_bi.CONTRATO
    c = saas_servico.CAT.get(saas)
    if not c or c["auth"]["tipo"] != "oauth2_refresh":
        raise HTTPException(404, "sistema sem OAuth2 no catálogo")
    return c


@app.get("/api/saas/{saas}/oauth/iniciar")
def oauth_iniciar(saas: str, request: Request, s: Annotated[Sessao, Depends(sessao)]) -> dict:
    _papel(s, {"admin"})
    contrato = _contrato_oauth(saas)
    try:
        app_oauth = oauth.app_do_ambiente(contrato.get("app_oauth", saas), _url_publica(request))
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
            tokens = oauth.trocar_codigo(contrato, oauth.app_do_ambiente(contrato.get("app_oauth", saas), _url_publica(request)), code, http)
        cofre.guardar(oauth.nome_no_cofre(carga["t"], saas), tokens.para_cofre())
    except (oauth.Credencial, HTTPException) as e:
        motivo = e.detail if isinstance(e, HTTPException) else str(e)
        return HTMLResponse(f"<p>Não foi possível concluir a autorização: {html.escape(str(motivo))}</p><p><a href='/'>voltar ao Lastro</a></p>", 400)
    banco.repo(carga["t"], carga["e"], "admin").registrar(carga["e"], "autorizou_conector", {"saas": saas})  # sem token
    if saas == "planilha_bi":  # primeira carga da planilha já na volta da autorização (LST-48)
        try:
            _enviar_planilha(carga["t"], carga["e"])
        except Exception as e:  # noqa: BLE001  (a autorização valeu; o envio aparece como erro na tela do BI)
            log.warning("planilha do BI: primeiro envio falhou para %s: %s", carga["t"], type(e).__name__)
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
            if _planilha_autorizada(tenant):  # LST-48: a planilha do Data Studio acompanha a aprovação e a carga
                _enviar_planilha(tenant)
    except BIIndisponivel:
        return
    except Exception as e:  # noqa: BLE001
        log.error("bi: falha ao republicar %s: %s", tenant, type(e).__name__)


def _estado_bi(bi: AcessoBI, tenant: str) -> dict:
    a = bi.acesso(tenant)
    if not a:
        return {"disponivel": True, "ligado": False}
    return {"disponivel": True, "ligado": a["ativo"], "conexao": bi.conexao(a["nome"]),
            "chave_ativa": a.get("chave_ativa", False),
            "planilha": {"autorizada": bool(cofre.ler(oauth.nome_no_cofre(tenant, "planilha_bi"))), "id": a.get("planilha_id"),
                         "url": f"https://docs.google.com/spreadsheets/d/{a['planilha_id']}/edit" if a.get("planilha_id") else None,
                         "enviada_em": a["planilha_enviada_em"].isoformat() if a.get("planilha_enviada_em") else None},
            "chave_criada_em": a["chave_criada_em"].isoformat() if a.get("chave_criada_em") else None,
            "chave_usada_em": a["chave_usada_em"].isoformat() if a.get("chave_usada_em") else None,
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
    if _planilha_autorizada(s.tenant):  # a planilha do Data Studio acompanha cada publicação (LST-48)
        try:
            r["planilha"] = _enviar_planilha(s.tenant, s.email)
        except Exception as e:  # noqa: BLE001
            r["avisos"] = [*r["avisos"], f"planilha Google não foi atualizada: {e}"]
    return r


@app.post("/api/bi/chave")
def chave_bi(request: Request, s: Annotated[Sessao, Depends(sessao)], p: Annotated[Plataforma, Depends(plataforma)]) -> dict:
    """Chave de leitura do BI por HTTPS (LST-47). Gera ou troca; a chave volta só nesta resposta."""
    _papel(s, {"admin"})
    try:
        chave = _bi().gerar_chave(s.tenant)
    except BIIndisponivel as e:
        raise HTTPException(409, str(e)) from e
    p.repo.registrar(s.email, "gerou_chave_bi", {})
    return {"chave": chave, "cabecalho": CABECALHO_CHAVE, "base": f"{_url_publica(request)}/bi/v1/"}


@app.delete("/api/bi/chave")
def revogar_chave_bi(s: Annotated[Sessao, Depends(sessao)], p: Annotated[Plataforma, Depends(plataforma)]) -> dict:
    _papel(s, {"admin"})
    _bi().revogar_chave(s.tenant)
    p.repo.registrar(s.email, "revogou_chave_bi", {})
    return {"chave_ativa": False}


# ---- BI por HTTPS (LST-47): o Power BI lê as tabelas publicadas sem certificado do Supabase e sem gateway ----
CABECALHO_CHAVE = "X-Lastro-Chave"


def _pela_chave(chave: str | None, agente: str | None = None) -> tuple[AcessoBI, dict]:
    try:
        bi = _bi()
    except HTTPException:
        raise HTTPException(404, "BI por HTTPS indisponível neste servidor") from None
    dono = bi.pela_chave(chave or "", agente or "")
    if not dono:
        raise HTTPException(401, f"chave de leitura ausente ou inválida (cabeçalho {CABECALHO_CHAVE})")
    return bi, dono


@app.get("/bi/v1/", response_class=Response)
def bi_https_raiz() -> Response:
    """Sem chave e sem dado: o Power BI Service testa a URL base ao salvar a credencial 'Anônimo'."""
    return Response("Lastro · BI por HTTPS. Use /bi/v1/<tabela>.parquet com o cabeçalho X-Lastro-Chave.\n", media_type="text/plain")


@app.get("/bi/v1/tabelas")
def bi_https_tabelas(x_lastro_chave: Annotated[str | None, Header()] = None,
                     user_agent: Annotated[str | None, Header()] = None) -> dict:
    bi, dono = _pela_chave(x_lastro_chave, user_agent)
    return {"tabelas": bi.tabelas_publicadas(dono["nome"])}


@app.get("/bi/v1/{tabela}.parquet")
def bi_https_tabela(tabela: str, x_lastro_chave: Annotated[str | None, Header()] = None,
                    user_agent: Annotated[str | None, Header()] = None) -> Response:
    bi, dono = _pela_chave(x_lastro_chave, user_agent)
    try:
        dados = bi.parquet(dono["nome"], tabela)
    except LookupError as e:
        raise HTTPException(404, str(e)) from e
    return Response(dados, media_type="application/vnd.apache.parquet",
                    headers={"Content-Disposition": f'attachment; filename="{tabela}.parquet"', "Cache-Control": "no-store"})


# ---- BI sem atrito C (LST-48): tabelas prontas numa planilha Google do cliente, para o Data Studio ----------

def _enviar_planilha(tenant: str, email: str = "lastro") -> dict:
    from datetime import datetime
    from zoneinfo import ZoneInfo

    from . import planilha_bi

    bi = _bi()
    a = bi.acesso(tenant)
    if not a or not a["ativo"]:
        raise BIIndisponivel("ligue o BI da empresa antes de enviar para a planilha")
    http = _cliente_oauth()
    try:
        g = oauth.GerenteToken(planilha_bi.CONTRATO, oauth.app_do_ambiente(planilha_bi.CONTRATO["app_oauth"], ""),
                               cofre, tenant, planilha_bi.SAAS, http)

        def token(forcar: bool = False) -> str:
            if forcar:
                g.forcar_renovacao()
            return g.token()

        tabelas = {t: bi.linhas(a["nome"], t) for t in bi.tabelas_publicadas(a["nome"]) if t.startswith(planilha_bi.PREFIXO)}
        agora = datetime.now(ZoneInfo("America/Sao_Paulo")).strftime("%d/%m/%Y %H:%M")
        r = planilha_bi.enviar(planilha_bi.Planilha(http, token), tabelas, a.get("planilha_id"), f"Lastro · BI · {tenant}", agora)
    finally:
        http.close()
    bi.marcar_planilha(tenant, r["planilha_id"])
    banco.repo(tenant, email, "admin").registrar(email, "enviou_planilha_bi", {"abas": len(r["abas"]), "avisos": r["avisos"]})
    return r


def _planilha_autorizada(tenant: str) -> bool:
    return bool(cofre.ler(oauth.nome_no_cofre(tenant, "planilha_bi")))


@app.post("/api/bi/planilha/autorizar")
def autorizar_planilha(request: Request, s: Annotated[Sessao, Depends(sessao)]) -> dict:
    """URL do consentimento do Google (escopo drive.file: só a planilha que o Lastro criar)."""
    _papel(s, {"admin"})
    return oauth_iniciar("planilha_bi", request, s)


@app.post("/api/bi/planilha/enviar")
def enviar_planilha(s: Annotated[Sessao, Depends(sessao)]) -> dict:
    from . import planilha_bi

    _papel(s, {"admin"})
    try:
        return _enviar_planilha(s.tenant, s.email)
    except (BIIndisponivel, oauth.Credencial) as e:
        raise HTTPException(409, str(e)) from e
    except planilha_bi.ErroPlanilha as e:
        raise HTTPException(502, str(e)) from e


@app.delete("/api/bi/planilha")
def desconectar_planilha(s: Annotated[Sessao, Depends(sessao)], p: Annotated[Plataforma, Depends(plataforma)]) -> dict:
    """Esquece a autorização e a planilha. A planilha continua no Drive do cliente (é dele)."""
    _papel(s, {"admin"})
    cofre.guardar(oauth.nome_no_cofre(s.tenant, "planilha_bi"), "")
    _bi().marcar_planilha(s.tenant, None)
    p.repo.registrar(s.email, "desconectou_planilha_bi", {})
    return {"autorizada": False}


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


PAPEIS_DA_PREVIA = ("revisor", "admin")


@app.get("/api/demandas/{did}/dashboard", response_class=HTMLResponse)
def dashboard(did: int, s: Annotated[Sessao, Depends(sessao)], p: Annotated[Plataforma, Depends(plataforma)]) -> str:
    """Dashboard da demanda no portal (LST-57): mesmo padrão do Streamlit, montado na hora a partir do gold da demanda.

    Aprovada: todos da empresa veem (a versão do painel, se alguém personalizou; senão a proposta inicial).
    Aguardando revisor: só revisor e admin, como prévia marcada (regra 2: nada sai antes das duas camadas)."""
    from datetime import datetime
    from zoneinfo import ZoneInfo

    from . import paineis

    d = p.repo.demanda(did)  # o repo já é da empresa do login: outra empresa recebe 404
    if not d:
        raise HTTPException(404, "demanda não encontrada")
    if d["status"] == "em_revisao":
        if s.papel not in PAPEIS_DA_PREVIA:
            raise HTTPException(403, "o dashboard aparece depois que o revisor de negócio aprovar a demanda")
    elif d["status"] != "aprovada":
        raise HTTPException(409, "o dashboard nasce do resultado conferido: rode a demanda antes")
    gold = p.pasta_demanda(did) / "gold"
    try:
        spec = (paineis.atual(p.pasta_demanda(did)) if d["status"] == "aprovada" else None) or paineis.inicial(d, gold)
    except paineis.PedidoInvalido as e:
        raise HTTPException(409, str(e)) from e
    if d["status"] == "em_revisao":
        spec = {**spec, "modo": "previa"}
    agora = datetime.now(ZoneInfo("America/Sao_Paulo")).strftime("%d/%m/%Y %H:%M") + " (Brasília)"
    return paineis.html_painel(spec, gold, agora)


@app.get("/api/demandas/{did}/painel/html")
def painel_html(did: int, p: Annotated[Plataforma, Depends(plataforma)]) -> FileResponse:
    from . import paineis

    arq = paineis.pasta(p.pasta_demanda(did)) / "painel.html"
    if not p.repo.demanda(did) or not arq.exists():
        raise HTTPException(404, "painel não encontrado")
    return FileResponse(arq, media_type="text/html", filename=f"painel_demanda_{did}.html")


@app.get("/api/demandas/{did}/painel/powerbi")
def painel_powerbi(did: int, request: Request, s: Annotated[Sessao, Depends(sessao)],
                   p: Annotated[Plataforma, Depends(plataforma)], via: str = "https") -> Response:
    """Projeto aberto do Power BI (PBIP) num .zip. Padrão: lê o BI da empresa por HTTPS com a chave de leitura
    (LST-47, sem certificado nem gateway). via=postgres gera a conexão direta ao Postgres (LST-33)."""
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
    if via != "postgres":
        con = {"via": "https", "api": _url_publica(request) + "/"}
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        for caminho, conteudo in paineis.projeto_powerbi(spec, gold, con).items():
            z.writestr(caminho, conteudo)
    p.repo.registrar(s.email, "baixou_powerbi", {"versao": spec["versao"], "via": con.get("via", "postgres"),
                                                         "aponta_para_bi": con.get("via") == "https" or con["esquema"] != "SEU_SCHEMA"}, did)
    return Response(buf.getvalue(), media_type="application/zip",
                    headers={"Content-Disposition": f'attachment; filename="lastro_demanda_{did}_powerbi.zip"'})


@app.get("/api/demandas/{did}/relatorio/powerbi")
def relatorio_powerbi(did: int, request: Request, s: Annotated[Sessao, Depends(sessao)],
                      p: Annotated[Plataforma, Depends(plataforma)]) -> Response:
    """Relatório Power BI de entrega (LST-52): várias páginas sobre a tabela pronta da demanda, lida por HTTPS com a chave."""
    import io
    import zipfile

    from . import relatorio_powerbi as rp
    from .agents.construtores import ident

    d = p.repo.demanda(did)
    if not d:
        raise HTTPException(404, "demanda não encontrada")
    if d["status"] != "aprovada":
        raise HTTPException(409, "o relatório de entrega sai só de demanda aprovada")
    bi = _bi()
    a = bi.acesso(s.tenant)
    if not a or not a["ativo"]:
        raise HTTPException(409, "ligue o BI da empresa: o relatório lê a tabela pronta publicada nele")
    tabela = next((t for t in bi.tabelas_publicadas(a["nome"]) if t.startswith(f"painel_{did}_")), None)
    if not tabela:
        raise HTTPException(409, "a tabela pronta desta demanda ainda não foi publicada: clique em publicar no BI")
    medida = ((d.get("resultado") or {}).get("modelo") or {}).get("medida")
    colunas = rp.colunas_do_postgres(bi.colunas(a["nome"], tabela))
    distintos = bi.distintos(a["nome"], tabela, [c for c, tp in colunas.items() if tp == "string"])
    arqs = rp.projeto(did, d["pergunta"], tabela, colunas, ident(medida) if medida else None, _url_publica(request) + "/",
                      distintos=distintos)
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        for caminho, conteudo in arqs.items():
            z.writestr(caminho, conteudo)
    p.repo.registrar(s.email, "baixou_relatorio_powerbi", {"tabela": tabela}, did)
    return Response(buf.getvalue(), media_type="application/zip",
                    headers={"Content-Disposition": f'attachment; filename="lastro_relatorio_{did}_powerbi.zip"'})


# ---- Demonstração do site (LST-39, ADR 0010) ------------------------------------------------
# Pública e sem login. Desligada por padrão: LASTRO_DEMO=1 liga (produção só depois dos limites do LST-42).

_DEMOS = None


def _demos():
    global _DEMOS
    if os.environ.get("LASTRO_DEMO") != "1":
        raise HTTPException(404, "demonstração desligada")
    if _DEMOS is None:
        import threading

        from .demo import Demos

        _DEMOS = Demos(cfg, ao_evento=banco.registrar_demo)

        def varrer_sempre() -> None:
            while True:
                time.sleep(300)
                try:
                    _DEMOS.varrer()
                except Exception as e:  # noqa: BLE001
                    log.error("demo: varredura falhou: %s", type(e).__name__)

        threading.Thread(target=varrer_sempre, daemon=True, name="demo-varredura").start()
    return _DEMOS


def _erro_demo(e: Exception) -> HTTPException:
    from .demo import Demorou, LimiteIP, Ocupado

    if isinstance(e, Ocupado):
        return HTTPException(503, str(e), headers={"Retry-After": "10"})
    if isinstance(e, LimiteIP):
        return HTTPException(429, str(e))
    if isinstance(e, Demorou):
        return HTTPException(504, str(e))
    return HTTPException(404 if "sessão" in str(e) else 400, str(e))


def _ip(request: Request) -> str:
    """No Render o endereço do visitante vem no primeiro X-Forwarded-For; localmente, no socket."""
    encaminhado = request.headers.get("x-forwarded-for", "")
    return encaminhado.split(",")[0].strip() or (request.client.host if request.client else "desconhecido")


@app.post("/api/demo/sessoes")
async def demo_abrir(request: Request, arquivo: UploadFile | None = File(None), exemplo: bool = Form(False)) -> dict:  # noqa: B008
    from starlette.concurrency import run_in_threadpool

    from .demo import MAX_BYTES, ErroDemo

    demos = _demos()
    conteudo, nome = None, None
    if arquivo is not None and not exemplo:
        conteudo = await arquivo.read(MAX_BYTES + 1)
        nome = arquivo.filename
    try:
        _, resposta = await run_in_threadpool(demos.abrir, nome, conteudo, None, _ip(request))
    except ErroDemo as e:
        raise _erro_demo(e) from e
    return resposta


@app.get("/api/demo/fila")
def demo_fila() -> dict:
    d = _demos()
    return {"esperando": d.esperando, "sessoes_abertas": d.abertas}


class RespostasDemo(BaseModel):
    respostas: dict[str, str] = {}


@app.post("/api/demo/sessoes/{sid}/painel")
def demo_painel(sid: str, dados: RespostasDemo) -> dict:
    from .demo import ErroDemo

    try:
        return _demos().responder(sid, dados.respostas)
    except ErroDemo as e:
        raise _erro_demo(e) from e


@app.delete("/api/demo/sessoes/{sid}")
def demo_apagar(sid: str) -> dict:
    from .demo import ErroDemo

    d = _demos()
    try:
        recibo = d.apagar(sid)
    except ErroDemo as e:
        raise HTTPException(404, str(e)) from e
    d.evento("desistiu")
    return {"recibo": recibo}


@app.post("/api/demo/sessoes/{sid}/apagar", include_in_schema=False)
def demo_apagar_ao_sair(sid: str) -> dict:
    """O navegador avisa (sendBeacon, só POST) quando o visitante sai da página no meio da análise."""
    from .demo import ErroDemo

    d = _demos()
    try:
        recibo = d.apagar(sid)
    except ErroDemo:
        return {"recibo": None}
    d.evento("desistiu")
    return {"recibo": recibo}


class CliqueDemo(BaseModel):
    visual: str | None = None


@app.post("/api/demo/contato", include_in_schema=False)
def demo_clicou_contato(dados: CliqueDemo) -> dict:
    """O visitante clicou para conversar depois do painel. Só o formato do painel, de lista fechada."""
    _demos().evento("clicou_contato", visual=dados.visual)
    return {"ok": True}


# ---- Conversa com os dados da demanda (LST-35) ----------------------------------------------------

def _conversa_arq(p: Plataforma, did: int) -> Path:
    return p.pasta_demanda(did) / "conversa.json"


def _ler_conversa(p: Plataforma, did: int) -> list[dict]:
    arq = _conversa_arq(p, did)
    return json.loads(arq.read_text(encoding="utf-8")) if arq.exists() else []


class PerguntaConversa(BaseModel):
    pergunta: str


@app.get("/api/demandas/{did}/conversa")
def ver_conversa(did: int, p: Annotated[Plataforma, Depends(plataforma)]) -> list[dict]:
    if not p.repo.demanda(did):
        raise HTTPException(404, "demanda não encontrada")
    return _ler_conversa(p, did)


@app.post("/api/demandas/{did}/conversa")
def conversar(did: int, dados: PerguntaConversa, s: Annotated[Sessao, Depends(sessao)], p: Annotated[Plataforma, Depends(plataforma)]) -> dict:
    """O Intérprete responde com insights provados (camada 1); o turno espera o revisor (camada 2)."""
    from .agents.interprete import Interprete

    d = p.repo.demanda(did)
    if not d:
        raise HTTPException(404, "demanda não encontrada")
    if d["status"] != "aprovada":
        raise HTTPException(409, "a conversa usa o resultado aprovado: aprove a demanda antes")
    pergunta = dados.pergunta.strip()[:300]
    if not pergunta:
        raise HTTPException(400, "escreva uma pergunta")
    agente = Interprete(d, p.pasta_demanda(did))
    try:
        resposta = agente.responder(pergunta)
    finally:
        agente.fechar()
    conversa = _ler_conversa(p, did)
    turno = {"n": len(conversa) + 1, "autor": s.email, "em": time.time(), **resposta,
             "camada2": "aguardando revisor", "revisao": None}
    conversa.append(turno)
    _conversa_arq(p, did).write_text(json.dumps(conversa, ensure_ascii=False, default=str), encoding="utf-8")
    p.repo.registrar("interprete", "interpretou", {"pergunta": pergunta, "insights": len(resposta["insights"]),
                                                   "recusados": len(resposta["recusados"]), "autor": s.email}, did)
    for r in resposta["recusados"]:
        p.repo.registrar("auditor", "recusou_insight", r, did)
    return turno


class RevisaoConversa(BaseModel):
    aprovado: bool
    parecer: str = ""


@app.post("/api/demandas/{did}/conversa/{n}/revisao")
def revisar_conversa(did: int, n: int, dados: RevisaoConversa, s: Annotated[Sessao, Depends(sessao)],
                     p: Annotated[Plataforma, Depends(plataforma)]) -> dict:
    _papel(s, PAPEIS_QUE_REVISAM)
    conversa = _ler_conversa(p, did)
    turno = next((t for t in conversa if t["n"] == n), None)
    if not p.repo.demanda(did) or not turno:
        raise HTTPException(404, "turno não encontrado")
    turno["camada2"] = "aprovado" if dados.aprovado else "reprovado"
    turno["revisao"] = {"revisor": s.email, "aprovado": dados.aprovado, "parecer": dados.parecer[:500], "em": time.time()}
    _conversa_arq(p, did).write_text(json.dumps(conversa, ensure_ascii=False, default=str), encoding="utf-8")
    p.repo.registrar(s.email, "revisou_insights", {"turno": n, "aprovado": dados.aprovado, "parecer": dados.parecer[:500]}, did)
    return turno
