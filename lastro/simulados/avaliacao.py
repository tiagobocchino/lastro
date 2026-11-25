"""Fase 2 do LST-36: os agentes do Lastro contra o gabarito da base GIMI simulada.

Usa o produto como um cliente usaria: empresa de teste, as planilhas como fontes, demandas em português,
grill respondido com as regras que cabem nele (status, corte de data, valor zero, registros de teste) e
execução normal (Arquiteto → Engenheiro → Analista → Auditor). O resultado de cada demanda é comparado
com o gabarito; o que não bate vira achado.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from . import gimi

FILTRO_CONTRATOS = ("status_nome = 'Aprovado' AND data_criacao >= '2024-01-01' AND valores_produtos > 0 "
                    "AND cliente_nome NOT ILIKE '%teste%' AND projeto_nome NOT ILIKE '%teste%'")
FILTRO_CARTEIRA = ("data_criacao >= '2024-01-01' AND valores_produtos > 0 "
                   "AND cliente_nome NOT ILIKE '%teste%' AND projeto_nome NOT ILIKE '%teste%'")
FILTRO_ITENS = ("contrato_status = 'Aprovado' AND contrato_data >= '2024-01-01' AND valor_contrato > 0 "
                "AND cliente_nome NOT ILIKE '%teste%' AND projeto_nome NOT ILIKE '%teste%'")


def _rodar(plat: Any, fonte_id: int, pergunta: str, respostas: dict[str, str]) -> dict:
    d = plat.abrir("avaliador@lastro", pergunta, [fonte_id])
    perguntas = {q["id"] for q in d["grill"]}
    d = plat.responder_grill(d["id"], "avaliador@lastro", {k: v for k, v in respostas.items() if k in perguntas})
    return plat.executar(d["id"], "avaliador@lastro")


def _por_grupo(d: dict, coluna_total: str | None = None) -> dict[str, float]:
    r = d["resultado"]["resposta"]
    i_valor = next((i for i, c in enumerate(r["colunas"]) if c.startswith("total_")), None) if coluna_total is None else r["colunas"].index(coluna_total)
    return {str(lin[0]): float(lin[i_valor]) for lin in r["linhas"] if i_valor is not None}


def avaliar(home: Path, contratos_por_empresa: int = 3000, semente: int = 36) -> dict:
    import os

    os.environ["LASTRO_HOME"] = str(home)
    from ..banco import BancoSqlite
    from ..config import carregar
    from ..servico import Plataforma

    base = gimi.gerar(semente, contratos_por_empresa)
    gab = gimi.gabarito(base)
    cfg = carregar()
    banco = BancoSqlite(cfg.banco)
    banco.criar_tenant("gimi-teste", "GIMI simulada (teste)")
    repo = banco.repo("gimi-teste", "avaliador@lastro", "admin")
    pasta = cfg.pasta_tenant("gimi-teste") / "fontes"
    gimi.exportar(base, pasta)
    fontes = {n: repo.adicionar_fonte(n, "arquivo", str(pasta / f"{n}.csv")) for n in ("contratos", "itens", "funcionarios")}
    plat = Plataforma(cfg, repo)
    checagens: list[dict] = []
    achados: list[str] = []

    def checar(nome: str, esperado: Any, obtido: Any, tolerancia: float = 0.05) -> bool:
        if isinstance(esperado, (int, float)) and isinstance(obtido, (int, float)):
            ok = abs(float(esperado) - float(obtido)) <= tolerancia
        else:
            ok = esperado == obtido
        checagens.append({"checagem": nome, "esperado": esperado, "obtido": obtido, "ok": ok})
        return ok

    # D1 · vendas por vendedor (contratos aprovados, com as regras de limpeza no recorte)
    r_cont = {"contratos:medida": "valores_produtos", "contratos:data": "data_criacao", "contratos:chave": "id",
              "contratos:filtro": FILTRO_CONTRATOS, "geral:revisor": "Tiago"}
    d1 = _rodar(plat, fontes["contratos"], "Quanto cada vendedor vendeu, em valor de produtos, nos contratos aprovados?", r_cont)
    checar("D1 total vendido (aprovados, sem teste, desde 2024, sem valor zero)", gab["vendido_total"], round(float(d1["resultado"]["resposta"]["total"]), 2))
    checar("D1 auditoria camada 1 aprovada", True, bool(d1["resultado"]["auditoria"]["aprovado_camada1"]))
    brutos = _por_grupo(d1)
    limpos: dict[str, float] = {}
    for nome, v in brutos.items():
        limpos[gimi.limpar_vendedor(nome)] = limpos.get(gimi.limpar_vendedor(nome), 0) + v
    esperado_nd = gab["vendido_por_vendedor"].get("NAO DEFINIDO", 0)
    checar("D1 soma por vendedor = total (sem vendedor fica de fora do agrupamento?)", gab["vendido_total"] - esperado_nd, round(sum(brutos.values()), 2), 1)
    if any(" - (" in n or "_" in n for n in brutos):
        achados.append("O agente agrupa pelo nome **bruto** do vendedor (\"Carla Moura - (…)\", \"diego_vaz\"). A regra de limpeza do ETL "
                       "(cortar \" - (\" e \"_\") não tem lugar no grill: o painel mostraria o mesmo vendedor com o nome do sistema.")
    if esperado_nd and "NAO DEFINIDO" not in brutos:
        achados.append(f"Contratos **sem vendedor** ({gimi.limpar_vendedor(None)} no ETL) somem do agrupamento por vendedor: "
                       f"{esperado_nd:,.2f} ficam fora da tabela, embora estejam no total.")
    checar("D1 por vendedor, depois de aplicar a limpeza do ETL", {k: round(v, 2) for k, v in gab["vendido_por_vendedor"].items() if k != "NAO DEFINIDO"},
           {k: round(v, 2) for k, v in sorted(limpos.items(), key=lambda kv: -kv[1])})
    achados.append("**Tipo de venda (GIMI × representante)** e **classe (texto entre parênteses do grupo)** são colunas derivadas por regra. "
                   "O grill só aceita recorte (WHERE): não há como o agente criar a coluna. O gabarito tem "
                   + ", ".join(f"{k}: {v:,.2f}" for k, v in gab["vendido_por_tipo_venda"].items()) + ".")

    # D2 · funil de orçamentos (toda a carteira limpa, por status)
    r_fun = r_cont | {"contratos:filtro": FILTRO_CARTEIRA}
    d2 = _rodar(plat, fontes["contratos"], "Como fica o funil de orçamentos, em valor de produtos, por status?", r_fun)
    rr = d2["resultado"]["resposta"]
    i_reg = rr["colunas"].index("registros") if "registros" in rr["colunas"] else None
    contagem = {str(lin[0]): int(lin[i_reg]) for lin in rr["linhas"]} if i_reg is not None else {}
    checar("D2 contratos por status (funil)", gab["funil"], dict(sorted(contagem.items(), key=lambda kv: -kv[1])))
    checar("D2 valor orçado total (carteira limpa)", gab["orcado_total"], round(float(rr["total"]), 2))

    # D3 · produtos por categoria de SKU (itens dos contratos aprovados)
    r_itens = {"itens:medida": "valores_total", "itens:data": "contrato_data", "itens:chave": "id", "itens:filtro": FILTRO_ITENS, "geral:revisor": "Tiago"}
    d3 = _rodar(plat, fontes["itens"], "Quanto vendemos por categoria de produto nos contratos aprovados?", r_itens)
    checar("D3 total vendido pelos itens", round(sum(gab["vendido_por_categoria"].values()), 2), round(float(d3["resultado"]["resposta"]["total"]), 2))
    achados.append("**Categoria de produto por prefixo de SKU** (ESQ = Esquadria, POR = Porta…, fora da lista = MATERIAL AVULSO) também é "
                   "regra derivada: o agente só enxerga o código do produto, que tem valores demais para virar dimensão.")

    # D4 · RH: funcionários ativos por setor
    r_rh = {"funcionarios:filtro": "ativo = true", "funcionarios:chave": "id", "geral:revisor": "Tiago"}
    try:
        d4 = _rodar(plat, fontes["funcionarios"], "Quantos funcionários ativos temos por setor?", r_rh)
        rr4 = d4["resultado"]["resposta"]
        cols4 = rr4["colunas"]
        i4 = cols4.index("registros") if "registros" in cols4 else None
        i_setor = cols4.index("setor_nome") if "setor_nome" in cols4 else 0
        obtido4: Any = {str(lin[i_setor]): int(lin[i4]) for lin in rr4["linhas"]} if i4 is not None else rr4
        checar("D4 funcionários ativos por setor", gab["rh_ativos_por_setor"], dict(sorted(obtido4.items())) if isinstance(obtido4, dict) else obtido4)
        extras = [c for c in cols4[:i_setor] if c != "setor_nome"]
        if extras:
            achados.append(f"No RH, o agente agrupou também por {', '.join(f'`{c}`' for c in extras)}: a palavra \"ativos\" da pergunta virou "
                           "dimensão, embora já esteja no filtro. O número por setor bate, mas a tabela ganha uma coluna inútil.")
        if cols4.count("registros") > 1:
            achados.append("Sem medida numérica, o Engenheiro gera `count(*) AS registros` **duas vezes** no SELECT "
                           "(`lastro/agents/construtores.py`): a contagem funciona, mas a coluna sai duplicada.")
        achados.append("**Contagem não é medida declarada:** o RH não tem coluna de valor, o grill fica sem `medida` e a contagem "
                       "só sai pelo `registros` implícito. \"Quantos funcionários\" deveria ter contagem como medida explícita.")
    except Exception as e:  # noqa: BLE001
        checar("D4 funcionários ativos por setor", gab["rh_ativos_por_setor"], f"falhou: {type(e).__name__}: {str(e)[:160]}")
        achados.append("**Contagem não é medida:** o RH não tem coluna de valor para somar, e o Arquiteto exige uma medida numérica. "
                       "\"Quantos funcionários\" precisa de contagem como medida.")

    return {"gabarito": gab, "checagens": checagens, "achados": achados,
            "demandas": {k: v["id"] for k, v in (("D1", d1), ("D2", d2), ("D3", d3))}}


def relatorio_md(r: dict) -> str:
    linhas = ["| Checagem | Gabarito | Agente | Bate |", "| --- | --- | --- | --- |"]
    for c in r["checagens"]:
        e, o = (json.dumps(x, ensure_ascii=False) if isinstance(x, dict) else str(x) for x in (c["esperado"], c["obtido"]))
        linhas.append(f"| {c['checagem']} | {e[:160]} | {o[:160]} | {'✅' if c['ok'] else '❌'} |")
    return "\n".join(linhas) + "\n\n## Achados\n\n" + "\n".join(f"{i}. {a}" for i, a in enumerate(r["achados"], 1)) + "\n"
