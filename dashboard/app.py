from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

from config.settings import settings

st.set_page_config(page_title="FuelPrice Analytics", layout="wide")
st.title("FuelPrice Analytics")


@st.cache_data(ttl=900)
def load_data() -> pd.DataFrame:
    path = Path(settings.processed_dir / "fuel_prices.parquet")
    if not path.exists():
        return pd.DataFrame()
    return pd.read_parquet(path)


df = load_data()
if df.empty:
    st.info("Execute `python main.py` para gerar a camada processada.")
    st.stop()

with st.sidebar:
    st.header("Filtros")
    products = st.multiselect("Combustível", sorted(df.produto.dropna().unique()), default=[])
    regions = st.multiselect("Região", sorted(df.regiao.dropna().unique()), default=[])
    states = st.multiselect("Estado", sorted(df.uf.dropna().unique()), default=[])
    municipalities = st.multiselect("Município", sorted(df.municipio.dropna().unique()), default=[])
    start, end = st.date_input("Período", (df.data_coleta.min().date(), df.data_coleta.max().date()))

filtered = df[df.data_coleta.between(pd.Timestamp(start), pd.Timestamp(end))]
for column, values in (("produto", products), ("regiao", regions), ("uf", states), ("municipio", municipalities)):
    if values:
        filtered = filtered[filtered[column].isin(values)]

stats = filtered.preco_venda.agg(["mean", "median", "min", "max"])
cols = st.columns(8)
labels = [("Preço médio", stats["mean"]), ("Mediana", stats["median"]), ("Mínimo", stats["min"]), ("Máximo", stats["max"]), ("Postos", filtered.cnpj_revenda.nunique()), ("Municípios", filtered.municipio.nunique()), ("Estados", filtered.uf.nunique()), ("Outliers", int(filtered.outlier.sum()))]
for col, (label, value) in zip(cols, labels):
    col.metric(label, f"{value:.2f}" if isinstance(value, float) else value)

monthly = filtered.groupby(["ano_mes", "produto"], as_index=False).preco_venda.mean()
st.plotly_chart(px.line(monthly, x="ano_mes", y="preco_venda", color="produto", markers=True, title="Evolução temporal"), use_container_width=True)
left, right = st.columns(2)
left.plotly_chart(px.bar(filtered.groupby("uf", as_index=False).preco_venda.mean().sort_values("preco_venda"), x="uf", y="preco_venda", title="Preço médio por estado"), use_container_width=True)
right.plotly_chart(px.box(filtered, x="produto", y="preco_venda", color="produto", title="Distribuição e outliers"), use_container_width=True)

if not filtered.empty:
    state = filtered.groupby("uf").preco_venda.mean().idxmax()
    volatility = filtered.groupby("regiao").preco_venda.std().idxmax()
    competitive = filtered.loc[filtered.etanol_compensa.eq("SIM"), "uf"].nunique()
    st.subheader("Insights automáticos")
    st.write(f"O estado com maior preço médio no recorte é **{state}**. O etanol foi competitivo em **{competitive} estados**. A região com maior volatilidade foi **{volatility}**.")
