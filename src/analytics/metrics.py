import json
from pathlib import Path

import pandas as pd

from config.settings import settings
from src.analytics.statistics import descriptive_statistics


def generate_metrics(df: pd.DataFrame, target: Path | None = None) -> dict:
    metrics = {"records": len(df), "stations": int(df["cnpj_revenda"].nunique()) if "cnpj_revenda" in df else int(df["revenda"].nunique()), "municipalities": int(df["municipio"].nunique()), "states": int(df["uf"].nunique()), "outliers": int(df["outlier"].sum()), "price": descriptive_statistics(df["preco_venda"])}
    output = target or settings.processed_dir / "metrics.json"
    output.write_text(json.dumps(metrics, ensure_ascii=False, indent=2), encoding="utf-8")
    return metrics
