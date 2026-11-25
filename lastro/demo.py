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
from .agents.construtores import dimensoes_candidatas
from .config import RAIZ, Config
from .pessoal import aviso as aviso_pessoal
from .servico import Plataforma

log = logging.getLogger("lastro.demo")
TTL_S = 15 * 60
MAX_BYTES = 5 * 1024 * 1024  # limite básico; o LST-42 completa os limites (linhas, tempo, fila, IP)
EXTENSOES = {".csv", ".xlsx"}
EXEMPLO = RAIZ / "exemplos" / "orcamentos.csv"
FUSO = ZoneInfo("America/Sao_Paulo")
PERGUNTA_PADRAO = "Visão geral dos dados enviados"
FORMATOS = {"ranking (barras)": "ranking", "tabela": "tabela", "evolução no tempo": "evolucao", "só o número": "numero"}
PERIODOS = {"por mês": "ano_mes", "por ano": "ano"}


def pessoais(perfil: dict) -> dict[str, str]:
    return {c["nome"]: c["pessoal"] for c in perfil["colunas"] if c.get("pessoal")}


def perguntas_visitante(perfil: dict, grill: list[dict]) -> list[dict]:
    """Até 4 perguntas curtas, cada uma com sugestão (LST-40). O resto do grill (chave, data, recorte)
    fica com a sugestão do Orquestrador, sem ocupar o visitante."""
    sug = {q["id"]: q.get("sugestao") for q in grill}
    cols = [c for c in perfil["colunas"] if not c.get("pessoal")]  # LST-41: dado pessoal fica fora do painel
    numeros = [c["nome"] for c in cols if c["papel"] == "numero" and not c["nome"].lower().endswith("id")]
    dims = [d for d in dimensoes_candidatas(perfil, (perfil["chaves_candidatas"] or [None])[0]) if d not in pessoais(perfil)]
    datas = [c["nome"] for c in cols if c["papel"] == "data"]
    out = []
    if numeros:
        out.append({"id": "planilha:medida", "pergunta": "Qual valor você quer acompanhar?",
                    "sugestao": sug.get("planilha:medida") if sug.get("planilha:medida") in numeros else numeros[0], "opcoes": numeros})
    if dims:
        out.append({"id": "demo:quebra", "pergunta": "Quebrado por qual categoria?", "sugestao": dims[0], "opcoes": dims})
    if datas:
        out.append({"id": "demo:periodo", "pergunta": "No tempo, agrupar por mês ou por ano?", "sugestao": "por mês", "opcoes": list(PERIODOS)})
    formatos = [f for f, k in FORMATOS.items() if (k in {"ranking", "tabela"} and dims) or (k == "evolucao" and datas) or k == "numero"]
    out.append({"id": "demo:formato", "pergunta": "Como você quer ver?", "sugestao": formatos[0], "opcoes": formatos})
    return out


class ErroDemo(ValueError):
    """Problema que o visitante pode entender (arquivo grande, formato, sessão expirada)."""


class Ocupado(ErroDemo):
    """Fila cheia: alguém está analisando agora (Render gratuito, 1 análise por vez)."""


class Demorou(ErroDemo):
    """A análise passou do prazo."""


class LimiteIP(ErroDemo):
    """Passou do limite de análises por hora ou por dia deste endereço."""


MAX_LINHAS = 50_000
PRAZO_S = 60
ESPERA_FILA_S = 20
POR_HORA, POR_DIA = 5, 20


class Limites:
    """Contagem de análises por endereço, só em memória. O IP vira hash com sal aleatório do processo:
    o endereço em si nunca é guardado, e reiniciar o servidor zera tudo."""

    def __init__(self, por_hora: int = POR_HORA, por_dia: int = POR_DIA):
        self.por_hora, self.por_dia = por_hora, por_dia
        self._sal = secrets.token_bytes(16)
        self._vezes: dict[str, list[float]] = {}
        self._trava = threading.Lock()

    def _chave(self, ip: str) -> str:
        import hashlib

        return hashlib.sha256(self._sal + ip.encode()).hexdigest()[:24]

    def registrar(self, ip: str, agora: float | None = None) -> None:
        agora = time.time() if agora is None else agora
        k = self._chave(ip)
        with self._trava:
            vezes = [t for t in self._vezes.get(k, []) if agora - t < 86_400]
            if sum(1 for t in vezes if agora - t < 3_600) >= self.por_hora:
                raise LimiteIP(f"você já fez {self.por_hora} análises na última hora: tente de novo mais tarde ou fale com a gente")
            if len(vezes) >= self.por_dia:
                raise LimiteIP(f"você já fez {self.por_dia} análises hoje: volte amanhã ou fale com a gente")
            vezes.append(agora)
            self._vezes[k] = vezes
            for chave in [c for c, v in self._vezes.items() if not v or agora - v[-1] >= 86_400]:  # memória não cresce
                del self._vezes[chave]


@dataclass
class Sessao:
    id: str
    pasta: Path
    criada_em: float
    plataforma: Plataforma
    demanda_id: int | None = None
    perguntas: list[dict] = field(default_factory=list)


def faixa(n_bytes: int) -> str:
    return "até 100 KB" if n_bytes <= 100 * 1024 else ("100 KB a 1 MB" if n_bytes <= 1024 * 1024 else "1 a 5 MB")


def _motivo(e: Exception) -> str:
    if isinstance(e, LimiteIP):
        return "limite_ip"
    if isinstance(e, Ocupado):
        return "fila"
    if isinstance(e, Demorou):
        return "prazo"
    t = str(e)
    return "formato" if "CSV ou Excel" in t else "tamanho" if "5 MB" in t else "linhas" if "linhas" in t else "leitura"


def base_padrao() -> Path:
    return Path(os.environ.get("LASTRO_DEMO_DIR") or Path(tempfile.gettempdir()) / "lastro-demo")


def _tamanho(pasta: Path) -> tuple[int, int, int]:
    arquivos = [p for p in pasta.rglob("*") if p.is_file()] if pasta.exists() else []
    tabelas = sum(1 for p in arquivos if p.suffix == ".parquet")
    return len(arquivos), sum(p.stat().st_size for p in arquivos), tabelas


class Demos:
    def __init__(self, cfg: Config, base: Path | None = None, ttl_s: int = TTL_S, prazo_s: float = PRAZO_S,
                 espera_fila_s: float = ESPERA_FILA_S, max_linhas: int = MAX_LINHAS, limites: Limites | None = None,
                 ao_evento: Any = None):
        self.cfg, self.base, self.ttl_s = cfg, (base or base_padrao()), ttl_s
        self.prazo_s, self.espera_fila_s, self.max_linhas = prazo_s, espera_fila_s, max_linhas
        self.limites = limites or Limites()
        self.ao_evento = ao_evento  # funil anônimo (LST-44): banco.registrar_demo
        self._fila = threading.BoundedSemaphore(1)
        self.esperando = 0
        self._sessoes: dict[str, Sessao] = {}
        self._trava = threading.Lock()
        self.base.mkdir(parents=True, exist_ok=True)
        for sobra in self.base.glob("demo-*"):  # restos de antes de reiniciar: ninguém mais tem o id
            shutil.rmtree(sobra, ignore_errors=True)

    # ---- ciclo da sessão --------------------------------------------------------------
    def abrir(self, nome_arquivo: str | None, conteudo: bytes | None, agora: float | None = None, ip: str | None = None) -> tuple[Sessao, dict]:
        """Limite por IP, depois fila e prazo. Se o prazo estoura, a sessão é apagada assim que a análise termina."""
        def cancelar(res: tuple[Sessao, dict]) -> None:
            with self._trava:
                self._sessoes.pop(res[0].id, None)
            self._apagar(res[0])

        try:
            if ip:
                self.limites.registrar(ip, agora)
            return self._na_fila(lambda: self._abrir(nome_arquivo, conteudo, agora), cancelar)
        except ErroDemo as e:
            self.evento("recusou", motivo=_motivo(e))
            raise

    def _abrir(self, nome_arquivo: str | None, conteudo: bytes | None, agora: float | None = None) -> tuple[Sessao, dict]:
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
        perfil = next(iter(d["resultado"]["perfis"].values()))
        if perfil["linhas"] <= self.max_linhas:
            self.evento("subiu", duracao_ms=int((time.perf_counter() - inicio) * 1000), faixa_tamanho=faixa(len(conteudo)),
                        n_colunas=len(perfil["colunas"]))
        if perfil["linhas"] > self.max_linhas:
            plat.repo.apagar()  # type: ignore[attr-defined]
            shutil.rmtree(pasta, ignore_errors=True)
            self._log("recusou_linhas", inicio, len(conteudo), len(perfil["colunas"]))
            raise ErroDemo(f"a planilha tem mais de {self.max_linhas:,} linhas: para volumes maiores, fale com a gente".replace(",", "."))
        s = Sessao(sid, pasta, agora, plat, d["id"], perguntas_visitante(perfil, d["grill"]))
        with self._trava:
            self._sessoes[sid] = s
        self._log("perfil", inicio, len(conteudo), len(perfil["colunas"]))
        return s, {
            "sessao": sid, "expira_em": datetime.fromtimestamp(agora + self.ttl_s, FUSO).isoformat(timespec="seconds"),
            "perfil": {"linhas": perfil["linhas"], "colunas": [{"nome": c["nome"], "papel": "pessoal" if c.get("pessoal") else c["papel"]}
                                                          for c in perfil["colunas"]]},
            "avisos": aviso_pessoal(pessoais(perfil)),
            "perguntas": [{k: q[k] for k in ("id", "pergunta", "sugestao", "opcoes")} for q in s.perguntas],
        }

    def responder(self, sid: str, respostas: dict[str, str], agora: float | None = None) -> dict:
        self._pegar(sid, agora)  # sessão inexistente responde na hora, sem entrar na fila
        try:
            return self._na_fila(lambda: self._responder(sid, respostas, agora), None)
        except (Ocupado, Demorou) as e:
            self.evento("painel_falhou", motivo=_motivo(e))
            raise

    def _responder(self, sid: str, respostas: dict[str, str], agora: float | None = None) -> dict:
        """Roda a análise, monta o painel e apaga tudo. Devolve o painel e o recibo, com sucesso ou não."""
        inicio = time.perf_counter()
        s = self._pegar(sid, agora)
        plat = s.plataforma
        escolhas = {}
        for q in s.perguntas:  # resposta fora das opções volta antes de rodar; a sessão continua aberta
            valor = str(respostas.get(q["id"]) or q["sugestao"])
            if valor not in q["opcoes"]:
                raise ErroDemo(f"resposta inválida para '{q['pergunta']}': escolha uma das opções")
            escolhas[q["id"]] = valor
        try:
            r = {k: v for k, v in escolhas.items() if not k.startswith("demo:")} | {"geral:revisor": "demonstração (ADR 0010)"}
            d = plat.executar(plat.responder_grill(s.demanda_id, "visitante", r)["id"], "visitante")  # type: ignore[arg-type]
            gold = plat.pasta_demanda(d["id"]) / "gold"
            perfil = next(iter(d["resultado"]["perfis"].values()))
            spec = paineis.para_visitante(d, gold, escolhas.get("demo:quebra"), PERIODOS.get(escolhas.get("demo:periodo", "")),
                                          FORMATOS[escolhas["demo:formato"]], excluir=set(pessoais(perfil)))
            html = paineis.html_painel(spec, gold, datetime.now(FUSO).strftime("%d/%m/%Y %H:%M"))
            aud = d["resultado"]["auditoria"]
            resultado = {"html": html, "visuais": [v["titulo"] for v in spec["visuais"]],
                         "auditoria": {"aprovada": bool(aud["aprovado_camada1"]), "checagens": len(aud.get("checagens", []))},
                         "modo": "demonstracao"}
            self._log("painel", inicio, None, len(spec["visuais"]))
            self.evento("painel", duracao_ms=int((time.perf_counter() - inicio) * 1000), visual=FORMATOS[escolhas["demo:formato"]])
        except Exception as e:  # noqa: BLE001  (o visitante recebe o recibo mesmo quando a análise falha)
            resultado = {"erro": "não consegui montar o painel com esses dados: tente outra coluna de valor ou outro recorte"}
            self._log("painel_falhou", inicio, None, None, erro=type(e).__name__)
            self.evento("painel_falhou")
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

    def evento(self, etapa: str, **campos: Any) -> None:
        """Registra no funil sem nunca derrubar a demonstração."""
        if not self.ao_evento:
            return
        try:
            self.ao_evento(etapa, **campos)
        except Exception as e:  # noqa: BLE001
            log.warning("demo: evento do funil não gravado: %s", type(e).__name__)

    # ---- internos ---------------------------------------------------------------------
    def _na_fila(self, tarefa: Any, ao_cancelar: Any) -> Any:
        """Uma análise por vez, com prazo. A vaga só volta quando a análise termina de verdade (mesmo
        depois de estourar o prazo), para o servidor nunca rodar duas ao mesmo tempo."""
        with self._trava:
            self.esperando += 1
        try:
            if not self._fila.acquire(timeout=self.espera_fila_s):
                raise Ocupado("tem gente analisando agora e você é o próximo: tente de novo em alguns segundos")
        finally:
            with self._trava:
                self.esperando -= 1
        res: dict[str, Any] = {}
        fim, cancelado = threading.Event(), threading.Event()

        def rodar() -> None:
            try:
                res["v"] = tarefa()
            except BaseException as e:  # noqa: BLE001
                res["e"] = e
            finally:
                if cancelado.is_set() and "v" in res and ao_cancelar:
                    ao_cancelar(res["v"])
                fim.set()
                self._fila.release()

        threading.Thread(target=rodar, daemon=True, name="demo-analise").start()
        if not fim.wait(self.prazo_s):
            cancelado.set()
            if fim.is_set() and "v" in res and ao_cancelar:  # terminou no limite: apaga já
                ao_cancelar(res["v"])
            self._log("prazo_estourado", None, None, None, prazo_s=self.prazo_s)
            raise Demorou(f"a análise passou de {int(self.prazo_s)} segundos e foi cancelada; seus dados são apagados assim que ela parar")
        if "e" in res:
            raise res["e"]
        return res["v"]

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
