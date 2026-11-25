"""Motor de leitura de SaaS dirigido por contrato (catalogo.yaml).

Lições da GIMI (IAPP, IMUV, OMIE) viraram regras do motor:
- Erro pode vir com HTTP 200: o corpo é a verdade (`erro_200`).
- Nunca inferir o fim da lista por lote menor que o pedido; usar total, páginas, cursor ou cabeçalho.
- A extração só vale se o número de registros bater com o total informado (truncamento).
- Respeitar o limite de requisições; 429 e 5xx tentam de novo com espera crescente.
- Só leitura: GET, ou POST de consulta em APIs RPC (Listar*/Consultar*/Pesquisar*) e o login.
"""

from __future__ import annotations

import json
import re
import time
from urllib.parse import quote
from dataclasses import dataclass, field
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any, Protocol

import httpx
import yaml

CATALOGO = Path(__file__).with_name("catalogo.yaml")
CHAMADAS_DE_LEITURA = ("Listar", "Consultar", "Pesquisar", "Obter")


class ErroSaaS(RuntimeError):
    """A API respondeu um erro lógico (inclusive com HTTP 200)."""


class Truncamento(RuntimeError):
    """Foram extraídos menos (ou mais) registros que o total informado pela API."""


class EscritaNaFonte(PermissionError):
    """Tentativa de chamada que não é leitura."""


class CotaEsgotada(ErroSaaS):
    """A próxima requisição passaria da cota diária do contrato do cliente (LST-7)."""


class Credencial(RuntimeError):
    """Credencial ausente, inválida ou expirada sem como renovar."""


def carregar_catalogo(caminho: Path = CATALOGO) -> dict[str, dict]:
    return yaml.safe_load(caminho.read_text(encoding="utf-8"))


def pegar(obj: Any, caminho: str | None) -> Any:
    """Lê `a.b.c` de um dicionário aninhado."""
    if not caminho:
        return None
    for parte in caminho.split("."):
        if not isinstance(obj, dict):
            return None
        obj = obj.get(parte)
    return obj


class Relogio(Protocol):
    def agora(self) -> float: ...
    def dormir(self, s: float) -> None: ...


class RelogioReal:
    def agora(self) -> float:
        return time.monotonic()

    def dormir(self, s: float) -> None:
        time.sleep(s)


class Limitador:
    """Espaça as chamadas para nunca passar do limite do contrato."""

    def __init__(self, limite: dict, relogio: Relogio):
        por_s = limite.get("por_segundo")
        por_min = limite.get("por_minuto")
        intervalo = 1.0 / por_s if por_s else (60.0 / por_min if por_min else 0.0)
        self.intervalo = max(intervalo, float(limite.get("pausa_s", 0.0)))
        self.relogio = relogio
        self.ultima: float | None = None

    def esperar(self) -> None:
        if self.ultima is not None and self.intervalo:
            falta = self.intervalo - (self.relogio.agora() - self.ultima)
            if falta > 0:
                self.relogio.dormir(falta)
        self.ultima = self.relogio.agora()


@dataclass
class Extracao:
    saas: str
    entidade: str
    registros: list[dict]
    total_informado: int | None
    chamadas: int
    desde: str | None
    tentativas_429: int = 0
    relogins: int = 0
    avisos: list[str] = field(default_factory=list)


class Leitor:
    def __init__(
        self,
        saas: str,
        credenciais: dict[str, str],
        variaveis_url: dict[str, str] | None = None,
        cliente: httpx.Client | None = None,
        relogio: Relogio | None = None,
        catalogo: dict | None = None,
        max_tentativas: int = 5,
        oauth: Any = None,
        orcamento: int | None = None,
    ):
        cat = catalogo or carregar_catalogo()
        if saas not in cat:
            raise KeyError(f"SaaS desconhecido: {saas}")
        self.saas = saas
        self.c = cat[saas]
        self.cred = credenciais
        self.vars = variaveis_url or {}
        self.http = cliente or httpx.Client(timeout=30)
        self.relogio = relogio or RelogioReal()
        self.limitador = Limitador(self.c.get("limite", {}), self.relogio)
        self.max_tentativas = max_tentativas
        self.orcamento = orcamento  # máximo de requisições nesta execução (cota diária restante)
        self.oauth = oauth  # GerenteToken (lastro/saas/oauth.py): token renovado e guardado no cofre
        self.token: str | None = None
        self.chamadas = 0
        self.tentativas_429 = 0
        self.relogins = 0
        self._vars_url = self._validar_variaveis()
        faltando = [k for k in self.c["auth"].get("campos", []) if not self.cred.get(k)]
        if self.c["auth"]["tipo"] in ("bearer_estatico", "oauth2_refresh") and not self.cred.get("token") and not self.oauth:
            faltando.append("token")
        if self.c["auth"]["tipo"] == "api_key_header":
            faltando += [k for k in self.c["auth"]["cabecalhos"] if not self.cred.get(k)]
        if faltando:
            raise Credencial(f"{saas}: faltam credenciais {sorted(set(faltando))}")

    # ---- montagem ------------------------------------------------------------------
    def _validar_variaveis(self) -> dict[str, str]:
        """Variável no host só aceita [a-z0-9-]; no caminho, é codificada. Impede desviar a credencial."""
        hosts = set()
        for modelo in (self.c["base_url"], self.c["auth"].get("url_login", "")):
            host = modelo.split("://", 1)[-1].split("/", 1)[0]
            hosts |= set(re.findall(r"\{(\w+)\}", host))
        seguras = {}
        for k, v in self.vars.items():
            v = str(v)
            if k in hosts:
                if not re.fullmatch(r"[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?", v):
                    raise ValueError(f"{self.saas}: variável de host '{k}' inválida: use só letras minúsculas, números e hífen")
                seguras[k] = v
            else:
                seguras[k] = quote(v, safe="")
        return seguras

    def _url(self, caminho: str) -> str:
        return self.c["base_url"].format(**self._vars_url).rstrip("/") + caminho.format(**self._vars_url)

    def _cabecalhos(self) -> dict[str, str]:
        a = self.c["auth"]
        t = a["tipo"]
        if t == "basic":
            import base64  # noqa: PLC0415

            par = f"{self.cred['usuario']}:{self.cred['senha']}".encode()
            return {"Authorization": "Basic " + base64.b64encode(par).decode()}
        if t == "api_key_header":
            pref = a.get("prefixo", "")
            return {cab: pref + self.cred[k] for k, cab in a["cabecalhos"].items()}
        if t == "oauth2_refresh" and self.oauth:
            return {"Authorization": f"Bearer {self.oauth.token()}"}
        if t in ("bearer_estatico", "oauth2_refresh"):
            return {"Authorization": f"Bearer {self.cred['token']}"}
        if t == "email_token_header":
            return {"email": self.cred["email"], "token": self.cred["token"]}
        if t == "login_bearer":
            if not self.token:
                self._login()
            return {"Authorization": f"Bearer {self.token}"}
        return {}

    def _login(self) -> None:
        a = self.c["auth"]
        corpo = {k: self.cred[k] for k in a["campos"]}
        r = self.http.post(a["url_login"].format(**self._vars_url), json=corpo)
        self.chamadas += 1
        if r.status_code >= 400:
            raise Credencial(f"{self.saas}: login recusado ({r.status_code})")
        dados = r.json()
        self.token = dados.get(a.get("campo_token", "access_token"))
        if not self.token:
            raise Credencial(f"{self.saas}: login sem token na resposta")

    # ---- uma chamada --------------------------------------------------------------
    def _chamar(self, caminho: str, params: dict, call: str | None = None) -> httpx.Response:
        rpc = bool(self.c.get("rpc"))
        if rpc and not (call or "").startswith(CHAMADAS_DE_LEITURA):
            raise EscritaNaFonte(f"{self.saas}: chamada '{call}' não é de leitura")
        relogou = False
        for tentativa in range(1, self.max_tentativas + 1):
            if self.orcamento is not None and self.chamadas >= self.orcamento:
                raise CotaEsgotada(f"{self.saas}: cota diária do contrato esgotada ({self.orcamento} requisições restantes hoje)")
            self.limitador.esperar()
            cab = self._cabecalhos()
            if rpc:
                corpo = {"call": call, "param": [params]} | {k: self.cred[k] for k in self.c["auth"]["campos"]}
                r = self.http.post(self._url(caminho), json=corpo, headers=cab)
            else:
                r = self.http.get(self._url(caminho), params=params, headers=cab)
            self.chamadas += 1
            if r.status_code == 401 and self.c["auth"]["tipo"] == "login_bearer" and not relogou:
                self.token, relogou = None, True
                self.relogins += 1
                continue
            if r.status_code == 401 and self.oauth and not relogou:  # token revogado ou vencido antes da hora
                self.oauth.forcar_renovacao()
                relogou = True
                self.relogins += 1
                continue
            if r.status_code == 429 or r.status_code >= 500:
                self.tentativas_429 += r.status_code == 429
                if tentativa == self.max_tentativas:
                    raise ErroSaaS(f"{self.saas}: {r.status_code} após {tentativa} tentativas em {caminho}")
                espera = float(r.headers.get("Retry-After") or 2 ** tentativa)
                self.relogio.dormir(espera)
                continue
            if r.status_code in (401, 403):
                raise Credencial(f"{self.saas}: acesso negado ({r.status_code}) em {caminho}")
            if r.status_code >= 400:
                raise ErroSaaS(f"{self.saas}: HTTP {r.status_code} em {caminho}: {r.text[:200]}")
            self._checar_erro_200(r, caminho)
            return r
        raise ErroSaaS(f"{self.saas}: sem resposta válida em {caminho}")  # pragma: no cover

    def _checar_erro_200(self, r: httpx.Response, caminho: str) -> None:
        regra = self.c.get("erro_200")
        if not regra or r.status_code == 204 or not r.content:
            return
        corpo = r.json()
        if not isinstance(corpo, dict):
            return
        valor = corpo.get(regra["campo"])
        if "valor_erro" in regra:
            if valor == regra["valor_erro"]:
                raise ErroSaaS(f"{self.saas}: erro com HTTP 200 em {caminho}: {corpo.get('code') or corpo.get('message') or corpo}")
        elif valor:
            raise ErroSaaS(f"{self.saas}: erro com HTTP 200 em {caminho}: {valor}")

    # ---- extração -----------------------------------------------------------------
    def extrair(self, entidade: str, desde: date | datetime | None = None, filtros: dict | None = None) -> Extracao:
        e = self.c["entidades"][entidade]
        pag = self.c["paginacao"]
        maximo = int(e.get("maximo", pag["maximo"]))
        caminho_reg = e.get("registros") or pegar(self.c, "envelope.registros")
        params = dict(e.get("params_fixos") or {}) | dict(filtros or {})
        inc = self.c.get("incremental")
        if desde is not None:
            if not inc:
                raise ValueError(f"{self.saas} não tem filtro incremental no contrato")
            momento = desde if isinstance(desde, datetime) else datetime.combine(desde, datetime.min.time(), timezone.utc)
            params[inc["param"]] = int(momento.timestamp()) if inc["formato"] == "epoch" else momento.strftime(inc["formato"])
        registros: list[dict] = []
        total: int | None = None
        tipo = pag["tipo"]
        pagina = int(pag.get("primeira", 1))
        offset = 0
        cursor: str | None = None
        while True:
            p = dict(params)
            if tipo == "offset":
                p[pag["param_offset"]], p[pag["param_limite"]] = offset, maximo
            elif tipo in ("pagina", "pagina_total", "cabecalho"):
                p[pag["param_pagina"]], p[pag["param_limite"]] = pagina, maximo
            elif tipo == "cursor":
                p[pag["param_limite"]] = maximo
                if cursor:
                    p[pag["param_cursor"]] = cursor
            r = self._chamar(e["caminho"], p, call=e.get("call"))
            if r.status_code == 204 or not r.content:
                break
            corpo = r.json()
            lote = (pegar(corpo, caminho_reg) if caminho_reg else corpo) or []
            if not isinstance(lote, list):
                raise ErroSaaS(f"{self.saas}: resposta sem lista em '{caminho_reg}'")
            if e.get("formato") == "matriz":
                lote = matriz_para_registros(lote)
            registros.extend(lote)
            if tipo == "nenhuma":
                break
            if tipo == "offset":
                t = pegar(corpo, pegar(self.c, "envelope.total"))
                total = int(t) if t is not None else total
                offset += len(lote)
                if not lote or (total is not None and offset >= total) or (total is None and len(lote) < maximo):
                    break
            elif tipo == "pagina_total":
                total = int(pegar(corpo, pegar(self.c, "envelope.total")) or 0)
                paginas = int(pegar(corpo, pegar(self.c, "envelope.paginas")) or 0)
                if not lote or pagina >= paginas:
                    break
                pagina += 1
            elif tipo == "cabecalho":
                total = int(r.headers.get(pag["cab_total"], 0))
                if pagina >= int(r.headers.get(pag["cab_paginas"], 0)) or not lote:
                    break
                pagina += 1
            elif tipo == "pagina":
                t = pegar(corpo, pegar(self.c, "envelope.total"))
                total = int(t) if t is not None else None
                if not lote or (total is not None and len(registros) >= total):
                    break
                pagina += 1
            elif tipo == "cursor":
                cursor = pegar(corpo, pag["cursor_resposta"])
                if not cursor:
                    break
        if total is not None and len(registros) != total:
            raise Truncamento(f"{self.saas}.{entidade}: extraídos {len(registros)}, API informou {total}")
        ext = Extracao(self.saas, entidade, registros, total, self.chamadas, str(desde) if desde else None, self.tentativas_429, self.relogins)
        if total is None:
            ext.avisos.append("API não informa total: truncamento não pôde ser conferido")
        return ext


def matriz_para_registros(linhas: list[list]) -> list[dict]:
    """Primeira linha é o cabeçalho. Linhas curtas (células vazias no fim omitidas) são completadas com ""."""
    if not linhas:
        return []
    cab = [str(c) for c in linhas[0]]
    return [dict(zip(cab, list(l) + [""] * (len(cab) - len(l)))) for l in linhas[1:]]


def gravar_bronze(raiz: Path, tenant: str, ext: Extracao, quando: date | None = None) -> Path:
    """Bronze no padrão da GIMI: {saas}/{entidade}/tenant=/data_extracao=/ + metadados ao lado."""
    quando = quando or date.today()
    pasta = raiz / ext.saas / ext.entidade / f"tenant={tenant}" / f"data_extracao={quando.isoformat()}"
    pasta.mkdir(parents=True, exist_ok=True)
    arq = pasta / "dados.jsonl"
    with arq.open("w", encoding="utf-8") as f:
        for r in ext.registros:
            f.write(json.dumps(r, ensure_ascii=False, default=str) + "\n")
    meta = {
        "saas": ext.saas, "entidade": ext.entidade, "tenant": tenant, "data_extracao": quando.isoformat(),
        "registros": len(ext.registros), "total_informado": ext.total_informado, "chamadas": ext.chamadas,
        "desde": ext.desde, "tentativas_429": ext.tentativas_429, "relogins": ext.relogins, "avisos": ext.avisos,
    }
    (pasta / "_meta.json").write_text(json.dumps(meta, ensure_ascii=False, indent=1), encoding="utf-8")
    return arq
