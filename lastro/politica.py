"""Política do tenant: plano de contrato e liberdades de cada agente.

Tudo começa desligado, menos ler as fontes conectadas e buscar na Caixa de Ferramenta.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import yaml

PLANOS = ("consulta", "pipeline", "operacao")

# O que cada plano permite, acima do mínimo.
PLANO_PERMITE = {
    "consulta": {"ler_fontes", "buscar_caixa", "sandbox_temporario"},
    "pipeline": {"ler_fontes", "buscar_caixa", "sandbox_temporario", "staging_persistente", "gerar_pipeline"},
    "operacao": {"ler_fontes", "buscar_caixa", "sandbox_temporario", "staging_persistente", "gerar_pipeline", "agendar_pipeline"},
}

PADRAO_AGENTE = {"ler_fontes", "buscar_caixa"}


class PermissaoNegada(PermissionError):
    pass


@dataclass
class Politica:
    plano: str = "consulta"
    agentes: dict[str, set[str]] = field(default_factory=dict)
    pesquisar_fora: bool = False

    def __post_init__(self) -> None:
        if self.plano not in PLANOS:
            raise ValueError(f"plano inválido: {self.plano}")

    def pode(self, agente: str, acao: str) -> bool:
        if acao == "pesquisar_fora":
            return self.pesquisar_fora and acao in self.agentes.get(agente, set())
        liberado = PADRAO_AGENTE | self.agentes.get(agente, set())
        return acao in liberado and acao in PLANO_PERMITE[self.plano]

    def exigir(self, agente: str, acao: str) -> None:
        if not self.pode(agente, acao):
            raise PermissaoNegada(f"agente '{agente}' não pode '{acao}' no plano '{self.plano}'")

    @classmethod
    def de_arquivo(cls, caminho: Path) -> "Politica":
        if not caminho.exists():
            return cls()
        dados = yaml.safe_load(caminho.read_text(encoding="utf-8")) or {}
        agentes = {k: set(v or []) for k, v in (dados.get("agentes") or {}).items()}
        return cls(plano=dados.get("plano", "consulta"), agentes=agentes, pesquisar_fora=bool(dados.get("pesquisar_fora", False)))

    def salvar(self, caminho: Path) -> None:
        caminho.parent.mkdir(parents=True, exist_ok=True)
        dados = {"plano": self.plano, "pesquisar_fora": self.pesquisar_fora, "agentes": {k: sorted(v) for k, v in self.agentes.items()}}
        caminho.write_text(yaml.safe_dump(dados, allow_unicode=True, sort_keys=True), encoding="utf-8")


def politica_padrao() -> Politica:
    """Liberdades típicas do plano Consulta."""
    return Politica(
        plano="consulta",
        agentes={
            "engenheiro": {"sandbox_temporario"},
            "analista": {"sandbox_temporario"},
            "auditor": {"sandbox_temporario"},
        },
    )
