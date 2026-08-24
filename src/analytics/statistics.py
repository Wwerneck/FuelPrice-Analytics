import numpy as np
import pandas as pd


def descriptive_statistics(values: pd.Series) -> dict[str, float]:
    data = values.dropna().to_numpy(dtype=float)
    if data.size == 0:
        return {key: np.nan for key in ("media","mediana","minimo","maximo","variancia","desvio_padrao","p25","p50","p75","p90","p95","coeficiente_variacao","amplitude")}
    mean, std = np.mean(data), np.std(data)
    return {"media": float(mean), "mediana": float(np.median(data)), "minimo": float(np.min(data)), "maximo": float(np.max(data)), "variancia": float(np.var(data)), "desvio_padrao": float(std), "p25": float(np.percentile(data,25)), "p50": float(np.percentile(data,50)), "p75": float(np.percentile(data,75)), "p90": float(np.percentile(data,90)), "p95": float(np.percentile(data,95)), "coeficiente_variacao": float(std / mean if mean else np.nan), "amplitude": float(np.max(data)-np.min(data))}
