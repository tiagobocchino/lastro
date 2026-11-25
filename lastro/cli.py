"""Linha de comando: `lastro demo`, `lastro serve`, `lastro buscar "<pergunta>"`."""

from __future__ import annotations

import argparse
import os
import shutil
import sys

from .banco import abrir_banco
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
    banco = abrir_banco(cfg)
    banco.criar_tenant(DEMO_TENANT, "Empresa Demo")
    for email, nome, papel in DEMO_USUARIOS:
        banco.criar_usuario(DEMO_TENANT, email, nome, papel, DEMO_SENHA)
    repo = banco.repo(DEMO_TENANT, "admin@demo.lastro", "admin")
    arq_politica = cfg.pasta_tenant(DEMO_TENANT) / "politica.yaml"
    if not arq_politica.exists():  # a demo mostra o plano Operação (cargas agendadas)
        from .politica import politica_padrao  # noqa: PLC0415

        pol = politica_padrao()
        pol.plano = "operacao"
        arq_politica.parent.mkdir(parents=True, exist_ok=True)
        pol.salvar(arq_politica)
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
    s.add_argument("--porta", type=int, default=int(os.environ.get("PORT", "8000")))
    sub.add_parser("cargas", help="roda as cargas agendadas que estão na hora (o Cloud Scheduler faz isso em produção)")
    pn = sub.add_parser("painel", help="gera o painel de operação (HTML) a partir do schema painel do Supabase")
    pn.add_argument("--saida", default="painel-operacao.html")
    pn.add_argument("--dias", type=int, default=30)
    b = sub.add_parser("buscar", help="busca na Caixa de Ferramenta global")
    b.add_argument("pergunta")
    a = p.parse_args(argv)
    if a.cmd == "demo":
        demo()
    elif a.cmd == "serve":
        import uvicorn  # noqa: PLC0415

        if os.environ.get("LASTRO_AMBIENTE", "local") != "producao":
            preparar_demo()  # contas de demonstração só fora de produção
        uvicorn.run("lastro.api:app", host="0.0.0.0", port=a.porta)
    elif a.cmd == "cargas":
        from .banco import abrir_banco as _abrir  # noqa: PLC0415
        from .cargas import executar_devidas  # noqa: PLC0415
        from .cofre import abrir_cofre  # noqa: PLC0415

        cfg = carregar()
        banco = _abrir(cfg)
        for r in executar_devidas(banco, abrir_cofre(cfg, banco), cfg):
            print(f"carga {r['carga']} ({r['tenant']}, {r['saas']}): {r['status']} · {r['chamadas']} requisições {r.get('aviso', '')}")
    elif a.cmd == "painel":
        from .painel import gerar  # noqa: PLC0415

        with open(a.saida, "w", encoding="utf-8") as f:
            f.write(gerar(dias=a.dias))
        print(f"painel gravado em {a.saida}")
    elif a.cmd == "buscar":
        caixa = Caixa({"global": CAIXA_GLOBAL})
        for t in caixa.buscar(a.pergunta):
            print(f"{t.pontuacao:.4f}  {t.caminho} § {t.secao}\n        {t.resumo}")


if __name__ == "__main__":
    main(sys.argv[1:])
