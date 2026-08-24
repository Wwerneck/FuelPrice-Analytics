from pathlib import Path
from unittest.mock import Mock

from config.settings import Settings
from src.extraction.anp_extractor import discover_latest_source, extract


def test_discovers_latest_semester():
    response = Mock(text='<a href="/ca-2025-02.zip">x</a><a href="/ca-2026-01.zip">y</a>')
    response.raise_for_status.return_value = None
    session = Mock()
    session.get.return_value = response
    cfg = Settings(base_dir=Path("."), anp_catalog_url="https://example.test/catalog")
    assert discover_latest_source(session, cfg).endswith("ca-2026-01.zip")


def test_extract_falls_back_to_valid_cache(tmp_path, monkeypatch):
    import requests
    cached = tmp_path / "ca-2026-01.zip"
    cached.write_bytes(b"x" * 2048)
    cfg = Settings(base_dir=tmp_path, raw_dir=tmp_path, min_download_bytes=1024)
    monkeypatch.setattr("src.extraction.anp_extractor.discover_latest_source", lambda *_: (_ for _ in ()).throw(requests.ConnectionError("offline")))
    assert extract(cfg) == cached
