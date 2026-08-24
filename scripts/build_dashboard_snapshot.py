"""Gera um snapshot oficial compacto para publicação do dashboard."""

from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "data" / "processed" / "fuel_prices.parquet"
TARGET = ROOT / "data" / "published" / "fuel_prices.parquet"

COLUMNS = [
    "data_coleta", "ano", "mes", "ano_mes", "regiao", "uf", "municipio",
    "produto", "revenda", "cnpj_revenda", "preco_venda", "z_score",
    "outlier", "faixa_preco",
]
CATEGORICAL = ["regiao", "uf", "municipio", "produto", "faixa_preco"]


def build_snapshot(source: Path = SOURCE, target: Path = TARGET) -> Path:
    frame = pd.read_parquet(source, columns=COLUMNS)
    for column in CATEGORICAL:
        frame[column] = frame[column].astype("category")
    months = sorted(frame["ano_mes"].dropna().astype(str).unique())
    frame["ano_mes"] = pd.Categorical(frame["ano_mes"], categories=months, ordered=True)
    target.parent.mkdir(parents=True, exist_ok=True)
    frame.to_parquet(target, index=False, compression="zstd")
    return target


if __name__ == "__main__":
    output = build_snapshot()
    print(f"Snapshot publicado: {output} ({output.stat().st_size / 1024 / 1024:.2f} MB)")
