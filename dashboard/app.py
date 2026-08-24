from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
import plotly.express as px
import streamlit as st

from config.settings import settings

st.set_page_config(page_title="FuelPrice Analytics", page_icon="⛽", layout="wide")

NAVY, BLUE, GREEN, ORANGE, RED = "#0B1F33", "#1473E6", "#19A974", "#F59E0B", "#E5484D"
PRODUCT_COLORS = {
    "GASOLINA COMUM": BLUE, "GASOLINA ADITIVADA": "#7357D8",
    "ETANOL HIDRATADO": GREEN, "DIESEL": ORANGE,
    "DIESEL S10": "#E8732A", "GNV": "#16B8C8",
}

st.markdown("""
<style>
.stApp{background:#F5F7FA}.block-container{max-width:1500px;padding-top:1.4rem;padding-bottom:3rem}
[data-testid="stSidebar"]{background:linear-gradient(180deg,#091A2C 0%,#102D49 100%);border-right:1px solid #24445F}
[data-testid="stSidebar"] *{color:#F8FAFC}[data-testid="stSidebar"] [data-baseweb="select"]>div{background:#173752}
[data-testid="stMetric"]{background:white;border:1px solid #E1E8F0;border-radius:14px;padding:17px 18px;
box-shadow:0 3px 14px rgba(11,31,51,.045);min-height:112px}
[data-testid="stMetricLabel"]{color:#64748B;font-size:.84rem;font-weight:600;letter-spacing:.01em}
[data-testid="stMetricValue"]{color:#0B1F33;font-weight:750;font-size:1.55rem}
.hero{position:relative;overflow:hidden;background:linear-gradient(120deg,#091A2C,#123E66 72%,#1473E6);
color:white;padding:29px 32px;border-radius:18px;margin-bottom:20px;box-shadow:0 10px 30px rgba(11,31,51,.16)}
.hero:after{content:"";position:absolute;width:240px;height:240px;border:42px solid rgba(255,255,255,.06);
border-radius:50%;right:-60px;top:-100px}.hero-brand{font-size:.72rem;font-weight:700;letter-spacing:.16em;
text-transform:uppercase;color:#79B8FF;margin-bottom:8px}.hero h1{font-size:2.05rem;margin:0 0 7px;letter-spacing:-.025em}
.hero p{margin:0;color:#CFE1F5}.hero-meta{display:flex;gap:8px;margin-top:17px;flex-wrap:wrap}
.pill{display:inline-block;background:rgba(255,255,255,.1);border:1px solid rgba(255,255,255,.15);
padding:5px 10px;border-radius:999px;font-size:.75rem;color:#E7F1FC}
.section-title{margin:23px 0 12px}.section-title h3{margin:0;color:#0B1F33;font-size:1.12rem}.section-title p{margin:3px 0 0;color:#64748B;font-size:.86rem}
.coverage{background:white;border:1px solid #E1E8F0;border-radius:12px;padding:11px 16px;margin:10px 0 18px;
color:#526477;font-size:.84rem}.coverage strong{color:#0B1F33}.status-dot{display:inline-block;width:8px;height:8px;
border-radius:50%;background:#19A974;margin-right:6px;box-shadow:0 0 0 3px rgba(25,169,116,.13)}
.insight{background:white;border-left:4px solid #1473E6;border-radius:10px;padding:13px 16px;
margin:7px 0;box-shadow:0 3px 12px rgba(11,31,51,.04)}
div[data-testid="stPlotlyChart"]{background:white;border:1px solid #E4EAF2;border-radius:14px;padding:8px}
button[data-baseweb="tab"]{font-weight:650}.stTabs [data-baseweb="tab-list"]{gap:8px}
.stTabs [data-baseweb="tab"]{background:white;border:1px solid #E1E8F0;border-radius:10px 10px 0 0;padding:10px 18px}
footer{visibility:hidden}@media(max-width:900px){.block-container{padding-left:1rem;padding-right:1rem}.hero{padding:23px}.hero h1{font-size:1.65rem}}
</style>""", unsafe_allow_html=True)


@st.cache_data(ttl=900, show_spinner="Carregando camada analítica...")
def load_data() -> pd.DataFrame:
    candidates = [
        Path(settings.processed_dir / "fuel_prices.parquet"),
        Path(settings.base_dir / "data" / "published" / "fuel_prices.parquet"),
    ]
    path = next((candidate for candidate in candidates if candidate.exists()), None)
    if path is None:
        return pd.DataFrame()
    frame = pd.read_parquet(path)
    frame["data_coleta"] = pd.to_datetime(frame["data_coleta"])
    return frame


def money(value: float) -> str:
    return "—" if pd.isna(value) else f"R$ {value:,.3f}".replace(",", "X").replace(".", ",").replace("X", ".")


def percent(value: float) -> str:
    return "—" if pd.isna(value) else f"{value:+.2f}%".replace(".", ",")


def polish(fig, height: int = 420):
    fig.update_layout(height=height, margin=dict(l=20, r=20, t=55, b=25), paper_bgcolor="white",
                      plot_bgcolor="white", font=dict(family="Arial", color=NAVY), legend_title_text="")
    fig.update_xaxes(showgrid=False)
    fig.update_yaxes(gridcolor="#E8EEF5", zeroline=False)
    return fig


df = load_data()
if df.empty:
    st.error("A camada processada não foi encontrada. Execute `python main.py`.")
    st.stop()

st.markdown(f"""<div class="hero"><div class="hero-brand">Data intelligence platform</div>
<h1>FuelPrice Analytics</h1><p>Monitoramento executivo do mercado brasileiro de combustíveis</p>
<div class="hero-meta"><span class="pill">Fonte oficial · ANP</span><span class="pill">Atualização semanal</span>
<span class="pill">Período · {df.data_coleta.min():%d/%m/%Y} — {df.data_coleta.max():%d/%m/%Y}</span>
<span class="pill">Qualidade monitorada</span></div></div>""",
            unsafe_allow_html=True)

with st.sidebar:
    st.markdown("# ⛽ FuelPrice")
    st.caption("ANALYTICS WORKSPACE")
    st.divider()
    st.markdown("### Filtros da análise")
    st.caption("Todo o painel responde ao recorte")
    min_date, max_date = df.data_coleta.min().date(), df.data_coleta.max().date()
    period = st.date_input("Período", (min_date, max_date), min_value=min_date, max_value=max_date)
    years = st.multiselect("Ano", sorted(df.ano.dropna().unique()), placeholder="Todos")
    months = st.multiselect("Mês", sorted(df.mes.dropna().unique()), placeholder="Todos")
    regions = st.multiselect("Região", sorted(df.regiao.dropna().unique()), placeholder="Todas")
    states = st.multiselect("Estado", sorted(df.uf.dropna().unique()), placeholder="Todos")
    products = st.multiselect("Combustível", sorted(df.produto.dropna().unique()), placeholder="Todos")
    city_source = df[df.uf.isin(states)] if states else df
    cities = st.multiselect("Município", sorted(city_source.municipio.dropna().unique()), placeholder="Todos")
    st.divider()
    st.markdown("<span class='status-dot'></span>Dados processados disponíveis", unsafe_allow_html=True)
    st.caption(f"{len(df):,.0f} observações na base".replace(",", "."))

start, end = period if isinstance(period, (tuple, list)) and len(period) == 2 else (period, period)
filtered = df[df.data_coleta.between(pd.Timestamp(start), pd.Timestamp(end))].copy()
for column, values in (("ano", years), ("mes", months), ("regiao", regions), ("uf", states),
                       ("produto", products), ("municipio", cities)):
    if values:
        filtered = filtered[filtered[column].isin(values)]
if filtered.empty:
    st.warning("Nenhum registro corresponde aos filtros selecionados.")
    st.stop()

daily = filtered.groupby("data_coleta", as_index=False).preco_venda.mean().sort_values("data_coleta")
first_price, last_price = daily.preco_venda.iloc[0], daily.preco_venda.iloc[-1]
change = ((last_price / first_price) - 1) * 100 if first_price else np.nan
st.markdown('<div class="section-title"><h3>Resumo executivo</h3><p>Indicadores centrais para o recorte selecionado</p></div>', unsafe_allow_html=True)
kpi_data = [
    ("Preço médio", money(filtered.preco_venda.mean()), percent(change)),
    ("Mediana", money(filtered.preco_venda.median()), None),
    ("Menor preço", money(filtered.preco_venda.min()), None),
    ("Maior preço", money(filtered.preco_venda.max()), None),
    ("Variação", percent(change), "início × fim"),
    ("Postos", f"{filtered.cnpj_revenda.nunique():,}".replace(",", "."), None),
    ("Municípios", f"{filtered.municipio.nunique():,}".replace(",", "."), None),
    ("Outliers", f"{int(filtered.outlier.sum()):,}".replace(",", "."), None),
]
for row in (kpi_data[:4], kpi_data[4:]):
    for box, (label, value, delta) in zip(st.columns(4), row):
        box.metric(label, value, delta)
st.markdown(f"""<div class="coverage"><span class="status-dot"></span><strong>Recorte ativo</strong> &nbsp;·&nbsp;
{len(filtered):,.0f} observações &nbsp;·&nbsp; {filtered.uf.nunique()} UFs &nbsp;·&nbsp;
{filtered.municipio.nunique()} municípios &nbsp;·&nbsp; {filtered.produto.nunique()} combustíveis</div>""".replace(",", "."), unsafe_allow_html=True)

overview, geography, competition, quality = st.tabs(
    ["◉ Visão geral", "⌖ Geografia", "◇ Etanol × Gasolina", "✓ Qualidade & Outliers"]
)

monthly = filtered.groupby(["ano_mes", "produto"], as_index=False).preco_venda.mean()
with overview:
    st.markdown('<div class="section-title"><h3>Comportamento de mercado</h3><p>Tendência, posicionamento e dispersão dos combustíveis</p></div>', unsafe_allow_html=True)
    fig = px.line(monthly, x="ano_mes", y="preco_venda", color="produto", markers=True,
                  color_discrete_map=PRODUCT_COLORS, title="Evolução do preço médio")
    fig.update_yaxes(tickprefix="R$ ")
    st.plotly_chart(polish(fig, 450), width="stretch")
    left, right = st.columns(2)
    product_avg = filtered.groupby("produto", as_index=False).preco_venda.mean().sort_values("preco_venda")
    fig = px.bar(product_avg, x="preco_venda", y="produto", orientation="h", color="produto",
                 color_discrete_map=PRODUCT_COLORS, title="Preço médio por combustível", text_auto=".3f")
    fig.update_xaxes(tickprefix="R$ ")
    left.plotly_chart(polish(fig), width="stretch")
    # A distribuição visual usa amostra determinística para limitar a serialização no navegador;
    # todos os KPIs e agregações acima continuam calculados sobre 100% do recorte.
    distribution = filtered.sample(min(len(filtered), 30_000), random_state=42)
    fig = px.box(distribution, x="produto", y="preco_venda", color="produto", color_discrete_map=PRODUCT_COLORS,
                 title="Distribuição dos preços", points=False)
    fig.update_yaxes(tickprefix="R$ ")
    right.plotly_chart(polish(fig), width="stretch")

with geography:
    st.markdown('<div class="section-title"><h3>Inteligência regional</h3><p>Diferenças de preço, volatilidade e ranking municipal</p></div>', unsafe_allow_html=True)
    left, right = st.columns([1.35, 1])
    state_avg = filtered.groupby(["uf", "regiao"], as_index=False).preco_venda.mean().sort_values("preco_venda", ascending=False)
    fig = px.bar(state_avg, x="uf", y="preco_venda", color="regiao", title="Preço médio por estado", text_auto=".2f")
    fig.update_yaxes(tickprefix="R$ ")
    left.plotly_chart(polish(fig), width="stretch")
    region_stats = filtered.groupby("regiao", as_index=False).agg(preco_medio=("preco_venda", "mean"), volatilidade=("preco_venda", "std"))
    fig = px.scatter(region_stats, x="preco_medio", y="volatilidade", text="regiao", size="preco_medio",
                     color="volatilidade", color_continuous_scale="Blues", title="Preço × volatilidade regional")
    fig.update_traces(textposition="top center")
    right.plotly_chart(polish(fig), width="stretch")
    station = "cnpj_revenda" if "cnpj_revenda" in filtered else "revenda"
    cities_rank = filtered.groupby(["uf", "municipio"], as_index=False).agg(preco_medio=("preco_venda", "mean"), postos=(station, "nunique"))
    top = cities_rank.nlargest(15, "preco_medio").sort_values("preco_medio")
    fig = px.bar(top, x="preco_medio", y="municipio", color="uf", orientation="h",
                 title="15 municípios com maior preço médio", hover_data=["postos"])
    fig.update_xaxes(tickprefix="R$ ")
    st.plotly_chart(polish(fig, 480), width="stretch")

with competition:
    st.markdown('<div class="section-title"><h3>Decisão de abastecimento</h3><p>Comparação econômica com limiar configurável de 70%</p></div>', unsafe_allow_html=True)
    base = filtered[filtered.produto.isin(["ETANOL HIDRATADO", "GASOLINA COMUM"])]
    comparison = base.groupby(["ano_mes", "uf", "produto"], as_index=False).preco_venda.mean()
    pivot = comparison.pivot_table(index=["ano_mes", "uf"], columns="produto", values="preco_venda").reset_index()
    if {"ETANOL HIDRATADO", "GASOLINA COMUM"} <= set(pivot.columns):
        pivot["relacao"] = pivot["ETANOL HIDRATADO"] / pivot["GASOLINA COMUM"]
        pivot["compensa"] = np.where(pivot.relacao <= settings.ethanol_threshold, "Compensa", "Não compensa")
        latest = pivot[pivot.ano_mes.eq(pivot.ano_mes.max())].sort_values("relacao")
        fig = px.bar(latest, x="uf", y="relacao", color="compensa",
                     color_discrete_map={"Compensa": GREEN, "Não compensa": ORANGE},
                     title=f"Competitividade do etanol por UF — {pivot.ano_mes.max()}")
        fig.add_hline(y=settings.ethanol_threshold, line_dash="dash", line_color=RED,
                      annotation_text=f"Limiar {settings.ethanol_threshold:.0%}")
        st.plotly_chart(polish(fig, 450), width="stretch")
        left, right = st.columns(2)
        trend = pivot.groupby("ano_mes", as_index=False).relacao.mean()
        fig = px.line(trend, x="ano_mes", y="relacao", markers=True, title="Evolução da relação etanol/gasolina")
        fig.add_hline(y=settings.ethanol_threshold, line_dash="dash", line_color=RED)
        left.plotly_chart(polish(fig), width="stretch")
        right.dataframe(latest[["uf", "ETANOL HIDRATADO", "GASOLINA COMUM", "relacao", "compensa"]],
                        hide_index=True, width="stretch")
    else:
        st.info("Selecione gasolina comum e etanol hidratado para visualizar a comparação.")

with quality:
    st.markdown('<div class="section-title"><h3>Confiabilidade dos dados</h3><p>Dispersão e observações que merecem investigação</p></div>', unsafe_allow_html=True)
    left, right = st.columns([1, 1.3])
    outliers = filtered[filtered.outlier].copy()
    counts = pd.DataFrame({"classe": ["Regulares", "Outliers"], "registros": [len(filtered) - len(outliers), len(outliers)]})
    fig = px.pie(counts, names="classe", values="registros", hole=.65, color="classe",
                 color_discrete_map={"Regulares": BLUE, "Outliers": RED}, title="Composição da qualidade")
    left.plotly_chart(polish(fig), width="stretch")
    volatility = filtered.groupby("produto", as_index=False).agg(
        volatilidade=("preco_venda", "std"), amplitude=("preco_venda", lambda s: s.max() - s.min()))
    fig = px.bar(volatility.sort_values("volatilidade"), x="volatilidade", y="produto", orientation="h",
                 color="amplitude", color_continuous_scale="Oranges", title="Volatilidade por combustível")
    right.plotly_chart(polish(fig), width="stretch")
    st.markdown("#### Registros sinalizados para investigação")
    columns = ["data_coleta", "uf", "municipio", "produto", "revenda", "preco_venda", "z_score", "faixa_preco"]
    st.dataframe(outliers.sort_values("z_score", key=abs, ascending=False)[columns].head(200),
                 hide_index=True, width="stretch")

st.markdown("### Insights do recorte")
state_means = filtered.groupby("uf").preco_venda.mean()
region_volatility = filtered.groupby("regiao").preco_venda.std()
changes = monthly.sort_values("ano_mes").groupby("produto").preco_venda.agg(["first", "last"])
changes["change"] = np.where(changes["first"] > 0, (changes["last"] / changes["first"] - 1) * 100, np.nan)
top_product = changes.change.idxmax()
for insight in [
    f"**{state_means.idxmax()}** apresentou o maior preço médio: **{money(state_means.max())}**.",
    f"A região **{region_volatility.idxmax()}** teve a maior volatilidade (**{region_volatility.max():.3f}**).",
    f"**{top_product}** teve a maior variação no período (**{percent(changes.loc[top_product, 'change'])}**).",
    f"Foram sinalizados **{int(filtered.outlier.sum()):,} outliers** para investigação, sem remoção automática.".replace(",", "."),
]:
    st.markdown(f'<div class="insight">{insight}</div>', unsafe_allow_html=True)

st.caption("Fonte: ANP — Série Histórica de Preços de Combustíveis. Indicadores calculados dinamicamente.")

with st.expander("Metodologia e notas técnicas"):
    st.markdown("""
    - **Preço médio:** média aritmética das observações no recorte selecionado.
    - **Variação:** diferença percentual entre o primeiro e o último preço médio diário do período.
    - **Volatilidade:** desvio padrão dos preços observados; não representa risco financeiro.
    - **Etanol competitivo:** relação entre preço médio do etanol e da gasolina comum menor ou igual a 70%.
    - **Outliers:** observações com valor absoluto do Z-Score superior ao limite configurado; não são removidas.
    - Os resultados refletem os postos pesquisados pela ANP e não necessariamente todo o universo de revendas.
    """)

st.markdown("""<div style="margin-top:24px;padding:18px 4px;border-top:1px solid #DDE5EE;
display:flex;justify-content:space-between;color:#718096;font-size:.78rem">
<span>FuelPrice Analytics · Engenharia de Dados & Analytics</span><span>Python · Pandas · NumPy · Plotly · Streamlit</span></div>""",
            unsafe_allow_html=True)
