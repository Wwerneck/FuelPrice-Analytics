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
.stApp{background:#F4F7FB}[data-testid="stSidebar"]{background:#0B1F33}
[data-testid="stSidebar"] *{color:#F8FAFC}[data-testid="stMetric"]{background:white;
border:1px solid #E4EAF2;border-radius:14px;padding:15px;box-shadow:0 4px 16px rgba(11,31,51,.05)}
[data-testid="stMetricLabel"]{color:#64748B}[data-testid="stMetricValue"]{color:#0B1F33;font-weight:700}
.hero{background:linear-gradient(120deg,#0B1F33,#123E66);color:white;padding:24px 28px;
border-radius:18px;margin-bottom:18px}.hero h1{font-size:2rem;margin:0 0 5px}.hero p{margin:0;color:#CFE1F5}
.insight{background:white;border-left:4px solid #1473E6;border-radius:10px;padding:13px 16px;
margin:7px 0;box-shadow:0 3px 12px rgba(11,31,51,.04)}
div[data-testid="stPlotlyChart"]{background:white;border:1px solid #E4EAF2;border-radius:14px;padding:8px}
</style>""", unsafe_allow_html=True)


@st.cache_data(ttl=900, show_spinner="Carregando camada analítica...")
def load_data() -> pd.DataFrame:
    path = Path(settings.processed_dir / "fuel_prices.parquet")
    if not path.exists():
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

st.markdown(f"""<div class="hero"><h1>⛽ FuelPrice Analytics</h1><p>Inteligência sobre preços
de combustíveis • ANP • {df.data_coleta.min():%d/%m/%Y} a {df.data_coleta.max():%d/%m/%Y}</p></div>""",
            unsafe_allow_html=True)

with st.sidebar:
    st.markdown("## Painel de filtros")
    st.caption("Refine todos os indicadores e gráficos")
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
    st.caption(f"Base: {len(df):,.0f} observações".replace(",", "."))

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
for box, (label, value, delta) in zip(st.columns(8), kpi_data):
    box.metric(label, value, delta)
st.caption(f"Recorte: {len(filtered):,.0f} observações • {filtered.uf.nunique()} UFs • {filtered.produto.nunique()} combustíveis".replace(",", "."))

overview, geography, competition, quality = st.tabs(
    ["Visão geral", "Geografia", "Etanol × Gasolina", "Qualidade & Outliers"]
)

monthly = filtered.groupby(["ano_mes", "produto"], as_index=False).preco_venda.mean()
with overview:
    fig = px.line(monthly, x="ano_mes", y="preco_venda", color="produto", markers=True,
                  color_discrete_map=PRODUCT_COLORS, title="Evolução do preço médio")
    fig.update_yaxes(tickprefix="R$ ")
    st.plotly_chart(polish(fig, 450), use_container_width=True)
    left, right = st.columns(2)
    product_avg = filtered.groupby("produto", as_index=False).preco_venda.mean().sort_values("preco_venda")
    fig = px.bar(product_avg, x="preco_venda", y="produto", orientation="h", color="produto",
                 color_discrete_map=PRODUCT_COLORS, title="Preço médio por combustível", text_auto=".3f")
    fig.update_xaxes(tickprefix="R$ ")
    left.plotly_chart(polish(fig), use_container_width=True)
    fig = px.box(filtered, x="produto", y="preco_venda", color="produto", color_discrete_map=PRODUCT_COLORS,
                 title="Distribuição dos preços", points=False)
    fig.update_yaxes(tickprefix="R$ ")
    right.plotly_chart(polish(fig), use_container_width=True)

with geography:
    left, right = st.columns([1.35, 1])
    state_avg = filtered.groupby(["uf", "regiao"], as_index=False).preco_venda.mean().sort_values("preco_venda", ascending=False)
    fig = px.bar(state_avg, x="uf", y="preco_venda", color="regiao", title="Preço médio por estado", text_auto=".2f")
    fig.update_yaxes(tickprefix="R$ ")
    left.plotly_chart(polish(fig), use_container_width=True)
    region_stats = filtered.groupby("regiao", as_index=False).agg(preco_medio=("preco_venda", "mean"), volatilidade=("preco_venda", "std"))
    fig = px.scatter(region_stats, x="preco_medio", y="volatilidade", text="regiao", size="preco_medio",
                     color="volatilidade", color_continuous_scale="Blues", title="Preço × volatilidade regional")
    fig.update_traces(textposition="top center")
    right.plotly_chart(polish(fig), use_container_width=True)
    station = "cnpj_revenda" if "cnpj_revenda" in filtered else "revenda"
    cities_rank = filtered.groupby(["uf", "municipio"], as_index=False).agg(preco_medio=("preco_venda", "mean"), postos=(station, "nunique"))
    top = cities_rank.nlargest(15, "preco_medio").sort_values("preco_medio")
    fig = px.bar(top, x="preco_medio", y="municipio", color="uf", orientation="h",
                 title="15 municípios com maior preço médio", hover_data=["postos"])
    fig.update_xaxes(tickprefix="R$ ")
    st.plotly_chart(polish(fig, 480), use_container_width=True)

with competition:
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
        st.plotly_chart(polish(fig, 450), use_container_width=True)
        left, right = st.columns(2)
        trend = pivot.groupby("ano_mes", as_index=False).relacao.mean()
        fig = px.line(trend, x="ano_mes", y="relacao", markers=True, title="Evolução da relação etanol/gasolina")
        fig.add_hline(y=settings.ethanol_threshold, line_dash="dash", line_color=RED)
        left.plotly_chart(polish(fig), use_container_width=True)
        right.dataframe(latest[["uf", "ETANOL HIDRATADO", "GASOLINA COMUM", "relacao", "compensa"]],
                        hide_index=True, use_container_width=True)
    else:
        st.info("Selecione gasolina comum e etanol hidratado para visualizar a comparação.")

with quality:
    left, right = st.columns([1, 1.3])
    outliers = filtered[filtered.outlier].copy()
    counts = pd.DataFrame({"classe": ["Regulares", "Outliers"], "registros": [len(filtered) - len(outliers), len(outliers)]})
    fig = px.pie(counts, names="classe", values="registros", hole=.65, color="classe",
                 color_discrete_map={"Regulares": BLUE, "Outliers": RED}, title="Composição da qualidade")
    left.plotly_chart(polish(fig), use_container_width=True)
    volatility = filtered.groupby("produto", as_index=False).agg(
        volatilidade=("preco_venda", "std"), amplitude=("preco_venda", lambda s: s.max() - s.min()))
    fig = px.bar(volatility.sort_values("volatilidade"), x="volatilidade", y="produto", orientation="h",
                 color="amplitude", color_continuous_scale="Oranges", title="Volatilidade por combustível")
    right.plotly_chart(polish(fig), use_container_width=True)
    st.markdown("#### Registros sinalizados para investigação")
    columns = ["data_coleta", "uf", "municipio", "produto", "revenda", "preco_venda", "z_score", "faixa_preco"]
    st.dataframe(outliers.sort_values("z_score", key=abs, ascending=False)[columns].head(200),
                 hide_index=True, use_container_width=True)

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
