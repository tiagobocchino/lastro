"""Espelho da pasta de cada empresa no Supabase Storage (card LST-30, plano B da ADR 0009).

No Render gratuito, o disco some quando o serviço reinicia, publica de novo ou dorme. O código continua
lendo e gravando arquivos na pasta da empresa; este módulo:

- `restaurar`: quando a pasta não existe no disco, baixa tudo de `tenants/<empresa>/` antes do uso;
- `sincronizar`: depois de cada gravação, envia ao bucket só os arquivos novos ou alterados (manifesto local).

Sem LASTRO_STORAGE_URL nada disso liga: o modo local e o bucket montado da ADR 0007 seguem iguais.
A chave do Storage só existe em variável de ambiente; nunca é gravada, registrada no rastro ou devolvida.
"""

from __future__ import annotations

import json
import mimetypes
import os
from pathlib import Path
from urllib.parse import quote

import httpx

MANIFESTO = ".espelho.json"
IGNORAR_SUFIXOS = (".tmp", ".duckdb", ".duckdb.wal")


class ErroEspelho(RuntimeError):
    pass


class EspelhoStorage:
    def __init__(self, url: str, chave: str, bucket: str = "tenants", http: httpx.Client | None = None):
        self.base = url.rstrip("/") + "/storage/v1"
        self.bucket = bucket
        self.http = http or httpx.Client(timeout=60)
        # Chave secreta nova (sb_secret_...) vai só no apikey: não é JWT e quebra no Authorization.
        # A service_role antiga (JWT, "eyJ...") ainda aceita os dois (docs/infra/fontes/supabase-chaves-api.txt).
        self._cab = {"apikey": chave} | ({"Authorization": f"Bearer {chave}"} if chave.startswith("eyJ") else {})

    # ---- API do Storage ----------------------------------------------------------------
    def _pedir(self, metodo: str, url: str, **kw) -> httpx.Response:  # noqa: ANN003
        try:
            return self.http.request(metodo, url, **kw)
        except httpx.HTTPError as e:  # rede fora, DNS, proxy: vira erro do espelho, não derruba quem chamou
            raise ErroEspelho(f"Storage inacessível ({type(e).__name__})") from e

    def _objeto(self, chave_obj: str) -> str:
        return f"{self.base}/object/{self.bucket}/{quote(chave_obj)}"

    def enviar(self, arquivo: Path, chave_obj: str) -> None:
        tipo = mimetypes.guess_type(arquivo.name)[0] or "application/octet-stream"
        r = self._pedir("POST", self._objeto(chave_obj), content=arquivo.read_bytes(),
                        headers=self._cab | {"Content-Type": tipo, "x-upsert": "true"})
        if r.status_code >= 400:
            raise ErroEspelho(f"envio de {chave_obj} recusado pelo Storage (HTTP {r.status_code})")

    def baixar(self, chave_obj: str) -> bytes:
        r = self._pedir("GET", self._objeto(chave_obj), headers=self._cab)
        if r.status_code >= 400:
            raise ErroEspelho(f"download de {chave_obj} recusado pelo Storage (HTTP {r.status_code})")
        return r.content

    def apagar(self, chaves_obj: list[str]) -> None:
        r = self._pedir("DELETE", f"{self.base}/object/{self.bucket}", headers=self._cab, json={"prefixes": chaves_obj})
        if r.status_code >= 400:
            raise ErroEspelho(f"remoção recusada pelo Storage (HTTP {r.status_code})")

    def listar(self, prefixo: str) -> list[str]:
        """Todas as chaves de objeto sob o prefixo (a API lista uma pasta por vez)."""
        chaves, pendentes = [], [prefixo.rstrip("/")]
        while pendentes:
            pasta = pendentes.pop()
            offset = 0
            while True:
                r = self._pedir("POST", f"{self.base}/object/list/{self.bucket}", headers=self._cab,
                                json={"prefix": pasta, "limit": 1000, "offset": offset, "sortBy": {"column": "name", "order": "asc"}})
                if r.status_code >= 400:
                    raise ErroEspelho(f"listagem de {pasta} recusada pelo Storage (HTTP {r.status_code})")
                itens = r.json()
                for it in itens:
                    caminho = f"{pasta}/{it['name']}" if pasta else it["name"]
                    (chaves if it.get("id") else pendentes).append(caminho)  # sem id = subpasta
                if len(itens) < 1000:
                    break
                offset += 1000
        return chaves

    # ---- espelho da pasta da empresa ------------------------------------------------------
    def restaurar(self, pasta: Path, tenant: str) -> int:
        if pasta.exists() and any(pasta.iterdir()):
            return 0
        baixados = 0
        for chave_obj in self.listar(tenant):
            destino = pasta / chave_obj[len(tenant) + 1:]
            destino.parent.mkdir(parents=True, exist_ok=True)
            destino.write_bytes(self.baixar(chave_obj))
            baixados += 1
        self._salvar_manifesto(pasta, self._estado(pasta))
        return baixados

    def sincronizar(self, pasta: Path, tenant: str) -> int:
        if not pasta.exists():
            return 0
        antes = self._ler_manifesto(pasta)
        agora = self._estado(pasta)
        enviados = 0
        for rel, assinatura in sorted(agora.items()):
            if antes.get(rel) != assinatura:
                self.enviar(pasta / rel, f"{tenant}/{rel}")
                enviados += 1
        self._salvar_manifesto(pasta, agora)
        return enviados

    @staticmethod
    def _estado(pasta: Path) -> dict[str, list[int]]:
        estado = {}
        for arq in pasta.rglob("*"):
            if arq.is_file() and arq.name != MANIFESTO and not arq.name.endswith(IGNORAR_SUFIXOS) and not arq.name.startswith("."):
                st = arq.stat()
                estado[arq.relative_to(pasta).as_posix()] = [st.st_size, st.st_mtime_ns]
        return estado

    @staticmethod
    def _ler_manifesto(pasta: Path) -> dict:
        try:
            return json.loads((pasta / MANIFESTO).read_text())
        except (OSError, ValueError):
            return {}

    @staticmethod
    def _salvar_manifesto(pasta: Path, estado: dict) -> None:
        pasta.mkdir(parents=True, exist_ok=True)
        (pasta / MANIFESTO).write_text(json.dumps(estado))


def abrir_espelho() -> EspelhoStorage | None:
    url, chave = os.environ.get("LASTRO_STORAGE_URL", ""), os.environ.get("LASTRO_STORAGE_CHAVE", "")
    if not url:
        return None
    if not chave:
        raise RuntimeError("LASTRO_STORAGE_URL sem LASTRO_STORAGE_CHAVE")
    return EspelhoStorage(url, chave, os.environ.get("LASTRO_STORAGE_BUCKET", "tenants"))
