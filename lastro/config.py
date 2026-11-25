"""Configuração lida do ambiente. Nenhum segredo tem valor padrão real."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

PACOTE = Path(__file__).resolve().parent
RAIZ = PACOTE.parent


@dataclass(frozen=True)
class Config:
    home: Path
    segredo: str
    llm_provedor: str
    llm_modelo: str
    llm_url: str
    llm_chave: str
    embedder: str = "nenhum"
    tenants: Path | None = None
    banco_url: str = ""

    @property
    def banco(self) -> Path:
        return self.home / "lastro.db"

    def pasta_tenant(self, tenant: str) -> Path:
        # Em produção, LASTRO_TENANTS aponta para o bucket montado (gs://<bucket>/tenants/<tenant>/).
        return (self.tenants or self.home / "tenants") / tenant


def carregar() -> Config:
    segredo = os.environ.get("LASTRO_SEGREDO", "")
    if os.environ.get("LASTRO_AMBIENTE", "local") == "producao" and len(segredo) < 32:
        raise RuntimeError("produção exige LASTRO_SEGREDO aleatório com pelo menos 32 caracteres")
    home = Path(os.environ.get("LASTRO_HOME", RAIZ / ".lastro")).resolve()
    home.mkdir(parents=True, exist_ok=True)
    return Config(
        home=home,
        segredo=segredo or "segredo-de-desenvolvimento-nao-use-em-producao",
        llm_provedor=os.environ.get("LASTRO_LLM", "nenhum"),
        llm_modelo=os.environ.get("LASTRO_LLM_MODELO", ""),
        llm_url=os.environ.get("LASTRO_LLM_URL", ""),
        llm_chave=os.environ.get("LASTRO_LLM_CHAVE", ""),
        embedder=os.environ.get("LASTRO_EMBEDDER", "nenhum"),
        banco_url=os.environ.get("LASTRO_BANCO_URL", ""),
        tenants=Path(os.environ["LASTRO_TENANTS"]).resolve() if os.environ.get("LASTRO_TENANTS") else None,
    )


CAIXA_GLOBAL = RAIZ / "caixa" / "global"
SKILLS = RAIZ / "skills"
