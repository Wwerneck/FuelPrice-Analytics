from __future__ import annotations

import json
import uuid
from dataclasses import asdict, dataclass
from datetime import UTC, datetime

import pandas as pd

from config.settings import settings
from src.analytics.metrics import generate_metrics
from src.database.loader import load_postgresql
from src.extraction.anp_extractor import extract
from src.ingestion.raw_loader import ingest_raw
from src.transformation.cleaner import clean
from src.transformation.feature_engineering import create_features
from src.transformation.transformer import transform
from src.utils.logger import logger
from src.validation.data_quality import validate_processed, validate_raw


@dataclass
class PipelineResult:
    run_id: str
    source_file: str
    records_read: int
    records_written: int
    quality_status: str
    processed_file: str


def save_parquet(df: pd.DataFrame, path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(path, index=False, engine="pyarrow", compression="snappy")


def run_pipeline(source_path=None, load_database: bool | None = None) -> PipelineResult:
    run_id = str(uuid.uuid4())
    started = datetime.now(UTC)
    logger.info("PIPELINE | START | run_id=%s", run_id)
    try:
        source = source_path or extract()
        raw = ingest_raw(source)
        logger.info("VALIDATE_RAW | START | %d registros", len(raw))
        validate_raw(raw)
        logger.info("VALIDATE_RAW | SUCCESS")
        logger.info("CLEAN | START")
        cleaned, cleaning_report = clean(raw)
        logger.info("CLEAN | SUCCESS | %d duplicatas e %d inválidos removidos", cleaning_report.duplicates_removed, cleaning_report.invalid_critical_removed)
        logger.info("TRANSFORM | START")
        transformed = transform(cleaned)
        logger.info("TRANSFORM | SUCCESS")
        logger.info("FEATURES | START")
        featured = create_features(transformed)
        logger.info("FEATURES | SUCCESS")
        logger.info("QUALITY | START")
        quality = validate_processed(featured, len(raw))
        logger.info("QUALITY | SUCCESS | %s", quality.status)
        interim = settings.interim_dir / f"fuel_prices_{run_id}.parquet"
        processed = settings.processed_dir / "fuel_prices.parquet"
        save_parquet(featured, interim)
        save_parquet(featured, processed)
        (settings.processed_dir / "quality_report.json").write_text(json.dumps(quality.to_dict(), ensure_ascii=False, indent=2), encoding="utf-8")
        if settings.load_database if load_database is None else load_database:
            logger.info("DATABASE | START")
            load_postgresql(featured)
            logger.info("DATABASE | SUCCESS")
        else:
            logger.warning("DATABASE | WARNING | Carga desabilitada por configuração")
        logger.info("METRICS | START")
        generate_metrics(featured)
        logger.info("METRICS | SUCCESS")
        result = PipelineResult(run_id, str(source), len(raw), len(featured), quality.status, str(processed))
        metadata = {**asdict(result), "started_at": started.isoformat(), "finished_at": datetime.now(UTC).isoformat(), "status": "SUCCESS", "cleaning": asdict(cleaning_report)}
        (settings.processed_dir / "last_run.json").write_text(json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8")
        logger.info("PIPELINE | SUCCESS | %d registros", len(featured))
        return result
    except Exception as exc:
        logger.exception("PIPELINE | FAILURE | run_id=%s", run_id)
        metadata = {"run_id": run_id, "started_at": started.isoformat(), "finished_at": datetime.now(UTC).isoformat(), "status": "FAILURE", "error_message": str(exc)}
        settings.ensure_directories()
        (settings.processed_dir / "last_run.json").write_text(json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8")
        raise
