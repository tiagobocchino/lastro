"""Gera uma nota da Caixa global por SaaS a partir do catálogo (os agentes acham pela busca)."""

from __future__ import annotations

from pathlib import Path

from ..caixa import gravar_nota
from ..config import CAIXA_GLOBAL
from .motor import carregar_catalogo


def gerar(destino: Path = CAIXA_GLOBAL / "fontes") -> list[Path]:
    feitas = []
    for k, c in carregar_catalogo().items():
        pag, lim = c["paginacao"], c.get("limite", {})
        linhas = [
            f"# Contrato\n\nOrigem: {c['confianca']}.\n\nURL base: `{c['base_url']}`.",
            f"# Autenticação\n\nTipo `{c['auth']['tipo']}`." + (f" Login em `{c['auth']['url_login']}`." if c["auth"].get("url_login") else ""),
            f"# Paginação\n\nTipo `{pag['tipo']}`, teto de {pag['maximo']} por página." + (" Total informado pela API: o motor confere truncamento." if c.get("envelope", {}).get("total") or pag["tipo"] == "cabecalho" else " A API não informa total."),
            "# Limites\n\n" + ", ".join(f"{a}: {b}" for a, b in lim.items()),
            "# Carga incremental\n\n" + (f"Parâmetro `{c['incremental']['param']}`." if c.get("incremental") else "Não tem: carga completa a cada execução."),
            "# Entidades\n\n" + "\n".join(f"- `{n}` em `{e['caminho']}`" for n, e in c["entidades"].items()),
            "# Armadilhas\n\n" + ("\n".join(f"- {a}" for a in c.get("armadilhas", [])) or "Nenhuma registrada ainda."),
        ]
        feitas.append(gravar_nota(destino, f"fonte-{k}", f"Contrato da API {c['nome']}: autenticação, paginação, limites e armadilhas", "fonte", "\n\n".join(linhas), tags=[k, "api", "conector", "saas"]))
    return feitas


if __name__ == "__main__":
    for p in gerar():
        print(p)
