"""Repo em memória para o modo visitante (card LST-38, ADR 0010).

Mesma interface do `Repo` usada pela `Plataforma` (demandas, fontes e rastro), sem banco: tudo some com o
objeto. O visitante do site nunca vira linha no SQLite nem no Postgres.
"""

from __future__ import annotations

import copy
import json
import time


class RepoMemoria:
    def __init__(self, tenant: str = "visitante"):
        self.tenant = tenant
        self._fontes: list[dict] = []
        self._demandas: dict[int, dict] = {}
        self._eventos: list[dict] = []

    def registrar(self, ator: str, acao: str, detalhe: dict | str, demanda_id: int | None = None) -> None:
        if not isinstance(detalhe, str):
            detalhe = json.dumps(detalhe, ensure_ascii=False, default=str)
        self._eventos.append({"demanda_id": demanda_id, "ator": ator, "acao": acao, "detalhe": detalhe, "em": time.time()})

    def eventos(self, demanda_id: int) -> list[dict]:
        return [{k: e[k] for k in ("ator", "acao", "detalhe", "em")} for e in self._eventos if e["demanda_id"] == demanda_id]

    def adicionar_fonte(self, nome: str, tipo: str, caminho: str) -> int:
        fid = len(self._fontes) + 1
        self._fontes.append({"id": fid, "tenant_id": self.tenant, "nome": nome, "tipo": tipo, "caminho": caminho, "criado_em": time.time()})
        return fid

    def fontes(self, ids: list[int] | None = None) -> list[dict]:
        return [dict(f) for f in self._fontes if ids is None or f["id"] in ids]

    def criar_demanda(self, autor: str, pergunta: str, fontes: list[int]) -> int:
        if not set(fontes) <= {f["id"] for f in self._fontes}:
            raise PermissionError("fonte fora desta sessão")
        did = len(self._demandas) + 1
        self._demandas[did] = {"id": did, "tenant_id": self.tenant, "autor": autor, "pergunta": pergunta, "fontes": list(fontes),
                               "status": "nova", "grill": [], "respostas": {}, "resultado": {}, "criado_em": time.time()}
        return did

    def demanda(self, demanda_id: int) -> dict | None:
        d = self._demandas.get(demanda_id)
        return copy.deepcopy(d) if d else None

    def demandas(self) -> list[dict]:
        return [copy.deepcopy(self._demandas[i]) for i in sorted(self._demandas, reverse=True)]

    def atualizar_demanda(self, demanda_id: int, **campos: object) -> None:
        if not set(campos) <= {"status", "grill", "respostas", "resultado"}:
            raise ValueError(sorted(set(campos) - {"status", "grill", "respostas", "resultado"}))
        d = self._demandas[demanda_id]
        for k, v in campos.items():
            d[k] = json.loads(v) if isinstance(v, str) and k != "status" else copy.deepcopy(v)

    def apagar(self) -> int:
        """Esquece tudo da sessão; devolve quantos registros havia (vai para o recibo)."""
        n = len(self._fontes) + len(self._demandas) + len(self._eventos)
        self._fontes.clear()
        self._demandas.clear()
        self._eventos.clear()
        return n
