"""'Pergunte' dentro da demanda do portal (LST-57): um pedido em português vira gráfico sobre os dados da demanda.

O mesmo núcleo do Streamlit (`lastro.rapido.nucleo`): a LLM recebe só a pergunta e os nomes das colunas, devolve um
plano, o Lastro valida o plano contra o catálogo da demanda e monta o SQL de leitura. Nenhuma linha de dado vai ao
provedor. O escopo é a demanda: as colunas são as do modelo que o agente montou para aquela pergunta.

Chaves (grill do Tiago, 26/11):
- padrão: a chave do Lastro (`GOOGLE_API_KEY` no servidor), Gemini gratuito, com aviso de limites;
- o cliente pode usar a chave do próprio modelo (ticket 3); aí o padrão de construção não é garantido;
- sem chave ou com o provedor fora do ar: palavras-chave, com aviso.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import duckdb

from .rapido import nucleo

AVISO_LASTRO = ("Interpretado pelo Gemini gratuito, com a chave do Lastro: sujeito aos limites do plano gratuito (pedidos por "
                "minuto e por dia). Se o limite estourar, o pedido é interpretado por palavras-chave.")
AVISO_CLIENTE = ("Interpretado pelo modelo de IA da sua empresa. O padrão de construção dos gráficos só é garantido com os modelos "
                 "do Lastro ou nos pacotes com implementação no seu modelo; fora disso, o resultado pode variar.")
AVISO_SEM_LLM = "Interpretado por palavras-chave (sem modelo de IA configurado)."


def tabela(did: int) -> str:
    return f"painel_{did}_demanda"


def carregar(did: int, gold: Path, cat_demanda: dict) -> tuple[duckdb.DuckDBPyConnection, dict[str, dict[str, Any]]]:
    """A tabela pronta da demanda (fato + dimensões + mês) num DuckDB em memória, e o catálogo que a LLM vê."""
    con = duckdb.connect()
    for arq in gold.glob("*.parquet"):
        con.execute(f"CREATE VIEW \"{arq.stem}\" AS SELECT * FROM read_parquet('{str(arq).replace(chr(39), chr(39) * 2)}')")
    dims = list(cat_demanda["dimensoes"])
    sel = [f'"dim_{d}"."{d}" AS "{d}"' for d in dims]
    joins = [f'LEFT JOIN "dim_{d}" USING ("{d}_id")' for d in dims]
    if "ano_mes" in cat_demanda["tempo"]:
        sel.append("dim_data.ano_mes AS ano_mes")
        joins.append("LEFT JOIN dim_data USING (data)")
    sel += [f'fato."{m}" AS "{m}"' for m in cat_demanda["medidas"]] + ["1 AS registros"]
    con.execute(f'CREATE TABLE "{tabela(did)}" AS SELECT {", ".join(sel)} FROM fato {" ".join(joins)}')
    cat = {tabela(did): {"assunto": "Esta demanda", "medidas": list(cat_demanda["medidas"]),
                         "dimensoes": dims + (["ano_mes"] if "ano_mes" in cat_demanda["tempo"] else []), "tem_registros": True}}
    return con, cat


def responder(did: int, gold: Path, cat_demanda: dict, pergunta: str, chave_cliente: str | None = None,
              modelo_cliente: str | None = None) -> dict[str, Any]:
    pergunta = (pergunta or "").strip()[:300]
    if not pergunta:
        raise nucleo.PlanoInvalido("escreva o que você quer ver, por exemplo: 'valor vendido por estado por mês'")
    con, cat = carregar(did, gold, cat_demanda)
    try:
        origem, aviso, llm = "palavras-chave", AVISO_SEM_LLM, None
        chave = chave_cliente or os.environ.get("GOOGLE_API_KEY", "")
        if chave:
            try:
                llm = nucleo.modelo_gemini(chave, modelo_cliente or os.environ.get("GEMINI_MODELO") or nucleo.MODELO_GEMINI)
                origem, aviso = ("cliente", AVISO_CLIENTE) if chave_cliente else ("lastro", AVISO_LASTRO)
            except Exception:  # noqa: BLE001  (biblioteca ausente ou chave inválida: segue por palavras-chave)
                llm = None
        plano = nucleo.interpretar(pergunta, cat, llm)
        if any("palavras-chave" in a for a in plano.avisos):
            origem = "palavras-chave"
        colunas, linhas = nucleo.executar(con, plano)
        q, _ = nucleo.sql(plano)
        return {"titulo": plano.titulo, "grafico": plano.grafico, "por_mes": plano.por_mes, "dimensao": plano.dimensao,
                "agregacao": plano.agregacao, "colunas": colunas, "linhas": [list(r) for r in linhas], "avisos": plano.avisos,
                "sql": q, "origem": origem, "aviso_modelo": aviso}
    finally:
        con.close()
