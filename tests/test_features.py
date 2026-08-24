import numpy as np

from src.transformation.cleaner import clean
from src.transformation.feature_engineering import create_features
from src.transformation.transformer import transform


def test_features_include_variation_and_ethanol_analysis(raw_df):
    cleaned, _ = clean(raw_df)
    result = create_features(transform(cleaned), ethanol_threshold=0.70)
    assert {"variacao_percentual", "z_score", "faixa_preco", "relacao_etanol_gasolina", "etanol_compensa"} <= set(result)
    gasoline = result[result["produto"] == "GASOLINA COMUM"].sort_values("data_coleta")
    assert np.isnan(gasoline.iloc[0]["variacao_percentual"])
    assert gasoline.iloc[1]["variacao_percentual"] > 0
    assert set(result["etanol_compensa"].dropna()) == {"SIM"}
