"""Linha de comando: `lastro demo`, `lastro serve`, `lastro buscar "<pergunta>"`."""

from __future__ import annotations

import argparse
import shutil
import sys

from .banco import Repo, conectar, criar_tenant, criar_usuario
from .caixa import Caixa
from .config import CAIXA_GLOBAL, RAIZ, carregar
from .servico import Plataforma

DEMO_TENANT = "demo"
DEMO_USUARIOS = [
    ("ana@demo.lastro", "Ana (demandante)", "demandante"),
    ("rui@demo.lastro", "Rui (revisor de negócio)", "revisor"),
    ("admin@demo.lastro", "Admin da Demo", "admin"),
]
DEMO_SENHA = "demo1234"


def preparar_demo() -> tuple[Plataforma, int]:
    cfg = carregar()
    con = conectar(cfg.banco)
    criar_tenant(con, DEMO_TENANT, "Empresa Demo")
    for email, nome, papel in DEMO_USUARIOS:
        criar_usuario(con, DEMO_TENANT, email, nome, papel, DEMO_SENHA)
    repo = Repo(con, DEMO_TENANT)
    existentes = [f for f in repo.fontes() if f["nome"] == "orcamentos"]
    if existentes:
        return Plataforma(cfg, repo), existentes[0]["id"]
    origem = RAIZ / "exemplos" / "orcamentos.csv"
    destino = cfg.pasta_tenant(DEMO_TENANT) / "fontes" / "orcamentos.csv"
    destino.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy(origem, destino)
    fid = repo.adicionar_fonte("orcamentos", "arquivo", str(destino))
    return Plataforma(cfg, repo), fid


def demo() -> None:
    plat, fid = preparar_demo()
    pergunta = "Quanto cada vendedor vendeu, em valor vendido, nos contratos fechados?"
    d = plat.abrir("ana@demo.lastro", pergunta, [fid])
    print(f"Demanda {d['id']} aberta. Grill com {len(d['grill'])} perguntas:")
    for q in d["grill"]:
        print(f"  - {q['pergunta']}  [sugestão: {q['sugestao']}]")
    respostas = {"orcamentos:medida": "valor_vendido", "orcamentos:filtro": "status = 'Fechado'", "geral:revisor": "Rui"}
    d = plat.responder_grill(d["id"], "ana@demo.lastro", respostas)
    d = plat.executar(d["id"], "ana@demo.lastro")
    r, a = d["resultado"]["resposta"], d["resultado"]["auditoria"]
    print(f"\nResposta ({len(r['linhas'])} linhas), total {r['total']:,.2f}:")
    for linha in r["linhas"][:8]:
        print("  ", linha)
    print(f"\nAuditoria camada 1: {'aprovada' if a['aprovado_camada1'] else 'REPROVADA'}")
    for c in a["checagens"]:
        print(f"  [{'ok' if c['ok'] else c['nivel']}] {c['checagem']}: {c['detalhe']}")
    pasta = plat.pasta_demanda(d["id"])
    print(f"\nRelatório: {pasta / 'relatorio.html'}\nNotebook:  {pasta / 'auditoria_colab.ipynb'}\nPipeline:  {pasta / 'pipeline.py'}")
    d2 = plat.abrir("ana@demo.lastro", "Como evoluiu o valor orçado por mês em cada segmento?", [fid])
    print(f"\nSegunda demanda sobre a mesma fonte: {len(d2['grill'])} perguntas no grill (as decisões já tomadas não voltam).")


def main(argv: list[str] | None = None) -> None:
    p = argparse.ArgumentParser(prog="lastro")
    sub = p.add_subparsers(dest="cmd", required=True)
    sub.add_parser("demo", help="cria o tenant demo e roda uma demanda de ponta a ponta")
    s = sub.add_parser("serve", help="sobe a API e o portal")
    s.add_argument("--porta", type=int, default=8000)
    b = sub.add_parser("buscar", help="busca na Caixa de Ferramenta global")
    b.add_argument("pergunta")
    a = p.parse_args(argv)
    if a.cmd == "demo":
        demo()
    elif a.cmd == "serve":
        import uvicorn  # noqa: PLC0415

        preparar_demo()
        uvicorn.run("lastro.api:app", host="0.0.0.0", port=a.porta)
    elif a.cmd == "buscar":
        caixa = Caixa({"global": CAIXA_GLOBAL})
        for t in caixa.buscar(a.pergunta):
            print(f"{t.pontuacao:.4f}  {t.caminho} § {t.secao}\n        {t.resumo}")


if __name__ == "__main__":
    main(sys.argv[1:])
