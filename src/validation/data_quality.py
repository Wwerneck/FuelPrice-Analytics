from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

import pandas as pd

RAW_COLUMN_GROUPS = {
    "data": {"data_da_coleta", "data_coleta"},
    "preco": {"valor_de_venda", "preco_venda"},
    "produto": {"produto"},
    "uf": {"estado_sigla", "uf"},
    "municipio": {"municipio"},
}
VALID_UFS = {"AC","AL","AP","AM","BA","CE","DF","ES","GO","MA","MT","MS","MG","PA","PB","PR","PE","PI","RJ","RN","RS","RO","RR","SC","SP","SE","TO"}


class DataQualityError(ValueError):
    pass


@dataclass(frozen=True)
class QualityReport:
    records_received: int
    records_processed: int
    duplicates: int
    critical_nulls: int
    invalid_prices: int
    invalid_dates: int
    invalid_ufs: int
    outliers: int
    status: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _normalized(columns) -> set[str]:
    from src.transformation.cleaner import normalize_column
    return {normalize_column(c) for c in columns}


def validate_raw(df: pd.DataFrame) -> None:
    if df.empty:
        raise DataQualityError("Dataset bruto vazio")
    columns = _normalized(df.columns)
    missing = [name for name, aliases in RAW_COLUMN_GROUPS.items() if not aliases & columns]
    if missing:
        raise DataQualityError(f"Schema bruto incompatível; campos ausentes: {missing}")
    aliases = {next(iter(aliases & columns)): name for name, aliases in RAW_COLUMN_GROUPS.items() if aliases & columns}
    normalized = df.copy()
    normalized.columns = [__import__("src.transformation.cleaner", fromlist=["normalize_column"]).normalize_column(c) for c in df.columns]
    date_col = next(k for k, v in aliases.items() if v == "data")
    price_col = next(k for k, v in aliases.items() if v == "preco")
    product_col = next(k for k, v in aliases.items() if v == "produto")
    uf_col = next(k for k, v in aliases.items() if v == "uf")
    if pd.to_datetime(normalized[date_col], dayfirst=True, errors="coerce").isna().any():
        raise DataQualityError("Datas inválidas nos dados brutos")
    prices = pd.to_numeric(normalized[price_col].astype(str).str.replace(".", "", regex=False).str.replace(",", ".", regex=False), errors="coerce")
    if prices.isna().any():
        raise DataQualityError("Preços não interpretáveis nos dados brutos")
    if normalized[product_col].isna().any() or normalized[uf_col].isna().any():
        raise DataQualityError("Produto ou UF ausente nos dados brutos")


def validate_processed(df: pd.DataFrame, records_received: int | None = None) -> QualityReport:
    required = {"data_coleta", "preco_venda", "produto", "uf", "municipio", "ano_mes", "z_score", "outlier"}
    missing = required - set(df.columns)
    if missing:
        raise DataQualityError(f"Schema processado incompatível: {sorted(missing)}")
    duplicates = int(df.duplicated().sum())
    critical_nulls = int(df[["data_coleta", "preco_venda", "produto", "uf", "municipio"]].isna().any(axis=1).sum())
    invalid_prices = int((df["preco_venda"] <= 0).sum())
    invalid_dates = int(df["data_coleta"].isna().sum())
    invalid_ufs = int((~df["uf"].isin(VALID_UFS)).sum())
    outliers = int(df["outlier"].sum())
    critical = critical_nulls + invalid_prices + invalid_dates + invalid_ufs
    status = "REPROVADO" if critical else ("APROVADO COM ALERTA" if duplicates or outliers else "APROVADO")
    report = QualityReport(records_received or len(df), len(df), duplicates, critical_nulls, invalid_prices, invalid_dates, invalid_ufs, outliers, status)
    if critical:
        raise DataQualityError(f"Dados processados reprovados: {report.to_dict()}")
    return report
