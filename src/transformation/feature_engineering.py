import numpy as np
import pandas as pd

from config.settings import settings


def create_features(df: pd.DataFrame, ethanol_threshold: float | None = None) -> pd.DataFrame:
    threshold = settings.ethanol_threshold if ethanol_threshold is None else ethanol_threshold
    result = df.copy().sort_values(["produto", "uf", "municipio", "data_coleta"])
    date = result["data_coleta"]
    result["ano"] = date.dt.year
    result["mes"] = date.dt.month
    result["ano_mes"] = date.dt.to_period("M").astype(str)
    result["trimestre"] = date.dt.quarter
    result["semana"] = date.dt.isocalendar().week.astype("int64")
    result["dia_semana"] = date.dt.day_name()
    groups = [result[c] for c in ("produto", "uf", "municipio")]
    result["preco_anterior"] = result.groupby(["produto", "uf", "municipio"], dropna=False)["preco_venda"].shift()
    result["variacao_absoluta"] = result["preco_venda"] - result["preco_anterior"]
    previous = result["preco_anterior"].to_numpy(dtype=float)
    current = result["preco_venda"].to_numpy(dtype=float)
    result["variacao_percentual"] = np.where((previous != 0) & ~np.isnan(previous), ((current / previous) - 1) * 100, np.nan)
    grouped = result.groupby(["produto", "uf", "municipio"], dropna=False)["preco_venda"]
    result["media_movel_4_periodos"] = grouped.transform(lambda s: s.rolling(4, min_periods=1).mean())
    result["media_movel_8_periodos"] = grouped.transform(lambda s: s.rolling(8, min_periods=1).mean())
    values = result["preco_venda"].to_numpy(dtype=float)
    mean, std = np.mean(values), np.std(values)
    result["z_score"] = np.where(std > 0, (values - mean) / std, 0.0)
    result["outlier"] = np.abs(result["z_score"]) > settings.zscore_threshold
    p25, p75 = np.percentile(values, [25, 75])
    result["faixa_preco"] = np.select([values <= p25, values <= p75], ["BAIXO", "MEDIO"], default="ALTO")
    monthly = result.groupby(["ano_mes", "uf", "produto"], as_index=False)["preco_venda"].mean()
    pivot = monthly.pivot_table(index=["ano_mes", "uf"], columns="produto", values="preco_venda")
    ethanol = next((c for c in pivot if "ETANOL" in c), None)
    gasoline = next((c for c in pivot if c == "GASOLINA COMUM"), None)
    if ethanol and gasoline:
        relation = (pivot[ethanol] / pivot[gasoline]).rename("relacao_etanol_gasolina")
        result = result.merge(relation.reset_index(), on=["ano_mes", "uf"], how="left")
    else:
        result["relacao_etanol_gasolina"] = np.nan
    result["etanol_compensa"] = np.where(result["relacao_etanol_gasolina"].notna(), np.where(result["relacao_etanol_gasolina"] <= threshold, "SIM", "NAO"), pd.NA)
    return result.reset_index(drop=True)
