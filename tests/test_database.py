import os

import pandas as pd
import pytest
from sqlalchemy import create_engine, text

from src.database.loader import load_postgresql


@pytest.mark.skipif(not os.getenv("TEST_DATABASE_URL"), reason="TEST_DATABASE_URL não configurada")
def test_postgresql_load_is_idempotent(raw_df):
    from src.transformation.cleaner import clean
    from src.transformation.feature_engineering import create_features
    from src.transformation.transformer import transform

    engine = create_engine(os.environ["TEST_DATABASE_URL"])
    cleaned, _ = clean(raw_df)
    featured = create_features(transform(cleaned))
    load_postgresql(featured, engine)
    load_postgresql(featured, engine)
    with engine.connect() as connection:
        count = connection.execute(text("SELECT COUNT(*) FROM fuel_prices")).scalar_one()
    assert count == len(featured)
