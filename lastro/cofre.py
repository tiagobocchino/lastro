"""Cofre de segredos dos clientes (tokens OAuth, credenciais somente leitura). Card LST-9.

- Produção: Supabase Vault (`vault.create_secret`, `vault.update_secret`, `vault.decrypted_secrets`). O segredo
  fica cifrado na tabela `vault.secrets`; só a conexão de dono do backend lê (o papel `authenticated` não alcança).
- Desenvolvimento: um arquivo JSON em LASTRO_HOME/cofre, com permissão 600, fora da pasta das empresas
  (que pode ser um bucket montado). Recusado em produção.

Nenhum segredo vai para as tabelas da plataforma, para o rastro de eventos ou para o laudo.
"""

from __future__ import annotations

import json
import os
from pathlib import Path


class CofreLocal:
    def __init__(self, pasta: Path):
        self.arquivo = pasta / "cofre" / "segredos.json"
        self.arquivo.parent.mkdir(parents=True, exist_ok=True)
        os.chmod(self.arquivo.parent, 0o700)

    def _tudo(self) -> dict[str, str]:
        return json.loads(self.arquivo.read_text()) if self.arquivo.exists() else {}

    def ler(self, nome: str) -> str | None:
        return self._tudo().get(nome)

    def guardar(self, nome: str, segredo: str) -> None:
        tudo = self._tudo() | {nome: segredo}
        tmp = self.arquivo.with_suffix(".tmp")
        tmp.write_text(json.dumps(tudo))
        os.chmod(tmp, 0o600)
        tmp.replace(self.arquivo)


class CofreSupabase:
    def __init__(self, banco):  # noqa: ANN001  (BancoPostgres; usa a conexão de dono)
        self.banco = banco

    def ler(self, nome: str) -> str | None:
        with self.banco._dono() as con:  # noqa: SLF001
            r = con.execute("SELECT decrypted_secret FROM vault.decrypted_secrets WHERE name = %s", (nome,)).fetchone()
        return r["decrypted_secret"] if r else None

    def guardar(self, nome: str, segredo: str) -> None:
        with self.banco._dono() as con:  # noqa: SLF001
            r = con.execute("SELECT id FROM vault.secrets WHERE name = %s", (nome,)).fetchone()
            if r:
                con.execute("SELECT vault.update_secret(%s, %s)", (r["id"], segredo))
            else:
                con.execute("SELECT vault.create_secret(%s, %s, %s)", (segredo, nome, "token OAuth de cliente do Lastro"))


def abrir_cofre(cfg, banco):  # noqa: ANN001, ANN201
    if getattr(cfg, "banco_url", ""):
        return CofreSupabase(banco)
    if os.environ.get("LASTRO_AMBIENTE", "local") == "producao":
        raise RuntimeError("produção exige o cofre do Supabase (LASTRO_BANCO_URL)")
    return CofreLocal(cfg.home)
