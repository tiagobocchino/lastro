"""BI sem atrito C (LST-48): as tabelas prontas do BI (`painel_*`) numa planilha Google do próprio cliente,
para o Data Studio ler com o conector nativo de planilha (sem certificado, sem senha de banco).

- Escopo `drive.file`: o Lastro só alcança a planilha que ele mesmo criou; nada mais no Drive do cliente.
- Uma aba por tabela pronta, gravada com `RAW`: texto que começa com '=' fica texto (sem injeção de fórmula).
- Cada aba é redimensionada ao tamanho exato dos dados: célula vazia também conta no limite de 10 milhões.
- Abas `painel_*` de demandas que saíram do BI são removidas; outras abas que o cliente criar ficam intactas.
"""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import Any

import httpx

SAAS = "planilha_bi"  # nome no cofre e no state do OAuth
API = "https://sheets.googleapis.com/v4/spreadsheets"
LIMITE_CELULAS = 9_000_000  # o Google aceita 10 milhões por planilha; folga para o cliente criar as próprias abas
PREFIXO = "painel_"

CONTRATO: dict = {
    "nome": "Planilha Google do BI",
    "app_oauth": "google_sheets",  # mesmo aplicativo Google do conector de planilhas (LASTRO_OAUTH_GOOGLE_SHEETS_*)
    "auth": {
        "tipo": "oauth2_refresh",
        "escopos": ["https://www.googleapis.com/auth/drive.file"],
        "escopo": "https://www.googleapis.com/auth/drive.file",
        "url_autorizar": "https://accounts.google.com/o/oauth2/v2/auth",
        "url_token": "https://oauth2.googleapis.com/token",
        "cliente_no": "corpo",
        "params_autorizar": {"access_type": "offline", "prompt": "consent"},
        "validade_s": 3600,
        "refresh_rotativo": False,
    },
}


class ErroPlanilha(RuntimeError):
    pass


def celula(v: Any) -> Any:
    """Valor que a Sheets API aceita em JSON. Data vira AAAA-MM-DD (o Data Studio reconhece como data)."""
    if v is None:
        return ""
    if isinstance(v, bool | int | float | str):
        return v
    if isinstance(v, Decimal):
        return float(v)
    if isinstance(v, datetime):
        return v.isoformat(sep=" ", timespec="seconds")
    if isinstance(v, date):
        return v.isoformat()
    return str(v)


def url(planilha_id: str) -> str:
    return f"https://docs.google.com/spreadsheets/d/{planilha_id}/edit"


def _aba(nome: str) -> str:
    return "'" + nome.replace("'", "''") + "'"


class Planilha:
    """Cliente mínimo da Sheets API v4, com o token do `GerenteToken` (renova sozinho)."""

    def __init__(self, http: httpx.Client, token: Any):
        self.http, self.token = http, token

    def _pedir(self, metodo: str, caminho: str, **kw: Any) -> httpx.Response:
        r = self.http.request(metodo, API + caminho, headers={"Authorization": f"Bearer {self.token()}"}, **kw)
        if r.status_code == 401:  # token revogado no meio do caminho: uma nova tentativa com token renovado
            self.token(forcar=True)
            r = self.http.request(metodo, API + caminho, headers={"Authorization": f"Bearer {self.token()}"}, **kw)
        return r

    def abas(self, planilha_id: str) -> dict[str, int] | None:
        r = self._pedir("GET", f"/{planilha_id}", params={"fields": "sheets.properties(sheetId,title)"})
        if r.status_code in (403, 404):  # apagada pelo cliente ou fora do alcance do drive.file: cria outra
            return None
        self._ok(r, "ler a planilha")
        return {s["properties"]["title"]: s["properties"]["sheetId"] for s in r.json().get("sheets", [])}

    def criar(self, titulo: str) -> tuple[str, dict[str, int]]:
        r = self._pedir("POST", "", json={"properties": {"title": titulo, "locale": "pt_BR"},
                                          "sheets": [{"properties": {"title": "LEIA-ME"}}]})
        self._ok(r, "criar a planilha")
        d = r.json()
        return d["spreadsheetId"], {s["properties"]["title"]: s["properties"]["sheetId"] for s in d.get("sheets", [])}

    def lote(self, planilha_id: str, pedidos: list[dict]) -> dict:
        if not pedidos:
            return {}
        r = self._pedir("POST", f"/{planilha_id}:batchUpdate", json={"requests": pedidos})
        self._ok(r, "organizar as abas")
        return r.json()

    def gravar(self, planilha_id: str, dados: list[dict]) -> None:
        if not dados:
            return
        r = self._pedir("POST", f"/{planilha_id}/values:batchUpdate", json={"valueInputOption": "RAW", "data": dados})
        self._ok(r, "gravar os dados")

    @staticmethod
    def _ok(r: httpx.Response, acao: str) -> None:
        if r.status_code >= 400:
            try:
                msg = r.json().get("error", {}).get("message", "")
            except ValueError:
                msg = r.text[:200]
            raise ErroPlanilha(f"o Google recusou {acao} ({r.status_code}): {msg}")


def enviar(planilha: Planilha, tabelas: dict[str, tuple[list[str], list[tuple]]], planilha_id: str | None,
           titulo: str, agora: str) -> dict:
    """Grava cada tabela pronta numa aba. `tabelas`: nome → (colunas, linhas). Devolve id, link, abas e avisos."""
    abas = planilha.abas(planilha_id) if planilha_id else None
    if abas is None:
        planilha_id, abas = planilha.criar(titulo)
    avisos: list[str] = []
    escolhidas: dict[str, list[list]] = {}
    celulas = 0
    for nome, (cols, linhas) in sorted(tabelas.items()):
        valores = [cols] + [[celula(v) for v in ln] for ln in linhas]
        tamanho = len(valores) * max(len(cols), 1)
        if celulas + tamanho > LIMITE_CELULAS:
            avisos.append(f"{nome}: ficou fora da planilha (passaria do limite de células do Google); "
                          "use o Postgres ou o Power BI por HTTPS para esta tabela")
            continue
        celulas += tamanho
        escolhidas[nome] = valores
    pedidos: list[dict] = []
    for nome in escolhidas:
        if nome not in abas:
            pedidos.append({"addSheet": {"properties": {"title": nome}}})
    criadas = planilha.lote(planilha_id, pedidos)
    for resp in criadas.get("replies", []):
        if "addSheet" in resp:
            p = resp["addSheet"]["properties"]
            abas[p["title"]] = p["sheetId"]
    # tamanho exato de cada aba (encolher também apaga o que sobrou da versão anterior) e limpeza das abas velhas
    pedidos = [{"updateSheetProperties": {
        "properties": {"sheetId": abas[n], "gridProperties": {"rowCount": len(v), "columnCount": max(len(v[0]), 1),
                                                                "frozenRowCount": 1}},
        "fields": "gridProperties(rowCount,columnCount,frozenRowCount)"}} for n, v in escolhidas.items()]
    pedidos += [{"deleteSheet": {"sheetId": sid}} for t, sid in abas.items() if t.startswith(PREFIXO) and t not in escolhidas]
    planilha.lote(planilha_id, pedidos)
    leia = [["Lastro · tabelas prontas do BI"], [f"Atualizada em {agora}. O Lastro regrava as abas painel_* a cada publicação; não edite essas abas."],
            ["No Data Studio: Criar → Fonte de dados → Planilhas Google → esta planilha → uma aba painel_*."],
            ["Some a coluna 'registros' para contar. Categoria vazia aparece vazia: o rótulo para o vazio é regra do seu negócio."]]
    dados = [{"range": f"{_aba(n)}!A1", "values": v} for n, v in escolhidas.items()]
    if "LEIA-ME" in abas:
        dados.append({"range": "'LEIA-ME'!A1", "values": leia})
    planilha.gravar(planilha_id, dados)
    return {"planilha_id": planilha_id, "url": url(planilha_id), "avisos": avisos,
            "abas": [{"aba": n, "linhas": len(v) - 1, "colunas": len(v[0])} for n, v in escolhidas.items()]}
