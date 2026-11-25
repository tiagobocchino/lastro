"""API HTTP e portal. Login próprio; cada token carrega o tenant e o papel do usuário."""

from __future__ import annotations

import re
import time
from pathlib import Path
from typing import Annotated

from fastapi import Depends, FastAPI, File, Form, Header, HTTPException, UploadFile
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from .banco import PAPEIS_QUE_DEMANDAM, PAPEIS_QUE_REVISAM, Repo, autenticar, conectar, emitir_token, ler_token
from .config import carregar
from .conectores import EXTENSOES
from .politica import PermissaoNegada
from .servico import Plataforma
from .somente_leitura import EscritaBloqueada

cfg = carregar()
con = conectar(cfg.banco)
WEB = Path(__file__).parent / "web"
app = FastAPI(title="Lastro", version="0.1.0")


class Sessao(BaseModel):
    email: str
    tenant: str
    papel: str


def sessao(authorization: Annotated[str | None, Header()] = None) -> Sessao:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(401, "faça login")
    carga = ler_token(cfg.segredo, authorization[7:])
    if not carga:
        raise HTTPException(401, "sessão expirada")
    return Sessao(email=carga["e"], tenant=carga["t"], papel=carga["p"])


def plataforma(s: Annotated[Sessao, Depends(sessao)]) -> Plataforma:
    return Plataforma(cfg, Repo(con, s.tenant))


def _papel(s: Sessao, permitidos: set[str]) -> None:
    if s.papel not in permitidos:
        raise HTTPException(403, f"papel '{s.papel}' não pode fazer isso")


class Login(BaseModel):
    email: str
    senha: str


@app.post("/api/login")
def login(dados: Login) -> dict:
    u = autenticar(con, dados.email, dados.senha)
    if not u:
        raise HTTPException(401, "e-mail ou senha inválidos")
    return {"token": emitir_token(cfg.segredo, u["email"], u["tenant_id"], u["papel"]), "nome": u["nome"], "papel": u["papel"], "tenant": u["tenant_id"]}


@app.get("/api/eu")
def eu(s: Annotated[Sessao, Depends(sessao)]) -> Sessao:
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
    destino = p.pasta / "fontes" / f"{nome}_{int(time.time())}{suf}"
    destino.parent.mkdir(parents=True, exist_ok=True)
    destino.write_bytes(await arquivo.read())
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
        return _resumo(p.revisar(did, s.email, dados.aprovado, dados.parecer))
    except Exception as e:  # noqa: BLE001
        raise _erro(e) from e


ARQUIVOS = {"relatorio": "relatorio.html", "notebook": "auditoria_colab.ipynb", "pipeline": "pipeline.py"}


@app.get("/api/demandas/{did}/arquivo/{tipo}")
def arquivo(did: int, tipo: str, p: Annotated[Plataforma, Depends(plataforma)]) -> FileResponse:
    if tipo not in ARQUIVOS or not p.repo.demanda(did):
        raise HTTPException(404, "arquivo não encontrado")
    caminho = p.pasta_demanda(did) / ARQUIVOS[tipo]
    if not caminho.exists():
        raise HTTPException(404, "arquivo ainda não gerado")
    return FileResponse(caminho, filename=f"demanda{did}_{ARQUIVOS[tipo]}")


@app.get("/api/caixa")
def buscar_caixa(q: str, p: Annotated[Plataforma, Depends(plataforma)]) -> dict:
    caixa = p.caixa()
    return {"indice": caixa.indice(), "achados": [t.__dict__ for t in caixa.buscar(q)]}


@app.get("/", response_class=HTMLResponse)
def portal() -> str:
    return (WEB / "index.html").read_text(encoding="utf-8")


app.mount("/web", StaticFiles(directory=WEB), name="web")
