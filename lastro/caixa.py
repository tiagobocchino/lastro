"""Caixa de Ferramenta: acervo de notas Markdown buscado por índice, nunca carregado inteiro.

Três camadas de leitura (progressive disclosure):
1. `indice()`  -> uma linha por nota (nome + descrição do frontmatter).
2. `buscar()`  -> trechos ranqueados (BM25 do SQLite FTS5, fundidos por RRF entre escopos e,
                  quando houver um `Embedder`, com a busca vetorial).
3. `ler()`     -> só a seção pedida de uma nota.

Escopos, em ordem de prioridade: demanda > tenant > global.
"""

from __future__ import annotations

import re
import sqlite3
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable, Protocol

import yaml

ESCOPOS = ("demanda", "tenant", "global")
PESO_ESCOPO = {"demanda": 1.0, "tenant": 0.9, "global": 0.8}
RRF_K = 60


@dataclass
class Nota:
    caminho: Path
    escopo: str
    nome: str
    descricao: str
    tipo: str
    tags: list[str]
    secoes: list[tuple[str, str]]  # (titulo, corpo)


@dataclass
class Trecho:
    caminho: str
    escopo: str
    nome: str
    secao: str
    resumo: str
    pontuacao: float = 0.0
    fontes: list[str] = field(default_factory=list)


class Embedder(Protocol):
    def vetor(self, texto: str) -> list[float]: ...


def ler_nota(caminho: Path, escopo: str) -> Nota:
    texto = caminho.read_text(encoding="utf-8")
    meta: dict = {}
    corpo = texto
    if texto.startswith("---"):
        partes = texto.split("---", 2)
        if len(partes) == 3:
            try:
                meta = yaml.safe_load(partes[1]) or {}
            except yaml.YAMLError:
                meta = dict(re.findall(r"^(\w+):\s*(.*)$", partes[1], flags=re.M))
            corpo = partes[2]
    secoes: list[tuple[str, str]] = []
    titulo = "(início)"
    linhas: list[str] = []
    for linha in corpo.splitlines():
        m = re.match(r"^#{1,3}\s+(.*)", linha)
        if m:
            if "".join(linhas).strip():
                secoes.append((titulo, "\n".join(linhas).strip()))
            titulo, linhas = m.group(1).strip(), []
        else:
            linhas.append(linha)
    if "".join(linhas).strip():
        secoes.append((titulo, "\n".join(linhas).strip()))
    return Nota(
        caminho=caminho,
        escopo=escopo,
        nome=str(meta.get("name") or caminho.stem),
        descricao=str(meta.get("description") or ""),
        tipo=str(meta.get("type") or "nota"),
        tags=list(meta.get("tags") or []),
        secoes=secoes,
    )


def _consulta_fts(texto: str) -> str:
    """Converte texto livre numa consulta FTS5 segura (sem operadores do usuário)."""
    palavras = re.findall(r"[\wÀ-ÿ]{2,}", texto.lower())
    vazias = {"de", "da", "do", "das", "dos", "em", "no", "na", "os", "as", "um", "uma", "por", "para", "com", "que", "e", "o", "a"}
    termos = [p for p in palavras if p not in vazias]
    return " OR ".join(f'"{t}"*' for t in termos)


def rrf(listas: Iterable[list[str]], k: int = RRF_K) -> dict[str, float]:
    """Reciprocal Rank Fusion: soma 1/(k + posição) de cada lista ranqueada."""
    pontos: dict[str, float] = {}
    for lista in listas:
        for pos, chave in enumerate(lista, start=1):
            pontos[chave] = pontos.get(chave, 0.0) + 1.0 / (k + pos)
    return pontos


class Caixa:
    """Índice de uma ou mais pastas de notas, cada uma com seu escopo."""

    def __init__(self, pastas: dict[str, Path], embedder: Embedder | None = None):
        desconhecidos = set(pastas) - set(ESCOPOS)
        if desconhecidos:
            raise ValueError(f"escopo desconhecido: {desconhecidos}")
        self.pastas = {e: p for e, p in pastas.items() if p is not None}
        self.embedder = embedder
        self.db = sqlite3.connect(":memory:", check_same_thread=False)
        self.db.execute(
            "CREATE VIRTUAL TABLE trechos USING fts5(chave UNINDEXED, escopo UNINDEXED, caminho UNINDEXED,"
            " nome, secao, corpo, tokenize='unicode61 remove_diacritics 2')"
        )
        self.notas: dict[str, Nota] = {}
        self.vetores: dict[str, list[float]] = {}
        self.reindexar()

    def reindexar(self) -> int:
        self.db.execute("DELETE FROM trechos")
        self.notas.clear()
        self.vetores.clear()
        for escopo, pasta in self.pastas.items():
            if not pasta.exists():
                continue
            for arq in sorted(pasta.rglob("*.md")):
                if arq.name.upper() == "INDEX.MD":
                    continue
                nota = ler_nota(arq, escopo)
                rel = f"{escopo}:{arq.relative_to(pasta).as_posix()}"
                self.notas[rel] = nota
                for i, (secao, corpo) in enumerate(nota.secoes):
                    chave = f"{rel}#{i}"
                    self.db.execute(
                        "INSERT INTO trechos VALUES (?,?,?,?,?,?)",
                        (chave, escopo, rel, f"{nota.nome} {nota.descricao} {' '.join(nota.tags)}", secao, corpo),
                    )
                    if self.embedder:
                        self.vetores[chave] = self.embedder.vetor(f"{nota.nome}\n{secao}\n{corpo}")
        self.db.commit()
        return len(self.notas)

    def indice(self) -> str:
        """Camada 1: uma linha por nota. É o único pedaço da caixa que vai sempre no prompt."""
        linhas = [f"- [{n.escopo}] {rel.split(':', 1)[1]} ({n.tipo}): {n.descricao}" for rel, n in sorted(self.notas.items())]
        return "\n".join(linhas)

    def buscar(self, pergunta: str, k: int = 5) -> list[Trecho]:
        """Camada 2: trechos ranqueados. BM25 por escopo, fusão por RRF, peso por escopo."""
        consulta = _consulta_fts(pergunta)
        if not consulta:
            return []
        listas: list[list[str]] = []
        resumos: dict[str, Trecho] = {}
        for escopo in ESCOPOS:
            linhas = self.db.execute(
                "SELECT chave, caminho, nome, secao, snippet(trechos, 5, '[', ']', ' … ', 24), bm25(trechos, 0, 0, 0, 3.0, 2.0, 1.0)"
                " FROM trechos WHERE trechos MATCH ? AND escopo = ? ORDER BY 6 LIMIT 20",
                (consulta, escopo),
            ).fetchall()
            listas.append([l[0] for l in linhas])
            for chave, caminho, nome, secao, resumo, _ in linhas:
                nota = self.notas[caminho]
                resumos[chave] = Trecho(caminho, escopo, nota.nome, secao, resumo, fontes=["bm25"])
        if self.embedder and self.vetores:
            alvo = self.embedder.vetor(pergunta)
            sim = sorted(self.vetores, key=lambda c: -_cosseno(alvo, self.vetores[c]))[:20]
            listas.append(sim)
            for chave in sim:
                if chave not in resumos:
                    caminho, i = chave.rsplit("#", 1)
                    nota = self.notas[caminho]
                    secao, corpo = nota.secoes[int(i)]
                    resumos[chave] = Trecho(caminho, nota.escopo, nota.nome, secao, corpo[:160], fontes=[])
                resumos[chave].fontes.append("vetor")
        pontos = rrf(listas)
        for chave, t in resumos.items():
            t.pontuacao = pontos.get(chave, 0.0) * PESO_ESCOPO[t.escopo]
        return sorted(resumos.values(), key=lambda t: -t.pontuacao)[:k]

    def ler(self, caminho: str, secao: str | None = None) -> str:
        """Camada 3: só a seção pedida (ou a nota inteira, se ela for curta)."""
        nota = self.notas.get(caminho)
        if nota is None:
            raise KeyError(f"nota não encontrada: {caminho}")
        if secao is None:
            return "\n\n".join(f"## {t}\n{c}" for t, c in nota.secoes)
        for titulo, corpo in nota.secoes:
            if titulo.lower() == secao.lower():
                return f"## {titulo}\n{corpo}"
        raise KeyError(f"seção '{secao}' não existe em {caminho}")


def _cosseno(a: list[float], b: list[float]) -> float:
    num = sum(x * y for x, y in zip(a, b))
    den = (sum(x * x for x in a) ** 0.5) * (sum(y * y for y in b) ** 0.5)
    return num / den if den else 0.0


def gravar_nota(pasta: Path, nome: str, descricao: str, tipo: str, corpo: str, tags: list[str] | None = None) -> Path:
    """Escreve uma nota com frontmatter. É assim que o grill e os agentes alimentam a caixa."""
    pasta.mkdir(parents=True, exist_ok=True)
    import unicodedata  # noqa: PLC0415

    plano = "".join(c for c in unicodedata.normalize("NFD", nome.lower()) if unicodedata.category(c) != "Mn")
    slug = re.sub(r"[^a-z0-9]+", "-", plano).strip("-")
    meta = {"name": slug, "description": descricao, "type": tipo, "tags": tags or []}
    arq = pasta / f"{slug}.md"
    arq.write_text("---\n" + yaml.safe_dump(meta, allow_unicode=True, sort_keys=False) + "---\n\n" + corpo.strip() + "\n", encoding="utf-8")
    return arq
