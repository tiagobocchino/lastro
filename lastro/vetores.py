"""Embeddings locais e gratuitos para a Caixa de Ferramenta (fastembed + ONNX, sem GPU, sem API paga).

O modelo é baixado uma vez para `LASTRO_HOME/modelos` e os vetores ficam em cache num SQLite
(chave = modelo + hash do texto), para a reindexação não recalcular o que não mudou.
Ligado por `LASTRO_EMBEDDER=fastembed`; desligado (padrão), a Caixa usa só BM25.
"""

from __future__ import annotations

import hashlib
import os
import sqlite3
import struct
from pathlib import Path

os.environ.setdefault("HF_HUB_DISABLE_XET", "1")  # baixa pelo CDN comum; o protocolo xet pede hosts extras

MODELO_PADRAO = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"


class EmbedderLocal:
    def __init__(self, pasta: Path, modelo: str = MODELO_PADRAO):
        from fastembed import TextEmbedding  # noqa: PLC0415  (dependência opcional: extra "vetores")

        pasta.mkdir(parents=True, exist_ok=True)
        self.modelo_nome = modelo
        self.modelo = TextEmbedding(modelo, cache_dir=str(pasta / "modelos"))
        self.cache = sqlite3.connect(pasta / "vetores.db", check_same_thread=False)
        self.cache.execute("CREATE TABLE IF NOT EXISTS vetor (chave TEXT PRIMARY KEY, dados BLOB)")
        self.calculados = 0

    def _chave(self, texto: str) -> str:
        return hashlib.sha256(f"{self.modelo_nome}\n{texto}".encode()).hexdigest()

    def vetor(self, texto: str) -> list[float]:
        chave = self._chave(texto)
        linha = self.cache.execute("SELECT dados FROM vetor WHERE chave=?", (chave,)).fetchone()
        if linha:
            n = len(linha[0]) // 4
            return list(struct.unpack(f"{n}f", linha[0]))
        v = [float(x) for x in next(iter(self.modelo.embed([texto])))]
        self.cache.execute("INSERT OR REPLACE INTO vetor VALUES (?,?)", (chave, struct.pack(f"{len(v)}f", *v)))
        self.cache.commit()
        self.calculados += 1
        return v


_INSTANCIAS: dict[str, EmbedderLocal] = {}


def obter(pasta: Path, tipo: str) -> EmbedderLocal | None:
    """Embedder configurado, reaproveitado entre chamadas (carregar o modelo custa ~10 s)."""
    if tipo in ("", "nenhum"):
        return None
    if tipo != "fastembed":
        raise ValueError(f"LASTRO_EMBEDDER desconhecido: {tipo}")
    chave = str(pasta)
    if chave not in _INSTANCIAS:
        _INSTANCIAS[chave] = EmbedderLocal(pasta)
    return _INSTANCIAS[chave]
