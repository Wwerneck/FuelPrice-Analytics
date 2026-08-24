import pandas as pd

from src.analytics.statistics import descriptive_statistics


def test_descriptive_statistics():
    stats = descriptive_statistics(pd.Series([1, 2, 3]))
    assert stats["media"] == 2
    assert stats["amplitude"] == 2
    assert stats["p50"] == 2
