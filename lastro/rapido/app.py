"""Lastro · relatórios rápidos (LST-54). Rodar: `uv run --extra rapido streamlit run lastro/rapido/app.py`.

Segredos (Streamlit Cloud → Settings → Secrets, ou .streamlit/secrets.toml local, nunca no repositório):
    LASTRO_API = "https://lastro-api-73zx.onrender.com"
    LASTRO_CHAVE = "lst_..."          # chave de leitura do BI da empresa (LST-47)
    GOOGLE_API_KEY = "..."            # opcional: Gemini gratuito do AI Studio para o agente
"""

from __future__ import annotations

import sys
from pathlib import Path

import plotly.express as px
import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))  # no Streamlit Cloud o app roda como script
from lastro.rapido import nucleo as n

OURO = "#B58324"
PALETA = ["#B58324", "#2F5D7C", "#8E98A3", "#A4602F", "#4F7A5A", "#56606B", "#C9A15B", "#3E4A57"]
MARCA = Path(__file__).resolve().parents[2] / "site" / "marca" / "favicon-32.png"
st.set_page_config(page_title="Lastro · relatórios rápidos", page_icon=str(MARCA) if MARCA.exists() else None, layout="wide")


def br(v: float, casas: int = 2) -> str:
    return f"{v:,.{casas}f}".replace(",", "X").replace(".", ",").replace("X", ".")


def segredo(nome: str) -> str:
    try:
        return str(st.secrets.get(nome, ""))
    except Exception:  # noqa: BLE001  (sem secrets.toml local)
        return ""


@st.cache_resource(ttl=3600, show_spinner="Lendo as tabelas prontas do BI…")
def conexao(api: str, chave: str):
    return n.carregar(n.baixar(api, chave))


# Cores vêm do tema (.streamlit/config.toml): nada fixo no texto, para não sumir no tema escuro (LST-55, C3).
st.title("Lastro · relatórios rápidos")
st.caption("KPIs gerais por empresa, setor, região/UF e mês. O detalhe por cliente, vendedor e produto está nos relatórios do Power BI e do Looker.")


def grafico(fig, medida_nome: str):
    """Plotly no padrão brasileiro (1.234,56) e com o nome da medida no eixo, em vez de "valor"."""
    fig.update_layout(separators=",.", font_family="IBM Plex Sans, Segoe UI, sans-serif", margin={"t": 48, "l": 8, "r": 8, "b": 8},
                      yaxis_title=medida_nome, legend_title_text="")
    return fig


def rotulo_total(nome: str) -> str:
    return nome.capitalize() if nome.lower().startswith("total") else f"Total de {nome}"

api = segredo("LASTRO_API") or "https://lastro-api-73zx.onrender.com"
chave = segredo("LASTRO_CHAVE")
if not chave:
    chave = st.sidebar.text_input("Chave de leitura do BI (lst_…)", type="password")
if not chave:
    st.info("Informe a chave de leitura do BI da empresa (portal do Lastro → conta → Conectar ao BI).")
    st.stop()
try:
    con = n.por_sessao(conexao(api, chave))  # cursor por execução: a conexão em cache é de todos
except Exception as e:  # noqa: BLE001
    st.error(f"Não consegui ler o BI ({type(e).__name__}). Confira a chave de leitura.")
    st.stop()
cat = n.catalogo(con)
if not cat:
    st.warning("Nenhuma tabela pronta publicada no BI desta empresa.")
    st.stop()

aba_kpi, aba_agente = st.tabs(["Indicadores", "Pergunte"])

with aba_kpi:
    tabela = st.selectbox("Relatório", list(cat), format_func=lambda t: cat[t]["assunto"])
    c = cat[tabela]
    medida = c["medidas"][0] if c["medidas"] else None
    filtros = [d for d in c["dimensoes"] if d in ("company",) or d.endswith("_regiao")]
    where, params = [], []
    cols_f = st.columns(max(len(filtros), 1))
    for col, d in zip(cols_f, filtros, strict=False):
        valores = [r[0] for r in con.execute(f'SELECT DISTINCT "{d}" FROM "{tabela}" WHERE "{d}" IS NOT NULL ORDER BY 1').fetchall()]
        escolha = col.multiselect(n.nome(d).capitalize(), valores, placeholder="todas")
        if escolha:
            where.append(f'"{d}" IN ({", ".join("?" * len(escolha))})')
            params += escolha
    filtro_sql = (" WHERE " + " AND ".join(where)) if where else ""
    total = con.execute(f'SELECT {"sum(" + chr(34) + medida + chr(34) + ")" if medida else "0"}, sum(registros) FROM "{tabela}"{filtro_sql}', params).fetchone()
    k1, k2, k3 = st.columns(3)
    if medida:
        k1.metric(rotulo_total(n.nome(medida)), br(total[0] or 0))
        k3.metric("Média por registro", br((total[0] or 0) / (total[1] or 1)))
    k2.metric("Registros", br(total[1] or 0, 0))
    valor_sql = f'sum("{medida}")' if medida else "sum(registros)"
    medida_nome = n.nome(medida).capitalize() if medida else "Registros"
    g1, g2 = st.columns([3, 2])
    if "ano_mes" in c["dimensoes"]:
        df = con.execute(f'SELECT ano_mes AS "Mês", {valor_sql} AS valor FROM "{tabela}"{filtro_sql} GROUP BY 1 ORDER BY 1', params).df()
        g1.plotly_chart(grafico(px.line(df, x="Mês", y="valor", title="Evolução mensal", color_discrete_sequence=[OURO]), medida_nome), use_container_width=True)
    geo = next((d for d in c["dimensoes"] if d.endswith("_regiao")), None) or next((d for d in c["dimensoes"] if d == "setor_nome"), None)
    if geo:
        df = con.execute(f'SELECT "{geo}" AS dim, {valor_sql} AS valor FROM "{tabela}"{filtro_sql} GROUP BY 1 ORDER BY 2 DESC', params).df()
        # Participação em barras ordenadas (mais legível que rosca para comparar partes; LST-55)
        g2.plotly_chart(grafico(px.bar(df, x="valor", y="dim", orientation="h", title=f"Por {n.nome(geo)}", color_discrete_sequence=[OURO],
                                       labels={"dim": "", "valor": medida_nome}).update_yaxes(autorange="reversed"), ""), use_container_width=True)
    uf = next((d for d in c["dimensoes"] if d.endswith("_estado")), None)
    if uf:
        df = con.execute(f'SELECT "{uf}" AS UF, {valor_sql} AS valor FROM "{tabela}"{filtro_sql} GROUP BY 1 ORDER BY 2 DESC', params).df()
        st.plotly_chart(grafico(px.bar(df, x="UF", y="valor", title=f"Por {n.nome(uf)}", color_discrete_sequence=[OURO]), medida_nome), use_container_width=True)
    st.caption("Números somados das tabelas prontas do BI (demandas aprovadas no Lastro). Valores vazios aparecem como vazios.")

with aba_agente:
    google = segredo("GOOGLE_API_KEY")
    st.caption("Agente LangChain com Gemini gratuito" if google else "Sem chave do Gemini: interpretação por palavras-chave. "
               "Com GOOGLE_API_KEY nos secrets, um agente LangChain interpreta o pedido.")
    pergunta = st.text_input("O que você quer ver?", placeholder="Ex.: vendas por região da obra por mês; quantos funcionários por setor")
    if pergunta:
        try:
            plano = n.interpretar_llm(pergunta, cat, n.modelo_gemini(google)) if google else n.interpretar_simples(pergunta, cat)
            colunas, linhas = n.executar(con, plano)
        except Exception as e:  # noqa: BLE001
            st.warning(f"Não consegui montar esse gráfico: {e}")
        else:
            import pandas as pd

            df = pd.DataFrame(linhas, columns=colunas)
            st.subheader(plano.titulo)
            for a in plano.avisos:
                st.caption(a)
            if plano.grafico == "numero" or len(colunas) == 1:
                st.metric(plano.titulo, br(float(df["valor"].iloc[0] or 0), 0 if plano.agregacao == "contagem" else 2))
            elif plano.por_mes and plano.dimensao:
                st.plotly_chart(px.line(df, x="ano_mes", y="valor", color=plano.dimensao, color_discrete_sequence=PALETA), use_container_width=True)
            elif plano.por_mes:
                st.plotly_chart(px.line(df, x="ano_mes", y="valor", color_discrete_sequence=[OURO]), use_container_width=True)
            elif plano.grafico == "pizza":
                st.plotly_chart(px.pie(df, names=plano.dimensao, values="valor", hole=.5, color_discrete_sequence=PALETA), use_container_width=True)
            else:
                st.plotly_chart(px.bar(df, x=plano.dimensao, y="valor", color_discrete_sequence=[OURO]), use_container_width=True)
            with st.expander("Como calculei"):
                q, p = n.sql(plano)
                st.code(q, language="sql")
                st.caption("O modelo de linguagem só recebeu o pedido e os nomes das colunas; os números saem deste SQL, rodado no Lastro.")
