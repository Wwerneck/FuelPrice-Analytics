from __future__ import annotations

import hashlib

import pandas as pd
from sqlalchemy import Engine, text

from src.database.connection import get_engine


def _business_key(df: pd.DataFrame) -> pd.Series:
    columns = [c for c in ("cnpj_revenda", "produto", "data_coleta", "preco_venda") if c in df]
    return df[columns].astype(str).agg("|".join, axis=1).map(lambda value: hashlib.sha256(value.encode()).hexdigest())


def load_postgresql(df: pd.DataFrame, engine: Engine | None = None) -> int:
    engine = engine or get_engine()
    payload = df.copy()
    payload["record_id"] = _business_key(payload)
    # Staging preserva os tipos inferidos pelo SQLAlchemy; o merge abaixo mantém reruns idempotentes.
    payload.to_sql("fuel_prices_staging", engine, if_exists="replace", index=False, method="multi", chunksize=5000)
    columns = list(payload.columns)
    quoted = ", ".join(f'"{c}"' for c in columns)
    updates = ", ".join(f'"{c}" = EXCLUDED."{c}"' for c in columns if c != "record_id")
    with engine.begin() as connection:
        connection.execute(text("CREATE TABLE IF NOT EXISTS fuel_prices (LIKE fuel_prices_staging INCLUDING ALL)"))
        connection.execute(text("""
            DO $$ BEGIN
              ALTER TABLE fuel_prices ADD CONSTRAINT fuel_prices_pkey PRIMARY KEY (record_id);
            EXCEPTION WHEN duplicate_object OR invalid_table_definition THEN NULL;
            END $$
        """))
        # Evolução aditiva do schema: novas features recebem o mesmo tipo da staging.
        connection.execute(text("""
            DO $$
            DECLARE col record;
            BEGIN
              FOR col IN
                SELECT s.column_name, s.data_type, s.udt_name
                FROM information_schema.columns s
                LEFT JOIN information_schema.columns t
                  ON t.table_schema='public' AND t.table_name='fuel_prices' AND t.column_name=s.column_name
                WHERE s.table_schema='public' AND s.table_name='fuel_prices_staging' AND t.column_name IS NULL
              LOOP
                EXECUTE format('ALTER TABLE fuel_prices ADD COLUMN %I %s', col.column_name,
                  CASE WHEN col.data_type='ARRAY' THEN col.udt_name ELSE col.data_type END);
              END LOOP;
            END $$
        """))
        connection.execute(text(f"INSERT INTO fuel_prices ({quoted}) SELECT {quoted} FROM fuel_prices_staging ON CONFLICT (record_id) DO UPDATE SET {updates}"))
        connection.execute(text("DROP TABLE fuel_prices_staging"))
    return len(payload)
