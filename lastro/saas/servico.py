"""Teste de conexão, importação como fonte e coleção do Postman para os SaaS do catálogo."""

from __future__ import annotations

import json
import re
import time
from datetime import date
from pathlib import Path
from typing import Any

import httpx
import pandas as pd

from .motor import incremental_da, Credencial, ErroSaaS, EscritaNaFonte, Leitor, Truncamento, carregar_catalogo, gravar_bronze, pegar
from .simulador import RelogioVirtual, Simulador

CAT = carregar_catalogo()


def resumo_catalogo() -> list[dict]:
    lista = []
    for k, c in CAT.items():
        lim = c.get("limite", {})
        limite = f"{lim['por_segundo']}/s" if lim.get("por_segundo") else (f"{lim['por_minuto']}/min" if lim.get("por_minuto") else "—")
        lista.append({
            "escopos": c["auth"].get("escopos", []),
            "id": k, "nome": c["nome"], "confianca": c["confianca"], "auth": c["auth"]["tipo"],
            "campos": campos_credencial(k), "paginacao": c["paginacao"]["tipo"], "maximo_pagina": c["paginacao"]["maximo"],
            "limite": limite, "incremental": (c.get("incremental") or next((e["incremental"] for e in c["entidades"].values() if e.get("incremental")), None) or {}).get("param"), "erro_200": bool(c.get("erro_200")),
            "entidades": list(c["entidades"]), "armadilhas": c.get("armadilhas", []), "variaveis_url": _variaveis(k),
            "pacotes": list((lim.get("por_dia_por_pacote") or {}).keys()),
        })
    return lista


def _variaveis(saas: str) -> list[str]:
    import string  # noqa: PLC0415

    c = CAT[saas]
    textos = [c["base_url"], c["auth"].get("url_login", "")] + [e["caminho"] for e in c["entidades"].values()]
    return sorted({f for t in textos for _, f, _, _ in string.Formatter().parse(t) if f})


def campos_credencial(saas: str) -> list[str]:
    a = CAT[saas]["auth"]
    campos = list(a.get("campos", [])) + list(a.get("cabecalhos", {}))
    if a["tipo"] == "bearer_estatico":  # OAuth2 não pede token no formulário: o admin autoriza no sistema
        campos.append("token")
    return campos


def _oauth_no_sandbox(saas: str, sim: Simulador, cliente: httpx.Client) -> Any:
    """Sandbox de sistema OAuth2: roda o fluxo inteiro no simulador, sem nada sair da plataforma.
    Troca o código por tokens, adianta o relógio para perto do vencimento e deixa o Leitor renovar."""
    from .oauth import AppOAuth, GerenteToken, nome_no_cofre, trocar_codigo  # noqa: PLC0415

    class CofreDaMemoria(dict):
        def ler(self, nome: str) -> str | None:
            return self.get(nome)

        def guardar(self, nome: str, segredo: str) -> None:
            self[nome] = segredo

    app = AppOAuth("app-sandbox", "segredo-sandbox", "http://sandbox/oauth/retorno")
    cofre = CofreDaMemoria()
    tokens = trocar_codigo(CAT[saas], app, Simulador.CODIGO_SANDBOX, cliente, sim.relogio.agora())
    cofre.guardar(nome_no_cofre("sandbox", saas), tokens.para_cofre())
    sim.relogio.t = tokens.expira_em - 60  # falta 1 minuto: a primeira chamada já precisa renovar
    return GerenteToken(CAT[saas], app, cofre, "sandbox", saas, cliente, sim.relogio)


def testar(saas: str, entidade: str, credenciais: dict, variaveis: dict, desde: date | None = None, modo: str = "sandbox",
           oauth: Any = None, cliente: httpx.Client | None = None) -> dict[str, Any]:
    """Roda uma extração e devolve um laudo legível. Sandbox usa o simulador (nada sai da plataforma)."""
    if saas not in CAT or entidade not in CAT[saas]["entidades"]:
        raise LookupError("SaaS ou entidade fora do catálogo")
    inicio = time.monotonic()
    sim = None
    if modo == "sandbox":
        sim = Simulador(saas, n=180)
        cliente = httpx.Client(transport=sim.transporte())
        relogio = sim.relogio
    elif modo == "real":
        cliente, relogio = cliente or httpx.Client(timeout=30), None
    else:
        raise ValueError("modo deve ser sandbox ou real")
    laudo: dict[str, Any] = {"saas": saas, "entidade": entidade, "modo": modo, "ok": False}
    try:
        if sim is not None and CAT[saas]["auth"]["tipo"] == "oauth2_refresh" and not credenciais.get("token"):
            oauth = _oauth_no_sandbox(saas, sim, cliente)
        lei = Leitor(saas, credenciais, variaveis, cliente=cliente, relogio=relogio, oauth=oauth)
        ext = lei.extrair(entidade, desde=desde)
        laudo |= {
            "ok": True, "registros": len(ext.registros), "total_informado": ext.total_informado, "chamadas": ext.chamadas,
            "tentativas_429": ext.tentativas_429, "relogins": ext.relogins, "avisos": ext.avisos,
            "truncamento": "conferido" if ext.total_informado is not None else "a API não informa total",
            "amostra": ext.registros[:3], "colunas": sorted({k for r in ext.registros[:50] for k in r}),
            "renovacoes_token": getattr(oauth, "renovacoes", 0),
            "_extracao": ext,
        }
        if isinstance(relogio, RelogioVirtual):
            laudo["tempo_real_estimado_s"] = round(relogio.dormido, 1)
    except (Credencial, ErroSaaS, Truncamento, EscritaNaFonte) as e:
        laudo |= {"erro": type(e).__name__, "mensagem": str(e)}
    laudo["duracao_s"] = round(time.monotonic() - inicio, 2)
    if sim is not None:
        laudo["tentativas_escrita_bloqueadas"] = sim.tentativas_escrita
        laudo["requisicoes_no_sandbox"] = len(sim.chamadas)
    return laudo


def importar_como_fonte(pasta_tenant: Path, tenant: str, laudo: dict) -> Path:
    """Grava a bronze e um CSV achatado (aninhados viram coluna com prefixo, lição da OMIE)."""
    ext = laudo["_extracao"]
    gravar_bronze(pasta_tenant / "bronze", tenant, ext)
    plano = pd.json_normalize(ext.registros, sep="_")
    destino = pasta_tenant / "fontes" / f"{ext.saas}_{ext.entidade}_{int(time.time())}.csv"
    destino.parent.mkdir(parents=True, exist_ok=True)
    plano.to_csv(destino, index=False)
    return destino


def colecao_postman(saas: str, base_sandbox: str) -> dict:
    """Coleção Postman v2.1: login (se houver), uma requisição por entidade e testes das armadilhas."""
    c = CAT[saas]
    pag = c["paginacao"]
    itens = []
    cab: list[dict] = []
    a = c["auth"]
    auth: dict | None = None
    if a["tipo"] == "basic":
        auth = {"type": "basic", "basic": [{"key": "username", "value": "{{usuario}}"}, {"key": "password", "value": "{{senha}}"}]}
    elif a["tipo"] in ("bearer_estatico", "oauth2_refresh", "login_bearer"):
        auth = {"type": "bearer", "bearer": [{"key": "token", "value": "{{token}}"}]}
    elif a["tipo"] == "api_key_header":
        cab = [{"key": nome, "value": a.get("prefixo", "") + "{{" + k + "}}"} for k, nome in a["cabecalhos"].items()]
    if a["tipo"] == "login_bearer":
        campo_tok = a.get("campo_token", "access_token")
        itens.append({
            "name": "0 · login",
            "event": [{"listen": "test", "script": {"exec": [
                "pm.test('login 200', () => pm.response.to.have.status(200));",
                f"pm.collectionVariables.set('token', pm.response.json()['{campo_tok}']);",
            ]}}],
            "request": {"method": "POST", "header": [{"key": "Content-Type", "value": "application/json"}],
                        "body": {"mode": "raw", "raw": json.dumps({k: "{{" + k + "}}" for k in a["campos"]})},
                        "url": "{{url_login}}"},
        })
    regra = c.get("erro_200")
    lim = c.get("limite", {})
    espera_ms = int(1100 / lim["por_segundo"]) if lim.get("por_segundo") else (int(61000 / lim["por_minuto"]) if lim.get("por_minuto") else 0)
    for i, (nome, e) in enumerate(c["entidades"].items(), start=1):
        testes = ["pm.test('HTTP 200', () => pm.expect(pm.response.code).to.be.oneOf([200, 204]));"]
        if regra:
            if "valor_erro" in regra:
                testes.append(f"pm.test('sem erro escondido no HTTP 200', () => pm.expect(pm.response.json()['{regra['campo']}']).to.not.eql({json.dumps(regra['valor_erro'])}));")
            else:
                testes.append(f"pm.test('sem erro escondido no HTTP 200', () => pm.expect(pm.response.json()).to.not.have.property('{regra['campo']}'));")
        reg = e.get("registros") or pegar(c, "envelope.registros")
        if reg:
            testes.append(f"pm.test('lista de registros em {reg}', () => {{ const j = pm.response.json(); const v = '{reg}'.split('.').reduce((o, k) => o && o[k], j); pm.expect(v).to.be.an('array'); }});")
        maximo = int(e.get("maximo", pag["maximo"]))
        caminho = re.sub(r"\{(\w+)\}", r"{{\1}}", e["caminho"])
        if pag["tipo"] == "nenhuma":
            q = []
        elif pag["tipo"] == "offset":
            q = [{"key": pag["param_offset"], "value": "0"}, {"key": pag["param_limite"], "value": str(maximo)}]
        elif pag["tipo"] == "cursor":
            q = [{"key": pag["param_limite"], "value": str(maximo)}, {"key": pag["param_cursor"], "value": "", "disabled": True}]
        else:
            q = [{"key": pag["param_pagina"], "value": str(pag.get("primeira", 1))}, {"key": pag["param_limite"], "value": str(maximo)}]
        q += [{"key": k, "value": str(v)} for k, v in (e.get("params_fixos") or {}).items()]
        inc = incremental_da(c, nome)
        if inc:
            q.append({"key": inc["param"], "value": "2026-09-01" if inc["formato"] != "epoch" else "1788220800", "disabled": True})
        if c.get("rpc"):
            corpo = {"call": e["call"], "param": [{q[0]["key"]: int(q[0]["value"]), q[1]["key"]: int(q[1]["value"])}]} | {k: "{{" + k + "}}" for k in a["campos"]}
            req = {"method": "POST", "header": [{"key": "Content-Type", "value": "application/json"}], "body": {"mode": "raw", "raw": json.dumps(corpo, ensure_ascii=False)}, "url": "{{base_url}}" + caminho}
        else:
            req = {"method": "GET", "header": cab, "url": {"raw": "{{base_url}}" + caminho, "host": ["{{base_url}}"], "path": [p for p in caminho.split("/") if p], "query": q}}
        if auth:
            req["auth"] = auth
        eventos = [{"listen": "test", "script": {"exec": testes}}]
        if espera_ms:  # respeita o limite do contrato também no Postman/Newman (ex.: Bling, 3 por segundo)
            eventos.insert(0, {"listen": "prerequest", "script": {"exec": [f"setTimeout(() => {{}}, {espera_ms});"]}})
        itens.append({"name": f"{i} · {nome}", "event": eventos, "request": req})
    variaveis = [{"key": "base_url", "value": f"{base_sandbox}/sandbox/{saas}"}]
    if a.get("url_login"):
        variaveis.append({"key": "url_login", "value": f"{base_sandbox}/sandbox/{saas}/auth/" + a["url_login"].rstrip("/").split("/")[-1]})
    variaveis += [{"key": k, "value": "demo"} for k in campos_credencial(saas) + [v for v in _variaveis(saas) if v not in ("subdominio", "dominio")]]
    descricao = (
        f"{c['nome']} · contrato do catálogo Lastro ({c['confianca']}).\n\n"
        "Aponta para o sandbox do Lastro. Para a API real, troque base_url por "
        f"{c['base_url']} e use credenciais somente leitura do cliente.\n\nArmadilhas:\n- " + "\n- ".join(c.get("armadilhas", ["nenhuma registrada"]))
    )
    return {
        "info": {"name": f"Lastro · {c['nome']}", "description": descricao, "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json"},
        "item": itens,
        "variable": variaveis,
    }
