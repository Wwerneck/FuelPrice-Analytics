from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parents[1]
load_dotenv(BASE_DIR / ".env")


@dataclass(frozen=True)
class Settings:
    base_dir: Path = BASE_DIR
    raw_dir: Path = BASE_DIR / "data" / "raw"
    interim_dir: Path = BASE_DIR / "data" / "interim"
    processed_dir: Path = BASE_DIR / "data" / "processed"
    logs_dir: Path = BASE_DIR / "logs"
    anp_catalog_url: str = os.getenv("ANP_CATALOG_URL", "https://www.gov.br/anp/pt-br/centrais-de-conteudo/dados-abertos/serie-historica-de-precos-de-combustiveis")
    anp_source_url: str | None = os.getenv("ANP_SOURCE_URL") or None
    request_timeout: int = int(os.getenv("REQUEST_TIMEOUT", "60"))
    request_retries: int = int(os.getenv("REQUEST_RETRIES", "3"))
    min_download_bytes: int = int(os.getenv("MIN_DOWNLOAD_BYTES", "1024"))
    ethanol_threshold: float = float(os.getenv("ETANOL_THRESHOLD", "0.70"))
    zscore_threshold: float = float(os.getenv("ZSCORE_THRESHOLD", "3.0"))
    database_url: str = os.getenv("DATABASE_URL", "postgresql+psycopg2://postgres:postgres@localhost:5432/fuelprice_db")
    load_database: bool = os.getenv("LOAD_DATABASE", "false").lower() in {"1", "true", "yes"}

    def ensure_directories(self) -> None:
        for path in (self.raw_dir, self.interim_dir, self.processed_dir, self.logs_dir):
            path.mkdir(parents=True, exist_ok=True)


settings = Settings()
