"""Cliente de LLM opcional, compatível com a API de chat da OpenAI.

Serve para Ollama local (gratuito), free tier de Groq ou Gemini (endpoint compatível)
ou uma chave paga cedida pelo cliente. Com `LASTRO_LLM=nenhum`, os agentes usam só
heurísticas determinísticas: a plataforma funciona sem custo e sem rede.
"""

from __future__ import annotations

import httpx

from .config import Config

URLS = {
    "ollama": "http://localhost:11434/v1",
    "groq": "https://api.groq.com/openai/v1",
    "gemini": "https://generativelanguage.googleapis.com/v1beta/openai",
}


class LLM:
    def __init__(self, cfg: Config):
        self.provedor = cfg.llm_provedor
        self.modelo = cfg.llm_modelo
        self.url = cfg.llm_url or URLS.get(self.provedor, "")
        self.chave = cfg.llm_chave

    @property
    def ativo(self) -> bool:
        return self.provedor != "nenhum" and bool(self.url and self.modelo)

    def responder(self, sistema: str, pedido: str, temperatura: float = 0.1) -> str | None:
        if not self.ativo:
            return None
        cab = {"Authorization": f"Bearer {self.chave}"} if self.chave else {}
        corpo = {
            "model": self.modelo,
            "temperature": temperatura,
            "messages": [{"role": "system", "content": sistema}, {"role": "user", "content": pedido}],
        }
        try:
            r = httpx.post(f"{self.url}/chat/completions", json=corpo, headers=cab, timeout=60)
            r.raise_for_status()
            return r.json()["choices"][0]["message"]["content"]
        except (httpx.HTTPError, KeyError, IndexError):
            return None
