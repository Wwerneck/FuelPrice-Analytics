from __future__ import annotations

import re
from pathlib import Path
from urllib.parse import urljoin

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from config.settings import Settings, settings
from src.utils.logger import logger


class ExtractionError(RuntimeError):
    pass


def _session(retries: int) -> requests.Session:
    retry = Retry(total=retries, connect=retries, read=retries, backoff_factor=1, status_forcelist=(429, 500, 502, 503, 504), allowed_methods=("GET",))
    session = requests.Session()
    session.headers["User-Agent"] = "FuelPrice-Analytics/1.0 (portfolio data pipeline)"
    session.mount("https://", HTTPAdapter(max_retries=retry))
    return session


def discover_latest_source(session: requests.Session, cfg: Settings = settings) -> str:
    if cfg.anp_source_url:
        return cfg.anp_source_url
    response = session.get(cfg.anp_catalog_url, timeout=cfg.request_timeout)
    response.raise_for_status()
    links = re.findall(r'href=["\']([^"\']*ca-(\d{4})-(0[12])\.zip[^"\']*)', response.text, flags=re.I)
    if not links:
        raise ExtractionError("Nenhum arquivo semestral de combustíveis automotivos foi localizado no catálogo da ANP")
    href, _, _ = max(links, key=lambda item: (int(item[1]), int(item[2])))
    return urljoin(cfg.anp_catalog_url, href)


def extract(cfg: Settings = settings, force: bool = False) -> Path:
    cfg.ensure_directories()
    logger.info("EXTRACT | START | Localizando arquivo oficial da ANP")
    session = _session(cfg.request_retries)
    try:
        url = discover_latest_source(session, cfg)
        filename = Path(url.split("?", 1)[0]).name
        if Path(filename).suffix.lower() not in {".csv", ".zip", ".xlsx"}:
            raise ExtractionError(f"Extensão não suportada: {filename}")
        target = cfg.raw_dir / filename
        if target.exists() and target.stat().st_size >= cfg.min_download_bytes and not force:
            logger.info("EXTRACT | SUCCESS | Arquivo já existe: %s", target)
            return target
        with session.get(url, stream=True, timeout=cfg.request_timeout) as response:
            response.raise_for_status()
            temporary = target.with_suffix(target.suffix + ".part")
            with temporary.open("wb") as output:
                for chunk in response.iter_content(1024 * 1024):
                    if chunk:
                        output.write(chunk)
            if temporary.stat().st_size < cfg.min_download_bytes:
                temporary.unlink(missing_ok=True)
                raise ExtractionError("Download menor que o tamanho mínimo configurado")
            temporary.replace(target)
        logger.info("EXTRACT | SUCCESS | Download concluído: %s", target)
        return target
    except requests.RequestException as exc:
        cached = sorted(cfg.raw_dir.glob("ca-????-0[12].zip"))
        if cached and cached[-1].stat().st_size >= cfg.min_download_bytes and not force:
            logger.warning("EXTRACT | WARNING | Catálogo indisponível; usando cache validado: %s", cached[-1])
            return cached[-1]
        logger.exception("EXTRACT | FAILURE | %s", exc)
        raise ExtractionError(str(exc)) from exc
    except OSError as exc:
        logger.exception("EXTRACT | FAILURE | %s", exc)
        raise ExtractionError(str(exc)) from exc
