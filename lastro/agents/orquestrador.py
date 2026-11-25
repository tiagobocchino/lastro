"""Orquestrador: faz o grill, decide o plano e chama os especialistas em ordem.

O grill é obrigatório. Cada resposta vira uma nota de decisão na Caixa do tenant;
na próxima demanda sobre a mesma fonte, a pergunta já respondida não volta.
"""

from __future__ import annotations

import re
import unicodedata

from ..caixa import gravar_nota
from .base import Agente, Contexto


def _sem_acento(t: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFD", t.lower()) if unicodedata.category(c) != "Mn")


def _slug(t: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", _sem_acento(t)).strip("-")


def colunas_citadas(pergunta: str, colunas: list[str]) -> list[str]:
    """Colunas cujo nome (ou raiz do nome) aparece na pergunta."""
    p = _sem_acento(pergunta)
    pontos: dict[str, float] = {}
    for c in colunas:
        partes = [x for x in re.split(r"[_\W]+", _sem_acento(c)) if len(x) >= 4]
        bate = sum(1 for x in partes if re.search(rf"\b{re.escape(x[:-1] if x.endswith('s') else x)}", p))
        if bate:
            pontos[c] = bate + bate / len(partes)
    # Mais termos batidos primeiro: "valor vendido" prefere valor_vendido a valor_orcado.
    return sorted(pontos, key=lambda c: -pontos[c])


class Orquestrador(Agente):
    nome = "orquestrador"

    def decisoes_conhecidas(self, ctx: Contexto, fonte: str) -> dict[str, str]:
        conhecidas = {}
        prefixo = f"tenant:decisoes/decisao-{_slug(fonte)}-"
        for rel, nota in ctx.caixa.notas.items():
            if rel.startswith(prefixo):
                qid = rel[len(prefixo):].removesuffix(".md")
                for titulo, corpo in nota.secoes:
                    if titulo == "Resposta":
                        conhecidas[qid] = corpo.strip()
        return conhecidas

    def grill(self, ctx: Contexto) -> list[dict]:
        """Perguntas que faltam responder, cada uma com uma sugestão padrão."""
        perfis = ctx.memoria["perfis"]
        perguntas: list[dict] = []
        for view, perfil in perfis.items():
            fonte = perfil["fonte"]
            sabidas = self.decisoes_conhecidas(ctx, fonte)
            cols = perfil["colunas"]
            numeros = [c["nome"] for c in cols if c["papel"] == "numero" and not c["nome"].lower().endswith("id")]
            datas = [c["nome"] for c in cols if c["papel"] == "data"]
            citadas = colunas_citadas(ctx.pergunta, [c["nome"] for c in cols])
            medidas_citadas = [c for c in citadas if c in numeros]

            def add(qid: str, texto: str, sugestao: str, opcoes: list[str], persistir: bool = True) -> None:
                # Decisões da fonte (data, chave) ficam gravadas e não voltam.
                # Decisões da pergunta (medida, recorte) são perguntadas a cada demanda.
                if persistir and qid in sabidas:
                    ctx.respostas[f"{fonte}:{qid}"] = sabidas[qid]
                    return
                perguntas.append({"id": f"{fonte}:{qid}", "fonte": fonte, "pergunta": texto, "sugestao": sugestao, "opcoes": opcoes, "persistir": persistir})

            if numeros:
                add("medida", f"Em '{fonte}', qual coluna é o valor que a análise soma?", (medidas_citadas or numeros)[0], numeros, persistir=False)
            if datas:
                add("data", f"Em '{fonte}', qual data define o período?", datas[0], datas)
            repetidos = next((c["repetidos"] for c in cols if perfil["chaves_candidatas"] and c["nome"] == perfil["chaves_candidatas"][0]), 0)
            aviso = f" '{perfil['chaves_candidatas'][0]}' tem {repetidos} valores repetidos na fonte." if repetidos else ""
            add(
                "chave",
                f"Em '{fonte}', qual coluna identifica cada registro sem repetir? Linhas repetidas nessa chave serão removidas.{aviso}",
                (perfil["chaves_candidatas"] or ["(nenhuma: manter todas as linhas)"])[0],
                perfil["chaves_candidatas"] + ["(nenhuma: manter todas as linhas)"],
            )
            add(
                "filtro",
                f"Existe um recorte obrigatório em '{fonte}' (ex.: só um status ou uma empresa)? Escreva como condição SQL ou deixe 'nenhum'.",
                "nenhum",
                [],
                persistir=False,
            )
        gerais = self.decisoes_conhecidas(ctx, "geral")
        if "revisor" in gerais:
            ctx.respostas.setdefault("geral:revisor", gerais["revisor"])
        else:
            perguntas.append(
                {"id": "geral:revisor", "fonte": "geral", "pergunta": "Quem faz a segunda camada da auditoria (revisor de negócio)?", "sugestao": "revisor do tenant", "opcoes": [], "persistir": True}
            )
        extra = ctx.llm.responder(
            self.instrucoes(),
            f"Pergunta do demandante: {ctx.pergunta}\nColunas: {[c['nome'] for p in perfis.values() for c in p['colunas']]}\n"
            "Liste no máximo 2 termos ambíguos da pergunta, um por linha, só o termo.",
        )
        for termo in (extra or "").splitlines()[:2]:
            termo = termo.strip("-• ").strip()
            if termo:
                perguntas.append({"id": f"geral:termo-{_slug(termo)}", "fonte": "geral", "pergunta": f"O que '{termo}' significa nesta análise?", "sugestao": "", "opcoes": [], "persistir": True})
        self.anotar(ctx, "grill", {"perguntas": [q["id"] for q in perguntas], "ja_sabidas": len(ctx.respostas)})
        return perguntas

    def gravar_respostas(self, ctx: Contexto, perguntas: list[dict], respostas: dict[str, str]) -> None:
        """Respostas viram notas de decisão na Caixa do tenant (o agente fica mais contextualizado)."""
        for q in perguntas:
            valor = (respostas.get(q["id"]) or q["sugestao"] or "").strip()
            ctx.respostas[q["id"]] = valor
            fonte, qid = q["id"].split(":", 1)
            # Decisão da fonte (data, chave, revisor) fica em decisoes/ e não volta ao grill.
            # Decisão da demanda (medida, recorte) fica no histórico: a busca acha, o grill pergunta de novo.
            persistente = q.get("persistir", True)
            pasta = ctx.pasta_tenant_caixa / "decisoes" / ("" if persistente else "historico")
            nome = f"decisao-{fonte}-{qid}" if persistente else f"decisao-{fonte}-{qid}-demanda-{ctx.demanda_id}"
            termos = valor.replace("_", " ")
            gravar_nota(
                pasta,
                nome,
                f"Decisão do grill ({qid}): {termos} · {q['pergunta']}",
                "decisao",
                f"# Pergunta\n\n{q['pergunta']}\n\n# Resposta\n\n{valor}\n\n# Em palavras\n\n{termos}\n\n# Origem\n\nDemanda {ctx.demanda_id}: {ctx.pergunta}",
                tags=[fonte, qid],
            )
        ctx.caixa.reindexar()
        self.anotar(ctx, "gravou_decisoes", {"fonte": sum(1 for q in perguntas if q.get("persistir", True)), "historico": sum(1 for q in perguntas if not q.get("persistir", True))})
