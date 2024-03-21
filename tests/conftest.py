"""titiler.stacapi tests configuration."""

import os

import pytest
import rasterio
from fastapi.testclient import TestClient

DATA_DIR = os.path.join(os.path.dirname(__file__), "fixtures")


@pytest.fixture
def app(monkeypatch):
    """App fixture."""
    monkeypatch.setenv("TITILER_STACAPI_STAC_API_URL", "http://something.stac")

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
