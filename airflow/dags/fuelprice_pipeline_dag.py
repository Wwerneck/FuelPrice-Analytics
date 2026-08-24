from __future__ import annotations

from datetime import timedelta
from pathlib import Path

from airflow.decorators import dag, task
from airflow.utils.dates import days_ago

from config.settings import settings


@dag(
    dag_id="fuelprice_pipeline",
    schedule="0 10 * * 1",  # ANP pesquisa/publica semanalmente; segunda-feira permite consolidar a semana anterior.
    start_date=days_ago(1),
    catchup=False,
    max_active_runs=1,
    default_args={"retries": 1, "retry_delay": timedelta(minutes=5), "execution_timeout": timedelta(minutes=30)},
    tags=["anp", "fuelprice", "data-engineering"],
)
def fuelprice_pipeline():
    @task(retries=3)
    def extract_anp() -> str:
        from src.extraction.anp_extractor import extract
        return str(extract())

    @task(retries=0)
    def validate_raw(source: str) -> str:
        from src.ingestion.raw_loader import ingest_raw
        from src.validation.data_quality import validate_raw as validate
        df = ingest_raw(Path(source)); validate(df)
        path = settings.interim_dir / "airflow_raw.parquet"; df.to_parquet(path, index=False)
        return str(path)

    @task
    def clean_data(path: str) -> str:
        import pandas as pd
        from src.transformation.cleaner import clean
        df, _ = clean(pd.read_parquet(path)); output = settings.interim_dir / "airflow_clean.parquet"; df.to_parquet(output, index=False)
        return str(output)

    @task
    def transform_data(path: str) -> str:
        import pandas as pd
        from src.transformation.transformer import transform
        df = transform(pd.read_parquet(path)); output = settings.interim_dir / "airflow_transformed.parquet"; df.to_parquet(output, index=False)
        return str(output)

    @task
    def feature_engineering(path: str) -> str:
        import pandas as pd
        from src.transformation.feature_engineering import create_features
        df = create_features(pd.read_parquet(path)); output = settings.interim_dir / "airflow_featured.parquet"; df.to_parquet(output, index=False)
        return str(output)

    @task(retries=0)
    def validate_processed(path: str) -> str:
        import pandas as pd
        from src.validation.data_quality import validate_processed as validate
        validate(pd.read_parquet(path)); return path

    @task
    def save_parquet(path: str) -> str:
        import pandas as pd
        output = settings.processed_dir / "fuel_prices.parquet"; pd.read_parquet(path).to_parquet(output, index=False)
        return str(output)

    @task
    def load_postgresql(path: str) -> int:
        import pandas as pd
        from src.database.loader import load_postgresql as load
        return load(pd.read_parquet(path))

    @task
    def generate_metrics(path: str) -> dict:
        import pandas as pd
        from src.analytics.metrics import generate_metrics as generate
        return generate(pd.read_parquet(path))

    source = extract_anp()
    raw = validate_raw(source)
    cleaned = clean_data(raw)
    transformed = transform_data(cleaned)
    featured = feature_engineering(transformed)
    validated = validate_processed(featured)
    processed = save_parquet(validated)
    loaded = load_postgresql(processed)
    metrics = generate_metrics(processed)
    loaded >> metrics


fuelprice_pipeline()
