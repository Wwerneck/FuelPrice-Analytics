from __future__ import annotations

from pathlib import Path
from zipfile import BadZipFile, ZipFile

import pandas as pd

from config.settings import settings
from src.utils.logger import logger


class IngestionError(RuntimeError):
    pass


def discover_raw_files() -> list[Path]:
    return sorted((p for p in settings.raw_dir.iterdir() if p.suffix.lower() in {".csv", ".zip", ".xlsx", ".xls"}), key=lambda p: p.stat().st_mtime)


def _read_csv(source) -> pd.DataFrame:
    errors: list[str] = []
    for encoding in ("utf-8-sig", "utf-8", "latin-1"):
        try:
            if hasattr(source, "seek"):
                source.seek(0)
            return pd.read_csv(source, sep=";", encoding=encoding, dtype=str, low_memory=False)
        except (UnicodeDecodeError, pd.errors.ParserError) as exc:
            errors.append(f"{encoding}: {exc}")
    raise IngestionError("CSV ilegível: " + "; ".join(errors))


def ingest_raw(path: Path | None = None) -> pd.DataFrame:
    path = path or (discover_raw_files()[-1] if discover_raw_files() else None)
    if path is None:
        raise IngestionError("Nenhum arquivo bruto disponível")
    logger.info("INGEST | START | %s", path)
    try:
        if path.suffix.lower() == ".zip":
            with ZipFile(path) as archive:
                members = [n for n in archive.namelist() if n.lower().endswith(".csv") and not n.startswith("__MACOSX")]
                if not members:
                    raise IngestionError("ZIP não contém CSV")
                frames = [_read_csv(archive.open(name)) for name in members]
                frame = pd.concat(frames, ignore_index=True)
        elif path.suffix.lower() == ".csv":
            frame = _read_csv(path)
        else:
            frame = pd.read_excel(path, dtype=str)
    except (BadZipFile, OSError, ValueError) as exc:
        raise IngestionError(f"Arquivo bruto corrompido ou ilegível: {path}") from exc
    logger.info("INGEST | SUCCESS | %d registros carregados", len(frame))
    return frame
