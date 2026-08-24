from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass

import pandas as pd


@dataclass(frozen=True)
class CleaningReport:
    received: int
    duplicates_removed: int
    invalid_critical_removed: int


def normalize_column(value: str) -> str:
    value = unicodedata.normalize("NFKD", str(value)).encode("ascii", "ignore").decode()
    return re.sub(r"_+", "_", re.sub(r"[^a-zA-Z0-9]+", "_", value).strip("_")).lower()


ALIASES = {"regiao_sigla": "regiao", "estado_sigla": "uf", "data_da_coleta": "data_coleta", "valor_de_venda": "preco_venda", "valor_de_compra": "preco_compra", "cnpj_da_revenda": "cnpj_revenda", "unidade_de_medida": "unidade_medida"}
PRODUCTS = {"GASOLINA": "GASOLINA COMUM", "GASOLINA C": "GASOLINA COMUM", "ETANOL": "ETANOL HIDRATADO", "ALCOOL": "ETANOL HIDRATADO"}


def clean(df: pd.DataFrame) -> tuple[pd.DataFrame, CleaningReport]:
    result = df.copy()
    result.columns = [ALIASES.get(normalize_column(c), normalize_column(c)) for c in result.columns]
    for column in result.select_dtypes(include=["object", "string"]):
        result[column] = result[column].astype("string").str.strip().replace({"": pd.NA, "nan": pd.NA})
    for column in ("regiao", "uf", "municipio", "produto", "bandeira"):
        if column in result:
            result[column] = result[column].str.upper()
    if "produto" in result:
        result["produto"] = result["produto"].replace(PRODUCTS)
    if "data_coleta" in result:
        result["data_coleta"] = pd.to_datetime(result["data_coleta"], dayfirst=True, errors="coerce")
    for column in ("preco_venda", "preco_compra"):
        if column in result:
            result[column] = pd.to_numeric(result[column].str.replace(".", "", regex=False).str.replace(",", ".", regex=False), errors="coerce").astype("float64")
    before = len(result)
    result = result.drop_duplicates().reset_index(drop=True)
    critical = [c for c in ("data_coleta", "preco_venda", "produto", "uf") if c in result]
    invalid = result[critical].isna().any(axis=1) if critical else pd.Series(False, index=result.index)
    invalid |= result.get("preco_venda", pd.Series(1, index=result.index)).le(0)
    removed_invalid = int(invalid.sum())
    result = result.loc[~invalid].reset_index(drop=True)
    return result, CleaningReport(before, before - len(result) - removed_invalid, removed_invalid)
