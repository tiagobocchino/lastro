"""Sheets API v4 e token do Google simulados, para testar o envio do BI para a planilha (LST-48)."""

from __future__ import annotations

import json
import re
from urllib.parse import parse_qs

import httpx


class GoogleFalso:
    def __init__(self):
        self.planilhas: dict[str, dict] = {}  # id → {"titulo", "abas": {titulo: {"id", "linhas", "colunas", "valores"}}}
        self.pedidos: list[str] = []
        self.renovacoes = 0
        self.token_valido = "at-1"
        self._n = 0

    def _id(self) -> int:
        self._n += 1
        return self._n

    def transporte(self) -> httpx.MockTransport:
        return httpx.MockTransport(self._tratar)

    def _tratar(self, req: httpx.Request) -> httpx.Response:
        u = str(req.url)
        self.pedidos.append(f"{req.method} {req.url.path}")
        if u.startswith("https://oauth2.googleapis.com/token"):
            corpo = parse_qs(req.content.decode())
            if corpo.get("grant_type") == ["refresh_token"]:
                self.renovacoes += 1
                self.token_valido = f"at-{self.renovacoes + 1}"
            return httpx.Response(200, json={"access_token": self.token_valido, "expires_in": 3600, "refresh_token": "rt-1"})
        if req.headers.get("authorization") != f"Bearer {self.token_valido}":
            return httpx.Response(401, json={"error": {"message": "token inválido"}})
        caminho = req.url.path.removeprefix("/v4/spreadsheets")
        if req.method == "POST" and caminho == "":
            d = json.loads(req.content)
            pid = f"planilha{self._id():020d}"
            abas = {s["properties"]["title"]: {"id": self._id(), "linhas": 1000, "colunas": 26, "valores": []} for s in d.get("sheets", [])}
            self.planilhas[pid] = {"titulo": d["properties"]["title"], "abas": abas}
            return httpx.Response(200, json=self._doc(pid))
        m = re.fullmatch(r"/([^/:]+)(:batchUpdate|/values:batchUpdate)?", caminho)
        pid, acao = m.group(1), m.group(2)
        if pid not in self.planilhas:
            return httpx.Response(404, json={"error": {"message": "não encontrada"}})
        p = self.planilhas[pid]
        if req.method == "GET":
            return httpx.Response(200, json=self._doc(pid))
        d = json.loads(req.content)
        if acao == ":batchUpdate":
            respostas = []
            for r in d["requests"]:
                if "addSheet" in r:
                    t = r["addSheet"]["properties"]["title"]
                    p["abas"][t] = {"id": self._id(), "linhas": 1000, "colunas": 26, "valores": []}
                    respostas.append({"addSheet": {"properties": {"title": t, "sheetId": p["abas"][t]["id"]}}})
                elif "updateSheetProperties" in r:
                    props = r["updateSheetProperties"]["properties"]
                    aba = next(a for a in p["abas"].values() if a["id"] == props["sheetId"])
                    aba["linhas"], aba["colunas"] = props["gridProperties"]["rowCount"], props["gridProperties"]["columnCount"]
                    aba["valores"] = [ln[: aba["colunas"]] for ln in aba["valores"][: aba["linhas"]]]
                    respostas.append({})
                elif "deleteSheet" in r:
                    t = next(t for t, a in p["abas"].items() if a["id"] == r["deleteSheet"]["sheetId"])
                    del p["abas"][t]
                    respostas.append({})
            return httpx.Response(200, json={"replies": respostas})
        assert d["valueInputOption"] == "RAW", "fórmula do cliente não pode virar fórmula na planilha"
        for bloco in d["data"]:
            t = re.fullmatch(r"'(.*)'!A1", bloco["range"]).group(1).replace("''", "'")
            aba = p["abas"][t]
            if len(bloco["values"]) > aba["linhas"]:
                return httpx.Response(400, json={"error": {"message": f"faixa maior que a grade da aba {t}"}})
            aba["valores"] = bloco["values"]
        return httpx.Response(200, json={})

    def _doc(self, pid: str) -> dict:
        return {"spreadsheetId": pid, "sheets": [{"properties": {"title": t, "sheetId": a["id"]}} for t, a in self.planilhas[pid]["abas"].items()]}
