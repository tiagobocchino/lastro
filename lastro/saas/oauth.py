"""OAuth2 com refresh_token (card LST-9): autorização única pelo admin do cliente e renovação automática.

Fluxo:
1. `url_autorizacao` monta o link para o admin do cliente autorizar o Lastro no sistema dele. O `state` é
   assinado com LASTRO_SEGREDO e carrega tenant, sistema e validade (protege contra CSRF e diz de quem é o código).
2. O sistema redireciona para /oauth/retorno com `code` e `state`; `trocar_codigo` troca o código pelo par de tokens.
3. `GerenteToken` entrega um token de acesso válido ao `Leitor`: renova antes de vencer (ou ao receber 401) e
   grava o novo par no cofre, porque RD Station e Conta Azul invalidam o refresh_token antigo a cada renovação.

Tokens só existem no cofre (`lastro/cofre.py`) e na memória do processo; nunca em tabela, log ou laudo.
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
import secrets
import time
from dataclasses import dataclass
from typing import Protocol
from urllib.parse import urlencode

import httpx

from .motor import Credencial, Relogio, RelogioReal

MARGEM_S = 300  # renova quando faltam menos de 5 minutos (recomendação da RD Station)
VALIDADE_STATE_S = 600


@dataclass(frozen=True)
class AppOAuth:
    """Credenciais do aplicativo do Lastro no sistema (não do cliente). Vêm do Secret Manager."""

    client_id: str
    client_secret: str
    redirect_uri: str


def app_do_ambiente(saas: str, url_publica: str) -> AppOAuth:
    chave = saas.upper()
    cid, segredo = os.environ.get(f"LASTRO_OAUTH_{chave}_CLIENT_ID", ""), os.environ.get(f"LASTRO_OAUTH_{chave}_CLIENT_SECRET", "")
    if not cid or not segredo:
        raise Credencial(f"{saas}: aplicativo OAuth do Lastro não configurado (LASTRO_OAUTH_{chave}_CLIENT_ID/_CLIENT_SECRET)")
    return AppOAuth(cid, segredo, url_publica.rstrip("/") + "/oauth/retorno")


# ---- state assinado -------------------------------------------------------------------------

def emitir_state(segredo: str, tenant: str, saas: str, email: str, agora: float | None = None) -> str:
    carga = {"t": tenant, "s": saas, "e": email, "x": int((time.time() if agora is None else agora) + VALIDADE_STATE_S), "n": secrets.token_hex(8)}
    b = base64.urlsafe_b64encode(json.dumps(carga).encode()).decode().rstrip("=")
    return f"{b}.{hmac.new(segredo.encode(), b.encode(), hashlib.sha256).hexdigest()}"


def ler_state(segredo: str, state: str, agora: float | None = None) -> dict:
    try:
        b, assinatura = state.rsplit(".", 1)
    except ValueError as e:
        raise Credencial("state inválido") from e
    if not hmac.compare_digest(hmac.new(segredo.encode(), b.encode(), hashlib.sha256).hexdigest(), assinatura):
        raise Credencial("state com assinatura inválida")
    carga = json.loads(base64.urlsafe_b64decode(b + "=" * (-len(b) % 4)))
    if carga["x"] < (time.time() if agora is None else agora):
        raise Credencial("autorização expirou: comece de novo")
    return carga


# ---- chamadas ao servidor de autorização ----------------------------------------------------

def url_autorizacao(contrato: dict, app: AppOAuth, state: str) -> str:
    a = contrato["auth"]
    params = {"response_type": "code", "client_id": app.client_id, "redirect_uri": app.redirect_uri, "state": state}
    if a.get("escopo"):
        params["scope"] = a["escopo"]
    params |= a.get("params_autorizar", {})
    return f"{a['url_autorizar']}?{urlencode(params)}"


@dataclass
class Tokens:
    access_token: str
    refresh_token: str
    expira_em: float

    def para_cofre(self) -> str:
        return json.dumps({"access_token": self.access_token, "refresh_token": self.refresh_token, "expira_em": self.expira_em})

    @staticmethod
    def do_cofre(texto: str) -> Tokens:
        d = json.loads(texto)
        return Tokens(d["access_token"], d["refresh_token"], float(d["expira_em"]))


def _pedir_token(contrato: dict, app: AppOAuth, corpo: dict, http: httpx.Client, agora: float, refresh_anterior: str = "") -> Tokens:
    a = contrato["auth"]
    cab = {"Content-Type": "application/x-www-form-urlencoded"}
    if a.get("cliente_no", "corpo") == "basic":
        cab["Authorization"] = "Basic " + base64.b64encode(f"{app.client_id}:{app.client_secret}".encode()).decode()
    else:
        corpo = corpo | {"client_id": app.client_id, "client_secret": app.client_secret}
    r = http.post(a["url_token"], data=corpo, headers=cab)
    if r.status_code >= 400:
        try:
            erro = r.json()
        except ValueError:
            erro = {}
        motivo = erro.get("error_subtype") or erro.get("error") or f"HTTP {r.status_code}"
        raise Credencial(f"{contrato['nome']}: servidor de autorização recusou ({motivo}); o admin precisa autorizar de novo")
    d = r.json()
    if not d.get("access_token"):
        raise Credencial(f"{contrato['nome']}: resposta de token sem access_token")
    validade = float(d.get("expires_in") or a.get("validade_s") or 3600)
    # Google não devolve refresh_token na renovação: o anterior continua valendo.
    return Tokens(d["access_token"], d.get("refresh_token") or refresh_anterior, agora + validade)


def trocar_codigo(contrato: dict, app: AppOAuth, code: str, http: httpx.Client, agora: float | None = None) -> Tokens:
    tokens = _pedir_token(
        contrato, app, {"grant_type": "authorization_code", "code": code, "redirect_uri": app.redirect_uri}, http, time.time() if agora is None else agora
    )
    if not tokens.refresh_token:
        raise Credencial(f"{contrato['nome']}: o sistema não devolveu refresh_token; revise o escopo e o acesso offline")
    return tokens


def renovar(contrato: dict, app: AppOAuth, refresh_token: str, http: httpx.Client, agora: float | None = None) -> Tokens:
    return _pedir_token(contrato, app, {"grant_type": "refresh_token", "refresh_token": refresh_token}, http, time.time() if agora is None else agora, refresh_token)


# ---- entrega de token válido ao Leitor -----------------------------------------------------

class CofreTokens(Protocol):
    def ler(self, nome: str) -> str | None: ...
    def guardar(self, nome: str, segredo: str) -> None: ...


def nome_no_cofre(tenant: str, saas: str) -> str:
    return f"lastro:{tenant}:oauth:{saas}"


class GerenteToken:
    """Dá ao `Leitor` um token de acesso válido; renova e regrava no cofre quando precisa."""

    def __init__(self, contrato: dict, app: AppOAuth, cofre: CofreTokens, tenant: str, saas: str,
                 http: httpx.Client, relogio: Relogio | None = None):
        self.contrato, self.app, self.cofre, self.http = contrato, app, cofre, http
        self.nome = nome_no_cofre(tenant, saas)
        self.relogio = relogio or RelogioReal()
        self.renovacoes = 0
        guardado = cofre.ler(self.nome)
        if not guardado:
            raise Credencial(f"{contrato['nome']}: sem autorização; o admin precisa clicar em 'autorizar'")
        self.tokens = Tokens.do_cofre(guardado)

    def token(self) -> str:
        if self.tokens.expira_em - self.relogio.agora() < MARGEM_S:
            self.forcar_renovacao()
        return self.tokens.access_token

    def forcar_renovacao(self) -> None:
        self.tokens = renovar(self.contrato, self.app, self.tokens.refresh_token, self.http, self.relogio.agora())
        self.cofre.guardar(self.nome, self.tokens.para_cofre())  # o refresh antigo pode já estar morto
        self.renovacoes += 1
