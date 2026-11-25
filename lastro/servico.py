"""Ciclo de vida de uma demanda.

nova -> grill -> pronta -> em_revisao -> aprovada | reprovada

1. abrir: Explorador perfila as fontes; Orquestrador faz o grill.
2. responder_grill: respostas viram decisões na Caixa do tenant.
3. executar: Arquiteto -> Engenheiro -> Analista -> Auditor (camada 1).
4. revisar: humano de negócio (camada 2) aprova ou reprova; reprovação vira nota de aprendizado.
"""

from __future__ import annotations

from pathlib import Path

from . import relatorio, vetores
from .agents.auditor import Auditor
from .agents.base import Contexto
from .agents.construtores import Analista, Arquiteto, Engenheiro
from .agents.explorador import Explorador
from .agents.orquestrador import Orquestrador
from .banco import Repo
from .caixa import Caixa, gravar_nota
from .conectores import Fonte, Sandbox
from .config import CAIXA_GLOBAL, Config
from .llm import LLM
from .politica import Politica, politica_padrao


class Plataforma:
    def __init__(self, cfg: Config, repo: Repo, espelho=None):  # noqa: ANN001  (EspelhoStorage, LST-30)
        self.cfg = cfg
        self.repo = repo
        self.espelho = espelho
        self.pasta = cfg.pasta_tenant(repo.tenant)
        if espelho:  # disco efêmero (Render): traz a pasta da empresa antes de qualquer leitura
            espelho.restaurar(self.pasta, repo.tenant)
        self.pasta.mkdir(parents=True, exist_ok=True)
        arq_politica = self.pasta / "politica.yaml"
        if not arq_politica.exists():
            politica_padrao().salvar(arq_politica)
        self.politica = Politica.de_arquivo(arq_politica)
        self.llm = LLM(cfg)

    def sincronizar(self) -> int:
        """Envia ao espelho o que mudou na pasta da empresa (no-op sem espelho)."""
        return self.espelho.sincronizar(self.pasta, self.repo.tenant) if self.espelho else 0

    def caixa(self, demanda_id: int | None = None) -> Caixa:
        pastas = {"global": CAIXA_GLOBAL, "tenant": self.pasta / "caixa"}
        if demanda_id is not None:
            pastas["demanda"] = self.pasta_demanda(demanda_id) / "caixa"
        return Caixa(pastas, embedder=vetores.obter(self.cfg.home, self.cfg.embedder))

    def pasta_demanda(self, demanda_id: int) -> Path:
        return self.pasta / "demandas" / str(demanda_id)

    def _contexto(self, demanda: dict) -> Contexto:
        pasta = self.pasta_demanda(demanda["id"])
        sb = Sandbox(pasta / "staging", gravavel=pasta)
        for f in self.repo.fontes(demanda["fontes"]):
            sb.anexar(Fonte(f["nome"], f["tipo"], f["caminho"]))
        sb.travar()
        ctx = Contexto(
            demanda_id=demanda["id"],
            pergunta=demanda["pergunta"],
            caixa=self.caixa(demanda["id"]),
            politica=self.politica,
            sandbox=sb,
            llm=self.llm,
            pasta_demanda=pasta,
            pasta_tenant_caixa=self.pasta / "caixa",
            respostas=dict(demanda.get("respostas") or {}),
        )
        ctx.memoria.update(demanda.get("resultado") or {})
        return ctx

    def _fechar(self, ctx: Contexto) -> None:
        for e in ctx.rastro:
            self.repo.registrar(e["ator"], e["acao"], e["detalhe"], ctx.demanda_id)
        ctx.rastro.clear()
        ctx.sandbox.fechar()

    def abrir(self, autor: str, pergunta: str, fontes: list[int]) -> dict:
        did = self.repo.criar_demanda(autor, pergunta, fontes)
        self.repo.registrar(autor, "abriu_demanda", {"pergunta": pergunta, "fontes": fontes}, did)
        ctx = self._contexto(self.repo.demanda(did))  # type: ignore[arg-type]
        try:
            Explorador().executar(ctx)
            perguntas = Orquestrador().grill(ctx)
        finally:
            self._fechar(ctx)
        status = "grill" if perguntas else "pronta"
        self.repo.atualizar_demanda(did, status=status, grill=perguntas, respostas=ctx.respostas, resultado={"perfis": ctx.memoria["perfis"]})
        return self.repo.demanda(did)  # type: ignore[return-value]

    def responder_grill(self, demanda_id: int, autor: str, respostas: dict[str, str]) -> dict:
        d = self._exigir(demanda_id, {"grill"})
        ctx = self._contexto(d)
        try:
            Orquestrador().gravar_respostas(ctx, d["grill"], respostas)
        finally:
            self._fechar(ctx)
        self.repo.registrar(autor, "respondeu_grill", respostas, demanda_id)
        self.repo.atualizar_demanda(demanda_id, status="pronta", respostas=ctx.respostas)
        return self.repo.demanda(demanda_id)  # type: ignore[return-value]

    def executar(self, demanda_id: int, autor: str) -> dict:
        d = self._exigir(demanda_id, {"pronta"})
        ctx = self._contexto(d)
        try:
            for agente in (Arquiteto(), Engenheiro(), Analista(), Auditor()):
                agente.executar(ctx)
        finally:
            self._fechar(ctx)
        resultado = {k: ctx.memoria[k] for k in ("perfis", "modelo", "pipeline", "resposta", "auditoria")}
        self.repo.registrar(autor, "executou", {"aprovado_camada1": resultado["auditoria"]["aprovado_camada1"]}, demanda_id)
        self.repo.atualizar_demanda(demanda_id, status="em_revisao", resultado=resultado)
        return self._salvar_relatorio(demanda_id)

    def revisar(self, demanda_id: int, revisor: str, aprovado: bool, parecer: str) -> dict:
        d = self._exigir(demanda_id, {"em_revisao"})
        resultado = d["resultado"]
        resultado["revisao"] = {"revisor": revisor, "aprovado": aprovado, "parecer": parecer}
        status = "aprovada" if aprovado else "reprovada"
        self.repo.atualizar_demanda(demanda_id, status=status, resultado=resultado)
        self.repo.registrar(revisor, "revisou", {"aprovado": aprovado, "parecer": parecer}, demanda_id)
        if not aprovado and parecer.strip():
            gravar_nota(
                self.pasta / "caixa" / "aprendizados",
                f"reprovacao-demanda-{demanda_id}",
                f"Revisor reprovou a demanda {demanda_id}: {parecer[:80]}",
                "erro-conhecido",
                f"# Pergunta\n\n{d['pergunta']}\n\n# O que o revisor apontou\n\n{parecer}\n\n# Modelo usado\n\n{resultado.get('modelo')}",
                tags=["reprovacao"],
            )
        return self._salvar_relatorio(demanda_id)

    def _salvar_relatorio(self, demanda_id: int) -> dict:
        d = self.repo.demanda(demanda_id)
        (self.pasta_demanda(demanda_id) / "relatorio.html").write_text(relatorio.gerar(d, d["resultado"]), encoding="utf-8")  # type: ignore[index]
        return d  # type: ignore[return-value]

    def _exigir(self, demanda_id: int, status: set[str]) -> dict:
        d = self.repo.demanda(demanda_id)
        if d is None:
            raise LookupError("demanda não encontrada neste tenant")
        if d["status"] not in status:
            raise ValueError(f"demanda está em '{d['status']}', esperado {sorted(status)}")
        return d
