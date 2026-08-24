import logging
from logging.handlers import RotatingFileHandler

from config.settings import settings


def configure_logging() -> logging.Logger:
    settings.ensure_directories()
    logger = logging.getLogger("fuelprice")
    if logger.handlers:
        return logger
    logger.setLevel(logging.INFO)
    formatter = logging.Formatter("%(asctime)s | %(levelname)s | %(name)s | %(message)s")
    console = logging.StreamHandler()
    console.setFormatter(formatter)
    file_handler = RotatingFileHandler(settings.logs_dir / "pipeline.log", maxBytes=5_000_000, backupCount=3, encoding="utf-8")
    file_handler.setFormatter(formatter)
    logger.addHandler(console)
    logger.addHandler(file_handler)
    return logger


logger = configure_logging()
