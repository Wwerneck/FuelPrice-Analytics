from pathlib import Path

from src.pipeline.fuelprice_pipeline import save_parquet
from src.transformation.cleaner import clean
from src.transformation.feature_engineering import create_features
from src.transformation.transformer import transform
from src.validation.data_quality import validate_processed, validate_raw


def test_pipeline_chain(raw_df, tmp_path: Path):
    validate_raw(raw_df)
    cleaned, _ = clean(raw_df)
    processed = create_features(transform(cleaned))
    report = validate_processed(processed, len(raw_df))
    target = tmp_path / "processed.parquet"
    save_parquet(processed, target)
    assert target.exists()
    assert report.status in {"APROVADO", "APROVADO COM ALERTA"}
    assert len(processed) == len(raw_df)
