"""Simulador de SaaS: responde como a API real descrita no catálogo, com as armadilhas reais.

O mesmo simulador serve três usos:
1. testes automáticos (httpx.MockTransport),
2. o sandbox do portal ("testar conexão" sem tocar em sistema do cliente),
3. o Postman, pelas rotas /sandbox/{saas}/... da API.

Credenciais de sandbox: qualquer valor funciona, menos os que disparam armadilhas:
- "invalida"            -> 401
- "empresa_inexistente" -> erro com HTTP 200 (quando o contrato tem `erro_200`)
"""

from __future__ import annotations

import base64
import json
import re
import random
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Any
from urllib.parse import parse_qs, urlparse

import httpx

from .motor import carregar_catalogo, pegar

VERBOS_DE_ESCRITA = {"PUT", "PATCH", "DELETE"}


def _pôr(obj: dict, caminho: str, valor: Any) -> None:
    partes = caminho.split(".")
    for p in partes[:-1]:
        obj = obj.setdefault(p, {})
    obj[partes[-1]] = valor


class RelogioVirtual:
    """Relógio compartilhado pelo simulador e pelo motor nos testes: dormir não espera de verdade."""

    def __init__(self) -> None:
        self.t = 0.0
        self.dormido = 0.0

    def agora(self) -> float:
        return self.t

    def dormir(self, s: float) -> None:
        self.t += s
        self.dormido += s


@dataclass
class Simulador:
    saas: str
    n: int = 237
    semente: int = 7
    relogio: Any = None
    rajada_429: int = 0           # quantas respostas 429 seguidas soltar no começo
    expirar_token_apos: int = 0   # login_bearer: token vence depois de N chamadas (0 = nunca)
    validade_token_s: float = 0   # oauth2_refresh: validade do token emitido (0 = a do catálogo)
    catalogo: dict | None = None
    chamadas: list[dict] = field(default_factory=list)
    tentativas_escrita: int = 0

    def __post_init__(self) -> None:
        self.c = (self.catalogo or carregar_catalogo())[self.saas]
        self.relogio = self.relogio or RelogioVirtual()
        self._429_restantes = self.rajada_429
        self._tokens: dict[str, int] = {}
        self._oauth_acesso: dict[str, float] = {}   # token de acesso -> vence em
        self._oauth_refresh: set[str] = set()
        self.oauth_emitidos = 0
        self._janela: list[float] = []
        rnd = random.Random(self.semente)
        base = datetime(2026, 1, 1, tzinfo=timezone.utc)
        self.dados: dict[str, list[dict]] = {}
        for ent in self.c["entidades"]:
            regs = []
            for i in range(1, self.n + 1):
                atualizado = base + timedelta(days=rnd.randint(0, 320), hours=rnd.randint(0, 23))
                r = {
                    "id": i,
                    "nome": f"{ent[:-1] if ent.endswith('s') else ent} {i:04d}",
                    "valor": round(rnd.lognormvariate(10, 0.9), 2),
                    "status": rnd.choice(["aberto", "ganho", "perdido"]),
                    "atualizado_em": atualizado.strftime("%Y-%m-%dT%H:%M:%SZ"),
                }
                if self.saas == "google_sheets":  # última coluna às vezes vazia: a API omite a célula
                    r["observacao"] = rnd.choice(["", "", "conferir com o financeiro", "cliente novo"])
                if self.saas == "omie":  # campos aninhados viram colunas com prefixo
                    r["enderecoEntrega"] = {"cidade": rnd.choice(["São Paulo", "Recife", "Goiânia"]), "cep": f"{rnd.randint(10000, 99999)}-000"}
                    r["info"] = {"dInc": atualizado.strftime("%d/%m/%Y")}
                regs.append(r)
            self.dados[ent] = regs

    # ---- transporte para httpx --------------------------------------------------------
    def transporte(self) -> httpx.MockTransport:
        def handler(req: httpx.Request) -> httpx.Response:
            corpo: Any = None
            if req.content:
                if "x-www-form-urlencoded" in req.headers.get("content-type", ""):
                    from urllib.parse import parse_qsl  # noqa: PLC0415

                    corpo = dict(parse_qsl(req.content.decode()))
                else:
                    corpo = json.loads(req.content)
            st, cab, resp = self.responder(req.method, req.url.path, dict(req.url.params), dict(req.headers), corpo)
            return httpx.Response(st, headers=cab, content=b"" if resp is None else json.dumps(resp).encode())

        return httpx.MockTransport(handler)

    # ---- lógica -------------------------------------------------------------------------
    def responder(self, metodo: str, caminho: str, query: dict, cab: dict, corpo: Any) -> tuple[int, dict, Any]:
        cab = {k.lower(): v for k, v in cab.items()}
        self.chamadas.append({"metodo": metodo, "caminho": caminho, "query": query, "t": self.relogio.agora()})
        a = self.c["auth"]
        # login
        if a["tipo"] == "login_bearer" and caminho.endswith(urlparse(a["url_login"]).path.split("/")[-1]) and "auth" in caminho:
            if metodo != "POST":
                return 405, {}, {"erro": "use POST"}
            if (corpo or {}).get(a["campos"][-1]) == "invalida":
                return 401, {}, {"erro": "credenciais inválidas"}
            tok = base64.urlsafe_b64encode(f"{self.saas}-{len(self._tokens)}".encode()).decode()
            self._tokens[tok] = 0
            return 200, {}, {a.get("campo_token", "access_token"): tok, "token_type": "Bearer", "expires_in": 21600}
        if a["tipo"] == "oauth2_refresh" and a.get("url_token") and metodo == "POST" and caminho == urlparse(a["url_token"]).path:
            return self._servidor_de_token(cab, corpo or {})
        if metodo in VERBOS_DE_ESCRITA or (metodo == "POST" and not self.c.get("rpc")):
            self.tentativas_escrita += 1
            return 405, {}, {"erro": "o sandbox do Lastro só aceita leitura"}
        # limite de requisições
        if self._429_restantes > 0:
            self._429_restantes -= 1
            return 429, {"Retry-After": "2"}, {"erro": "Too Many Requests"}
        if not self._dentro_do_limite():
            return 429, {"Retry-After": "1"}, {"erro": "Too Many Requests"}
        # autenticação
        erro = self._autenticar(cab, corpo)
        if erro:
            return erro
        # entidade
        ent, e = self._entidade(caminho, corpo)
        if ent is None:
            return 404, {}, {"erro": f"recurso não encontrado: {caminho}"}
        if self._empresa_inexistente(cab, corpo) and self.c.get("erro_200"):
            regra = self.c["erro_200"]
            erro_corpo = {regra["campo"]: regra.get("valor_erro", "ERRO: empresa não encontrada"), "code": "ESTABELECIMENTO_NOT_FOUND", "message": "empresa não encontrada"}
            return 200, {}, erro_corpo
        params = (corpo or {}).get("param", [{}])[0] if self.c.get("rpc") else query
        regs = self._filtrar(self.dados[ent], params)
        return self._paginar(regs, e, params)

    def _dentro_do_limite(self) -> bool:
        lim = self.c.get("limite", {})
        janela, maximo = (1.0, lim["por_segundo"]) if lim.get("por_segundo") else (60.0, lim.get("por_minuto"))
        if not maximo:
            return True
        agora = self.relogio.agora()
        self._janela = [t for t in self._janela if agora - t < janela]
        if len(self._janela) >= maximo:
            return False
        self._janela.append(agora)
        return True

    def _autenticar(self, cab: dict, corpo: Any) -> tuple[int, dict, Any] | None:
        a = self.c["auth"]
        t = a["tipo"]
        nega = (401, {}, {"erro": "não autorizado"})
        if t == "basic":
            v = cab.get("authorization", "")
            if not v.startswith("Basic ") or "invalida" in base64.b64decode(v[6:]).decode(errors="ignore"):
                return nega
        elif t == "api_key_header":
            for cab_nome in a["cabecalhos"].values():
                v = cab.get(cab_nome.lower())
                if not v or "invalida" in v:
                    return nega
        elif t in ("bearer_estatico", "oauth2_refresh"):
            v = cab.get("authorization", "")
            if not v.startswith("Bearer ") or "invalida" in v:
                return nega
            tok = v[7:]
            if tok.startswith("sim-at-"):  # emitido pelo servidor de token simulado: confere validade
                vence = self._oauth_acesso.get(tok)
                if vence is None or vence <= self.relogio.agora():
                    return 401, {}, {"erro": "token expirado"}
        elif t == "login_bearer":
            tok = cab.get("authorization", "").removeprefix("Bearer ")
            if tok not in self._tokens:
                return nega
            self._tokens[tok] += 1
            if self.expirar_token_apos and self._tokens[tok] > self.expirar_token_apos:
                del self._tokens[tok]
                return 401, {}, {"erro": "token expirado"}
        elif t == "credencial_no_corpo":
            if not corpo or any(not corpo.get(k) or corpo.get(k) == "invalida" for k in a["campos"]):
                return 200, {}, {"faultstring": "ERROR: credenciais inválidas", "faultcode": "SOAP-ENV:Client-5113"}
        return None

    CODIGO_SANDBOX = "codigo-sandbox"

    def _servidor_de_token(self, cab: dict, corpo: dict) -> tuple[int, dict, Any]:
        """Imita o /oauth/token: troca de código, renovação, validade e refresh_token rotativo."""
        a = self.c["auth"]
        invalido = lambda sub: (400, {}, {"error": "invalid_grant", "error_subtype": sub})  # noqa: E731
        if a.get("cliente_no", "corpo") == "basic":
            ok_cliente = cab.get("authorization", "").startswith("Basic ")
        else:
            ok_cliente = bool(corpo.get("client_id") and corpo.get("client_secret"))
        if not ok_cliente:
            return 401, {}, {"error": "invalid_client"}
        tipo = corpo.get("grant_type")
        if tipo == "authorization_code":
            if corpo.get("code") != self.CODIGO_SANDBOX:
                return invalido("invalid_code")
        elif tipo == "refresh_token":
            rt = corpo.get("refresh_token", "")
            if rt not in self._oauth_refresh:
                return invalido("invalid_refresh_token")
            if a.get("refresh_rotativo", True):
                self._oauth_refresh.discard(rt)
        else:
            return 400, {}, {"error": "unsupported_grant_type"}
        self.oauth_emitidos += 1
        validade = self.validade_token_s or a.get("validade_s", 3600)
        acesso = f"sim-at-{self.oauth_emitidos}"
        self._oauth_acesso[acesso] = self.relogio.agora() + validade
        resposta = {"access_token": acesso, "token_type": "Bearer", "expires_in": validade}
        if tipo == "authorization_code" or a.get("refresh_rotativo", True):
            novo = f"sim-rt-{self.oauth_emitidos}"
            self._oauth_refresh.add(novo)
            resposta["refresh_token"] = novo
        return 200, {}, resposta

    def _empresa_inexistente(self, cab: dict, corpo: Any) -> bool:
        textos = list(cab.values()) + list((corpo or {}).values() if isinstance(corpo, dict) else [])
        return any(isinstance(v, str) and "empresa_inexistente" in v for v in textos)

    def _entidade(self, caminho: str, corpo: Any) -> tuple[str | None, dict]:
        for nome, e in self.c["entidades"].items():
            padrao = re.sub(r"\\\{[^}]+\\\}", "[^/]+", re.escape(e["caminho"].rstrip("/"))) + "$"
            if re.search(padrao, caminho.rstrip("/")):
                if self.c.get("rpc") and (corpo or {}).get("call") != e.get("call"):
                    continue
                return nome, e
        return None, {}

    def _filtrar(self, regs: list[dict], params: dict) -> list[dict]:
        inc = self.c.get("incremental")
        if not inc or inc["param"] not in params:
            return regs
        v = params[inc["param"]]
        if inc["formato"] == "epoch":
            corte = datetime.fromtimestamp(int(v), tz=timezone.utc)
        else:
            corte = datetime.strptime(str(v)[:10], "%Y-%m-%d").replace(tzinfo=timezone.utc)
        return [r for r in regs if datetime.strptime(r["atualizado_em"], "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc) >= corte]

    def _paginar(self, regs: list[dict], e: dict, params: dict) -> tuple[int, dict, Any]:
        pag = self.c["paginacao"]
        maximo = int(e.get("maximo", pag["maximo"]))
        caminho_reg = e.get("registros") or pegar(self.c, "envelope.registros")
        tipo = pag["tipo"]
        cab: dict[str, str] = {}
        corpo: dict[str, Any] = {}
        if tipo == "nenhuma":
            lote = regs
            if e.get("formato") == "matriz":
                colunas = list(regs[0]) if regs else []
                linhas = [colunas] + [[r.get(c, "") for c in colunas] for r in regs]
                for l in linhas[1:]:
                    while l and l[-1] == "":
                        l.pop()  # a API real omite células vazias no fim da linha
                lote = linhas
        elif tipo == "offset":
            ini = int(params.get(pag["param_offset"], 0))
            tam = min(int(params.get(pag["param_limite"], maximo)), maximo)
            lote = regs[ini:ini + tam]
            if pegar(self.c, "envelope.total"):
                _pôr(corpo, pegar(self.c, "envelope.total"), len(regs))
        elif tipo == "cursor":
            ini = int(base64.urlsafe_b64decode(params[pag["param_cursor"]]).decode()) if params.get(pag["param_cursor"]) else 0
            tam = min(int(params.get(pag["param_limite"], maximo)), maximo)
            lote = regs[ini:ini + tam]
            prox = base64.urlsafe_b64encode(str(ini + tam).encode()).decode() if ini + tam < len(regs) else None
            _pôr(corpo, pag["cursor_resposta"], prox)
        else:
            primeira = int(pag.get("primeira", 1))
            pagina = int(params.get(pag["param_pagina"], primeira))
            if pagina < primeira:
                return 400, {}, {"success": False, "code": "PAGE_MISSING_OR_INVALID"}
            tam = min(int(params.get(pag["param_limite"], maximo)), maximo)  # teto, mesmo pedindo mais
            ini = (pagina - primeira) * tam
            lote = regs[ini:ini + tam]
            paginas = max(1, -(-len(regs) // tam))
            if tipo == "pagina_total":
                _pôr(corpo, pegar(self.c, "envelope.total"), len(regs))
                _pôr(corpo, pegar(self.c, "envelope.paginas"), paginas)
                corpo["pagina"] = pagina
            elif tipo == "cabecalho":
                cab[pag["cab_total"]] = str(len(regs))
                cab[pag["cab_paginas"]] = str(paginas)
            elif tipo == "pagina":
                if pegar(self.c, "envelope.total"):
                    _pôr(corpo, pegar(self.c, "envelope.total"), len(regs))
                if not lote and self.saas == "kommo":
                    return 204, {}, None  # Kommo: fim da lista é 204 sem corpo
        if caminho_reg:
            _pôr(corpo, caminho_reg, lote)
            if self.c.get("erro_200", {}).get("valor_erro") is False:
                corpo["success"] = True
            return 200, cab, corpo
        return 200, cab, lote
