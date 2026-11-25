"""Cargas incrementais agendadas por fonte (card LST-7, plano Operação).

Uma carga mantém uma fonte vinda de um SaaS atualizada todo dia, sem o demandante pedir de novo:

- **Marca d'água:** o início da última carga boa. A próxima pede só o que mudou desde ela, com 1 hora de
  sobreposição; o que vier repetido é deduplicado pela chave da entidade.
- **Cota diária:** o `Leitor` recebe um orçamento (cota do contrato menos o que as outras cargas do mesmo
  sistema já gastaram no dia) e para antes de passar dele. Ex.: Sienge pacote Free, 100 requisições por dia.
- **Tudo ou nada:** a fonte nova é escrita num arquivo temporário e só substitui a antiga (`os.replace`)
  se a extração inteira deu certo. Falha não move a marca d'água e vira aviso no portal.

Disparo: o Cloud Scheduler chama `POST /tarefas/cargas` de hora em hora; localmente, `lastro cargas`.
"""

from __future__ import annotations

import json
import os
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable
from zoneinfo import ZoneInfo

import httpx
import pandas as pd

from .saas import oauth
from .saas.motor import CotaEsgotada, Credencial, ErroSaaS, EscritaNaFonte, Leitor, Truncamento, carregar_catalogo, gravar_bronze
from .saas.simulador import Simulador

FUSO = ZoneInfo("America/Sao_Paulo")
SOBREPOSICAO_S = 3600
CAT = carregar_catalogo()


def nome_credencial(tenant: str, saas: str) -> str:
    return f"lastro:{tenant}:cred:{saas}"


def cota_do_contrato(saas: str, pacote: str | None) -> int | None:
    """Cota diária pelo pacote do cliente (ex.: Sienge Free = 100), quando o catálogo conhece."""
    por_pacote = CAT[saas].get("limite", {}).get("por_dia_por_pacote") or {}
    if pacote and pacote not in por_pacote:
        raise ValueError(f"{saas}: pacote '{pacote}' desconhecido; use {sorted(por_pacote)}")
    return por_pacote.get(pacote) if pacote else None


def _frase(e: Exception) -> str:
    t = str(e).strip()
    return t if t.endswith((".", "!", "?")) else t + "."


def _dia(epoch: float) -> str:
    return datetime.fromtimestamp(epoch, FUSO).date().isoformat()


def devida(carga: dict, agora: float) -> bool:
    """Roda uma vez por dia, a partir da hora marcada. Falha comum tenta de novo na hora seguinte;
    cota esgotada só no dia seguinte."""
    if not carga["ativa"]:
        return False
    local = datetime.fromtimestamp(agora, FUSO)
    if local.hour < carga["hora"]:
        return False
    hoje = local.date().isoformat()
    if carga["marca_dagua"] and _dia(carga["marca_dagua"]) == hoje:
        return False  # já tem carga boa de hoje
    return not (carga["ultimo_status"] == "cota" and carga["ultima_execucao"] and _dia(carga["ultima_execucao"]) == hoje)


def _leitor(carga: dict, cofre: Any, cliente: httpx.Client | None, orcamento: int | None) -> tuple[Leitor, Any]:
    saas, c = carga["saas"], CAT[carga["saas"]]
    if carga["modo"] == "sandbox":
        from .saas.servico import _oauth_no_sandbox  # noqa: PLC0415

        sim = Simulador(saas, n=180)
        http = httpx.Client(transport=sim.transporte())
        gerente = _oauth_no_sandbox(saas, sim, http) if c["auth"]["tipo"] == "oauth2_refresh" else None
        cred = {} if gerente else {k: "demo" for k in _campos(saas)}
        return Leitor(saas, cred, carga["variaveis"], cliente=http, relogio=sim.relogio, oauth=gerente, orcamento=orcamento), gerente
    http = cliente or httpx.Client(timeout=30)
    gerente = None
    cred: dict = {}
    if c["auth"]["tipo"] == "oauth2_refresh":
        gerente = oauth.GerenteToken(c, oauth.app_do_ambiente(saas, ""), cofre, carga["tenant_id"], saas, http)
    else:
        guardada = cofre.ler(nome_credencial(carga["tenant_id"], saas))
        if not guardada:
            raise Credencial(f"{c['nome']}: sem credencial guardada; o admin precisa refazer a conexão")
        cred = json.loads(guardada)
    return Leitor(saas, cred, carga["variaveis"], cliente=http, oauth=gerente, orcamento=orcamento), gerente


def _campos(saas: str) -> list[str]:
    from .saas.servico import campos_credencial  # noqa: PLC0415

    return campos_credencial(saas)


def _mesclar(destino: Path, registros: list[dict], chave: str) -> int:
    """Junta o que mudou na fonte existente, sem duplicar pela chave, e troca o arquivo de uma vez."""
    novo = pd.json_normalize(registros, sep="_") if registros else pd.DataFrame()
    if registros and chave not in novo.columns:
        raise ErroSaaS(f"a chave '{chave}' não veio nos registros: a fonte não foi alterada")
    antigo = pd.read_csv(destino, dtype=str, keep_default_na=False) if destino.exists() else pd.DataFrame()
    novo = novo.astype(object).where(pd.notna(novo), "").astype(str)
    junto = pd.concat([antigo, novo], ignore_index=True)
    if chave in junto.columns:
        junto = junto.drop_duplicates(subset=chave, keep="last")
    tmp = destino.with_name(f".{destino.name}.{os.getpid()}.tmp")
    junto.to_csv(tmp, index=False)
    os.replace(tmp, destino)  # atômico: quem lê vê a fonte velha inteira ou a nova inteira
    return len(junto)


def executar(banco: Any, cofre: Any, cfg: Any, carga: dict, agora: float | None = None,
             cliente: httpx.Client | None = None) -> dict:
    agora = time.time() if agora is None else agora
    repo = banco.repo(carga["tenant_id"], "agendador@lastro", "admin")
    hoje = _dia(agora)
    gasto_meu = carga["chamadas_no_dia"] if carga["dia_cota"] == hoje else 0
    gasto_sistema = sum(c["chamadas_no_dia"] for c in repo.cargas() if c["saas"] == carga["saas"] and c["dia_cota"] == hoje)
    orcamento = (carga["cota_diaria"] - gasto_sistema) if carga["cota_diaria"] else None
    resultado: dict = {"carga": carga["id"], "tenant": carga["tenant_id"], "saas": carga["saas"], "chamadas": 0}
    leitor = None
    try:
        if orcamento is not None and orcamento <= 0:
            raise CotaEsgotada(f"{carga['saas']}: cota diária do contrato já foi usada hoje ({carga['cota_diaria']} requisições)")
        fonte = repo.fontes([carga["fonte_id"]])
        if not fonte:
            raise ErroSaaS("a fonte desta carga não existe mais")
        leitor, _ = _leitor(carga, cofre, cliente, orcamento)
        desde = None
        if carga["marca_dagua"] and CAT[carga["saas"]].get("incremental"):
            desde = datetime.fromtimestamp(carga["marca_dagua"] - SOBREPOSICAO_S, timezone.utc)
        ext = leitor.extrair(carga["entidade"], desde=desde)
        gravar_bronze(cfg.pasta_tenant(carga["tenant_id"]) / "bronze", carga["tenant_id"], ext)
        linhas = _mesclar(Path(fonte[0]["caminho"]), ext.registros, carga["chave"])
        resultado |= {"status": "ok", "novos_ou_alterados": len(ext.registros), "linhas_na_fonte": linhas,
                      "incremental": desde is not None, "aviso": ""}
        campos = {"marca_dagua": agora, "ultimo_status": "ok", "ultimo_aviso": ""}
    except CotaEsgotada as e:
        resultado |= {"status": "cota", "aviso": f"{_frase(e)} Nada foi alterado; a carga volta amanhã."}
        campos = {"ultimo_status": "cota", "ultimo_aviso": resultado["aviso"]}
    except (Credencial, ErroSaaS, Truncamento, EscritaNaFonte, ValueError, OSError) as e:
        resultado |= {"status": "falhou", "aviso": f"{_frase(e)} Nada foi alterado; nova tentativa na próxima hora."}
        campos = {"ultimo_status": "falhou", "ultimo_aviso": resultado["aviso"]}
    resultado["chamadas"] = leitor.chamadas if leitor else 0
    repo.atualizar_carga(carga["id"], ultima_execucao=agora, dia_cota=hoje,
                         chamadas_no_dia=gasto_meu + resultado["chamadas"], **campos)
    repo.registrar("agendador", "executou_carga", {k: v for k, v in resultado.items() if k != "tenant"})
    return resultado


def executar_devidas(banco: Any, cofre: Any, cfg: Any, agora: float | None = None,
                     cliente: Callable[[], httpx.Client] | None = None) -> list[dict]:
    agora = time.time() if agora is None else agora
    feitas = []
    for carga in banco.cargas_ativas():
        if devida(carga, agora):
            feitas.append(executar(banco, cofre, cfg, carga, agora, cliente() if cliente else None))
    return feitas
