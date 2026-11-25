"""Demonstração do site (card LST-39, plano `docs/planos/painel-gratis-no-site.md`, ADR 0010).

O visitante sobe uma planilha (ou usa a de exemplo), vê o que o Lastro entendeu, responde as perguntas e
recebe o painel. Logo depois tudo é apagado e ele recebe o **recibo** do apagamento.

- Cada sessão vive numa pasta `demo-<id aleatório>` no disco local, nunca no bucket, no banco ou no Storage,
  e roda a `Plataforma` em modo visitante (LST-38).
- Uma sessão dura no máximo 15 minutos. A varredura apaga as abandonadas, e a pasta inteira é limpa ao subir
  o servidor (o Render já apaga o disco ao reiniciar).
- O log só tem etapa, tempo, tamanho e número de colunas: nunca valores nem nomes de coluna.
"""

from __future__ import annotations

import logging
import os
import secrets
import shutil
import tempfile
import threading
import time
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

from . import paineis
from .config import RAIZ, Config
from .servico import Plataforma

log = logging.getLogger("lastro.demo")
TTL_S = 15 * 60
MAX_BYTES = 5 * 1024 * 1024  # limite básico; o LST-42 completa os limites (linhas, tempo, fila, IP)
EXTENSOES = {".csv", ".xlsx"}
EXEMPLO = RAIZ / "exemplos" / "orcamentos.csv"
FUSO = ZoneInfo("America/Sao_Paulo")
PERGUNTA_PADRAO = "Visão geral dos dados enviados"


class ErroDemo(ValueError):
    """Problema que o visitante pode entender (arquivo grande, formato, sessão expirada)."""


@dataclass
class Sessao:
    id: str
    pasta: Path
    criada_em: float
    plataforma: Plataforma
    demanda_id: int | None = None
    perguntas: list[dict] = field(default_factory=list)


def base_padrao() -> Path:
    return Path(os.environ.get("LASTRO_DEMO_DIR") or Path(tempfile.gettempdir()) / "lastro-demo")


def _tamanho(pasta: Path) -> tuple[int, int, int]:
    arquivos = [p for p in pasta.rglob("*") if p.is_file()] if pasta.exists() else []
    tabelas = sum(1 for p in arquivos if p.suffix == ".parquet")
    return len(arquivos), sum(p.stat().st_size for p in arquivos), tabelas


class Demos:
    def __init__(self, cfg: Config, base: Path | None = None, ttl_s: int = TTL_S):
        self.cfg, self.base, self.ttl_s = cfg, (base or base_padrao()), ttl_s
        self._sessoes: dict[str, Sessao] = {}
        self._trava = threading.Lock()
        self.base.mkdir(parents=True, exist_ok=True)
        for sobra in self.base.glob("demo-*"):  # restos de antes de reiniciar: ninguém mais tem o id
            shutil.rmtree(sobra, ignore_errors=True)

    # ---- ciclo da sessão --------------------------------------------------------------
    def abrir(self, nome_arquivo: str | None, conteudo: bytes | None, agora: float | None = None) -> tuple[Sessao, dict]:
        """Recebe o arquivo (ou o exemplo), perfila e devolve as perguntas. Falha apaga o que já foi gravado."""
        inicio = time.perf_counter()
        agora = time.time() if agora is None else agora
        self.varrer(agora)
        if conteudo is None:
            nome_arquivo, conteudo = "exemplo.csv", EXEMPLO.read_bytes()
        ext = Path(nome_arquivo or "").suffix.lower()
        if ext not in EXTENSOES:
            raise ErroDemo("envie uma planilha CSV ou Excel (.xlsx)")
        if len(conteudo) > MAX_BYTES:
            raise ErroDemo("a planilha passa de 5 MB: para arquivos maiores, fale com a gente")
        sid = secrets.token_urlsafe(16)
        pasta = self.base / f"demo-{sid}"
        try:
            plat = Plataforma.visitante(self.cfg, pasta)
            destino = plat.pasta / "fontes" / f"planilha{ext}"
            destino.parent.mkdir(parents=True, exist_ok=True)
            destino.write_bytes(conteudo)
            fid = plat.repo.adicionar_fonte("planilha", "arquivo", str(destino))
            d = plat.abrir("visitante", PERGUNTA_PADRAO, [fid])
        except Exception as e:
            shutil.rmtree(pasta, ignore_errors=True)
            self._log("abrir_falhou", inicio, len(conteudo), None, erro=type(e).__name__)
            raise ErroDemo("não consegui ler a planilha: confira se a primeira linha tem os nomes das colunas") from e
        s = Sessao(sid, pasta, agora, plat, d["id"], [q for q in d["grill"] if q["id"] != "geral:revisor"])
        with self._trava:
            self._sessoes[sid] = s
        perfil = next(iter(d["resultado"]["perfis"].values()))
        self._log("perfil", inicio, len(conteudo), len(perfil["colunas"]))
        return s, {
            "sessao": sid, "expira_em": datetime.fromtimestamp(agora + self.ttl_s, FUSO).isoformat(timespec="seconds"),
            "perfil": {"linhas": perfil["linhas"], "colunas": [{"nome": c["nome"], "papel": c["papel"]} for c in perfil["colunas"]]},
            "perguntas": [{k: q[k] for k in ("id", "pergunta", "sugestao", "opcoes")} for q in s.perguntas],
        }

    def responder(self, sid: str, respostas: dict[str, str], agora: float | None = None) -> dict:
        """Roda a análise, monta o painel e apaga tudo. Devolve o painel e o recibo, com sucesso ou não."""
        inicio = time.perf_counter()
        s = self._pegar(sid, agora)
        plat = s.plataforma
        try:
            validas = {q["id"] for q in s.perguntas}
            r = {k: str(v) for k, v in respostas.items() if k in validas} | {"geral:revisor": "demonstração (ADR 0010)"}
            d = plat.executar(plat.responder_grill(s.demanda_id, "visitante", r)["id"], "visitante")  # type: ignore[arg-type]
            gold = plat.pasta_demanda(d["id"]) / "gold"
            spec = paineis.inicial(d, gold)
            html = paineis.html_painel(spec, gold, datetime.now(FUSO).strftime("%d/%m/%Y %H:%M"))
            aud = d["resultado"]["auditoria"]
            resultado = {"html": html, "visuais": [v["titulo"] for v in spec["visuais"]],
                         "auditoria": {"aprovada": bool(aud["aprovado_camada1"]), "checagens": len(aud.get("checagens", []))},
                         "modo": "demonstracao"}
            self._log("painel", inicio, None, len(spec["visuais"]))
        except Exception as e:  # noqa: BLE001  (o visitante recebe o recibo mesmo quando a análise falha)
            resultado = {"erro": "não consegui montar o painel com esses dados: tente outra coluna de valor ou outro recorte"}
            self._log("painel_falhou", inicio, None, None, erro=type(e).__name__)
        resultado["recibo"] = self.apagar(sid)
        return resultado

    def apagar(self, sid: str) -> dict:
        with self._trava:
            s = self._sessoes.pop(sid, None)
        if not s:
            raise ErroDemo("sessão não encontrada: ela já foi apagada ou expirou")
        return self._apagar(s)

    def varrer(self, agora: float | None = None) -> int:
        agora = time.time() if agora is None else agora
        with self._trava:
            vencidas = [sid for sid, s in self._sessoes.items() if agora - s.criada_em > self.ttl_s]
            sessoes = [self._sessoes.pop(sid) for sid in vencidas]
        for s in sessoes:
            self._apagar(s)
        if sessoes:
            log.info("demo: varredura apagou %d sessões vencidas", len(sessoes))
        return len(sessoes)

    @property
    def abertas(self) -> int:
        return len(self._sessoes)

    # ---- internos ---------------------------------------------------------------------
    def _pegar(self, sid: str, agora: float | None) -> Sessao:
        self.varrer(agora)
        s = self._sessoes.get(sid)
        if not s:
            raise ErroDemo("sessão não encontrada: ela já foi apagada ou expirou")
        return s

    def _apagar(self, s: Sessao) -> dict:
        arquivos, total_bytes, tabelas = _tamanho(s.pasta)
        registros = s.plataforma.repo.apagar()  # type: ignore[attr-defined]
        shutil.rmtree(s.pasta, ignore_errors=True)
        conferido = not s.pasta.exists()
        recibo = {"apagado_em": datetime.now(FUSO).isoformat(timespec="seconds"), "arquivos": arquivos, "bytes": total_bytes,
                  "tabelas": tabelas, "registros_em_memoria": registros, "conferido": conferido}
        self._log("apagou", None, total_bytes, None, arquivos=arquivos, conferido=conferido)
        return recibo

    @staticmethod
    def _log(etapa: str, inicio: float | None, tamanho: int | None, colunas: int | None, **extra: Any) -> None:
        partes = [f"etapa={etapa}"]
        if inicio is not None:
            partes.append(f"ms={int((time.perf_counter() - inicio) * 1000)}")
        if tamanho is not None:
            partes.append(f"bytes={tamanho}")
        if colunas is not None:
            partes.append(f"n={colunas}")
        partes += [f"{k}={v}" for k, v in extra.items()]
        log.info("demo: %s", " ".join(partes))
