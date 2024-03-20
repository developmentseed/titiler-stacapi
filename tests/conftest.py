"""titiler.stacapi tests configuration."""

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def app(monkeypatch):
    """App fixture."""
    monkeypatch.setenv("TITILER_STACAPI_STAC_API_URL", "http://something.stac")

    from titiler.stacapi.main import app

    with TestClient(app) as client:
        yield client
