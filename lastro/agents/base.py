"""Base dos agentes: cada agente é uma skill (SKILL.md) + permissões + acesso à Caixa.

O agente nunca recebe o acervo inteiro: recebe o índice e busca o que precisa.
Cada passo fica no rastro (eventos do tenant).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from ..caixa import Caixa, Trecho, ler_nota
from ..config import SKILLS
from ..conectores import Sandbox
from ..llm import LLM
from ..politica import Politica


@dataclass
class Contexto:
    """Tudo que um agente pode tocar numa demanda."""

    demanda_id: int
    pergunta: str
    caixa: Caixa
    politica: Politica
    sandbox: Sandbox
    llm: LLM
    pasta_demanda: Path
    pasta_tenant_caixa: Path
    respostas: dict[str, str] = field(default_factory=dict)
    memoria: dict[str, Any] = field(default_factory=dict)  # resultados entre agentes
    rastro: list[dict] = field(default_factory=list)


class Agente:
    nome = "agente"

    def __init__(self) -> None:
        arq = SKILLS / self.nome / "SKILL.md"
        self.skill = ler_nota(arq, "global") if arq.exists() else None

    @property
    def descricao(self) -> str:
        return self.skill.descricao if self.skill else ""

    def instrucoes(self) -> str:
        if not self.skill:
            return ""
        return "\n\n".join(f"## {t}\n{c}" for t, c in self.skill.secoes)

    def anotar(self, ctx: Contexto, acao: str, detalhe: Any) -> None:
        ctx.rastro.append({"ator": self.nome, "acao": acao, "detalhe": detalhe})

    def buscar(self, ctx: Contexto, pergunta: str, k: int = 3) -> list[Trecho]:
        ctx.politica.exigir(self.nome, "buscar_caixa")
        achados = ctx.caixa.buscar(pergunta, k=k)
        self.anotar(ctx, "buscou_caixa", {"pergunta": pergunta, "achados": [f"{t.caminho} § {t.secao}" for t in achados]})
        return achados

    def executar(self, ctx: Contexto) -> Any:  # pragma: no cover - interface
        raise NotImplementedError
