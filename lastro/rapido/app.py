"""Lastro · relatórios rápidos (LST-54). Rodar: `uv run --extra rapido streamlit run lastro/rapido/app.py`.

Segredos (Streamlit Cloud → Settings → Secrets, ou .streamlit/secrets.toml local, nunca no repositório):
    LASTRO_API = "https://lastro-api-73zx.onrender.com"
    LASTRO_CHAVE = "lst_..."          # chave de leitura do BI da empresa (LST-47)
    GOOGLE_API_KEY = "..."            # opcional: Gemini gratuito do AI Studio para o agente
"""

from __future__ import annotations

import logging
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

MESES = ["jan", "fev", "mar", "abr", "mai", "jun", "jul", "ago", "set", "out", "nov", "dez"]

def indicadores() -> None:
    # Mesmo esqueleto do painel de entrega (LST-55): filtros → 4 cartões → gráfico principal + ranking → conferência
    with st.container(border=True):
        tabela = st.selectbox("Relatório", list(cat), format_func=lambda t: cat[t]["assunto"])
        c = cat[tabela]
        medida = c["medidas"][0] if c["medidas"] else None
        nomes_f = [d for d in c["dimensoes"] if d == "company" or d.endswith("_regiao")] + (["ano"] if "ano_mes" in c["dimensoes"] else [])
        filtros: dict[str, list] = {}
        if nomes_f:
            cols_f = st.columns(len(nomes_f))
            for col, d in zip(cols_f, nomes_f, strict=True):
                expr = n.ANO_SQL if d == "ano" else f'"{d}"'
                cond = "ano_mes IS NOT NULL" if d == "ano" else f'"{d}" IS NOT NULL'
                valores = [r[0] for r in con.execute(f'SELECT DISTINCT {expr} FROM "{tabela}" WHERE {cond} ORDER BY 1').fetchall()]
                filtros[d] = col.multiselect("Ano" if d == "ano" else n.nome(d).capitalize(), valores, placeholder="todos" if d == "ano" else "todas")
    medida_nome = n.nome(medida).capitalize() if medida else "Registros"
    r = n.resumo(con, tabela, medida, filtros)
    # Sem coluna de valor (ex.: RH), a medida é a contagem: um cartão "Registros" só, sem média (26/11)
    comp = r["comparacao"]
    k = st.columns((3 if medida else 1) + (1 if comp else 0))
    if medida:
        k[0].metric(rotulo_total(n.nome(medida)), br(r["total"]), border=True)
        k[1].metric("Registros", br(r["registros"], 0), border=True)
        k[2].metric("Média por registro", br(r["media"]) if r["media"] is not None else "—", border=True)
    else:
        k[0].metric("Registros", br(r["registros"], 0), border=True)
    if comp:
        var = comp["variacao"]
        base = f"{comp['ano'] - 1}: {br(comp['anterior'])}" if comp["anterior"] is not None else f"sem dados de {comp['ano'] - 1}"
        k[-1].metric(f"{comp['ano']} até {MESES[comp['mes'] - 1]} vs mesmo período", br(comp["atual"], 2 if medida else 0),
                    delta=(f"{var * 100:+.1f}%".replace(".", ",") if var is not None else None), border=True)
        k[-1].caption(base)
    g1, g2 = st.columns([2, 1])
    valor_sql = f'sum("{medida}")' if medida else "sum(registros)"
    if "ano_mes" in c["dimensoes"]:
        w, p = n.onde(filtros)
        df = con.execute(f'SELECT ano_mes AS "Mês", {valor_sql} AS valor FROM "{tabela}"{w} GROUP BY 1 ORDER BY 1', p).df()
        fig_mes = grafico(px.line(df, x="Mês", y="valor", title="Evolução mensal", color_discrete_sequence=[OURO]), medida_nome)
        g1.plotly_chart(fig_mes.update_xaxes(type="category", nticks=8), use_container_width=True)  # "2025-10", não "Oct 2025"
    dim = n.dimensao_do_ranking(c["dimensoes"])
    if dim:
        topo, detalhe = n.ranking(con, tabela, dim, medida, filtros)
        import pandas as pd

        df = pd.DataFrame(topo, columns=["dim", "valor", "parte"])
        df["rotulo"] = [f"{p * 100:.1f}%".replace(".", ",") if p is not None else "" for p in df["parte"]]
        fig = px.bar(df, x="valor", y="dim", orientation="h", text="rotulo", title=f"Ranking por {n.nome(dim)} (top 10)".replace("uf ", "UF "),
                     color_discrete_sequence=[OURO], labels={"dim": "", "valor": medida_nome})
        fig = grafico(fig.update_yaxes(autorange="reversed").update_traces(textposition="outside", cliponaxis=False), "")
        g2.plotly_chart(fig.update_layout(margin={"t": 48, "l": 8, "r": 64, "b": 8}), use_container_width=True)
        st.subheader(f"Conferência por {n.nome(dim)}")
        rotulo_dim = n.nome(dim)[:1].upper() + n.nome(dim)[1:]  # "UF da obra", não "Uf da obra"
        pct = lambda p: f"{p * 100:.1f}%".replace(".", ",") if p is not None else "—"
        if medida:
            tab = pd.DataFrame([(k_, br(v), br(r_, 0), pct(p)) for k_, v, r_, p in detalhe], columns=[rotulo_dim, medida_nome, "Registros", "% do total"])
        else:  # sem coluna de valor: a medida já é a contagem de registros
            tab = pd.DataFrame([(k_, br(r_, 0), pct(p)) for k_, _, r_, p in detalhe], columns=[rotulo_dim, "Registros", "% do total"])
        st.dataframe(tab, use_container_width=True, hide_index=True)  # números já no formato 1.234,56
        st.caption(f"Soma da conferência: {br(sum(v for _, v, _, _ in detalhe), 2 if medida else 0)}, igual ao primeiro cartão.")
    st.caption("Números somados das tabelas prontas do BI (demandas aprovadas no Lastro). Comparação: janeiro até o último mês com dado, "
               "contra o mesmo período do ano anterior.")

def pergunte() -> None:
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
                q, _ = n.sql(plano)
                st.code(q, language="sql")
                st.caption("O modelo de linguagem só recebeu o pedido e os nomes das colunas; os números saem deste SQL, rodado no Lastro.")


def aba_segura(aba, desenhar) -> None:
    """Uma aba com erro não derruba a outra: as duas rodam no mesmo script (26/11, RH quebrava o "Pergunte")."""
    with aba:
        try:
            desenhar()
        except Exception:
            logging.getLogger("lastro.rapido").exception("aba falhou")
            st.error("Esta parte do relatório não carregou. O erro foi registrado; as outras abas continuam funcionando.")


aba_segura(aba_kpi, indicadores)
aba_segura(aba_agente, pergunte)
