"""Relatórios Python rápidos (LST-54): KPIs gerais sobre as tabelas prontas do BI, com um agente LangChain que
transforma um pedido em português num plano de gráfico.

Garantias:
- A LLM (gratuita, Gemini do AI Studio) recebe **só a pergunta e o catálogo** (nomes de tabela e de coluna). Nenhuma linha
  de dado sai do Lastro: o plano volta como JSON, é validado aqui e o SQL é montado e rodado aqui (DuckDB em memória).
- Profundidade de demonstração (pedido do Tiago, 26/11): no máximo empresa, setor, estado/região e data. Cliente, vendedor,
  produto e outros detalhes ficam para os relatórios de entrega (Power BI e Looker).
- Só leitura: o SQL passa pela trava `somente_leitura`; nomes de coluna vêm de lista fechada e valores vão como parâmetro.
"""

from __future__ import annotations

import io
import json
import re
import unicodedata
from dataclasses import dataclass, field
from typing import Any, Literal

import duckdb

from ..somente_leitura import verificar

# Dimensões de demonstração: empresa, setor, status do funil, região/UF e tempo. O resto fica nos relatórios de entrega.
DIMENSAO_PERMITIDA = re.compile(r"^(company|setor_nome|status_nome|\w+_regiao|\w+_estado|ano|ano_mes)$")
NOMES = {"company": "empresa", "setor_nome": "setor", "status_nome": "status", "projeto_regiao": "região da obra",
         "projeto_estado": "UF da obra", "cliente_regiao": "região do cliente", "cliente_estado": "UF do cliente",
         "ano": "ano", "ano_mes": "mês", "valores_produtos": "valor de produtos", "valores_total": "valor total",
         "valores_desconto": "desconto", "valor_contrato": "valor do contrato", "quantidade": "quantidade", "registros": "registros"}
ASSUNTOS = {"vendedor": "Vendas", "funil": "Funil de orçamentos", "produto": "Produtos", "funcionario": "RH"}
AGREGACOES = {"soma": "sum", "media": "avg", "contagem": "sum"}  # contagem = soma da coluna registros (1 por linha)
GRAFICOS = ("numero", "barras", "linha", "pizza")


def _sem_acento(t: str) -> str:
    return unicodedata.normalize("NFKD", t).encode("ascii", "ignore").decode().lower()


def nome(col: str) -> str:
    return NOMES.get(col, col.replace("_", " "))


def assunto(tabela: str) -> str:
    t = _sem_acento(tabela)
    return next((v for k, v in ASSUNTOS.items() if k in t), tabela)


# ---- dados -----------------------------------------------------------------------------------------------------

def carregar(parquets: dict[str, bytes]) -> duckdb.DuckDBPyConnection:
    """Tabelas prontas (nome → bytes Parquet) num DuckDB em memória. Nada é gravado em disco."""
    con = duckdb.connect()
    for tabela, dados in parquets.items():
        if not re.fullmatch(r"painel_\d+_[a-z0-9_]+", tabela):
            raise ValueError(f"tabela inesperada: {tabela}")
        import pyarrow.parquet as pq  # vem com o duckdb/pandas do projeto

        con.register(f"_{tabela}", pq.read_table(io.BytesIO(dados)))
        con.execute(f'CREATE TABLE "{tabela}" AS SELECT * FROM "_{tabela}"')
        con.unregister(f"_{tabela}")
    return con


def baixar(api: str, chave: str, cliente: Any = None) -> dict[str, bytes]:
    """As tabelas prontas da empresa pela API do Lastro (LST-47), com a chave de leitura no cabeçalho."""
    import httpx

    http = cliente or httpx.Client(base_url=api.rstrip("/"), timeout=120, headers={"X-Lastro-Chave": chave})
    tabelas = [t for t in http.get("/bi/v1/tabelas").raise_for_status().json()["tabelas"] if t.startswith("painel_")]
    return {t: http.get(f"/bi/v1/{t}.parquet").raise_for_status().content for t in tabelas}


def catalogo(con: duckdb.DuckDBPyConnection) -> dict[str, dict[str, Any]]:
    """Por tabela: assunto, medidas numéricas e dimensões permitidas (só nomes e tipos; nenhum valor)."""
    cat: dict[str, dict[str, Any]] = {}
    for (tabela,) in con.execute("SELECT table_name FROM information_schema.tables ORDER BY 1").fetchall():
        cols = {r[0]: str(r[1]) for r in con.execute(f'DESCRIBE "{tabela}"').fetchall()}
        medidas = [c for c, t in cols.items() if t in ("DOUBLE", "FLOAT", "DECIMAL") or (c == "quantidade" and "INT" in t)]
        dims = [c for c in cols if DIMENSAO_PERMITIDA.match(c)
                and con.execute(f'SELECT count(DISTINCT "{c}") FROM "{tabela}"').fetchone()[0] > 1]
        cat[tabela] = {"assunto": assunto(tabela), "medidas": medidas, "dimensoes": dims, "tem_registros": "registros" in cols}
    return cat


# ---- plano ------------------------------------------------------------------------------------------------------

@dataclass
class Plano:
    tabela: str
    agregacao: Literal["soma", "media", "contagem"] = "soma"
    medida: str | None = None
    dimensao: str | None = None
    por_mes: bool = False
    filtro_coluna: str | None = None
    filtro_valor: str | None = None
    grafico: Literal["numero", "barras", "linha", "pizza"] = "barras"
    titulo: str = ""
    avisos: list[str] = field(default_factory=list)


class PlanoInvalido(ValueError):
    pass


def validar(p: Plano, cat: dict[str, dict[str, Any]]) -> Plano:
    """Tudo o que entra no SQL vem do catálogo; o que não vem é recusado com o motivo."""
    if p.tabela not in cat:
        raise PlanoInvalido(f"não conheço a tabela {p.tabela!r}; escolha entre {', '.join(cat)}")
    c = cat[p.tabela]
    if p.agregacao not in AGREGACOES:
        raise PlanoInvalido(f"agregação {p.agregacao!r} não existe")
    if p.agregacao == "contagem":
        p.medida = "registros"
    elif p.medida not in c["medidas"]:
        if not c["medidas"]:
            p.agregacao, p.medida = "contagem", "registros"
            p.avisos.append("esta tabela não tem valor numérico: mostrei a contagem de registros")
        else:
            raise PlanoInvalido(f"{p.medida!r} não é um valor desta tabela; use {', '.join(c['medidas'])}")
    for col in (p.dimensao, p.filtro_coluna):
        if col and col not in c["dimensoes"]:
            raise PlanoInvalido(f"{col!r} detalha demais para o relatório rápido; use {', '.join(nome(d) for d in c['dimensoes'])}"
                                " (cliente, vendedor e produto estão nos relatórios do Power BI e do Looker)")
    if p.por_mes and "ano_mes" not in c["dimensoes"]:
        raise PlanoInvalido("esta tabela não tem data por mês")
    if p.grafico not in GRAFICOS:
        p.grafico = "barras"
    if p.grafico == "linha" and not p.por_mes:
        p.por_mes = "ano_mes" in c["dimensoes"]
    if not p.titulo:
        partes = [("Quantidade de registros" if p.agregacao == "contagem" else f"{p.agregacao.capitalize()} de {nome(p.medida or '')}")]
        if p.dimensao:
            partes.append(f"por {nome(p.dimensao)}")
        if p.por_mes:
            partes.append("por mês")
        p.titulo = " ".join(partes)
    return p


def sql(p: Plano) -> tuple[str, list[Any]]:
    """SQL de leitura montado pelo Lastro (nunca pela LLM). Nomes vêm do catálogo validado; valor de filtro é parâmetro."""
    grupos = [c for c in ((["ano_mes"] if p.por_mes else []) + ([p.dimensao] if p.dimensao else []))]
    valor = f'round({AGREGACOES[p.agregacao]}("{p.medida}"), 2) AS valor'
    q = f"SELECT {', '.join(f'{chr(34)}{g}{chr(34)}' for g in grupos) + ', ' if grupos else ''}{valor} FROM \"{p.tabela}\""
    params: list[Any] = []
    if p.filtro_coluna and p.filtro_valor is not None:
        q += f' WHERE "{p.filtro_coluna}" = ?'
        params.append(str(p.filtro_valor))
    if grupos:
        q += f" GROUP BY {', '.join(str(i + 1) for i in range(len(grupos)))}"
        q += " ORDER BY 1" if p.por_mes else f" ORDER BY {len(grupos) + 1} DESC"
    verificar(q)
    return q, params


def executar(con: duckdb.DuckDBPyConnection, p: Plano) -> tuple[list[str], list[tuple]]:
    q, params = sql(p)
    cur = con.execute(q, params)
    return [d[0] for d in cur.description], cur.fetchall()


# ---- interpretação: LLM (LangChain + Gemini gratuito) ou regras simples -----------------------------------------

INSTRUCOES = """Você transforma um pedido de análise em português num plano JSON para um gráfico.
Responda SÓ com um objeto JSON com as chaves: tabela, agregacao ("soma" | "media" | "contagem"), medida (coluna numérica ou null),
dimensao (coluna ou null), por_mes (true/false), filtro_coluna (coluna ou null), filtro_valor (texto ou null),
grafico ("numero" | "barras" | "linha" | "pizza"), titulo (texto curto em português).
Use só tabelas e colunas do catálogo abaixo. Se o pedido detalhar além das dimensões permitidas, escolha a mais próxima permitida.
Catálogo (só nomes; você não recebe dados):
{catalogo}"""


def catalogo_para_llm(cat: dict[str, dict[str, Any]]) -> str:
    return json.dumps({t: {"assunto": c["assunto"], "medidas": c["medidas"], "dimensoes": c["dimensoes"]} for t, c in cat.items()},
                      ensure_ascii=False)


def interpretar_llm(pergunta: str, cat: dict[str, dict[str, Any]], llm: Any) -> Plano:
    """Agente LangChain: prompt → modelo de chat → JSON → Plano validado. O modelo só vê pergunta e catálogo."""
    from langchain_core.output_parsers import StrOutputParser
    from langchain_core.prompts import ChatPromptTemplate

    prompt = ChatPromptTemplate.from_messages([("system", INSTRUCOES), ("human", "{pergunta}")])
    texto = (prompt | llm | StrOutputParser()).invoke({"catalogo": catalogo_para_llm(cat), "pergunta": pergunta})
    achado = re.search(r"\{.*\}", texto, re.DOTALL)
    if not achado:
        raise PlanoInvalido("o modelo não devolveu um plano em JSON")
    bruto = json.loads(achado.group(0))
    campos = {k: bruto.get(k) for k in Plano.__dataclass_fields__ if k != "avisos" and k in bruto}
    return validar(Plano(**campos), cat)


def interpretar_simples(pergunta: str, cat: dict[str, dict[str, Any]]) -> Plano:
    """Sem chave de LLM: palavras-chave do pedido. Bom para os pedidos comuns de demonstração."""
    q = _sem_acento(pergunta)
    tabela = next((t for t, c in cat.items() if any(w in q for w in _sem_acento(c["assunto"]).split())), next(iter(cat)))
    for chave, assunto_ in (("funcionari", "RH"), ("funil", "Funil"), ("orcament", "Funil"), ("produto", "Produtos"), ("vend", "Vendas")):
        if chave in q:
            tabela = next((t for t, c in cat.items() if c["assunto"].startswith(assunto_)), tabela)
            break
    c = cat[tabela]
    dims = {"regiao": next((d for d in c["dimensoes"] if d.endswith("_regiao")), None),
            "estado": next((d for d in c["dimensoes"] if d.endswith("_estado")), None), "uf": next((d for d in c["dimensoes"] if d.endswith("_estado")), None),
            "empresa": "company" if "company" in c["dimensoes"] else None, "setor": "setor_nome" if "setor_nome" in c["dimensoes"] else None,
            "status": "status_nome" if "status_nome" in c["dimensoes"] else None}
    dimensao = next((d for k, d in dims.items() if k in q and d), None)
    por_mes = bool(re.search(r"\b(mes|mensal|evolu|tempo|ao longo)", q)) and "ano_mes" in c["dimensoes"]
    contagem = bool(re.search(r"\b(quant|numero de|qtd)", q)) or not c["medidas"]
    medida = None if contagem else c["medidas"][0]
    grafico = "linha" if por_mes else ("barras" if dimensao else "numero")
    return validar(Plano(tabela=tabela, agregacao="contagem" if contagem else ("media" if "media" in q else "soma"), medida=medida,
                         dimensao=dimensao, por_mes=por_mes, grafico=grafico), cat)


def modelo_gemini(chave: str, modelo: str = "gemini-2.0-flash") -> Any:
    from langchain_google_genai import ChatGoogleGenerativeAI

    return ChatGoogleGenerativeAI(model=modelo, google_api_key=chave, temperature=0)
