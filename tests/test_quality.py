import pandas as pd
import pytest

from src.validation.data_quality import DataQualityError, validate_raw


def test_validate_raw_accepts_official_schema(raw_df):
    validate_raw(raw_df)


def test_validate_raw_rejects_missing_schema():
    with pytest.raises(DataQualityError):
        validate_raw(pd.DataFrame({"x": [1]}))
