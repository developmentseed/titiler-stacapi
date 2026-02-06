"""titiler.stacapi tests configuration."""

import os
from typing import Any

import pytest
import rasterio
from fastapi.testclient import TestClient
from rasterio.io import MemoryFile

DATA_DIR = os.path.join(os.path.dirname(__file__), "fixtures")


def parse_img(content: bytes) -> dict[Any, Any]:
    """Read tile image and return metadata."""
    with MemoryFile(content) as mem:
        with mem.open() as dst:
            return dst.profile


@pytest.fixture
def app(monkeypatch):
    """App fixture."""
    monkeypatch.setenv("TITILER_STACAPI_STAC_API_URL", "http://something.stac")
    monkeypatch.setenv("TITILER_STACAPI_API_DEBUG", "TRUE")
    monkeypatch.setenv("TITILER_STACAPI_CACHE_DISABLE", "TRUE")

    from titiler.stacapi.main import app

    with TestClient(app) as client:
        yield client


def mock_rasterio_open(asset):
    """Mock rasterio Open."""
    assert asset.startswith(
        "https://noaa-eri-pds.s3.us-east-1.amazonaws.com/2020_Nashville_Tornado/20200307a_RGB/"
    )
    asset = asset.replace(
        "https://noaa-eri-pds.s3.us-east-1.amazonaws.com/2020_Nashville_Tornado/20200307a_RGB",
        DATA_DIR,
    )
    return rasterio.open(asset)
