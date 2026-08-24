from src.transformation.cleaner import clean, normalize_column


def test_normalize_column():
    assert normalize_column("PREÇO DE VENDA") == "preco_de_venda"


def test_clean_converts_schema_and_types(raw_df):
    result, report = clean(raw_df)
    assert {"preco_venda", "data_coleta", "uf"} <= set(result)
    assert result["preco_venda"].dtype == "float64"
    assert report.invalid_critical_removed == 0
